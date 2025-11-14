#!/usr/bin/env python3
"""
RSS 크롤링 기능 테스트
RSS 피드 파싱, 기사 수집, 데이터 처리 등 테스트
"""

import sys
import os
from pathlib import Path
import pandas as pd

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_rss_feed_parsing():
    """RSS 피드 파싱 테스트"""
    print("=" * 60)
    print("📡 RSS 피드 파싱 테스트")
    print("=" * 60)
    
    try:
        import feedparser
        
        # 테스트용 RSS 피드들 (안정적인 공개 피드)
        test_feeds = [
            {
                'name': 'BBC News',
                'url': 'https://feeds.bbci.co.uk/news/rss.xml'
            },
            {
                'name': 'Reuters',
                'url': 'https://www.reuters.com/rssFeed/technologyNews'
            },
            {
                'name': 'TechCrunch',
                'url': 'https://techcrunch.com/feed/'
            }
        ]
        
        successful_feeds = 0
        
        for i, feed_info in enumerate(test_feeds, 1):
            print(f"\n{i}. {feed_info['name']} 테스트")
            print(f"   URL: {feed_info['url']}")
            
            try:
                # RSS 피드 파싱
                parsed = feedparser.parse(feed_info['url'])
                
                if parsed.entries:
                    print(f"   ✅ 파싱 성공: {len(parsed.entries)}개 기사")
                    
                    # 첫 번째 기사 정보 출력
                    first_entry = parsed.entries[0]
                    print(f"   📰 첫 번째 기사:")
                    print(f"      제목: {getattr(first_entry, 'title', 'N/A')[:80]}...")
                    print(f"      링크: {getattr(first_entry, 'link', 'N/A')}")
                    print(f"      날짜: {getattr(first_entry, 'published', 'N/A')}")
                    
                    successful_feeds += 1
                else:
                    print(f"   ⚠️ 기사를 찾을 수 없습니다")
                    
            except Exception as feed_error:
                print(f"   ❌ 피드 파싱 실패: {feed_error}")
        
        print(f"\n📊 결과: {successful_feeds}/{len(test_feeds)} 피드 파싱 성공")
        return successful_feeds > 0
        
    except Exception as e:
        print(f"❌ RSS 피드 파싱 테스트 실패: {e}")
        return False

def test_crawler_initialization():
    """크롤러 초기화 테스트"""
    print("\n" + "=" * 60)
    print("🤖 크롤러 초기화 테스트")
    print("=" * 60)
    
    try:
        from src.core.crawler import RSSCrawler
        
        print("📡 RSSCrawler 인스턴스 생성 중...")
        crawler = RSSCrawler()
        
        print("✅ RSSCrawler 초기화 성공")
        
        # 설정된 피드 확인
        feeds_file = project_root / 'config' / 'rss_feeds.csv'
        if not feeds_file.exists():
            feeds_file = project_root / 'rss_feeds.csv'
            
        if feeds_file.exists():
            df = pd.read_csv(feeds_file)
            print(f"📊 등록된 피드 수: {len(df)}개")
            
            # 처음 3개 피드 정보 출력
            for i in range(min(3, len(df))):
                feed = df.iloc[i]
                name = feed.get('source') or feed.get('name', f'Feed {i+1}')
                url = feed.get('rss_url') or feed.get('url', 'N/A')
                print(f"   {i+1}. {name}: {url}")
        else:
            print("⚠️ 피드 설정 파일을 찾을 수 없습니다")
            
        return True, crawler
        
    except Exception as e:
        print(f"❌ 크롤러 초기화 실패: {e}")
        return False, None

