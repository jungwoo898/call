#!/usr/bin/env python3
"""
pytest 설정 및 공통 fixture
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock
from typing import AsyncGenerator, Generator

# 테스트용 환경변수 설정
os.environ.update({
    "ENVIRONMENT": "test",
    "REDIS_HOST": "localhost",
    "REDIS_PORT": "6379",
    "REDIS_DB": "1",  # 테스트용 DB
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_DB": "callytics_test",
    "POSTGRES_USER": "test_user",
    "POSTGRES_PASSWORD": "test_password",
    "JWT_SECRET_KEY": "test-secret-key-for-testing-only",
    "SESSION_DURATION_HOURS": "1"
})

@pytest.fixture(scope="session")
def event_loop():
    """이벤트 루프 fixture"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def temp_dir():
    """임시 디렉토리 fixture"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def mock_redis():
    """Mock Redis 클라이언트"""
    redis_mock = AsyncMock()
    redis_mock.ping.return_value = True
    redis_mock.get.return_value = None
    redis_mock.set.return_value = True
    redis_mock.delete.return_value = True
    redis_mock.exists.return_value = False
    
    return redis_mock

@pytest.fixture
def mock_postgres():
    """Mock PostgreSQL 연결"""
    conn_mock = AsyncMock()
    conn_mock.fetchval.return_value = 1
    conn_mock.fetch.return_value = []
    conn_mock.fetchrow.return_value = None
    conn_mock.execute.return_value = "INSERT 0 1"
    
    pool_mock = AsyncMock()
    pool_mock.acquire.return_value.__aenter__.return_value = conn_mock
    pool_mock.acquire.return_value.__aexit__.return_value = None
    
    return pool_mock

@pytest.fixture
def sample_audio_data():
    """샘플 오디오 데이터"""
    return {
        "file_path": "/test/sample.wav",
        "duration": 60.0,
        "sample_rate": 16000,
        "channels": 1,
        "format": "wav"
    }

@pytest.fixture
def sample_text_data():
    """샘플 텍스트 데이터"""
    return {
        "text": "안녕하세요. 상담사입니다. 무엇을 도와드릴까요?",
        "speaker": "agent",
        "timestamp": 0.0
    }

@pytest.fixture
def sample_analysis_result():
    """샘플 분석 결과"""
    return {
        "sentiment": {
            "overall": "positive",
            "confidence": 0.85,
            "scores": {
                "positive": 0.85,
                "negative": 0.10,
                "neutral": 0.05
            }
        },
        "topics": [
            {"topic": "greeting", "confidence": 0.9},
            {"topic": "inquiry", "confidence": 0.7}
        ],
        "communication_quality": {
            "empathy_score": 0.8,
            "professionalism_score": 0.9,
            "clarity_score": 0.85
        }
    }

@pytest.fixture
async def test_client():
    """테스트용 HTTP 클라이언트"""
    from httpx import AsyncClient
    async with AsyncClient() as client:
        yield client

@pytest.fixture
def jwt_token():
    """테스트용 JWT 토큰"""
    import jwt
    payload = {
        "user_id": "test_user",
        "username": "test_agent",
        "exp": 9999999999  # 먼 미래 시간
    }
    return jwt.encode(payload, "test-secret-key-for-testing-only", algorithm="HS256") 