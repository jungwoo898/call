#!/usr/bin/env python3
"""
Callytics 공통 API 스키마
모든 마이크로서비스에서 사용하는 표준화된 요청/응답 스키마
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

# =============================================================================
# 공통 응답 스키마
# =============================================================================

class StatusEnum(str, Enum):
    """응답 상태 열거형"""
    SUCCESS = "success"
    ERROR = "error"
    PROCESSING = "processing"
    PENDING = "pending"

class BaseResponse(BaseModel):
    """기본 응답 스키마"""
    status: StatusEnum = Field(..., description="처리 상태")
    message: str = Field(..., description="응답 메시지")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="응답 시간 (UTC)")
    request_id: str | None = Field(None, description="요청 ID")

class SuccessResponse(BaseResponse):
    """성공 응답 스키마"""
    status: StatusEnum = StatusEnum.SUCCESS
    data: Optional[Dict[str, Any]] = Field(None, description="응답 데이터")

class ErrorResponse(BaseResponse):
    """오류 응답 스키마"""
    status: StatusEnum = StatusEnum.ERROR
    error_code: str | None = Field(None, description="오류 코드")
    error_details: Optional[Dict[str, Any]] = Field(None, description="오류 상세 정보")

class HealthResponse(BaseModel):
    """헬스체크 응답 스키마"""
    status: str = Field("healthy", description="서비스 상태 (healthy/unhealthy)")
    service: str = Field(..., description="서비스 이름")
    version: str = Field("1.0.0", description="서비스 버전")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="체크 시간 (UTC)")
    uptime_seconds: float = Field(..., description="서비스 실행 시간 (초)")
    model_ready: bool = Field(default=True, description="모델 준비 상태")
    details: Optional[Dict[str, Any]] = Field(None, description="상세 헬스체크 정보")

class MetricsResponse(BaseModel):
    """메트릭 응답 스키마"""
    service: str = Field(..., description="서비스 이름")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="측정 시간 (UTC)")
    uptime_seconds: float = Field(..., description="서비스 실행 시간 (초)")
    cpu_percent: float = Field(..., description="CPU 사용률 (%)")
    memory_percent: float = Field(..., description="메모리 사용률 (%)")
    memory_available_gb: float = Field(..., description="사용 가능한 메모리 (GB)")
    disk_percent: float = Field(..., description="디스크 사용률 (%)")
    disk_available_gb: float = Field(..., description="사용 가능한 디스크 (GB)")
    custom_metrics: Optional[Dict[str, Any]] = Field(None, description="서비스별 추가 메트릭")

# =============================================================================
# 오디오 처리 스키마
# =============================================================================

class AudioProcessRequest(BaseModel):
    """오디오 처리 요청 스키마"""
    audio_path: str = Field(..., description="오디오 파일 경로")
    options: Optional[Dict[str, Any]] = Field(None, description="처리 옵션")

class AudioProcessResponse(SuccessResponse):
    """오디오 처리 응답 스키마"""
    original_path: str = Field(..., description="원본 파일 경로")
    processed_path: str = Field(..., description="처리된 파일 경로")
    processing_time: float | None = Field(None, description="처리 시간 (초)")

class AudioSegmentRequest(BaseModel):
    """오디오 분할 요청 스키마"""
    audio_path: str = Field(..., description="오디오 파일 경로")
    chunk_duration: int = Field(30, description="청크 길이 (초)")

class AudioSegment(BaseModel):
    """오디오 세그먼트 스키마"""
    start_time: float = Field(..., description="시작 시간 (초)")
    end_time: float = Field(..., description="종료 시간 (초)")
    duration: float = Field(..., description="길이 (초)")
    path: str = Field(..., description="세그먼트 파일 경로")

class AudioSegmentResponse(SuccessResponse):
    """오디오 분할 응답 스키마"""
    original_path: str = Field(..., description="원본 파일 경로")
    segments: List[AudioSegment] = Field(..., description="분할된 세그먼트 목록")
    segment_count: int = Field(..., description="세그먼트 개수")

# =============================================================================
# 음성 인식 스키마
# =============================================================================

class TranscriptionRequest(BaseModel):
    """음성 인식 요청 스키마"""
    audio_path: str | None = Field(None, description="오디오 파일 경로")
    segments: Optional[List[AudioSegment]] = Field(None, description="오디오 세그먼트 목록")
    language: str = Field("ko", description="언어 코드")
    model: str = Field("whisper-large-v2", description="사용할 모델")

class TranscriptionResult(BaseModel):
    """음성 인식 결과 스키마"""
    text: str = Field(..., description="인식된 텍스트")
    confidence: float | None = Field(None, description="신뢰도 (0.0 ~ 1.0)")
    start_time: float | None = Field(None, description="시작 시간 (초)")
    end_time: float | None = Field(None, description="종료 시간 (초)")
    speaker_id: str | None = Field(None, description="화자 ID")

class TranscriptionResponse(SuccessResponse):
    """음성 인식 응답 스키마"""
    transcriptions: List[TranscriptionResult] = Field(..., description="음성 인식 결과 목록")
    transcription_count: int = Field(..., description="인식 결과 개수")
    total_duration: float | None = Field(None, description="전체 길이 (초)")

# =============================================================================
# 화자 분리 스키마
# =============================================================================

class SpeakerDiarizationRequest(BaseModel):
    """화자 분리 요청 스키마"""
    audio_path: str = Field(..., description="오디오 파일 경로")
    min_speakers: int = Field(2, description="최소 화자 수")
    max_speakers: int = Field(10, description="최대 화자 수")

class SpeakerSegment(BaseModel):
    """화자 세그먼트 스키마"""
    speaker_id: str = Field(..., description="화자 ID")
    start_time: float = Field(..., description="시작 시간 (초)")
    end_time: float = Field(..., description="종료 시간 (초)")
    confidence: float | None = Field(None, description="신뢰도 (0.0 ~ 1.0)")

class SpeakerDiarizationResponse(SuccessResponse):
    """화자 분리 응답 스키마"""
    segments: List[SpeakerSegment] = Field(..., description="화자 세그먼트 목록")
    speaker_count: int = Field(..., description="감지된 화자 수")
    total_duration: float = Field(..., description="전체 길이 (초)")

# =============================================================================
# 감정 분석 스키마
# =============================================================================

class SentimentAnalysisRequest(BaseModel):
    """감정 분석 요청 스키마"""
    text_data: str = Field(..., description="분석할 텍스트")
    segments: Optional[List[TranscriptionResult]] = Field(None, description="세그먼트별 분석")

class SentimentResult(BaseModel):
    """감정 분석 결과 스키마"""
    emotion: str = Field(..., description="감정 (positive/negative/neutral)")
    confidence: float = Field(..., description="신뢰도 (0.0 ~ 1.0)")
    emotions_detail: Optional[Dict[str, float]] = Field(None, description="세부 감정 점수")

class SentimentAnalysisResponse(SuccessResponse):
    """감정 분석 응답 스키마"""
    sentiment_analysis: SentimentResult = Field(..., description="감정 분석 결과")
    segment_sentiments: Optional[List[SentimentResult]] = Field(None, description="세그먼트별 감정 분석")

# =============================================================================
# LLM 분석 스키마
# =============================================================================

class LLMAnalysisRequest(BaseModel):
    """LLM 분석 요청 스키마"""
    text_data: str = Field(..., description="분석할 텍스트")
    analysis_type: str = Field("quality", description="분석 유형 (quality/complaints/insights)")
    context: Optional[Dict[str, Any]] = Field(None, description="분석 컨텍스트")

class LLMAnalysisResult(BaseModel):
    """LLM 분석 결과 스키마"""
    analysis_type: str = Field(..., description="분석 유형")
    score: float | None = Field(None, description="품질 점수 (0.0 ~ 1.0)")
    summary: str = Field(..., description="분석 요약")
    details: Dict[str, Any] = Field(..., description="상세 분석 결과")
    recommendations: Optional[List[str]] = Field(None, description="개선 권장사항")

class LLMAnalysisResponse(SuccessResponse):
    """LLM 분석 응답 스키마"""
    llm_analysis: LLMAnalysisResult = Field(..., description="LLM 분석 결과")

# =============================================================================
# 데이터베이스 스키마
# =============================================================================

class SaveResultRequest(BaseModel):
    """결과 저장 요청 스키마"""
    result: Dict[str, Any] = Field(..., description="저장할 결과 데이터")
    result_type: str = Field("analysis", description="결과 유형")

class SaveResultResponse(SuccessResponse):
    """결과 저장 응답 스키마"""
    saved_ids: Dict[str, str | None] = Field(..., description="저장된 ID 목록")

class GetAnalysisResponse(SuccessResponse):
    """분석 결과 조회 응답 스키마"""
    analysis_id: str = Field(..., description="분석 ID")
    result: Dict[str, Any] = Field(..., description="분석 결과")

# =============================================================================
# 통합 처리 스키마
# =============================================================================

class IntegratedAnalysisRequest(BaseModel):
    """통합 분석 요청 스키마"""
    audio_path: str = Field(..., description="오디오 파일 경로")
    options: Optional[Dict[str, Any]] = Field(None, description="처리 옵션")

class IntegratedAnalysisResult(BaseModel):
    """통합 분석 결과 스키마"""
    audio_path: str = Field(..., description="원본 오디오 경로")
    speaker_segments: List[SpeakerSegment] = Field(..., description="화자 분리 결과")
    transcriptions: List[TranscriptionResult] = Field(..., description="음성 인식 결과")
    sentiment_analysis: SentimentResult = Field(..., description="감정 분석 결과")
    llm_analysis: LLMAnalysisResult = Field(..., description="LLM 분석 결과")
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow, description="처리 시간")
    processing_duration: float | None = Field(None, description="전체 처리 시간 (초)")

class IntegratedAnalysisResponse(SuccessResponse):
    """통합 분석 응답 스키마"""
    final_result: IntegratedAnalysisResult = Field(..., description="최종 분석 결과")

# =============================================================================
# 헬퍼 함수
# =============================================================================

def util_create_success_response(
    message: str, 
    data: Optional[Dict[str, Any]] = None,
    request_id: str | None = None
) -> Dict[str, Any]:
    """성공 응답 생성 헬퍼"""
    response = SuccessResponse(message=message, data=data, request_id=request_id)
    return response.model_dump()

def util_create_error_response(
    message: str,
    error_code: str | None = None,
    error_details: Optional[Dict[str, Any]] = None,
    request_id: str | None = None
) -> Dict[str, Any]:
    """오류 응답 생성 헬퍼"""
    response = ErrorResponse(
        message=message,
        error_code=error_code,
        error_details=error_details,
        request_id=request_id
    )
    return response.model_dump() 
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class AudioInput(BaseModel):
    audio_data: str = Field(..., description="Base64 인코딩된 오디오 데이터")
    sample_rate: int = Field(default=16000, description="샘플링 레이트 (Hz)")
    format: str = Field(default="wav", description="오디오 포맷")

class TextInput(BaseModel):
    text: str = Field(..., description="분석할 텍스트")
    language: str = Field(default="ko", description="언어 코드")
    options: Optional[Dict[str, Any]] = Field(default=None, description="추가 옵션")

class AnalysisResult(BaseModel):
    status: str = Field(..., description="처리 상태")
    message: Optional[str] = Field(default=None, description="메시지")
    data: Optional[Dict[str, Any]] = Field(default=None, description="결과 데이터")
    timestamp: str = Field(default_factory=lambda: get_current_time().isoformat())
    processing_time: Optional[float] = Field(default=None, description="처리 시간")
