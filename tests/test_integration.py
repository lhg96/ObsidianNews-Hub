#!/usr/bin/env python3
"""
RSS Crawler 통합 테스트 및 실행 스크립트
모든 주요 기능을 테스트하고 통합 실행할 수 있습니다.

사용법:
  python tests/test_integration.py [옵션]

옵션:
  --test-only     테스트만 실행
  --crawl-only    크롤링만 실행
  --web-only      웹 GUI만 실행
  --skip-tests    테스트 건너뛰기
  --port PORT     웹 서버 포트 (기본값: 5004)
  --auto          자동 모드 (사용자 입력 없음)
"""

import sys
import os
import argparse
import subprocess
import time
import threading
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def parse_arguments():
    """명령줄 인수 파싱"""
    parser = argparse.ArgumentParser(description='RSS Crawler 통합 테스트 및 실행')
    parser.add_argument('--test-only', action='store_true', help='테스트만 실행')
    parser.add_argument('--crawl-only', action='store_true', help='크롤링만 실행')
    parser.add_argument('--web-only', action='store_true', help='웹 GUI만 실행')
    parser.add_argument('--skip-tests', action='store_true', help='테스트 건너뛰기')
    parser.add_argument('--port', type=int, default=5004, help='웹 서버 포트')
    parser.add_argument('--auto', action='store_true', help='자동 모드')
    return parser.parse_args()

def print_header(title):
    """예쁜 헤더 출력"""
    print("\n" + "="*80)
    print(f"🚀 {title}")
    print("="*80)

def run_test_module(test_name, test_file, auto_mode=False):
    """개별 테스트 모듈 실행"""
    print(f"\n{'='*80}")
    print(f"🧪 {test_name} 실행 중...")
    print(f"📁 파일: {test_file}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    try:
        # 테스트 실행
        result = subprocess.run(
            [sys.executable, str(test_file)],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=120
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ {test_name} 성공! ({duration:.2f}초)")
            if result.stdout:
                print(f"출력:\n{result.stdout}")
            return True
        else:
            print(f"❌ {test_name} 실패! ({duration:.2f}초)")
            if result.stderr:
                print(f"오류:\n{result.stderr}")
            if result.stdout:
                print(f"출력:\n{result.stdout}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {test_name} 시간 초과 (120초)")
        return False
    except Exception as e:
        print(f"❌ {test_name} 실행 중 오류: {e}")
        return False

def run_all_tests(auto_mode=False):
    """모든 테스트 실행"""
    print_header("RSS Crawler 전체 테스트 실행")
    
    tests = [
        ("Config 테스트", project_root / "tests" / "test_config.py"),
        ("Database 테스트", project_root / "tests" / "test_database.py"),
        ("Crawler 테스트", project_root / "tests" / "test_crawler.py"),
        ("WebGUI 테스트", project_root / "tests" / "test_webgui.py"),
    ]
    
    results = {}
    total_tests = len(tests)
    passed_tests = 0
    
    for test_name, test_file in tests:
        if test_file.exists():
            success = run_test_module(test_name, test_file, auto_mode)
            results[test_name] = success
            if success:
                passed_tests += 1
        else:
            print(f"⚠️ {test_name} 파일을 찾을 수 없음: {test_file}")
            results[test_name] = False
    
    # 결과 요약
    print(f"\n{'='*80}")
    print("📊 테스트 결과 요약")
    print(f"{'='*80}")
    print(f"전체 테스트: {total_tests}")
    print(f"성공: {passed_tests}")
    print(f"실패: {total_tests - passed_tests}")
    print(f"성공률: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\n상세 결과:")
    for test_name, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        print(f"  {test_name}: {status}")
    
    return passed_tests == total_tests

def run_crawling_test():
    """크롤링 기능 테스트"""
    print_header("RSS 크롤링 테스트 실행")
    
    try:
        from src.core.crawler import RSSCrawler
        from src.core.database import DatabaseManager
        from src.utils.config import Config
        
        print("🔧 시스템 초기화 중...")
        config = Config()
        db_manager = DatabaseManager(
            db_path=config.database_path,
            collection_name=config.collection_name
        )
        
        crawler = RSSCrawler(db_manager)
        
        print("📊 크롤링 전 통계:")
        before_count = db_manager.get_collection().count()
        print(f"  총 기사 수: {before_count:,}")
        
        print("\n🕷️ RSS 크롤링 시작...")
        stats = crawler.crawl_all_feeds()
        
        print("\n📊 크롤링 후 통계:")
        after_count = db_manager.get_collection().count()
        print(f"  총 기사 수: {after_count:,}")
        print(f"  새 기사 수: {stats.get('total_articles', 0):,}")
        
        print("\n✅ 크롤링 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 크롤링 테스트 실패: {e}")
        return False

def run_web_gui(port=5004):
    """웹 GUI 실행"""
    print_header(f"웹 GUI 실행 (포트: {port})")
    
    try:
        # simple_web_gui.py가 있는지 확인
        web_gui_file = project_root / "scripts" / "simple_web_gui.py"
        if not web_gui_file.exists():
            web_gui_file = project_root / "scripts" / "run_web_gui.py"
        
        if not web_gui_file.exists():
            print("❌ 웹 GUI 파일을 찾을 수 없습니다.")
            return False
        
        print(f"🌐 웹 서버 시작: http://localhost:{port}")
        print("💡 종료하려면 Ctrl+C를 누르세요")
        
        # 웹 서버 실행
        subprocess.run([
            sys.executable, str(web_gui_file)
        ], cwd=str(project_root))
        
        return True
        
    except KeyboardInterrupt:
        print("\n👋 웹 GUI 종료됨")
        return True
    except Exception as e:
        print(f"❌ 웹 GUI 실행 실패: {e}")
        return False

def generate_test_report(results):
    """테스트 결과 리포트 생성"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = project_root / f"test_report_{timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# RSS Crawler 테스트 리포트\n\n")
        f.write(f"**실행 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 테스트 결과\n\n")
        for test_name, success in results.items():
            status = "✅ 성공" if success else "❌ 실패"
            f.write(f"- **{test_name}**: {status}\n")
        
        passed = sum(results.values())
        total = len(results)
        f.write(f"\n**전체**: {total}개 중 {passed}개 성공 ({(passed/total)*100:.1f}%)\n")
    
    print(f"📄 테스트 리포트 생성됨: {report_file}")
    return report_file

def main():
    """메인 함수"""
    args = parse_arguments()
    
    print("🚀 RSS Crawler 통합 테스트 시스템")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = True
    results = {}
    
    try:
        if args.test_only or not (args.crawl_only or args.web_only):
            if not args.skip_tests:
                test_success = run_all_tests(args.auto)
                results['전체 테스트'] = test_success
                success = success and test_success
        
        if args.crawl_only or (not args.test_only and not args.web_only):
            if not args.skip_tests:
                crawl_success = run_crawling_test()
                results['크롤링 테스트'] = crawl_success
                success = success and crawl_success
        
        if args.web_only:
            web_success = run_web_gui(args.port)
            results['웹 GUI'] = web_success
            success = success and web_success
        
        # 리포트 생성 (자동 모드일 때만)
        if args.auto and results:
            generate_test_report(results)
        
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단됨")
        success = False
    except Exception as e:
        print(f"\n❌ 실행 중 오류: {e}")
        success = False
    
    print(f"\n{'='*80}")
    print(f"🏁 실행 완료: {'성공' if success else '실패'}")
    print(f"⏰ 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()