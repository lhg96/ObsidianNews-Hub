#!/usr/bin/env python3
"""
RSS 뉴스 수집기 (collector.py)
RSS 피드에서 뉴스를 수집하여 데이터베이스에 저장

사용법: python tests/collector.py [옵션]
옵션:
  --verbose, -v    상세 출력
  --feeds PATH     RSS 피드 설정 파일 경로
"""

import argparse
from utils import setup_project_path, init_components, print_header, print_error, print_success, get_feeds_file_path

def parse_arguments():
    """명령줄 인수 파싱"""
    parser = argparse.ArgumentParser(description='RSS 뉴스 수집 및 데이터베이스 저장')
    parser.add_argument('--verbose', '-v', action='store_true', help='상세 출력')
    parser.add_argument('--feeds', type=str, help='RSS 피드 설정 파일 경로')
    return parser.parse_args()

def main():
    """RSS 크롤링 실행"""
    project_root = setup_project_path()
    args = parse_arguments()
    
    try:
        print_header("RSS 뉴스 수집기", "RSS 피드에서 최신 뉴스를 수집합니다")
        
        # 핵심 컴포넌트 초기화
        db_manager, config, logger = init_components()
        
        # RSS Crawler 초기화
        from src.core.crawler import RSSCrawler
        crawler = RSSCrawler(db_manager=db_manager)
        
        # RSS 피드 파일 경로 결정
        if args.feeds:
            feeds_file = project_root / args.feeds
            if not feeds_file.exists():
                print_error(f"지정된 피드 파일이 없습니다: {feeds_file}")
                return False
        else:
            feeds_file = get_feeds_file_path(project_root)
        
        print(f"📂 RSS 피드 파일: {feeds_file}")
        
        # 크롤링 실행
        logger.info("Starting RSS crawling...")
        stats = crawler.crawl_all_feeds(
            feed_configs=crawler.load_feeds_from_csv(str(feeds_file))
        )
        
        # 결과 출력
        total_articles = stats.get('total_articles', 0)
        new_articles = stats.get('new_articles', 0)
        updated_articles = stats.get('updated_articles', 0)
        
        print_success(
            f"크롤링 완료: {total_articles}개 기사 처리",
            f"새 기사: {new_articles}개, 업데이트: {updated_articles}개"
        )
        
        if args.verbose:
            print("\n📊 상세 통계:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        print_error(f"크롤링 중 오류 발생: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)