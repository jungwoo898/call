#!/usr/bin/env python3
"""
현재 상태 안전성 확인 스크립트
변경된 코드가 정상 작동하는지 간단히 테스트
"""

import os
import sys
import importlib
from pathlib import Path

def test_import_safety():
    """import 안전성 테스트"""
    print("🔍 Import 안전성 테스트...")
    
    # 주요 모듈들 import 테스트
    test_modules = [
        "src.utils.common_endpoints",
        "src.utils.common_types", 
        "src.utils.common_functions",
        "src.upload.agent_audio_upload"
    ]
    
    failed_imports = []
    for module_name in test_modules:
        try:
            importlib.import_module(module_name)
            print(f"✅ {module_name} import 성공")
        except Exception as e:
            print(f"❌ {module_name} import 실패: {e}")
            failed_imports.append(module_name)
    
    return len(failed_imports) == 0

def test_syntax_safety():
    """구문 오류 테스트"""
    print("🔍 구문 오류 테스트...")
    
    syntax_errors = []
    for py_file in Path("src").rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            compile(content, str(py_file), 'exec')
        except SyntaxError as e:
            print(f"❌ 구문 오류: {py_file}, 라인 {e.lineno}: {e}")
            syntax_errors.append(str(py_file))
    
    if not syntax_errors:
        print("✅ 모든 파일 구문 정상")
    
    return len(syntax_errors) == 0

def test_changed_functions():
    """변경된 함수들 테스트"""
    print("🔍 변경된 함수들 테스트...")
    
    # upload 모듈의 변경된 함수들 확인
    upload_file = "src/upload/agent_audio_upload.py"
    if os.path.exists(upload_file):
        try:
            with open(upload_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 변경된 함수들이 정의되어 있는지 확인
            changed_functions = [
                "upload_audio_validate_audio_file",
                "upload_audio_generate_unique_filename", 
                "upload_audio_upload_audio_with_agent_info"
            ]
            
            missing_functions = []
            for func_name in changed_functions:
                if f"def {func_name}" not in content:
                    missing_functions.append(func_name)
            
            if not missing_functions:
                print("✅ 변경된 함수들 모두 정상 정의됨")
                return True
            else:
                print(f"❌ 누락된 함수들: {missing_functions}")
                return False
                
        except Exception as e:
            print(f"❌ 파일 읽기 실패: {e}")
            return False
    else:
        print("❌ upload 파일 없음")
        return False

def test_backup_files():
    """백업 파일 확인"""
    print("🔍 백업 파일 확인...")
    
    backup_files = list(Path("src").rglob("*.backup"))
    if backup_files:
        print(f"✅ 백업 파일 {len(backup_files)}개 존재")
        for backup in backup_files[:5]:  # 상위 5개만 표시
            print(f"   - {backup}")
        return True
    else:
        print("❌ 백업 파일 없음")
        return False

def main():
    """메인 안전성 테스트"""
    print("🚀 현재 상태 안전성 확인 시작...")
    print("=" * 50)
    
    test_results = []
    
    # 1. Import 안전성
    test_results.append(test_import_safety())
    
    # 2. 구문 오류 확인
    test_results.append(test_syntax_safety())
    
    # 3. 변경된 함수들 확인
    test_results.append(test_changed_functions())
    
    # 4. 백업 파일 확인
    test_results.append(test_backup_files())
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 안전성 확인 결과")
    print("=" * 50)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"✅ 통과: {passed}/{total}")
    print(f"📈 안전성: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 모든 안전성 테스트 통과! 현재 상태 안전함")
        return True
    else:
        print("⚠️ 일부 안전성 문제 발견. 복구 권장")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 