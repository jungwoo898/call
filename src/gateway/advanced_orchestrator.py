#!/usr/bin/env python3
"""
강화된 서비스 오케스트레이터
재시도 로직, 서킷 브레이커, Graceful Degradation 포함
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CIRCUIT_OPEN = "circuit_open"

@dataclass
class ServiceConfig:
    """서비스별 설정"""
    name: str
    url: str
    timeout: float = 300.0  # 5분
    max_retries: int = 3
    retry_delay: float = 1.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0  # 1분

class CircuitBreaker:
    """서킷 브레이커 구현"""
    
    def __init__(self, threshold: int, timeout: float):
        self.threshold = threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = ServiceStatus.HEALTHY
    
    def gateway_record_success(self):
        """성공 기록"""
        self.failure_count = 0
        self.state = ServiceStatus.HEALTHY
    
    def gateway_record_failure(self):
        """실패 기록"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.threshold:
            self.state = ServiceStatus.CIRCUIT_OPEN
    
    def gateway_can_execute(self) -> bool:
        """실행 가능 여부 확인"""
        if self.state == ServiceStatus.CIRCUIT_OPEN:
            # 타임아웃 후 다시 시도
            if time.time() - self.last_failure_time > self.timeout:
                self.state = ServiceStatus.DEGRADED
                return True
            return False
        return True
    
    def gateway_get_status(self) -> ServiceStatus:
        """현재 상태 반환"""
        return self.state

