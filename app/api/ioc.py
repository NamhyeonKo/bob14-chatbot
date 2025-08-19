from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.crud import ioc as ioc_crud
from app.schemas import ioc as ioc_schema
from app.core import security
from app.database import db

router = APIRouter()

class IPRequest(BaseModel):
    ip: str = Field(..., description="분석할 IP 주소", example="8.8.8.8")

@router.post("/analyze/ip", response_model=ioc_schema.IoC)
def analyze_ip(
    request: IPRequest,
    db_session: Session = Depends(db.get_session),
    api_key: str = Depends(security.get_api_key)
):
    """IP 주소를 분석하여 악성 여부를 확인하고 결과를 DB에 저장합니다."""
    # 1. DB에 이미 분석 결과가 있는지 확인
    db_ioc = ioc_crud.get_ioc_by_value(db_session, value=request.ip)
    if db_ioc:
        return db_ioc
    # 2. DB에 없다면 VirusTotal API 호출
    vt_data = ioc_crud.analyze_ip_with_virustotal(request.ip)
    if not vt_data:
        raise HTTPException(status_code=404, detail="Could not get analysis from VirusTotal.")
    # 3. 분석 결과를 DB에 저장하고 반환
    return ioc_crud.create_ioc_report(db_session, ip=request.ip, vt_data=vt_data)
