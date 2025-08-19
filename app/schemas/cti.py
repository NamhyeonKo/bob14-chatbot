from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CTIBase(BaseModel):
    search_item: str = Field(..., description="조회 대상 도메인 또는 검색어")
    malicious_score: Optional[int] = 0
    detect_count: Optional[int] = 0
    detect_vendor: Optional[str] = None
    tag: str = Field(..., description="데이터 출처 식별자: virustotal|hybrid|urlscan 등")
    country: Optional[str] = None
    dns: Optional[str] = None
    raw_data: Optional[Any] = None


class CTICreate(CTIBase):
    last_analyzed: datetime


class CTI(CTIBase):
    id: int
    last_analyzed: datetime

    class Config:
        # pydantic v1/v2 호환 설정
        orm_mode = True
        from_attributes = True
