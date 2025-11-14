"""
Database management for RSS Crawler using ChromaDB
"""

import chromadb
from chromadb.config import Settings
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from src.utils.config import config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class DatabaseManager:
    """ChromaDB 데이터베이스 관리 클래스"""
    
    def __init__(self, config_obj=None, db_path: str = None, collection_name: str = None):
        """
        데이터베이스 매니저 초기화
        
        Args:
            config_obj: Config 객체 (선택사항)
            db_path: ChromaDB 저장 경로
            collection_name: 컬렉션 이름
        """
        if config_obj:
            self.db_path = db_path or config_obj.database_path
            self.collection_name = collection_name or config_obj.collection_name
        else:
            self.db_path = db_path or config.database_path
            self.collection_name = collection_name or config.collection_name
        
        # ChromaDB 클라이언트 초기화
        self.client = chromadb.PersistentClient(path=self.db_path)
        logger.info(f"ChromaDB client initialized at {self.db_path}")
        
        # 컬렉션 가져오기 또는 생성
        self.collection = self.client.get_or_create_collection(name=self.collection_name)
        logger.info(f"Collection '{self.collection_name}' ready with {self.collection.count()} articles")
    
    def hash_url(self, url: str) -> str:
        """URL을 해시로 변환"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def article_exists(self, url: str) -> bool:
        """기사가 이미 존재하는지 확인"""
        url_hash = self.hash_url(url)
        result = self.collection.get(ids=[url_hash])
        return bool(result['ids'])
    
    def store_article(self, article_data: Dict) -> bool:
        """
        기사를 데이터베이스에 저장
        
        Args:
            article_data: 기사 정보 딕셔너리
            
        Returns:
            저장 성공 여부
        """
        try:
            url = article_data.get('url', '')
            if not url:
                logger.warning("Article URL is missing")
                return False
            
            url_hash = self.hash_url(url)
            
            # 이미 존재하는지 확인
            if self.article_exists(url):
                logger.info(f"Article already exists: {url}")
                return False
            
            # 메타데이터 구성
            metadata = {
                "url": url,
                "title": article_data.get('title', ''),
                "summary": article_data.get('summary', ''),
                "source": article_data.get('source', ''),
                "date": article_data.get('date', int(datetime.now().timestamp())),
                "authors": article_data.get('authors', '')
            }
            
            # ChromaDB에 저장
            self.collection.add(
                ids=[url_hash],
                documents=[article_data.get('content', '')],
                metadatas=[metadata]
            )
            
            logger.info(f"Article stored: {metadata['title']}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing article: {e}")
            return False
    
    def get_article_by_url(self, url: str) -> Optional[Dict]:
        """URL로 기사 조회"""
        try:
            url_hash = self.hash_url(url)
            result = self.collection.get(ids=[url_hash])
            
            if result['ids']:
                return {
                    'id': result['ids'][0],
                    'metadata': result['metadatas'][0],
                    'content': result['documents'][0]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting article by URL {url}: {e}")
            return None
    
    def search_articles(self, query: str, limit: int = 10, 
                       start_date: datetime = None, 
                       end_date: datetime = None) -> List[Dict]:
        """
        기사 검색
        
        Args:
            query: 검색 쿼리
            limit: 결과 개수 제한
            start_date: 시작 날짜
            end_date: 종료 날짜
            
        Returns:
            검색 결과 목록
        """
        try:
            where_clause = {}
            if start_date and end_date:
                where_clause = {
                    "$and": [
                        {"date": {"$gte": int(start_date.timestamp())}},
                        {"date": {"$lte": int(end_date.timestamp())}}
                    ]
                }
            elif start_date:
                where_clause = {"date": {"$gte": int(start_date.timestamp())}}
            elif end_date:
                where_clause = {"date": {"$lte": int(end_date.timestamp())}}

            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_clause if where_clause else None
            )
            
            articles = []
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    articles.append({
                        'id': results['ids'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'content': results['documents'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    })
            
            return articles
            
        except Exception as e:
            logger.error(f"Error searching articles: {e}")
            return []
    
    def get_recent_articles(self, days: int = 7, limit: int = 100) -> List[Dict]:
        """최근 기사 조회"""
        try:
            from datetime import timedelta
            recent_date = datetime.now() - timedelta(days=days)
            
            where_clause = {"date": {"$gte": int(recent_date.timestamp())}}
            
            results = self.collection.query(
                query_texts=[""],
                n_results=limit,
                where=where_clause
            )
            
            articles = []
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    articles.append({
                        'id': results['ids'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'content': results['documents'][0][i]
                    })
                    
            # 날짜순 정렬
            articles.sort(key=lambda x: x['metadata']['date'], reverse=True)
            return articles
            
        except Exception as e:
            logger.error(f"Error getting recent articles: {e}")
            return []
    
    def get_articles_by_source(self, source: str, limit: int = 50) -> List[Dict]:
        """특정 소스의 기사 조회"""
        try:
            where_clause = {"source": source}
            
            results = self.collection.query(
                query_texts=[""],
                n_results=limit,
                where=where_clause
            )
            
            articles = []
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    articles.append({
                        'id': results['ids'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'content': results['documents'][0][i]
                    })
                    
            # 날짜순 정렬
            articles.sort(key=lambda x: x['metadata']['date'], reverse=True)
            return articles
            
        except Exception as e:
            logger.error(f"Error getting articles by source {source}: {e}")
            return []
    
    def get_collection_stats(self) -> Dict:
        """컬렉션 통계 정보"""
        try:
            total_count = self.collection.count()
            
            # 최근 30일 기사 수
            from datetime import timedelta
            recent_date = datetime.now() - timedelta(days=30)
            recent_results = self.collection.query(
                query_texts=[""],
                n_results=total_count,
                where={"date": {"$gte": int(recent_date.timestamp())}}
            )
            recent_count = len(recent_results['ids'][0]) if recent_results['ids'] and recent_results['ids'][0] else 0
            
            return {
                'total_articles': total_count,
                'recent_articles_30d': recent_count,
                'collection_name': self.collection_name,
                'database_path': self.db_path
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
    
    def get_collection(self):
        """컬렉션 객체 반환"""
        return self.collection
    
    def save_article(self, article_data: dict) -> bool:
        """단일 기사를 데이터베이스에 저장"""
        try:
            # 필수 필드 확인
            required_fields = ['title', 'content', 'url', 'source']
            for field in required_fields:
                if not article_data.get(field):
                    logger.warning(f"Missing required field: {field}")
                    return False
            
            # 고유 ID 생성 (URL 기반)
            article_id = f"article_{hash(article_data['url'])}"
            
            # 메타데이터 준비
            metadata = {
                'title': article_data['title'],
                'url': article_data['url'],
                'source': article_data['source'],
                'published_date': article_data.get('published_date', ''),
                'category': article_data.get('category', 'General')
            }
            
            # 컬렉션에 추가
            self.collection.add(
                ids=[article_id],
                documents=[article_data['content']],
                metadatas=[metadata]
            )
            
            logger.info(f"Article saved: {article_data['title'][:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error saving article: {e}")
            return False
    
    def clear_collection(self) -> bool:
        """컬렉션 전체 삭제 (주의!)"""
        try:
            # 컬렉션 삭제 후 재생성
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
            logger.warning(f"Collection '{self.collection_name}' cleared")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            return False
    
    def get_sources(self) -> List[str]:
        """데이터베이스의 모든 고유 소스 목록 조회"""
        try:
            # 모든 문서의 메타데이터 조회
            results = self.collection.get()
            if not results or not results.get('metadatas'):
                return []
            
            # 고유 소스 추출
            sources = set()
            for metadata in results['metadatas']:
                if metadata and metadata.get('source'):
                    sources.add(metadata['source'])
            
            return sorted(list(sources))
            
        except Exception as e:
            logger.error(f"소스 목록 조회 오류: {e}")
            return []
    
    def get_article_sources(self) -> List[str]:
        """기사 소스 목록 조회"""
        return self.get_sources()
    
    def get_articles_paginated(self, page: int = 1, per_page: int = 20, source: Optional[str] = None, days: Optional[int] = None) -> Dict:
        """페이지네이션된 기사 목록 조회"""
        try:
            # 필터 조건 설정
            where_conditions = {}
            if source:
                where_conditions["source"] = source
            
            # 전체 개수 조회
            if where_conditions:
                all_results = self.collection.get(where=where_conditions)
                total_docs = len(all_results['ids']) if all_results['ids'] else 0
            else:
                total_docs = self.collection.count()
            
            # 페이지네이션 계산
            offset = (page - 1) * per_page
            total_pages = (total_docs + per_page - 1) // per_page
            
            # 데이터 조회
            try:
                if where_conditions:
                    results = self.collection.get(where=where_conditions)
                    # 수동으로 페이지네이션 적용
                    if results and results['ids']:
                        start_idx = offset
                        end_idx = offset + per_page
                        results = {
                            'ids': results['ids'][start_idx:end_idx],
                            'documents': results['documents'][start_idx:end_idx] if results['documents'] else [],
                            'metadatas': results['metadatas'][start_idx:end_idx] if results['metadatas'] else []
                        }
                else:
                    # 전체 조회 후 수동 페이지네이션
                    results = self.collection.get()
                    if results and results['ids']:
                        start_idx = offset
                        end_idx = offset + per_page
                        results = {
                            'ids': results['ids'][start_idx:end_idx],
                            'documents': results['documents'][start_idx:end_idx] if results['documents'] else [],
                            'metadatas': results['metadatas'][start_idx:end_idx] if results['metadatas'] else []
                        }
            except Exception:
                # ChromaDB에서 오프셋이 지원되지 않을 경우
                results = self.collection.get()
                if results and results['ids']:
                    start_idx = offset
                    end_idx = offset + per_page
                    results = {
                        'ids': results['ids'][start_idx:end_idx],
                        'documents': results['documents'][start_idx:end_idx] if results['documents'] else [],
                        'metadatas': results['metadatas'][start_idx:end_idx] if results['metadatas'] else []
                    }
            
            # 결과 포맷팅
            articles = []
            if results and results.get('metadatas'):
                for i, metadata in enumerate(results['metadatas']):
                    content_length = 0
                    if results.get('documents') and i < len(results['documents']):
                        content_length = len(results['documents'][i])
                    
                    article = {
                        'id': results['ids'][i] if results['ids'] else '',
                        'title': metadata.get('title', ''),
                        'url': metadata.get('url', ''),
                        'source': metadata.get('source', ''),
                        'date': metadata.get('published_date', ''),
                        'authors': metadata.get('authors', ''),
                        'summary': metadata.get('summary', '')[:200] + '...' if metadata.get('summary', '') else '',
                        'content_length': content_length
                    }
                    articles.append(article)
            
            return {
                'articles': articles,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_docs,
                    'pages': total_pages
                }
            }
            
        except Exception as e:
            logger.error(f"페이지네이션 기사 조회 오류: {e}")
            return {
                'articles': [],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0,
                    'pages': 0
                }
            }