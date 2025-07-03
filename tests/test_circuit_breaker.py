#!/usr/bin/env python3
"""
Circuit Breaker 테스트
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from src.utils.circuit_breaker import (
    CircuitBreaker, 
    CircuitBreakerConfig, 
    CircuitState,
    CircuitBreakerOpenException,
    get_circuit_breaker
)

class TestCircuitBreaker:
    """Circuit Breaker 테스트"""
    
    @pytest.fixture
    def circuit_config(self):
        """테스트용 Circuit Breaker 설정"""
        return CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout=1.0,
            window_size=10,
            minimum_request_count=5,
            failure_rate_threshold=0.6  # 60%
        )
    
    @pytest.fixture
    def circuit_breaker(self, circuit_config):
        """테스트용 Circuit Breaker"""
        return CircuitBreaker("test_service", circuit_config)
    
    async def test_circuit_breaker_closed_state_success(self, circuit_breaker):
        """CLOSED 상태에서 성공 호출 테스트"""
        async def success_func():
            return "success"
        
        result = await circuit_breaker.call(success_func)
        assert result == "success"
        
        status = await circuit_breaker.get_status()
        assert status["state"] == CircuitState.CLOSED.value
    
    async def test_circuit_breaker_trip_on_failures(self, circuit_breaker):
        """실패 임계값 초과 시 OPEN 상태 전환 테스트"""
        async def failing_func():
            raise Exception("Test failure")
        
        # 5번 실패 (minimum_request_count)
        for _ in range(5):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
        
        # 상태 확인 - 아직 CLOSED (실패율이 임계값 미달)
        status = await circuit_breaker.get_status()
        assert status["state"] == CircuitState.CLOSED.value
        
        # 2번 더 실패 (총 7번 실패, 실패율 70%)
        for _ in range(2):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
        
        # 상태 확인 - OPEN으로 전환되어야 함
        status = await circuit_breaker.get_status()
        assert status["state"] == CircuitState.OPEN.value
    
    async def test_circuit_breaker_open_state_blocks_calls(self, circuit_breaker):
        """OPEN 상태에서 호출 차단 테스트"""
        # Circuit Breaker를 OPEN 상태로 만들기
        async def failing_func():
            raise Exception("Test failure")
        
        for _ in range(7):  # 실패율 100%로 만들기
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
        
        # OPEN 상태에서 호출 시도
        async def success_func():
            return "success"
        
        with pytest.raises(CircuitBreakerOpenException):
            await circuit_breaker.call(success_func)
    
    async def test_circuit_breaker_fallback_function(self, circuit_config):
        """폴백 함수 테스트"""
        async def fallback_func():
            return "fallback_result"
        
        cb = CircuitBreaker("test_fallback", circuit_config, fallback_func)
        
        # Circuit Breaker를 OPEN 상태로 만들기
        async def failing_func():
            raise Exception("Test failure")
        
        for _ in range(7):
            with pytest.raises(Exception):
                await cb.call(failing_func)
        
        # OPEN 상태에서 폴백 함수 실행
        async def success_func():
            return "success"
        
        result = await cb.call(success_func)
        assert result == "fallback_result"
    
    async def test_circuit_breaker_half_open_recovery(self, circuit_breaker):
        """HALF_OPEN 상태에서 복구 테스트"""
        # Circuit Breaker를 OPEN 상태로 만들기
        async def failing_func():
            raise Exception("Test failure")
        
        for _ in range(7):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
        
        # 타임아웃 시뮬레이션 (실제로는 1초 대기하지 않고 mock 처리)
        with patch('time.time', side_effect=[0, 0, 0, 2.0]):  # 2초 후로 시뮬레이션
            async def success_func():
                return "success"
            
            # 첫 번째 성공 - HALF_OPEN 상태
            result = await circuit_breaker.call(success_func)
            assert result == "success"
            
            # 두 번째 성공 - CLOSED 상태로 전환
            result = await circuit_breaker.call(success_func)
            assert result == "success"
            
            status = await circuit_breaker.get_status()
            assert status["state"] == CircuitState.CLOSED.value
    
    async def test_circuit_breaker_reset(self, circuit_breaker):
        """Circuit Breaker 수동 리셋 테스트"""
        # Circuit Breaker를 OPEN 상태로 만들기
        async def failing_func():
            raise Exception("Test failure")
        
        for _ in range(7):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
        
        status = await circuit_breaker.get_status()
        assert status["state"] == CircuitState.OPEN.value
        
        # 수동 리셋
        circuit_breaker.reset()
        
        status = await circuit_breaker.get_status()
        assert status["state"] == CircuitState.CLOSED.value
    
    def test_get_circuit_breaker_singleton(self):
        """Circuit Breaker 싱글톤 패턴 테스트"""
        cb1 = get_circuit_breaker("singleton_test")
        cb2 = get_circuit_breaker("singleton_test")
        
        assert cb1 is cb2
    
    async def test_circuit_breaker_metrics(self, circuit_breaker):
        """Circuit Breaker 메트릭 테스트"""
        async def success_func():
            return "success"
        
        async def failing_func():
            raise Exception("Test failure")
        
        # 성공 3번, 실패 2번
        for _ in range(3):
            await circuit_breaker.call(success_func)
        
        for _ in range(2):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
        
        status = await circuit_breaker.get_status()
        metrics = status["metrics"]
        
        assert metrics["total_requests"] == 5
        assert metrics["successful_requests"] == 3
        assert metrics["failed_requests"] == 2
        assert status["failure_rate"] == 0.4  # 40% 실패율 