#!/usr/bin/env python3
"""
Callytics API Gateway
마이크로서비스 간 요청 라우팅 및 오케스트레이션
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn
import httpx
from contextlib import asynccontextmanager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 서비스 URL 환경 변수
SERVICE_URLS = {
    'audio_processor': os.getenv('AUDIO_PROCESSOR_URL', 'http://audio-processor:8001'),
    'speaker_diarizer': os.getenv('SPEAKER_DIARIZER_URL', 'http://speaker-diarizer:8002'),
    'speech_recognizer': os.getenv('SPEECH_RECOGNIZER_URL', 'http://speech-recognizer:8003'),
    'punctuation_restorer': os.getenv('PUNCTUATION_RESTORER_URL', 'http://punctuation-restorer:8004'),
    'sentiment_analyzer': os.getenv('SENTIMENT_ANALYZER_URL', 'http://sentiment-analyzer:8005'),
    'llm_analyzer': os.getenv('LLM_ANALYZER_URL', 'http://llm-analyzer:8006'),
    'database_service': os.getenv('DATABASE_SERVICE_URL', 'http://database-service:8007'),
}

# 전역 변수로 처리 상태 관리
processing_status = {
    "is_processing": False,
    "current_file": None,
    "total_processed": 0,
    "errors": []
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    logger.info("🚀 Callytics API Gateway 시작")
    yield
    logger.info("🛑 Callytics API Gateway 종료")

app = FastAPI(title="Callytics API Gateway", version="1.0.0", lifespan=lifespan)

class ServiceOrchestrator:
    """서비스 오케스트레이터"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=300.0)  # 5분 타임아웃
    
    async def check_service_health(self, service_name: str) -> bool:
        """서비스 헬스체크"""
        try:
            url = f"{SERVICE_URLS[service_name]}/health"
            response = await self.client.get(url)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"서비스 {service_name} 헬스체크 실패: {e}")
            return False
    
    async def process_audio_pipeline(self, audio_file_path: str) -> Dict[str, Any]:
        """전체 오디오 처리 파이프라인"""
        try:
            processing_status["is_processing"] = True
            processing_status["current_file"] = audio_file_path
            
            logger.info(f"오디오 처리 파이프라인 시작: {audio_file_path}")
            
            # 1. 오디오 전처리
            logger.info("1단계: 오디오 전처리")
            preprocessed_audio = await self._call_service(
                'audio_processor', 
                '/preprocess', 
                {'audio_path': audio_file_path}
            )
            
            # 2. 화자 분리
            logger.info("2단계: 화자 분리")
            speaker_segments = await self._call_service(
                'speaker_diarizer', 
                '/diarize', 
                {'audio_path': preprocessed_audio['processed_path']}
            )
            
            # 3. 음성 인식
            logger.info("3단계: 음성 인식")
            transcriptions = await self._call_service(
                'speech_recognizer', 
                '/transcribe', 
                {'segments': speaker_segments['segments']}
            )
            
            # 4. 문장 부호 복원
            logger.info("4단계: 문장 부호 복원")
            punctuated_text = await self._call_service(
                'punctuation_restorer', 
                '/restore', 
                {'transcriptions': transcriptions['transcriptions']}
            )
            
            # 5. 감정 분석
            logger.info("5단계: 감정 분석")
            sentiment_results = await self._call_service(
                'sentiment_analyzer', 
                '/analyze', 
                {'text_data': punctuated_text['restored_text']}
            )
            
            # 6. LLM 분석
            logger.info("6단계: LLM 분석")
            llm_results = await self._call_service(
                'llm_analyzer', 
                '/analyze', 
                {'text_data': punctuated_text['restored_text']}
            )
            
            # 7. 결과 통합 및 저장
            logger.info("7단계: 결과 저장")
            final_result = {
                'audio_path': audio_file_path,
                'speaker_segments': speaker_segments,
                'transcriptions': transcriptions,
                'punctuated_text': punctuated_text,
                'sentiment_analysis': sentiment_results,
                'llm_analysis': llm_results,
                'processing_timestamp': asyncio.get_event_loop().time()
            }
            
            # 데이터베이스에 저장
            await self._call_service(
                'database_service', 
                '/save_result', 
                {'result': final_result}
            )
            
            processing_status["total_processed"] += 1
            logger.info("오디오 처리 파이프라인 완료")
            
            return final_result
            
        except Exception as e:
            error_msg = f"파이프라인 처리 중 오류: {e}"
            logger.error(error_msg)
            processing_status["errors"].append(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
        finally:
            processing_status["is_processing"] = False
            processing_status["current_file"] = None
    
    async def _call_service(self, service_name: str, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """서비스 호출"""
        try:
            url = f"{SERVICE_URLS[service_name]}{endpoint}"
            logger.info(f"서비스 호출: {service_name} -> {endpoint}")
            
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"서비스 {service_name} HTTP 오류: {e.response.status_code}")
            raise HTTPException(status_code=e.response.status_code, detail=f"서비스 {service_name} 오류")
        except Exception as e:
            logger.error(f"서비스 {service_name} 호출 실패: {e}")
            raise HTTPException(status_code=500, detail=f"서비스 {service_name} 연결 실패")

# 오케스트레이터 인스턴스
orchestrator = ServiceOrchestrator()

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    try:
        # 모든 서비스 헬스체크
        service_health = {}
        for service_name in SERVICE_URLS.keys():
            service_health[service_name] = await orchestrator.check_service_health(service_name)
        
        # 전체 상태 결정
        all_healthy = all(service_health.values())
        status = "healthy" if all_healthy else "degraded"
        
        return JSONResponse({
            "status": status,
            "gateway": "healthy",
            "services": service_health,
            "processing_status": processing_status
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
        
        # 시스템 메트릭
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # 서비스별 메트릭 수집
        service_metrics = {}
        for service_name in SERVICE_URLS.keys():
            try:
                url = f"{SERVICE_URLS[service_name]}/metrics"
                response = await orchestrator.client.get(url)
                if response.status_code == 200:
                    service_metrics[service_name] = response.json()
            except:
                service_metrics[service_name] = {"status": "unavailable"}
        
        return JSONResponse({
            "gateway": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / 1024**3,
            },
            "services": service_metrics,
            "processing_status": processing_status
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process_audio")
async def process_audio(audio_file_path: str, background_tasks: BackgroundTasks):
    """오디오 파일 처리 엔드포인트"""
    try:
        if processing_status["is_processing"]:
            raise HTTPException(status_code=409, detail="이미 처리 중인 파일이 있습니다")
        
        # 백그라운드에서 처리
        background_tasks.add_task(orchestrator.process_audio_pipeline, audio_file_path)
        
        return JSONResponse({
            "message": "오디오 처리가 시작되었습니다",
            "audio_file": audio_file_path,
            "status": "processing"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_processing_status():
    """처리 상태 조회"""
    return JSONResponse(processing_status)

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Callytics API Gateway가 실행 중입니다",
        "version": "1.0.0",
        "services": list(SERVICE_URLS.keys()),
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "process_audio": "/process_audio",
            "status": "/status",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 