from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from app.crud import user as user_crud
from app.schemas import user as user_schema
from app.core import security
from app.database import db

router = APIRouter()

@router.post("/", response_model=user_schema.User)
def create_user(
    user: user_schema.UserCreate,
    db_session: Session = Depends(db.get_session),
    api_key: str = Depends(security.get_api_key)
) -> Any:
    """Create new user"""
    if user_crud.get_user_by_email(db_session, email=user.email):
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    return user_crud.create_user(db_session, user=user)

@router.get("/{user_id}", response_model=user_schema.User)
def get_user(
    user_id: int,
    db_session: Session = Depends(db.get_session),
    api_key: str = Depends(security.get_api_key)
) -> Any:
    """Get user by ID"""
    db_user = user_crud.get_user_by_id(db_session, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    user_crud.create_access_log(db_session, user_id=user_id)
    
    return db_user
