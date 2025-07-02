#!/usr/bin/env python3
"""
화자 분리 서비스
NeMo 기반 화자 분리 및 세그먼트 생성
"""

import os
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from pathlib import Path

# 화자 분리 모듈 import
from .advanced_analysis import AdvancedCommunicationAnalyzer

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Speaker Diarizer Service", version="1.0.0")

# 화자 분리기 인스턴스
diarizer = AdvancedCommunicationAnalyzer()

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return JSONResponse({
        "status": "healthy",
        "service": "speaker-diarizer",
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
            "service": "speaker-diarizer"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/diarize")
async def diarize_speakers(data: Dict[str, Any]):
    """화자 분리 엔드포인트"""
    try:
        audio_path = data.get('audio_path')
        if not audio_path:
            raise HTTPException(status_code=400, detail="audio_path가 필요합니다")
        
        if not Path(audio_path).exists():
            raise HTTPException(status_code=404, detail=f"오디오 파일을 찾을 수 없습니다: {audio_path}")
        
        logger.info(f"화자 분리 시작: {audio_path}")
        
        # 화자 분리 실행
        segments = await diarizer.diarize_speakers_async(audio_path)
        
        logger.info(f"화자 분리 완료: {len(segments)}개 세그먼트")
        
        return JSONResponse({
            "status": "success",
            "audio_path": audio_path,
            "segments": segments,
            "segment_count": len(segments),
            "message": "화자 분리가 완료되었습니다"
        })
        
    except Exception as e:
        logger.error(f"화자 분리 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze_speakers")
async def analyze_speakers(data: Dict[str, Any]):
    """화자 분석 엔드포인트"""
    try:
        audio_path = data.get('audio_path')
        segments = data.get('segments', [])
        
        if not audio_path:
            raise HTTPException(status_code=400, detail="audio_path가 필요합니다")
        
        logger.info(f"화자 분석 시작: {audio_path}")
        
        # 화자 분석 실행
        speaker_analysis = await diarizer.analyze_speakers_async(audio_path, segments)
        
        logger.info(f"화자 분석 완료: {len(speaker_analysis)}개 화자")
        
        return JSONResponse({
            "status": "success",
            "audio_path": audio_path,
            "speaker_analysis": speaker_analysis,
            "speaker_count": len(speaker_analysis),
            "message": "화자 분석이 완료되었습니다"
        })
        
    except Exception as e:
        logger.error(f"화자 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Speaker Diarizer Service가 실행 중입니다",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "diarize": "/diarize",
            "analyze_speakers": "/analyze_speakers"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002) 