from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class WikiSearchRequest(BaseModel):
    """위키 검색 요청"""
    search_term: str
    

class WikiPage(BaseModel):
    """위키 페이지 정보"""
    title: str
    url: str
    content: str
    author: Optional[str] = None
    last_modified: Optional[datetime] = None


class WikiSearchResult(BaseModel):
    """위키 검색 결과"""
    search_term: str
    pages: List[WikiPage]
    total_pages: int


class WikiSummaryRequest(BaseModel):
    """위키 요약 요청"""
    search_term: str
    content: str


class WikiSummaryResponse(BaseModel):
    """위키 요약 응답"""
    search_term: str
    summary: str
    source_pages: List[str]  # 요약에 사용된 페이지 URL들
