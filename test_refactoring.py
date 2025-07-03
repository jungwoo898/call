#!/usr/bin/env python3
"""
리팩터링 결과 검증 테스트
중복 제거, 타입 통합, 네임스페이스 표준화 검증
"""

import sys
import os
import asyncio
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_common_endpoints_import():
    """공통 엔드포인트 모듈 import 테스트"""
    print("🔍 공통 엔드포인트 모듈 import 테스트...")
    
    try:
        from src.utils.common_endpoints import get_common_endpoints, CommonEndpoints
        print("✅ 공통 엔드포인트 모듈 import 성공")
        
        # 인스턴스 생성 테스트
        endpoints = get_common_endpoints("test-service", "1.0.0")
        assert isinstance(endpoints, CommonEndpoints)
        print("✅ CommonEndpoints 인스턴스 생성 성공")
        
        return True
    except Exception as e:
        print(f"❌ 공통 엔드포인트 모듈 import 실패: {e}")
        return False

def test_common_types_import():
    """공통 타입 모듈 import 테스트"""
    print("🔍 공통 타입 모듈 import 테스트...")
    
    try:
        from src.utils.common_types import (
            HealthResponse, MetricsResponse, SuccessResponse, ErrorResponse,
            AudioProperties, SpeakerSegment, Utterance, AnalysisResult,
            DatabaseConfig, ServiceConfig, ProcessingStatus
        )
        print("✅ 공통 타입 모듈 import 성공")
        
        # 타입 인스턴스 생성 테스트
        health_response = HealthResponse(
            status="healthy",
            service="test",
            version="1.0.0",
            timestamp="2024-01-01T00:00:00",
            uptime=3600.0,
            system={"cpu": 50.0}
        )
        assert isinstance(health_response, HealthResponse)
        print("✅ HealthResponse 인스턴스 생성 성공")
        
        return True
    except Exception as e:
        print(f"❌ 공통 타입 모듈 import 실패: {e}")
        return False

async def test_health_check_endpoint():
    """헬스체크 엔드포인트 테스트"""
    print("🔍 헬스체크 엔드포인트 테스트...")
    
    try:
        from src.utils.common_endpoints import get_common_endpoints
        
        endpoints = get_common_endpoints("test-service", "1.0.0")
        
        # 기본 헬스체크 테스트
        result = await endpoints.health_check()
        assert "status" in result
        assert "service" in result
        assert "version" in result
        print("✅ 기본 헬스체크 성공")
        
        # 추가 체크 항목 테스트
        additional_checks = {
            "custom_check": "passed",
            "database": "connected"
        }
        result_with_checks = await endpoints.health_check(additional_checks)
        assert "custom_check" in result_with_checks
        assert "database" in result_with_checks
        print("✅ 추가 체크 항목 헬스체크 성공")
        
        return True
    except Exception as e:
        print(f"❌ 헬스체크 엔드포인트 테스트 실패: {e}")
        return False

async def test_metrics_endpoint():
    """메트릭 엔드포인트 테스트"""
    print("🔍 메트릭 엔드포인트 테스트...")
    
    try:
        from src.utils.common_endpoints import get_common_endpoints
        
        endpoints = get_common_endpoints("test-service", "1.0.0")
        
        # 기본 메트릭 테스트
        result = await endpoints.get_metrics()
        assert "timestamp" in result
        assert "service" in result
        assert "system" in result
        print("✅ 기본 메트릭 성공")
        
        # 추가 메트릭 테스트
        additional_metrics = {
            "custom_metric": 100,
            "performance": "good"
        }
        result_with_metrics = await endpoints.get_metrics(additional_metrics)
        assert "custom_metric" in result_with_metrics
        assert "performance" in result_with_metrics
        print("✅ 추가 메트릭 성공")
        
        return True
    except Exception as e:
        print(f"❌ 메트릭 엔드포인트 테스트 실패: {e}")
        return False

