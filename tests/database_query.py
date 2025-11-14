#!/usr/bin/env python3
"""
데이터베이스 조회 및 관리 스크립트
RSS 수집 데이터를 조회하고 관리하는 유틸리티

사용법: python tests/database_query.py [명령] [옵션]

명령:
  stats              데이터베이스 통계 표시
  recent [--days N]  최근 기사 표시 (기본값: 7일)
  search QUERY       벡터 검색 수행
  sources [--days N] 소스별 기사 수 표시 (기본값: 30일)
  export [--format]  데이터 내보내기 (json|csv)

옵션:
  --limit N          결과 개수 제한 (기본값: 10)
  --output PATH      결과를 파일로 저장
  --verbose, -v      상세 출력
"""

import sys
import argparse
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from utils import setup_project_path, init_components, print_header, print_error, print_success

def parse_arguments():
    """명령줄 인수 파싱"""
    parser = argparse.ArgumentParser(description='데이터베이스 조회 및 관리')
    
    subparsers = parser.add_subparsers(dest='command', help='사용 가능한 명령')
    
    # stats 명령
    stats_parser = subparsers.add_parser('stats', help='데이터베이스 통계 표시')
    
    # recent 명령
    recent_parser = subparsers.add_parser('recent', help='최근 기사 표시')
    recent_parser.add_argument('--days', type=int, default=7, help='최근 N일 (기본값: 7)')
    recent_parser.add_argument('--limit', type=int, default=10, help='결과 개수 (기본값: 10)')
    
    # search 명령
    search_parser = subparsers.add_parser('search', help='벡터 검색 수행')
    search_parser.add_argument('query', help='검색 쿼리')
    search_parser.add_argument('--limit', type=int, default=10, help='결과 개수 (기본값: 10)')
    
    # sources 명령
    sources_parser = subparsers.add_parser('sources', help='소스별 기사 수 표시')
    sources_parser.add_argument('--days', type=int, default=30, help='최근 N일 (기본값: 30)')
    
    # cleanup 명령
    cleanup_parser = subparsers.add_parser('cleanup', help='중복 제거 및 최적화')
    
    # 공통 옵션
    parser.add_argument('--output', type=str, help='결과를 JSON 파일로 저장')
    parser.add_argument('--verbose', '-v', action='store_true', help='상세 출력')
    
    return parser.parse_args()

def print_stats(db_manager, args):
    """데이터베이스 통계 출력"""
    print("📊 === Database Statistics ===")
    
    stats = db_manager.get_collection_stats()
    for key, value in stats.items():
        print(f"  {key}: {value:,}" if isinstance(value, (int, float)) else f"  {key}: {value}")
    
    # 추가 통계
    stats_data = db_manager.get_collection_stats()
    total_articles = stats_data.get('total_articles', 0)
    print(f"  Total Articles: {total_articles:,}")
    
    # 최근 활동
    recent_count = len(db_manager.get_recent_articles(days=7, limit=1000))
    print(f"  Articles (Last 7 days): {recent_count:,}")
    
    return {'stats': stats, 'total_articles': total_articles, 'recent_7d': recent_count}

def print_recent_articles(db_manager, args):
    """최근 기사 출력"""
    print(f"📰 === Recent Articles (Last {args.days} days, Limit: {args.limit}) ===")
    
    articles = db_manager.get_recent_articles(days=args.days, limit=args.limit)
    
    if not articles:
        print("  기사가 없습니다.")
        return {'articles': []}
    
    results = []
    for i, article in enumerate(articles, 1):
        metadata = article['metadata']
        date_str = datetime.fromtimestamp(metadata['date']).strftime('%Y-%m-%d %H:%M')
        
        print(f"  {i:2d}. [{metadata['source']}] {metadata['title']}")
        print(f"      📅 {date_str}")
        print(f"      🔗 {metadata.get('url', 'N/A')}")
        if args.verbose and 'summary' in metadata:
            summary = metadata['summary'][:100] + '...' if len(metadata['summary']) > 100 else metadata['summary']
            print(f"      � {summary}")
        print()
        
        results.append({
            'title': metadata['title'],
            'source': metadata['source'],
            'date': date_str,
            'url': metadata.get('url', ''),
            'summary': metadata.get('summary', '')
        })
    
    return {'articles': results}

