import asyncio
import re
import requests
from app.crud.wiki import wiki_crawler
from app.crud.wiki_summarizer import wiki_summarizer
from app.crud.cti import analyze_with_virustotal
from app.crud.ioc import analyze_ip_with_virustotal
from app.core.config import get_config


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
• `/bobbot ioc [도메인/IP]` - IoC 위험도 분석 (VirusTotal)

**IoC 분석 예시:**
• `/bobbot ioc naver.com` - 도메인 분석
• `/bobbot ioc 8.8.8.8` - IP 주소 분석

더 많은 기능이 곧 추가될 예정입니다!
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
        
        elif command == "ioc":
            # IoC 분석 명령어 처리
            if len(command_parts) < 2:
                return {
                    "response_type": "ephemeral",
                    "text": "❌ 사용법: `/bobbot ioc [도메인/IP주소]`\n\n**예시:**\n• `/bobbot ioc naver.com`\n• `/bobbot ioc 8.8.8.8`"
                }
            
            ioc_value = command_parts[1]
            return handle_ioc_command(ioc_value)
    
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


def handle_ioc_command(ioc_value: str) -> dict:
    """IoC 분석 처리 함수"""
    try:
        # 1. 입력값 검증 및 정리
        cleaned_ioc = ioc_value.strip()
        
        # 2. 도메인/IP 형식 검증
        ioc_type = get_ioc_type(cleaned_ioc)
        if not ioc_type:
            return {
                "response_type": "ephemeral",
                "text": f"❌ 올바르지 않은 형식입니다: `{cleaned_ioc}`\n\n**지원 형식:**\n• 도메인: example.com, sub.example.com\n• IP 주소: 192.168.1.1, 8.8.8.8\n\n**사용법:** `/bobbot ioc naver.com`"
            }
        
        # 3. IP와 도메인에 따라 다른 API 호출
        if ioc_type == "ip":
            vt_result = analyze_ip_with_virustotal_for_slack(cleaned_ioc)
        else:  # domain
            # CTI 형식을 슬랙 형식으로 변환
            cti_result = analyze_with_virustotal(cleaned_ioc)
            vt_result = {
                "status": cti_result.get("raw_data", {}).get("status", cti_result.get("status", 500)),
                "reputation": cti_result.get("malicious_score", 0),
                "stats": cti_result.get("raw_data", {}).get("stats", {}),
                "country": cti_result.get("country"),
                "as_owner": cti_result.get("raw_data", {}).get("as_owner"),
            }
        
        # 4. 결과 포맷팅
        formatted_result = format_ioc_result(cleaned_ioc, vt_result, ioc_type)
        
        return {
            "response_type": "ephemeral",
            "text": formatted_result
        }
        
    except Exception as e:
        return {
            "response_type": "ephemeral",
            "text": f"❌ IoC 분석 중 오류가 발생했습니다: {str(e)}"
        }


def get_ioc_type(ioc_value: str) -> str:
    """IoC 타입 판별 (ip 또는 domain 또는 None)"""
    # IP 주소 형식 검증
    ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    
    # 도메인 형식 검증 (간단한 패턴)
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    
    if re.match(ip_pattern, ioc_value):
        return "ip"
    elif re.match(domain_pattern, ioc_value):
        return "domain"
    else:
        return None


