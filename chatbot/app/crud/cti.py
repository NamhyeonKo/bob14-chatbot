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
	if not api_key:
		return {
			"status": 401,
			"malicious_score": 0,
			"detect_count": 0,
			"detect_vendor": "VirusTotal",
			"country": None,
			"dns": None,
			"raw_data": {"error": "VirusTotal API key not configured"},
		}
	
	headers = {"x-apikey": api_key, "accept": "application/json"}
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

	# 404 에러일 때만 IP 폴백 시도 (권한 문제가 아닌 경우)
	if status == 404:
		try:
			_, _, ips = socket.gethostbyname_ex(domain)
			if ips:
				ip = ips[0]
				ip_url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
				try:
					r2 = requests.get(ip_url, headers=headers, timeout=15)
					if r2.status_code == 200:
						status = r2.status_code
						try:
							data = r2.json()
						except Exception:
							data = {"text": r2.text}
				except requests.RequestException:
					# IP 폴백 실패 시 원래 상태 유지
					pass
		except Exception:
			# DNS 조회 실패 시 원래 상태 유지
			pass

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
			"malicious": stats.get("malicious", 0),
			"suspicious": stats.get("suspicious", 0),
			"harmless": stats.get("harmless", 0),
			"undetected": stats.get("undetected", 0),
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
	"""
	Hybrid Analysis API를 사용해 도메인을 분석합니다.
	먼저 search/terms로 기존 분석 결과를 검색하고, 없으면 quick-scan/url로 제출합니다.
	"""
	api_key = _strip_key(conf.get("hybrid_analysis_api_key"))
	
	if not api_key:
		return {
			"status": 401,
			"malicious_score": 0,
			"detect_count": 0,
			"detect_vendor": "Hybrid-Analysis",
			"country": None,
			"dns": None,
			"raw_data": {"error": "API key for Hybrid Analysis is not configured."},
		}

	headers = {
		"api-key": api_key,
		"accept": "application/json",
		"User-Agent": "Falcon",
		"Content-Type": "application/json"
	}

	# 1단계: search/terms로 기존 분석 결과 검색
	search_url = "https://www.hybrid-analysis.com/api/v2/search/terms"
	
	try:
		# domain으로 검색
		search_payload = {
			"domain": domain
		}
		
		r = requests.post(search_url, headers=headers, json=search_payload, timeout=20)
		status = r.status_code
		
		if status == 200:
			try:
				data = r.json()
				# 기존 분석 결과가 있으면 사용
				if data and isinstance(data, dict) and data.get("result"):
					results = data.get("result", [])
					if results and len(results) > 0:
						# 첫 번째 결과 사용
						first_result = results[0]
						
						# 위협 점수 계산
						threat_score = first_result.get("threat_score", 0)
						verdict = first_result.get("verdict", "")
						
						malicious_score = 0
						if verdict in ["malicious", "suspicious"]:
							malicious_score = min(threat_score, 100) if threat_score else 50
						
						return {
							"status": 200,
							"malicious_score": malicious_score,
							"detect_count": 1 if malicious_score > 0 else 0,
							"detect_vendor": "Hybrid-Analysis",
							"country": first_result.get("submit_country"),
							"dns": None,
							"raw_data": {
								"status": 200,
								"search_type": "existing_analysis",
								"job_id": first_result.get("job_id"),
								"threat_score": threat_score,
								"verdict": verdict,
								"analysis_start_time": first_result.get("analysis_start_time"),
								"environment_description": first_result.get("environment_description"),
								"total_network_connections": first_result.get("total_network_connections", 0)
							}
						}
			except Exception:
				pass
		
		# 2단계: 기존 결과가 없으면 quick-scan/url로 새로운 분석 제출
		submit_url = domain.strip()
		if not submit_url.startswith(("http://", "https://")):
			submit_url = f"https://{submit_url}"
			
		scan_url = "https://www.hybrid-analysis.com/api/v2/quick-scan/url"
		scan_payload = {
			"url": submit_url,
			"scan_type": "all"
		}
		
		r = requests.post(scan_url, headers=headers, json=scan_payload, timeout=25)
		status = r.status_code
		
		try:
			data = r.json()
		except Exception:
			data = {"text": r.text}
			
	except requests.RequestException as e:
		status = 502
		data = {"error": str(e)}

	# 결과 파싱
	detect_count = 0
	malicious_score = 0
	country = None
	
	# raw_data 요약 저장용
	trimmed: Dict[str, Any] = {"status": status}
	
	if isinstance(data, dict) and status in (200, 201):
		# Quick scan 제출 성공
		job_id = data.get("job_id") or data.get("scan_id") or data.get("id")
		
		if job_id:
			trimmed.update({
				"scan_type": "quick_scan_submitted",
				"job_id": job_id,
				"message": data.get("message", "Quick scan submitted successfully"),
				"submitted_url": submit_url,
				"state": data.get("state"),
				"note": "Analysis submitted, results will be available later"
			})
		else:
			trimmed.update({
				"scan_type": "quick_scan_submitted", 
				"message": data.get("message", "Quick scan submitted"),
				"submitted_url": submit_url,
				"note": "Analysis submitted successfully"
			})
	else:
		# 에러 응답 처리
		if isinstance(data, dict):
			trimmed.update({
				"error": data.get("message", "Unknown error"),
				"details": data.get("validation_errors") or data.get("errors"),
				"submitted_url": submit_url if 'submit_url' in locals() else domain,
				"error_code": status
			})
		else:
			trimmed.update({
				"error": f"Request failed with status {status}",
				"response": str(data)[:500] if data else "No response data",
				"submitted_url": submit_url if 'submit_url' in locals() else domain
			})

	return {
		"status": status,
		"malicious_score": malicious_score,
		"detect_count": detect_count,
		"detect_vendor": "Hybrid-Analysis",
		"country": country,
		"dns": None,
		"raw_data": trimmed,
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

	# malicious 점수 및 detect_count 계산
	malicious_score = 0
	detect_count = 0
	country = None
	
	# raw_data를 필요한 필드만 축약해서 저장
	trimmed: Dict[str, Any] = {}
	if isinstance(data, dict):
		# 흔히 유용한 키들만 선별
		trimmed["total"] = data.get("total")
		trimmed["took"] = data.get("took")
		
		# 결과에서 malicious 점수 추출
		if isinstance(data.get("results"), list) and data["results"]:
			results = data["results"]
			malicious_count = 0
			total_results = len(results)
			
			# 각 결과에서 malicious 정보 수집
			for result in results:
				if isinstance(result, dict):
					stats = result.get("stats", {}) or {}
					# malicious나 maliciousCount가 있으면 카운트
					if stats.get("malicious") or stats.get("maliciousCount"):
						malicious_count += 1
					
					# verdicts에서 malicious 판정 확인
					verdicts = result.get("verdicts", {}) or {}
					if isinstance(verdicts, dict):
						for engine, verdict in verdicts.items():
							if isinstance(verdict, dict) and verdict.get("malicious"):
								malicious_count += 1
								break
			
			# malicious 비율로 점수 계산 (0-100)
			if total_results > 0:
				malicious_ratio = malicious_count / total_results
				malicious_score = int(malicious_ratio * 100)
			
			detect_count = malicious_count
			
			# 가장 최근 결과 하나만 요약 저장
			latest = results[0]
			page = latest.get("page", {}) if isinstance(latest, dict) else {}
			task = latest.get("task", {}) if isinstance(latest, dict) else {}
			stats = latest.get("stats", {}) if isinstance(latest, dict) else {}
			
			if page.get("country"):
				country = page.get("country")
				
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
			trimmed["malicious_summary"] = {
				"total_scans": total_results,
				"malicious_count": malicious_count,
				"malicious_ratio": malicious_ratio if total_results > 0 else 0
			}

	return {
		"status": status,
		"malicious_score": malicious_score,
		"detect_count": detect_count,
		"detect_vendor": "Urlscan",
		"country": country,
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
