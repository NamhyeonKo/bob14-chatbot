from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core import security
from app.database import db
from app.crud import cti as cti_crud
from app.schemas import cti as cti_schema

router = APIRouter()


class CTISearchRequest(BaseModel):
	item: str = Field(..., description="IP / 파일 해시 / 도메인 중 하나", example="8.8.8.8")


@router.post("/analyze", response_model=cti_schema.CTI)
def analyze_cti(
	request: CTISearchRequest,
	db_session: Session = Depends(db.get_session),
	api_key: str = Depends(security.get_api_key)
):
	existing = cti_crud.get_cti_by_search_item(db_session, request.item)
	if existing:
		return existing
	return cti_crud.analyze_and_create(db_session, request.item)

