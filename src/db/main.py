#!/usr/bin/env python3
"""
데이터베이스 서비스
분산 데이터베이스 관리 및 결과 저장
"""

import os
import time
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import HTTPException
import uvicorn

# BaseService 패턴 적용
from ..utils.base_service import BaseService
from ..utils.type_definitions import JsonDict
from ..utils.api_schemas import (
    HealthResponse,
    MetricsResponse,
    SaveResultRequest,
    SaveResultResponse,
    GetAnalysisResponse,
    SuccessResponse,
    create_success_response,
    create_error_response
)

# 데이터베이스 모듈 import (PostgreSQL)
from .postgres_manager import PostgreSQLManager

class DatabaseService(BaseService):
    """데이터베이스 서비스 클래스"""
    
    def __init__(self):
        super().__init__(
            service_name="database-service",
            version="2.0.0",
            description="PostgreSQL 기반 데이터베이스 관리 및 결과 저장 서비스"
        )
        self.postgres_manager: Optional[PostgreSQLManager] = None
    
    async def initialize_models(self) -> None:
        """PostgreSQL 연결 초기화"""
        try:
            self.logger.info("PostgreSQL 연결 초기화 시작")
            self.postgres_manager = PostgreSQLManager()
            await self.postgres_manager.initialize()
            
            # PostgreSQL 연결 테스트
            health_status = await self.postgres_manager.health_check()
            if health_status['status'] != 'healthy':
                raise Exception(f"PostgreSQL 연결 실패: {health_status}")
            
            self.model_ready = True
            self.logger.info("PostgreSQL 연결 초기화 완료")
        except Exception as e:
            self.logger.error(f"PostgreSQL 초기화 실패: {e}")
            self.model_ready = False
            raise e
    
    async def cleanup_models(self) -> None:
        """PostgreSQL 연결 정리"""
        if self.postgres_manager:
            self.logger.info("PostgreSQL 연결 정리")
            await self.postgres_manager.close()
            self.postgres_manager = None
    
    def db_get_custom_metrics(self) -> JsonDict:
        """PostgreSQL 커스텀 메트릭 반환"""
        stats = {}
        
        if self.postgres_manager:
            stats = self.postgres_manager.get_stats()
        
        return {
            "database_ready": self.postgres_manager is not None and self.postgres_manager.is_connected,
            "database_type": "PostgreSQL",
            "connection_pool_stats": stats,
            "supported_operations": [
                "save_audio_analysis",
                "save_quality_analysis",
                "get_analysis", 
                "list_analyses",
                "health_check"
            ],
            "tables": [
                "audio_files",
                "consultation_sessions",
                "sentiment_analysis",
                "transcriptions",
                "speaker_segments"
            ]
        }

# 서비스 인스턴스 생성
service = DatabaseService()

@asynccontextmanager
async def lifespan(app):
    """애플리케이션 생명주기 관리"""
    await service.startup()
    yield
    await service.shutdown()

# FastAPI 앱 생성
app = service.create_app(lifespan=lifespan)

# 공통 엔드포인트 사용
from src.utils.common_endpoints import get_common_endpoints

db_common_endpoints = get_common_endpoints("database-service", "1.0.0")

# 커스텀 헬스체크 오버라이드 (데이터베이스 상태 포함)
@app.get("/health", response_model=SuccessResponse)
async def health_check() -> SuccessResponse:
    """헬스체크 엔드포인트 (데이터베이스 상태 포함)"""
    try:
        if not service.model_ready or not service.db_manager:
            raise HTTPException(status_code=503, detail="데이터베이스가 준비되지 않았습니다")
        
        # 데이터베이스 연결 확인
        audio_conn = service.db_manager.get_connection('audio')
        quality_conn = service.db_manager.get_connection('quality')
        
        # 추가 체크 항목 구성
        additional_checks = {
            "databases": {
                "audio": "connected",
                "quality": "connected"
            },
            "uptime_seconds": service.get_uptime()
        }
        
        health_result = await db_common_endpoints.health_check(additional_checks)
        
        return SuccessResponse(
            status="success",
            message="Database Service 정상 동작",
            data=health_result
        )
    except Exception as e:
        service.logger.error(f"헬스체크 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save_result", response_model=SaveResultResponse)
async def save_result(request: SaveResultRequest) -> SaveResultResponse:
    """분석 결과 저장 엔드포인트"""
    try:
        if not service.model_ready:
            raise HTTPException(status_code=503, detail="데이터베이스가 준비되지 않았습니다")
        
        service.logger.info("분석 결과 저장 시작")
        
        audio_id = None
        quality_id = None
        
        # 오디오 분석 결과 저장
        if 'audio_path' in request.result and request.result['audio_path']:
            audio_id = await service.db_manager.save_audio_analysis_async(request.result)
            service.logger.info(f"오디오 분석 결과 저장 완료: {audio_id}")
        
        # 상담 품질 분석 결과 저장 
        if 'sentiment_analysis' in request.result or 'llm_analysis' in request.result:
            quality_id = await service.db_manager.save_quality_analysis_async(request.result)
            service.logger.info(f"상담 품질 분석 결과 저장 완료: {quality_id}")
        
        service.logger.info("분석 결과 저장 완료")
        
        return SaveResultResponse(
            status="success",
            message="분석 결과가 저장되었습니다",
            data={
                "audio_id": audio_id,
                "quality_id": quality_id,
                "save_timestamp": time.time(),
                "result_type": request.result_type
            },
            saved_ids={
                "audio_id": audio_id,
                "quality_id": quality_id
            }
        )
        
    except Exception as e:
        service.logger.error(f"분석 결과 저장 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save_audio_analysis", response_model=SaveResultResponse)
