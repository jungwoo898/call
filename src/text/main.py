#!/usr/bin/env python3
"""
화자 분리 서비스
NeMo 기반 화자 분리 및 세그먼트 생성
"""

import time
from typing import Optional
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import HTTPException
import uvicorn

# BaseService 패턴 적용
from ..utils.base_service import GPUService
from ..utils.type_definitions import JsonDict
from ..utils.api_schemas import (
    HealthResponse,
    MetricsResponse,
    SpeakerDiarizationRequest,
    SpeakerDiarizationResponse,
    SpeakerSegment,
    SuccessResponse,
    create_success_response,
    create_error_response
)

# 화자 분리 모듈 import
from .advanced_analysis import AdvancedCommunicationAnalyzer

class SpeakerDiarizerService(GPUService):
    """화자 분리 서비스 클래스"""
    
    def __init__(self):
        super().__init__(
            service_name="speaker-diarizer",
            version="1.0.0",
            description="NeMo 기반 화자 분리 및 세그먼트 생성 서비스"
        )
        self.diarizer: Optional[AdvancedCommunicationAnalyzer] = None
    
    async def initialize_models(self) -> None:
        """모델 초기화"""
        try:
            self.logger.info("화자 분리 모델 초기화 시작")
            self.diarizer = AdvancedCommunicationAnalyzer()
            self.model_ready = True
            self.logger.info("화자 분리 모델 초기화 완료")
        except Exception as e:
            self.logger.error(f"모델 초기화 실패: {e}")
            self.model_ready = False
            raise e
    
    async def cleanup_models(self) -> None:
        """모델 정리"""
        if self.diarizer:
            self.logger.info("화자 분리 모델 정리")
            # 필요시 모델 정리 로직 추가
            self.diarizer = None
    
    def text_get_custom_metrics(self) -> JsonDict:
        """커스텀 메트릭 반환"""
        return {
            "model_loaded": self.diarizer is not None,
            "model_type": "speaker_diarizer",
            "supported_formats": ["wav", "mp3", "flac"],
            "diarization_features": [
                "speaker_identification",
                "segment_extraction",
                "speaker_analysis",
                "multi_speaker_support"
            ]
        }

# 서비스 인스턴스 생성
service = SpeakerDiarizerService()

@asynccontextmanager
async def lifespan(app):
    """애플리케이션 생명주기 관리"""
    await service.startup()
    yield
    await service.shutdown()

# FastAPI 앱 생성
app = service.create_app(lifespan=lifespan)

@app.post("/diarize", response_model=SpeakerDiarizationResponse)
async def diarize_speakers(request: SpeakerDiarizationRequest) -> SpeakerDiarizationResponse:
    """화자 분리 엔드포인트"""
    try:
        if not service.model_ready:
            raise HTTPException(status_code=503, detail="모델이 준비되지 않았습니다")
        
        if not Path(request.audio_path).exists():
            raise HTTPException(status_code=404, detail=f"오디오 파일을 찾을 수 없습니다: {request.audio_path}")
        
        service.logger.info(f"화자 분리 시작: {request.audio_path}")
        
        # 화자 분리 실행
        start_time = time.time()
        segment_data = await service.diarizer.diarize_speakers_async(request.audio_path)
        processing_time = time.time() - start_time
        
        # 세그먼트 데이터를 SpeakerSegment 객체로 변환
        segments = [
            SpeakerSegment(
                speaker_id=seg.get("speaker_id", f"speaker_{i}"),
                start_time=seg.get("start_time", 0.0),
                end_time=seg.get("end_time", 0.0),
                confidence=seg.get("confidence", 0.0)
            )
            for i, seg in enumerate(segment_data)
        ]
        
        # 전체 길이 계산
        total_duration = max([seg.end_time for seg in segments]) if segments else 0.0
        
        service.logger.info(f"화자 분리 완료: {len(segments)}개 세그먼트")
        
        return SpeakerDiarizationResponse(
            status="success",
            message="화자 분리가 완료되었습니다",
            data={
                "audio_path": request.audio_path,
                "segments": [seg.dict() for seg in segments],
                "segment_count": len(segments),
                "processing_time": processing_time,
                "min_speakers": request.min_speakers,
                "max_speakers": request.max_speakers
            },
            segments=segments,
            speaker_count=len(set(seg.speaker_id for seg in segments)),
            total_duration=total_duration
        )
        
    except Exception as e:
        service.logger.error(f"화자 분리 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze_speakers", response_model=SpeakerDiarizationResponse)
async def analyze_speakers(request: SpeakerDiarizationRequest) -> SpeakerDiarizationResponse:
    """화자 분석 엔드포인트"""
    try:
        if not service.model_ready:
            raise HTTPException(status_code=503, detail="모델이 준비되지 않았습니다")
        
        if not Path(request.audio_path).exists():
            raise HTTPException(status_code=404, detail=f"오디오 파일을 찾을 수 없습니다: {request.audio_path}")
        
        service.logger.info(f"화자 분석 시작: {request.audio_path}")
        
        # 화자 분석 실행
        start_time = time.time()
        speaker_analysis = await service.diarizer.analyze_speakers_async(request.audio_path, [])
        processing_time = time.time() - start_time
        
        # 분석 결과를 SpeakerSegment 객체로 변환
        segments = [
            SpeakerSegment(
                speaker_id=analysis.get("speaker_id", f"speaker_{i}"),
                start_time=analysis.get("start_time", 0.0),
                end_time=analysis.get("end_time", 0.0),
                confidence=analysis.get("confidence", 0.0)
            )
            for i, analysis in enumerate(speaker_analysis)
        ]
        
        # 전체 길이 계산
        total_duration = max([seg.end_time for seg in segments]) if segments else 0.0
        
        service.logger.info(f"화자 분석 완료: {len(speaker_analysis)}개 화자")
        
        return SpeakerDiarizationResponse(
            status="success",
            message="화자 분석이 완료되었습니다",
            data={
                "audio_path": request.audio_path,
                "speaker_analysis": speaker_analysis,
                "speaker_count": len(speaker_analysis),
                "processing_time": processing_time,
                "analysis_type": "speaker_analysis"
            },
            segments=segments,
            speaker_count=len(speaker_analysis),
            total_duration=total_duration
        )
        
    except Exception as e:
        service.logger.error(f"화자 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002) 