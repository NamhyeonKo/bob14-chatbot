from fastapi import APIRouter, HTTPException
from app.schemas.wiki import WikiSearchRequest, WikiSearchResult, WikiSummaryResponse
from app.crud.wiki import wiki_crawler
from app.crud.wiki_summarizer import wiki_summarizer

router = APIRouter()


@router.post("/search", response_model=WikiSearchResult)
async def search_wiki(request: WikiSearchRequest):
    """BOB 위키에서 학생 검색"""
    try:
        result = wiki_crawler.search_student(request.search_term)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"위키 검색 중 오류 발생: {str(e)}")


@router.post("/summarize", response_model=WikiSummaryResponse)
async def summarize_wiki(request: WikiSearchRequest):
    """BOB 위키 검색 후 요약"""
    try:
        # 1. 위키에서 검색
        search_result = wiki_crawler.search_student(request.search_term)
        
        if not search_result.pages:
            raise HTTPException(
                status_code=404, 
                detail=f"'{request.search_term}'에 대한 정보를 찾을 수 없습니다."
            )
        
        # 2. OpenAI로 요약 (사용자가 구현할 부분)
        summary_result = wiki_summarizer.summarize_wiki_content(
            search_result.pages, 
            request.search_term
        )
        
        return summary_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요약 생성 중 오류 발생: {str(e)}")


@router.get("/health")
async def wiki_health():
    """Wiki 서비스 헬스체크"""
    return {"status": "healthy", "service": "wiki-crawler"}
