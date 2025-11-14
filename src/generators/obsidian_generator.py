"""
Obsidian 볼트 생성기 모듈
RSS 뉴스를 Obsidian 볼트에 최적화된 구조로 생성
"""

import os
import re
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Set

# 프로젝트 루트 경로 추가 (CLI 실행 시에만)
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

from src.core.database import DatabaseManager
from src.utils.config import config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class ObsidianGenerator:
    """Obsidian 볼트 생성기"""
    
    def __init__(self, db_manager: DatabaseManager = None, config_obj=None):
        """
        초기화
        
        Args:
            db_manager: 데이터베이스 매니저
            config_obj: 설정 객체
        """
        self.db_manager = db_manager or DatabaseManager(db_path=config.database_path)
        self.config = config_obj or config
        
        # Obsidian 설정
        self.vault_settings = {
            'useMarkdownLinks': True,
            'newFileLocation': 'current',
            'attachmentFolderPath': 'attachments',
            'promptForTaggingNewFiles': False,
            'tagPaneOrder': 'frequency'
        }
        
        logger.info("Obsidian generator initialized")
    
    def sanitize_filename(self, text: str) -> str:
        """파일명에 사용할 수 없는 문자 제거"""
        # Obsidian에서 지원하지 않는 문자들
        invalid_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(invalid_chars, '_', text)
        
        # 연속된 공백을 하나로 변경
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        # 길이 제한 (Windows 파일시스템 고려)
        return sanitized[:200].strip()
    
    def create_obsidian_link(self, text: str, alias: str = None) -> str:
        """Obsidian 내부 링크 생성"""
        if alias:
            return f"[[{text}|{alias}]]"
        return f"[[{text}]]"
    
    def create_tag(self, text: str, nested: bool = True) -> str:
        """Obsidian 태그 생성"""
        # 태그에 사용할 수 없는 문자 제거
        clean_text = re.sub(r'[^a-zA-Z0-9가-힣_-]', '', text)
        
        if nested:
            # 중첩 태그 (예: #뉴스/정치/국내)
            return f"#{clean_text}"
        else:
            # 평면 태그 (예: #뉴스_정치_국내)
            return f"#{clean_text}"
    
    def extract_keywords(self, text: str, limit: int = 10) -> List[str]:
        """키워드 추출 (한글/영문 최적화)"""
        # 한글, 영문만 추출 (최소 2글자 이상)
        korean_words = re.findall(r'[가-힣]{2,}', text)
        english_words = re.findall(r'[a-zA-Z]{3,}', text.lower())
        
        # 한글 불용어
        korean_stops = {'것이', '경우', '때문', '그런', '이런', '저런', '그리고', '하지만', '그러나', 
                       '따라서', '그래서', '또한', '뿐만', '아니라', '대해', '대한', '관련', '통해',
                       '위해', '때문에', '경우에', '것을', '것은', '것의', '되는', '된다', '한다',
                       '있다', '없다', '이다', '아니다', '같다', '다른', '새로운', '많은', '적은'}
        
        # 영문 불용어  
        english_stops = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 
                        'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its',
                        'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'man', 'own',
                        'say', 'she', 'too', 'use', 'way', 'will', 'with', 'that', 'this', 'have',
                        'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time', 'very',
                        'when', 'come', 'here', 'just', 'like', 'long', 'make', 'many', 'over', 'such',
                        'take', 'than', 'them', 'well', 'were'}
        
        # 빈도 계산
        word_freq = defaultdict(int)
        
        # 한글 단어 처리
        for word in korean_words:
            if word not in korean_stops and len(word) >= 2:
                word_freq[word] += 1
        
        # 영문 단어 처리
        for word in english_words:
            if word not in english_stops and len(word) >= 3:
                word_freq[word] += 1
        
        # 상위 키워드 반환 (빈도순)
        keywords = [word for word, _ in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:limit]]
        
        # 키워드가 없을 경우 기본값
        if not keywords:
            keywords = ['뉴스', '기사']
            
        return keywords
    
    def format_date(self, timestamp: int) -> str:
        """날짜 포맷팅"""
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime('%Y-%m-%d')
        except (ValueError, OSError):
            return datetime.now().strftime('%Y-%m-%d')
    
    def format_datetime(self, timestamp: int) -> str:
        """날짜시간 포맷팅"""
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime('%Y-%m-%d %H:%M')
        except (ValueError, OSError):
            return datetime.now().strftime('%Y-%m-%d %H:%M')
    
    def create_daily_note(self, articles: List[Dict], date_str: str, tag_system: str = 'nested') -> str:
        """일간 노트 생성"""
        content = []
        
        # YAML 프론트매터
        content.append("---")
        content.append(f"date: {date_str}")
        content.append("type: daily-news")
        content.append("tags:")
        content.append("  - 뉴스")
        content.append("  - 일간정리")
        content.append(f"  - {date_str}")
        content.append("---")
        content.append("")
        
        # 제목
        content.append(f"# 📰 {date_str} 뉴스")
        content.append("")
        
        # 요약 정보
        total_articles = len(articles)
        sources = set(article['metadata']['source'] for article in articles)
        
        content.append("## 📊 요약")
        content.append(f"- **총 기사 수**: {total_articles}개")
        content.append(f"- **뉴스 소스**: {len(sources)}개")
        content.append(f"- **수집 날짜**: {date_str}")
        content.append("")
        
        # 뉴스 소스별 분류
        articles_by_source = defaultdict(list)
        for article in articles:
            source = article['metadata']['source']
            articles_by_source[source].append(article)
        
        # 목차 생성
        content.append("## 📑 목차")
        for source in sorted(articles_by_source.keys()):
            count = len(articles_by_source[source])
            content.append(f"- {self.create_obsidian_link(source)} ({count}개)")
        content.append("")
        
        # 소스별 기사 목록
        for source in sorted(articles_by_source.keys()):
            source_articles = articles_by_source[source]
            content.append(f"## 📺 {source}")
            content.append("")
            
            for article in source_articles:
                metadata = article['metadata']
                title = metadata.get('title', 'No Title')
                url = metadata.get('url', '')
                date_time = self.format_datetime(metadata.get('date', 0))
                
                # 기사 제목을 링크로 (개별 기사 노트 생성 시)
                safe_title = self.sanitize_filename(title)
                article_link = self.create_obsidian_link(f"{date_str} - {safe_title}", title)
                
                content.append(f"### {article_link}")
                content.append(f"- **시간**: {date_time}")
                content.append(f"- **원문**: [링크]({url})")
                
                # 기사 미리보기 추가 (첫 200자)
                article_content = article.get('content', '')
                if article_content:
                    preview = article_content[:200].replace('\n', ' ').strip()
                    if len(article_content) > 200:
                        preview += "..."
                    content.append(f"- **미리보기**: {preview}")
                
                # 요약이 있는 경우 추가
                summary = metadata.get('summary', '')
                if summary and summary.strip():
                    content.append(f"- **요약**: {summary}")
                
                # 키워드 태그 (개선된 키워드)
                keywords = self.extract_keywords(article_content, limit=5)
                if keywords:
                    tags = [self.create_tag(kw, tag_system == 'nested') for kw in keywords]
                    content.append(f"- **키워드**: {' '.join(tags)}")
                
                content.append("")
        
        # 하단 탐색 링크
        content.append("---")
        content.append("## 📅 관련 노트")
        
        # 전날, 다음날 링크
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            prev_date = (dt - timedelta(days=1)).strftime('%Y-%m-%d')
            next_date = (dt + timedelta(days=1)).strftime('%Y-%m-%d')
            
            content.append(f"- 이전: {self.create_obsidian_link(prev_date)}")
            content.append(f"- 다음: {self.create_obsidian_link(next_date)}")
        except ValueError:
            pass
        
        content.append("")
        content.append(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return '\n'.join(content)
    
    def create_article_note(self, article: Dict, date_str: str, tag_system: str = 'nested') -> str:
        """개별 기사 노트 생성"""
        metadata = article['metadata']
        content_text = article.get('content', '')
        
        title = metadata.get('title', 'No Title')
        source = metadata.get('source', 'Unknown')
        url = metadata.get('url', '')
        summary = metadata.get('summary', '')
        authors = metadata.get('authors', '')
        date_time = self.format_datetime(metadata.get('date', 0))
        
        content = []
        
        # YAML 프론트매터
        content.append("---")
        content.append(f"title: \"{title}\"")
        content.append(f"source: {source}")
        content.append(f"date: {date_str}")
        content.append(f"datetime: {date_time}")
        content.append(f"url: {url}")
        content.append("type: news-article")
        
        # 태그 추가
        keywords = self.extract_keywords(content_text, limit=8)
        tags = ['뉴스', source] + keywords
        content.append("tags:")
        for tag in tags:
            content.append(f"  - {tag}")
        
        if authors:
            content.append(f"authors: {authors}")
        
        content.append("---")
        content.append("")
        
        # 기사 내용
        content.append(f"# {title}")
        content.append("")
        
        # 메타데이터 테이블
        content.append("| 속성 | 값 |")
        content.append("| --- | --- |")
        content.append(f"| **출처** | {self.create_obsidian_link(source)} |")
        content.append(f"| **날짜** | {date_time} |")
        if authors:
            content.append(f"| **저자** | {authors} |")
        content.append(f"| **원문링크** | [바로가기]({url}) |")
        content.append("")
        
        # 요약 (있는 경우)
        if summary and summary.strip():
            content.append("## 📝 요약")
            content.append(f"> {summary}")
            content.append("")
        
        # 키워드 (의미 있는 키워드만)
        if keywords:
            content.append("## 🏷️ 키워드")
            # 키워드를 카테고리로 분류
            korean_keywords = [kw for kw in keywords if re.match(r'[가-힣]', kw)]
            english_keywords = [kw for kw in keywords if re.match(r'[a-zA-Z]', kw)]
            
            if korean_keywords:
                content.append("**주요 키워드**: " + " | ".join([f"`{kw}`" for kw in korean_keywords[:5]]))
            if english_keywords:
                content.append("**영문 키워드**: " + " | ".join([f"`{kw}`" for kw in english_keywords[:3]]))
            
            # 태그 형태로도 제공
            content.append("")
            content.append("**태그**: " + ' '.join([self.create_tag(kw, tag_system == 'nested') for kw in keywords[:6]]))
            content.append("")
        
        # 본문 (구조화)
        if content_text:
            content.append("## 📰 본문")
            content.append("")
            
            # 본문을 문단별로 나누어 가독성 향상
            paragraphs = content_text.split('\n')
            formatted_paragraphs = []
            
            for para in paragraphs:
                para = para.strip()
                if para:
                    # 문장이 너무 길면 적절히 줄바꿈
                    if len(para) > 200:
                        # 마침표 기준으로 문장 분리
                        sentences = re.split(r'(?<=[.!?])\s+', para)
                        current_para = ""
                        for sentence in sentences:
                            if len(current_para + sentence) > 200 and current_para:
                                formatted_paragraphs.append(current_para.strip())
                                current_para = sentence
                            else:
                                current_para += " " + sentence if current_para else sentence
                        if current_para:
                            formatted_paragraphs.append(current_para.strip())
                    else:
                        formatted_paragraphs.append(para)
            
            # 문단들을 적절히 간격을 두고 배치
            for i, para in enumerate(formatted_paragraphs):
                content.append(para)
                # 긴 문단 뒤에는 빈 줄 추가
                if len(para) > 100 and i < len(formatted_paragraphs) - 1:
                    content.append("")
            content.append("")
        
        # 관련 링크
        content.append("## 📅 관련 노트")
        content.append(f"- 일간 정리: {self.create_obsidian_link(date_str)}")
        content.append(f"- 출처별 정리: {self.create_obsidian_link(f'출처 - {source}')}")
        content.append("")
        
        content.append(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return '\n'.join(content)
    
    def create_index_note(self, vault_path: Path, articles: List[Dict], structure: str = 'date') -> str:
        """인덱스 노트 생성"""
        content = []
        
        # YAML 프론트매터
        content.append("---")
        content.append("title: RSS 뉴스 아카이브")
        content.append("type: index")
        content.append("tags:")
        content.append("  - 뉴스")
        content.append("  - 인덱스")
        content.append("---")
        content.append("")
        
        # 제목
        content.append("# 📰 RSS 뉴스 아카이브")
        content.append("")
        
        # 통계
        total_articles = len(articles)
        sources = set(article['metadata']['source'] for article in articles)
        dates = set(self.format_date(article['metadata']['date']) for article in articles)
        
        content.append("## 📊 통계")
        content.append(f"- **총 기사 수**: {total_articles:,}개")
        content.append(f"- **뉴스 소스**: {len(sources)}개") 
        content.append(f"- **수집 기간**: {len(dates)}일")
        content.append("")
        
        # 날짜별 인덱스
        content.append("## 📅 날짜별 뉴스")
        articles_by_date = defaultdict(list)
        for article in articles:
            date_str = self.format_date(article['metadata']['date'])
            articles_by_date[date_str].append(article)
        
        for date_str in sorted(articles_by_date.keys(), reverse=True):
            count = len(articles_by_date[date_str])
            content.append(f"- {self.create_obsidian_link(date_str)} ({count}개)")
        content.append("")
        
        # 소스별 인덱스 (구조에 따라 다르게)
        content.append("## 📺 소스별 뉴스")
        articles_by_source = defaultdict(list)
        for article in articles:
            source = article['metadata']['source']
            articles_by_source[source].append(article)
        
        for source in sorted(articles_by_source.keys()):
            count = len(articles_by_source[source])
            # 구조에 따라 링크 방식 결정
            if structure == 'source':
                # source 구조에서는 '출처 - source' 형태의 파일이 생성됨
                link = self.create_obsidian_link(f'출처 - {source}', source)
            else:
                # date, category 구조에서는 단순히 소스명으로 링크 (실제 파일은 없을 수 있음)
                link = f"**{source}**"  # 링크 대신 굵은 글씨로 표시
            content.append(f"- {link} ({count}개)")
        content.append("")
        
        # 최근 업데이트
        content.append("## 🔄 최근 업데이트")
        content.append(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return '\n'.join(content)
    
    def create_vault_settings(self, vault_path: Path) -> None:
        """Obsidian 볼트 설정 파일 생성"""
        obsidian_dir = vault_path / '.obsidian'
        obsidian_dir.mkdir(exist_ok=True)
        
        # app.json 설정
        app_settings = {
            "legacyEditor": False,
            "livePreview": True,
            "showLineNumber": True,
            "spellcheck": True,
            "foldHeading": True,
            "foldIndent": True,
            "showFrontmatter": True
        }
        
        with open(obsidian_dir / 'app.json', 'w', encoding='utf-8') as f:
            json.dump(app_settings, f, ensure_ascii=False, indent=2)
        
        # core-plugins.json
        core_plugins = [
            "file-explorer",
            "global-search", 
            "switcher",
            "graph",
            "backlink",
            "tag-pane",
            "page-preview",
            "daily-notes",
            "templates",
            "note-composer",
            "command-palette",
            "markdown-importer",
            "outline",
            "word-count"
        ]
        
        with open(obsidian_dir / 'core-plugins.json', 'w', encoding='utf-8') as f:
            json.dump(core_plugins, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Obsidian vault settings created in {obsidian_dir}")
    
    def create_vault(self, vault_path: Path, vault_name: str, days: int = 7, 
                    structure: str = 'date', tag_system: str = 'nested',
                    single_file: bool = False, include_content: bool = False) -> bool:
        """
        Obsidian 볼트 생성
        
        Args:
            vault_path: 볼트 경로
            vault_name: 볼트 이름
            days: 조회할 일수
            structure: 폴더 구조 (date|category|source)
            tag_system: 태그 시스템 (flat|nested)  
            single_file: 단일 파일로 생성 여부
            include_content: 전체 내용 포함 여부
        
        Returns:
            성공 여부
        """
        try:
            logger.info(f"Creating Obsidian vault: {vault_name}")
            
            # 볼트 디렉토리 생성
            vault_path.mkdir(parents=True, exist_ok=True)
            
            # 최근 기사 가져오기
            articles = self.db_manager.get_recent_articles(days=days)
            if not articles:
                logger.warning("No articles found")
                return False
            
            logger.info(f"Processing {len(articles)} articles")
            
            # Obsidian 설정 파일 생성
            self.create_vault_settings(vault_path)
            
            if single_file:
                # 단일 파일로 생성
                self._create_single_file_vault(vault_path, articles, tag_system, include_content)
            else:
                # 구조화된 볼트 생성
                if structure == 'date':
                    self._create_date_structure_vault(vault_path, articles, tag_system, include_content)
                elif structure == 'source':
                    self._create_source_structure_vault(vault_path, articles, tag_system, include_content)
                elif structure == 'category':
                    self._create_category_structure_vault(vault_path, articles, tag_system, include_content)
            
            # 인덱스 노트 생성 (구조별 차이 반영)
            index_content = self.create_index_note(vault_path, articles, structure)
            with open(vault_path / 'README.md', 'w', encoding='utf-8') as f:
                f.write(index_content)
            
            logger.info(f"Obsidian vault created successfully: {vault_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create Obsidian vault: {e}")
            return False
    
    def _create_date_structure_vault(self, vault_path: Path, articles: List[Dict], 
                                   tag_system: str, include_content: bool) -> None:
        """날짜별 구조로 볼트 생성"""
        # 날짜별로 분류
        articles_by_date = defaultdict(list)
        for article in articles:
            date_str = self.format_date(article['metadata']['date'])
            articles_by_date[date_str].append(article)
        
        # 날짜별 폴더 및 노트 생성
        for date_str, date_articles in articles_by_date.items():
            # 년/월 폴더 구조
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            year_month_dir = vault_path / f"{dt.year}" / f"{dt.month:02d}"
            year_month_dir.mkdir(parents=True, exist_ok=True)
            
            # 일간 노트 생성
            daily_content = self.create_daily_note(date_articles, date_str, tag_system)
            with open(year_month_dir / f"{date_str}.md", 'w', encoding='utf-8') as f:
                f.write(daily_content)
            
            # 개별 기사 노트 생성 (옵션)
            if include_content:
                article_dir = year_month_dir / f"{date_str}-articles"
                article_dir.mkdir(exist_ok=True)
                
                for article in date_articles:
                    title = article['metadata'].get('title', 'No Title')
                    safe_title = self.sanitize_filename(title)
                    # 파일명에 날짜 프리픽스 추가 (링크 일치성 확보)
                    filename = f"{date_str} - {safe_title}.md"
                    article_content = self.create_article_note(article, date_str, tag_system)
                    
                    with open(article_dir / filename, 'w', encoding='utf-8') as f:
                        f.write(article_content)
    
    def _create_source_structure_vault(self, vault_path: Path, articles: List[Dict], 
                                     tag_system: str, include_content: bool) -> None:
        """소스별 구조로 볼트 생성"""
        # 소스별로 분류
        articles_by_source = defaultdict(list)
        for article in articles:
            source = article['metadata']['source']
            articles_by_source[source].append(article)
        
        # 소스별 폴더 및 노트 생성
        for source, source_articles in articles_by_source.items():
            source_dir = vault_path / "sources" / source
            source_dir.mkdir(parents=True, exist_ok=True)
            
            # 소스별 인덱스 노트
            source_content = self._create_source_index(source, source_articles, tag_system)
            with open(source_dir / f"{source}-index.md", 'w', encoding='utf-8') as f:
                f.write(source_content)
            
            # 개별 기사 노트
            if include_content:
                for article in source_articles:
                    date_str = self.format_date(article['metadata']['date'])
                    title = article['metadata'].get('title', 'No Title')
                    safe_title = self.sanitize_filename(title)
                    # 파일명에 날짜 프리픽스 추가
                    filename = f"{date_str} - {safe_title}.md"
                    article_content = self.create_article_note(article, date_str, tag_system)
                    
                    with open(source_dir / filename, 'w', encoding='utf-8') as f:
                        f.write(article_content)
    
    def _create_category_structure_vault(self, vault_path: Path, articles: List[Dict], 
                                       tag_system: str, include_content: bool) -> None:
        """카테고리별 구조로 볼트 생성"""
        # 키워드 기반 카테고리 자동 분류
        categories = {
            '정치': ['정치', '국회', '대통령', '정부', '정당', '선거'],
            '경제': ['경제', '금융', '주식', '기업', '산업', '무역'],
            '사회': ['사회', '교육', '의료', '복지', '문화', '종교'],
            '국제': ['국제', '외교', '해외', '글로벌', '세계'],
            '기술': ['기술', '과학', 'IT', 'AI', '인공지능', '혁신'],
            '스포츠': ['스포츠', '축구', '야구', '농구', '올림픽'],
            '연예': ['연예', '가수', '배우', '드라마', '영화', '음악'],
        }
        
        # 기사를 카테고리별로 분류
        articles_by_category = defaultdict(list)
        for article in articles:
            content_text = article.get('content', '') + article['metadata'].get('title', '')
            
            # 카테고리 매칭
            matched_category = '기타'
            for category, keywords in categories.items():
                if any(keyword in content_text for keyword in keywords):
                    matched_category = category
                    break
            
            articles_by_category[matched_category].append(article)
        
        # 카테고리별 폴더 및 노트 생성
        for category, category_articles in articles_by_category.items():
            category_dir = vault_path / "categories" / category
            category_dir.mkdir(parents=True, exist_ok=True)
            
            # 카테고리별 인덱스 노트
            category_content = self._create_category_index(category, category_articles, tag_system)
            with open(category_dir / f"{category}-index.md", 'w', encoding='utf-8') as f:
                f.write(category_content)
            
            # 개별 기사 노트
            if include_content:
                for article in category_articles:
                    date_str = self.format_date(article['metadata']['date'])
                    title = article['metadata'].get('title', 'No Title')
                    safe_title = self.sanitize_filename(title)
                    # 파일명에 날짜 프리픽스 추가
                    filename = f"{date_str} - {safe_title}.md"
                    article_content = self.create_article_note(article, date_str, tag_system)
                    
                    with open(category_dir / filename, 'w', encoding='utf-8') as f:
                        f.write(article_content)
    
    def _create_single_file_vault(self, vault_path: Path, articles: List[Dict], 
                                tag_system: str, include_content: bool) -> None:
        """단일 파일로 볼트 생성"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"RSS_News_{timestamp}.md"
        
        content = []
        content.append("---")
        content.append("title: RSS 뉴스 모음")
        content.append(f"date: {datetime.now().strftime('%Y-%m-%d')}")
        content.append("type: news-collection")
        content.append("tags: [뉴스, 모음집]")
        content.append("---")
        content.append("")
        content.append(f"# 📰 RSS 뉴스 모음 ({len(articles)}개)")
        content.append("")
        
        # 날짜별로 정리
        articles_by_date = defaultdict(list)
        for article in articles:
            date_str = self.format_date(article['metadata']['date'])
            articles_by_date[date_str].append(article)
        
        for date_str in sorted(articles_by_date.keys(), reverse=True):
            content.append(f"## 📅 {date_str}")
            content.append("")
            
            for article in articles_by_date[date_str]:
                metadata = article['metadata']
                title = metadata.get('title', 'No Title')
                source = metadata.get('source', 'Unknown')
                url = metadata.get('url', '')
                
                content.append(f"### [{title}]({url})")
                content.append(f"**출처**: {source}")
                
                if include_content and article.get('content'):
                    content.append("")
                    content.append(article['content'])
                
                content.append("")
                content.append("---")
                content.append("")
        
        # 파일 저장
        with open(vault_path / filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
    
    def _create_source_index(self, source: str, articles: List[Dict], tag_system: str) -> str:
        """소스별 인덱스 생성"""
        content = []
        content.append("---")
        content.append(f"title: {source} 뉴스")
        content.append(f"source: {source}")
        content.append("type: source-index") 
        content.append("tags: [뉴스, 소스별정리]")
        content.append("---")
        content.append("")
        content.append(f"# 📺 {source}")
        content.append("")
        content.append(f"**총 기사 수**: {len(articles)}개")
        content.append("")
        
        # 날짜별 분류
        articles_by_date = defaultdict(list)
        for article in articles:
            date_str = self.format_date(article['metadata']['date'])
            articles_by_date[date_str].append(article)
        
        for date_str in sorted(articles_by_date.keys(), reverse=True):
            content.append(f"## {date_str}")
            for article in articles_by_date[date_str]:
                title = article['metadata'].get('title', 'No Title')
                url = article['metadata'].get('url', '')
                content.append(f"- [{title}]({url})")
            content.append("")
        
        return '\n'.join(content)
    
    def _create_category_index(self, category: str, articles: List[Dict], tag_system: str) -> str:
        """카테고리별 인덱스 생성"""
        content = []
        content.append("---")
        content.append(f"title: {category} 뉴스")
        content.append(f"category: {category}")
        content.append("type: category-index")
        content.append("tags: [뉴스, 카테고리별정리]")
        content.append("---")
        content.append("")
        content.append(f"# 📂 {category}")
        content.append("")
        content.append(f"**총 기사 수**: {len(articles)}개")
        content.append("")
        
        # 최신 기사부터 정렬
        sorted_articles = sorted(articles, key=lambda x: x['metadata']['date'], reverse=True)
        
        for article in sorted_articles:
            metadata = article['metadata']
            title = metadata.get('title', 'No Title')
            source = metadata.get('source', 'Unknown')
            url = metadata.get('url', '')
            date_str = self.format_date(metadata.get('date', 0))
            
            content.append(f"## [{title}]({url})")
            content.append(f"**출처**: {source} | **날짜**: {date_str}")
            content.append("")
        
        return '\n'.join(content)


def main():
    """CLI 메인 함수"""
    import sys
    import argparse
    from pathlib import Path
    
    # 프로젝트 루트를 Python 경로에 추가
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    def parse_arguments():
        """명령줄 인수 파싱"""
        parser = argparse.ArgumentParser(description='RSS 뉴스를 Obsidian 호환 마크다운으로 변환')
        parser.add_argument('--days', type=int, default=7, help='최근 N일 기사만 포함 (기본값: 7)')
        parser.add_argument('--output', type=str, help='출력 디렉토리 경로 (기본값: ./output/obsidian)')
        parser.add_argument('--vault-name', type=str, default='RSS-News', help='Obsidian 볼트 이름')
        parser.add_argument('--structure', type=str, choices=['date', 'category', 'source'], 
                           default='date', help='폴더 구조 방식 (기본값: date)')
        parser.add_argument('--tag-system', type=str, choices=['flat', 'nested'], 
                           default='nested', help='태그 시스템 (기본값: nested)')
        parser.add_argument('--single-file', action='store_true', help='단일 파일로 생성')
        parser.add_argument('--exclude-content', action='store_true', help='기사 내용 제외 (기본값: 내용 포함)')
        return parser.parse_args()

    try:
        from src.core.database import DatabaseManager
        from src.utils.config import Config
        from src.utils.logger import setup_logger
        
        logger = setup_logger(__name__)
        args = parse_arguments()
        
        logger.info("📝 Obsidian 마크다운 생성을 시작합니다...")
        
        # 설정 로드
        config = Config()
        
        # 데이터베이스 초기화
        db_manager = DatabaseManager(
            db_path=config.get('database.path', './data/chroma_db'),
            collection_name=config.get('database.collection_name', 'news_articles')
        )
        
        # Obsidian 생성기 초기화
        obsidian_gen = ObsidianGenerator(db_manager=db_manager)
        
        # 출력 디렉토리 결정
        if args.output:
            output_dir = Path(args.output)
        else:
            output_dir = project_root / 'output' / 'obsidian' / args.vault_name
        
        # 출력 디렉토리 생성
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Obsidian 볼트 생성
        success = obsidian_gen.create_vault(
            vault_path=output_dir,
            vault_name=args.vault_name,
            days=args.days,
            structure=args.structure,
            tag_system=args.tag_system,
            single_file=args.single_file,
            include_content=not args.exclude_content  # 기본값 True, --exclude-content 시 False
        )
        
        if success:
            logger.info(f"✅ Obsidian 볼트 생성 완료: {output_dir}")
            print(f"📁 Obsidian 볼트 경로: {output_dir}")
            print(f"💡 Obsidian에서 '{output_dir}' 폴더를 볼트로 열어보세요!")
            
            # 볼트 통계 정보
            vault_files = list(output_dir.rglob("*.md"))
            print(f"📊 생성된 마크다운 파일: {len(vault_files)}개")
        else:
            logger.error("❌ Obsidian 볼트 생성 실패")
            sys.exit(1)
        
    except ImportError as e:
        print(f"❌ 모듈 import 오류: {e}")
        print("필요한 종속성을 설치하세요: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()