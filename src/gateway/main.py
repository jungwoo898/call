#!/usr/bin/env python3
"""
Callytics API Gateway
마이크로서비스 오케스트레이션 및 통합 분석기 연동
"""

import asyncio
import logging
import uuid
import time
from pathlib import Path
from typing import Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
import httpx

# 마이크로서비스 오케스트레이션
from .advanced_orchestrator import AdvancedServiceOrchestrator
from .saga_orchestrator import SagaOrchestrator, SagaStep
from .message_queue import MessageQueue

# 통합 분석기 (단일 컨테이너 모드용)
from ..integrated_analyzer_advanced import AdvancedIntegratedAnalyzer

# 상담사 인증 및 업로드
from ..auth.agent_auth import AgentAuthManager
from ..upload.agent_audio_upload import AgentAudioUploadManager

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

# 처리 상태 관리
processing_status = {
    "is_processing": False,
    "current_file": None,
    "total_processed": 0,
    "errors": []
}

# 통합 분석기 인스턴스 (단일 컨테이너 모드용)
integrated_analyzer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 초기화
    logger.info("🚀 Callytics API Gateway 시작")
    
    # 마이크로서비스 오케스트레이터 초기화
    app.state.orchestrator = AdvancedServiceOrchestrator(SERVICE_URLS)
    
    # Saga 오케스트레이터 초기화
    app.state.saga_orchestrator = SagaOrchestrator()
    
    # 메시지 큐 초기화
    app.state.message_queue = MessageQueue()
    
    # 통합 분석기 초기화 (단일 컨테이너 모드용)
    global integrated_analyzer
    integrated_analyzer = AdvancedIntegratedAnalyzer(
        enable_cache=True,
        enable_parallel=True,
        enable_async=True,
        max_workers=4
    )
    
    # 상담사 인증 관리자 초기화
    app.state.auth_manager = AgentAuthManager()
    
    # 오디오 업로드 관리자 초기화
    app.state.upload_manager = AgentAudioUploadManager()
    
    yield
    
    # 종료 시 정리
    logger.info("🛑 Callytics API Gateway 종료")
    await app.state.orchestrator.close()
    if integrated_analyzer:
        integrated_analyzer.cleanup()

app = FastAPI(lifespan=lifespan)

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
        result = await app.state.orchestrator.call_service_with_retry(
            'audio_processor', '/preprocess', {'audio_path': data['audio_path']}
        )
        return {'preprocessed_audio': result}
    
    async def speaker_diarize(data: Dict[str, Any]) -> Dict[str, Any]:
        """화자 분리"""
        result = await app.state.orchestrator.call_service_with_retry(
            'speaker_diarizer', '/diarize', 
            {'audio_path': data['preprocessed_audio']['processed_path']}
        )
        return {'speaker_segments': result}
    
    async def speech_transcribe(data: Dict[str, Any]) -> Dict[str, Any]:
        """음성 인식"""
        result = await app.state.orchestrator.call_service_with_retry(
            'speech_recognizer', '/transcribe', 
            {'segments': data['speaker_segments']['segments']}
        )
        return {'transcriptions': result}
    
    async def punctuation_restore(data: Dict[str, Any]) -> Dict[str, Any]:
        """문장 부호 복원"""
        result = await app.state.orchestrator.call_service_with_retry(
            'punctuation_restorer', '/restore', 
            {'transcriptions': data['transcriptions']['transcriptions']}
        )
        return {'punctuated_text': result}
    
    async def sentiment_analyze(data: Dict[str, Any]) -> Dict[str, Any]:
        """감정 분석"""
        result = await app.state.orchestrator.call_service_with_retry(
            'sentiment_analyzer', '/analyze', 
            {'text_data': data['punctuated_text']['restored_text']}
        )
        return {'sentiment_analysis': result}
    
    async def llm_analyze(data: Dict[str, Any]) -> Dict[str, Any]:
        """LLM 분석"""
        result = await app.state.orchestrator.call_service_with_retry(
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
        
        await app.state.orchestrator.call_service_with_retry(
            'database_service', '/save_result', {'result': final_result}
        )
        return {'final_result': final_result}
    
    # 보상 함수들 (롤백 처리)
    async def compensate_audio_preprocess(data: Dict[str, Any]):
        """오디오 전처리 보상"""
        logger.info("오디오 전처리 보상 처리")
    
    async def compensate_speaker_diarize(data: Dict[str, Any]):
        """화자 분리 보상"""
        logger.info("화자 분리 보상 처리")
    
    async def compensate_speech_transcribe(data: Dict[str, Any]):
        """음성 인식 보상"""
        logger.info("음성 인식 보상 처리")
    
    async def compensate_punctuation_restore(data: Dict[str, Any]):
        """문장 부호 복원 보상"""
        logger.info("문장 부호 복원 보상 처리")
    
    async def compensate_sentiment_analyze(data: Dict[str, Any]):
        """감정 분석 보상"""
        logger.info("감정 분석 보상 처리")
    
    async def compensate_llm_analyze(data: Dict[str, Any]):
        """LLM 분석 보상"""
        logger.info("LLM 분석 보상 처리")
    
    async def compensate_save_results(data: Dict[str, Any]):
        """결과 저장 보상"""
        logger.info("결과 저장 보상 처리")
    
    return [
        SagaStep("audio_preprocess", audio_preprocess, compensate_audio_preprocess),
        SagaStep("speaker_diarize", speaker_diarize, compensate_speaker_diarize),
        SagaStep("speech_transcribe", speech_transcribe, compensate_speech_transcribe),
        SagaStep("punctuation_restore", punctuation_restore, compensate_punctuation_restore),
        SagaStep("sentiment_analyze", sentiment_analyze, compensate_sentiment_analyze),
        SagaStep("llm_analyze", llm_analyze, compensate_llm_analyze),
        SagaStep("save_results", save_results, compensate_save_results),
    ]

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    try:
        # 모든 서비스 헬스체크
        service_health = await app.state.orchestrator.get_service_health()
        
        # 전체 상태 결정
        all_healthy = all(
            status['status'] == 'healthy' 
            for status in service_health.values()
        )
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
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url)
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

