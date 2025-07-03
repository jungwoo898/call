#!/usr/bin/env python3
"""
Callytics 마이크로서비스 API 문서 생성기
모든 서비스의 OpenAPI 스키마를 수집하고 통합 문서를 생성
"""

import json
import yaml
import asyncio
import aiohttp
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 서비스 URL 설정
SERVICE_URLS = {
    "api-gateway": "http://localhost:8000",
    "audio-processor": "http://localhost:8001",
    "speaker-diarizer": "http://localhost:8002",
    "speech-recognizer": "http://localhost:8003",
    "punctuation-restorer": "http://localhost:8004",
    "sentiment-analyzer": "http://localhost:8005",
    "llm-analyzer": "http://localhost:8006",
    "database-service": "http://localhost:8007"
}

class APIDocumentationGenerator:
    """API 문서 생성기"""
    
    def __init__(self):
        self.service_schemas = {}
        self.service_health = {}
    
    async def check_service_health(self, session: aiohttp.ClientSession, 
                                 service_name: str, base_url: str) -> bool:
        """서비스 헬스체크"""
        try:
            async with session.get(f"{base_url}/health", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    self.service_health[service_name] = {
                        "status": "healthy",
                        "details": data
                    }
                    logger.info(f"✅ {service_name} 서비스 정상")
                    return True
                else:
                    logger.warning(f"⚠️ {service_name} 서비스 응답 오류: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ {service_name} 서비스 연결 실패: {e}")
            self.service_health[service_name] = {
                "status": "unhealthy",
                "error": str(e)
            }
            return False
    
    async def fetch_openapi_schema(self, session: aiohttp.ClientSession,
                                 service_name: str, base_url: str) -> Dict[str, Any]:
        """OpenAPI 스키마 가져오기"""
        try:
            async with session.get(f"{base_url}/openapi.json", timeout=15) as response:
                if response.status == 200:
                    schema = await response.json()
                    self.service_schemas[service_name] = schema
                    logger.info(f"📄 {service_name} OpenAPI 스키마 수집 완료")
                    return schema
                else:
                    logger.warning(f"⚠️ {service_name} OpenAPI 스키마 가져오기 실패: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"❌ {service_name} OpenAPI 스키마 오류: {e}")
            return {}
    
    async def collect_all_schemas(self):
        """모든 서비스의 스키마 수집"""
        async with aiohttp.ClientSession() as session:
            # 병렬로 헬스체크 실행
            health_tasks = [
                self.check_service_health(session, name, url)
                for name, url in SERVICE_URLS.items()
            ]
            health_results = await asyncio.gather(*health_tasks, return_exceptions=True)
            
            # 정상 서비스에서만 스키마 수집
            healthy_services = [
                (name, url) for (name, url), is_healthy in 
                zip(SERVICE_URLS.items(), health_results) if is_healthy is True
            ]
            
            logger.info(f"🟢 정상 서비스: {len(healthy_services)}/{len(SERVICE_URLS)}개")
            
            # 병렬로 스키마 수집
            if healthy_services:
                schema_tasks = [
                    self.fetch_openapi_schema(session, name, url)
                    for name, url in healthy_services
                ]
                await asyncio.gather(*schema_tasks, return_exceptions=True)
    
    def generate_unified_docs(self) -> Dict[str, Any]:
        """통합 API 문서 생성"""
        unified_docs = {
            "openapi": "3.0.0",
            "info": {
                "title": "Callytics 통합 API 문서",
                "description": "AI 기반 상담 품질 분석 시스템의 모든 마이크로서비스 API",
                "version": "1.0.0",
                "contact": {
                    "name": "Callytics Team",
                    "email": "team@callytics.com"
                },
                "license": {
                    "name": "MIT",
                    "url": "https://opensource.org/licenses/MIT"
                }
            },
            "servers": [
                {
                    "url": "http://localhost:8000",
                    "description": "개발 환경 (API Gateway)"
                }
            ],
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {}
            },
            "tags": []
        }
        
        # 각 서비스의 경로와 스키마 통합
        service_tags = []
        
        for service_name, schema in self.service_schemas.items():
            # 서비스별 태그 생성
            service_tag = {
                "name": service_name,
                "description": schema.get("info", {}).get("description", f"{service_name} 서비스")
            }
            service_tags.append(service_tag)
            
            # 경로 추가 (서비스별 prefix 추가)
            paths = schema.get("paths", {})
            for path, methods in paths.items():
                # 서비스별 prefix 추가 (gateway 제외)
                if service_name != "api-gateway":
                    prefixed_path = f"/{service_name}{path}"
                else:
                    prefixed_path = path
                
                # 각 메서드에 서비스 태그 추가
                for method, details in methods.items():
                    if "tags" not in details:
                        details["tags"] = []
                    details["tags"].append(service_name)
                    
                    # 서비스별 operationId prefix 추가
                    if "operationId" in details:
                        details["operationId"] = f"{service_name}_{details['operationId']}"
                
                unified_docs["paths"][prefixed_path] = methods
            
            # 스키마 통합 (이름 충돌 방지)
            components = schema.get("components", {})
            schemas = components.get("schemas", {})
            for schema_name, schema_def in schemas.items():
                prefixed_schema_name = f"{service_name}_{schema_name}"
                unified_docs["components"]["schemas"][prefixed_schema_name] = schema_def
        
        unified_docs["tags"] = service_tags
        return unified_docs
    
    def generate_service_summary(self) -> Dict[str, Any]:
        """서비스별 요약 정보 생성"""
        summary = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_services": len(SERVICE_URLS),
            "healthy_services": len([s for s in self.service_health.values() if s["status"] == "healthy"]),
            "services": {}
        }
        
        for service_name in SERVICE_URLS.keys():
            service_info = {
                "health": self.service_health.get(service_name, {"status": "unknown"}),
                "has_openapi": service_name in self.service_schemas,
                "endpoints": [],
                "schemas": []
            }
            
            if service_name in self.service_schemas:
                schema = self.service_schemas[service_name]
                
                # 엔드포인트 정보
                paths = schema.get("paths", {})
                for path, methods in paths.items():
                    for method in methods.keys():
                        if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                            service_info["endpoints"].append({
                                "path": path,
                                "method": method.upper(),
                                "summary": methods[method].get("summary", "")
                            })
                
                # 스키마 정보
                components = schema.get("components", {})
                schemas = components.get("schemas", {})
                service_info["schemas"] = list(schemas.keys())
            
            summary["services"][service_name] = service_info
        
        return summary
    
    def save_documentation(self, output_dir: str = "docs/api"):
        """문서 파일들 저장"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 1. 통합 OpenAPI 문서 (JSON)
        unified_docs = self.generate_unified_docs()
        with open(output_path / "openapi.json", 'w', encoding='utf-8') as f:
            json.dump(unified_docs, f, indent=2, ensure_ascii=False)
        
        # 2. 통합 OpenAPI 문서 (YAML)
        with open(output_path / "openapi.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(unified_docs, f, default_flow_style=False, allow_unicode=True)
        
        # 3. 서비스별 개별 스키마
        for service_name, schema in self.service_schemas.items():
            service_dir = output_path / "services" / service_name
            service_dir.mkdir(parents=True, exist_ok=True)
            
            with open(service_dir / "openapi.json", 'w', encoding='utf-8') as f:
                json.dump(schema, f, indent=2, ensure_ascii=False)
        
        # 4. 서비스 요약
        summary = self.generate_service_summary()
        with open(output_path / "services_summary.json", 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # 5. README 생성
        self.generate_readme(output_path, summary)
        
        logger.info(f"📚 API 문서 생성 완료: {output_path}")
        return output_path
    
    def generate_readme(self, output_path: Path, summary: Dict[str, Any]):
        """README.md 파일 생성"""
        readme_content = f"""# Callytics API 문서

