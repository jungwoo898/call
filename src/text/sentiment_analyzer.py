#!/usr/bin/env python3
"""
감정 분석 서비스
한국어 감정 분석 및 감정 변화 추적
"""

import os
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# 감정 분석 모듈 import
from .advanced_analysis import AdvancedCommunicationAnalyzer

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Sentiment Analyzer Service", version="1.0.0")

# 감정 분석기 인스턴스
analyzer = AdvancedCommunicationAnalyzer()

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return JSONResponse({
        "status": "healthy",
        "service": "sentiment-analyzer",
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
            "service": "sentiment-analyzer"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_sentiment(data: Dict[str, Any]):
    """감정 분석 엔드포인트"""
    try:
        text_data = data.get('text_data', '')
        if not text_data:
            raise HTTPException(status_code=400, detail="text_data가 필요합니다")
        
        logger.info(f"감정 분석 시작: {len(text_data)}자")
        
        # 감정 분석 실행
        sentiment_result = await analyzer.analyze_sentiment_async(text_data)
        
        logger.info("감정 분석 완료")
        
        return JSONResponse({
            "status": "success",
            "sentiment_analysis": sentiment_result,
            "message": "감정 분석이 완료되었습니다"
        })
        
    except Exception as e:
        logger.error(f"감정 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze_trend")
async def analyze_sentiment_trend(data: Dict[str, Any]):
    """감정 변화 추이 분석 엔드포인트"""
    try:
        text_data = data.get('text_data', '')
        segments = data.get('segments', [])
        
        if not text_data and not segments:
            raise HTTPException(status_code=400, detail="text_data 또는 segments가 필요합니다")
        
        logger.info(f"감정 변화 추이 분석 시작")
        
        # 감정 변화 추이 분석 실행
        if segments:
            trend_result = await analyzer.analyze_sentiment_trend_async(segments)
        else:
            trend_result = await analyzer.analyze_sentiment_trend_text_async(text_data)
        
        logger.info("감정 변화 추이 분석 완료")
        
        return JSONResponse({
            "status": "success",
            "sentiment_trend": trend_result,
            "message": "감정 변화 추이 분석이 완료되었습니다"
        })
        
    except Exception as e:
        logger.error(f"감정 변화 추이 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze_emotion")
async def analyze_emotion(data: Dict[str, Any]):
    """세부 감정 분석 엔드포인트"""
    try:
        text_data = data.get('text_data', '')
        if not text_data:
            raise HTTPException(status_code=400, detail="text_data가 필요합니다")
        
        logger.info(f"세부 감정 분석 시작: {len(text_data)}자")
        
        # 세부 감정 분석 실행
        emotion_result = await analyzer.analyze_emotion_detailed_async(text_data)
        
        logger.info("세부 감정 분석 완료")
        
        return JSONResponse({
            "status": "success",
            "emotion_analysis": emotion_result,
            "message": "세부 감정 분석이 완료되었습니다"
        })
        
    except Exception as e:
        logger.error(f"세부 감정 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Sentiment Analyzer Service가 실행 중입니다",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "analyze": "/analyze",
            "analyze_trend": "/analyze_trend",
            "analyze_emotion": "/analyze_emotion"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005) 