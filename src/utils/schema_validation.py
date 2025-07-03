
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime

class BaseRequest(BaseModel):
    """기본 요청 모델"""
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class BaseResponse(BaseModel):
    """기본 응답 모델"""
    status: str = Field(..., description="처리 상태")
    message: Optional[str] = Field(default=None, description="메시지")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ['success', 'error']:
            raise ValueError('status must be "success" or "error"')
        return v

class AudioRequest(BaseRequest):
    """오디오 요청 모델"""
    audio_data: str = Field(..., description="Base64 인코딩된 오디오 데이터")
    sample_rate: int = Field(default=16000, ge=8000, le=48000)
    format: str = Field(default="wav", regex="^(wav|mp3|flac)$")

class TextRequest(BaseRequest):
    """텍스트 요청 모델"""
    text: str = Field(..., min_length=1, max_length=10000)
    language: str = Field(default="ko", regex="^[a-z]{2}$")

class AnalysisResponse(BaseResponse):
    """분석 응답 모델"""
    data: Optional[Dict[str, Any]] = Field(default=None)
    processing_time: Optional[float] = Field(default=None, ge=0)
