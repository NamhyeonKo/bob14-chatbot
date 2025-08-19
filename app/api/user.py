from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Any

from app.crud import user as user_crud
from app.crud import ioc as ioc_crud

from app.schemas import user as user_schema
from app.core import security
from app.database import db

router = APIRouter()

@router.post("/", response_model=user_schema.User)
def create_user(
    user: user_schema.UserCreate,
    db_session: Session = Depends(db.get_session),
    api_key: str = Depends(security.get_api_key)
) -> Any:
    """Create new user"""
    if user_crud.get_user_by_email(db_session, email=user.email):
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    if user_crud.get_user_by_username(db_session, username=user.username):
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    return user_crud.create_user(db_session, user=user)

@router.get("/{user_id}", response_model=user_schema.User)
def get_user(
    user_id: int,
    request: Request, # Request 객체 주입
    db_session: Session = Depends(db.get_session),
    api_key: str = Depends(security.get_api_key)
) -> Any:
    """ID로 사용자를 조회하고, 접근 IP에 대한 IoC 분석을 수행합니다."""
    client_ip = request.client.host
    
    db_user = user_crud.get_user_by_id(db_session, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 1. IP 주소를 포함하여 접근 로그 생성
    access_log = user_crud.create_access_log(db_session, user_id=user_id, ip_address=client_ip)
    
    # 2. 해당 IP에 대한 IoC 분석 수행 (이미 분석된 IP는 생략 가능)
    existing_ioc = ioc_crud.get_ioc_by_value(db_session, value=client_ip)
    if not existing_ioc:
        vt_data = ioc_crud.analyze_ip_with_virustotal(client_ip)
        if vt_data:
            ioc_crud.create_ioc_report(
                db=db_session, 
                access_log_id=access_log.id,
                ip=client_ip,
                vt_data=vt_data
            )
            
    return db_user
