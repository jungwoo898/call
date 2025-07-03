"""
공통 타입 정의 모듈
전 프로젝트에서 일관된 타입 정의를 제공하여 타입 불일치 해결
"""

from typing import Dict, List, Any, Optional, Union, Tuple
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

# ============================================================================
# 기본 응답 타입
# ============================================================================

class HealthStatus(str, Enum):
    """헬스체크 상태 열거형"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"

class HealthResponse(BaseModel):
    """통합 헬스체크 응답 타입"""
    status: HealthStatus
    service: str
    version: str
    timestamp: datetime
    uptime: float = Field(description="서비스 가동 시간 (초)")
    system: Dict[str, Any] = Field(description="시스템 정보")
    gpu: Optional[Dict[str, Any]] = Field(None, description="GPU 정보")
    error: str | None = Field(None, description="오류 메시지")

class MetricsResponse(BaseModel):
    """통합 메트릭 응답 타입"""
    timestamp: datetime
    service: str
    system: Dict[str, Any] = Field(description="시스템 메트릭")
    network: Dict[str, Any] = Field(description="네트워크 메트릭")
    gpu: Optional[Dict[str, Any]] = Field(None, description="GPU 메트릭")
    error: str | None = Field(None, description="오류 메시지")

class SuccessResponse(BaseModel):
    """성공 응답 타입"""
    success: bool = True
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    """오류 응답 타입"""
    success: bool = False
    error: str
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Optional[Dict[str, Any]] = None

# ============================================================================
# 오디오 처리 타입
# ============================================================================

class AudioFormat(str, Enum):
    """오디오 포맷 열거형"""
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    M4A = "m4a"

class AudioProperties(BaseModel):
    """오디오 속성 타입"""
    file_path: str
    file_name: str
    duration: float = Field(description="오디오 길이 (초)")
    sample_rate: int = Field(description="샘플링 레이트")
    channels: int = Field(description="채널 수")
    format: AudioFormat
    min_frequency: float | None = Field(None, description="최소 주파수")
    max_frequency: float | None = Field(None, description="최대 주파수")
    bit_depth: int | None = Field(None, description="비트 깊이")

class SpeakerSegment(BaseModel):
    """화자 세그먼트 타입"""
    speaker_id: str
    start_time: float
    end_time: float
    confidence: float | None = Field(None, description="신뢰도")

class Utterance(BaseModel):
    """발화 타입"""
    speaker_id: str
    text: str
    start_time: float
    end_time: float
    confidence: float | None = None
    sentiment: str | None = None
    profane: bool | None = None

# ============================================================================
# 분석 결과 타입
# ============================================================================

class SentimentType(str, Enum):
    """감정 분석 타입"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class AnalysisResult(BaseModel):
    """분석 결과 타입"""
    consultation_id: str | None = None
    audio_properties: AudioProperties
    utterances: List[Utterance]
    speaker_segments: List[SpeakerSegment]
    summary: str | None = None
    topics: List[str] = Field(default_factory=list)
    sentiment_overall: Optional[SentimentType] = None
    quality_score: float | None = Field(None, ge=0.0, le=1.0)
    processing_time: float = Field(description="처리 시간 (초)")

# ============================================================================
# 데이터베이스 타입
# ============================================================================

class DatabaseType(str, Enum):
    """데이터베이스 타입"""
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"

class DatabaseConfig(BaseModel):
    """데이터베이스 설정 타입"""
    type: DatabaseType
    host: str | None = None
    port: int | None = None
    database: str
    username: str | None = None
    password: str | None = None
    ssl_mode: str | None = None

# ============================================================================
# 서비스 설정 타입
# ============================================================================

class ServiceConfig(BaseModel):
    """서비스 설정 타입"""
    name: str
    version: str
    host: str = "0.0.0.0"
    port: int
    workers: int = 1
    log_level: str = "INFO"
    environment: str = "production"

class ModelConfig(BaseModel):
    """모델 설정 타입"""
    device: str = "auto"
    batch_size: int = 1
    max_length: int | None = None
    temperature: float = 0.7
    model_name: str

# ============================================================================
# 유틸리티 타입
# ============================================================================

class ProcessingStatus(BaseModel):
    """처리 상태 타입"""
    is_processing: bool
    current_file: str | None = None
    total_processed: int = 0
    errors: List[str] = Field(default_factory=list)
    start_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None

class CacheConfig(BaseModel):
    """캐시 설정 타입"""
    enabled: bool = True
    max_size: int = 1000
    ttl: int = 3600  # 초
    backend: str = "memory"  # memory, redis

# ============================================================================
# 타입 별칭 (기존 코드와의 호환성)
# ============================================================================

# 기존 코드에서 사용하던 타입들을 새로운 타입으로 매핑
JSONResponse = Dict[str, Any]
APIResponse = Union[SuccessResponse, ErrorResponse]
AudioData = Union[str, bytes]  # 파일 경로 또는 바이트 데이터
ModelInput = Union[str, List[str], Dict[str, Any]]
ModelOutput = Union[str, List[str], Dict[str, Any]]

# ============================================================================
# 타입 검증 함수
# ============================================================================

def util_validate_audio_properties(props: Dict[str, Any]) -> AudioProperties:
    """오디오 속성 검증"""
    return AudioProperties(**props)

def util_validate_analysis_result(result: Dict[str, Any]) -> AnalysisResult:
    """분석 결과 검증"""
    return AnalysisResult(**result)

def util_validate_service_config(config: Dict[str, Any]) -> ServiceConfig:
    """서비스 설정 검증"""
    return ServiceConfig(**config) 