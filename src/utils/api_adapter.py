#!/usr/bin/env python3
"""
Callytics API 어댑터
기존 서비스 응답과 표준 스키마 간 변환 처리
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import uuid

from .api_schemas import (
    create_success_response, 
    create_error_response,
    HealthResponse,
    MetricsResponse,
    AudioProcessResponse,
    AudioSegmentResponse,
    TranscriptionResponse,
    SpeakerDiarizationResponse,
    SentimentAnalysisResponse,
    LLMAnalysisResponse,
    SaveResultResponse,
    AudioSegment,
    TranscriptionResult,
    SpeakerSegment,
    SentimentResult,
    LLMAnalysisResult
)

logger = logging.getLogger(__name__)

class APIAdapter:
    """기존 API와 표준 스키마 간 변환 어댑터"""
    
    def __init__(self):
        self.request_id_generator = lambda: str(uuid.uuid4())
    
    # =============================================================================
    # 공통 응답 변환
    # =============================================================================
    
    def util_adapt_health_response(self, legacy_response: Dict[str, Any]) -> Dict[str, Any]:
        """헬스체크 응답 변환"""
        try:
            health = HealthResponse(
                status=legacy_response.get("status", "healthy"),
                service=legacy_response.get("service", "unknown"),
                version=legacy_response.get("version", "1.0.0")
            )
            return health.model_dump()
        except Exception as e:
            logger.error(f"헬스체크 응답 변환 실패: {e}")
            return create_error_response("헬스체크 응답 변환 실패", error_details={"original": legacy_response})
    
    def util_adapt_metrics_response(self, legacy_response: Dict[str, Any]) -> Dict[str, Any]:
        """메트릭 응답 변환"""
        try:
            metrics = MetricsResponse(
                cpu_percent=legacy_response.get("cpu_percent", 0.0),
                memory_percent=legacy_response.get("memory_percent", 0.0),
                memory_available_gb=legacy_response.get("memory_available_gb", 0.0),
                service=legacy_response.get("service", "unknown")
            )
            return metrics.model_dump()
        except Exception as e:
            logger.error(f"메트릭 응답 변환 실패: {e}")
            return create_error_response("메트릭 응답 변환 실패", error_details={"original": legacy_response})
    
    # =============================================================================
    # 오디오 처리 응답 변환
    # =============================================================================
    
    def util_adapt_audio_preprocess_response(self, legacy_response: Dict[str, Any]) -> Dict[str, Any]:
        """오디오 전처리 응답 변환"""
        try:
            if legacy_response.get("status") != "success":
                return create_error_response(
                    legacy_response.get("message", "오디오 전처리 실패"),
                    request_id=self.request_id_generator()
                )
            
            # 표준 스키마로 변환
            response_data = {
                "status": "success",
                "message": legacy_response.get("message", "오디오 전처리가 완료되었습니다"),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request_id": self.request_id_generator(),
                "data": {
                    "original_path": legacy_response.get("original_path"),
                    "processed_path": legacy_response.get("processed_path"),
                    "processing_time": None  # legacy에서 제공하지 않음
                }
            }
            return response_data
            
        except Exception as e:
            logger.error(f"오디오 전처리 응답 변환 실패: {e}")
            return create_error_response("오디오 전처리 응답 변환 실패", error_details={"original": legacy_response})
    
    def util_adapt_audio_segment_response(self, legacy_response: Dict[str, Any]) -> Dict[str, Any]:
        """오디오 분할 응답 변환"""
        try:
            if legacy_response.get("status") != "success":
                return create_error_response(
                    legacy_response.get("message", "오디오 분할 실패"),
                    request_id=self.request_id_generator()
                )
            
            # 세그먼트 변환
            segments = []
            for segment in legacy_response.get("segments", []):
                segments.append({
                    "start_time": segment.get("start_time", 0.0),
                    "end_time": segment.get("end_time", 0.0),
                    "duration": segment.get("duration", 0.0),
                    "path": segment.get("path", "")
                })
            
            response_data = {
                "status": "success",
                "message": legacy_response.get("message", "오디오 분할이 완료되었습니다"),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request_id": self.request_id_generator(),
                "data": {
                    "original_path": legacy_response.get("original_path"),
                    "segments": segments,
                    "segment_count": legacy_response.get("segment_count", len(segments))
                }
            }
            return response_data
            
        except Exception as e:
            logger.error(f"오디오 분할 응답 변환 실패: {e}")
            return create_error_response("오디오 분할 응답 변환 실패", error_details={"original": legacy_response})
    
    # =============================================================================
    # 음성 인식 응답 변환
    # =============================================================================
    
    def util_adapt_transcription_response(self, legacy_response: Dict[str, Any]) -> Dict[str, Any]:
        """음성 인식 응답 변환"""
        try:
            if legacy_response.get("status") != "success":
                return create_error_response(
                    legacy_response.get("message", "음성 인식 실패"),
                    request_id=self.request_id_generator()
                )
            
            # 음성 인식 결과 변환
            transcriptions = []
            for transcription in legacy_response.get("transcriptions", []):
                transcriptions.append({
                    "text": transcription.get("text", ""),
                    "confidence": transcription.get("confidence"),
                    "start_time": transcription.get("start_time"),
                    "end_time": transcription.get("end_time"),
                    "speaker_id": transcription.get("speaker_id")
                })
            
            response_data = {
                "status": "success",
                "message": legacy_response.get("message", "음성 인식이 완료되었습니다"),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request_id": self.request_id_generator(),
                "data": {
                    "transcriptions": transcriptions,
                    "transcription_count": legacy_response.get("transcription_count", len(transcriptions)),
                    "total_duration": None  # legacy에서 제공하지 않음
                }
            }
            return response_data
            
        except Exception as e:
            logger.error(f"음성 인식 응답 변환 실패: {e}")
            return create_error_response("음성 인식 응답 변환 실패", error_details={"original": legacy_response})
    
    # =============================================================================
    # 화자 분리 응답 변환
    # =============================================================================
    
    def util_adapt_speaker_diarization_response(self, legacy_response: Dict[str, Any]) -> Dict[str, Any]:
        """화자 분리 응답 변환"""
        try:
            if legacy_response.get("status") != "success":
                return create_error_response(
                    legacy_response.get("message", "화자 분리 실패"),
                    request_id=self.request_id_generator()
                )
            
            # 화자 세그먼트 변환
            segments = []
            for segment in legacy_response.get("segments", []):
                segments.append({
                    "speaker_id": segment.get("speaker_id", "unknown"),
                    "start_time": segment.get("start_time", 0.0),
                    "end_time": segment.get("end_time", 0.0),
                    "confidence": segment.get("confidence")
                })
            
            response_data = {
                "status": "success",
                "message": legacy_response.get("message", "화자 분리가 완료되었습니다"),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request_id": self.request_id_generator(),
                "data": {
                    "segments": segments,
                    "speaker_count": legacy_response.get("speaker_count", len(set(s["speaker_id"] for s in segments))),
                    "total_duration": legacy_response.get("total_duration", 0.0)
                }
            }
            return response_data
            
        except Exception as e:
            logger.error(f"화자 분리 응답 변환 실패: {e}")
            return create_error_response("화자 분리 응답 변환 실패", error_details={"original": legacy_response})
    
    # =============================================================================
    # 감정 분석 응답 변환
    # =============================================================================
    
    def util_adapt_sentiment_analysis_response(self, legacy_response: Dict[str, Any]) -> Dict[str, Any]:
        """감정 분석 응답 변환"""
        try:
            if legacy_response.get("status") != "success":
                return create_error_response(
                    legacy_response.get("message", "감정 분석 실패"),
                    request_id=self.request_id_generator()
                )
            
            # 감정 분석 결과 변환
            sentiment_data = legacy_response.get("sentiment_analysis", {})
            sentiment_result = {
                "emotion": sentiment_data.get("emotion", "neutral"),
                "confidence": sentiment_data.get("confidence", 0.0),
                "emotions_detail": sentiment_data.get("emotions_detail")
            }
            
            # 세그먼트별 감정 분석 (있는 경우)
            segment_sentiments = []
            for segment_sentiment in legacy_response.get("segment_sentiments", []):
                segment_sentiments.append({
                    "emotion": segment_sentiment.get("emotion", "neutral"),
                    "confidence": segment_sentiment.get("confidence", 0.0),
                    "emotions_detail": segment_sentiment.get("emotions_detail")
                })
            
            response_data = {
                "status": "success",
                "message": legacy_response.get("message", "감정 분석이 완료되었습니다"),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request_id": self.request_id_generator(),
                "data": {
                    "sentiment_analysis": sentiment_result,
                    "segment_sentiments": segment_sentiments if segment_sentiments else None
                }
            }
            return response_data
            
        except Exception as e:
            logger.error(f"감정 분석 응답 변환 실패: {e}")
            return create_error_response("감정 분석 응답 변환 실패", error_details={"original": legacy_response})
    
    # =============================================================================
    # LLM 분석 응답 변환
    # =============================================================================
    
    def util_adapt_llm_analysis_response(self, legacy_response: Dict[str, Any]) -> Dict[str, Any]:
        """LLM 분석 응답 변환"""
        try:
            if legacy_response.get("status") != "success":
                return create_error_response(
                    legacy_response.get("message", "LLM 분석 실패"),
                    request_id=self.request_id_generator()
                )
            
            # LLM 분석 결과 변환
            analysis_data = legacy_response.get("communication_analysis", {}) or \
                           legacy_response.get("llm_analysis", {}) or \
                           legacy_response.get("insights", {}) or \
                           legacy_response.get("complaint_analysis", {})
            
            llm_result = {
                "analysis_type": "quality",  # 기본값
                "score": analysis_data.get("score"),
                "summary": analysis_data.get("summary", ""),
                "details": analysis_data.get("details", {}),
                "recommendations": analysis_data.get("recommendations")
            }
            
            response_data = {
                "status": "success",
                "message": legacy_response.get("message", "LLM 분석이 완료되었습니다"),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request_id": self.request_id_generator(),
                "data": {
                    "llm_analysis": llm_result
                }
            }
            return response_data
            
        except Exception as e:
            logger.error(f"LLM 분석 응답 변환 실패: {e}")
            return create_error_response("LLM 분석 응답 변환 실패", error_details={"original": legacy_response})
    
    # =============================================================================
    # 데이터베이스 응답 변환
    # =============================================================================
    
    def util_adapt_save_result_response(self, legacy_response: Dict[str, Any]) -> Dict[str, Any]:
        """결과 저장 응답 변환"""
        try:
            if legacy_response.get("status") != "success":
                return create_error_response(
                    legacy_response.get("message", "결과 저장 실패"),
                    request_id=self.request_id_generator()
                )
            
            # 저장된 ID들 변환
            saved_ids = legacy_response.get("saved_ids", {})
            if not saved_ids:
                # 개별 ID 필드들 확인
                saved_ids = {
                    "audio_id": legacy_response.get("audio_id"),
                    "quality_id": legacy_response.get("quality_id")
                }
            
            response_data = {
                "status": "success",
                "message": legacy_response.get("message", "결과가 저장되었습니다"),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request_id": self.request_id_generator(),
                "data": {
                    "saved_ids": saved_ids
                }
            }
            return response_data
            
        except Exception as e:
            logger.error(f"결과 저장 응답 변환 실패: {e}")
            return create_error_response("결과 저장 응답 변환 실패", error_details={"original": legacy_response})
    
    # =============================================================================
    # 요청 데이터 변환
    # =============================================================================
    
    def util_adapt_request_data(self, standardized_request: Dict[str, Any], service_type: str) -> Dict[str, Any]:
        """표준 요청을 기존 서비스 형식으로 변환"""
        try:
            if service_type == "audio_processor":
                return {
                    "audio_path": standardized_request.get("audio_path"),
                    "chunk_duration": standardized_request.get("chunk_duration", 30)
                }
            
            elif service_type == "speech_recognizer":
                return {
                    "audio_path": standardized_request.get("audio_path"),
                    "segments": standardized_request.get("segments", [])
                }
            
            elif service_type == "speaker_diarizer":
                return {
                    "audio_path": standardized_request.get("audio_path")
                }
            
            elif service_type == "sentiment_analyzer":
                return {
                    "text_data": standardized_request.get("text_data"),
                    "segments": standardized_request.get("segments")
                }
            
            elif service_type == "llm_analyzer":
                return {
                    "text_data": standardized_request.get("text_data"),
                    "analysis_data": standardized_request.get("context", {})
                }
            
            elif service_type == "database_service":
                return {"status": "success", "data": result: standardized_request.get("result")
                }
            
            else:
                return standardized_request
                
        except Exception as e:
            logger.error(f"요청 데이터 변환 실패 ({service_type}): {e}")
            return standardized_request

# 전역 어댑터 인스턴스
api_adapter = APIAdapter() 