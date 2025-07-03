#!/usr/bin/env python3
"""
API 계약 문제 분석 스크립트
데이터 구조, 타입 불일치, null vs "" 문제 등을 탐지
"""

import os
import re
import json
import ast
from pathlib import Path
from typing import Dict, List, Set, Any

class APIContractAnalyzer:
    def __init__(self):
        self.api_endpoints = []
        self.type_issues = []
        self.null_empty_issues = []
        self.schema_issues = []
        self.response_patterns = {}
        
    def analyze_project(self, project_root: str = "src"):
        print("🔍 API 계약 문제 분석 시작...")
        self._find_api_endpoints(project_root)
        self._analyze_type_consistency(project_root)
        self._analyze_null_empty_issues(project_root)
        self._analyze_response_schemas(project_root)
        self._generate_report()
    
    def _find_api_endpoints(self, project_root: str):
        """API 엔드포인트 찾기"""
        print("📋 API 엔드포인트 탐지 중...")
        
        for py_file in Path(project_root).rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # FastAPI 라우터 패턴 찾기
                router_patterns = [
                    r'@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
                    r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
                    r'@.*\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
                ]
                
                for pattern in router_patterns:
                    matches = re.findall(pattern, content)
                    for method, path in matches:
                        self.api_endpoints.append({
                            'file': str(py_file),
                            'method': method.upper(),
                            'path': path,
                            'full_path': f"{method.upper()} {path}"
                        })
                        
            except Exception as e:
                print(f"⚠️ 파일 분석 실패: {py_file}, 오류: {e}")
    
    def _analyze_type_consistency(self, project_root: str):
        """타입 일관성 분석"""
        print("🔍 타입 일관성 분석 중...")
        
        type_patterns = [
            (r'Optional\[str\]', 'str | None'),
            (r'Optional\[int\]', 'int | None'),
            (r'Optional\[List\]', 'List | None'),
            (r'Optional\[Dict\]', 'Dict | None'),
            (r'Union\[str,\s*None\]', 'str | None'),
            (r'Union\[int,\s*None\]', 'int | None'),
        ]
        
        for py_file in Path(project_root).rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for old_pattern, new_pattern in type_patterns:
                    if re.search(old_pattern, content):
                        self.type_issues.append({
                            'file': str(py_file),
                            'issue': f"구식 타입 사용: {old_pattern} → {new_pattern}",
                            'severity': 'medium'
                        })
                        
            except Exception as e:
                print(f"⚠️ 타입 분석 실패: {py_file}, 오류: {e}")
    
    def _analyze_null_empty_issues(self, project_root: str):
        """null vs "" 문제 분석"""
        print("🔍 null vs empty 문제 분석 중...")
        
        null_empty_patterns = [
            (r'return\s+""', '빈 문자열 반환'),
            (r'return\s+None', 'None 반환'),
            (r'=\s*""', '빈 문자열 할당'),
            (r'=\s*None', 'None 할당'),
            (r'if\s+.*\s*==\s*""', '빈 문자열 비교'),
            (r'if\s+.*\s*is\s+None', 'None 비교'),
        ]
        
        for py_file in Path(project_root).rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern, description in null_empty_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        self.null_empty_issues.append({
                            'file': str(py_file),
                            'pattern': pattern,
                            'description': description,
                            'count': len(matches)
                        })
                        
            except Exception as e:
                print(f"⚠️ null/empty 분석 실패: {py_file}, 오류: {e}")
    
    def _analyze_response_schemas(self, project_root: str):
        """응답 스키마 분석"""
        print("🔍 응답 스키마 분석 중...")
        
        response_patterns = [
            r'return\s+\{([^}]+)\}',
            r'JSONResponse\s*\(\s*\{([^}]+)\}',
            r'SuccessResponse\s*\(\s*([^)]+)\s*\)',
            r'ErrorResponse\s*\(\s*([^)]+)\s*\)',
        ]
        
        for py_file in Path(project_root).rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern in response_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        # 응답 구조 분석
                        if 'status' in match and 'message' in match:
                            self.response_patterns[str(py_file)] = {
                                'type': 'standard_response',
                                'fields': self._extract_fields(match)
                            }
                        elif 'data' in match:
                            self.response_patterns[str(py_file)] = {
                                'type': 'data_response',
                                'fields': self._extract_fields(match)
                            }
                        
            except Exception as e:
                print(f"⚠️ 스키마 분석 실패: {py_file}, 오류: {e}")
    
    def _extract_fields(self, content: str) -> List[str]:
        """응답에서 필드 추출"""
        fields = []
        # 간단한 필드 추출 (키: 값 패턴)
        field_pattern = r'(\w+)\s*:'
        matches = re.findall(field_pattern, content)
        return list(set(matches))
    
    def _generate_report(self):
        """분석 리포트 생성"""
        print("\n" + "="*60)
        print("📊 API 계약 문제 분석 리포트")
        print("="*60)
        
        # 1. API 엔드포인트 요약
        print(f"\n🔗 API 엔드포인트: {len(self.api_endpoints)}개")
        for endpoint in self.api_endpoints[:10]:  # 상위 10개만 표시
            print(f"   - {endpoint['full_path']} ({endpoint['file']})")
        
        # 2. 타입 일관성 문제
        print(f"\n🔧 타입 일관성 문제: {len(self.type_issues)}개")
        for issue in self.type_issues[:5]:
            print(f"   - {issue['file']}: {issue['issue']}")
        
        # 3. null vs empty 문제
        print(f"\n⚠️ null vs empty 문제: {len(self.null_empty_issues)}개")
        for issue in self.null_empty_issues[:5]:
            print(f"   - {issue['file']}: {issue['description']} ({issue['count']}회)")
        
        # 4. 응답 스키마 패턴
        print(f"\n📋 응답 스키마 패턴: {len(self.response_patterns)}개")
        for file_path, pattern in list(self.response_patterns.items())[:5]:
            print(f"   - {file_path}: {pattern['type']} ({', '.join(pattern['fields'])})")
        
        # 5. 권장사항
        print(f"\n💡 권장사항:")
        print(f"   1. OpenAPI/Swagger 명세 작성 필요")
        print(f"   2. JSON Schema 정의 필요")
        print(f"   3. null vs empty 값 정책 통일 필요")
        print(f"   4. 타입 힌트 현대화 필요 (Python 3.10+ 문법)")
        
        # 6. 상세 리포트 저장
        self._save_detailed_report()
    
    def _save_detailed_report(self):
        """상세 리포트 저장"""
        report = {
            'summary': {
                'total_endpoints': len(self.api_endpoints),
                'type_issues': len(self.type_issues),
                'null_empty_issues': len(self.null_empty_issues),
                'response_patterns': len(self.response_patterns)
            },
            'endpoints': self.api_endpoints,
            'type_issues': self.type_issues,
            'null_empty_issues': self.null_empty_issues,
            'response_patterns': self.response_patterns
        }
        
        with open('api_contract_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 상세 리포트 저장: api_contract_report.json")

def main():
    analyzer = APIContractAnalyzer()
    analyzer.analyze_project()
    print("\n🎉 API 계약 분석 완료!")

if __name__ == "__main__":
    main() 