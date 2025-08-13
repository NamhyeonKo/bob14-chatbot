import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from urllib.parse import urljoin, quote
import re
from app.schemas.wiki import WikiPage, WikiSearchResult


class BOBWikiCrawler:
    def __init__(self):
        self.base_url = "https://kitribob.wiki"
        self.search_url = "https://kitribob.wiki/wiki/14기_교육생"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def search_student(self, student_name: str) -> WikiSearchResult:
        """14기 교육생 페이지에서 특정 학생 검색"""
        try:
            print(f"🔍 '{student_name}' 검색 시작...")
            
            # 14기 교육생 메인 페이지 가져오기
            response = self.session.get(self.search_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 학생 페이지 링크 찾기
            student_links = self._find_student_links(soup, student_name)
            
            pages = []
            for link in student_links:
                page = self._crawl_page(link)
                if page:
                    pages.append(page)
            
            result = WikiSearchResult(
                search_term=student_name,
                pages=pages,
                total_pages=len(pages)
            )
            
            print(f"✅ 검색 완료: {len(pages)}개 페이지 발견")
            return result
            
        except Exception as e:
            print(f"❌ 검색 중 오류 발생: {e}")
            return WikiSearchResult(
                search_term=student_name,
                pages=[],
                total_pages=0
            )
    
    def _find_student_links(self, soup: BeautifulSoup, student_name: str) -> List[str]:
        """학생 이름과 관련된 링크들 찾기"""
        links = []
        
        # 1. 직접적인 이름 매칭으로 링크 찾기
        for link in soup.find_all('a', href=True):
            link_text = link.get_text(strip=True)
            href = link.get('href')
            
            # 학생 이름이 포함된 링크 찾기
            if student_name in link_text or student_name.replace(' ', '') in link_text.replace(' ', ''):
                full_url = urljoin(self.base_url, href)
                if full_url not in links:
                    links.append(full_url)
                    print(f"📄 발견된 링크: {link_text} -> {full_url}")
        
        # 2. 테이블에서 학생 정보 찾기
        for table in soup.find_all('table'):
            for row in table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                for cell in cells:
                    if student_name in cell.get_text(strip=True):
                        # 같은 행에서 링크 찾기
                        for link in row.find_all('a', href=True):
                            full_url = urljoin(self.base_url, link.get('href'))
                            if full_url not in links:
                                links.append(full_url)
                                print(f"📊 테이블에서 발견: {link.get_text(strip=True)} -> {full_url}")
        
        return links
    
    def _crawl_page(self, url: str) -> Optional[WikiPage]:
        """개별 페이지 크롤링"""
        try:
            print(f"📖 페이지 크롤링: {url}")
            
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 페이지 제목 추출
            title = self._extract_title(soup)
            
            # 페이지 내용 추출
            content = self._extract_content(soup)
            
            if not content.strip():
                print(f"⚠️ 빈 내용: {url}")
                return None
            
            page = WikiPage(
                title=title,
                url=url,
                content=content[:5000],  # 내용 길이 제한
                author=self._extract_author(soup)
            )
            
            print(f"✅ 크롤링 완료: {title} ({len(content)} 문자)")
            return page
            
        except Exception as e:
            print(f"❌ 페이지 크롤링 실패 ({url}): {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """페이지 제목 추출"""
        # h1 태그에서 제목 추출
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        
        # title 태그에서 제목 추출
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        
        return "제목 없음"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """페이지 내용 추출"""
        # 불필요한 요소들 제거
        for element in soup(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()
        
        # 메인 콘텐츠 영역 찾기
        content_selectors = [
            '#content',
            '.content',
            '#main',
            '.main',
            'article',
            '.wiki-content'
        ]
        
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                text = content_div.get_text(separator='\n', strip=True)
                if text.strip():
                    return self._clean_text(text)
        
        # 전체 body에서 텍스트 추출 (fallback)
        body = soup.find('body')
        if body:
            text = body.get_text(separator='\n', strip=True)
            return self._clean_text(text)
        
        return ""
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """작성자 정보 추출"""
        # 일반적인 작성자 표시 패턴들
        author_patterns = [
            '.author',
            '.creator',
            '[class*="author"]',
            '[class*="creator"]'
        ]
        
        for pattern in author_patterns:
            author_elem = soup.select_one(pattern)
            if author_elem:
                return author_elem.get_text(strip=True)
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """텍스트 정리"""
        # 연속된 공백/줄바꿈 정리
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r' +', ' ', text)
        
        # 앞뒤 공백 제거
        text = text.strip()
        
        return text

# 글로벌 크롤러 인스턴스
wiki_crawler = BOBWikiCrawler()
