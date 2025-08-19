from sqlalchemy import Column, DateTime, Integer, String, JSON, ForeignKey
from app.database import Base

class IoC(Base):
    __tablename__ = 'IoCTable'
    id = Column(Integer, primary_key=True, index=True)
    access_log_id = Column(String(64), ForeignKey('AccessLogTable.id'), nullable=False) # 외래 키 추가
    indicator_type = Column(String(50), nullable=False)
    indicator_value = Column(String(255), nullable=False, index=True)
    source = Column(String(100), nullable=False)
    malicious_count = Column(Integer, default=0)
    suspicious_count = Column(Integer, default=0)
    harmless_count = Column(Integer, default=0)
    reputation = Column(Integer, default=0)
    raw_data = Column(JSON)
    last_analyzed = Column(DateTime(timezone=True), nullable=False)