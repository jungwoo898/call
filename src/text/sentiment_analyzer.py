#!/usr/bin/env python3
"""
감정 분석 서비스
한국어 감정 분석 및 감정 변화 추적
BaseService를 상속받아 표준화된 서비스 구조 제공
"""

import time
from typing import Dict, Any
from fastapi import HTTPException
from fastapi.responses import JSONResponse

# 기본 서비스 클래스 import
from ..utils.base_service import ModelService
from ..utils.api_schemas import (
    SentimentAnalysisRequest, SentimentAnalysisResponse, SentimentResult
)

# 감정 분석 모듈 import
from .advanced_analysis import AdvancedCommunicationAnalyzer

class SentimentAnalyzerService(ModelService):
    """감정 분석 서비스 클래스"""
    
    def __init__(self):
        super().__init__(
            service_name="Sentiment-Analyzer",
            version="1.0.0",
            port=8005
        )
        
        # 감정 분석기 초기화
        self.analyzer = AdvancedCommunicationAnalyzer()
        
        # 모델 사전 로더 설정
        try:
            from .model_preloader import model_preloader
            self.model_preloader = model_preloader
        except ImportError:
            self.logger.warning("모델 사전 로더를 찾을 수 없습니다")
            self.model_preloader = None
    
    def _get_required_models(self) -> list:
        """감정 분석에 필요한 모델 목록"""
        return ['sentiment_model', 'emotion_model']
    
    async def _get_gpu_service_metrics(self) -> Dict[str, Any]:
        """감정 분석 서비스별 추가 메트릭"""
        metrics = {}
        
        if self.model_preloader:
            try:
                status = self.model_preloader.get_status()
                metrics.update({
                    "models_loaded": len([k for k, v in status.items() if v.get('loaded', False)]),
                    "total_models": len(status),
                    "sentiment_model_ready": self.model_preloader.is_ready('sentiment_model')
                })
            except Exception as e:
                self.logger.warning(f"모델 메트릭 수집 실패: {e}")
        
        return metrics
    
    def _register_service_endpoints(self):
        """감정 분석 서비스 고유 엔드포인트 등록"""
        
        @self.app.post("/analyze", response_model=SentimentAnalysisResponse)
        async def analyze_sentiment(request: SentimentAnalysisRequest):
            """감정 분석 엔드포인트"""
            start_time = time.time()
            self.log_request("/analyze", len(request.text_data))
            
            try:
                if not request.text_data:
                    raise HTTPException(status_code=400, detail="text_data가 필요합니다")
                
                self.logger.info(f"감정 분석 시작: {len(request.text_data)}자")
                
                # 감정 분석 실행
                sentiment_result = await self.analyzer.analyze_sentiment_async(request.text_data)
                
                # SentimentResult 스키마에 맞게 변환
                result = SentimentResult(
                    emotion=sentiment_result.get('emotion', 'neutral'),
                    confidence=sentiment_result.get('confidence', 0.0),
                    emotions_detail=sentiment_result.get('emotions_detail', {})
                )
                
                duration_ms = (time.time() - start_time) * 1000
                self.log_response("/analyze", True, duration_ms)
                
                self.logger.info("감정 분석 완료")
                
                return SentimentAnalysisResponse(
                    status="success",
                    message="감정 분석이 완료되었습니다",
                    data={
                        "sentiment_analysis": result,
                        "processing_time_ms": duration_ms
                    }
                )
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                self.log_response("/analyze", False, duration_ms)
                raise self.create_error_response(e, "/analyze")
        
        @self.app.post("/analyze_trend")
        async def analyze_sentiment_trend(data: Dict[str, Any]):
            """감정 변화 추이 분석 엔드포인트 (레거시 호환)"""
            start_time = time.time()
            self.log_request("/analyze_trend", len(str(data)))
            
            try:
                text_data = data.get('text_data', '')
                segments = data.get('segments', [])
                
                if not text_data and not segments:
                    raise HTTPException(
                        status_code=400, 
                        detail="text_data 또는 segments가 필요합니다"
                    )
                
                self.logger.info("감정 변화 추이 분석 시작")
                
                # 감정 변화 추이 분석 실행
                if segments:
                    trend_result = await self.analyzer.analyze_sentiment_trend_async(segments)
                else:
                    trend_result = await self.analyzer.analyze_sentiment_trend_text_async(text_data)
                
                duration_ms = (time.time() - start_time) * 1000
                self.log_response("/analyze_trend", True, duration_ms)
                
                self.logger.info("감정 변화 추이 분석 완료")
                
                return JSONResponse({
                    "status": "success",
                    "sentiment_trend": trend_result,
                    "processing_time_ms": duration_ms,
                    "message": "감정 변화 추이 분석이 완료되었습니다"
                })
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                self.log_response("/analyze_trend", False, duration_ms)
                raise self.create_error_response(e, "/analyze_trend")
        
        @self.app.post("/analyze_emotion")
        async def analyze_emotion(data: Dict[str, Any]):
            """세부 감정 분석 엔드포인트 (레거시 호환)"""
            start_time = time.time()
            self.log_request("/analyze_emotion", len(data.get('text_data', '')))
            
            try:
                text_data = data.get('text_data', '')
                if not text_data:
                    raise HTTPException(status_code=400, detail="text_data가 필요합니다")
                
                self.logger.info(f"세부 감정 분석 시작: {len(text_data)}자")
                
                # 세부 감정 분석 실행
                emotion_result = await self.analyzer.analyze_emotion_detailed_async(text_data)
                
                duration_ms = (time.time() - start_time) * 1000
                self.log_response("/analyze_emotion", True, duration_ms)
                
                self.logger.info("세부 감정 분석 완료")
                
                return JSONResponse({
                    "status": "success",
                    "emotion_analysis": emotion_result,
                    "processing_time_ms": duration_ms,
                    "message": "세부 감정 분석이 완료되었습니다"
                })
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                self.log_response("/analyze_emotion", False, duration_ms)
                raise self.create_error_response(e, "/analyze_emotion")
    
    def _get_service_endpoints(self) -> Dict[str, str]:
        """감정 분석 서비스 엔드포인트 목록"""
        return {
            "health": "/health",
            "metrics": "/metrics",
            "analyze": "/analyze",
            "analyze_trend": "/analyze_trend (레거시)",
            "analyze_emotion": "/analyze_emotion (레거시)"
        }

# 서비스 인스턴스 생성
service = SentimentAnalyzerService()
app = service.app

if __name__ == "__main__":
    service.run() 