def print_search_results(db_manager, args):
    """검색 결과 출력"""
    print(f"🔍 === Search Results for '{args.query}' (Limit: {args.limit}) ===")
    
    results = db_manager.search_articles(args.query, limit=args.limit)
    
    if not results:
        print("  검색 결과가 없습니다.")
        return {'results': []}
    
    search_results = []
    for i, result in enumerate(results, 1):
        # search_articles는 리스트 형태로 결과를 반환
        if isinstance(result, dict) and 'metadata' in result:
            metadata = result['metadata']
            content = result.get('content', result.get('text', ''))
            date_str = datetime.fromtimestamp(metadata['date']).strftime('%Y-%m-%d %H:%M')
            
            print(f"  {i:2d}. [{metadata['source']}] {metadata['title']}")
            print(f"      📅 {date_str}")
            print(f"      🔗 {metadata.get('url', 'N/A')}")
            if args.verbose and content:
                summary = content[:100] + '...' if len(content) > 100 else content
                print(f"      📝 {summary}")
            print()
            
            search_results.append({
                'title': metadata['title'],
                'source': metadata['source'],
                'date': date_str,
                'url': metadata.get('url', ''),
                'summary': content
            })
    
    return {'query': args.query, 'results': search_results}

def print_sources_stats(db_manager, args):
    """소스별 통계 출력"""
    print(f"📈 === Articles by Source (Last {args.days} days) ===")
    
    # 최근 기사 가져오기
    articles = db_manager.get_recent_articles(days=args.days, limit=10000)
    
    # 소스별 집계
    sources_count = {}
    for article in articles:
        source = article['metadata']['source']
        sources_count[source] = sources_count.get(source, 0) + 1
    
    # 정렬 및 출력
    sorted_sources = sorted(sources_count.items(), key=lambda x: x[1], reverse=True)
    
    total = sum(sources_count.values())
    print(f"  Total Sources: {len(sorted_sources)}, Total Articles: {total:,}")
    print()
    
    results = []
    for source, count in sorted_sources:
        percentage = (count / total * 100) if total > 0 else 0
        print(f"  {source:<30} {count:>6,} ({percentage:>5.1f}%)")
        results.append({'source': source, 'count': count, 'percentage': percentage})
    
    return {'total_sources': len(sorted_sources), 'total_articles': total, 'sources': results}

def perform_cleanup(db_manager, args):
    """데이터베이스 정리 수행"""
    print("🧹 === Database Cleanup ===")
    
    print("  데이터베이스 정리 기능은 구현 중입니다...")
    print("  현재 사용 가능한 기능:")
    print("    - 통계 확인: stats")
    print("    - 기사 검색: search")
    print("    - 최근 기사: recent")
    
    return {'status': 'not_implemented'}

def save_results(data, output_path):
    """결과를 JSON 파일로 저장"""
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 결과가 저장되었습니다: {output_file}")
        
    except Exception as e:
        print(f"❌ 파일 저장 실패: {e}")

def export_data(db_manager, args):
    """데이터 내보내기"""
    print("📤 === Data Export ===")
    
    # 전체 기사 가져오기
    articles = db_manager.get_recent_articles(days=365, limit=10000)  # 1년치 최대 10000개
    
    if not articles:
        print("  내보낼 데이터가 없습니다.")
        return {'status': 'no_data'}
    
    export_format = getattr(args, 'format', 'json')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if export_format == 'json':
        filename = f"rss_export_{timestamp}.json"
        export_data = []
        
        for article in articles:
            metadata = article['metadata']
            export_data.append({
                'title': metadata.get('title', ''),
                'source': metadata.get('source', ''),
                'url': metadata.get('url', ''),
                'date': datetime.fromtimestamp(metadata.get('date', 0)).isoformat(),
                'summary': metadata.get('summary', ''),
                'content': article.get('content', '')
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"  JSON 파일로 내보내기 완료: {filename}")
        return {'format': 'json', 'filename': filename, 'count': len(export_data)}
    
    else:
        print(f"  지원하지 않는 형식: {export_format}")
        return {'status': 'unsupported_format'}

def main():
    """메인 실행 함수"""
    project_root = setup_project_path()
    args = parse_arguments()
    
    if not args.command:
        print_error("명령을 지정해주세요", "--help 옵션으로 사용법을 확인하세요")
        sys.exit(1)
    
    try:
        print_header("RSS 데이터베이스 조회 도구", f"명령: {args.command}")
        
        # 핵심 컴포넌트 초기화
        db_manager, config, logger = init_components()
        
        # 명령 실행
        result_data = None
        if args.command == 'stats':
            result_data = print_stats(db_manager, args)
        elif args.command == 'recent':
            result_data = print_recent_articles(db_manager, args)
        elif args.command == 'search':
            result_data = print_search_results(db_manager, args)
        elif args.command == 'sources':
            result_data = print_sources_stats(db_manager, args)
        elif args.command == 'export':
            result_data = export_data(db_manager, args)
        
        # 결과 저장
        if args.output and result_data:
            save_results(result_data, args.output)
        
        print_success("데이터베이스 조회 완료")
        
    except Exception as e:
        print_error(f"데이터베이스 조회 중 오류 발생: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()