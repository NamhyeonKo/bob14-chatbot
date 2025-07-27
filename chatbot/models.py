from sqlalchemy import Column, DateTime, Integer, String, func
from database import Base

class User(Base):
    __tablename__ = 'UserTable'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    salt = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

class AccessLog(Base):
    __tablename__ = 'AccessLogTable'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    access_time = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    action = Column(String(50), nullable=False)