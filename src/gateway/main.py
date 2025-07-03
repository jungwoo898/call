#!/usr/bin/env python3
"""
Callytics API Gateway
마이크로서비스 오케스트레이션 전용
"""

import asyncio
import logging
import uuid
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import uvicorn

# BaseService 패턴 적용
from ..utils.base_service import BaseService
from ..utils.type_definitions import JsonDict
from ..utils.api_schemas import (
    HealthResponse,
    MetricsResponse,
    IntegratedAnalysisRequest,
    IntegratedAnalysisResponse,
    SuccessResponse,
    create_success_response,
    create_error_response
)

# 마이크로서비스 오케스트레이션
from .advanced_orchestrator import AdvancedServiceOrchestrator
from .saga_orchestrator import SagaOrchestrator, SagaStep
from .message_queue import MessageQueue

# 상담사 인증 및 업로드
from ..auth.agent_auth import AgentAuthManager
from ..upload.agent_audio_upload import AgentAudioUploadManager

# API 스키마 import
from ..utils.api_schemas import (
    HealthResponse,
    MetricsResponse,
    IntegratedAnalysisRequest,
    IntegratedAnalysisResponse,
    SuccessResponse,
    create_success_response,
    create_error_response
)

logger = logging.getLogger(__name__)

# 서비스 URL 설정
SERVICE_URLS = {
    'audio_processor': 'http://audio-processor:8001',
    'speaker_diarizer': 'http://speaker-diarizer:8002', 
    'speech_recognizer': 'http://speech-recognizer:8003',
    'punctuation_restorer': 'http://punctuation-restorer:8004',
    'sentiment_analyzer': 'http://sentiment-analyzer:8005',
    'llm_analyzer': 'http://llm-analyzer:8006',
    'database_service': 'http://database-service:8007'
}

class GatewayService(BaseService):
    """API Gateway 서비스 클래스"""
    
    def __init__(self):
        super().__init__(
            service_name="api-gateway",
            version="1.0.0", 
            description="Callytics 마이크로서비스 오케스트레이션 API Gateway"
        )
        self.orchestrator: Optional[AdvancedServiceOrchestrator] = None
        self.saga_orchestrator: Optional[SagaOrchestrator] = None
        self.message_queue: Optional[MessageQueue] = None
        self.auth_manager: Optional[AgentAuthManager] = None
        self.upload_manager: Optional[AgentAudioUploadManager] = None
        self.processing_status = {
            "is_processing": False,
            "current_file": None,
            "total_processed": 0,
            "errors": []
        }
    
    async def initialize_models(self) -> None:
        """게이트웨이 구성 요소 초기화"""
        try:
            self.logger.info("API Gateway 구성 요소 초기화 시작")
            
            # 마이크로서비스 오케스트레이터 초기화
            self.orchestrator = AdvancedServiceOrchestrator(SERVICE_URLS)
            
            # Saga 오케스트레이터 초기화
            self.saga_orchestrator = SagaOrchestrator()
            
            # 메시지 큐 초기화
            self.message_queue = MessageQueue()
            
            # 상담사 인증 관리자 초기화
            self.auth_manager = AgentAuthManager()
            
            # 오디오 업로드 관리자 초기화
            self.upload_manager = AgentAudioUploadManager()
            
            self.model_ready = True
            self.logger.info("API Gateway 구성 요소 초기화 완료")
        except Exception as e:
            self.logger.error(f"게이트웨이 초기화 실패: {e}")
            self.model_ready = False
            raise e
    
    async def cleanup_models(self) -> None:
        """게이트웨이 구성 요소 정리"""
        try:
            self.logger.info("API Gateway 구성 요소 정리 시작")
            
            if self.orchestrator:
                await self.orchestrator.close()
                self.orchestrator = None
            
            # 다른 구성 요소들도 필요시 정리
            self.saga_orchestrator = None
            self.message_queue = None
            self.auth_manager = None
            self.upload_manager = None
            
            self.logger.info("API Gateway 구성 요소 정리 완료")
        except Exception as e:
            self.logger.error(f"게이트웨이 정리 실패: {e}")
    
    def gateway_get_custom_metrics(self) -> JsonDict:
        """커스텀 메트릭 반환"""
        return {
            "orchestrator_ready": self.orchestrator is not None,
            "saga_orchestrator_ready": self.saga_orchestrator is not None,
            "message_queue_ready": self.message_queue is not None,
            "auth_manager_ready": self.auth_manager is not None,
            "upload_manager_ready": self.upload_manager is not None,
            "connected_services": list(SERVICE_URLS.keys()),
            "processing_status": self.processing_status,
            "gateway_features": [
                "service_orchestration",
                "saga_pattern",
                "message_queue",
                "agent_authentication",
                "file_upload",
                "cors_support"
            ]
        }

