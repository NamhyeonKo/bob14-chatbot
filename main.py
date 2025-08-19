import uvicorn
import asyncio
from fastapi import FastAPI
from app.api import user
from app.api import ioc
from app.api import cti
from app.api import slack
from app.api import wiki
from app.database import db, Base

app = FastAPI(title="Bobbot API")

# Include routers
app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(ioc.router, prefix="/ioc", tags=["ioc"])
app.include_router(cti.router, prefix="/cti", tags=["cti"])
app.include_router(slack.router, prefix="/slack", tags=["slack"])
app.include_router(wiki.router, prefix="/wiki", tags=["wiki"])

# Global variable to store the socket client task
socket_task = None

@app.on_event("startup")
async def on_startup():
    global socket_task
    
    # Ensure CTI table exists
    try:
        Base.metadata.create_all(bind=db.engine)
    except Exception:
        # Silent fail to avoid blocking dev loop; DB issues will surface per-request
        pass
    
    # Socket Mode 시작 (백그라운드에서 실행)
    try:
        from app.core.slack_socket_client import slack_socket_client
        socket_task = asyncio.create_task(slack_socket_client.start())
        print("✅ Slack Socket Mode 태스크 생성됨")
    except Exception as e:
        print(f"❌ Slack Socket Mode 시작 실패: {e}")


@app.on_event("shutdown")
async def on_shutdown():
    global socket_task
    
    # Socket Mode 종료
    if socket_task:
        try:
            socket_task.cancel()
            from app.core.slack_socket_client import slack_socket_client
            await slack_socket_client.stop()
            print("✅ Slack Socket Mode 종료됨")
        except Exception as e:
            print(f"❌ Slack Socket Mode 종료 실패: {e}")


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True  # 개발 시에만 True로 설정
    )