async def save_audio_analysis(request: SaveResultRequest) -> SaveResultResponse:
    """오디오 분석 결과 저장 엔드포인트"""
    try:
        if not service.model_ready:
            raise HTTPException(status_code=503, detail="데이터베이스가 준비되지 않았습니다")
        
        service.logger.info("오디오 분석 결과 저장 시작")
        
        # 오디오 분석 결과 저장
        audio_id = await service.db_manager.save_audio_analysis_async(request.result)
        
        service.logger.info(f"오디오 분석 결과 저장 완료: {audio_id}")
        
        return SaveResultResponse(
            status="success",
            message="오디오 분석 결과가 저장되었습니다",
            data={
                "audio_id": audio_id,
                "save_timestamp": time.time(),
                "result_type": "audio_analysis"
            },
            saved_ids={
                "audio_id": audio_id,
                "quality_id": None
            }
        )
        
    except Exception as e:
        service.logger.error(f"오디오 분석 결과 저장 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save_quality_analysis", response_model=SaveResultResponse)
async def save_quality_analysis(request: SaveResultRequest) -> SaveResultResponse:
    """상담 품질 분석 결과 저장 엔드포인트"""
    try:
        if not service.model_ready:
            raise HTTPException(status_code=503, detail="데이터베이스가 준비되지 않았습니다")
        
        service.logger.info("상담 품질 분석 결과 저장 시작")
        
        # 상담 품질 분석 결과 저장
        quality_id = await service.db_manager.save_quality_analysis_async(request.result)
        
        service.logger.info(f"상담 품질 분석 결과 저장 완료: {quality_id}")
        
        return SaveResultResponse(
            status="success",
            message="상담 품질 분석 결과가 저장되었습니다",
            data={
                "quality_id": quality_id,
                "save_timestamp": time.time(),
                "result_type": "quality_analysis"
            },
            saved_ids={
                "audio_id": None,
                "quality_id": quality_id
            }
        )
        
    except Exception as e:
        service.logger.error(f"상담 품질 분석 결과 저장 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_analysis/{analysis_id}", response_model=GetAnalysisResponse)
async def get_analysis(analysis_id: str, db_type: str = "audio") -> GetAnalysisResponse:
    """분석 결과 조회 엔드포인트"""
    try:
        if not service.model_ready:
            raise HTTPException(status_code=503, detail="데이터베이스가 준비되지 않았습니다")
        
        service.logger.info(f"분석 결과 조회: {analysis_id} (DB: {db_type})")
        
        if db_type == "audio":
            result = await service.db_manager.get_audio_analysis_async(analysis_id)
        elif db_type == "quality":
            result = await service.db_manager.get_quality_analysis_async(analysis_id)
        else:
            raise HTTPException(status_code=400, detail="db_type은 'audio' 또는 'quality'여야 합니다")
        
        if not result:
            raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다")
        
        return GetAnalysisResponse(
            status="success",
            message=f"분석 결과 조회 완료: {analysis_id}",
            data={
                "analysis_id": analysis_id,
                "db_type": db_type,
                "result": result
            },
            analysis_id=analysis_id,
            result=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        service.logger.error(f"분석 결과 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list_analyses", response_model=SuccessResponse)
async def list_analyses(db_type: str = "audio", limit: int = 10, offset: int = 0) -> SuccessResponse:
    """분석 결과 목록 조회 엔드포인트"""
    try:
        if not service.model_ready:
            raise HTTPException(status_code=503, detail="데이터베이스가 준비되지 않았습니다")
        
        service.logger.info(f"분석 결과 목록 조회: {db_type} (limit: {limit}, offset: {offset})")
        
        if db_type == "audio":
            results = await service.db_manager.list_audio_analyses_async(limit, offset)
        elif db_type == "quality":
            results = await service.db_manager.list_quality_analyses_async(limit, offset)
        else:
            raise HTTPException(status_code=400, detail="db_type은 'audio' 또는 'quality'여야 합니다")
        
        return SuccessResponse(
            status="success",
            message=f"분석 결과 목록 조회 완료 ({db_type})",
            data={
                "db_type": db_type,
                "results": results,
                "count": len(results),
                "limit": limit,
                "offset": offset
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        service.logger.error(f"분석 결과 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8007) 