# 서비스 인스턴스 생성
service = GatewayService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    await service.startup()
    yield
    await service.shutdown()

app = service.create_app(lifespan=lifespan)

# 🌐 CORS 설정 추가 (브라우저 호출 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # React 개발 서버
        "http://localhost:3001",    # Vue 개발 서버  
        "http://localhost:8000",    # API Gateway
        "http://localhost:8080",    # 일반적인 개발 서버
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001", 
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

async def save_uploaded_file(upload_file: UploadFile) -> str:
    """업로드된 파일 저장"""
    file_path = Path("audio") / f"{uuid.uuid4()}_{upload_file.filename}"
    file_path.parent.mkdir(exist_ok=True)
    
    with open(file_path, "wb") as buffer:
        content = await upload_file.read()
        buffer.write(content)
    
    return str(file_path)

async def create_audio_processing_saga(audio_file_path: str) -> list:
    """오디오 처리 Saga 단계 생성"""
    
    async def audio_preprocess(data: Dict[str, Any]) -> Dict[str, Any]:
        """오디오 전처리"""
        result = await service.orchestrator.call_service_with_retry(
            'audio_processor', '/preprocess', {'audio_path': data['audio_path']}
        )
        return {'preprocessed_audio': result}
    
    async def speaker_diarize(data: Dict[str, Any]) -> Dict[str, Any]:
        """화자 분리"""
        result = await service.orchestrator.call_service_with_retry(
            'speaker_diarizer', '/diarize', 
            {'audio_path': data['preprocessed_audio']['processed_path']}
        )
        return {'speaker_segments': result}
    
    async def speech_transcribe(data: Dict[str, Any]) -> Dict[str, Any]:
        """음성 인식"""
        result = await service.orchestrator.call_service_with_retry(
            'speech_recognizer', '/transcribe', 
            {'segments': data['speaker_segments']['segments']}
        )
        return {'transcriptions': result}
    
    async def punctuation_restore(data: Dict[str, Any]) -> Dict[str, Any]:
        """문장 부호 복원"""
        result = await service.orchestrator.call_service_with_retry(
            'punctuation_restorer', '/restore', 
            {'transcriptions': data['transcriptions']['transcriptions']}
        )
        return {'punctuated_text': result}
    
    async def sentiment_analyze(data: Dict[str, Any]) -> Dict[str, Any]:
        """감정 분석"""
        result = await service.orchestrator.call_service_with_retry(
            'sentiment_analyzer', '/analyze', 
            {'text_data': data['punctuated_text']['restored_text']}
        )
        return {'sentiment_analysis': result}
    
    async def llm_analyze(data: Dict[str, Any]) -> Dict[str, Any]:
        """LLM 분석"""
        result = await service.orchestrator.call_service_with_retry(
            'llm_analyzer', '/analyze', 
            {'text_data': data['punctuated_text']['restored_text']}
        )
        return {'llm_analysis': result}
    
    async def save_results(data: Dict[str, Any]) -> Dict[str, Any]:
        """결과 저장"""
        final_result = {
            'audio_path': data['audio_path'],
            'speaker_segments': data['speaker_segments'],
            'transcriptions': data['transcriptions'],
            'punctuated_text': data['punctuated_text'],
            'sentiment_analysis': data['sentiment_analysis'],
            'llm_analysis': data['llm_analysis'],
            'processing_timestamp': asyncio.get_event_loop().time()
        }
        
        await service.orchestrator.call_service_with_retry(
            'database_service', '/save_result', {'result': final_result}
        )
        return {'final_result': final_result}
    
    # 보상 함수들 (롤백 처리)
    async def compensate_audio_preprocess(data: Dict[str, Any]):
        """오디오 전처리 보상"""
        service.logger.info("오디오 전처리 보상 처리")
    
    async def compensate_speaker_diarize(data: Dict[str, Any]):
        """화자 분리 보상"""
        service.logger.info("화자 분리 보상 처리")
    
    async def compensate_speech_transcribe(data: Dict[str, Any]):
        """음성 인식 보상"""
        service.logger.info("음성 인식 보상 처리")
    
    async def compensate_punctuation_restore(data: Dict[str, Any]):
        """문장 부호 복원 보상"""
        service.logger.info("문장 부호 복원 보상 처리")
    
    async def compensate_sentiment_analyze(data: Dict[str, Any]):
        """감정 분석 보상"""
        service.logger.info("감정 분석 보상 처리")
    
    async def compensate_llm_analyze(data: Dict[str, Any]):
        """LLM 분석 보상"""
        service.logger.info("LLM 분석 보상 처리")
    
    async def compensate_save_results(data: Dict[str, Any]):
        """결과 저장 보상"""
        service.logger.info("결과 저장 보상 처리")
    
    # Saga 단계 정의
    return [
        SagaStep("audio_preprocess", audio_preprocess, compensate_audio_preprocess),
        SagaStep("speaker_diarize", speaker_diarize, compensate_speaker_diarize),
        SagaStep("speech_transcribe", speech_transcribe, compensate_speech_transcribe),
        SagaStep("punctuation_restore", punctuation_restore, compensate_punctuation_restore),
        SagaStep("sentiment_analyze", sentiment_analyze, compensate_sentiment_analyze),
        SagaStep("llm_analyze", llm_analyze, compensate_llm_analyze),
        SagaStep("save_results", save_results, compensate_save_results)
    ]

