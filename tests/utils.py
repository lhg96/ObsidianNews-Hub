#!/usr/bin/env python3
"""
공통 유틸리티 함수 모듈
tests 폴더 스크립트들이 공통으로 사용하는 함수들
"""

import sys
import os
from pathlib import Path
from typing import Tuple

def setup_project_path() -> Path:
    """프로젝트 루트를 Python 경로에 추가하고 루트 경로 반환"""
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    return project_root

def init_components(config_path: str = None) -> Tuple:
    """
    RSS Crawler 핵심 컴포넌트 초기화
    
    Returns:
        (db_manager, config, logger) 튜플
    """
    try:
        from src.core.database import DatabaseManager
        from src.utils.config import Config
        from src.utils.logger import setup_logger
        
        logger = setup_logger(__name__)
        config = Config()
        
        # 데이터베이스 초기화
        db_manager = DatabaseManager(
            db_path=config.get('database.path', './data/chroma_db'),
            collection_name=config.get('database.collection_name', 'news_articles')
        )
        
        return db_manager, config, logger
        
    except ImportError as e:
        print(f"❌ 모듈 import 오류: {e}")
        print("필요한 종속성을 설치하세요: pip install -r requirements.txt")
        sys.exit(1)

def print_header(title: str, subtitle: str = None) -> None:
    """예쁜 헤더 출력"""
    print("=" * 80)
    print(f"🚀 {title}")
    if subtitle:
        print(f"📋 {subtitle}")
    print("=" * 80)
    print()

def print_error(message: str, details: str = None) -> None:
    """에러 메시지 출력"""
    print(f"❌ {message}")
    if details:
        print(f"💡 {details}")

def print_success(message: str, details: str = None) -> None:
    """성공 메시지 출력"""
    print(f"✅ {message}")
    if details:
        print(f"📊 {details}")

def get_feeds_file_path(project_root: Path) -> Path:
    """RSS 피드 파일 경로 반환 및 존재 여부 확인"""
    feeds_file = project_root / 'config' / 'rss_feeds.csv'
    if not feeds_file.exists():
        raise FileNotFoundError(f"RSS 피드 파일이 없습니다: {feeds_file}")
    return feeds_file