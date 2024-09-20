import chromadb
from chromadb.config import Settings
import hashlib
from datetime import datetime, timedelta
import random
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ChromaDB 클라이언트 설정
logger.info("Initializing ChromaDB client")
chroma_client = chromadb.PersistentClient(path="./chroma_db")
logger.info("ChromaDB client initialized")

# 컬렉션 가져오기 또는 생성
logger.info("Attempting to get or create collection 'news_articles'")
collection = chroma_client.get_or_create_collection(name="news_articles")
logger.info(
    f"Collection 'news_articles' {'created' if collection.count() == 0 else 'accessed'}")


def hash_url(url):
    return hashlib.md5(url.encode()).hexdigest()


def get_sample_articles(sample_size=5):
    total_articles = collection.count()
    sample_size = min(sample_size, total_articles)
    random_indices = random.sample(range(total_articles), sample_size)
    results = collection.get(ids=None, limit=total_articles)

    sample_articles = []
    for idx in random_indices:
        sample_articles.append({
            'id': results['ids'][idx],
            'metadata': results['metadatas'][idx],
            'document': results['documents'][idx]
        })

    return sample_articles


def search_articles_by_keyword(keyword, limit=10, start_date=None, end_date=None):
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

    results = collection.query(
        query_texts=[keyword],
        n_results=limit,
        where=where_clause
    )
    return results


def get_recent_articles(days=1, limit=10):
    recent_date = datetime.now() - timedelta(days=days)
    where_clause = {"date": {"$gte": int(recent_date.timestamp())}}

    results = collection.query(
        query_texts=[""],
        n_results=limit,
        where=where_clause
    )

    return [
        {
            'id': results['ids'][0][i],
            'metadata': results['metadatas'][0][i],
            'document': results['documents'][0][i]
        }
        for i in range(len(results['ids'][0]))
    ]


def get_article_by_url(url):
    url_hash = hash_url(url)
    result = collection.get(ids=[url_hash])
    if result['ids']:
        return {
            'id': result['ids'][0],
            'metadata': result['metadatas'][0],
            'document': result['documents'][0]
        }
    return None


def get_recent_articles_by_source(source, limit=10):
    where_clause = {"source": source}

    logger.info(f"Searching for articles with source: {source}")

    # 먼저 전체 컬렉션의 항목 수를 확인합니다.
    total_count = collection.count()
    logger.info(f"Total items in collection: {total_count}")

    # 일단 큰 수의 결과를 요청합니다.
    n_results = min(1000, total_count)

    results = collection.query(
        query_texts=[""],
        n_results=n_results,
        where=where_clause
    )
    logger.info(f"Query results count: {len(results['ids'][0])}")

    # 모든 메타데이터의 'source' 필드를 확인합니다.
    all_sources = set(meta['source'] for meta in results['metadatas'][0])
    logger.info(f"All sources found in results: {all_sources}")

    articles = []
    for i in range(len(results['ids'][0])):
        article = {
            'id': results['ids'][0][i],
            'title': results['metadatas'][0][i]['title'],
            'url': results['metadatas'][0][i]['url'],
            'date': datetime.fromtimestamp(results['metadatas'][0][i]['date']),
            'summary': results['metadatas'][0][i].get('summary', 'No summary available'),
            'source': results['metadatas'][0][i]['source']
        }
        articles.append(article)

    # 날짜를 기준으로 정렬
    articles.sort(key=lambda x: x['date'], reverse=True)

    # 상위 limit 개수만큼 반환
    return articles[:limit]


# 사용 예시
if __name__ == "__main__":
    # 키워드로 기사 검색
    print("Searching articles with keyword 'Sounds':")
    tech_articles = search_articles_by_keyword("Sounds", limit=5)
    for i, doc in enumerate(tech_articles['documents'][0]):
        print(
            f"{i+1}. {tech_articles['metadatas'][0][i]['title']} {tech_articles['metadatas'][0][i]['date']}")

    # ----------------------------
    # 날짜 범위로 기사 검색
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()

    print(
        f"\nSearching articles from {start_date.date()} to {end_date.date()}:")
    date_articles = search_articles_by_keyword(
        "Global", limit=5, start_date=start_date, end_date=end_date)
    for i, doc in enumerate(date_articles['documents'][0]):
        publish_date = datetime.fromtimestamp(
            date_articles['metadatas'][0][i]['date'])
        print(
            f"{i+1}. {date_articles['metadatas'][0][i]['title']} ({publish_date})")

    # -------------------------
    print("\nGetting recent articles:")
    recent_articles = get_recent_articles(days=7, limit=5)
    for article in recent_articles:
        publish_date = datetime.fromtimestamp(article['metadata']['date'])
        print(f"- {article['metadata']['title']} ({publish_date})")

    # 샘플 기사 가져오기
    print("\nGetting sample articles:")
    sample_articles = get_sample_articles(5)
    for article in sample_articles:
        publish_date = datetime.fromtimestamp(article['metadata']['date'])
        print(f"- Title: {article['metadata']['title']}")
        print(f"  URL: {article['metadata']['url']}")
        print(f"  Published: {publish_date}")
        print(
            f"  Summary: {article['metadata'].get('summary', 'No summary available')[:100]}...")
        print()

    # 특정 URL의 기사 가져오기
    sample_url = "https://www.bbc.com/sport/cricket/videos/crr5wkng7d7o"
    print(f"\nGetting article from URL: {sample_url}")
    article = get_article_by_url(sample_url)
    if article:
        publish_date = datetime.fromtimestamp(article['metadata']['date'])
        print(f"Title: {article['metadata']['title']}")
        print(f"Publish Date: {publish_date}")
        print(
            f"Summary: {article['metadata'].get('summary', 'No summary available')}")
    else:
        print("Article not found")

     # 특정 소스의 최근 뉴스 10개 가져오기
    source = "Donga"
    logger.info(f"\nGetting 10 most recent news articles from {source}:")
    recent_source_news = get_recent_articles_by_source(source, 10)

    logger.info(f"Total articles retrieved: {len(recent_source_news)}")

    # 최근 뉴스 출력
    for i, article in enumerate(recent_source_news, 1):
        logger.info(f"{i}. {article['title']}")
        logger.info(f"   Published: {article['date']}")
        logger.info(f"   URL: {article['url']}")
        logger.info(f"   Summary: {article['summary'][:100]}...")
        logger.info("")
