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
            
            # bobwiki 명령어인 경우 특별 처리
            if command["text"].strip().startswith("bobwiki"):
                # 즉시 "처리 중" 메시지 전송
                await respond(
                    text="🔍 BOB 위키에서 검색 중입니다... 잠시만 기다려주세요!",
                    response_type="ephemeral"
                )
                
                # 백그라운드에서 실제 처리 (비동기)
                import asyncio
                asyncio.create_task(self._handle_bobwiki_async(command, say))
            else:
                # 일반 명령어는 즉시 응답
                await respond(
                    text=response["text"],
                    response_type="ephemeral"
                )
        
        print("✅ Slack 명령어 등록 완료: /bobbot")
    
    async def _handle_bobwiki_async(self, command, say):
        """bobwiki 명령어 비동기 처리"""
        try:
            from app.crud.slack import handle_bobwiki_command
            
            # 검색어 추출
            text_parts = command["text"].strip().split()
            if len(text_parts) < 2:
                await say(
                    text="❌ 사용법: `/bobbot bobwiki [검색할 이름]`\n예시: `/bobbot bobwiki 고남현`",
                    channel=command["channel_id"]
                )
                return
            
            search_term = " ".join(text_parts[1:])
            
            # 실제 bobwiki 처리 (시간이 오래 걸리는 작업)
            result = handle_bobwiki_command(search_term)
            
            # 결과 전송
            await say(
                text=result["text"],
                channel=command["channel_id"]
            )
            
        except Exception as e:
            # 에러 발생 시 에러 메시지 전송
            await say(
                text=f"❌ 처리 중 오류가 발생했습니다: {str(e)}",
                channel=command["channel_id"]
            )
    
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
