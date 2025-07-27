from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

# 사용자 생성을 위한 스키마 (클라이언트로부터 입력받음)
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

# 사용자 로그인을 위한 스키마
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# 사용자 정보를 반환하기 위한 스키마 (비밀번호 관련 정보 제외)
class User(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True

class AccessLogCreate(BaseModel):
    user_id: int
    access_time: datetime
    action: str