import hashlib
import os
import base64
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.models.user import User, AccessLog
from app.schemas import user as user_schema
from typing import Optional

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user: user_schema.UserCreate) -> User:
    salt = os.urandom(16)
    hashed_password = hashlib.pbkdf2_hmac(
        'sha256',
        user.password.encode(),
        salt,
        100000
    )
    
    db_user = User(
        email=user.email,
        username=user.username,
        salt=base64.b64encode(salt).decode(),
        hashed_password=base64.b64encode(hashed_password).decode()
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def verify_password(password: str, salt_b64: str, hashed_b64: str) -> bool:
    salt = base64.b64decode(salt_b64)
    stored_password = base64.b64decode(hashed_b64)
    password_to_check = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt,
        100000
    )
    return password_to_check == stored_password

def create_access_log(db: Session, user_id: int, ip_address: Optional[str] = None) -> AccessLog:
    """사용자 접근 로그를 IP 주소와 함께 생성하고 데이터베이스에 저장합니다."""
    access_time = datetime.now()
    data_to_hash = f"{access_time}{user_id}{ip_address}"
    access_id = hashlib.sha256(data_to_hash.encode()).hexdigest()

    db_access_log = AccessLog(
        id=access_id,
        user_id=user_id,
        ip_address=ip_address,
        access_time=access_time,
        action="get_user"
    )
    
    db.add(db_access_log)
    db.commit()
    db.refresh(db_access_log)
    return db_access_log