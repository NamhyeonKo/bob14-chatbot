from pydantic import BaseModel
from datetime import datetime
from typing import Any, Optional

class IoCBase(BaseModel):
    access_log_id: str
    indicator_type: str
    indicator_value: str
    source: str
    malicious_count: int
    suspicious_count: int
    harmless_count: int
    reputation: int
    raw_data: Optional[Any] = None

class IoCCreate(IoCBase):
    last_analyzed: datetime

class IoC(IoCBase):
    id: int
    last_analyzed: datetime

    class Config:
        from_attributes = True