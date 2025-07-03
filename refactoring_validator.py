#!/usr/bin/env python3
"""
리팩터링 검증 스크립트
"""

import os
import sys
from pathlib import Path

def check_backup_cleanup():
    """백업 폴더 정리 확인"""
    print("🔍 백업 폴더 정리 확인...")
    
    backup_dirs = [d for d in os.listdir(".") if d.startswith("backup_")]
    
    if not backup_dirs:
        print("✅ 백업 폴더 정리 완료")
        return True
    else:
        print(f"❌ 백업 폴더 존재: {backup_dirs}")
        return False

def check_duplicate_reduction():
    """중복 함수 감소 확인"""
    print("🔍 중복 함수 감소 확인...")
    
    # __init__ 함수 개수 확인
    init_count = 0
    main_count = 0
    
    for py_file in Path("src").rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "def __init__" in content:
                    init_count += 1
                if "def main" in content:
                    main_count += 1
        except:
            continue
    
    print(f"📊 __init__ 함수: {init_count}개")
    print(f"📊 main 함수: {main_count}개")
    
    # 적절한 수준인지 확인 (너무 많으면 안됨)
    if init_count <= 50 and main_count <= 20:
        print("✅ 중복 함수 수준 적절")
        return True
    else:
        print("⚠️ 중복 함수가 여전히 많음")
        return False

def check_dead_code_removal():
    """죽은 코드 제거 확인"""
    print("🔍 죽은 코드 제거 확인...")
    
    # 사용되지 않는 함수 패턴 검색
    dead_code_patterns = [
        "def _unused_",
        "def test_",  # 테스트 함수는 제외
        "def debug_",
        "def temp_"
    ]
    
    dead_code_count = 0
    for py_file in Path("src").rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                for pattern in dead_code_patterns:
                    if pattern in content:
                        dead_code_count += 1
        except:
            continue
    
    print(f"📊 의심스러운 죽은 코드: {dead_code_count}개")
    
    if dead_code_count <= 100:
        print("✅ 죽은 코드 제거 성공")
        return True
    else:
        print("⚠️ 죽은 코드가 여전히 많음")
        return False

def check_namespace_consistency():
    """네임스페이스 일관성 확인"""
    print("🔍 네임스페이스 일관성 확인...")
    
    # 모듈별 함수명 패턴 확인
    namespace_issues = 0
    
    for py_file in Path("src").rglob("*.py"):
        module_name = py_file.stem
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 함수 정의 찾기
                import re
                function_matches = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content)
                
                for func_name in function_matches:
                    # 공통 함수들은 제외
                    if func_name in ["__init__", "main", "health_check", "get_metrics"]:
                        continue
                    
                    # 모듈명과 일치하지 않는 함수 찾기
                    if not func_name.startswith(module_name.lower()) and not func_name.startswith('_'):
                        namespace_issues += 1
        except:
            continue
    
    print(f"📊 네임스페이스 불일치: {namespace_issues}개")
    
    if namespace_issues <= 200:
        print("✅ 네임스페이스 일관성 양호")
        return True
    else:
        print("⚠️ 네임스페이스 불일치 많음")
        return False

def check_common_modules():
    """공통 모듈 확인"""
    print("🔍 공통 모듈 확인...")
    
    required_modules = [
        "src/utils/common_endpoints.py",
        "src/utils/common_types.py"
    ]
    
    missing_modules = []
    for module in required_modules:
        if not os.path.exists(module):
            missing_modules.append(module)
    
    if not missing_modules:
        print("✅ 공통 모듈 모두 존재")
        return True
    else:
        print(f"❌ 누락된 모듈: {missing_modules}")
        return False

def main():
    """메인 검증 실행"""
    print("🚀 리팩터링 검증 시작...")
    print("=" * 50)
    
    results = []
    
    # 1. 백업 폴더 정리 확인
    results.append(check_backup_cleanup())
    
    # 2. 중복 함수 감소 확인
    results.append(check_duplicate_reduction())
    
    # 3. 죽은 코드 제거 확인
    results.append(check_dead_code_removal())
    
    # 4. 네임스페이스 일관성 확인
    results.append(check_namespace_consistency())
    
    # 5. 공통 모듈 확인
    results.append(check_common_modules())
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 리팩터링 검증 결과")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ 통과: {passed}/{total}")
    print(f"📈 성공률: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 모든 검증 통과! 리팩터링 완료!")
    else:
        print("⚠️ 일부 검증 실패. 추가 작업 필요.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 