"""
OpenAI API를 이용한 위키 내용 요약 서비스
"""

from typing import List
from app.schemas.wiki import WikiSummaryRequest, WikiSummaryResponse, WikiPage
from app.core.config import get_config

# LangChain 관련 임포트
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import logging

logging.basicConfig(level=logging.INFO)

class WikiSummarizer:
    def __init__(self):
        # conf.json에서 OpenAI API 키 가져오기
        config = get_config()
        self.api_key = config.get("OPENAI_API_KEY")
        
        # LangChain 모델 초기화 (속도 최적화)
        self.llm = ChatOpenAI(
            model='gpt-3.5-turbo',
            temperature=0.3,  # 낮은 temperature로 더 빠른 응답
            api_key=self.api_key,
            max_tokens=300,  # 토큰 수 제한으로 속도 개선
            timeout=15,  # 15초 타임아웃
            max_retries=1  # 재시도 횟수 제한
        )
        
        # 요약 프롬프트 템플릿 (간단하고 빠르게)
        self.summary_prompt = PromptTemplate.from_template(
            """BOB 14기 교육생 "{search_term}"의 정보를 3문장으로 요약해주세요:

{content}

조건: 웃기게"""
        )
        
        # 요약 체인 구성
        self.summary_chain = self.summary_prompt | self.llm
    
    def summarize_wiki_content(self, pages: List[WikiPage], search_term: str) -> WikiSummaryResponse:
        """
        위키 페이지들의 내용을 요약합니다.
        
        Args:
            pages: 크롤링된 위키 페이지들
            search_term: 검색어 (학생 이름)
        
        Returns:
            WikiSummaryResponse: 요약된 결과
        """
        
        # 1. 모든 페이지의 내용을 하나로 합치기
        combined_content = self._combine_page_contents(pages)
        
        # 2. LangChain을 이용한 요약 생성
        summary = self._generate_summary(combined_content, search_term)
        
        # 3. 응답 객체 생성
        source_urls = [page.url for page in pages]
        
        return WikiSummaryResponse(
            search_term=search_term,
            summary=summary,
            source_pages=source_urls
        )
    
    def _combine_page_contents(self, pages: List[WikiPage]) -> str:
        """페이지들의 내용을 합치기"""
        contents = []
        for page in pages:
            contents.append(f"=== {page.title} ===\n{page.content}\n")
        
        return "\n".join(contents)
    
    def _generate_summary(self, content: str, search_term: str) -> str:
        """
        OpenAI API를 이용한 실제 요약 생성
        """
        try:
            # 내용이 너무 길면 앞부분만 사용 (더 빠른 처리)
            if len(content) > 3000:
                content = content[:3000] + "\n\n... (내용 축약됨)"
            
            # LangChain 체인 실행
            response = self.summary_chain.invoke({
                "content": content,
                "search_term": search_term
            })
            
            summary = response.content
            logging.info(f"[요약 생성 완료] {search_term}: {len(summary)} 문자")
            
            return summary
            
        except Exception as e:
            logging.error(f"요약 생성 중 오류 발생: {str(e)}")
            return f"'{search_term}'에 대한 정보를 찾았지만 요약 생성 중 문제가 발생했습니다. 위키 링크를 직접 확인해주세요."


# 글로벌 요약기 인스턴스
wiki_summarizer = WikiSummarizer()
