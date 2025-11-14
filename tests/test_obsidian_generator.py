#!/usr/bin/env python3
"""
Obsidian Generator 테스트 스크립트
통합된 obsidian_generator.py 모듈의 기능을 테스트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_obsidian_generator():
    """ObsidianGenerator 기본 기능 테스트"""
    try:
        from src.generators.obsidian_generator import ObsidianGenerator
        from src.core.database import DatabaseManager
        from src.utils.config import Config
        
        print("🧪 Obsidian Generator 테스트 시작...")
        
        # 설정 및 데이터베이스 초기화
        config = Config()
        db_manager = DatabaseManager(
            db_path=config.get('database.path', './data/chroma_db'),
            collection_name=config.get('database.collection_name', 'news_articles')
        )
        
        # Generator 초기화
        generator = ObsidianGenerator(db_manager=db_manager)
        print("✅ ObsidianGenerator 초기화 성공")
        
        # 테스트용 볼트 생성
        test_output = project_root / 'output' / 'obsidian' / 'Test-Vault'
        test_output.mkdir(parents=True, exist_ok=True)
        
        success = generator.create_vault(
            vault_path=test_output,
            vault_name='Test-Vault',
            days=1,
            structure='date',
            tag_system='nested',
            single_file=False,
            include_content=True
        )
        
        if success:
            print(f"✅ 테스트 볼트 생성 성공: {test_output}")
            
            # 생성된 파일 확인
            vault_files = list(test_output.rglob("*.md"))
            print(f"📊 생성된 파일 수: {len(vault_files)}개")
            
            # 주요 파일 존재 확인
            readme_exists = (test_output / 'README.md').exists()
            obsidian_settings_exist = (test_output / '.obsidian').exists()
            
            print(f"📄 README.md: {'✅' if readme_exists else '❌'}")
            print(f"⚙️ .obsidian 설정: {'✅' if obsidian_settings_exist else '❌'}")
            
            return True
        else:
            print("❌ 테스트 볼트 생성 실패")
            return False
            
    except ImportError as e:
        print(f"❌ Import 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        return False

def test_different_structures():
    """다양한 구조 옵션 테스트"""
    try:
        from src.generators.obsidian_generator import ObsidianGenerator
        from src.core.database import DatabaseManager
        from src.utils.config import Config
        
        print("\n🔧 구조별 테스트 시작...")
        
        config = Config()
        db_manager = DatabaseManager(
            db_path=config.get('database.path', './data/chroma_db'),
            collection_name=config.get('database.collection_name', 'news_articles')
        )
        generator = ObsidianGenerator(db_manager=db_manager)
        
        structures = ['date', 'source', 'category']
        results = {}
        
        for structure in structures:
            print(f"📂 {structure} 구조 테스트...")
            
            test_output = project_root / 'output' / 'obsidian' / f'Test-{structure.title()}'
            test_output.mkdir(parents=True, exist_ok=True)
            
            success = generator.create_vault(
                vault_path=test_output,
                vault_name=f'Test-{structure.title()}',
                days=1,
                structure=structure,
                tag_system='nested',
                single_file=False,
                include_content=False  # 빠른 테스트를 위해 내용 제외
            )
            
            results[structure] = success
            print(f"   {'✅ 성공' if success else '❌ 실패'}")
        
        print("\n📊 구조별 테스트 결과:")
        for structure, result in results.items():
            print(f"   {structure}: {'✅' if result else '❌'}")
        
        return all(results.values())
        
    except Exception as e:
        print(f"❌ 구조별 테스트 중 오류: {e}")
        return False

def main():
    """메인 테스트 실행"""
    print("=" * 60)
    print("🧪 Obsidian Generator 통합 테스트")
    print("=" * 60)
    
    # 기본 기능 테스트
    basic_test_result = test_obsidian_generator()
    
    # 구조별 테스트
    structure_test_result = test_different_structures()
    
    print("\n" + "=" * 60)
    print("📋 최종 테스트 결과")
    print("=" * 60)
    print(f"기본 기능: {'✅ 통과' if basic_test_result else '❌ 실패'}")
    print(f"구조별 테스트: {'✅ 통과' if structure_test_result else '❌ 실패'}")
    
    if basic_test_result and structure_test_result:
        print("\n🎉 모든 테스트 통과! ObsidianGenerator가 정상 작동합니다.")
        print("💡 사용법:")
        print("   python src/generators/obsidian_generator.py --help")
    else:
        print("\n⚠️  일부 테스트가 실패했습니다. 설정을 확인해주세요.")
        sys.exit(1)

if __name__ == "__main__":
    main()