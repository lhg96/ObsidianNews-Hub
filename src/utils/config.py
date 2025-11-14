"""
Configuration Management System
환경변수와 YAML 파일을 통한 설정 관리
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

class Config:
    """애플리케이션 설정 관리 클래스"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self._config_data = None
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """기본 설정 파일 경로 반환"""
        env = os.getenv('ENVIRONMENT', 'development')
        return f"config/{env}.yaml"
    
    def _load_config(self):
        """설정 파일 로드"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config_data = yaml.safe_load(f)
            else:
                self._config_data = self._get_default_config()
        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            self._config_data = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """기본 설정값 반환"""
        return {
            'database': {
                'path': './data/chroma_db',
                'collection_name': 'news_articles'
            },
            'crawler': {
                'max_workers': 5,
                'timeout': 30,
                'retry_count': 3,
                'delay_between_requests': 1.0
            },
            'markdown': {
                'output_dir': './output',
                'filename': 'Today_News.md',
                'keywords_count': 5,
                'content_preview_length': 300
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': './logs/app.log'
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """설정값 가져오기 (환경변수 우선)"""
        # 환경변수에서 먼저 확인
        env_key = key.upper().replace('.', '_')
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._convert_env_value(env_value)
        
        # 설정 파일에서 확인
        keys = key.split('.')
        value = self._config_data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def _convert_env_value(self, value: str) -> Any:
        """환경변수 값을 적절한 타입으로 변환"""
        if value.lower() in ('true', '1', 'yes', 'on'):
            return True
        elif value.lower() in ('false', '0', 'no', 'off'):
            return False
        
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        return value
    
    # 편의 속성들
    @property
    def database_path(self) -> str:
        return self.get('database.path', './data/chroma_db')
    
    @property
    def collection_name(self) -> str:
        return self.get('database.collection_name', 'news_articles')
    
    @property
    def max_workers(self) -> int:
        return self.get('crawler.max_workers', 5)
    
    @property
    def timeout(self) -> int:
        return self.get('crawler.timeout', 30)
    
    @property
    def retry_count(self) -> int:
        return self.get('crawler.retry_count', 3)
    
    @property
    def output_dir(self) -> str:
        return self.get('markdown.output_dir', './output')
    
    @property
    def log_level(self) -> str:
        return self.get('logging.level', 'INFO')

# 전역 설정 인스턴스
config = Config()