@app.get("/health", response_model=SuccessResponse)
async def health_check() -> SuccessResponse:
    """헬스체크 엔드포인트"""
    try:
        # 모든 서비스 헬스체크
        service_health = await service.orchestrator.get_service_health()
        
        # 전체 상태 결정
        all_healthy = all(
            status['status'] == 'healthy' 
            for status in service_health.values()
        )
        status = "healthy" if all_healthy else "degraded"
        
        # 빠른 분석기 상태 추가
        from ..text.fast_analyzer import fast_analyzer
        fast_analyzer_status = fast_analyzer.get_status()
        
        return SuccessResponse(
            status="success",
            message=f"Gateway 상태: {status}",
            data={
                "gateway_status": status,
                "gateway": "healthy",
                "services": service_health,
                "processing_status": service.processing_status,
                "fast_analyzer": fast_analyzer_status,
                "ready_for_fast_analysis": fast_analyzer_status["ready"]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics", response_model=SuccessResponse)
async def get_metrics() -> SuccessResponse:
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
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        service_metrics[service_name] = response.json()
            except:
                service_metrics[service_name] = {"status": "unavailable"}
        
        return SuccessResponse(
            status="success",
            message="메트릭 수집 완료",
            data={
                "gateway": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / 1024**3,
                },
                "services": service_metrics,
                "processing_status": service.processing_status
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload_audio", response_model=SuccessResponse)
async def upload_audio(file: UploadFile = File(...)) -> SuccessResponse:
    """오디오 파일 업로드 엔드포인트"""
    try:
        if not service.model_ready:
            raise HTTPException(status_code=503, detail="게이트웨이가 준비되지 않았습니다")
        
        service.logger.info(f"오디오 파일 업로드: {file.filename}")
        
        # 파일 저장
        file_path = await save_uploaded_file(file)
        
        service.logger.info(f"오디오 파일 업로드 완료: {file_path}")
        
        return SuccessResponse(
            status="success",
            message="오디오 파일이 업로드되었습니다",
            data={
                "filename": file.filename,
                "file_path": file_path,
                "file_size": file.size
            }
        )
        
    except Exception as e:
        service.logger.error(f"오디오 파일 업로드 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process_audio_fast", response_model=IntegratedAnalysisResponse) 
async def process_audio_fast(request: IntegratedAnalysisRequest) -> IntegratedAnalysisResponse:
    """빠른 오디오 처리 (동기식)"""
    try:
        if not service.model_ready:
            raise HTTPException(status_code=503, detail="게이트웨이가 준비되지 않았습니다")
        
        service.logger.info(f"빠른 오디오 처리 시작: {request.audio_path}")
        
        start_time = time.time()
        
        # Saga 단계 생성 및 실행
        saga_steps = await create_audio_processing_saga(request.audio_path)
        saga_id = await service.saga_orchestrator.execute_saga(
            saga_steps, 
            {'audio_path': request.audio_path}
        )
        
        # Saga 완료 대기
        saga_result = await service.saga_orchestrator.wait_for_completion(saga_id)
        
        processing_time = time.time() - start_time
        
        service.logger.info(f"빠른 오디오 처리 완료: {request.audio_path}")
        
        return IntegratedAnalysisResponse(
            status="success",
            message="빠른 오디오 처리가 완료되었습니다",
            data={
                "saga_id": saga_id,
                "processing_time": processing_time,
                "saga_result": saga_result
            },
            final_result=saga_result['final_result']
        )
        
    except Exception as e:
        service.logger.error(f"빠른 오디오 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process_audio", response_model=IntegratedAnalysisResponse)
async def process_audio(request: IntegratedAnalysisRequest, background_tasks: BackgroundTasks) -> IntegratedAnalysisResponse:
    """전체 오디오 처리 (비동기식)"""
    try:
        if not service.model_ready:
            raise HTTPException(status_code=503, detail="게이트웨이가 준비되지 않았습니다")
        
        service.logger.info(f"전체 오디오 처리 시작: {request.audio_path}")
        
        # 처리 상태 업데이트
        service.processing_status["is_processing"] = True
        service.processing_status["current_file"] = request.audio_path
        
        # 백그라운드에서 Saga 실행
        saga_steps = await create_audio_processing_saga(request.audio_path)
        saga_id = await service.saga_orchestrator.execute_saga_async(
            saga_steps, 
            {'audio_path': request.audio_path}
        )
        
        return IntegratedAnalysisResponse(
            status="processing",
            message="오디오 처리가 시작되었습니다",
            data={
                "saga_id": saga_id,
                "audio_path": request.audio_path,
                "processing_status": "started"
            },
            final_result=None  # 비동기 처리이므로 결과는 나중에 조회
        )
        
    except Exception as e:
        service.logger.error(f"전체 오디오 처리 실패: {e}")
        service.processing_status["is_processing"] = False
        service.processing_status["errors"].append(str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status", response_model=SuccessResponse)
async def get_processing_status() -> SuccessResponse:
    """처리 상태 조회"""
    return SuccessResponse(
        status="success",
        message="처리 상태 조회 완료",
        data=service.processing_status
    )

@app.get("/saga/{saga_id}", response_model=SuccessResponse)
async def get_saga_status(saga_id: str) -> SuccessResponse:
    """Saga 상태 조회"""
    try:
        if not service.model_ready:
            raise HTTPException(status_code=503, detail="게이트웨이가 준비되지 않았습니다")
        
        saga_status = await service.saga_orchestrator.get_saga_status(saga_id)
        
        return SuccessResponse(
            status="success",
            message=f"Saga 상태 조회 완료: {saga_id}",
            data=saga_status
        )
        
    except Exception as e:
        service.logger.error(f"Saga 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/queue/stats", response_model=SuccessResponse)
async def get_queue_stats() -> SuccessResponse:
    """메시지 큐 통계 조회"""
    try:
        if not service.model_ready:
            raise HTTPException(status_code=503, detail="게이트웨이가 준비되지 않았습니다")
        
        queue_stats = await service.message_queue.get_stats()
        
        return SuccessResponse(
            status="success",
            message="메시지 큐 통계 조회 완료",
            data=queue_stats
        )
        
    except Exception as e:
        service.logger.error(f"메시지 큐 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_model=SuccessResponse)
async def root() -> SuccessResponse:
    """루트 엔드포인트"""
    return SuccessResponse(
        status="success",
        message="Callytics API Gateway가 실행 중입니다",
        data={
            "version": "1.0.0",
            "architecture": "microservices",
            "services": list(SERVICE_URLS.keys()),
            "endpoints": {
                "health": "/health",
                "metrics": "/metrics",
                "upload_audio": "/upload_audio",
                "process_audio": "/process_audio",
                "process_audio_fast": "/process_audio_fast",  # 🚀 빠른 분석
                "status": "/status",
                "saga_status": "/saga/{saga_id}",
                "queue_stats": "/queue/stats",
                "docs": "/docs"
            }
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 