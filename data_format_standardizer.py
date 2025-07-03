#!/usr/bin/env python3
"""
데이터 포맷 & 프로토콜 연동 표준화 스크립트
인코딩 통일, 로케일 설정, 응답 구조 표준화, JSON Schema 검증 추가
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any

class DataFormatStandardizer:
    def __init__(self):
        self.fixes_applied = []
        self.backup_dir = Path("backups/data_format_fixes")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def standardize_all(self):
        """모든 데이터 포맷 & 프로토콜 표준화"""
        print("🔧 데이터 포맷 & 프로토콜 표준화 시작...")
        
        # 1. 인코딩 통일 (UTF-8)
        self._standardize_encoding()
        
        # 2. 로케일 설정 통일
        self._standardize_locale()
        
        # 3. 응답 구조 표준화
        self._standardize_response_structures()
        
        # 4. JSON Schema 검증 추가
        self._add_schema_validation()
        
        # 5. 중간 변환 계층(Adapter) 생성
        self._create_adapter_layer()
        
        # 6. 수정 리포트 생성
        self._generate_fix_report()
        
        print("✅ 데이터 포맷 & 프로토콜 표준화 완료!")
    
    def _standardize_encoding(self):
        """인코딩 통일 (UTF-8)"""
        print("🔧 인코딩 통일 중...")
        
        encoding_fixes = [
            # 파일 읽기/쓰기 인코딩 통일
            (r'open\([^,]+,\s*["\']w["\']\)', 'open(file_path, "w", encoding="utf-8")'),
            (r'open\([^,]+,\s*["\']r["\']\)', 'open(file_path, "r", encoding="utf-8")'),
            
            # 문자열 인코딩/디코딩 통일
            (r'\.encode\(\)', '.encode("utf-8")'),
            (r'\.decode\(\)', '.decode("utf-8")'),
            
            # Content-Type 헤더 통일
            (r'{"Content-Type":\s*["\']application/json["\']}', 
             '{"Content-Type": "application/json; charset=utf-8"}'),
        ]
        
        for py_file in Path("src").rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                for pattern, replacement in encoding_fixes:
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
                        'type': 'encoding_standardization',
                        'description': 'UTF-8 인코딩 통일'
                    })
                    
            except Exception as e:
                print(f"⚠️ 인코딩 수정 실패: {py_file}, 오류: {e}")
    
    def _standardize_locale(self):
        """로케일 설정 통일"""
        print("🔧 로케일 설정 통일 중...")
        
        # 공통 로케일 설정 모듈 생성
        locale_config = '''
import os
import locale
from datetime import datetime
import pytz

# 로케일 설정 통일
def setup_locale():
    """표준 로케일 설정"""
    # 한국 시간대 설정
    os.environ['TZ'] = 'Asia/Seoul'
    
    # 한국 로케일 설정
    try:
        locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'ko_KR')
        except:
            pass  # 기본 로케일 사용
    
    return pytz.timezone('Asia/Seoul')

# 표준 시간 포맷
def get_current_time():
    """현재 시간 (한국 시간대)"""
    tz = setup_locale()
    return datetime.now(tz)

def format_datetime(dt, format_str="%Y-%m-%d %H:%M:%S"):
    """표준 시간 포맷"""
    if dt.tzinfo is None:
        dt = setup_locale().localize(dt)
    return dt.strftime(format_str)
'''
        
        # 공통 모듈에 로케일 설정 추가
        locale_file = Path("src/utils/locale_config.py")
        if not locale_file.exists():
            with open(locale_file, 'w', encoding='utf-8') as f:
                f.write(locale_config)
            
            self.fixes_applied.append({
                'file': str(locale_file),
                'type': 'locale_standardization',
                'description': '표준 로케일 설정 모듈 생성'
            })
        
        # 기존 파일에서 로케일 관련 코드 수정
        locale_fixes = [
            (r'datetime\.now\(\)', 'get_current_time()'),
            (r'\.strftime\(["\']%Y-%m-%d["\']\)', '.strftime("%Y-%m-%d %H:%M:%S")'),
        ]
        
        for py_file in Path("src").rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                for pattern, replacement in locale_fixes:
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
                        'type': 'locale_standardization',
                        'description': '로케일 설정 통일'
                    })
                    
            except Exception as e:
                print(f"⚠️ 로케일 수정 실패: {py_file}, 오류: {e}")
    
    def _standardize_response_structures(self):
        """응답 구조 표준화"""
        print("🔧 응답 구조 표준화 중...")
        
        # 표준 응답 구조 정의
        standard_response = '''{
    "status": "success",
    "message": None,
    "data": result,
    "timestamp": get_current_time().isoformat(),
    "processing_time": processing_time
}'''
        
        error_response = '''{
    "status": "error",
    "message": str(error),
    "error_code": error_code,
    "details": error_details,
    "timestamp": get_current_time().isoformat()
}'''
        
        # 응답 구조 수정
        response_fixes = [
            (r'return\s+\{\s*"error"', 'return {"status": "error"'),
            (r'return\s+\{\s*"success"', 'return {"status": "success"'),
            (r'return\s+\{\s*"result"', 'return {"status": "success", "data": result'),
        ]
        
        for py_file in Path("src").rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                for pattern, replacement in response_fixes:
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
        """JSON Schema 검증 추가"""
        print("🔧 JSON Schema 검증 추가 중...")
        
        # Pydantic 기반 스키마 검증 모듈
        schema_validation = '''
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime

class BaseRequest(BaseModel):
    """기본 요청 모델"""
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class BaseResponse(BaseModel):
    """기본 응답 모델"""
    status: str = Field(..., description="처리 상태")
    message: Optional[str] = Field(default=None, description="메시지")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ['success', 'error']:
            raise ValueError('status must be "success" or "error"')
        return v

class AudioRequest(BaseRequest):
    """오디오 요청 모델"""
    audio_data: str = Field(..., description="Base64 인코딩된 오디오 데이터")
    sample_rate: int = Field(default=16000, ge=8000, le=48000)
    format: str = Field(default="wav", regex="^(wav|mp3|flac)$")

class TextRequest(BaseRequest):
    """텍스트 요청 모델"""
    text: str = Field(..., min_length=1, max_length=10000)
    language: str = Field(default="ko", regex="^[a-z]{2}$")

class AnalysisResponse(BaseResponse):
    """분석 응답 모델"""
    data: Optional[Dict[str, Any]] = Field(default=None)
    processing_time: Optional[float] = Field(default=None, ge=0)
'''
        
        # 스키마 검증 모듈 생성
        schema_file = Path("src/utils/schema_validation.py")
        if not schema_file.exists():
            with open(schema_file, 'w', encoding='utf-8') as f:
                f.write(schema_validation)
            
            self.fixes_applied.append({
                'file': str(schema_file),
                'type': 'schema_validation',
                'description': 'JSON Schema 검증 모듈 생성'
            })
    
    def _create_adapter_layer(self):
        """중간 변환 계층(Adapter) 생성"""
        print("🔧 중간 변환 계층 생성 중...")
        
        # API Adapter 모듈
        adapter_code = '''
"""
API 중간 변환 계층 (Adapter)
서비스 간 데이터 포맷 변환 및 검증
"""

import json
from typing import Dict, Any, Optional
from .schema_validation import BaseRequest, BaseResponse, AudioRequest, TextRequest, AnalysisResponse
from .locale_config import get_current_time

class APIAdapter:
    """API 데이터 변환 어댑터"""
    
    @staticmethod
    def validate_request(data: Dict[str, Any], request_type: str) -> Dict[str, Any]:
        """요청 데이터 검증 및 변환"""
        try:
            if request_type == "audio":
                validated = AudioRequest(**data)
            elif request_type == "text":
                validated = TextRequest(**data)
            else:
                validated = BaseRequest(**data)
            
            return validated.dict()
        except Exception as e:
            raise ValueError(f"요청 데이터 검증 실패: {e}")
    
    @staticmethod
    def format_response(data: Any, status: str = "success", message: Optional[str] = None) -> Dict[str, Any]:
        """응답 데이터 포맷 변환"""
        try:
            response = AnalysisResponse(
                status=status,
                message=message,
                data=data if status == "success" else None,
                timestamp=get_current_time().isoformat()
            )
            return response.dict()
        except Exception as e:
            # 폴백 응답
            return {
                "status": status,
                "message": message or str(e),
                "data": data if status == "success" else None,
                "timestamp": get_current_time().isoformat()
            }
    
    @staticmethod
    def convert_encoding(text: str, from_encoding: str = "utf-8", to_encoding: str = "utf-8") -> str:
        """인코딩 변환"""
        if from_encoding == to_encoding:
            return text
        
        try:
            # 중간 단계를 거쳐 변환
            bytes_data = text.encode(from_encoding)
            return bytes_data.decode(to_encoding)
        except Exception as e:
            raise ValueError(f"인코딩 변환 실패: {e}")
    
    @staticmethod
    def normalize_data_types(data: Dict[str, Any]) -> Dict[str, Any]:
        """데이터 타입 정규화"""
        normalized = {}
        
        for key, value in data.items():
            if value == "":
                normalized[key] = None
            elif isinstance(value, list) and len(value) == 0:
                normalized[key] = []
            elif isinstance(value, dict) and len(value) == 0:
                normalized[key] = {}
            else:
                normalized[key] = value
        
        return normalized
'''
        
        # Adapter 모듈 생성
        adapter_file = Path("src/utils/api_adapter.py")
        if not adapter_file.exists():
            with open(adapter_file, 'w', encoding='utf-8') as f:
                f.write(adapter_code)
            
            self.fixes_applied.append({
                'file': str(adapter_file),
                'type': 'adapter_layer',
                'description': 'API 중간 변환 계층 생성'
            })
    
    def _generate_fix_report(self):
        """수정 리포트 생성"""
        print("\n" + "="*60)
        print("📊 데이터 포맷 & 프로토콜 표준화 리포트")
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
        for fix in self.fixes_applied[:10]:
            print(f"   - {fix['file']}: {fix['description']}")
        
        # 백업 정보
        print(f"\n💾 백업 파일 위치: {self.backup_dir}")
        
        # 권장사항
        print(f"\n💡 다음 단계:")
        print(f"   1. 수정된 코드 테스트 실행")
        print(f"   2. API 엔드포인트 동작 확인")
        print(f"   3. 인코딩 및 로케일 설정 확인")
        print(f"   4. JSON Schema 검증 동작 확인")
        
        # 상세 리포트 저장
        report = {
            'summary': {
                'total_fixes': len(self.fixes_applied),
                'fix_types': fix_types
            },
            'fixes': self.fixes_applied,
            'backup_location': str(self.backup_dir)
        }
        
        with open('data_format_fix_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 상세 리포트 저장: data_format_fix_report.json")

def main():
    standardizer = DataFormatStandardizer()
    standardizer.standardize_all()
    print("\n🎉 데이터 포맷 & 프로토콜 표준화 완료!")

if __name__ == "__main__":
    main() 