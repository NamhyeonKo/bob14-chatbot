from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core import security
from app.database import db
from app.schemas.cti import CTI
from app.crud.cti import upsert_cti_results


router = APIRouter()


class DomainRequest(BaseModel):
    domain: str = Field(..., description="분석할 도메인", example="example.com")


@router.post("/analyze/domain", response_model=list[CTI])
def analyze_domain(
    request: DomainRequest,
    db_session: Session = Depends(db.get_session),
    api_key: str = Depends(security.get_api_key),
):
    try:
        results = upsert_cti_results(db_session, domain=request.domain)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CTI 분석 중 오류: {e}")


 

