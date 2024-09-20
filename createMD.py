# createTodayNews.py

import chromadb
from datetime import datetime, timedelta
import os
from collections import defaultdict
import re


def extract_keywords(text, n=5):
    words = re.findall(r'\w+', text.lower())
    word_freq = defaultdict(int)
    for word in words:
        if len(word) > 2:
            word_freq[word] += 1
    return sorted(word_freq, key=word_freq.get, reverse=True)[:n]


def format_tag(keyword):
    return f"#[[{keyword}]]" if ' ' in keyword else f"#{keyword}"


# ChromaDB 설정
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection(name="news_articles")

# 날짜 설정
now = datetime.now()
one_week_ago = now - timedelta(days=7)

# 최근 1주일 기사 쿼리
results = collection.query(
    query_texts=[""],
    n_results=1000,
    where={"date": {"$gte": int(one_week_ago.timestamp())}}
)

# 결과를 source별로 정렬 및 그룹화
articles_by_source = defaultdict(list)
for metadata, document in zip(results['metadatas'][0], results['documents'][0]):
    source = metadata['source']
    articles_by_source[source].append((metadata, document))

# 마크다운 파일 생성
output_dir = r"C:\Users\hyun\OneDrive\문서\50.obsidian\WH2K\02.News\RSS"
output_file = os.path.join(output_dir, "Today News.md")

with open(output_file, "w", encoding="utf-8") as f:
    f.write(f"# 주간 뉴스 요약 ({now.strftime('%Y-%m-%d')})\n\n")

    # 소스 목차 생성
    f.write("## 뉴스 소스\n\n")
    for source in sorted(articles_by_source.keys()):
        f.write(f"- [[#{source}|{source}]]\n")
    f.write("\n---\n\n")

    for source, articles in sorted(articles_by_source.items()):
        f.write(f"## {source}\n\n")

        for metadata, content in sorted(articles, key=lambda x: x[0]['date'], reverse=True):
            title = metadata['title']
            url = metadata['url']
            summary = metadata['summary']
            keywords = extract_keywords(content)
            article_date = datetime.fromtimestamp(metadata['date'])

            f.write(f"### [{title}]({url})\n\n")
            f.write(f"**날짜**: {article_date.strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write(f"**요약**: {summary}\n\n")
            f.write(
                f"**키워드**: {' '.join(format_tag(kw) for kw in keywords)}\n\n")

            # 전문 출력 개선
            content_preview = content[:300]  # 처음 300자만 표시
            content_preview = content_preview.replace('\n', ' ')  # 줄바꿈 제거
            f.write(f"**전문 미리보기**:\n{content_preview}...\n\n")
            f.write(f"[전문 보기]({url})\n\n")  # 전문 링크 추가

            f.write("---\n\n")

    # 전체 키워드 모음
    all_keywords = [kw for articles in articles_by_source.values(
    ) for _, content in articles for kw in extract_keywords(content)]
    top_keywords = sorted(
        set(all_keywords), key=all_keywords.count, reverse=True)[:20]

    f.write("## 주간 주요 키워드\n\n")
    for keyword in top_keywords:
        f.write(f"{format_tag(keyword)}\n")

print(f"마크다운 파일이 생성되었습니다: {output_file}")
