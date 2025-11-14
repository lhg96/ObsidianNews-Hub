#!/usr/bin/env python3
"""
웹 GUI 기능 테스트
Flask 앱, API 엔드포인트, 프론트엔드 기능 등 테스트
"""

import sys
import os
from pathlib import Path
import requests
import time
import threading

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class WebGUITester:
    """웹 GUI 테스트 클래스"""
    
    def __init__(self, base_url="http://localhost:5002"):
        self.base_url = base_url
        self.session = requests.Session()
        self.web_server_running = False
    
    def check_server_running(self):
        """웹 서버 실행 상태 확인"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def test_main_page(self):
        """메인 페이지 테스트"""
        print("🏠 메인 페이지 접근 테스트")
        
        try:
            response = self.session.get(f"{self.base_url}/")
            
            if response.status_code == 200:
                print("   ✅ 메인 페이지 로드 성공")
                
                # HTML 내용 확인
                content = response.text
                
                # 필수 요소들 확인
                required_elements = [
                    "RSS Crawler 관리 시스템",
                    "크롤링 제어",
                    "피드 관리", 
                    "기사 검색",
                    "Bootstrap",
                    "navbar"
                ]
                
                missing_elements = []
                for element in required_elements:
                    if element in content:
                        print(f"   ✅ '{element}' 요소 발견")
                    else:
                        missing_elements.append(element)
                        print(f"   ❌ '{element}' 요소 누락")
                
                return len(missing_elements) == 0
            else:
                print(f"   ❌ 메인 페이지 로드 실패: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 메인 페이지 테스트 실패: {e}")
            return False
    
    def test_feeds_api(self):
        """피드 관리 API 테스트"""
        print("\n📡 피드 관리 API 테스트")
        
        try:
            # 1. 피드 목록 조회
            print("   1️⃣ 피드 목록 조회 테스트")
            response = self.session.get(f"{self.base_url}/api/feeds")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    feeds = data.get('feeds', [])
                    print(f"      ✅ 피드 목록 조회 성공: {len(feeds)}개 피드")
                    
                    # 첫 번째 피드 정보 출력
                    if feeds:
                        first_feed = feeds[0]
                        name = first_feed.get('source') or first_feed.get('name', 'N/A')
                        url = first_feed.get('rss_url') or first_feed.get('url', 'N/A')
                        print(f"      📰 첫 번째 피드: {name}")
                        print(f"      🔗 URL: {url}")
                else:
                    print(f"      ❌ API 응답 실패: {data.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"      ❌ HTTP 오류: {response.status_code}")
                return False
            
            # 2. 피드 추가 테스트
            print("\n   2️⃣ 피드 추가 테스트")
            test_feed_data = {
                'name': 'Test Feed',
                'url': 'https://feeds.bbci.co.uk/news/technology/rss.xml',
                'category': 'Technology'
            }
            
            response = self.session.post(
                f"{self.base_url}/api/feeds/add",
                json=test_feed_data
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("      ✅ 테스트 피드 추가 성공")
                else:
                    error_msg = data.get('error', 'Unknown error')
                    if 'already' in error_msg.lower() or '이미' in error_msg:
                        print("      ℹ️ 피드가 이미 존재함 (정상)")
                    else:
                        print(f"      ❌ 피드 추가 실패: {error_msg}")
                        return False
            else:
                print(f"      ❌ HTTP 오류: {response.status_code}")
                return False
            
            # 3. 피드 테스트
            print("\n   3️⃣ 피드 테스트")
            response = self.session.post(
                f"{self.base_url}/api/feeds/test",
                json={'index': 0}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    entries = data.get('entries', 0)
                    print(f"      ✅ 피드 테스트 성공: {entries}개 항목")
                else:
                    print(f"      ❌ 피드 테스트 실패: {data.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"      ❌ HTTP 오류: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            print(f"   ❌ 피드 API 테스트 실패: {e}")
            return False
    
    def test_search_api(self):
        """검색 API 테스트"""
        print("\n🔍 검색 API 테스트")
        
        try:
            search_queries = [
                "AI 인공지능",
                "technology",
                "news",
                "정치",
                "경제"
            ]
            
            successful_searches = 0
            
            for i, query in enumerate(search_queries, 1):
                print(f"   {i}️⃣ 검색어: '{query}'")
                
                response = self.session.post(
                    f"{self.base_url}/api/search",
                    json={'query': query}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        articles = data.get('articles', [])
                        print(f"      ✅ 검색 성공: {len(articles)}개 결과")
                        
                        # 첫 번째 결과 정보
                        if articles:
                            first_result = articles[0]
                            title = first_result.get('title', 'N/A')
                            source = first_result.get('source', 'N/A')
                            print(f"      📰 첫 번째 결과: {title[:50]}...")
                            print(f"      📍 출처: {source}")
                        
                        successful_searches += 1
                    else:
                        error_msg = data.get('error', 'Unknown error')
                        if 'database' in error_msg.lower() or '데이터베이스' in error_msg:
                            print(f"      ⚠️ 데이터베이스 연결 필요: {error_msg}")
                        else:
                            print(f"      ❌ 검색 실패: {error_msg}")
                else:
                    print(f"      ❌ HTTP 오류: {response.status_code}")
            
            print(f"\n📊 검색 테스트 결과: {successful_searches}/{len(search_queries)} 성공")
            return successful_searches > 0
            
        except Exception as e:
            print(f"   ❌ 검색 API 테스트 실패: {e}")
            return False
    
    def test_stats_api(self):
        """통계 API 테스트"""
        print("\n📊 통계 API 테스트")
        
        try:
            response = self.session.get(f"{self.base_url}/api/stats")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    stats = data.get('stats', {})
                    print("      ✅ 통계 조회 성공")
                    
                    # 통계 정보 출력
                    for key, value in stats.items():
                        print(f"      📈 {key}: {value}")
                        
                    return True
                else:
                    error_msg = data.get('error', 'Unknown error')
                    if 'database' in error_msg.lower() or '데이터베이스' in error_msg:
                        print(f"      ⚠️ 데이터베이스 연결 필요: {error_msg}")
                        return True  # 데이터베이스 없이도 정상 동작
                    else:
                        print(f"      ❌ 통계 조회 실패: {error_msg}")
                        return False
            else:
                print(f"      ❌ HTTP 오류: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 통계 API 테스트 실패: {e}")
            return False

def test_web_gui():
    """웹 GUI 종합 테스트"""
    print("=" * 60)
    print("🌐 웹 GUI 기능 테스트")
    print("=" * 60)
    
    tester = WebGUITester()
    
    # 서버 실행 상태 확인
    if not tester.check_server_running():
        print("❌ 웹 서버가 실행되지 않았습니다.")
        print("💡 웹 서버를 먼저 실행해주세요: python scripts/run_web_gui.py")
        return False
    
    print("✅ 웹 서버가 실행 중입니다")
    
    results = []
    
    # 1. 메인 페이지 테스트
    main_success = tester.test_main_page()
    results.append(("메인 페이지", main_success))
    
    # 2. 피드 API 테스트
    feeds_success = tester.test_feeds_api()
    results.append(("피드 API", feeds_success))
    
    # 3. 검색 API 테스트
    search_success = tester.test_search_api()
    results.append(("검색 API", search_success))
    
    # 4. 통계 API 테스트
    stats_success = tester.test_stats_api()
    results.append(("통계 API", stats_success))
    
    return results

def test_flask_app_structure():
    """Flask 앱 구조 테스트"""
    print("\n" + "=" * 60)
    print("🏗️ Flask 앱 구조 테스트")
    print("=" * 60)
    
    try:
        # 웹 GUI 스크립트 파일 확인
        web_gui_file = project_root / 'scripts' / 'run_web_gui.py'
        
        if not web_gui_file.exists():
            print("❌ 웹 GUI 스크립트 파일이 없습니다")
            return False
        
        print("✅ 웹 GUI 스크립트 파일 존재")
        
        # 파일 내용에서 필수 요소들 확인
        with open(web_gui_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_elements = [
            'from flask import',
            'app = Flask(',
            '@app.route',
            'app.run(',
            'render_template_string',
            'jsonify'
        ]
        
        print("\n📋 Flask 필수 요소 확인:")
        missing_elements = []
        
        for element in required_elements:
            if element in content:
                print(f"   ✅ {element}")
            else:
                missing_elements.append(element)
                print(f"   ❌ {element}")
        
        # API 엔드포인트 확인
        api_endpoints = [
            '/api/feeds',
            '/api/feeds/add',
            '/api/feeds/delete',
            '/api/feeds/test',
            '/api/search',
            '/api/stats',
            '/api/crawl/start'
        ]
        
        print("\n🔌 API 엔드포인트 확인:")
        missing_endpoints = []
        
        for endpoint in api_endpoints:
            if endpoint in content:
                print(f"   ✅ {endpoint}")
            else:
                missing_endpoints.append(endpoint)
                print(f"   ❌ {endpoint}")
        
        if not missing_elements and not missing_endpoints:
            print("\n🎉 Flask 앱 구조가 완벽합니다!")
            return True
        else:
            print(f"\n⚠️ 누락된 요소: {len(missing_elements + missing_endpoints)}개")
            return False
            
    except Exception as e:
        print(f"❌ Flask 앱 구조 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🧪 RSS Crawler - 웹 GUI 기능 테스트 시작")
    
    results = []
    
    # 1. Flask 앱 구조 테스트
    structure_success = test_flask_app_structure()
    results.append(("Flask 앱 구조", structure_success))
    
    # 2. 웹 GUI 기능 테스트 (서버가 실행 중인 경우)
    gui_results = test_web_gui()
    if gui_results:
        results.extend(gui_results)
    else:
        results.append(("웹 서버 연결", False))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📋 웹 GUI 테스트 결과 요약")
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
        print("🎉 모든 웹 GUI 테스트가 성공적으로 완료되었습니다!")
    else:
        print("⚠️ 일부 테스트가 실패했습니다.")
        if any('웹 서버 연결' in result[0] for result in results if not result[1]):
            print("💡 웹 서버를 실행한 후 다시 테스트해주세요.")

if __name__ == "__main__":
    main()