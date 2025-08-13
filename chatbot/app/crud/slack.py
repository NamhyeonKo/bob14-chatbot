def handle_bobbot_command(user_id: str, channel_id: str, text: str) -> dict:
    """Handle /bobbot slash command"""
    
    # 기본 인사 메시지
    greeting_message = "안녕하세요! 👋\n저는 BOB 14기 보안 분석 챗봇입니다.\n도움이 필요하시면 언제든 말씀해주세요!"
    
    # 추가 명령어가 있는 경우 처리 (향후 확장 가능)
    if text.strip():
        command_parts = text.strip().split()
        command = command_parts[0].lower()
        
        if command == "help":
            help_message = """
📖 *사용 가능한 명령어:*
• `/bobbot` - 기본 인사
• `/bobbot help` - 도움말 보기
• 더 많은 기능이 곧 추가될 예정입니다!
            """
            return {
                "response_type": "ephemeral",
                "text": help_message
            }
    
    return {
        "response_type": "ephemeral",
        "text": greeting_message
    }