def analyze_ip_with_virustotal_for_slack(ip: str) -> dict:
    """슬랙용 IP 분석 함수 (CTI 형식과 맞춤)"""
    try:
        from app.crud.ioc import VT_API_KEY
        import requests
        
        if not VT_API_KEY:
            return {
                "status": 401,
                "error": "VirusTotal API key is not configured"
            }
        
        # 직접 VirusTotal API 호출
        headers = {"x-apikey": VT_API_KEY.strip()}
        url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            status_code = response.status_code
            
            if status_code == 200:
                vt_data = response.json()
                attributes = vt_data.get("data", {}).get("attributes", {})
                stats = attributes.get("last_analysis_stats", {})
                
                return {
                    "status": 200,
                    "reputation": attributes.get("reputation", 0),
                    "stats": {
                        "malicious": stats.get("malicious", 0),
                        "suspicious": stats.get("suspicious", 0),
                        "harmless": stats.get("harmless", 0),
                        "undetected": stats.get("undetected", 0),
                    },
                    "country": attributes.get("country"),
                    "as_owner": attributes.get("as_owner"),
                }
            elif status_code == 404:
                return {
                    "status": 404,
                    "error": "IP address not found in VirusTotal database"
                }
            else:
                return {
                    "status": status_code,
                    "error": f"VirusTotal API error: {response.text[:200]}"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "status": 502,
                "error": f"Network error: {str(e)}"
            }
            
    except Exception as e:
        return {
            "status": 500,
            "error": str(e)
        }


def is_valid_ioc_format(ioc_value: str) -> bool:
    """IoC 형식 검증 (도메인 또는 IP) - 이전 버전과의 호환성"""
    return get_ioc_type(ioc_value) is not None


def format_ioc_result(ioc_value: str, vt_result: dict, ioc_type: str) -> str:
    """VirusTotal 결과를 슬랙 메시지 형식으로 포맷팅"""
    
    # API 호출 실패 처리
    status = vt_result.get("status", 0)
    if status != 200:
        if status == 404:
            return f"📊 **IoC 분석 결과: `{ioc_value}`** ({ioc_type.upper()})\n\n✅ **분석 완료**\n해당 {ioc_type}에 대한 정보가 VirusTotal에서 발견되지 않았습니다.\n이는 일반적으로 안전한 것으로 간주될 수 있습니다."
        elif status in [401, 403]:
            return f"📊 **IoC 분석 결과: `{ioc_value}`** ({ioc_type.upper()})\n\n❌ **API 인증 오류**\nVirusTotal API 키 설정을 확인해주세요."
        else:
            error_msg = vt_result.get("error", "알 수 없는 오류")
            return f"📊 **IoC 분석 결과: `{ioc_value}`** ({ioc_type.upper()})\n\n❌ **분석 실패**\n{error_msg}"
    
    # 분석 통계 추출
    stats = vt_result.get("stats", {})
    malicious = stats.get("malicious", 0)
    suspicious = stats.get("suspicious", 0)
    harmless = stats.get("harmless", 0)
    undetected = stats.get("undetected", 0)
    
    reputation = vt_result.get("reputation", 0)
    country = vt_result.get("country", "알 수 없음")
    as_owner = vt_result.get("as_owner", "알 수 없음")
    
    # 위험도 판정
    if malicious > 0:
        risk_level = "🔴 **높음**"
        risk_desc = f"{malicious}개 보안업체에서 악성으로 탐지"
    elif suspicious > 0:
        risk_level = "🟡 **중간**"
        risk_desc = f"{suspicious}개 보안업체에서 의심스러운 것으로 분류"
    elif harmless > 0:
        risk_level = "🟢 **낮음**"
        risk_desc = "대부분의 보안업체에서 안전한 것으로 분류"
    else:
        risk_level = "⚪ **알 수 없음**"
        risk_desc = "충분한 분석 데이터가 없음"
    
    # 결과 메시지 구성
    result_message = f"""📊 **IoC 분석 결과: `{ioc_value}`** ({ioc_type.upper()})

🛡️ **위험도:** {risk_level}
📝 **분석 요약:** {risk_desc}

📈 **상세 통계:**
• 🔴 악성: {malicious}개
• 🟡 의심: {suspicious}개  
• 🟢 안전: {harmless}개
• ⚪ 미탐지: {undetected}개

🌍 **추가 정보:**
• 평판 점수: {reputation}
• 국가: {country}"""

    if ioc_type == "ip" and as_owner != "알 수 없음":
        result_message += f"\n• AS 소유자: {as_owner}"

    result_message += "\n\n💡 *VirusTotal에서 제공된 정보입니다.*"

    return result_message
