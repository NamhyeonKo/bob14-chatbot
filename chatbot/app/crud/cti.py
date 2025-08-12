import requests
import socket
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any, List

from app.core.config import conf
from app.models.cti import CTI
from app.schemas.cti import CTICreate


def create_cti(db: Session, data: CTICreate) -> CTI:
	obj = CTI(**data.dict())
	db.add(obj)
	db.commit()
	db.refresh(obj)
	return obj


def _strip_key(value: Any) -> str:
	return str(value).strip() if value is not None else ""


def analyze_with_virustotal(domain: str) -> Dict[str, Any]:
	api_key = _strip_key(conf.get("virustotal_api_key"))
	headers = {"x-apikey": api_key, "accept": "application/json"} if api_key else {}
	url = f"https://www.virustotal.com/api/v3/domains/{domain}"
	try:
		r = requests.get(url, headers=headers, timeout=15)
		status = r.status_code
		try:
			data = r.json()
		except Exception:
			data = {"text": r.text}
	except requests.RequestException as e:
		status = 502
		data = {"error": str(e)}

	# 키 문제/권한/리소스 없음 등일 때 IP 엔드포인트로 폴백 시도
	if status in (401, 403, 404):
		try:
			_, _, ips = socket.gethostbyname_ex(domain)
		except Exception:
			ips = []
		if ips:
			ip = ips[0]
			ip_url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
			try:
				r2 = requests.get(ip_url, headers=headers, timeout=15)
				status = r2.status_code
				try:
					data = r2.json()
				except Exception:
					data = {"text": r2.text}
			except requests.RequestException as e:
				status = 502
				data = {"error": str(e)}
		else:
			data = {"status": status, "message": (data if isinstance(data, str) else str(data))[:500]}

	attrs = (data or {}).get("data", {}).get("attributes", {}) if isinstance(data, dict) else {}
	rep = attrs.get("reputation")
	stats = attrs.get("last_analysis_stats", {}) or {}
	malicious = stats.get("malicious")
	country = attrs.get("country")
	# 요약 벤더 목록 (악성으로 판정한 상위 몇 개만)
	results = attrs.get("last_analysis_results", {}) or {}
	vendors = [k for k, v in results.items() if isinstance(v, dict) and v.get("category") == "malicious"]

	# 저장용 최소 요약 필드 구성
	vt_trim = {
		"status": status,
		"reputation": rep if isinstance(rep, int) else 0,
		"stats": {
			"malicious": stats.get("malicious"),
			"suspicious": stats.get("suspicious"),
			"harmless": stats.get("harmless"),
			"undetected": stats.get("undetected"),
		},
		"country": country,
		"as_owner": attrs.get("as_owner"),
		"tags": (attrs.get("tags") or [])[:10],
		"vendors_malicious": vendors[:5],
		"last_modification_date": attrs.get("last_modification_date"),
	}

	return {
		"status": status,
		"malicious_score": rep if isinstance(rep, int) else 0,
		"detect_count": malicious if isinstance(malicious, int) else 0,
		"detect_vendor": "VirusTotal",
		"country": country,
		"dns": None,
		"raw_data": vt_trim,
	}


