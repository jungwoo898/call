#!/usr/bin/env python3
"""
OpenAPI 명세 및 JSON Schema 자동 생성 스크립트
API 계약 문제를 해결하기 위한 표준화된 명세 생성
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any

class OpenAPIGenerator:
    def __init__(self):
        self.openapi_spec = {
            "openapi": "3.0.3",
            "info": {
                "title": "Callytics API",
                "description": "음성 분석 및 텍스트 처리 마이크로서비스 API",
                "version": "1.0.0"
            },
            "servers": [
                {"url": "http://localhost:8000", "description": "개발 서버"},
                {"url": "http://localhost:8001", "description": "오디오 처리 서버"},
                {"url": "http://localhost:8002", "description": "텍스트 분석 서버"},
                {"url": "http://localhost:8003", "description": "데이터베이스 서버"}
            ],
            "paths": {},
            "components": {
                "schemas": {},
                "responses": {
                    "SuccessResponse": {
                        "description": "성공 응답",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {"type": "string", "example": "success"},
                                        "message": {"type": "string", "example": "처리 완료"},
                                        "data": {"type": "object"}
                                    },
                                    "required": ["status"]
                                }
                            }
                        }
                    },
                    "ErrorResponse": {
                        "description": "오류 응답",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {"type": "string", "example": "error"},
                                        "message": {"type": "string", "example": "처리 실패"},
                                        "error_code": {"type": "string"},
                                        "details": {"type": "object"}
                                    },
                                    "required": ["status", "message"]
                                }
                            }
                        }
                    }
                }
            }
        }
        
        # 표준 스키마 정의
        self.standard_schemas = {
            "AudioInput": {
                "type": "object",
                "properties": {
                    "audio_data": {"type": "string", "description": "Base64 인코딩된 오디오 데이터"},
                    "sample_rate": {"type": "integer", "description": "샘플링 레이트 (Hz)", "default": 16000},
                    "format": {"type": "string", "description": "오디오 포맷", "enum": ["wav", "mp3", "flac"], "default": "wav"}
                },
                "required": ["audio_data"]
            },
            "TextInput": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "분석할 텍스트"},
                    "language": {"type": "string", "description": "언어 코드", "default": "ko"},
                    "options": {"type": "object", "description": "추가 옵션"}
                },
                "required": ["text"]
            },
            "AnalysisResult": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["success", "error"]},
                    "message": {"type": "string"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "result": {"type": "object"},
                            "processing_time": {"type": "number"},
                            "timestamp": {"type": "string", "format": "date-time"}
                        }
                    }
                },
                "required": ["status"]
            }
        }
    
    def generate_spec(self):
        """OpenAPI 명세 생성"""
        print("🔧 OpenAPI 명세 생성 중...")
        
        # 표준 스키마 추가
        self.openapi_spec["components"]["schemas"].update(self.standard_schemas)
        
        # 각 서비스별 API 정의
        self._add_audio_service_apis()
        self._add_text_service_apis()
        self._add_database_service_apis()
        self._add_gateway_apis()
        
        # 명세 저장
        self._save_spec()
        
        # JSON Schema 파일들 생성
        self._generate_json_schemas()
        
        print("✅ OpenAPI 명세 생성 완료!")
    
    def _add_audio_service_apis(self):
        """오디오 처리 서비스 API 추가"""
        audio_paths = {
            "/preprocess": {
                "post": {
                    "tags": ["Audio Processing"],
                    "summary": "오디오 전처리",
                    "description": "오디오 파일을 전처리하여 분석에 적합한 형태로 변환",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/AudioInput"}
                            }
                        }
                    },
                    "responses": {
                        "200": {"$ref": "#/components/responses/SuccessResponse"},
                        "400": {"$ref": "#/components/responses/ErrorResponse"},
                        "500": {"$ref": "#/components/responses/ErrorResponse"}
                    }
                }
            },
            "/enhance": {
                "post": {
                    "tags": ["Audio Processing"],
                    "summary": "오디오 품질 향상",
                    "description": "노이즈 제거 및 음성 품질 향상",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/AudioInput"}
                            }
                        }
                    },
                    "responses": {
                        "200": {"$ref": "#/components/responses/SuccessResponse"},
                        "400": {"$ref": "#/components/responses/ErrorResponse"},
                        "500": {"$ref": "#/components/responses/ErrorResponse"}
                    }
                }
            },
            "/segment": {
                "post": {
                    "tags": ["Audio Processing"],
                    "summary": "화자 분리",
                    "description": "오디오에서 화자를 분리하고 세그먼트 생성",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/AudioInput"}
                            }
                        }
                    },
                    "responses": {
                        "200": {"$ref": "#/components/responses/SuccessResponse"},
                        "400": {"$ref": "#/components/responses/ErrorResponse"},
                        "500": {"$ref": "#/components/responses/ErrorResponse"}
                    }
                }
            }
        }
        
        self.openapi_spec["paths"].update(audio_paths)
    
    def _add_text_service_apis(self):
        """텍스트 분석 서비스 API 추가"""
        text_paths = {
            "/analyze": {
                "post": {
                    "tags": ["Text Analysis"],
                    "summary": "텍스트 종합 분석",
                    "description": "감정 분석, 주제 분류, 품질 평가 등을 수행",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/TextInput"}
                            }
                        }
                    },
                    "responses": {
                        "200": {"$ref": "#/components/responses/SuccessResponse"},
                        "400": {"$ref": "#/components/responses/ErrorResponse"},
                        "500": {"$ref": "#/components/responses/ErrorResponse"}
                    }
                }
            },
            "/sentiment": {
                "post": {
                    "tags": ["Text Analysis"],
                    "summary": "감정 분석",
                    "description": "텍스트의 감정을 분석",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/TextInput"}
                            }
                        }
                    },
                    "responses": {
                        "200": {"$ref": "#/components/responses/SuccessResponse"},
                        "400": {"$ref": "#/components/responses/ErrorResponse"},
                        "500": {"$ref": "#/components/responses/ErrorResponse"}
                    }
                }
            },
            "/punctuation": {
                "post": {
                    "tags": ["Text Analysis"],
                    "summary": "문장 부호 복원",
                    "description": "음성 인식 결과에 문장 부호 추가",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/TextInput"}
                            }
                        }
                    },
                    "responses": {
                        "200": {"$ref": "#/components/responses/SuccessResponse"},
                        "400": {"$ref": "#/components/responses/ErrorResponse"},
                        "500": {"$ref": "#/components/responses/ErrorResponse"}
                    }
                }
            }
        }
        
        self.openapi_spec["paths"].update(text_paths)
    
    def _add_database_service_apis(self):
        """데이터베이스 서비스 API 추가"""
        db_paths = {
            "/health": {
                "get": {
                    "tags": ["Database"],
                    "summary": "데이터베이스 상태 확인",
                    "description": "데이터베이스 연결 상태 및 서비스 상태 확인",
                    "responses": {
                        "200": {"$ref": "#/components/responses/SuccessResponse"},
                        "500": {"$ref": "#/components/responses/ErrorResponse"}
                    }
                }
            },
            "/save_result": {
                "post": {
                    "tags": ["Database"],
                    "summary": "분석 결과 저장",
                    "description": "분석 결과를 데이터베이스에 저장",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "analysis_type": {"type": "string", "enum": ["audio", "text", "quality"]},
                                        "result_data": {"type": "object"},
                                        "metadata": {"type": "object"}
                                    },
                                    "required": ["analysis_type", "result_data"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"$ref": "#/components/responses/SuccessResponse"},
                        "400": {"$ref": "#/components/responses/ErrorResponse"},
                        "500": {"$ref": "#/components/responses/ErrorResponse"}
                    }
                }
            }
        }
        
        self.openapi_spec["paths"].update(db_paths)
    
    def _add_gateway_apis(self):
        """게이트웨이 API 추가"""
        gateway_paths = {
            "/process": {
                "post": {
                    "tags": ["Gateway"],
                    "summary": "통합 처리",
                    "description": "오디오 업로드부터 분석 완료까지 전체 파이프라인 처리",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/AudioInput"}
                            }
                        }
                    },
                    "responses": {
                        "200": {"$ref": "#/components/responses/SuccessResponse"},
                        "400": {"$ref": "#/components/responses/ErrorResponse"},
                        "500": {"$ref": "#/components/responses/ErrorResponse"}
                    }
                }
            }
        }
        
        self.openapi_spec["paths"].update(gateway_paths)
    
    def _save_spec(self):
        """OpenAPI 명세 저장"""
        # JSON 형식으로만 저장
        with open('openapi.json', 'w', encoding='utf-8') as f:
            json.dump(self.openapi_spec, f, indent=2, ensure_ascii=False)
        
        print("📄 OpenAPI 명세 저장: openapi.json")
    
    def _generate_json_schemas(self):
        """개별 JSON Schema 파일들 생성"""
        schemas_dir = Path("schemas")
        schemas_dir.mkdir(exist_ok=True)
        
        # 각 스키마를 개별 파일로 저장
        for schema_name, schema_def in self.standard_schemas.items():
            schema_file = schemas_dir / f"{schema_name.lower()}.json"
            with open(schema_file, 'w', encoding='utf-8') as f:
                json.dump(schema_def, f, indent=2, ensure_ascii=False)
        
        # 응답 스키마들도 저장
        response_schemas = {
            "success_response": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["success"]},
                    "message": {"type": "string"},
                    "data": {"type": "object"}
                },
                "required": ["status"]
            },
            "error_response": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["error"]},
                    "message": {"type": "string"},
                    "error_code": {"type": "string"},
                    "details": {"type": "object"}
                },
                "required": ["status", "message"]
            }
        }
        
        for schema_name, schema_def in response_schemas.items():
            schema_file = schemas_dir / f"{schema_name}.json"
            with open(schema_file, 'w', encoding='utf-8') as f:
                json.dump(schema_def, f, indent=2, ensure_ascii=False)
        
        print(f"📄 JSON Schema 파일들 저장: schemas/ 디렉토리")

def main():
    generator = OpenAPIGenerator()
    generator.generate_spec()
    print("\n🎉 OpenAPI 명세 및 JSON Schema 생성 완료!")

if __name__ == "__main__":
    main() 