from sqlalchemy import Column, DateTime, Integer, String, JSON, ForeignKey
from app.database import Base

# Virustotal – 백신 엔진의 결과 멜웨어 탐지 결과
# Hybrid-analysis – 멜웨어 탐지 결과
# Urlscan – 도메인 생성 정보

class CTI(Base):
    __tablename__ = 'CTITable'
    id = Column(Integer, primary_key=True, index=True)
    search_item = Column(String(255), index=True)  # 검색 항목 (도메인, IP 등)
    malicious_score = Column(Integer, default=0)  # 악성 점수
    detect_count = Column(Integer, default=0)  # 탐지 횟수
    detect_vendor = Column(String(100))  # 탐지 벤더
    tag = Column(String(100))  # 태그
    country = Column(String(50))  # 국가
    dns = Column(String(255))  # DNS 정보
    raw_data = Column(JSON)  # 원시 데이터
    last_analyzed = Column(DateTime(timezone=True), nullable=False)  # 마지막 분석 시간