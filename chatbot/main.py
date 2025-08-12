import uvicorn
from fastapi import FastAPI
from app.api import user
from app.api import ioc
from app.api import cti
from app.database import db, Base

app = FastAPI(title="Bobbot API")

# Include routers
app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(ioc.router, prefix="/ioc", tags=["ioc"])
app.include_router(cti.router, prefix="/cti", tags=["cti"])


@app.on_event("startup")
def on_startup():
    # Ensure CTI table exists
    try:
        Base.metadata.create_all(bind=db.engine)
    except Exception:
        # Silent fail to avoid blocking dev loop; DB issues will surface per-request
        pass

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True  # 개발 시에만 True로 설정
    )
