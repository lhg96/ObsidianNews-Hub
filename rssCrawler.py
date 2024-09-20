import logging
import feedparser
import requests
from bs4 import BeautifulSoup
import chromadb
from chromadb.config import Settings
import hashlib
from datetime import datetime, timedelta
import csv
from newspaper import Article
import threading
import nltk

# NLTK 데이터 다운로드 (처음 한 번만 실행하면 됩니다)
nltk.download('punkt')

# 로깅 설정
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ChromaDB 클라이언트 설정
chroma_client = chromadb.PersistentClient(path="./chroma_db")
logger.info("ChromaDB client initialized")

# 뉴스 기사 컬렉션 가져오기 또는 생성
collection = chroma_client.get_or_create_collection(name="news_articles")
logger.info(
    f"Collection 'news_articles' {'created' if collection.count() == 0 else 'accessed'}")


def hash_url(url):
    return hashlib.md5(url.encode()).hexdigest()


def fetch_article_content(url):
    logger.info(f"Fetching content from URL: {url}")
    try:
        article = Article(url)
        article.download()
        article.parse()

        content = article.text
        title = article.title

        # publish_date = article.publish_date.isoformat(
        # ) if article.publish_date else datetime.now().isoformat()
        publish_date = article.publish_date if article.publish_date else datetime.now()

        authors = ', '.join(article.authors)

        logger.info(
            f"Content fetched successfully. Length: {len(content)} characters")
        return {
            'content': content,
            'title': title,
            # 'date': publish_date,
            'date': int(publish_date.timestamp()),  # Unix timestamp로 변환
            'authors': authors
        }
    except Exception as e:
        logger.error(f"Error fetching content from {url}: {str(e)}")
        return None


def process_feed(source, rss_url):
    logger.info(f"Processing feed: {source} - {rss_url}")
    feed = feedparser.parse(rss_url)
    logger.info(f"Feed parsed. Number of entries: {len(feed.entries)}")

    for entry in feed.entries:
        url = entry.link
        url_hash = hash_url(url)

        # 이미 처리된 URL인지 확인
        if collection.get(ids=[url_hash])['ids']:
            logger.info(f"Article already exists: {url}")
            continue

        article_data = fetch_article_content(url)
        if not article_data:
            logger.warning(
                f"Skipping article due to content fetch failure: {url}")
            continue

        # ChromaDB에 저장
        try:
            collection.add(
                ids=[url_hash],
                documents=[article_data['content']],
                metadatas=[{
                    "url": url,
                    "title": article_data['title'],
                    "summary": entry.get('summary', ''),
                    "source": source,
                    "date": article_data['date'],
                    "authors": article_data['authors']
                }]
            )
            logger.info(f"Article added to ChromaDB: {article_data['title']}")
        except Exception as e:
            logger.error(f"Error adding article to ChromaDB: {str(e)}")


def main():
    logger.info("Starting RSS feed processing")
    with open('rss_feeds.csv', 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            process_feed(row['source'], row['rss_url'])
    logger.info("RSS feed processing completed")
    logger.info(f"Total articles in collection: {collection.count()}")


if __name__ == "__main__":
    main()
