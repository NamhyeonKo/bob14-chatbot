from pydantic import BaseModel
from datetime import datetime
from typing import Any, Optional

class CTIBase(BaseModel):
    search_item: str
    malicious_score: int
    detect_count: int
    detect_vendor: str
    tag: str
    country: str
    dns: str
    raw_data: Optional[Any] = None
    last_analyzed: datetime

class CTICreate(CTIBase):
    last_analyzed: datetime

class CTI(CTIBase):
    id: int
    last_analyzed: datetime

    class Config:
        from_attributes = True

