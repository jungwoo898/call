#!/usr/bin/env python3
"""
음성 인식 서비스
Whisper 기반 음성 인식 및 텍스트 변환
BaseService를 상속받아 표준화된 서비스 구조 제공
"""

import time
from typing import Dict, Any
from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import JSONResponse

# 기본 서비스 클래스 import
from ..utils.base_service import ModelService
from ..utils.api_schemas import TranscriptionRequest, TranscriptionResponse, TranscriptionResult

# 음성 인식 모듈 import
from .advanced_analysis import AdvancedAnalysisManager

class SpeechRecognizerService(ModelService):
    """음성 인식 서비스 클래스"""
    
    def __init__(self):
        super().__init__(
            service_name="Speech-Recognizer",
            version="1.0.0",
            port=8003
        )
        
        # 음성 인식기 초기화
        self.recognizer = AdvancedAnalysisManager()
        
        # 모델 사전 로더 설정
        try:
            from .model_preloader import model_preloader
            self.model_preloader = model_preloader
        except ImportError:
            self.logger.warning("모델 사전 로더를 찾을 수 없습니다")
            self.model_preloader = None
    
    def _get_required_models(self) -> list:
        """음성 인식에 필요한 모델 목록"""
        return ['whisper']
    
    async def _get_gpu_service_metrics(self) -> Dict[str, Any]:
        """음성 인식 서비스별 추가 메트릭"""
        metrics = {}
        
        if self.model_preloader:
            try:
                status = self.model_preloader.get_status()
                metrics.update({
                    "models_loaded": len([k for k, v in status.items() if v.get('loaded', False)]),
                    "total_models": len(status),
                    "whisper_ready": self.model_preloader.is_ready('whisper')
                })
            except Exception as e:
                self.logger.warning(f"모델 메트릭 수집 실패: {e}")
        
        return metrics
    
    def _register_service_endpoints(self):
        """음성 인식 서비스 고유 엔드포인트 등록"""
        
        @self.app.post("/transcribe", response_model=TranscriptionResponse)
        async def transcribe_audio(request: TranscriptionRequest):
            """음성 인식 엔드포인트"""
            start_time = time.time()
            self.log_request("/transcribe", len(str(request.model_dump())))
            
            try:
                # 입력 데이터 검증
                if not request.segments and not request.audio_path:
                    raise HTTPException(
                        status_code=400, 
                        detail="segments 또는 audio_path가 필요합니다"
                    )
                
                self.logger.info(f"음성 인식 시작: {len(request.segments or [])}개 세그먼트")
                
                # 음성 인식 실행
                if request.segments:
                    # 세그먼트 기반 인식
                    segment_data = [seg.model_dump() for seg in request.segments]
                    transcriptions = await self.recognizer.transcribe_segments_async(segment_data)
                else:
                    # 파일 기반 인식
                    transcriptions = await self.recognizer.transcribe_audio_async(request.audio_path)
                    
                    # 단일 파일 결과를 리스트 형태로 변환
                    if isinstance(transcriptions, dict):
                        transcriptions = [transcriptions]
                
                # 결과를 TranscriptionResult 스키마에 맞게 변환
                results = []
                for trans in transcriptions:
                    if isinstance(trans, dict):
                        results.append(TranscriptionResult(
                            text=trans.get('text', ''),
                            confidence=trans.get('confidence'),
                            start_time=trans.get('start_time'),
                            end_time=trans.get('end_time'),
                            speaker_id=trans.get('speaker_id')
                        ))
                    else:
                        results.append(trans)
                
                duration_ms = (time.time() - start_time) * 1000
                self.log_response("/transcribe", True, duration_ms)
                
                self.logger.info(f"음성 인식 완료: {len(results)}개 전사")
                
                return TranscriptionResponse(
                    status="success",
                    message="음성 인식이 완료되었습니다",
                    data={
                        "transcriptions": results,
                        "transcription_count": len(results),
                        "processing_time_ms": duration_ms
                    }
                )
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                self.log_response("/transcribe", False, duration_ms)
                raise self.create_error_response(e, "/transcribe")
        
        @self.app.post("/transcribe_file")
        async def transcribe_file(data: Dict[str, Any]):
            """파일 기반 음성 인식 엔드포인트 (레거시 호환)"""
            start_time = time.time()
            self.log_request("/transcribe_file", len(str(data)))
            
            try:
                audio_path = data.get('audio_path')
                if not audio_path:
                    raise HTTPException(status_code=400, detail="audio_path가 필요합니다")
                
                if not Path(audio_path).exists():
                    raise HTTPException(
                        status_code=404, 
                        detail=f"오디오 파일을 찾을 수 없습니다: {audio_path}"
                    )
                
                self.logger.info(f"파일 음성 인식 시작: {audio_path}")
                
                # 파일 기반 음성 인식 실행
                result = await self.recognizer.transcribe_audio_async(audio_path)
                
                duration_ms = (time.time() - start_time) * 1000
                self.log_response("/transcribe_file", True, duration_ms)
                
                self.logger.info(f"파일 음성 인식 완료: {audio_path}")
                
                return JSONResponse({
                    "status": "success",
                    "audio_path": audio_path,
                    "text": result.get('text', ''),
                    "segments": result.get('segments', []),
                    "processing_time_ms": duration_ms,
                    "message": "파일 음성 인식이 완료되었습니다"
                })
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                self.log_response("/transcribe_file", False, duration_ms)
                raise self.create_error_response(e, "/transcribe_file")
    
    def _get_service_endpoints(self) -> Dict[str, str]:
        """음성 인식 서비스 엔드포인트 목록"""
        return {
            "health": "/health",
            "metrics": "/metrics",
            "transcribe": "/transcribe",
            "transcribe_file": "/transcribe_file (레거시)"
        }

# 서비스 인스턴스 생성
service = SpeechRecognizerService()
app = service.app

if __name__ == "__main__":
    service.run() 