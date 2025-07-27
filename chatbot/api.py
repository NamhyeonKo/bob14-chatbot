from fastapi import Depends, FastAPI, HTTPException, Security
from sqlalchemy.orm import Session
import logging

import schema
import crud
from database import db

app = FastAPI()

@app.get("/")
async def root():
    logging.info("root api run")
    return {"message": "Hello World, Bobbot!"}

@app.post("/users/", response_model=schema.User)
def post_create_user(
    user: schema.UserCreate, 
    dbsession: Session = Depends(db.get_session),
    api_key: str = Security(crud.get_api_key)
):
    """
    새로운 사용자를 생성합니다 (API 키 필요).
    """
    if not all([user.username, user.email, user.password]):
        raise HTTPException(status_code=400, detail="Username, email, and password are required")
    
    if crud.get_user_by_email(dbsession, email=user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if crud.get_user_by_username(dbsession, username=user.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    
    new_user = crud.create_user(dbsession, user)
    if not new_user:
        raise HTTPException(status_code=500, detail="User creation failed")
    
    return new_user

@app.get("/users/{user_id}", response_model=schema.User)
def get_user(
    user_id: int, 
    dbsession: Session = Depends(db.get_session),
    api_key: str = Security(crud.get_api_key)
):
    """
    ID로 사용자 정보를 조회합니다 (API 키 필요).
    """
    db_user = crud.get_user_by_id(dbsession, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return db_user

@app.post("/users/login")
def post_login_user(user: schema.UserLogin, dbsession: Session = Depends(db.get_session)):
    """
    사용자 로그인을 처리합니다 (API 키 필요 없음).
    """
    db_user = crud.get_user_by_email(dbsession, email=user.email)
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    if not crud.verify_password(user.password, db_user.salt, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    return {"message": f"Login successful for user {db_user.username}"}