#!/usr/bin/env python3
"""
Callytics 오디오 처리 서비스
오디오 파일 전처리, 노이즈 제거, 음성 강화
"""

import os
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path

# 오디오 처리 모듈 import
from . import preprocessing, processing, io
from .advanced_processing import AdvancedAudioProcessor

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    logger.info("🎵 Callytics 오디오 처리 서비스 시작")
    yield
    logger.info("🛑 Callytics 오디오 처리 서비스 종료")

app = FastAPI(title="Callytics Audio Processor", version="1.0.0", lifespan=lifespan)

# 오디오 프로세서 인스턴스
audio_processor = AdvancedAudioProcessor()

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return JSONResponse({
        "status": "healthy",
        "service": "audio-processor",
        "version": "1.0.0"
    })

@app.get("/metrics")
async def get_metrics():
    """메트릭 엔드포인트"""
    try:
        import psutil
        
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        return JSONResponse({
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / 1024**3,
            "service": "audio-processor"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/preprocess")
async def preprocess_audio(data: Dict[str, Any]):
    """오디오 전처리 엔드포인트"""
    try:
        audio_path = data.get('audio_path')
        if not audio_path:
            raise HTTPException(status_code=400, detail="audio_path가 필요합니다")
        
        if not Path(audio_path).exists():
            raise HTTPException(status_code=404, detail=f"오디오 파일을 찾을 수 없습니다: {audio_path}")
        
        logger.info(f"오디오 전처리 시작: {audio_path}")
        
        # 오디오 전처리 실행
        processed_path = await audio_processor.preprocess_audio_async(audio_path)
        
        logger.info(f"오디오 전처리 완료: {processed_path}")
        
        return JSONResponse({
            "status": "success",
            "original_path": audio_path,
            "processed_path": processed_path,
            "message": "오디오 전처리가 완료되었습니다"
        })
        
    except Exception as e:
        logger.error(f"오디오 전처리 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/enhance")
async def enhance_audio(data: Dict[str, Any]):
    """오디오 향상 엔드포인트"""
    try:
        audio_path = data.get('audio_path')
        if not audio_path:
            raise HTTPException(status_code=400, detail="audio_path가 필요합니다")
        
        logger.info(f"오디오 향상 시작: {audio_path}")
        
        # 오디오 향상 실행
        enhanced_path = await audio_processor.enhance_audio_async(audio_path)
        
        logger.info(f"오디오 향상 완료: {enhanced_path}")
        
        return JSONResponse({
            "status": "success",
            "original_path": audio_path,
            "enhanced_path": enhanced_path,
            "message": "오디오 향상이 완료되었습니다"
        })
        
    except Exception as e:
        logger.error(f"오디오 향상 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/segment")
async def segment_audio(data: Dict[str, Any]):
    """오디오 분할 엔드포인트"""
    try:
        audio_path = data.get('audio_path')
        chunk_duration = data.get('chunk_duration', 30)  # 기본 30초
        
        if not audio_path:
            raise HTTPException(status_code=400, detail="audio_path가 필요합니다")
        
        logger.info(f"오디오 분할 시작: {audio_path}, 청크 길이: {chunk_duration}초")
        
        # 오디오 분할 실행
        segments = await audio_processor.segment_audio_async(audio_path, chunk_duration)
        
        logger.info(f"오디오 분할 완료: {len(segments)}개 세그먼트")
        
        return JSONResponse({
            "status": "success",
            "original_path": audio_path,
            "segments": segments,
            "segment_count": len(segments),
            "message": "오디오 분할이 완료되었습니다"
        })
        
    except Exception as e:
        logger.error(f"오디오 분할 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Callytics 오디오 처리 서비스가 실행 중입니다",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "preprocess": "/preprocess",
            "enhance": "/enhance",
            "segment": "/segment"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001) 