#!/usr/bin/env python3
"""
설정 및 유틸리티 기능 테스트
Config 로딩, 로깅, 파일 I/O 등 테스트
"""

import sys
import os
from pathlib import Path
import tempfile

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_config_loading():
    """설정 파일 로딩 테스트"""
    print("=" * 60)
    print("⚙️ 설정 파일 로딩 테스트")
    print("=" * 60)
    
    try:
        from src.utils.config import config, Config
        
        print("📂 Config 객체 초기화 중...")
        
        # 전역 config 객체 테스트
        print("✅ 전역 config 객체 로드 성공")
        
        # 주요 설정값들 확인
        test_configs = [
            ('database.collection_name', 'news_articles'),
            ('crawler.delay', 1),
            ('crawler.retry_count', 3),
            ('markdown.keywords_count', 5),
            ('markdown.content_preview_length', 300),
            ('logging.level', 'INFO')
        ]
        
        print("\n📋 주요 설정값 확인:")
        
        for config_key, expected_default in test_configs:
            try:
                value = config.get(config_key, expected_default)
                print(f"   ✅ {config_key}: {value}")
            except Exception as e:
                print(f"   ❌ {config_key}: 오류 - {e}")
        
        # 속성 접근 테스트
        print("\n🔧 속성 접근 테스트:")
        
        properties_to_test = [
            'collection_name',
            'database_path', 
            'delay',
            'retry_count',
            'output_dir',
            'log_level'
        ]
        
        for prop in properties_to_test:
            try:
                value = getattr(config, prop)
                print(f"   ✅ config.{prop}: {value}")
            except AttributeError:
                print(f"   ⚠️ config.{prop}: 속성 없음")
            except Exception as e:
                print(f"   ❌ config.{prop}: 오류 - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 설정 로딩 테스트 실패: {e}")
        return False

def test_logger_functionality():
    """로거 기능 테스트"""
    print("\n" + "=" * 60)
    print("📝 로거 기능 테스트")
    print("=" * 60)
    
    try:
        from src.utils.logger import setup_logger
        
        # 테스트용 로거 생성
        test_logger = setup_logger("test_module")
        
        print("🔧 로거 초기화 성공")
        
        # 다양한 레벨의 로그 메시지 테스트
        print("\n📊 다양한 로그 레벨 테스트:")
        
        test_logger.debug("디버그 메시지 테스트")
        print("   ✅ DEBUG 레벨 테스트 완료")
        
        test_logger.info("정보 메시지 테스트")
        print("   ✅ INFO 레벨 테스트 완료")
        
        test_logger.warning("경고 메시지 테스트")
        print("   ✅ WARNING 레벨 테스트 완료")
        
        test_logger.error("에러 메시지 테스트")
        print("   ✅ ERROR 레벨 테스트 완료")
        
        # 로거 속성 확인
        print(f"\n🔍 로거 속성:")
        print(f"   이름: {test_logger.name}")
        print(f"   레벨: {test_logger.level}")
        print(f"   핸들러 수: {len(test_logger.handlers)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 로거 기능 테스트 실패: {e}")
        return False

