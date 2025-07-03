#!/usr/bin/env python3
"""
Callytics API 일관성 검사 도구
현재 코드베이스에서 타입 불일치 및 스키마 문제를 감지
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Set
from dataclasses import dataclass

@dataclass
class Issue:
    """발견된 문제"""
    file_path: str
    line_number: int
    issue_type: str
    message: str
    severity: str = "warning"

class APIConsistencyChecker:
    """API 일관성 검사기"""
    
    def __init__(self):
        self.issues: List[Issue] = []
        self.response_patterns: Dict[str, List[str]] = {}
        self.pydantic_models: Set[str] = set()
        
    def scan_pydantic_models(self):
        """Pydantic 모델 스캔"""
        schema_file = Path("src/utils/api_schemas.py")
        if schema_file.exists():
            content = schema_file.read_text(encoding='utf-8')
            
            # BaseModel 클래스 찾기
            model_pattern = r'class\s+(\w+)\s*\([^)]*BaseModel[^)]*\):'
            models = re.findall(model_pattern, content)
            self.pydantic_models.update(models)
            
            print(f"🔍 발견된 Pydantic 모델: {len(self.pydantic_models)}개")
            for model in sorted(self.pydantic_models):
                print(f"  - {model}")
    
    def check_service_files(self):
        """서비스 파일들의 API 일관성 검사"""
        service_dirs = [
            "src/audio",
            "src/text", 
            "src/gateway",
            "src/db"
        ]
        
        for service_dir in service_dirs:
            main_file = Path(service_dir) / "main.py"
            if main_file.exists():
                self.check_main_file(main_file)
    
    def check_main_file(self, file_path: Path):
        """main.py 파일 개별 검사"""
        print(f"\n📁 검사 중: {file_path}")
        
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                # 1. Dict[str, Any] 사용 검사
                if "Dict[str, Any]" in line and "@app." in lines[max(0, i-5):i]:
                    self.issues.append(Issue(
                        file_path=str(file_path),
                        line_number=i,
                        issue_type="TYPE_SAFETY",
                        message="Dict[str, Any] 사용 - Pydantic 모델 사용 권장",
                        severity="warning"
                    ))
                
                # 2. JSONResponse 직접 사용 검사
                if "JSONResponse(" in line:
                    self.issues.append(Issue(
                        file_path=str(file_path),
                        line_number=i,
                        issue_type="RESPONSE_FORMAT",
                        message="JSONResponse 직접 사용 - Pydantic 응답 모델 권장",
                        severity="warning"
                    ))
                
                # 3. response_model 누락 검사
                if re.match(r'\s*@app\.(get|post|put|delete)', line):
                    if "response_model" not in line:
                        self.issues.append(Issue(
                            file_path=str(file_path),
                            line_number=i,
                            issue_type="MISSING_SCHEMA",
                            message="response_model 매개변수 누락",
                            severity="error"
                        ))
                
                # 4. 응답 패턴 수집
                if "return" in line and "{" in line:
                    self.collect_response_pattern(str(file_path), i, line)
                    
        except Exception as e:
            print(f"❌ {file_path} 읽기 실패: {e}")
    
    def collect_response_pattern(self, file_path: str, line_num: int, line: str):
        """응답 패턴 수집"""
        # 응답에서 키 추출
        key_pattern = r'"(\w+)":\s*[^,}]+'
        keys = re.findall(key_pattern, line)
        
        if keys:
            service_name = file_path.split('/')[-2] if '/' in file_path else file_path.split('\\')[-2]
            if service_name not in self.response_patterns:
                self.response_patterns[service_name] = []
            self.response_patterns[service_name].extend(keys)
    
    def check_response_consistency(self):
        """응답 형식 일관성 검사"""
        print(f"\n🔍 응답 형식 일관성 검사")
        
        # 공통 키 분석
        all_keys = {}
        for service, keys in self.response_patterns.items():
            for key in keys:
                if key not in all_keys:
                    all_keys[key] = []
                all_keys[key].append(service)
        
        # 일관성 없는 키 찾기
        inconsistent_keys = []
        for key, services in all_keys.items():
            if len(services) < len(self.response_patterns) and len(services) > 1:
                inconsistent_keys.append((key, services))
        
        print(f"📊 응답 키 분석:")
        for service, keys in self.response_patterns.items():
            print(f"  {service}: {sorted(set(keys))}")
        
        if inconsistent_keys:
            print(f"\n⚠️ 일관성 없는 응답 키:")
            for key, services in inconsistent_keys:
                print(f"  '{key}': {services}에서만 사용")
    
    def check_null_empty_patterns(self):
        """null/empty 패턴 검사"""
        print(f"\n🔍 null/empty 패턴 검사")
        
        patterns_to_check = [
            (r':\s*""', "빈 문자열 사용"),
            (r':\s*None', "None 사용"),
            (r':\s*\[\]', "빈 리스트 사용"),
            (r':\s*null', "null 사용")
        ]
        
        for service_dir in ["src/audio", "src/text", "src/gateway", "src/db"]:
            main_file = Path(service_dir) / "main.py"
            if main_file.exists():
                content = main_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    for pattern, description in patterns_to_check:
                        if re.search(pattern, line):
                            print(f"  {main_file}:{i} - {description}")
    
    def generate_report(self):
        """검사 보고서 생성"""
        print(f"\n📋 API 일관성 검사 보고서")
        print(f"=" * 50)
        
        # 이슈 요약
        severity_counts = {}
        type_counts = {}
        
        for issue in self.issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
            type_counts[issue.issue_type] = type_counts.get(issue.issue_type, 0) + 1
        
        print(f"📊 전체 이슈: {len(self.issues)}개")
        print(f"심각도별:")
        for severity, count in severity_counts.items():
            emoji = "🔴" if severity == "error" else "🟡" if severity == "warning" else "🔵"
            print(f"  {emoji} {severity}: {count}개")
        
        print(f"\n유형별:")
        for issue_type, count in type_counts.items():
            print(f"  • {issue_type}: {count}개")
        
        # 상세 이슈 목록
        if self.issues:
            print(f"\n📝 상세 이슈 목록:")
            for issue in sorted(self.issues, key=lambda x: (x.severity, x.file_path)):
                severity_emoji = "🔴" if issue.severity == "error" else "🟡"
                print(f"  {severity_emoji} {issue.file_path}:{issue.line_number}")
                print(f"     {issue.issue_type}: {issue.message}")
        
        # 권장사항
        print(f"\n✅ 권장사항:")
        print(f"  1. Dict[str, Any] → Pydantic 모델 사용")
        print(f"  2. JSONResponse → response_model 매개변수 사용")
        print(f"  3. 모든 엔드포인트에 response_model 추가")
        print(f"  4. 응답 형식 표준화 (status, message, timestamp)")
        print(f"  5. null vs empty 일관성 유지")
        
        # JSON 보고서 저장
        report = {
            "timestamp": "2024-07-02T15:30:00Z",
            "summary": {
                "total_issues": len(self.issues),
                "by_severity": severity_counts,
                "by_type": type_counts
            },
            "pydantic_models": list(self.pydantic_models),
            "response_patterns": self.response_patterns,
            "issues": [
                {
                    "file": issue.file_path,
                    "line": issue.line_number,
                    "type": issue.issue_type,
                    "message": issue.message,
                    "severity": issue.severity
                }
                for issue in self.issues
            ]
        }
        
        with open("api_consistency_report.json", 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 상세 보고서 저장: api_consistency_report.json")

def main():
    """메인 실행 함수"""
    print("🚀 Callytics API 일관성 검사를 시작합니다...")
    
    checker = APIConsistencyChecker()
    
    # 1. Pydantic 모델 스캔
    checker.scan_pydantic_models()
    
    # 2. 서비스 파일 검사
    checker.check_service_files()
    
    # 3. 응답 일관성 검사
    checker.check_response_consistency()
    
    # 4. null/empty 패턴 검사
    checker.check_null_empty_patterns()
    
    # 5. 보고서 생성
    checker.generate_report()

if __name__ == "__main__":
    main() 