#!/usr/bin/env python3
"""
데이터베이스 서비스
분산 데이터베이스 관리 및 결과 저장
"""

import os
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# 데이터베이스 모듈 import
from .advanced_manager import MultiDatabaseManager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Database Service", version="1.0.0")

# 데이터베이스 매니저 인스턴스
db_manager = MultiDatabaseManager()

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    try:
        # 데이터베이스 연결 확인
        audio_conn = db_manager.get_connection('audio')
        quality_conn = db_manager.get_connection('quality')
        
        return JSONResponse({
            "status": "healthy",
            "service": "database-service",
            "version": "1.0.0",
            "databases": {
                "audio": "connected",
                "quality": "connected"
            }
        })
    except Exception as e:
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e)
        }, status_code=500)

@app.get("/metrics")
async def get_metrics():
    """메트릭 엔드포인트"""
    try:
        import psutil
        
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # 데이터베이스 크기 확인
        db_sizes = {}
        try:
            audio_conn = db_manager.get_connection('audio')
            audio_size = os.path.getsize(db_manager.audio_db_path) / (1024 * 1024)  # MB
            db_sizes['audio'] = f"{audio_size:.2f} MB"
        except:
            db_sizes['audio'] = "unknown"
        
        try:
            quality_conn = db_manager.get_connection('quality')
            quality_size = os.path.getsize(db_manager.quality_db_path) / (1024 * 1024)  # MB
            db_sizes['quality'] = f"{quality_size:.2f} MB"
        except:
            db_sizes['quality'] = "unknown"
        
        return JSONResponse({
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / 1024**3,
            "service": "database-service",
            "database_sizes": db_sizes
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save_result")
async def save_result(data: Dict[str, Any]):
    """분석 결과 저장 엔드포인트"""
    try:
        result = data.get('result', {})
        if not result:
            raise HTTPException(status_code=400, detail="result가 필요합니다")
        
        logger.info("분석 결과 저장 시작")
        
        # 오디오 분석 결과 저장
        if 'audio_path' in result:
            audio_id = await db_manager.save_audio_analysis_async(result)
            logger.info(f"오디오 분석 결과 저장 완료: {audio_id}")
        
        # 상담 품질 분석 결과 저장
        if 'llm_analysis' in result or 'sentiment_analysis' in result:
            quality_id = await db_manager.save_quality_analysis_async(result)
            logger.info(f"상담 품질 분석 결과 저장 완료: {quality_id}")
        
        logger.info("분석 결과 저장 완료")
        
        return JSONResponse({
            "status": "success",
            "message": "분석 결과가 저장되었습니다",
            "saved_ids": {
                "audio_id": audio_id if 'audio_path' in result else None,
                "quality_id": quality_id if ('llm_analysis' in result or 'sentiment_analysis' in result) else None
            }
        })
        
    except Exception as e:
        logger.error(f"분석 결과 저장 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save_audio_analysis")
async def save_audio_analysis(data: Dict[str, Any]):
    """오디오 분석 결과 저장 엔드포인트"""
    try:
        result = data.get('result', {})
        if not result:
            raise HTTPException(status_code=400, detail="result가 필요합니다")
        
        logger.info("오디오 분석 결과 저장 시작")
        
        # 오디오 분석 결과 저장
        audio_id = await db_manager.save_audio_analysis_async(result)
        
        logger.info(f"오디오 분석 결과 저장 완료: {audio_id}")
        
        return JSONResponse({
            "status": "success",
            "audio_id": audio_id,
            "message": "오디오 분석 결과가 저장되었습니다"
        })
        
    except Exception as e:
        logger.error(f"오디오 분석 결과 저장 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save_quality_analysis")
async def save_quality_analysis(data: Dict[str, Any]):
    """상담 품질 분석 결과 저장 엔드포인트"""
    try:
        result = data.get('result', {})
        if not result:
            raise HTTPException(status_code=400, detail="result가 필요합니다")
        
        logger.info("상담 품질 분석 결과 저장 시작")
        
        # 상담 품질 분석 결과 저장
        quality_id = await db_manager.save_quality_analysis_async(result)
        
        logger.info(f"상담 품질 분석 결과 저장 완료: {quality_id}")
        
        return JSONResponse({
            "status": "success",
            "quality_id": quality_id,
            "message": "상담 품질 분석 결과가 저장되었습니다"
        })
        
    except Exception as e:
        logger.error(f"상담 품질 분석 결과 저장 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_analysis/{analysis_id}")
async def get_analysis(analysis_id: str, db_type: str = "audio"):
    """분석 결과 조회 엔드포인트"""
    try:
        logger.info(f"분석 결과 조회: {analysis_id} (DB: {db_type})")
        
        if db_type == "audio":
            result = await db_manager.get_audio_analysis_async(analysis_id)
        elif db_type == "quality":
            result = await db_manager.get_quality_analysis_async(analysis_id)
        else:
            raise HTTPException(status_code=400, detail="db_type은 'audio' 또는 'quality'여야 합니다")
        
        if not result:
            raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다")
        
        return JSONResponse({
            "status": "success",
            "analysis_id": analysis_id,
            "result": result
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"분석 결과 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list_analyses")
async def list_analyses(db_type: str = "audio", limit: int = 10, offset: int = 0):
    """분석 결과 목록 조회 엔드포인트"""
    try:
        logger.info(f"분석 결과 목록 조회: {db_type} (limit: {limit}, offset: {offset})")
        
        if db_type == "audio":
            results = await db_manager.list_audio_analyses_async(limit, offset)
        elif db_type == "quality":
            results = await db_manager.list_quality_analyses_async(limit, offset)
        else:
            raise HTTPException(status_code=400, detail="db_type은 'audio' 또는 'quality'여야 합니다")
        
        return JSONResponse({
            "status": "success",
            "db_type": db_type,
            "results": results,
            "count": len(results)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"분석 결과 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Database Service가 실행 중입니다",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "save_result": "/save_result",
            "save_audio_analysis": "/save_audio_analysis",
            "save_quality_analysis": "/save_quality_analysis",
            "get_analysis": "/get_analysis/{analysis_id}",
            "list_analyses": "/list_analyses"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8007) 