def test_file_operations():
    """파일 연산 테스트"""
    print("\n" + "=" * 60)
    print("💾 파일 연산 테스트")
    print("=" * 60)
    
    try:
        import pandas as pd
        
        # 임시 디렉토리에서 테스트
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            print(f"📁 임시 디렉토리: {temp_path}")
            
            # CSV 파일 생성 테스트
            test_data = {
                'name': ['Test Feed 1', 'Test Feed 2', 'Test Feed 3'],
                'url': [
                    'https://example.com/feed1.xml',
                    'https://example.com/feed2.xml', 
                    'https://example.com/feed3.xml'
                ],
                'category': ['Tech', 'News', 'Science']
            }
            
            csv_file = temp_path / 'test_feeds.csv'
            df = pd.DataFrame(test_data)
            
            print("📝 CSV 파일 생성 중...")
            df.to_csv(csv_file, index=False)
            
            if csv_file.exists():
                print("   ✅ CSV 파일 생성 성공")
                
                # CSV 파일 읽기 테스트
                loaded_df = pd.read_csv(csv_file)
                
                if len(loaded_df) == len(df):
                    print("   ✅ CSV 파일 읽기 성공")
                    print(f"   📊 로드된 레코드 수: {len(loaded_df)}")
                else:
                    print("   ❌ CSV 파일 읽기 실패: 레코드 수 불일치")
            else:
                print("   ❌ CSV 파일 생성 실패")
            
            # 마크다운 파일 생성 테스트
            md_file = temp_path / 'test_output.md'
            
            markdown_content = """# 테스트 마크다운 파일

## 개요
이것은 파일 연산 테스트를 위한 마크다운 파일입니다.

## 기능 목록
- RSS 피드 수집
- 기사 분석  
- 마크다운 생성

## 결론
테스트가 성공적으로 완료되었습니다.
"""
            
            print("📄 마크다운 파일 생성 중...")
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            if md_file.exists():
                print("   ✅ 마크다운 파일 생성 성공")
                
                # 파일 크기 확인
                file_size = md_file.stat().st_size
                print(f"   📏 파일 크기: {file_size} bytes")
                
                # 파일 내용 읽기 테스트
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if len(content) > 0:
                    print("   ✅ 마크다운 파일 읽기 성공")
                    print(f"   📝 내용 길이: {len(content)}자")
                else:
                    print("   ❌ 마크다운 파일이 비어있습니다")
            else:
                print("   ❌ 마크다운 파일 생성 실패")
        
        return True
        
    except Exception as e:
        print(f"❌ 파일 연산 테스트 실패: {e}")
        return False

def test_project_structure():
    """프로젝트 구조 검증 테스트"""
    print("\n" + "=" * 60)
    print("🏗️ 프로젝트 구조 검증 테스트")
    print("=" * 60)
    
    try:
        # 필수 디렉토리들
        required_dirs = [
            'src',
            'src/core',
            'src/generators',
            'src/utils',
            'scripts',
            'config',
            'data'
        ]
        
        print("📁 필수 디렉토리 확인:")
        missing_dirs = []
        
        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                print(f"   ✅ {dir_name}")
            else:
                print(f"   ❌ {dir_name} (누락)")
                missing_dirs.append(dir_name)
        
        # 필수 파일들
        required_files = [
            'requirements.txt',
            'README.md',
            'src/__init__.py',
            'src/core/database.py',
            'src/core/crawler.py',
            'src/utils/config.py',
            'src/utils/logger.py'
        ]
        
        print("\n📄 필수 파일 확인:")
        missing_files = []
        
        for file_name in required_files:
            file_path = project_root / file_name
            if file_path.exists() and file_path.is_file():
                file_size = file_path.stat().st_size
                print(f"   ✅ {file_name} ({file_size} bytes)")
            else:
                print(f"   ❌ {file_name} (누락)")
                missing_files.append(file_name)
        
        # 결과 평가
        if not missing_dirs and not missing_files:
            print("\n🎉 프로젝트 구조가 완벽합니다!")
            return True
        else:
            if missing_dirs:
                print(f"\n⚠️ 누락된 디렉토리: {missing_dirs}")
            if missing_files:
                print(f"⚠️ 누락된 파일: {missing_files}")
            return False
            
    except Exception as e:
        print(f"❌ 프로젝트 구조 검증 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🧪 RSS Crawler - 설정 및 유틸리티 테스트 시작")
    
    results = []
    
    # 1. 설정 로딩 테스트
    config_success = test_config_loading()
    results.append(("설정 로딩", config_success))
    
    # 2. 로거 기능 테스트
    logger_success = test_logger_functionality()
    results.append(("로거 기능", logger_success))
    
    # 3. 파일 연산 테스트
    file_success = test_file_operations()
    results.append(("파일 연산", file_success))
    
    # 4. 프로젝트 구조 테스트
    structure_success = test_project_structure()
    results.append(("프로젝트 구조", structure_success))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📋 유틸리티 테스트 결과 요약")
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
        print("🎉 모든 유틸리티 테스트가 성공적으로 완료되었습니다!")
    else:
        print("⚠️ 일부 테스트가 실패했습니다. 설정을 확인해주세요.")

if __name__ == "__main__":
    main()