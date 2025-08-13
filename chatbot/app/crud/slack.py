import asyncio
from app.crud.wiki import wiki_crawler
from app.crud.wiki_summarizer import wiki_summarizer


def handle_bobbot_command(user_id: str, channel_id: str, text: str) -> dict:
    """Handle /bobbot slash command"""
    
    # 추가 명령어가 있는 경우 처리
    if text.strip():
        command_parts = text.strip().split()
        command = command_parts[0].lower()
        
        if command == "help":
            help_message = """
📖 *사용 가능한 명령어:*
• `/bobbot` - 기본 인사
• `/bobbot help` - 도움말 보기
• `/bobbot bobwiki [이름]` - BOB 14기 위키에서 교육생 검색
• 더 많은 기능이 곧 추가될 예정입니다!
            """
            return {
                "response_type": "ephemeral",
                "text": help_message
            }
        
        elif command == "bobwiki":
            # bobwiki는 Socket Client에서 비동기로 처리
            # 여기서는 에러 메시지만 반환
            if len(command_parts) < 2:
                return {
                    "response_type": "ephemeral",
                    "text": "❌ 사용법: `/bobbot bobwiki [검색할 이름]`\n예시: `/bobbot bobwiki 고남현`"
                }
            
            # 정상적인 bobwiki 요청은 Socket Client에서 처리됨
            return {
                "response_type": "ephemeral",
                "text": "🔍 BOB 위키에서 검색을 시작합니다..."
            }
    
    # 기본 인사 메시지
    greeting_message = "안녕하세요! 👋\n저는 BOB 14기 보안 분석 챗봇입니다.\n도움이 필요하시면 언제든 말씀해주세요!"
    
    return {
        "response_type": "ephemeral",
        "text": greeting_message
    }


def handle_bobwiki_command(search_term: str) -> dict:
    """BOB 위키 검색 및 요약 처리"""
    try:
        # 검색 시작 알림
        initial_message = f"🔍 '{search_term}'에 대한 정보를 BOB 위키에서 검색 중입니다..."
        
        # 1. 위키에서 검색
        search_result = wiki_crawler.search_student(search_term)
        
        if not search_result.pages:
            return {
                "response_type": "ephemeral",
                "text": f"❌ '{search_term}'에 대한 정보를 BOB 위키에서 찾을 수 없습니다.\n\n다른 이름으로 다시 시도해보세요."
            }
        
        # 2. 검색된 페이지 정보
        pages_info = []
        for i, page in enumerate(search_result.pages[:3], 1):  # 최대 3개만 표시
            pages_info.append(f"{i}. [{page.title}]({page.url})")
        
        # 3. 요약 생성
        summary_result = wiki_summarizer.summarize_wiki_content(
            search_result.pages, 
            search_term
        )
        
        # 4. 결과 메시지 구성
        result_message = f"""
🎯 **'{search_term}' 검색 결과**

📊 **요약:**
{summary_result.summary}

📚 **참고 페이지 ({search_result.total_pages}개 발견):**
{chr(10).join(pages_info)}

💡 *더 자세한 정보는 위 링크를 참고하세요.*
        """
        
        return {
            "response_type": "ephemeral",
            "text": result_message
        }
        
    except Exception as e:
        error_message = f"❌ '{search_term}' 검색 중 오류가 발생했습니다.\n\n오류 내용: {str(e)}"
        return {
            "response_type": "ephemeral",
            "text": error_message
        }
