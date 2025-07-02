#!/usr/bin/env python3
"""
문장 부호 복원 서비스
한국어 문장 부호 복원 및 텍스트 정제
"""

import os
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# 문장 부호 복원 모듈 import
from .advanced_analysis import AdvancedCommunicationAnalyzer

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Punctuation Restorer Service", version="1.0.0")

# 문장 부호 복원기 인스턴스
restorer = AdvancedCommunicationAnalyzer()

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return JSONResponse({
        "status": "healthy",
        "service": "punctuation-restorer",
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
            "service": "punctuation-restorer"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/restore")
async def restore_punctuation(data: Dict[str, Any]):
    """문장 부호 복원 엔드포인트"""
    try:
        transcriptions = data.get('transcriptions', [])
        text_data = data.get('text_data', '')
        
        if not transcriptions and not text_data:
            raise HTTPException(status_code=400, detail="transcriptions 또는 text_data가 필요합니다")
        
        logger.info(f"문장 부호 복원 시작: {len(transcriptions)}개 전사 또는 텍스트")
        
        # 문장 부호 복원 실행
        if transcriptions:
            restored_text = await restorer.restore_punctuation_async(transcriptions)
        else:
            restored_text = await restorer.restore_punctuation_text_async(text_data)
        
        logger.info("문장 부호 복원 완료")
        
        return JSONResponse({
            "status": "success",
            "restored_text": restored_text,
            "message": "문장 부호 복원이 완료되었습니다"
        })
        
    except Exception as e:
        logger.error(f"문장 부호 복원 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/restore_text")
async def restore_text_punctuation(data: Dict[str, Any]):
    """텍스트 기반 문장 부호 복원 엔드포인트"""
    try:
        text = data.get('text', '')
        if not text:
            raise HTTPException(status_code=400, detail="text가 필요합니다")
        
        logger.info(f"텍스트 문장 부호 복원 시작: {len(text)}자")
        
        # 텍스트 기반 문장 부호 복원 실행
        restored_text = await restorer.restore_punctuation_text_async(text)
        
        logger.info("텍스트 문장 부호 복원 완료")
        
        return JSONResponse({
            "status": "success",
            "original_text": text,
            "restored_text": restored_text,
            "message": "텍스트 문장 부호 복원이 완료되었습니다"
        })
        
    except Exception as e:
        logger.error(f"텍스트 문장 부호 복원 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Punctuation Restorer Service가 실행 중입니다",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "restore": "/restore",
            "restore_text": "/restore_text"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004) 