#!/usr/bin/env python3
"""
음성 인식 서비스
Whisper 기반 음성 인식 및 텍스트 변환
"""

import os
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from pathlib import Path

# 음성 인식 모듈 import
from .advanced_analysis import AdvancedCommunicationAnalyzer

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Speech Recognizer Service", version="1.0.0")

# 음성 인식기 인스턴스
recognizer = AdvancedCommunicationAnalyzer()

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return JSONResponse({
        "status": "healthy",
        "service": "speech-recognizer",
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
            "service": "speech-recognizer"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transcribe")
async def transcribe_audio(data: Dict[str, Any]):
    """음성 인식 엔드포인트"""
    try:
        segments = data.get('segments', [])
        audio_path = data.get('audio_path')
        
        if not segments and not audio_path:
            raise HTTPException(status_code=400, detail="segments 또는 audio_path가 필요합니다")
        
        logger.info(f"음성 인식 시작: {len(segments)}개 세그먼트")
        
        # 음성 인식 실행
        if segments:
            transcriptions = await recognizer.transcribe_segments_async(segments)
        else:
            transcriptions = await recognizer.transcribe_audio_async(audio_path)
        
        logger.info(f"음성 인식 완료: {len(transcriptions)}개 전사")
        
        return JSONResponse({
            "status": "success",
            "transcriptions": transcriptions,
            "transcription_count": len(transcriptions),
            "message": "음성 인식이 완료되었습니다"
        })
        
    except Exception as e:
        logger.error(f"음성 인식 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transcribe_file")
async def transcribe_file(data: Dict[str, Any]):
    """파일 기반 음성 인식 엔드포인트"""
    try:
        audio_path = data.get('audio_path')
        if not audio_path:
            raise HTTPException(status_code=400, detail="audio_path가 필요합니다")
        
        if not Path(audio_path).exists():
            raise HTTPException(status_code=404, detail=f"오디오 파일을 찾을 수 없습니다: {audio_path}")
        
        logger.info(f"파일 음성 인식 시작: {audio_path}")
        
        # 파일 기반 음성 인식 실행
        result = await recognizer.transcribe_audio_async(audio_path)
        
        logger.info(f"파일 음성 인식 완료: {audio_path}")
        
        return JSONResponse({
            "status": "success",
            "audio_path": audio_path,
            "text": result.get('text', ''),
            "segments": result.get('segments', []),
            "message": "파일 음성 인식이 완료되었습니다"
        })
        
    except Exception as e:
        logger.error(f"파일 음성 인식 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Speech Recognizer Service가 실행 중입니다",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "transcribe": "/transcribe",
            "transcribe_file": "/transcribe_file"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003) 