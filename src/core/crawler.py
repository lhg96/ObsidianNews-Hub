"""
RSS Crawler Core Module
RSS 피드 크롤링 및 기사 추출 기능
"""

import feedparser
import requests
from newspaper import Article
from datetime import datetime
from dateutil import parser
from typing import Dict, List, Optional
import csv
import nltk
import time

from src.utils.config import config
from src.utils.logger import setup_logger
from src.core.database import DatabaseManager

logger = setup_logger(__name__)

# NLTK 데이터 다운로드 (필요시)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class RSSCrawler:
    """RSS 크롤러 메인 클래스"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        """
        RSS 크롤러 초기화
        
        Args:
            db_manager: 데이터베이스 매니저 인스턴스
        """
        self.db_manager = db_manager or DatabaseManager(db_path=config.database_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AI-RSSCrawler/1.0'
        })
        
        # 설정값 로드
        self.timeout = config.timeout
        self.retry_count = config.retry_count
        self.delay = config.get('crawler.delay_between_requests', 1.0)
        
        logger.info("RSS Crawler initialized")
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """날짜 문자열 파싱"""
        try:
            return parser.parse(date_str)
        except Exception:
            return None
    
    def fetch_article_content(self, url: str, entry_published: str = None) -> Optional[Dict]:
        """
        개별 기사 내용 추출
        
        Args:
            url: 기사 URL
            entry_published: RSS 피드의 발행일
            
        Returns:
            기사 정보 딕셔너리 또는 None
        """
        logger.info(f"Fetching content from URL: {url}")
        
        try:
            article = Article(url)
            article.download()
            article.parse()

            content = article.text
            title = article.title

            # RSS 피드의 날짜를 우선적으로 사용
            publish_date = None
            if entry_published:
                publish_date = self.parse_date(entry_published)

            # RSS 피드의 날짜가 없거나 파싱 실패시 Article 객체의 발행일 사용
            if not publish_date:
                publish_date = article.publish_date

            # 둘 다 실패할 경우 현재 시간 사용
            if not publish_date:
                publish_date = datetime.now()

            authors = ', '.join(article.authors) if article.authors else ''

            logger.info(f"Content fetched successfully. Length: {len(content)} characters")
            
            return {
                'content': content,
                'title': title,
                'date': int(publish_date.timestamp()),
                'authors': authors,
                'url': url
            }
            
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {str(e)}")
            return None
    
    def process_feed(self, source: str, rss_url: str) -> int:
        """
        단일 RSS 피드 처리
        
        Args:
            source: 뉴스 소스 이름
            rss_url: RSS 피드 URL
            
        Returns:
            처리된 기사 수
        """
        logger.info(f"Processing feed: {source} - {rss_url}")
        
        try:
            # RSS 피드 파싱
            feed = feedparser.parse(rss_url)
            logger.info(f"Feed parsed. Number of entries: {len(feed.entries)}")
            
            processed_count = 0
            
            for entry in feed.entries:
                url = entry.link
                
                # 이미 처리된 URL인지 확인
                if self.db_manager.article_exists(url):
                    logger.info(f"Article already exists: {url}")
                    continue

                # RSS 피드의 발행일을 추출
                entry_published = entry.get('published')
                
                # 기사 내용 추출
                article_data = self.fetch_article_content(url, entry_published)
                if not article_data:
                    logger.warning(f"Skipping article due to content fetch failure: {url}")
                    continue

                # 추가 메타데이터 설정
                article_data.update({
                    'source': source,
                    'summary': entry.get('summary', ''),
                })

                # 데이터베이스에 저장
                if self.db_manager.store_article(article_data):
                    processed_count += 1
                
                # 요청 간 지연
                if self.delay > 0:
                    time.sleep(self.delay)
            
            logger.info(f"Processed {processed_count} new articles from {source}")
            return processed_count
            
        except Exception as e:
            logger.error(f"Error processing feed {source}: {str(e)}")
            return 0
    
    def load_feeds_from_csv(self, csv_path: str = 'rss_feeds.csv') -> List[Dict]:
        """
        CSV 파일에서 RSS 피드 설정 로드
        
        Args:
            csv_path: CSV 파일 경로
            
        Returns:
            피드 설정 리스트
        """
        feeds = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    feeds.append({
                        'source': row['source'],
                        'url': row['rss_url']
                    })
            logger.info(f"Loaded {len(feeds)} feeds from {csv_path}")
            
        except Exception as e:
            logger.error(f"Error loading feeds from CSV: {e}")
            
        return feeds
    
    def crawl_all_feeds(self, feed_configs: List[Dict] = None) -> Dict:
        """
        모든 피드 크롤링
        
        Args:
            feed_configs: 피드 설정 리스트 (없으면 CSV에서 로드)
            
        Returns:
            크롤링 결과 통계
        """
        if feed_configs is None:
            feed_configs = self.load_feeds_from_csv()
        
        if not feed_configs:
            logger.error("No feed configurations found")
            return {'total_feeds': 0, 'total_articles': 0}
        
        logger.info(f"Starting RSS feed crawling for {len(feed_configs)} feeds")
        
        total_articles = 0
        successful_feeds = 0
        
        for feed_config in feed_configs:
            source = feed_config['source']
            url = feed_config['url']
            
            try:
                article_count = self.process_feed(source, url)
                total_articles += article_count
                successful_feeds += 1
                
            except Exception as e:
                logger.error(f"Failed to process feed {source}: {e}")
        
        # 최종 통계
        stats = {
            'total_feeds': len(feed_configs),
            'successful_feeds': successful_feeds,
            'failed_feeds': len(feed_configs) - successful_feeds,
            'total_articles': total_articles,
            'collection_stats': self.db_manager.get_collection_stats()
        }
        
        logger.info(f"RSS feed crawling completed: {stats}")
        return stats
    
    def get_feed_health(self, rss_url: str) -> Dict:
        """
        RSS 피드 상태 확인
        
        Args:
            rss_url: RSS 피드 URL
            
        Returns:
            피드 상태 정보
        """
        try:
            start_time = time.time()
            response = requests.head(rss_url, timeout=self.timeout)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                # 실제 피드 파싱 시도
                feed = feedparser.parse(rss_url)
                
                return {
                    'status': 'healthy',
                    'response_time': response_time,
                    'status_code': response.status_code,
                    'entry_count': len(feed.entries),
                    'feed_title': getattr(feed.feed, 'title', 'Unknown'),
                    'last_updated': getattr(feed.feed, 'updated', 'Unknown')
                }
            else:
                return {
                    'status': 'error',
                    'response_time': response_time,
                    'status_code': response.status_code,
                    'error': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'response_time': 0,
                'status_code': 0,
                'error': str(e)
            }

def main():
    """메인 실행 함수"""
    logger.info("Starting RSS crawler main process")
    
    # 데이터베이스 매니저 초기화
    db_manager = DatabaseManager(db_path=config.database_path)
    
    # 크롤러 초기화
    crawler = RSSCrawler(db_manager)
    
    # 모든 피드 크롤링
    results = crawler.crawl_all_feeds()
    
    logger.info(f"Crawling completed: {results}")

if __name__ == "__main__":
    main()