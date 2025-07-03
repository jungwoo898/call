#!/usr/bin/env python3
"""
분산 Circuit Breaker 시스템
Redis 기반 상태 저장, 자동 복구, 메트릭 수집
"""

import asyncio
import time
import json
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, asdict
from enum import Enum
from contextlib import asynccontextmanager
import hashlib

from .redis_manager import get_redis_manager
from .structured_logger import get_logger

logger = get_logger(__name__)

class CircuitState(Enum):
    """Circuit Breaker 상태"""
    CLOSED = "closed"      # 정상 상태
    OPEN = "open"          # 차단 상태  
    HALF_OPEN = "half_open"  # 반개방 상태

@dataclass
class CircuitBreakerConfig:
    """Circuit Breaker 설정"""
    failure_threshold: int = 5          # 실패 임계값
    success_threshold: int = 3          # 성공 임계값 (HALF_OPEN 상태에서)
    timeout: float = 60.0               # 타임아웃 (초)
    window_size: int = 100              # 슬라이딩 윈도우 크기
    minimum_request_count: int = 10     # 최소 요청 수
    failure_rate_threshold: float = 0.5 # 실패율 임계값 (50%)

@dataclass
class CircuitMetrics:
    """Circuit Breaker 메트릭"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    circuit_open_count: int = 0
    circuit_half_open_count: int = 0
    last_failure_time: float = 0
    last_success_time: float = 0
    current_state: CircuitState = CircuitState.CLOSED
    state_changed_at: float = 0

class CircuitBreaker:
    """분산 Circuit Breaker"""
    
    def __init__(self, 
                 name: str,
                 config: CircuitBreakerConfig = None,
                 fallback_func: Optional[Callable] = None):
        """
        Circuit Breaker 초기화
        
        Parameters
        ----------
        name : str
            Circuit Breaker 이름 (서비스별 고유)
        config : CircuitBreakerConfig, optional
            설정 (기본값 사용 시 None)
        fallback_func : Callable, optional
            폴백 함수
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.fallback_func = fallback_func
        
        # Redis 키 생성
        self.redis_key = f"circuit_breaker:{self.name}"
        self.metrics_key = f"circuit_metrics:{self.name}"
        self.window_key = f"circuit_window:{self.name}"
        
        # 로컬 캐시 (성능 최적화)
        self._local_cache = {}
        self._cache_ttl = 5.0  # 5초
        self._last_cache_update = 0
    
    async def _get_redis(self):
        """Redis 매니저 인스턴스 반환"""
        return await get_redis_manager()
    
    async def _get_state(self) -> CircuitState:
        """현재 상태 조회"""
        # 로컬 캐시 확인
        current_time = time.time()
        if (current_time - self._last_cache_update < self._cache_ttl and 
            'state' in self._local_cache):
            return CircuitState(self._local_cache['state'])
        
        try:
            redis = await self._get_redis()
            state_data = await redis.get('cache', self.redis_key)
            
            if state_data:
                data = json.loads(state_data) if isinstance(state_data, str) else state_data
                state = CircuitState(data.get('state', CircuitState.CLOSED.value))
                
                # 로컬 캐시 업데이트
                self._local_cache = data
                self._last_cache_update = current_time
                
                return state
            else:
                return CircuitState.CLOSED
                
        except Exception as e:
            logger.error(f"Circuit Breaker 상태 조회 실패: {self.name}", error=e)
            return CircuitState.CLOSED
    
    async def _set_state(self, state: CircuitState, metrics: CircuitMetrics = None):
        """상태 저장"""
        try:
            redis = await get_redis_manager()
            
            if metrics is None:
                metrics = await self._get_metrics()
            
            metrics.current_state = state
            metrics.state_changed_at = time.time()
            
            state_data = {
                'state': state.value,
                'changed_at': metrics.state_changed_at,
                'metrics': asdict(metrics)
            }
            
            # Redis에 저장 (TTL: 1시간)
            await redis.set('cache', self.redis_key, state_data, ttl=3600)
            
            # 로컬 캐시 업데이트
            self._local_cache = state_data
            self._last_cache_update = time.time()
            
            logger.info(f"Circuit Breaker 상태 변경: {self.name} -> {state.value}")
            
        except Exception as e:
            logger.error(f"Circuit Breaker 상태 저장 실패: {self.name}", error=e)
    
    async def _get_metrics(self) -> CircuitMetrics:
        """메트릭 조회"""
        try:
            redis = await get_redis_manager()
            metrics_data = await redis.get('metrics', self.metrics_key)
            
            if metrics_data:
                data = json.loads(metrics_data) if isinstance(metrics_data, str) else metrics_data
                return CircuitMetrics(**data)
            else:
                return CircuitMetrics()
                
        except Exception as e:
            logger.error(f"Circuit Breaker 메트릭 조회 실패: {self.name}", error=e)
            return CircuitMetrics()
    
    async def _update_metrics(self, success: bool):
        """메트릭 업데이트"""
        try:
            redis = await get_redis_manager()
            metrics = await self._get_metrics()
            
            current_time = time.time()
            metrics.total_requests += 1
            
            if success:
                metrics.successful_requests += 1
                metrics.last_success_time = current_time
            else:
                metrics.failed_requests += 1
                metrics.last_failure_time = current_time
            
            # 슬라이딩 윈도우 업데이트
            await self._update_sliding_window(success, current_time)
            
            # Redis에 저장
            await redis.set('metrics', self.metrics_key, asdict(metrics), ttl=3600)
            
        except Exception as e:
            logger.error(f"Circuit Breaker 메트릭 업데이트 실패: {self.name}", error=e)
    
    async def _update_sliding_window(self, success: bool, timestamp: float):
        """슬라이딩 윈도우 업데이트"""
        try:
            redis = await get_redis_manager()
            
            # 윈도우에 결과 추가 (timestamp:result 형태)
            window_data = f"{timestamp}:{1 if success else 0}"
            
            # Redis List에 추가
            await redis.client.lpush(self.window_key, window_data)
            
            # 윈도우 크기 제한
            await redis.client.ltrim(self.window_key, 0, self.config.window_size - 1)
            
            # TTL 설정
            await redis.client.expire(self.window_key, 3600)
            
        except Exception as e:
            logger.error(f"슬라이딩 윈도우 업데이트 실패: {self.name}", error=e)
    
    async def _calculate_failure_rate(self) -> float:
        """최근 실패율 계산"""
        try:
            redis = await get_redis_manager()
            
            # 최근 윈도우 데이터 조회
            window_data = await redis.client.lrange(self.window_key, 0, -1)
            
            if not window_data or len(window_data) < self.config.minimum_request_count:
                return 0.0
            
            # 실패율 계산
            failures = sum(1 for item in window_data 
                          if item.decode("utf-8").split(':')[1] == '0')
            
            return failures / len(window_data)
            
        except Exception as e:
            logger.error(f"실패율 계산 실패: {self.name}", error=e)
            return 0.0
    
    async def _should_trip(self) -> bool:
        """Circuit Breaker를 열어야 하는지 판단"""
        failure_rate = await self._calculate_failure_rate()
        
        return (failure_rate >= self.config.failure_rate_threshold and
                failure_rate > 0)
    
    async def _should_attempt_reset(self) -> bool:
        """Circuit Breaker를 HALF_OPEN으로 전환할지 판단"""
        metrics = await self._get_metrics()
        current_time = time.time()
        
        return (current_time - metrics.state_changed_at) >= self.config.timeout
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Circuit Breaker를 통한 함수 호출"""
        state = await self._get_state()
        
        # OPEN 상태 처리
        if state == CircuitState.OPEN:
            if await self._should_attempt_reset():
                await self._set_state(CircuitState.HALF_OPEN)
                return await self._execute_call(func, *args, **kwargs)
            else:
                # 폴백 함수 실행
                if self.fallback_func:
                    logger.info(f"Circuit Breaker OPEN: 폴백 함수 실행 - {self.name}")
                    return await self.fallback_func(*args, **kwargs) if asyncio.iscoroutinefunction(self.fallback_func) else self.fallback_func(*args, **kwargs)
                else:
                    raise CircuitBreakerOpenException(f"Circuit Breaker is OPEN: {self.name}")
        
        # CLOSED 또는 HALF_OPEN 상태 처리
        return await self._execute_call(func, *args, **kwargs)
    
    async def _execute_call(self, func: Callable, *args, **kwargs) -> Any:
        """실제 함수 실행"""
        start_time = time.time()
        
        try:
            # 함수 실행
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # 성공 처리
            await self._handle_success()
            
            # 성능 로깅
            duration = (time.time() - start_time) * 1000
            logger.info(f"Circuit Breaker 호출 성공: {self.name} ({duration:.2f}ms)")
            
            return result
            
        except Exception as e:
            # 실패 처리
            await self._handle_failure(e)
            
            # 에러 로깅
            duration = (time.time() - start_time) * 1000
            logger.error(f"Circuit Breaker 호출 실패: {self.name} ({duration:.2f}ms)", error=e)
            
            raise e
    
    async def _handle_success(self):
        """성공 처리"""
        state = await self._get_state()
        await self._update_metrics(success=True)
        
        if state == CircuitState.HALF_OPEN:
            metrics = await self._get_metrics()
            
            # 최근 성공 횟수 확인
            recent_success_count = await self._count_recent_successes()
            
            if recent_success_count >= self.config.success_threshold:
                await self._set_state(CircuitState.CLOSED, metrics)
    
    async def _handle_failure(self, error: Exception):
        """실패 처리"""
        state = await self._get_state()
        await self._update_metrics(success=False)
        
        if state == CircuitState.CLOSED:
            if await self._should_trip():
                metrics = await self._get_metrics()
                metrics.circuit_open_count += 1
                await self._set_state(CircuitState.OPEN, metrics)
        
        elif state == CircuitState.HALF_OPEN:
            metrics = await self._get_metrics()
            await self._set_state(CircuitState.OPEN, metrics)
    
    async def _count_recent_successes(self) -> int:
        """최근 성공 횟수 계산"""
        try:
            redis = await get_redis_manager()
            
            # 최근 데이터만 확인 (성공 임계값 개수만큼)
            recent_data = await redis.client.lrange(
                self.window_key, 0, self.config.success_threshold - 1
            )
            
            return sum(1 for item in recent_data 
                      if item.decode("utf-8").split(':')[1] == '1')
            
        except Exception as e:
            logger.error(f"최근 성공 횟수 계산 실패: {self.name}", error=e)
            return 0
    
    @asynccontextmanager
    async def protect(self):
        """컨텍스트 매니저 형태의 Circuit Breaker"""
        state = await self._get_state()
        
        if state == CircuitState.OPEN:
            if not await self._should_attempt_reset():
                if self.fallback_func:
                    yield self.fallback_func
                    return
                else:
                    raise CircuitBreakerOpenException(f"Circuit Breaker is OPEN: {self.name}")
            else:
                await self._set_state(CircuitState.HALF_OPEN)
        
        try:
            yield None
            await self._handle_success()
        except Exception as e:
            await self._handle_failure(e)
            raise
    
    async def get_status(self) -> Dict[str, Any]:
        """Circuit Breaker 상태 반환"""
        state = await self._get_state()
        metrics = await self._get_metrics()
        failure_rate = await self._calculate_failure_rate()
        
        return {
            "name": self.name,
            "state": state.value,
            "config": asdict(self.config),
            "metrics": asdict(metrics),
            "failure_rate": failure_rate,
            "can_execute": state != CircuitState.OPEN or await self._should_attempt_reset()
        }
    
    async def reset(self):
        """Circuit Breaker 수동 리셋"""
        await self._set_state(CircuitState.CLOSED)
        
        # 메트릭 초기화
        try:
            redis = await get_redis_manager()
            await redis.delete('metrics', self.metrics_key)
            await redis.client.delete(self.window_key)
            
            logger.info(f"Circuit Breaker 수동 리셋: {self.name}")
            
        except Exception as e:
            logger.error(f"Circuit Breaker 리셋 실패: {self.name}", error=e)

class CircuitBreakerOpenException(Exception):
    """Circuit Breaker가 열린 상태에서 발생하는 예외"""
    pass

class CircuitBreakerManager:
    """Circuit Breaker 관리자"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    def util_get_circuit_breaker(self, 
                           name: str, 
                           config: CircuitBreakerConfig = None,
                           fallback_func: Optional[Callable] = None) -> CircuitBreaker:
        """Circuit Breaker 인스턴스 반환"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name, config, fallback_func)
        
        return self.circuit_breakers[name]
    
    async def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """모든 Circuit Breaker 상태 반환"""
        status = {}
        
        for name, cb in self.circuit_breakers.items():
            status[name] = await cb.get_status()
        
        return status
    
    async def reset_all(self):
        """모든 Circuit Breaker 리셋"""
        for cb in self.circuit_breakers.values():
            await cb.reset()

# 전역 매니저 인스턴스
_circuit_breaker_manager = CircuitBreakerManager()

def util_get_circuit_breaker(name: str, 
                       config: CircuitBreakerConfig = None,
                       fallback_func: Optional[Callable] = None) -> CircuitBreaker:
    """Circuit Breaker 인스턴스 반환"""
    return _circuit_breaker_manager.util_get_circuit_breaker(name, config, fallback_func)

async def get_all_circuit_breaker_status() -> Dict[str, Dict[str, Any]]:
    """모든 Circuit Breaker 상태 반환"""
    return await _circuit_breaker_manager.get_all_status() 