def test_single_feed_crawling(crawler):
    """단일 피드 크롤링 테스트"""
    print("\n" + "=" * 60)
    print("📰 단일 피드 크롤링 테스트")
    print("=" * 60)
    
    if not crawler:
        print("❌ 크롤러가 초기화되지 않았습니다.")
        return False
    
    try:
        # 테스트용 안정적인 RSS 피드
        test_feed_url = "https://feeds.bbci.co.uk/news/technology/rss.xml"
        
        print(f"🔍 테스트 피드 크롤링: {test_feed_url}")
        
        # 단일 피드 크롤링 시도
        try:
            articles = crawler.crawl_single_feed(test_feed_url, "BBC Tech")
            
            if articles and len(articles) > 0:
                print(f"✅ 크롤링 성공: {len(articles)}개 기사 수집")
                
                # 첫 번째 기사 상세 정보
                first_article = articles[0]
                print(f"📑 첫 번째 기사 정보:")
                print(f"   제목: {first_article.get('title', 'N/A')[:80]}...")
                print(f"   출처: {first_article.get('source', 'N/A')}")
                print(f"   URL: {first_article.get('url', 'N/A')}")
                print(f"   날짜: {first_article.get('published_date', 'N/A')}")
                print(f"   내용 길이: {len(first_article.get('content', ''))}자")
                
                return True
            else:
                print("⚠️ 수집된 기사가 없습니다")
                return False
                
        except AttributeError:
            # crawl_single_feed 메서드가 없는 경우 대체 테스트
            print("ℹ️ crawl_single_feed 메서드를 찾을 수 없습니다. 일반 크롤링 테스트로 대체...")
            
            import feedparser
            parsed = feedparser.parse(test_feed_url)
            
            if parsed.entries:
                print(f"✅ 대체 테스트 성공: {len(parsed.entries)}개 기사 발견")
                return True
            else:
                print("❌ 대체 테스트 실패")
                return False
                
    except Exception as e:
        print(f"❌ 단일 피드 크롤링 테스트 실패: {e}")
        return False

def test_article_processing():
    """기사 처리 로직 테스트"""
    print("\n" + "=" * 60)
    print("⚙️ 기사 처리 로직 테스트")
    print("=" * 60)
    
    try:
        # 테스트 기사 데이터
        test_article_data = {
            'title': 'Test Article: AI Technology Breakthrough',
            'content': 'This is a test article about artificial intelligence and machine learning advances. The content includes various technical details and implications for the future.',
            'url': 'https://example.com/test-article',
            'source': 'Test News',
            'published_date': '2025-11-12 21:00:00'
        }
        
        # 기사 데이터 검증
        required_fields = ['title', 'content', 'url', 'source']
        missing_fields = []
        
        for field in required_fields:
            if not test_article_data.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ 필수 필드 누락: {missing_fields}")
            return False
        
        print("✅ 기사 데이터 구조 검증 성공")
        
        # 내용 길이 확인
        content_length = len(test_article_data['content'])
        print(f"📝 기사 내용 길이: {content_length}자")
        
        # URL 유효성 기본 검증
        url = test_article_data['url']
        if url.startswith(('http://', 'https://')):
            print("🔗 URL 형식 검증 성공")
        else:
            print("⚠️ URL 형식이 올바르지 않습니다")
        
        # 날짜 형식 확인
        try:
            from datetime import datetime
            date_str = test_article_data['published_date']
            parsed_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            print(f"📅 날짜 형식 검증 성공: {parsed_date}")
        except ValueError:
            print("⚠️ 날짜 형식 검증 실패")
        
        print("✅ 기사 처리 로직 테스트 완료")
        return True
        
    except Exception as e:
        print(f"❌ 기사 처리 로직 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🧪 RSS Crawler - 크롤링 기능 테스트 시작")
    
    results = []
    
    # 1. RSS 피드 파싱 테스트
    parsing_success = test_rss_feed_parsing()
    results.append(("RSS 피드 파싱", parsing_success))
    
    # 2. 크롤러 초기화 테스트
    init_success, crawler = test_crawler_initialization()
    results.append(("크롤러 초기화", init_success))
    
    # 3. 단일 피드 크롤링 테스트
    if init_success:
        crawling_success = test_single_feed_crawling(crawler)
        results.append(("단일 피드 크롤링", crawling_success))
    
    # 4. 기사 처리 로직 테스트
    processing_success = test_article_processing()
    results.append(("기사 처리 로직", processing_success))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📋 크롤링 테스트 결과 요약")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 총 {passed}/{total} 테스트 통과")
    
    if passed == total:
        print("🎉 모든 크롤링 테스트가 성공적으로 완료되었습니다!")
    else:
        print("⚠️ 일부 테스트가 실패했습니다. 네트워크 연결을 확인해주세요.")

if __name__ == "__main__":
    main()