class AdvancedServiceOrchestrator:
    """강화된 서비스 오케스트레이터"""
    
    def __init__(self, service_urls: Dict[str, str]):
        self.service_configs = {}
        self.circuit_breakers = {}
        self.client = httpx.AsyncClient(timeout=300.0)
        
        # 각 서비스별 설정 초기화
        for service_name, url in service_urls.items():
            config = ServiceConfig(name=service_name, url=url)
            self.service_configs[service_name] = config
            self.circuit_breakers[service_name] = CircuitBreaker(
                config.circuit_breaker_threshold,
                config.circuit_breaker_timeout
            )
    
    async def call_service_with_retry(self, 
                                    service_name: str, 
                                    endpoint: str, 
                                    data: Dict[str, Any],
                                    max_retries: int | None = None) -> Dict[str, Any]:
        """재시도 로직이 포함된 서비스 호출"""
        
        config = self.service_configs[service_name]
        circuit_breaker = self.circuit_breakers[service_name]
        
        # 서킷 브레이커 확인
        if not circuit_breaker.gateway_can_execute():
            raise HTTPException(
                status_code=503, 
                detail=f"서비스 {service_name}가 일시적으로 사용할 수 없습니다 (서킷 브레이커 열림)"
            )
        
        retries = max_retries or config.max_retries
        last_exception = None
        
        for attempt in range(retries + 1):
            try:
                url = f"{config.url}{endpoint}"
                logger.info(f"서비스 호출 시도 {attempt + 1}/{retries + 1}: {service_name} -> {endpoint}")
                
                response = await self.client.post(url, json=data, timeout=config.timeout)
                response.raise_for_status()
                
                # 성공 시 서킷 브레이커 리셋
                circuit_breaker.gateway_record_success()
                return response.json()
                
            except httpx.TimeoutException as e:
                last_exception = e
                logger.warning(f"서비스 {service_name} 타임아웃 (시도 {attempt + 1}/{retries + 1})")
                
            except httpx.HTTPStatusError as e:
                last_exception = e
                logger.error(f"서비스 {service_name} HTTP 오류 {e.response.status_code} (시도 {attempt + 1}/{retries + 1})")
                
            except Exception as e:
                last_exception = e
                logger.error(f"서비스 {service_name} 호출 실패: {e} (시도 {attempt + 1}/{retries + 1})")
            
            # 마지막 시도가 아니면 대기
            if attempt < retries:
                await asyncio.sleep(config.retry_delay * (2 ** attempt))  # 지수 백오프
        
        # 모든 시도 실패
        circuit_breaker.gateway_record_failure()
        raise HTTPException(
            status_code=500, 
            detail=f"서비스 {service_name} 호출 실패 (최대 재시도 횟수 초과): {last_exception}"
        )
    
    async def process_audio_pipeline_graceful(self, audio_file_path: str) -> Dict[str, Any]:
        """Graceful Degradation이 포함된 오디오 처리 파이프라인"""
        
        result = {
            'audio_path': audio_file_path,
            'processing_timestamp': time.time(),
            'services_status': {},
            'warnings': []
        }
        
        try:
            # 1. 오디오 전처리 (필수)
            logger.info("1단계: 오디오 전처리")
            try:
                preprocessed_audio = await self.call_service_with_retry(
                    'audio_processor', '/preprocess', {'audio_path': audio_file_path}
                )
                result['preprocessed_audio'] = preprocessed_audio
                result['services_status']['audio_processor'] = 'success'
            except Exception as e:
                logger.error(f"오디오 전처리 실패: {e}")
                result['services_status']['audio_processor'] = 'failed'
                result['warnings'].append(f"오디오 전처리 실패: {e}")
                # 전처리 실패 시 원본 파일 사용
                preprocessed_audio = {'processed_path': audio_file_path}
            
            # 2. 화자 분리 (선택적)
            logger.info("2단계: 화자 분리")
            try:
                speaker_segments = await self.call_service_with_retry(
                    'speaker_diarizer', '/diarize', {'audio_path': preprocessed_audio['processed_path']}
                )
                result['speaker_segments'] = speaker_segments
                result['services_status']['speaker_diarizer'] = 'success'
            except Exception as e:
                logger.warning(f"화자 분리 실패 (선택적): {e}")
                result['services_status']['speaker_diarizer'] = 'failed'
                result['warnings'].append(f"화자 분리 실패: {e}")
                # 화자 분리 실패 시 전체 오디오를 하나의 세그먼트로 처리
                speaker_segments = {'segments': [{'start': 0, 'end': 999999, 'speaker': 'unknown'}]}
            
            # 3. 음성 인식 (필수)
            logger.info("3단계: 음성 인식")
            try:
                transcriptions = await self.call_service_with_retry(
                    'speech_recognizer', '/transcribe', {'segments': speaker_segments['segments']}
                )
                result['transcriptions'] = transcriptions
                result['services_status']['speech_recognizer'] = 'success'
            except Exception as e:
                logger.error(f"음성 인식 실패: {e}")
                result['services_status']['speech_recognizer'] = 'failed'
                result['warnings'].append(f"음성 인식 실패: {e}")
                raise HTTPException(status_code=500, detail="음성 인식 실패로 인해 분석을 중단합니다")
            
            # 4. 문장 부호 복원 (선택적)
            logger.info("4단계: 문장 부호 복원")
            try:
                punctuated_text = await self.call_service_with_retry(
                    'punctuation_restorer', '/restore', {'transcriptions': transcriptions['transcriptions']}
                )
                result['punctuated_text'] = punctuated_text
                result['services_status']['punctuation_restorer'] = 'success'
            except Exception as e:
                logger.warning(f"문장 부호 복원 실패 (선택적): {e}")
                result['services_status']['punctuation_restorer'] = 'failed'
                result['warnings'].append(f"문장 부호 복원 실패: {e}")
                # 문장 부호 복원 실패 시 원본 텍스트 사용
                punctuated_text = {'restored_text': transcriptions.get('text', '')}
            
            # 5. 감정 분석 (선택적)
            logger.info("5단계: 감정 분석")
            try:
                sentiment_results = await self.call_service_with_retry(
                    'sentiment_analyzer', '/analyze', {'text_data': punctuated_text['restored_text']}
                )
                result['sentiment_analysis'] = sentiment_results
                result['services_status']['sentiment_analyzer'] = 'success'
            except Exception as e:
                logger.warning(f"감정 분석 실패 (선택적): {e}")
                result['services_status']['sentiment_analyzer'] = 'failed'
                result['warnings'].append(f"감정 분석 실패: {e}")
                result['sentiment_analysis'] = {'status': 'failed', 'error': str(e)}
            
            # 6. LLM 분석 (선택적)
            logger.info("6단계: LLM 분석")
            try:
                llm_results = await self.call_service_with_retry(
                    'llm_analyzer', '/analyze', {'text_data': punctuated_text['restored_text']}
                )
                result['llm_analysis'] = llm_results
                result['services_status']['llm_analyzer'] = 'success'
            except Exception as e:
                logger.warning(f"LLM 분석 실패 (선택적): {e}")
                result['services_status']['llm_analyzer'] = 'failed'
                result['warnings'].append(f"LLM 분석 실패: {e}")
                result['llm_analysis'] = {'status': 'failed', 'error': str(e)}
            
            # 7. 결과 저장 (선택적)
            logger.info("7단계: 결과 저장")
            try:
                await self.call_service_with_retry(
                    'database_service', '/save_result', {'result': result}
                )
                result['services_status']['database_service'] = 'success'
            except Exception as e:
                logger.warning(f"결과 저장 실패 (선택적): {e}")
                result['services_status']['database_service'] = 'failed'
                result['warnings'].append(f"결과 저장 실패: {e}")
            
            logger.info("오디오 처리 파이프라인 완료 (Graceful Degradation 적용)")
            return result
            
        except Exception as e:
            logger.error(f"파이프라인 처리 중 치명적 오류: {e}")
            result['error'] = str(e)
            result['status'] = 'failed'
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_service_health(self) -> Dict[str, Any]:
        """모든 서비스의 상세 헬스 상태 확인"""
        health_status = {}
        
        for service_name, config in self.service_configs.items():
            circuit_breaker = self.circuit_breakers[service_name]
            
            try:
                # 실제 헬스체크
                response = await self.client.get(f"{config.url}/health", timeout=10.0)
                service_healthy = response.status_code == 200
                
                health_status[service_name] = {
                    'status': 'healthy' if service_healthy else 'unhealthy',
                    'circuit_breaker': circuit_breaker.gateway_get_status().value,
                    'failure_count': circuit_breaker.failure_count,
                    'last_check': time.time()
                }
                
            except Exception as e:
                health_status[service_name] = {
                    'status': 'unreachable',
                    'circuit_breaker': circuit_breaker.gateway_get_status().value,
                    'failure_count': circuit_breaker.failure_count,
                    'error': str(e),
                    'last_check': time.time()
                }
        
        return health_status
    
    async def close(self):
        """리소스 정리"""
        await self.client.aclose() 