AI 기반 상담 품질 분석 시스템의 통합 API 문서입니다.

## 📊 서비스 현황

- **전체 서비스**: {summary['total_services']}개
- **정상 서비스**: {summary['healthy_services']}개
- **문서 생성 시간**: {summary['timestamp']}

## 🔗 서비스 목록

| 서비스 | 상태 | 엔드포인트 수 | 스키마 수 | 설명 |
|--------|------|---------------|-----------|------|
"""
        
        for service_name, service_info in summary["services"].items():
            status_emoji = "🟢" if service_info["health"]["status"] == "healthy" else "🔴"
            endpoint_count = len(service_info["endpoints"])
            schema_count = len(service_info["schemas"])
            
            service_descriptions = {
                "api-gateway": "API 게이트웨이 및 오케스트레이터",
                "audio-processor": "오디오 전처리 및 향상",
                "speaker-diarizer": "화자 분리 및 식별",
                "speech-recognizer": "음성 인식 및 전사",
                "punctuation-restorer": "문장 부호 복원",
                "sentiment-analyzer": "감정 분석",
                "llm-analyzer": "LLM 기반 품질 분석",
                "database-service": "데이터 저장 및 조회"
            }
            
            description = service_descriptions.get(service_name, "알 수 없음")
            
            readme_content += f"| {service_name} | {status_emoji} | {endpoint_count} | {schema_count} | {description} |\n"
        
        readme_content += f"""

