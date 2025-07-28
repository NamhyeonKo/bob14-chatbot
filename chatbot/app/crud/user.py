import hashlib
import os
import base64
from sqlalchemy.orm import Session
from typing import Optional
from app.models.user import User
from app.schemas import user as user_schema

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