def test_duplicate_removal():
    """중복 제거 검증"""
    print("🔍 중복 제거 검증...")
    
    # 중복 함수 검색
    duplicate_functions = []
    
    # health_check 함수 검색
    health_check_files = []
    for py_file in Path("src").rglob("*.py"):
        if py_file.name != "common_endpoints.py":  # 공통 모듈 제외
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if "def health_check" in content:
                        health_check_files.append(str(py_file))
            except:
                continue
    
    # get_metrics 함수 검색
    metrics_files = []
    for py_file in Path("src").rglob("*.py"):
        if py_file.name != "common_endpoints.py":  # 공통 모듈 제외
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if "def get_metrics" in content:
                        metrics_files.append(str(py_file))
            except:
                continue
    
    print(f"📊 health_check 함수 발견: {len(health_check_files)}개")
    print(f"📊 get_metrics 함수 발견: {len(metrics_files)}개")
    
    # 중복이 적절히 제거되었는지 확인
    if len(health_check_files) <= 2:  # 공통 모듈 + main.py 정도만 허용
        print("✅ health_check 중복 제거 성공")
        health_check_ok = True
    else:
        print("⚠️ health_check 중복이 여전히 존재")
        health_check_ok = False
    
    if len(metrics_files) <= 2:  # 공통 모듈 + main.py 정도만 허용
        print("✅ get_metrics 중복 제거 성공")
        metrics_ok = True
    else:
        print("⚠️ get_metrics 중복이 여전히 존재")
        metrics_ok = False
    
    return health_check_ok and metrics_ok

def test_namespace_consistency():
    """네임스페이스 일관성 검증"""
    print("🔍 네임스페이스 일관성 검증...")
    
    # 모듈별 함수명 패턴 검사
    namespace_patterns = {
        "audio": [],
        "text": [],
        "db": [],
        "utils": []
    }
    
    for py_file in Path("src").rglob("*.py"):
        module_type = py_file.parts[1] if len(py_file.parts) > 1 else "unknown"
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 함수 정의 찾기
                import re
                function_matches = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content)
                
                for func_name in function_matches:
                    if not func_name.startswith('_') and not func_name.startswith('test_'):
                        if module_type in namespace_patterns:
                            namespace_patterns[module_type].append(func_name)
        except:
            continue
    
    # 네임스페이스 일관성 검사
    consistency_score = 0
    total_functions = 0
    
    for module_type, functions in namespace_patterns.items():
        if functions:
            total_functions += len(functions)
            consistent_functions = 0
            
            for func_name in functions:
                # 모듈별 접두사 규칙 검사
                if module_type == "audio" and func_name.startswith("audio_"):
                    consistent_functions += 1
                elif module_type == "text" and func_name.startswith("text_"):
                    consistent_functions += 1
                elif module_type == "db" and func_name.startswith("db_"):
                    consistent_functions += 1
                elif module_type == "utils" and func_name.startswith("util_"):
                    consistent_functions += 1
                else:
                    # 공통 함수들은 제외
                    if func_name in ["health_check", "get_metrics", "main", "__init__"]:
                        consistent_functions += 1
            
            if total_functions > 0:
                consistency_score += consistent_functions / len(functions)
    
    consistency_percentage = (consistency_score / len(namespace_patterns)) * 100 if namespace_patterns else 0
    
    print(f"📊 네임스페이스 일관성: {consistency_percentage:.1f}%")
    
    if consistency_percentage >= 70:
        print("✅ 네임스페이스 일관성 양호")
        return True
    else:
        print("⚠️ 네임스페이스 일관성 개선 필요")
        return False

async def main():
    """메인 테스트 실행"""
    print("🚀 리팩터링 결과 검증 시작...")
    print("=" * 60)
    
    test_results = []
    
    # 1. 공통 모듈 import 테스트
    test_results.append(test_common_endpoints_import())
    test_results.append(test_common_types_import())
    
    # 2. 엔드포인트 기능 테스트
    test_results.append(await test_health_check_endpoint())
    test_results.append(await test_metrics_endpoint())
    
    # 3. 중복 제거 검증
    test_results.append(test_duplicate_removal())
    
    # 4. 네임스페이스 일관성 검증
    test_results.append(test_namespace_consistency())
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 리팩터링 검증 결과")
    print("=" * 60)
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print(f"✅ 통과: {passed_tests}/{total_tests}")
    print(f"📈 성공률: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("🎉 모든 테스트 통과! 리팩터링이 성공적으로 완료되었습니다.")
        return True
    else:
        print("⚠️ 일부 테스트 실패. 추가 리팩터링이 필요합니다.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 