def analyze_with_hybrid(domain: str) -> Dict[str, Any]:
	api_key = _strip_key(conf.get("hybrid_analysis_api_key"))
	headers = {
		"api-key": api_key or "",
		"accept": "application/json",
		"User-Agent": "Falcon Sandbox",
	}
	# 공식 문서 기준: terms[0][term]=domain|host, terms[0][value]=<domain>
	url = "https://www.hybrid-analysis.com/api/v2/search/terms"
	try:
		# 1차: JSON 바디 (term=domain)
		json_body = {"terms": [{"term": "domain", "value": domain}], "maxresults": 25, "offset": 0}
		r = requests.post(url, headers={**headers, "Content-Type": "application/json"}, json=json_body, timeout=20)
		status = r.status_code
		try:
			data = r.json()
		except Exception:
			data = {"text": r.text}
		# 4xx면 파라미터 호환성 이슈 가능 → fallback 시도
		if status >= 400:
			# 1-2차: JSON 바디 (term=host)
			json_body2 = {"terms": [{"term": "host", "value": domain}], "maxresults": 25, "offset": 0}
			r2 = requests.post(url, headers={**headers, "Content-Type": "application/json"}, json=json_body2, timeout=20)
			status = r2.status_code
			try:
				data = r2.json()
			except Exception:
				data = {"text": r2.text}
			# 2차: x-www-form-urlencoded (terms[0][term]=domain)
			if status >= 400:
				form = {"terms[0][term]": "domain", "terms[0][value]": domain}
				r2 = requests.post(url, headers={**headers, "Content-Type": "application/x-www-form-urlencoded"}, data=form, timeout=20)
				status = r2.status_code
				try:
					data = r2.json()
				except Exception:
					data = {"text": r2.text}
			# 3차: 구 포맷(term=domain:<domain>)
			if status >= 400:
				alt = {"term": f"domain:{domain}"}
				r3 = requests.post(url, headers={**headers, "Content-Type": "application/x-www-form-urlencoded"}, data=alt, timeout=20)
				status = r3.status_code
				try:
					data = r3.json()
				except Exception:
					data = {"text": r3.text}
			# 최종 status는 마지막 시도 결과를 유지
	except requests.RequestException as e:
		status = 502
		data = {"error": str(e)}

	detect_count = 0
	trimmed: Dict[str, Any] = {"status": status}
	if isinstance(data, dict):
		# search/terms 응답은 {result: [...]} 구조
		results = data.get("result") if isinstance(data.get("result"), list) else []
		mal_like = {"malicious", "suspicious", "malware", "grayware"}
		def is_hit(it: Dict[str, Any]) -> bool:
			verdict = str(it.get("verdict", "")).lower()
			threat = it.get("threat_score") or it.get("threatscore") or 0
			av = it.get("av_detect") or 0
			return (verdict in mal_like) or (isinstance(threat, (int, float)) and threat > 0) or (isinstance(av, (int, float)) and av > 0)
		detect_count = sum(1 for it in results if isinstance(it, dict) and is_hit(it))
		# 요약 저장
		matches = []
		for it in results[:10]:
			if not isinstance(it, dict):
				continue
			matches.append({
				"sha256": it.get("sha256") or it.get("sha2") or it.get("sha1"),
				"verdict": it.get("verdict"),
				"threat_score": it.get("threat_score") or it.get("threatscore"),
				"av_detect": it.get("av_detect"),
				"vx_family": it.get("vx_family"),
				"type": it.get("type") or it.get("type_short"),
				"host": it.get("host") or it.get("host_ip") or it.get("domain"),
				"url": it.get("url"),
				"submit_time": it.get("submit_time") or it.get("analysis_start_time"),
			})
		trimmed.update({
			"total": len(results),
			"matches": matches,
		})

	# 권한/엔드포인트 이슈 힌트 추가
	if status == 404 and isinstance(data, dict) and "text" in data:
		trimmed = {"message": "Hybrid Analysis search/terms not available for this API key or incorrect endpoint", "hint": "Check API plan/permissions"}
	return {
		"status": status,
		"malicious_score": 0,
		"detect_count": detect_count,
		"detect_vendor": "Hybrid-Analysis",
		"country": None,
		"dns": None,
		"raw_data": trimmed if isinstance(trimmed, dict) and trimmed else data,
	}


def analyze_with_urlscan(domain: str) -> Dict[str, Any]:
	api_key = _strip_key(conf.get("urlscan_api_key"))
	headers = {
		"API-Key": api_key or "",
		"Content-Type": "application/json",
	}
	url = "https://urlscan.io/api/v1/search/"
	params = {"q": f"domain:{domain}"}
	try:
		r = requests.get(url, headers=headers, params=params, timeout=20)
		status = r.status_code
		try:
			data = r.json()
		except Exception:
			data = {"text": r.text}
	except requests.RequestException as e:
		status = 502
		data = {"error": str(e)}

	# raw_data를 필요한 필드만 축약해서 저장
	trimmed: Dict[str, Any] = {}
	if isinstance(data, dict):
		# 흔히 유용한 키들만 선별
		trimmed["total"] = data.get("total")
		trimmed["took"] = data.get("took")
		# 가장 최근 결과 하나만 요약 저장
		if isinstance(data.get("results"), list) and data["results"]:
			latest = data["results"][0]
			page = latest.get("page", {}) if isinstance(latest, dict) else {}
			task = latest.get("task", {}) if isinstance(latest, dict) else {}
			stats = latest.get("stats", {}) if isinstance(latest, dict) else {}
			trimmed["page"] = {
				"domain": page.get("domain"),
				"url": page.get("url"),
				"ip": page.get("ip"),
				"country": page.get("country"),
				"server": page.get("server"),
			}
			trimmed["task"] = {
				"time": task.get("time"),
				"method": task.get("method"),
			}
			trimmed["stats"] = {
				"malicious": stats.get("malicious") or stats.get("maliciousCount"),
				"suspicious": stats.get("suspicious"),
			}

	return {
		"status": status,
		"malicious_score": 0,
		"detect_count": 0,
		"detect_vendor": "Urlscan",
		"country": trimmed.get("page", {}).get("country") if isinstance(trimmed.get("page"), dict) else None,
		"dns": None,
		"raw_data": trimmed or data,
	}


 


def upsert_cti_results(db: Session, domain: str) -> List[CTI]:
	now = datetime.now()
	results: List[CTI] = []

	for source, analyzer in (
		("virustotal", analyze_with_virustotal),
		("hybrid", analyze_with_hybrid),
		("urlscan", analyze_with_urlscan),
	):
		res = analyzer(domain)
		cti = CTICreate(
			search_item=domain,
			malicious_score=res.get("malicious_score", 0),
			detect_count=res.get("detect_count", 0),
			detect_vendor=res.get("detect_vendor"),
			tag=source,
			country=res.get("country"),
			dns=res.get("dns"),
			raw_data=res.get("raw_data"),
			last_analyzed=now,
		)
		results.append(create_cti(db, cti))

	return results

