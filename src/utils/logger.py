"""
Logger utilities for RSS Crawler
"""

import logging
import logging.handlers
import os
from src.utils.config import config

def setup_logger(name: str = None, level: str = None) -> logging.Logger:
    """
    로거 설정 및 반환
    
    Args:
        name: 로거 이름 (기본값: __name__)
        level: 로깅 레벨 (기본값: 설정파일 값)
    
    Returns:
        설정된 로거 인스턴스
    """
    if name is None:
        name = __name__
    
    logger = logging.getLogger(name)
    
    # 이미 핸들러가 설정되어 있으면 반환
    if logger.handlers:
        return logger
    
    # 로깅 레벨 설정
    log_level = level or config.log_level
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 포매터 설정
    formatter = logging.Formatter(
        config.get('logging.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 (로그 디렉토리가 있는 경우)
    log_file = config.get('logging.file')
    if log_file:
        # 로그 디렉토리 생성
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # 로테이팅 파일 핸들러
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=config.get('logging.max_bytes', 10485760),  # 10MB
            backupCount=config.get('logging.backup_count', 5)
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# 기본 로거 인스턴스
logger = setup_logger('rss_crawler')