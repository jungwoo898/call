#!/usr/bin/env python3
"""
Database Service 호환성 검증 스크립트 (PostgreSQL 전용)
"""

import sys
import importlib

def test_imports():
    """필요한 라이브러리들이 정상적으로 import되는지 테스트"""
    
    required_modules = [
        'fastapi',
        'uvicorn', 
        'pydantic',
        'sqlalchemy',
        'asyncpg',  # PostgreSQL 전용
        'psycopg2'  # PostgreSQL 전용
    ]
    
    failed_imports = []
    
    print("🔍 Database Service import 테스트 시작 (PostgreSQL 전용)...")
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module} - 정상")
        except ImportError as e:
            print(f"❌ {module} - 실패: {e}")
            failed_imports.append(module)
        except Exception as e:
            print(f"⚠️ {module} - 경고: {e}")
    
    if failed_imports:
        print(f"\n❌ 실패한 import: {failed_imports}")
        return False
    else:
        print("\n✅ 모든 PostgreSQL import 성공!")
        return True

def test_database_service_code():
    """Database Service 관련 코드가 정상적으로 동작하는지 테스트"""
    
    try:
        # PostgreSQL 전용 MultiDatabaseManager 테스트
        from src.db.multi_database_manager import MultiDatabaseManager
        print("✅ MultiDatabaseManager import 성공")
        
        # PostgreSQL 연결 테스트 (환경변수 확인)
        import os
        postgres_configured = all([
            os.getenv('POSTGRES_HOST'),
            os.getenv('POSTGRES_DB'),
            os.getenv('POSTGRES_USER'),
            os.getenv('POSTGRES_PASSWORD')
        ])
        
        if postgres_configured:
            print("✅ PostgreSQL 환경변수 설정 확인")
        else:
            print("⚠️ PostgreSQL 환경변수 설정 부족")
            print("다음 환경변수를 설정하세요:")
            print("POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD")
        
        return True
        
    except Exception as e:
        print(f"❌ Database Service 코드 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    print("🗄️ Database Service 호환성 검증 (PostgreSQL 전용)")
    print("=" * 60)
    
    import_success = test_imports()
    code_success = test_database_service_code()
    
    if import_success and code_success:
        print("\n🎉 Database Service 호환성 검증 완료!")
        sys.exit(0)
    else:
        print("\n💥 Database Service 호환성 검증 실패!")
        sys.exit(1) 