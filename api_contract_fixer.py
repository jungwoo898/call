#!/usr/bin/env python3
"""
API 계약 문제 자동 수정 스크립트
null vs empty, 타입 불일치, 응답 구조 등을 표준화
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any

class APIContractFixer:
    def __init__(self):
        self.fixes_applied = []
        self.backup_dir = Path("backups/api_contract_fixes")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def fix_all_issues(self):
        """모든 API 계약 문제 수정"""
        print("🔧 API 계약 문제 자동 수정 시작...")
        
        # 1. 타입 힌트 현대화
        self._fix_type_hints()
        
        # 2. null vs empty 값 정책 통일
        self._fix_null_empty_policy()
        
        # 3. 응답 구조 표준화
        self._standardize_responses()
        
        # 4. API 스키마 검증 추가
        self._add_schema_validation()
        
        # 5. 수정 리포트 생성
        self._generate_fix_report()
        
        print("✅ API 계약 문제 수정 완료!")
    
    def _fix_type_hints(self):
        """타입 힌트 현대화 (Python 3.10+ 문법)"""
        print("🔧 타입 힌트 현대화 중...")
        
        type_replacements = [
            (r'Optional\[str\]', 'str | None'),
            (r'Optional\[int\]', 'int | None'),
            (r'Optional\[float\]', 'float | None'),
            (r'Optional\[bool\]', 'bool | None'),
            (r'Optional\[List\]', 'List | None'),
            (r'Optional\[Dict\]', 'Dict | None'),
            (r'Union\[str,\s*None\]', 'str | None'),
            (r'Union\[int,\s*None\]', 'int | None'),
            (r'Union\[float,\s*None\]', 'float | None'),
            (r'Union\[bool,\s*None\]', 'bool | None'),
            (r'Union\[List,\s*None\]', 'List | None'),
            (r'Union\[Dict,\s*None\]', 'Dict | None'),
        ]
        
        for py_file in Path("src").rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                for old_pattern, new_pattern in type_replacements:
                    content = re.sub(old_pattern, new_pattern, content)
                
                if content != original_content:
                    # 백업 생성
                    backup_file = self.backup_dir / f"{py_file.name}.backup"
                    with open(backup_file, 'w', encoding='utf-8') as f:
                        f.write(original_content)
                    
                    # 수정된 내용 저장
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    self.fixes_applied.append({
                        'file': str(py_file),
                        'type': 'type_hint_modernization',
                        'description': f'타입 힌트 현대화: {old_pattern} → {new_pattern}'
                    })
                    
            except Exception as e:
                print(f"⚠️ 타입 힌트 수정 실패: {py_file}, 오류: {e}")
    
    def _fix_null_empty_policy(self):
        """null vs empty 값 정책 통일"""
        print("🔧 null vs empty 정책 통일 중...")
        
        # 정책: 빈 문자열 대신 None 사용 (일관성)
        null_empty_fixes = [
            # 반환값 정책
            (r'return\s+""', 'return None'),
            (r'return\s+\{\s*"status":\s*"success",\s*"message":\s*""\s*\}', 
             'return {"status": "success", "message": None}'),
            
            # 할당 정책
            (r'=\s*""', '= None'),
            (r'=\s*\{\s*"status":\s*"success",\s*"message":\s*""\s*\}', 
             '= {"status": "success", "message": None}'),
            
            # 비교 정책
            (r'if\s+([^=]+)\s*==\s*""', r'if \1 is None'),
            (r'if\s+([^=]+)\s*!=\s*""', r'if \1 is not None'),
        ]
        
        for py_file in Path("src").rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                for pattern, replacement in null_empty_fixes:
                    content = re.sub(pattern, replacement, content)
                
                if content != original_content:
                    # 백업 생성
                    backup_file = self.backup_dir / f"{py_file.name}.backup"
                    with open(backup_file, 'w', encoding='utf-8') as f:
                        f.write(original_content)
                    
                    # 수정된 내용 저장
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    self.fixes_applied.append({
                        'file': str(py_file),
                        'type': 'null_empty_policy',
                        'description': 'null vs empty 정책 통일'
                    })
                    
            except Exception as e:
                print(f"⚠️ null/empty 정책 수정 실패: {py_file}, 오류: {e}")
    
    def _standardize_responses(self):
        """응답 구조 표준화"""
        print("🔧 응답 구조 표준화 중...")
        
        # 표준 응답 구조 정의
        standard_response = '''{
    "status": "success",
    "message": None,
    "data": result,
    "timestamp": datetime.now().isoformat(),
    "processing_time": processing_time
}'''
        
        error_response = '''{
    "status": "error",
    "message": str(error),
    "error_code": error_code,
    "details": error_details,
    "timestamp": datetime.now().isoformat()
}'''
        
        # 응답 패턴 찾기 및 수정
        response_patterns = [
            (r'return\s+\{\s*"status":\s*"success"[^}]*\}', standard_response),
            (r'return\s+\{\s*"status":\s*"error"[^}]*\}', error_response),
        ]
        
        for py_file in Path("src").rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                for pattern, replacement in response_patterns:
                    content = re.sub(pattern, replacement, content)
                
                if content != original_content:
                    # 백업 생성
                    backup_file = self.backup_dir / f"{py_file.name}.backup"
                    with open(backup_file, 'w', encoding='utf-8') as f:
                        f.write(original_content)
                    
                    # 수정된 내용 저장
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    self.fixes_applied.append({
                        'file': str(py_file),
                        'type': 'response_standardization',
                        'description': '응답 구조 표준화'
                    })
                    
            except Exception as e:
                print(f"⚠️ 응답 구조 수정 실패: {py_file}, 오류: {e}")
    
    def _add_schema_validation(self):
        """API 스키마 검증 추가"""
        print("🔧 API 스키마 검증 추가 중...")
        
        # Pydantic 모델 생성
        pydantic_models = '''
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class AudioInput(BaseModel):
    audio_data: str = Field(..., description="Base64 인코딩된 오디오 데이터")
    sample_rate: int = Field(default=16000, description="샘플링 레이트 (Hz)")
    format: str = Field(default="wav", description="오디오 포맷")

class TextInput(BaseModel):
    text: str = Field(..., description="분석할 텍스트")
    language: str = Field(default="ko", description="언어 코드")
    options: Optional[Dict[str, Any]] = Field(default=None, description="추가 옵션")

class AnalysisResult(BaseModel):
    status: str = Field(..., description="처리 상태")
    message: Optional[str] = Field(default=None, description="메시지")
    data: Optional[Dict[str, Any]] = Field(default=None, description="결과 데이터")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    processing_time: Optional[float] = Field(default=None, description="처리 시간")
'''
        
        # 공통 모듈에 스키마 추가
        schema_file = Path("src/utils/api_schemas.py")
        if schema_file.exists():
            with open(schema_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if "class AudioInput" not in content:
                # 백업 생성
                backup_file = self.backup_dir / f"{schema_file.name}.backup"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # 스키마 추가
                with open(schema_file, 'a', encoding='utf-8') as f:
                    f.write(pydantic_models)
                
                self.fixes_applied.append({
                    'file': str(schema_file),
                    'type': 'schema_validation',
                    'description': 'Pydantic 스키마 모델 추가'
                })
        else:
            # 새 파일 생성
            with open(schema_file, 'w', encoding='utf-8') as f:
                f.write(pydantic_models)
            
            self.fixes_applied.append({
                'file': str(schema_file),
                'type': 'schema_validation',
                'description': '새 Pydantic 스키마 파일 생성'
            })
    
    def _generate_fix_report(self):
        """수정 리포트 생성"""
        print("\n" + "="*60)
        print("📊 API 계약 수정 리포트")
        print("="*60)
        
        print(f"\n🔧 총 수정 사항: {len(self.fixes_applied)}개")
        
        # 타입별 수정 사항 요약
        fix_types = {}
        for fix in self.fixes_applied:
            fix_type = fix['type']
            if fix_type not in fix_types:
                fix_types[fix_type] = 0
            fix_types[fix_type] += 1
        
        for fix_type, count in fix_types.items():
            print(f"   - {fix_type}: {count}개")
        
        # 상세 수정 사항
        print(f"\n📋 상세 수정 사항:")
        for fix in self.fixes_applied[:10]:  # 상위 10개만 표시
            print(f"   - {fix['file']}: {fix['description']}")
        
        # 백업 정보
        print(f"\n💾 백업 파일 위치: {self.backup_dir}")
        
        # 권장사항
        print(f"\n💡 다음 단계:")
        print(f"   1. 수정된 코드 테스트 실행")
        print(f"   2. API 엔드포인트 동작 확인")
        print(f"   3. OpenAPI 명세 문서 확인")
        print(f"   4. 클라이언트 코드 업데이트")
        
        # 상세 리포트 저장
        report = {
            'summary': {
                'total_fixes': len(self.fixes_applied),
                'fix_types': fix_types
            },
            'fixes': self.fixes_applied,
            'backup_location': str(self.backup_dir)
        }
        
        with open('api_contract_fix_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 상세 리포트 저장: api_contract_fix_report.json")

def main():
    fixer = APIContractFixer()
    fixer.fix_all_issues()
    print("\n🎉 API 계약 수정 완료!")

if __name__ == "__main__":
    main() 