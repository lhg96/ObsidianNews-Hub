#!/usr/bin/env python3
"""
간단한 RSS Crawler 웹 GUI - 테스트용
사용법: python scripts/simple_web_gui.py
"""

import sys
import os
from pathlib import Path
from flask import Flask, render_template, request, jsonify
import pandas as pd
from datetime import datetime
import threading
import time

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# RSS Crawler 시스템 import
try:
    from src.core.crawler import RSSCrawler
    from src.core.database import DatabaseManager
    from src.utils.config import Config
    CRAWLER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ RSS Crawler 모듈을 가져올 수 없습니다: {e}")
    CRAWLER_AVAILABLE = False

# 로그 저장을 위한 전역 변수
system_logs = []
log_lock = threading.Lock()
crawl_thread = None
crawl_status = {"running": False, "progress": 0, "total": 0}

# Flask 앱 생성 (템플릿 폴더 지정)
app = Flask(__name__, template_folder=str(project_root / 'templates'))

def add_log(message):
    """시스템 로그 추가"""
    with log_lock:
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        system_logs.append(log_entry)
        # 최대 50개 로그만 유지
        if len(system_logs) > 50:
            system_logs.pop(0)
        print(log_entry)  # 콘솔에도 출력

def crawl_feeds_async():
    """백그라운드에서 RSS 피드 크롤링 실행"""
    global crawl_status
    
    try:
        if not CRAWLER_AVAILABLE:
            add_log("❌ RSS Crawler 모듈을 사용할 수 없습니다")
            crawl_status["running"] = False
            return
        
        crawl_status["running"] = True
        crawl_status["progress"] = 0
        
        # RSS 피드 파일 읽기
        feeds_file = project_root / 'config' / 'rss_feeds.csv'
        if not feeds_file.exists():
            add_log("❌ RSS 피드 파일이 없습니다")
            crawl_status["running"] = False
            return
        
        df = pd.read_csv(feeds_file)
        crawl_status["total"] = len(df)
        add_log(f"📊 크롤링할 피드 수: {crawl_status['total']}개")
        
        # 설정 로드
        config = Config()
        
        # 데이터베이스 매니저 초기화
        db_manager = DatabaseManager(db_path=config.database_path)
        add_log("💾 데이터베이스 연결됨")
        
        # RSS 크롤러 초기화
        crawler = RSSCrawler(db_manager)
        add_log("🕷️ RSS Crawler 초기화 완료")
        
        # CSV 형식에 맞게 피드 데이터 변환
        feeds_data = []
        for _, row in df.iterrows():
            feeds_data.append({
                'name': row['source'] if 'source' in row else row.get('name', 'Unknown'),
                'url': row['rss_url'] if 'rss_url' in row else row.get('url', ''),
                'category': row.get('category', 'General')
            })
        
        # 각 피드 크롤링
        total_articles = 0
        for i, feed_info in enumerate(feeds_data):
            if not crawl_status["running"]:  # 중단 체크
                add_log("⏹️ 크롤링이 중단되었습니다")
                break
                
            feed_name = feed_info['name']
            feed_url = feed_info['url']
            
            add_log(f"📡 크롤링 중: {feed_name}")
            crawl_status["progress"] = i
            
            try:
                # 단일 피드 크롤링 (process_feed 메서드 사용)
                articles_count = crawler.process_feed(feed_name, feed_url)
                if articles_count > 0:
                    total_articles += articles_count
                    add_log(f"✅ {feed_name}: {articles_count}개 기사 수집")
                else:
                    add_log(f"⚠️ {feed_name}: 새 기사 없음")
                    
            except Exception as e:
                add_log(f"❌ {feed_name} 크롤링 오류: {str(e)}")
            
            # 진행률 업데이트
            crawl_status["progress"] = i + 1
            time.sleep(1)  # 서버 부하 방지
        
        # 크롤링 완료
        crawl_status["running"] = False
        add_log(f"🎉 크롤링 완료! 총 {total_articles}개 기사 수집")
        add_log(f"📈 데이터베이스 통계 업데이트됨")
        
    except Exception as e:
        add_log(f"❌ 크롤링 중 치명적 오류: {str(e)}")
        crawl_status["running"] = False

@app.route('/')
def index():
    """메인 페이지"""
    try:
        # 피드 수 계산
        feed_count = 0
        feeds_file = project_root / 'config' / 'rss_feeds.csv'
        
        add_log("🌐 간단 웹 GUI 시작됨...")
        add_log("📋 피드 목록 로딩 중...")
        
        if feeds_file.exists():
            df = pd.read_csv(feeds_file)
            feed_count = len(df)
            add_log(f"✅ 피드 {feed_count}개 로딩 완료")
        else:
            add_log("❌ 피드 파일을 찾을 수 없음")
        
        add_log("🌟 RSS Crawler 간단 웹 시스템 시작됨")
        
        return render_template('simple.html', feed_count=feed_count)
    except Exception as e:
        add_log(f"❌ 페이지 로드 오류: {e}")
        return f"❌ 페이지 로드 오류: {e}"

