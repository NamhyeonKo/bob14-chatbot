import requests
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException
from typing import Optional

from app.core.config import conf
from app.models.ioc import IoC
from app.schemas.ioc import IoCCreate

VT_API_KEY = conf.get("virustotal_api_key")
VT_API_URL = "https://www.virustotal.com/api/v3/ip_addresses/"

def get_ioc_by_value(db: Session, value: str):
    """DB에서 기존 IoC 정보를 조회합니다."""
    return db.query(IoC).filter(IoC.indicator_value == value).first()


def analyze_ip_with_virustotal(ip: str):
    """VirusTotal API를 호출하여 IP 주소를 분석합니다."""
    if not VT_API_KEY:
        raise HTTPException(status_code=500, detail="VirusTotal API key is not configured.")
    
    headers = {"x-apikey": VT_API_KEY}
    url = f"{VT_API_URL}{ip}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 2xx 상태 코드가 아닐 경우 예외 발생
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch data from VirusTotal: {e}")


def create_ioc_report(db: Session, ip: str, vt_data: dict, access_log_id: Optional[str] = None) -> IoC:
    """분석 결과를 access_log_id와 연결하여 DB에 저장합니다."""
    
    attributes = vt_data.get("data", {}).get("attributes", {})
    stats = attributes.get("last_analysis_stats", {})

    ioc_data = IoCCreate(
        access_log_id=access_log_id,
        indicator_type="ip",
        indicator_value=ip,
        source="VirusTotal",
        malicious_count=stats.get("malicious", 0),
        suspicious_count=stats.get("suspicious", 0),
        harmless_count=stats.get("harmless", 0),
        reputation=attributes.get("reputation", 0),
        raw_data={},
        last_analyzed=datetime.now()
    )

    db_ioc = IoC(**ioc_data.model_dump())
    db.add(db_ioc)
    db.commit()
    db.refresh(db_ioc)
    return db_ioc