from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
import hashlib
import base64
import os

import models
import schema
from config import conf

# --- Password Utilities ---
def hash_password(password: str) -> tuple[str, str]:
    """비밀번호와 함께 랜덤 salt를 생성하고 해시화합니다."""
    salt = os.urandom(16)
    hashed_password = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    salt_b64 = base64.b64encode(salt).decode('utf-8')
    hashed_password_b64 = base64.b64encode(hashed_password).decode('utf-8')
    return salt_b64, hashed_password_b64

def verify_password(password: str, salt_b64: str, hashed_b64: str) -> bool:
    """입력된 비밀번호를 저장된 salt로 해시화하여 기존 해시와 비교합니다."""
    salt = base64.b64decode(salt_b64)
    hashed_password_to_check = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return hashed_password_to_check == base64.b64decode(hashed_b64)

# --- User CRUD ---
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, user: schema.UserCreate) -> models.User:
    """새로운 사용자를 데이터베이스에 생성합니다."""
    salt, hashed_password = hash_password(user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        salt=salt,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# --- API Key Authentication ---
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    """헤더에서 API 키를 받아 유효성을 검사합니다."""
    if api_key == conf['api_key']:
        return api_key
    else:
        raise HTTPException(status_code=403, detail="Could not validate API Key")