## 📖 문서 사용법

### OpenAPI 문서 보기

1. **통합 문서**: `openapi.json` 또는 `openapi.yaml`
2. **서비스별 문서**: `services/[서비스명]/openapi.json`
3. **Swagger UI**: http://localhost:8000/docs (API Gateway)

### 주요 엔드포인트

#### 🎵 오디오 처리
```bash
# 오디오 전처리
POST /audio-processor/preprocess
Content-Type: application/json

{{
    "audio_path": "/path/to/audio.wav",
    "options": {{}}
}}
```

#### 🎤 화자 분리
```bash
# 화자 분리
POST /speaker-diarizer/diarize
Content-Type: application/json

{{
    "audio_path": "/path/to/audio.wav",
    "min_speakers": 2,
    "max_speakers": 10
}}
```

#### 🗣️ 음성 인식
```bash
# 음성 인식
POST /speech-recognizer/transcribe
Content-Type: application/json

{{
    "audio_path": "/path/to/audio.wav",
    "language": "ko"
}}
```

#### 🤖 LLM 분석
```bash
# 품질 분석
POST /llm-analyzer/analyze
Content-Type: application/json

{{
    "text_data": "상담 대화 내용...",
    "analysis_type": "quality"
}}
```

## 🔧 개발 가이드

### 새 서비스 추가 시

1. **Pydantic 스키마 정의**: `src/utils/api_schemas.py`에 추가
2. **FastAPI 모델 적용**: `response_model` 매개변수 사용
3. **문서 재생성**: `python generate_api_docs.py` 실행

### API 스키마 검증

```bash
# 스키마 일관성 검증
python src/utils/schema_validator.py

# 문서 재생성
python generate_api_docs.py
```

## 📋 타입 안정성 가이드

### ✅ 권장 사항

1. **Pydantic 모델 사용**: `Dict[str, Any]` 대신 명시적 모델
2. **일관된 응답 형식**: `BaseResponse` 상속
3. **null vs empty 일관성**: `None` vs `""` vs `[]` 통일
4. **타입 명시**: 모든 필드에 타입 힌트 추가

### ❌ 피해야 할 것

1. `Dict[str, Any]` 직접 사용
2. 서비스별 다른 응답 형식
3. `"null"` vs `null` 혼용
4. 정수/문자열 타입 혼용

## 🚀 배포 정보

- **개발 환경**: http://localhost:8000
- **스테이징**: https://staging.callytics.com (예정)
- **프로덕션**: https://api.callytics.com (예정)

---
*이 문서는 자동 생성되었습니다. 최신 정보는 각 서비스의 `/docs` 엔드포인트를 확인하세요.*
"""
        
        with open(output_path / "README.md", 'w', encoding='utf-8') as f:
            f.write(readme_content)

async def main():
    """메인 실행 함수"""
    print("🚀 Callytics API 문서 생성을 시작합니다...")
    
    generator = APIDocumentationGenerator()
    
    # 1. 모든 서비스 스키마 수집
    await generator.collect_all_schemas()
    
    # 2. 문서 생성 및 저장
    output_path = generator.save_documentation()
    
    # 3. 결과 요약
    print(f"\n📚 API 문서 생성 완료!")
    print(f"📁 저장 위치: {output_path}")
    print(f"🔗 통합 문서: {output_path}/openapi.json")
    print(f"📖 README: {output_path}/README.md")
    
    # 4. 서비스 상태 요약
    healthy_count = len([s for s in generator.service_health.values() if s["status"] == "healthy"])
    total_count = len(SERVICE_URLS)
    print(f"\n📊 서비스 상태: {healthy_count}/{total_count}개 정상")
    
    for service_name, health in generator.service_health.items():
        status_emoji = "🟢" if health["status"] == "healthy" else "🔴"
        print(f"  {status_emoji} {service_name}: {health['status']}")

if __name__ == "__main__":
    asyncio.run(main()) 