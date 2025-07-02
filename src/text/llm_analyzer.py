#!/usr/bin/env python3
"""
LLM 분석 서비스
OpenAI/GPT 기반 상담 품질 분석 및 통찰 생성
"""

import os
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# LLM 분석 모듈 import
from .advanced_analysis import AdvancedCommunicationAnalyzer

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Analyzer Service", version="1.0.0")

# LLM 분석기 인스턴스
analyzer = AdvancedCommunicationAnalyzer()

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return JSONResponse({
        "status": "healthy",
        "service": "llm-analyzer",
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
            "service": "llm-analyzer"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_communication(data: Dict[str, Any]):
    """통신 품질 분석 엔드포인트"""
    try:
        text_data = data.get('text_data', '')
        if not text_data:
            raise HTTPException(status_code=400, detail="text_data가 필요합니다")
        
        logger.info(f"통신 품질 분석 시작: {len(text_data)}자")
        
        # 통신 품질 분석 실행
        analysis_result = await analyzer.analyze_communication_quality_async(text_data)
        
        logger.info("통신 품질 분석 완료")
        
        return JSONResponse({
            "status": "success",
            "communication_analysis": analysis_result,
            "message": "통신 품질 분석이 완료되었습니다"
        })
        
    except Exception as e:
        logger.error(f"통신 품질 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze_with_trend")
async def analyze_communication_with_trend(data: Dict[str, Any]):
    """통신 품질 분석 (추이 포함) 엔드포인트"""
    try:
        text_data = data.get('text_data', '')
        segments = data.get('segments', [])
        
        if not text_data and not segments:
            raise HTTPException(status_code=400, detail="text_data 또는 segments가 필요합니다")
        
        logger.info(f"통신 품질 분석 (추이 포함) 시작")
        
        # 통신 품질 분석 (추이 포함) 실행
        if segments:
            analysis_result = await analyzer.analyze_communication_quality_with_trend_async(segments)
        else:
            analysis_result = await analyzer.analyze_communication_quality_with_trend_text_async(text_data)
        
        logger.info("통신 품질 분석 (추이 포함) 완료")
        
        return JSONResponse({
            "status": "success",
            "communication_analysis_with_trend": analysis_result,
            "message": "통신 품질 분석 (추이 포함)이 완료되었습니다"
        })
        
    except Exception as e:
        logger.error(f"통신 품질 분석 (추이 포함) 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_insights")
async def generate_insights(data: Dict[str, Any]):
    """통찰 생성 엔드포인트"""
    try:
        text_data = data.get('text_data', '')
        analysis_data = data.get('analysis_data', {})
        
        if not text_data:
            raise HTTPException(status_code=400, detail="text_data가 필요합니다")
        
        logger.info(f"통찰 생성 시작: {len(text_data)}자")
        
        # 통찰 생성 실행
        insights = await analyzer.generate_insights_async(text_data, analysis_data)
        
        logger.info("통찰 생성 완료")
        
        return JSONResponse({
            "status": "success",
            "insights": insights,
            "message": "통찰 생성이 완료되었습니다"
        })
        
    except Exception as e:
        logger.error(f"통찰 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze_complaints")
async def analyze_complaints(data: Dict[str, Any]):
    """불만 분석 엔드포인트"""
    try:
        text_data = data.get('text_data', '')
        if not text_data:
            raise HTTPException(status_code=400, detail="text_data가 필요합니다")
        
        logger.info(f"불만 분석 시작: {len(text_data)}자")
        
        # 불만 분석 실행
        complaint_analysis = await analyzer.analyze_complaints_async(text_data)
        
        logger.info("불만 분석 완료")
        
        return JSONResponse({
            "status": "success",
            "complaint_analysis": complaint_analysis,
            "message": "불만 분석이 완료되었습니다"
        })
        
    except Exception as e:
        logger.error(f"불만 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "LLM Analyzer Service가 실행 중입니다",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "analyze": "/analyze",
            "analyze_with_trend": "/analyze_with_trend",
            "generate_insights": "/generate_insights",
            "analyze_complaints": "/analyze_complaints"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006) 