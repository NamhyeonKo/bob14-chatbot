import uvicorn
from fastapi import FastAPI
from app.api import user

app = FastAPI(title="Bobbot API")

# Include routers
app.include_router(user.router, prefix="/users", tags=["users"])

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True  # 개발 시에만 True로 설정
    )
