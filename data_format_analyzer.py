#!/usr/bin/env python3
"""
데이터 포맷 & 프로토콜 연동 점검 스크립트
서비스 간 API 호출 시 데이터 구조 불일치, 응답/요청 형식, 인코딩, 시간대, 언어셋 등 분석
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Any

class DataFormatAnalyzer:
    def __init__(self):
        self.api_endpoints = []
        self.data_format_issues = []
        self.encoding_issues = []
        self.locale_issues = []
        self.response_structure_issues = []
        self.request_structure_issues = []
        
    def analyze_project(self, project_root: str = "src"):
        print("🔍 데이터 포맷 & 프로토콜 연동 점검 시작...")
        
        self._find_api_endpoints(project_root)
        self._analyze_data_formats(project_root)
        self._analyze_encoding_issues(project_root)
        self._analyze_locale_settings(project_root)
        self._analyze_response_structures(project_root)
        self._analyze_request_structures(project_root)
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
    
    def _analyze_data_formats(self, project_root: str):
        """데이터 포맷 분석 (JSON, multipart, text)"""
        print("🔍 데이터 포맷 분석 중...")
        
        format_patterns = [
            # JSON 관련
            (r'JSONResponse', 'JSON 응답'),
            (r'application/json', 'JSON Content-Type'),
            (r'\.json\(\)', 'JSON 메서드'),
            
            # Multipart 관련
            (r'multipart/form-data', 'Multipart 폼'),
            (r'File\(', '파일 업로드'),
            (r'UploadFile', '파일 업로드'),
            
            # Text 관련
            (r'text/plain', '텍스트 응답'),
            (r'PlainTextResponse', '텍스트 응답'),
            
            # 기타
            (r'application/x-www-form-urlencoded', '폼 데이터'),
        ]
        
        for py_file in Path(project_root).rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern, description in format_patterns:
                    if re.search(pattern, content):
                        self.data_format_issues.append({
                            'file': str(py_file),
                            'format_type': description,
                            'pattern': pattern
                        })
                        
            except Exception as e:
                print(f"⚠️ 데이터 포맷 분석 실패: {py_file}, 오류: {e}")
    
    def _analyze_encoding_issues(self, project_root: str):
        """인코딩 문제 분석"""
        print("🔍 인코딩 문제 분석 중...")
        
        encoding_patterns = [
            (r'encoding\s*=\s*["\']utf-8["\']', 'UTF-8 인코딩'),
            (r'encoding\s*=\s*["\']iso-8859-1["\']', 'ISO-8859-1 인코딩'),
            (r'encoding\s*=\s*["\']cp949["\']', 'CP949 인코딩'),
            (r'\.encode\(["\']utf-8["\']\)', 'UTF-8 인코딩'),
            (r'\.decode\(["\']utf-8["\']\)', 'UTF-8 디코딩'),
        ]
        
        for py_file in Path(project_root).rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern, description in encoding_patterns:
                    if re.search(pattern, content):
                        self.encoding_issues.append({
                            'file': str(py_file),
                            'encoding_type': description,
                            'pattern': pattern
                        })
                        
            except Exception as e:
                print(f"⚠️ 인코딩 분석 실패: {py_file}, 오류: {e}")
    
    def _analyze_locale_settings(self, project_root: str):
        """로케일 설정 분석"""
        print("🔍 로케일 설정 분석 중...")
        
        locale_patterns = [
            (r'timezone\s*=\s*["\']Asia/Seoul["\']', '한국 시간대'),
            (r'locale\s*=\s*["\']ko_KR["\']', '한국 로케일'),
            (r'language\s*=\s*["\']ko["\']', '한국어'),
            (r'datetime\.now\(\)', '현재 시간'),
            (r'strftime\s*\(', '시간 포맷'),
        ]
        
        for py_file in Path(project_root).rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern, description in locale_patterns:
                    if re.search(pattern, content):
                        self.locale_issues.append({
                            'file': str(py_file),
                            'locale_type': description,
                            'pattern': pattern
                        })
                        
            except Exception as e:
                print(f"⚠️ 로케일 분석 실패: {py_file}, 오류: {e}")
    
    def _analyze_response_structures(self, project_root: str):
        """응답 구조 분석"""
        print("🔍 응답 구조 분석 중...")
        
        response_patterns = [
            # 필수 필드 누락 가능성
            (r'return\s+\{\s*"status"', 'status 필드 있음'),
            (r'return\s+\{\s*"message"', 'message 필드 있음'),
            (r'return\s+\{\s*"data"', 'data 필드 있음'),
            (r'return\s+\{\s*"result"', 'result 필드 있음'),
            
            # 응답 구조 불일치
            (r'return\s+\{\s*"error"', 'error 필드 (표준과 다름)'),
            (r'return\s+\{\s*"success"', 'success 필드 (표준과 다름)'),
        ]
        
        for py_file in Path(project_root).rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern, description in response_patterns:
                    if re.search(pattern, content):
                        self.response_structure_issues.append({
                            'file': str(py_file),
                            'structure_type': description,
                            'pattern': pattern
                        })
                        
            except Exception as e:
                print(f"⚠️ 응답 구조 분석 실패: {py_file}, 오류: {e}")
    
    def _analyze_request_structures(self, project_root: str):
        """요청 구조 분석"""
        print("🔍 요청 구조 분석 중...")
        
        request_patterns = [
            # 요청 데이터 구조
            (r'request\.json\(\)', 'JSON 요청'),
            (r'request\.form\(\)', '폼 요청'),
            (r'request\.files', '파일 요청'),
            
            # 필수 필드 검증
            (r'\.get\(["\']([^"\']+)["\']\)', '필드 접근'),
            (r'if\s+.*\s+not\s+in', '필드 존재 확인'),
            (r'assert\s+.*\s+in', '필드 검증'),
        ]
        
        for py_file in Path(project_root).rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern, description in request_patterns:
                    if re.search(pattern, content):
                        self.request_structure_issues.append({
                            'file': str(py_file),
                            'request_type': description,
                            'pattern': pattern
                        })
                        
            except Exception as e:
                print(f"⚠️ 요청 구조 분석 실패: {py_file}, 오류: {e}")
    
    def _generate_report(self):
        """분석 리포트 생성"""
        print("\n" + "="*60)
        print("📊 데이터 포맷 & 프로토콜 연동 점검 리포트")
        print("="*60)
        
        # 1. API 엔드포인트 요약
        print(f"\n🔗 API 엔드포인트: {len(self.api_endpoints)}개")
        for endpoint in self.api_endpoints[:10]:
            print(f"   - {endpoint['full_path']} ({endpoint['file']})")
        
        # 2. 데이터 포맷 분석
        print(f"\n📋 데이터 포맷 사용 현황:")
        format_counts = {}
        for issue in self.data_format_issues:
            format_type = issue['format_type']
            if format_type not in format_counts:
                format_counts[format_type] = 0
            format_counts[format_type] += 1
        
        for format_type, count in format_counts.items():
            print(f"   - {format_type}: {count}개")
        
        # 3. 인코딩 분석
        print(f"\n🔤 인코딩 사용 현황:")
        encoding_counts = {}
        for issue in self.encoding_issues:
            encoding_type = issue['encoding_type']
            if encoding_type not in encoding_counts:
                encoding_counts[encoding_type] = 0
            encoding_counts[encoding_type] += 1
        
        for encoding_type, count in encoding_counts.items():
            print(f"   - {encoding_type}: {count}개")
        
        # 4. 로케일 분석
        print(f"\n🌍 로케일 설정 현황:")
        locale_counts = {}
        for issue in self.locale_issues:
            locale_type = issue['locale_type']
            if locale_type not in locale_counts:
                locale_counts[locale_type] = 0
            locale_counts[locale_type] += 1
        
        for locale_type, count in locale_counts.items():
            print(f"   - {locale_type}: {count}개")
        
        # 5. 응답 구조 분석
        print(f"\n📤 응답 구조 현황:")
        response_counts = {}
        for issue in self.response_structure_issues:
            structure_type = issue['structure_type']
            if structure_type not in response_counts:
                response_counts[structure_type] = 0
            response_counts[structure_type] += 1
        
        for structure_type, count in response_counts.items():
            print(f"   - {structure_type}: {count}개")
        
        # 6. 권장사항
        print(f"\n💡 권장사항:")
        print(f"   1. 모든 서비스에서 UTF-8 인코딩 통일")
        print(f"   2. 한국 시간대(Asia/Seoul) 및 로케일(ko_KR) 통일")
        print(f"   3. 응답 구조 표준화: status, message, data 필드 필수")
        print(f"   4. JSON Schema 기반 요청/응답 검증 추가")
        print(f"   5. 중간 변환 계층(Adapter) 구현 고려")
        
        # 7. 상세 리포트 저장
        self._save_detailed_report()
    
    def _save_detailed_report(self):
        """상세 리포트 저장"""
        report = {
            'summary': {
                'total_endpoints': len(self.api_endpoints),
                'data_formats': len(self.data_format_issues),
                'encoding_issues': len(self.encoding_issues),
                'locale_issues': len(self.locale_issues),
                'response_structures': len(self.response_structure_issues),
                'request_structures': len(self.request_structure_issues)
            },
            'endpoints': self.api_endpoints,
            'data_formats': self.data_format_issues,
            'encoding_issues': self.encoding_issues,
            'locale_issues': self.locale_issues,
            'response_structures': self.response_structure_issues,
            'request_structures': self.request_structure_issues
        }
        
        with open('data_format_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 상세 리포트 저장: data_format_report.json")

def main():
    analyzer = DataFormatAnalyzer()
    analyzer.analyze_project()
    print("\n🎉 데이터 포맷 & 프로토콜 연동 점검 완료!")

if __name__ == "__main__":
    main() 