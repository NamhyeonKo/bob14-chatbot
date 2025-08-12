import re
import requests
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import conf
from app.models.cti import CTI
from app.schemas.cti import CTICreate

# Config keys (keep lowercase fallbacks for consistency)
VT_API_KEY = conf.get("virustotal_api_key") or conf.get("VIRUSTOTAL_API_KEY")
HYBRID_API_KEY = conf.get("HYBRID_API_KEY")
URLSCAN_API_KEY = conf.get("URLSCAN_API_KEY")

VT_IP_URL = "https://www.virustotal.com/api/v3/ip_addresses/"  # + {ip}
VT_DOMAIN_URL = "https://www.virustotal.com/api/v3/domains/"    # + {domain}
HYBRID_HASH_SEARCH_URL = "https://www.hybrid-analysis.com/api/v2/search/hash"  # parameter hash=<hash>
URLSCAN_DOMAIN_URL = "https://urlscan.io/api/v1/domain/"  # + {domain}

IP_REGEX = re.compile(r"^((25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.|$)){4}$")
SHA256_REGEX = re.compile(r"^[A-Fa-f0-9]{64}$")
SHA1_REGEX = re.compile(r"^[A-Fa-f0-9]{40}$")
MD5_REGEX = re.compile(r"^[A-Fa-f0-9]{32}$")
DOMAIN_REGEX = re.compile(r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)\.(?:[A-Za-z]{2,63})$")


def get_cti_by_search_item(db: Session, search_item: str) -> Optional[CTI]:
	return db.query(CTI).filter(CTI.search_item == search_item).first()


def classify_item(item: str) -> str:
	"""Return one of: ip, hash, domain. Raises if unsupported."""
	if IP_REGEX.match(item):
		return "ip"
	if SHA256_REGEX.match(item) or SHA1_REGEX.match(item) or MD5_REGEX.match(item):
		return "hash"
	# domain (simple heuristic – exclude protocol & path)
	cleaned = item.lower().strip()
	cleaned = cleaned.split("/")[0] if "://" not in cleaned else cleaned.split("//", 1)[1].split("/", 1)[0]
	if DOMAIN_REGEX.match(cleaned):
		return "domain"
	raise HTTPException(status_code=400, detail="지원하지 않는 검색 항목 형식입니다 (ip / hash / domain 만 지원).")


def analyze_ip_virustotal(ip: str) -> Dict[str, Any]:
	if not VT_API_KEY:
		raise HTTPException(status_code=500, detail="VirusTotal API Key 미설정")
	headers = {"x-apikey": VT_API_KEY}
	try:
		r = requests.get(VT_IP_URL + ip, headers=headers, timeout=15)
		r.raise_for_status()
		return r.json()
	except requests.RequestException as e:
		raise HTTPException(status_code=502, detail=f"VirusTotal IP 조회 실패: {e}")


def parse_vt_ip(data: Dict[str, Any]) -> Dict[str, Any]:
	attr = data.get("data", {}).get("attributes", {})
	stats = attr.get("last_analysis_stats", {})
	malicious = stats.get("malicious", 0)
	# Collect vendor names marking malicious (limit 5)
	results = attr.get("last_analysis_results", {}) or {}
	vendors: List[str] = [k for k, v in results.items() if v.get("category") == "malicious"]
	detect_vendor = ",".join(vendors[:5]) if vendors else "VirusTotal"
	return dict(
		malicious_score=malicious,
		detect_count=malicious,
		detect_vendor=detect_vendor,
		tag=attr.get("tags", ["ip"])[0] if attr.get("tags") else "ip",
		country=attr.get("country") or "",
		dns=attr.get("as_owner") or "",
	)


def analyze_hash_hybrid(file_hash: str) -> Dict[str, Any]:
	if not HYBRID_API_KEY:
		raise HTTPException(status_code=500, detail="Hybrid Analysis API Key 미설정")
	headers = {
		"api-key": HYBRID_API_KEY,
		"User-Agent": "Falcon Sandbox",
		"Accept": "application/json",
	}
	try:
		r = requests.get(HYBRID_HASH_SEARCH_URL, params={"hash": file_hash}, headers=headers, timeout=20)
		r.raise_for_status()
		return r.json()
	except requests.RequestException as e:
		raise HTTPException(status_code=502, detail=f"Hybrid Analysis 조회 실패: {e}")


def parse_hybrid_hash(data: Dict[str, Any]) -> Dict[str, Any]:
	# Response could be a list (search results)
	first = data[0] if isinstance(data, list) and data else {}
	score = first.get("threat_score") or 0
	av_detect = first.get("av_detect") or 0
	vendor = first.get("verdict") or "Hybrid-Analysis"
	tag = first.get("type") or first.get("environment_description") or "file"
	return dict(
		malicious_score=score,
		detect_count=av_detect,
		detect_vendor=vendor,
		tag=tag,
		country="",
		dns="",
	)


def analyze_domain_urlscan(domain: str) -> Dict[str, Any]:
	# urlscan domain info does not require API key; if provided, include
	headers = {"Accept": "application/json"}
	if URLSCAN_API_KEY:
		headers["API-Key"] = URLSCAN_API_KEY
	try:
		r = requests.get(URLSCAN_DOMAIN_URL + domain, headers=headers, timeout=15)
		r.raise_for_status()
		return r.json()
	except requests.RequestException as e:
		raise HTTPException(status_code=502, detail=f"Urlscan 조회 실패: {e}")


def parse_urlscan_domain(data: Dict[str, Any]) -> Dict[str, Any]:
	stats = data.get("stats", {})
	tags = data.get("tags") or []
	malicious = stats.get("malicious", 0) or stats.get("maliciousCount", 0) or 0
	country = data.get("country", "")
	dns_records = data.get("dns", {}).get("records", {}) if isinstance(data.get("dns"), dict) else {}
	a_records = dns_records.get("A") or []
	dns_join = ",".join([r.get("value") for r in a_records if isinstance(r, dict) and r.get("value")])
	return dict(
		malicious_score=malicious,
		detect_count=malicious,
		detect_vendor="Urlscan",
		tag=tags[0] if tags else "domain",
		country=country,
		dns=dns_join,
	)


def analyze_and_create(db: Session, search_item: str) -> CTI:
	kind = classify_item(search_item)
	raw: Dict[str, Any]
	parsed: Dict[str, Any]
	source: str
	if kind == "ip":
		raw = analyze_ip_virustotal(search_item)
		parsed = parse_vt_ip(raw)
		source = "VirusTotal"
	elif kind == "hash":
		raw = analyze_hash_hybrid(search_item)
		parsed = parse_hybrid_hash(raw)
		source = "Hybrid-Analysis"
	else:  # domain
		raw = analyze_domain_urlscan(search_item)
		parsed = parse_urlscan_domain(raw)
		source = "Urlscan"

	cti_create = CTICreate(
		search_item=search_item,
		malicious_score=parsed["malicious_score"],
		detect_count=parsed["detect_count"],
		detect_vendor=parsed["detect_vendor"],
		tag=parsed["tag"],
		country=parsed["country"],
		dns=parsed["dns"],
		raw_data=raw,
		last_analyzed=datetime.utcnow(),
	)
	db_obj = CTI(**cti_create.model_dump())
	db.add(db_obj)
	db.commit()
	db.refresh(db_obj)
	return db_obj