@app.post("/upload_audio")
async def upload_audio(file: UploadFile = File(...)):
    """오디오 파일 업로드 및 처리"""
    try:
        if processing_status["is_processing"]:
            raise HTTPException(status_code=409, detail="이미 처리 중인 파일이 있습니다")
        
        # 파일 저장
        audio_file_path = await save_uploaded_file(file)
        
        # 메시지 큐에 작업 추가
        message_id = await app.state.message_queue.publish(
            "audio_processing", 
            {"audio_path": audio_file_path, "filename": file.filename},
            priority=1
        )
        
        return JSONResponse({
            "message": "오디오 파일이 업로드되었습니다",
            "file_id": Path(audio_file_path).stem,
            "message_id": message_id,
            "status": "queued"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process_audio")
async def process_audio(audio_file_path: str, background_tasks: BackgroundTasks):
    """오디오 파일 처리 엔드포인트 (Saga 패턴 사용)"""
    try:
        if processing_status["is_processing"]:
            raise HTTPException(status_code=409, detail="이미 처리 중인 파일이 있습니다")
        
        processing_status["is_processing"] = True
        processing_status["current_file"] = audio_file_path
        
        # Saga 단계 생성
        saga_steps = await create_audio_processing_saga(audio_file_path)
        
        # Saga 실행
        saga_id = f"saga_{uuid.uuid4()}"
        result = await app.state.saga_orchestrator.execute_saga(
            saga_id, saga_steps, {"audio_path": audio_file_path}
        )
        
        processing_status["total_processed"] += 1
        
        return JSONResponse({
            "message": "오디오 처리가 완료되었습니다",
            "saga_id": saga_id,
            "result": result
        })
    except Exception as e:
        error_msg = f"파이프라인 처리 중 오류: {e}"
        logger.error(error_msg)
        processing_status["errors"].append(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    finally:
        processing_status["is_processing"] = False
        processing_status["current_file"] = None

@app.post("/process_audio_integrated")
async def process_audio_integrated(audio_file_path: str):
    """통합 분석기로 오디오 처리 (단일 컨테이너 모드)"""
    try:
        if processing_status["is_processing"]:
            raise HTTPException(status_code=409, detail="이미 처리 중인 파일이 있습니다")
        
        processing_status["is_processing"] = True
        processing_status["current_file"] = audio_file_path
        
        # 통합 분석기로 처리
        if integrated_analyzer:
            result = await integrated_analyzer.analyze_audio_comprehensive(audio_file_path)
            processing_status["total_processed"] += 1
            
            return JSONResponse({
                "message": "통합 분석이 완료되었습니다",
                "result": result
            })
        else:
            raise HTTPException(status_code=500, detail="통합 분석기가 초기화되지 않았습니다")
            
    except Exception as e:
        error_msg = f"통합 분석 중 오류: {e}"
        logger.error(error_msg)
        processing_status["errors"].append(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    finally:
        processing_status["is_processing"] = False
        processing_status["current_file"] = None

@app.get("/status")
async def get_processing_status():
    """처리 상태 조회"""
    return JSONResponse(processing_status)

@app.get("/saga/{saga_id}")
async def get_saga_status(saga_id: str):
    """Saga 상태 조회"""
    status = app.state.saga_orchestrator.get_saga_status(saga_id)
    if not status:
        raise HTTPException(status_code=404, detail="Saga를 찾을 수 없습니다")
    return JSONResponse(status)

@app.get("/queue/stats")
async def get_queue_stats():
    """메시지 큐 통계"""
    try:
        stats = {}
        for topic in ["audio_processing"]:
            stats[topic] = await app.state.message_queue.get_queue_stats(topic)
        return JSONResponse(stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Callytics API Gateway가 실행 중입니다",
        "version": "1.0.0",
        "architecture": "microservices + integrated",
        "services": list(SERVICE_URLS.keys()),
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "upload_audio": "/upload_audio",
            "process_audio": "/process_audio",
            "process_audio_integrated": "/process_audio_integrated",
            "status": "/status",
            "saga_status": "/saga/{saga_id}",
            "queue_stats": "/queue/stats",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 