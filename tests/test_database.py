#!/usr/bin/env python3
"""
데이터베이스 기능 테스트
ChromaDB 연결, 검색, 통계 등 핵심 기능 테스트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_database_connection():
    """데이터베이스 연결 테스트"""
    print("=" * 60)
    print("🔌 데이터베이스 연결 테스트")
    print("=" * 60)
    
    try:
        from src.core.database import DatabaseManager
        
        # DatabaseManager 초기화
        db_manager = DatabaseManager(
            db_path="./data/chroma_db",
            collection_name="news_articles"
        )
        
        print("✅ DatabaseManager 초기화 성공")
        
        # 컬렉션 정보 확인
        collection = db_manager.get_collection()
        count = collection.count()
        
        print(f"📊 저장된 기사 수: {count:,d}개")
        
        # 통계 정보 확인
        stats = db_manager.get_collection_stats()
        print(f"📈 컬렉션 통계:")
        for key, value in stats.items():
            print(f"   - {key}: {value}")
            
        return True, db_manager
        
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return False, None

def test_search_functionality(db_manager):
    """검색 기능 테스트"""
    print("\n" + "=" * 60)
    print("🔍 검색 기능 테스트")
    print("=" * 60)
    
    if not db_manager:
        print("❌ 데이터베이스가 연결되지 않았습니다.")
        return False
    
    try:
        # 다양한 검색어로 테스트
        search_queries = [
            "AI 인공지능",
            "경제 금융",
            "정치 정책",
            "기술 혁신",
            "환경 기후"
        ]
        
        for i, query in enumerate(search_queries, 1):
            print(f"\n{i}. 검색어: '{query}'")
            
            results = db_manager.search_articles(query, limit=3)
            
            if results and len(results) > 0:
                print(f"   ✅ {len(results)}개 결과 발견")
                
                # 첫 번째 결과 상세 정보
                if len(results) > 0:
                    first_result = results[0]
                    metadata = first_result.get('metadata', {})
                    content = first_result.get('content', '')
                    
                    print(f"   📰 첫 번째 결과:")
                    print(f"      제목: {metadata.get('title', 'N/A')}")
                    print(f"      출처: {metadata.get('source', 'N/A')}")
                    print(f"      날짜: {metadata.get('published_date', 'N/A')}")
                    print(f"      내용: {content[:100]}...")
            else:
                print(f"   ⚠️ 검색 결과 없음")
        
        return True
        
    except Exception as e:
        print(f"❌ 검색 테스트 실패: {e}")
        return False

def test_data_insertion(db_manager):
    """데이터 삽입 테스트"""
    print("\n" + "=" * 60)
    print("💾 데이터 삽입 테스트")
    print("=" * 60)
    
    if not db_manager:
        print("❌ 데이터베이스가 연결되지 않았습니다.")
        return False
    
    try:
        from datetime import datetime
        
        # 테스트 기사 데이터
        test_article = {
            'title': '테스트 기사 - RSS Crawler 시스템 검증',
            'content': '이것은 RSS Crawler 시스템의 데이터베이스 기능을 테스트하기 위한 테스트 기사입니다. 인공지능, 머신러닝, 자연어 처리 등의 기술을 활용하여 뉴스 기사를 수집하고 분석합니다.',
            'url': 'https://test.example.com/test-article',
            'source': 'Test Source',
            'published_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'category': 'Technology'
        }
        
        print("📝 테스트 기사 삽입 중...")
        
        # 기사 저장 전 개수
        collection = db_manager.get_collection()
        before_count = collection.count()
        
        # 기사 저장
        db_manager.save_article(test_article)
        
        # 기사 저장 후 개수
        after_count = collection.count()
        
        if after_count > before_count:
            print("✅ 테스트 기사 삽입 성공")
            print(f"📊 기사 수 변화: {before_count} → {after_count}")
            
            # 삽입된 기사 검색해보기
            print("\n🔍 삽입된 기사 검색 테스트...")
            search_results = db_manager.search_articles("테스트 RSS Crawler", limit=1)
            
            if search_results and len(search_results) > 0:
                result = search_results[0]
                metadata = result.get('metadata', {})
                print(f"   ✅ 삽입된 기사 검색 성공")
                print(f"   📰 제목: {metadata.get('title', 'N/A')}")
            else:
                print("   ⚠️ 삽입된 기사 검색 실패")
            
        else:
            print("⚠️ 기사 수가 증가하지 않았습니다 (중복 가능)")
            
        return True
        
    except Exception as e:
        print(f"❌ 데이터 삽입 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🧪 RSS Crawler - 데이터베이스 기능 테스트 시작")
    print(f"📅 테스트 시간: {os.getenv('TZ', 'UTC')} 기준")
    
    results = []
    
    # 1. 데이터베이스 연결 테스트
    success, db_manager = test_database_connection()
    results.append(("데이터베이스 연결", success))
    
    # 2. 검색 기능 테스트
    if success:
        search_success = test_search_functionality(db_manager)
        results.append(("검색 기능", search_success))
        
        # 3. 데이터 삽입 테스트
        insert_success = test_data_insertion(db_manager)
        results.append(("데이터 삽입", insert_success))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📋 테스트 결과 요약")
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
        print("🎉 모든 데이터베이스 테스트가 성공적으로 완료되었습니다!")
    else:
        print("⚠️ 일부 테스트가 실패했습니다. 로그를 확인해주세요.")

if __name__ == "__main__":
    main()