@app.route('/api/logs')
def get_logs():
    """시스템 로그 API"""
    try:
        with log_lock:
            return jsonify({'success': True, 'logs': system_logs.copy()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/feeds')
def get_feeds():
    """피드 목록 API"""
    try:
        feeds_file = project_root / 'config' / 'rss_feeds.csv'
        feeds = []
        
        if feeds_file.exists():
            df = pd.read_csv(feeds_file)
            # 컬럼명을 통일된 형태로 변환
            if 'source' in df.columns and 'rss_url' in df.columns:
                df = df.rename(columns={'source': 'name', 'rss_url': 'url'})
                # category 컬럼이 없다면 기본값 추가
                if 'category' not in df.columns:
                    df['category'] = 'News'
            # NaN 값을 기본값으로 대체
            df = df.fillna({'category': 'General'})
            feeds = df.to_dict('records')
        
        return jsonify({'success': True, 'feeds': feeds})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/feeds/add', methods=['POST'])
def add_feed():
    """피드 추가 API"""
    try:
        data = request.json
        name = data.get('name', '').strip()
        url = data.get('url', '').strip()
        
        add_log(f"📝 새 피드 추가 시도: {name}")
        
        if not name or not url:
            add_log("❌ 피드 이름 또는 URL이 비어있음")
            return jsonify({'success': False, 'error': '이름과 URL을 모두 입력해주세요'})
        
        feeds_file = project_root / 'config' / 'rss_feeds.csv'
        
        # 기존 피드 로드
        if feeds_file.exists():
            df = pd.read_csv(feeds_file)
            # 컬럼명을 통일된 형태로 변환
            if 'source' in df.columns and 'rss_url' in df.columns:
                df = df.rename(columns={'source': 'name', 'rss_url': 'url'})
                # category 컬럼이 없다면 기본값 추가
                if 'category' not in df.columns:
                    df['category'] = 'News'
            # NaN 값을 기본값으로 대체
            df = df.fillna({'category': 'General'})
            feeds_data = df.to_dict('records')
        else:
            feeds_data = []
        
        # 중복 체크
        for feed in feeds_data:
            if feed.get('url') == url:
                add_log(f"❌ 중복 URL: {url}")
                return jsonify({'success': False, 'error': '이미 등록된 URL입니다'})
            if feed.get('name') == name:
                add_log(f"❌ 중복 이름: {name}")
                return jsonify({'success': False, 'error': '이미 등록된 피드 이름입니다'})
        
        # 새 피드 추가
        feeds_data.append({
            'name': name, 
            'url': url, 
            'category': 'General'
        })
        
        # 저장 (다시 원래 컬럼명으로 변환)
        df = pd.DataFrame(feeds_data)
        if 'name' in df.columns and 'url' in df.columns:
            df = df.rename(columns={'name': 'source', 'url': 'rss_url'})
            # category 컬럼을 유지
        df.to_csv(feeds_file, index=False)
        
        add_log(f"✅ 피드 '{name}' 추가 완료")
        return jsonify({'success': True, 'message': f'피드 "{name}" 추가됨'})
        
    except Exception as e:
        add_log(f"❌ 피드 추가 중 오류: {str(e)}")
        return jsonify({'success': False, 'error': f'피드 추가 중 오류: {str(e)}'})

@app.route('/api/feeds/delete', methods=['POST'])
def delete_feed():
    """피드 삭제 API"""
    try:
        data = request.json
        index = data.get('index')
        
        if index is None:
            add_log("❌ 삭제할 피드 인덱스가 없음")
            return jsonify({'success': False, 'error': '삭제할 피드 인덱스가 없습니다'})
        
        feeds_file = project_root / 'config' / 'rss_feeds.csv'
        
        if not feeds_file.exists():
            add_log("❌ 피드 파일이 존재하지 않음")
            return jsonify({'success': False, 'error': '피드 파일이 존재하지 않습니다'})
        
        df = pd.read_csv(feeds_file)
        
        if index >= len(df):
            add_log(f"❌ 잘못된 피드 인덱스: {index}")
            return jsonify({'success': False, 'error': '잘못된 피드 인덱스입니다'})
        
        # 피드 삭제
        feed_name = df.iloc[index]['source'] if 'source' in df.columns else f'Feed {index}'
        add_log(f"🗑️ 피드 삭제 시도: {feed_name}")
        
        df = df.drop(df.index[index])
        df.to_csv(feeds_file, index=False)
        
        add_log(f"✅ 피드 '{feed_name}' 삭제 완료")
        return jsonify({'success': True, 'message': f'피드 "{feed_name}" 삭제됨'})
        
    except Exception as e:
        add_log(f"❌ 피드 삭제 중 오류: {str(e)}")
        return jsonify({'success': False, 'error': f'피드 삭제 중 오류: {str(e)}'})

@app.route('/api/crawl/start', methods=['POST'])
def start_crawl():
    """크롤링 시작 API"""
    global crawl_thread, crawl_status
    
    try:
        # 이미 실행 중인지 확인
        if crawl_status["running"]:
            add_log("⚠️ 크롤링이 이미 실행 중입니다")
            return jsonify({'success': False, 'error': '크롤링이 이미 실행 중입니다'})
        
        if not CRAWLER_AVAILABLE:
            add_log("❌ RSS Crawler 모듈을 사용할 수 없습니다")
            return jsonify({'success': False, 'error': 'RSS Crawler 모듈을 사용할 수 없습니다'})
        
        add_log("🚀 크롤링 시작 요청됨")
        
        feeds_file = project_root / 'config' / 'rss_feeds.csv'
        if not feeds_file.exists():
            add_log("❌ 등록된 피드가 없음")
            return jsonify({'success': False, 'error': '등록된 피드가 없습니다'})
        
        df = pd.read_csv(feeds_file)
        feed_count = len(df)
        
        if feed_count == 0:
            add_log("❌ 크롤링할 피드가 없음")
            return jsonify({'success': False, 'error': '크롤링할 피드가 없습니다'})
        
        add_log(f"📊 {feed_count}개 피드 발견")
        
        # 백그라운드 스레드에서 크롤링 시작
        crawl_thread = threading.Thread(target=crawl_feeds_async, daemon=True)
        crawl_thread.start()
        
        add_log("🔄 백그라운드 크롤링 스레드 시작됨")
        
        return jsonify({
            'success': True, 
            'message': f'{feed_count}개 피드에 대한 크롤링이 시작되었습니다'
        })
        
    except Exception as e:
        add_log(f"❌ 크롤링 시작 중 오류: {str(e)}")
        return jsonify({'success': False, 'error': f'크롤링 시작 중 오류: {str(e)}'})

@app.route('/api/crawl/status')
def crawl_status_api():
    """크롤링 상태 API"""
    try:
        return jsonify({
            'success': True,
            'status': crawl_status.copy()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/crawl/stop', methods=['POST'])
def stop_crawl():
    """크롤링 중단 API"""
    global crawl_status
    
    try:
        if not crawl_status["running"]:
            add_log("⚠️ 실행 중인 크롤링이 없습니다")
            return jsonify({'success': False, 'error': '실행 중인 크롤링이 없습니다'})
        
        add_log("⏹️ 크롤링 중단 요청됨")
        crawl_status["running"] = False
        
        return jsonify({
            'success': True,
            'message': '크롤링 중단이 요청되었습니다'
        })
        
    except Exception as e:
        add_log(f"❌ 크롤링 중단 중 오류: {str(e)}")
        return jsonify({'success': False, 'error': f'크롤링 중단 중 오류: {str(e)}'})

@app.route('/api/status')
def get_status():
    """시스템 상태 API"""
    try:
        feeds_file = project_root / 'config' / 'rss_feeds.csv'
        feed_count = 0
        
        if feeds_file.exists():
            df = pd.read_csv(feeds_file)
            feed_count = len(df)
        
        return jsonify({
            'success': True,
            'status': {
                'feed_count': feed_count,
                'system_status': 'online',
                'version': '1.0.0-simple'
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def check_requirements():
    """필요한 패키지 확인"""
    required_packages = ['flask', 'pandas']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 필요한 패키지가 없습니다: {', '.join(missing_packages)}")
        print("다음 명령으로 설치하세요:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def main():
    """메인 함수"""
    print("🌐 RSS Crawler 간단 웹 관리 시스템")
    print("=" * 50)
    
    # 패키지 확인
    if not check_requirements():
        sys.exit(1)
    
    # 프로젝트 구조 확인
    if not (project_root / 'templates' / 'simple.html').exists():
        print("❌ 템플릿 파일이 없습니다: templates/simple.html")
        sys.exit(1)
    
    # RSS 피드 파일 생성 (없는 경우)
    feeds_file = project_root / 'config' / 'rss_feeds.csv'
    if not feeds_file.exists():
        print("📝 RSS 피드 파일을 생성합니다...")
        # config 디렉토리 생성
        config_dir = project_root / 'config'
        config_dir.mkdir(exist_ok=True)
        
        sample_data = pd.DataFrame({
            'source': ['Sample Feed'],
            'rss_url': ['https://example.com/rss'],
            'category': ['General']
        })
        sample_data.to_csv(feeds_file, index=False)
        print(f"✅ 샘플 피드 파일 생성됨: {feeds_file}")
    
    print("\n🚀 서버를 시작합니다...")
    print("📱 브라우저에서 http://localhost:5004 을 열어주세요")
    print("🛑 종료하려면 Ctrl+C를 눌러주세요")
    print()
    
    try:
        app.run(
            host='0.0.0.0', 
            port=5004, 
            debug=False,  # 간단 버전에서는 디버그 모드 끄기
            use_reloader=False  # 자동 재시작 끄기
        )
    except KeyboardInterrupt:
        print("\n👋 서버가 종료되었습니다.")
    except Exception as e:
        print(f"❌ 서버 실행 오류: {e}")

if __name__ == "__main__":
    main()