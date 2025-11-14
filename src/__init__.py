"""
AI RSS Crawler Package

RSS 피드를 크롤링하고 마크다운으로 변환하는 패키지입니다.
"""

__version__ = "1.0.0"
__author__ = "lhg96"
__email__ = ""
__description__ = "AI-powered RSS crawler with markdown generation"

from src.core.crawler import RSSCrawler
from src.core.database import DatabaseManager
from src.generators.obsidian_generator import ObsidianGenerator

__all__ = [
    "RSSCrawler",
    "DatabaseManager", 
    "ObsidianGenerator"
]