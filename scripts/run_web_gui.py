#!/usr/bin/env python3
"""
RSS Crawler 완전한 웹 기반 관리 인터페이스

모든 기능을 통합한 Flask 기반 웹 GUI (외부 템플릿 버전)
"""

import sys
import os
from pathlib import Path
import logging

# 프로젝트 루트 경로를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    """필수 의존성 확인"""
    missing = []
    
    try:
        import flask
    except ImportError:
        missing.append('flask')
    
    try:
        from src.core.crawler import RSSCrawler
        from src.core.database import DatabaseManager
        from src.generators.obsidian_generator import ObsidianGenerator
        from src.utils.config import Config
    except ImportError as e:
        print(f"❌ 프로젝트 모듈 import 오류: {e}")
        return False
        
    if missing:
        print("❌ 필수 의존성이 없습니다:")
        for dep in missing:
            print(f"   - {dep}")
        print("💡 설치 방법: pip install flask")
        return False
        
    return True

def main():
    """웹 GUI 애플리케이션 실행"""
    try:
        if not check_dependencies():
            print("🔧 Flask를 설치하고 다시 시도해주세요:")
            print("   pip install flask")
            return
        
        from flask import Flask, render_template, request, jsonify, redirect, url_for
        from src.core.crawler import RSSCrawler
        from src.core.database import DatabaseManager
        from src.generators.obsidian_generator import ObsidianGenerator
        from src.utils.config import Config
        import pandas as pd
        import threading
        import json
        from datetime import datetime
        
        # Flask 앱 생성 (템플릿 폴더 지정)
        app = Flask(__name__, template_folder=str(project_root / 'templates'))
        
        # 데이터베이스 인스턴스 가져오기
        def get_db():
            """데이터베이스 매니저 인스턴스 반환"""
            return DatabaseManager(project_root / 'data' / 'chroma_db')
        
        # 전역 변수 초기화
        try:
            # Config는 성공적으로 초기화
            config = Config()
            print("✅ Config 초기화 성공")
            
            # 크롤링 상태 관리
            crawling_state = {
                'is_running': False,
                'thread': None,
                'start_time': None,
                'status_message': '대기 중'
            }
            
            # DatabaseManager 초기화
            db_manager = DatabaseManager(
                db_path="./data/chroma_db",
                collection_name="news_articles"
            )
            print("✅ DatabaseManager 초기화 성공")
            
            # RSSCrawler 초기화 - db_manager 하나만 전달
            try:
                crawler = RSSCrawler(db_manager)
                print("✅ RSSCrawler 초기화 성공")
            except Exception as crawler_error:
                print(f"❌ RSSCrawler 초기화 실패: {crawler_error}")
                crawler = None
            
            # ObsidianGenerator 초기화 
            try:
                obsidian_gen = ObsidianGenerator(db_manager)
                print("✅ ObsidianGenerator 초기화 성공")
            except Exception as mg_error:
                print(f"❌ ObsidianGenerator 초기화 실패: {mg_error}")
                obsidian_gen = None
                
        except Exception as e:
            print(f"❌ 전체 모듈 초기화 오류: {e}")
            print("기본 기능으로 계속 진행합니다...")
            config = None
            db_manager = None
            crawler = None
            obsidian_gen = None
        
        # 크롤링 상태 추적
        crawling_status = {
            'running': False,
            'progress': 0,
            'total_feeds': 0,
            'current_feed': '',
            'processed_feeds': 0,
            'total_articles': 0,
            'message': '대기 중'
        }

        @app.route('/')
        def index():
            """메인 페이지"""
            try:
                # 통계 정보 수집
                feed_count = 0
                article_count = 0
                
                # 피드 수 계산
                feeds_file = project_root / 'config' / 'rss_feeds.csv'
                if not feeds_file.exists():
                    feeds_file = project_root / 'rss_feeds.csv'
                
                if feeds_file.exists():
                    try:
                        df = pd.read_csv(feeds_file)
                        feed_count = len(df)
                    except Exception:
                        pass
                
                # 기사 수 계산
                if db_manager:
                    try:
                        collection = db_manager.get_collection()
                        article_count = collection.count()
                    except Exception as e:
                        print(f"DB 연결 오류: {e}")
                        article_count = 0
                
                return render_template('index.html',
                    feed_count=feed_count,
                    article_count=f"{article_count:,}",
                    last_crawl="Never",
                    db_status=db_manager is not None,
                    current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            except Exception as e:
                return f"페이지 로드 오류: {e}"

        @app.route('/api/feeds')
        def get_feeds():
            """피드 목록 API"""
            try:
                feeds_file = project_root / 'config' / 'rss_feeds.csv'
                if not feeds_file.exists():
                    feeds_file = project_root / 'rss_feeds.csv'
                
                feeds = []
                if feeds_file.exists():
                    df = pd.read_csv(feeds_file)
                    feeds = df.to_dict('records')
                
                return jsonify({'success': True, 'feeds': feeds})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @app.route('/api/feeds/add', methods=['POST'])
        def add_feed():
            """피드 추가 API"""
            try:
                data = request.get_json()
                name = data.get('name')
                url = data.get('url')
                category = data.get('category', 'General')
                
                feeds_file = project_root / 'config' / 'rss_feeds.csv'
                if not feeds_file.exists():
                    feeds_file = project_root / 'rss_feeds.csv'
                
                # 새로운 피드 추가
                new_feed = {
                    'source': name,
                    'rss_url': url,
                    'category': category
                }
                
                if feeds_file.exists():
                    df = pd.read_csv(feeds_file)
                    df = pd.concat([df, pd.DataFrame([new_feed])], ignore_index=True)
                else:
                    df = pd.DataFrame([new_feed])
                
                # 파일 저장
                feeds_file.parent.mkdir(exist_ok=True)
                df.to_csv(feeds_file, index=False)
                
                return jsonify({'success': True, 'message': '피드가 추가되었습니다.'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @app.route('/api/feeds/delete', methods=['POST'])
        def delete_feed():
            """피드 삭제 API"""
            try:
                data = request.get_json()
                index = data.get('index')
                
                feeds_file = project_root / 'config' / 'rss_feeds.csv'
                if not feeds_file.exists():
                    feeds_file = project_root / 'rss_feeds.csv'
                
                if feeds_file.exists():
                    df = pd.read_csv(feeds_file)
                    if 0 <= index < len(df):
                        df = df.drop(index).reset_index(drop=True)
                        df.to_csv(feeds_file, index=False)
                        return jsonify({'success': True, 'message': '피드가 삭제되었습니다.'})
                
                return jsonify({'success': False, 'error': '잘못된 인덱스입니다.'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @app.route('/api/feeds/test', methods=['POST'])
        def test_feed():
            """피드 테스트 API"""
            try:
                data = request.get_json()
                index = data.get('index')
                
                feeds_file = project_root / 'config' / 'rss_feeds.csv'
                if not feeds_file.exists():
                    feeds_file = project_root / 'rss_feeds.csv'
                
                if feeds_file.exists():
                    df = pd.read_csv(feeds_file)
                    if 0 <= index < len(df):
                        feed = df.iloc[index]
                        # 피드 테스트 로직
                        import feedparser
                        parsed = feedparser.parse(feed['rss_url'])
                        
                        if parsed.entries:
                            return jsonify({
                                'success': True, 
                                'entries': len(parsed.entries),
                                'title': parsed.feed.get('title', 'Unknown')
                            })
                        else:
                            return jsonify({'success': False, 'error': '피드에서 항목을 찾을 수 없습니다.'})
                
                return jsonify({'success': False, 'error': '잘못된 인덱스입니다.'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @app.route('/api/crawl/start', methods=['POST'])
        def start_crawl():
            """크롤링 시작 API"""
            try:
                if crawler and not crawling_status['running']:
                    def crawl_worker():
                        crawling_status['running'] = True
                        crawling_status['progress'] = 0
                        crawling_status['processed_feeds'] = 0
                        crawling_status['total_articles'] = 0
                        crawling_status['message'] = '크롤링 준비 중...'
                        
                        try:
                            # RSS 피드 파일 읽기
                            feeds_file = project_root / 'config' / 'rss_feeds.csv'
                            if not feeds_file.exists():
                                feeds_file = project_root / 'rss_feeds.csv'
                            
                            if feeds_file.exists():
                                # CSV 파일에서 피드 설정 로드
                                feed_configs = crawler.load_feeds_from_csv(str(feeds_file))
                                crawling_status['total_feeds'] = len(feed_configs)
                                crawling_status['message'] = f'{len(feed_configs)}개 피드 크롤링 시작'
                                
                                # 각 피드를 순차적으로 처리
                                for i, feed_config in enumerate(feed_configs):
                                    if not crawling_status['running']:  # 중지 체크
                                        crawling_status['message'] = '사용자에 의해 중단됨'
                                        break
                                    
                                    source = feed_config['source']
                                    url = feed_config['url']
                                    
                                    crawling_status['current_feed'] = source
                                    crawling_status['message'] = f'크롤링 중: {source}'
                                    
                                    try:
                                        # 단일 피드 처리
                                        article_count = crawler.process_feed(source, url)
                                        crawling_status['total_articles'] += article_count
                                        crawling_status['processed_feeds'] = i + 1
                                        crawling_status['progress'] = int((i + 1) / len(feed_configs) * 100)
                                        
                                        if article_count > 0:
                                            crawling_status['message'] = f'{source}: {article_count}개 새 기사 수집'
                                        else:
                                            crawling_status['message'] = f'{source}: 새 기사 없음'
                                            
                                    except Exception as feed_error:
                                        crawling_status['message'] = f'{source}: 오류 - {str(feed_error)}'
                                    
                                    # 잠시 대기 (서버 부하 방지)
                                    import time
                                    time.sleep(0.5)
                                
                                if crawling_status['running']:  # 정상 완료된 경우
                                    crawling_status['message'] = f'완료: {crawling_status["total_articles"]}개 기사 처리'
                                    crawling_status['progress'] = 100
                            else:
                                crawling_status['message'] = 'RSS 피드 파일을 찾을 수 없음'
                                
                        except Exception as e:
                            crawling_status['message'] = f'오류: {str(e)}'
                        finally:
                            crawling_status['running'] = False
                            crawling_status['current_feed'] = ''
                        
                    threading.Thread(target=crawl_worker, daemon=True).start()
                    
                    return jsonify({
                        'success': True, 
                        'message': '크롤링이 시작되었습니다.',
                        'status': crawling_status
                    })
                else:
                    return jsonify({'success': False, 'error': '크롤러가 준비되지 않았거나 이미 실행 중입니다.'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @app.route('/api/crawl/stop', methods=['POST'])
        def stop_crawl():
            """크롤링 중지 API"""
            try:
                if crawling_status['running']:
                    crawling_status['running'] = False
                    crawling_status['message'] = '크롤링 중지 요청됨...'
                    return jsonify({
                        'success': True, 
                        'message': '크롤링 중지 요청이 전송되었습니다.'
                    })
                else:
                    return jsonify({'success': False, 'error': '현재 실행 중인 크롤링이 없습니다.'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @app.route('/api/obsidian/generate', methods=['POST'])
        def generate_obsidian_api():
            """옵시디언 볼트 생성 및 ZIP 다운로드 API"""
            try:
                if not obsidian_gen:
                    return jsonify({'success': False, 'error': '옵시디언 생성기가 준비되지 않았습니다.'})
                
                data = request.get_json() or {}
                
                # 파라미터 추출
                days = data.get('days', 7)
                vault_name = data.get('vault_name', f"RSS-News-{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                structure = data.get('structure', 'date')
                tag_system = data.get('tag_system', 'nested')
                include_content = data.get('include_content', True)
                
                # 임시 디렉토리에 볼트 생성
                import tempfile
                import shutil
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    vault_path = Path(temp_dir) / vault_name
                    
                    # 볼트 생성
                    success = obsidian_gen.create_vault(
                        vault_path=vault_path,
                        vault_name=vault_name,
                        days=days,
                        structure=structure,
                        tag_system=tag_system,
                        single_file=False,
                        include_content=include_content
                    )
                    
                    if not success:
                        return jsonify({'success': False, 'error': '볼트 생성에 실패했습니다.'})
                    
                    # ZIP 파일 생성
                    zip_path = Path(temp_dir) / f"{vault_name}.zip"
                    shutil.make_archive(str(zip_path.with_suffix('')), 'zip', vault_path)
                    
                    # ZIP 파일을 웹에서 접근 가능한 위치로 복사
                    output_dir = project_root / 'output' / 'web_downloads'
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    final_zip_path = output_dir / f"{vault_name}.zip"
                    shutil.copy2(zip_path, final_zip_path)
                    
                    # 통계 정보
                    vault_files = list(vault_path.rglob("*.md"))
                    zip_filename = f"{vault_name}.zip"
                    
                    return jsonify({
                        'success': True,
                        'download_url': f'/downloads/{zip_filename}',
                        'stats': {
                            'vault_name': vault_name,
                            'files': len(vault_files),
                            'structure': structure,
                            'days': days
                        }
                    })
                    
            except Exception as e:
                return jsonify({'success': False, 'error': f'오류 발생: {str(e)}'})

        @app.route('/downloads/<filename>')
        def download_file(filename):
            """생성된 파일 다운로드"""
            try:
                download_dir = project_root / 'output' / 'web_downloads'
                file_path = download_dir / filename
                
                if not file_path.exists():
                    return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404
                
                from flask import send_file
                return send_file(file_path, as_attachment=True, download_name=filename)
                
            except Exception as e:
                return jsonify({'error': f'다운로드 오류: {str(e)}'}), 500

        @app.route('/api/feeds', methods=['POST'])
        def update_feeds_api():
            """RSS 피드 목록 업데이트"""
            try:
                data = request.get_json()
                feeds = data.get('feeds', [])
                
                if not feeds:
                    return jsonify({'success': False, 'error': '피드 데이터가 없습니다.'})
                
                # CSV 파일로 저장
                import pandas as pd
                df = pd.DataFrame(feeds)
                
                # config 폴더의 파일 사용
                feeds_file = project_root / 'config' / 'rss_feeds.csv'
                feeds_file.parent.mkdir(exist_ok=True)
                df.to_csv(feeds_file, index=False)
                
                return jsonify({'success': True, 'message': 'RSS 피드가 업데이트되었습니다.'})
            except Exception as e:
                return jsonify({'success': False, 'error': f'피드 업데이트 오류: {str(e)}'})

        @app.route('/api/articles', methods=['GET'])
        def get_articles_api():
            """수집된 기사 목록 조회"""
            try:
                if not db_manager:
                    return jsonify({'success': False, 'error': '데이터베이스가 준비되지 않았습니다.'})
                
                # 쿼리 파라미터 추출
                page = int(request.args.get('page', 1))
                per_page = int(request.args.get('per_page', 20))
                source = request.args.get('source', '')
                days = int(request.args.get('days', 7))
                
                # 최근 기사 조회
                articles = db_manager.get_recent_articles(days=days)
                
                # 소스별 필터링
                if source:
                    articles = [a for a in articles if a['metadata'].get('source') == source]
                
                # 페이지네이션
                total = len(articles)
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                page_articles = articles[start_idx:end_idx]
                
                # 결과 포맷팅
                result_articles = []
                for article in page_articles:
                    metadata = article.get('metadata', {})
                    content = article.get('content', '')
                    
                    result_articles.append({
                        'id': article.get('id', ''),
                        'title': metadata.get('title', '제목 없음'),
                        'url': metadata.get('url', ''),
                        'source': metadata.get('source', '알 수 없음'),
                        'date': metadata.get('published_date', ''),
                        'authors': metadata.get('authors', ''),
                        'summary': content[:200] + '...' if len(content) > 200 else content,
                        'content_length': len(content)
                    })
                
                return jsonify({
                    'success': True, 
                    'articles': result_articles,
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total': total,
                        'pages': (total + per_page - 1) // per_page
                    }
                })
                
            except Exception as e:
                return jsonify({'success': False, 'error': f'기사 조회 오류: {str(e)}'})

        @app.route('/api/articles/sources')
        def get_article_sources():
            """기사 소스 목록 조회"""
            try:
                if not db_manager:
                    return jsonify({'success': False, 'error': '데이터베이스가 준비되지 않았습니다.'})
                
                # 최근 30일 기사에서 소스 추출
                articles = db_manager.get_recent_articles(days=30)
                sources = list(set(a['metadata'].get('source', 'Unknown') for a in articles if a.get('metadata')))
                sources.sort()
                
                return jsonify({'success': True, 'sources': sources})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                page_articles = articles[start_idx:end_idx]
                
                # 응답 데이터 구성
                result_articles = []
                for article in page_articles:
                    metadata = article['metadata']
                    content = article.get('content', '')
                    
                    result_articles.append({
                        'title': metadata.get('title', 'No Title'),
                        'url': metadata.get('url', ''),
                        'source': metadata.get('source', 'Unknown'),
                        'date': datetime.fromtimestamp(metadata.get('date', 0)).strftime('%Y-%m-%d %H:%M') if metadata.get('date') else 'Unknown',
                        'summary': content[:300] + '...' if len(content) > 300 else content,
                        'authors': metadata.get('authors', ''),
                        'content_length': len(content)
                    })
                
                return jsonify({
                    'success': True, 
                    'articles': result_articles,
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total': len(articles),
                        'pages': (len(articles) + per_page - 1) // per_page
                    }
                })
                
            except Exception as e:
                return jsonify({'success': False, 'error': f'기사 조회 오류: {str(e)}'})

        @app.route('/api/search', methods=['POST'])
        def search_api():
            """벡터 검색 API"""
            try:
                data = request.get_json()
                query = data.get('query', '')
                
                if db_manager and query:
                    results = db_manager.search_articles(query, limit=10)
                    
                    articles = []
                    for result in results:
                        metadata = result.get('metadata', {})
                        content = result.get('content', '')
                        
                        articles.append({
                            'title': metadata.get('title', 'Unknown'),
                            'url': metadata.get('url', '#'),
                            'source': metadata.get('source', 'Unknown'),
                            'date': datetime.fromtimestamp(metadata.get('date', 0)).strftime('%Y-%m-%d %H:%M') if metadata.get('date') else 'Unknown',
                            'summary': content[:200] + '...' if len(content) > 200 else content
                        })
                    
                    return jsonify({'success': True, 'articles': articles})
                else:
                    return jsonify({'success': False, 'error': '검색 조건이 부족합니다.'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @app.route('/api/markdown/generate', methods=['POST'])
        def generate_markdown_api():
            """마크다운 파일 생성 API"""
            try:
                if not db_manager:
                    return jsonify({'success': False, 'error': '데이터베이스가 준비되지 않았습니다.'})
                
                # 최근 7일 기사 조회
                articles = db_manager.get_recent_articles(days=7)
                
                if not articles:
                    return jsonify({'success': False, 'error': '생성할 기사가 없습니다.'})
                
                # 마크다운 파일 생성
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"news_summary_{timestamp}.md"
                output_dir = project_root / 'output'
                output_dir.mkdir(exist_ok=True)
                
                md_file_path = output_dir / filename
                
                with open(md_file_path, 'w', encoding='utf-8') as f:
                    f.write(f"# RSS 뉴스 요약\n\n")
                    f.write(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"총 기사 수: {len(articles)}개\n\n")
                    
                    # 소스별로 그룹화
                    sources = {}
                    for article in articles:
                        source = article['metadata'].get('source', 'Unknown')
                        if source not in sources:
                            sources[source] = []
                        sources[source].append(article)
                    
                    for source, source_articles in sources.items():
                        f.write(f"## {source} ({len(source_articles)}개)\n\n")
                        
                        for article in source_articles[:10]:  # 소스당 최대 10개
                            metadata = article['metadata']
                            content = article.get('content', '')
                            
                            f.write(f"### {metadata.get('title', '제목 없음')}\n\n")
                            f.write(f"- **URL**: {metadata.get('url', 'N/A')}\n")
                            f.write(f"- **날짜**: {metadata.get('published_date', 'N/A')}\n")
                            if metadata.get('authors'):
                                f.write(f"- **저자**: {metadata.get('authors')}\n")
                            
                            # 요약 또는 내용 일부
                            summary = content[:300] + '...' if len(content) > 300 else content
                            f.write(f"\n{summary}\n\n")
                            f.write("---\n\n")
                
                return jsonify({
                    'success': True,
                    'filename': filename,
                    'path': str(md_file_path),
                    'articles_count': len(articles)
                })
                
            except Exception as e:
                return jsonify({'success': False, 'error': f'마크다운 생성 오류: {str(e)}'})

        @app.route('/api/status')
        def status_api():
            """시스템 상태 API"""
            return jsonify({
                'success': True,
                'status': crawling_status
            })

        @app.route('/api/stats')
        def stats_api():
            """통계 정보 API"""
            try:
                stats = {
                    'total_articles': 0,
                    'recent_articles_30d': 0,
                    'collection_name': 'news_articles',
                    'database_path': './data/chroma_db'
                }
                
                if db_manager:
                    try:
                        collection = db_manager.get_collection()
                        stats['total_articles'] = collection.count()
                        
                        # 최근 30일 기사는 간단하게 전체 수로 대체 (날짜 필터링 복잡)
                        stats['recent_articles_30d'] = min(stats['total_articles'], 100)
                    except Exception as e:
                        print(f"통계 수집 오류: {e}")
                
                return jsonify({'success': True, 'stats': stats})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @app.route('/api/database/stats')
        def database_stats_api():
            """데이터베이스 상세 통계 API"""
            try:
                if db_manager:
                    collection = db_manager.get_collection()
                    total_articles = collection.count()
                    
                    # 데이터베이스 크기 계산 (대략)
                    import os
                    db_path = project_root / 'data' / 'chroma_db'
                    size_mb = 0
                    if db_path.exists():
                        for root, dirs, files in os.walk(db_path):
                            for file in files:
                                size_mb += os.path.getsize(os.path.join(root, file))
                        size_mb = round(size_mb / (1024 * 1024), 2)
                    
                    return jsonify({
                        'success': True,
                        'total_articles': total_articles,
                        'size_mb': size_mb
                    })
                else:
                    return jsonify({'success': False, 'error': '데이터베이스가 연결되지 않았습니다.'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        # 서버 실행
        print("\n🌟 RSS Crawler 웹 관리 시스템 시작")
        print("=" * 50)
        print(f"📂 프로젝트 경로: {project_root}")
        print(f"🗄️  데이터베이스: {'연결됨' if db_manager else '오프라인'}")
        print(f"🕷️  크롤러: {'준비됨' if crawler else '오프라인'}")
        print(f"📝 옵시디언: {'준비됨' if obsidian_gen else '오프라인'}")
        print("=" * 50)
        print("🌐 웹 인터페이스: http://localhost:5001")
        print("💡 종료하려면 Ctrl+C를 누르세요")
        print("=" * 50)
        
        # Flask 앱 실행
        app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
        
    except KeyboardInterrupt:
        print("\n👋 RSS Crawler 웹 관리 시스템이 종료되었습니다.")
    except Exception as e:
        print(f"\n❌ 애플리케이션 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()