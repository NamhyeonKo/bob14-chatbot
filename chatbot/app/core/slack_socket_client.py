import asyncio
import json
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from app.core.config import get_config
from app.crud.slack import handle_bobbot_command


class SlackSocketClient:
    def __init__(self):
        config = get_config()
        
        # Socket Mode용 앱 초기화
        self.app = AsyncApp(
            token=config.get("bot_user_oauth_token"),
            signing_secret=config.get("signing_secret")
        )
        
        # Socket Mode 핸들러 초기화
        self.handler = AsyncSocketModeHandler(
            self.app, 
            config.get("slack_api_key")  # App-level token 필요
        )
        
        # 슬래시 명령어 등록
        self.register_commands()
    
    def register_commands(self):
        """슬래시 명령어 등록"""
        
        @self.app.command("/bobbot")
        async def handle_bobbot_slash(ack, say, command, respond):
            # 즉시 응답 (3초 내에 응답해야 함)
            await ack()
            
            # 명령어 처리
            response = handle_bobbot_command(
                command["user_id"], 
                command["channel_id"], 
                command["text"]
            )
            
            # Socket Mode에서는 respond 사용 (ephemeral 메시지)
            await respond(
                text=response["text"],
                response_type="ephemeral"  # 본인만 볼 수 있는 메시지
            )
        
        print("✅ Slack 명령어 등록 완료: /bobbot")
    
    async def start(self):
        """소켓 모드 시작"""
        print("🚀 Slack Socket Mode 시작 중...")
        try:
            await self.handler.start_async()
            print("✅ Slack Socket Mode 연결 성공!")
        except Exception as e:
            print(f"❌ Slack Socket Mode 시작 실패: {e}")
            raise
    
    async def stop(self):
        """소켓 모드 중지"""
        print("🛑 Slack Socket Mode 중지 중...")
        try:
            await self.handler.close_async()
            print("✅ Slack Socket Mode 종료 완료")
        except Exception as e:
            print(f"❌ Slack Socket Mode 종료 실패: {e}")


# 글로벌 인스턴스
slack_socket_client = SlackSocketClient()
