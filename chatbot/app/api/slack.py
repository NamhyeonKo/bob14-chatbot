from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def slack_health():
    """Health check endpoint for Slack bot"""
    return {"status": "healthy", "service": "slack-bot"}


@router.get("/test/bobbot")
async def test_bobbot_command(text: str = ""):
    """Test /bobbot command locally without Slack"""
    from app.crud.slack import handle_bobbot_command
    
    # 테스트용 더미 데이터
    test_user_id = "U123456789"
    test_channel_id = "C123456789"
    
    response = handle_bobbot_command(test_user_id, test_channel_id, text)
    
    return {
        "test_mode": True,
        "command": "/bobbot",
        "input_text": text,
        "response": response
    }
