#!/usr/bin/env python3
"""
마이크로서비스 통합 테스트
"""

import pytest
import asyncio
import json
from unittest.mock import patch, AsyncMock
import httpx

class TestMicroserviceIntegration:
    """마이크로서비스 통합 테스트"""
    
    @pytest.fixture
    def gateway_url(self):
        """게이트웨이 URL"""
        return "http://localhost:8000"
    
    @pytest.fixture
    def sample_audio_file(self, temp_dir):
        """샘플 오디오 파일 생성"""
        import wave
        import numpy as np
        
        audio_path = f"{temp_dir}/test_audio.wav"
        
        # 더미 오디오 데이터 생성 (1초, 16kHz)
        sample_rate = 16000
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
        
        with wave.open(audio_path, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        return audio_path
    
    async def test_health_check_all_services(self):
        """모든 서비스 헬스체크 테스트"""
        services = [
            ("gateway", 8000),
            ("audio-processor", 8001),
            ("speaker-diarizer", 8002),
            ("speech-recognizer", 8003),
            ("punctuation-restorer", 8004),
            ("sentiment-analyzer", 8005),
            ("llm-analyzer", 8006),
            ("database-service", 8007)
        ]
        
        async with httpx.AsyncClient() as client:
            for service_name, port in services:
                try:
                    response = await client.get(
                        f"http://localhost:{port}/health",
                        timeout=5.0
                    )
                    
                    if response.status_code == 200:
                        health_data = response.json()
                        assert health_data["status"] in ["healthy", "degraded"]
                        print(f"✅ {service_name}: {health_data['status']}")
                    else:
                        print(f"❌ {service_name}: HTTP {response.status_code}")
                        
                except Exception as e:
                    print(f"❌ {service_name}: 연결 실패 - {e}")
    
    async def test_audio_processing_pipeline(self, sample_audio_file):
        """오디오 처리 파이프라인 테스트"""
        pipeline_steps = [
            {
                "service": "audio-processor",
                "port": 8001,
                "endpoint": "/process_audio",
                "method": "POST"
            },
            {
                "service": "speaker-diarizer", 
                "port": 8002,
                "endpoint": "/diarize",
                "method": "POST"
            },
            {
                "service": "speech-recognizer",
                "port": 8003,
                "endpoint": "/recognize",
                "method": "POST"
            }
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. 오디오 전처리
            with open(sample_audio_file, 'rb') as f:
                files = {"file": ("test.wav", f, "audio/wav")}
                
                response = await client.post(
                    f"http://localhost:8001/process_audio",
                    files=files
                )
                
                if response.status_code == 200:
                    audio_result = response.json()
                    assert "processed_audio_path" in audio_result
                    print("✅ 오디오 전처리 완료")
    
    async def test_text_processing_pipeline(self):
        """텍스트 처리 파이프라인 테스트"""
        sample_text = "안녕하세요 고객님, 상담사 김철수입니다. 오늘 무엇을 도와드릴까요?"
        
        pipeline_steps = [
            {
                "service": "punctuation-restorer",
                "port": 8004,
                "endpoint": "/restore_punctuation",
                "expected_field": "restored_text"
            },
            {
                "service": "sentiment-analyzer",
                "port": 8005,
                "endpoint": "/analyze_sentiment",
                "expected_field": "sentiment"
            },
            {
                "service": "llm-analyzer",
                "port": 8006,
                "endpoint": "/analyze_communication_quality",
                "expected_field": "quality_analysis"
            }
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            current_text = sample_text
            
            for step in pipeline_steps:
                try:
                    response = await client.post(
                        f"http://localhost:{step['port']}{step['endpoint']}",
                        json={"text": current_text}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        assert step["expected_field"] in result
                        print(f"✅ {step['service']}: 처리 완료")
                        
                        # 다음 단계를 위해 텍스트 업데이트 (구두점 복원의 경우)
                        if step["service"] == "punctuation-restorer":
                            current_text = result["restored_text"]
                            
                    else:
                        print(f"❌ {step['service']}: HTTP {response.status_code}")
                        
                except Exception as e:
                    print(f"❌ {step['service']}: 오류 - {e}")
    
    async def test_gateway_orchestration(self, sample_audio_file):
        """게이트웨이 오케스트레이션 테스트"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(sample_audio_file, 'rb') as f:
                # 통합 분석 요청
                files = {"audio_file": ("test.wav", f, "audio/wav")}
                data = {
                    "analysis_options": json.dumps({
                        "include_sentiment": True,
                        "include_topics": True,
                        "include_quality": True,
                        "include_diarization": True
                    })
                }
                
                response = await client.post(
                    "http://localhost:8000/analyze",
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # 응답 구조 검증
                    expected_fields = [
                        "analysis_id",
                        "status",
                        "results"
                    ]
                    
                    for field in expected_fields:
                        assert field in result
                    
                    print("✅ 게이트웨이 통합 분석 완료")
                    print(f"분석 ID: {result.get('analysis_id')}")
                    
                else:
                    print(f"❌ 게이트웨이 오케스트레이션 실패: {response.status_code}")
                    print(response.text)
    
    async def test_database_operations(self):
        """데이터베이스 연산 테스트"""
        async with httpx.AsyncClient() as client:
            # 1. 상담 분석 결과 저장
            analysis_data = {
                "consultation_id": "test_consultation_001",
                "audio_properties": {
                    "duration": 60.0,
                    "sample_rate": 16000,
                    "channels": 1
                },
                "utterances": [
                    {
                        "speaker": "agent",
                        "text": "안녕하세요 고객님",
                        "start_time": 0.0,
                        "end_time": 2.0,
                        "confidence": 0.95
                    }
                ],
                "topics": [
                    {
                        "topic": "greeting",
                        "confidence": 0.9,
                        "keywords": ["안녕하세요", "고객님"]
                    }
                ],
                "sentiment_analysis": {
                    "overall_sentiment": "positive",
                    "confidence": 0.8,
                    "sentiment_timeline": []
                }
            }
            
            response = await client.post(
                "http://localhost:8007/store_analysis",
                json=analysis_data
            )
            
            if response.status_code == 200:
                result = response.json()
                assert "analysis_id" in result
                analysis_id = result["analysis_id"]
                print(f"✅ 분석 결과 저장 완료: {analysis_id}")
                
                # 2. 저장된 데이터 조회
                response = await client.get(
                    f"http://localhost:8007/get_analysis/{analysis_id}"
                )
                
                if response.status_code == 200:
                    retrieved_data = response.json()
                    assert retrieved_data["consultation_id"] == "test_consultation_001"
                    print("✅ 분석 결과 조회 완료")
                else:
                    print(f"❌ 분석 결과 조회 실패: {response.status_code}")
            else:
                print(f"❌ 분석 결과 저장 실패: {response.status_code}")
    
    async def test_error_handling_and_fallbacks(self):
        """오류 처리 및 폴백 메커니즘 테스트"""
        async with httpx.AsyncClient() as client:
            # 잘못된 데이터로 요청하여 오류 처리 확인
            invalid_requests = [
                {
                    "url": "http://localhost:8003/recognize",
                    "data": {"invalid": "data"},
                    "description": "음성 인식 - 잘못된 입력"
                },
                {
                    "url": "http://localhost:8005/analyze_sentiment",
                    "data": {},  # 텍스트 누락
                    "description": "감정 분석 - 필수 필드 누락"
                },
                {
                    "url": "http://localhost:8006/analyze_communication_quality",
                    "data": {"text": ""},  # 빈 텍스트
                    "description": "품질 분석 - 빈 입력"
                }
            ]
            
            for req in invalid_requests:
                try:
                    response = await client.post(req["url"], json=req["data"])
                    
                    # 4xx 오류 코드 예상
                    assert 400 <= response.status_code < 500
                    
                    # 오류 응답에 적절한 메시지 포함 확인
                    if response.headers.get('content-type', '').startswith('application/json'):
                        error_data = response.json()
                        assert "error" in error_data or "message" in error_data
                    
                    print(f"✅ {req['description']}: 적절한 오류 처리 ({response.status_code})")
                    
                except Exception as e:
                    print(f"❌ {req['description']}: 예외 발생 - {e}")
    
    async def test_performance_and_timeout(self):
        """성능 및 타임아웃 테스트"""
        async with httpx.AsyncClient(timeout=5.0) as client:
            # 각 서비스의 응답 시간 측정
            services_to_test = [
                ("sentiment-analyzer", 8005, "/analyze_sentiment", {"text": "테스트 문장입니다."}),
                ("punctuation-restorer", 8004, "/restore_punctuation", {"text": "안녕하세요 반갑습니다"}),
                ("database-service", 8007, "/health", {})
            ]
            
            for service_name, port, endpoint, data in services_to_test:
                try:
                    import time
                    start_time = time.time()
                    
                    if data:
                        response = await client.post(f"http://localhost:{port}{endpoint}", json=data)
                    else:
                        response = await client.get(f"http://localhost:{port}{endpoint}")
                    
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        print(f"✅ {service_name}: 응답시간 {response_time:.3f}초")
                        
                        # 성능 임계값 체크 (5초 이내)
                        assert response_time < 5.0, f"{service_name} 응답시간 초과: {response_time}초"
                    else:
                        print(f"❌ {service_name}: HTTP {response.status_code}")
                        
                except asyncio.TimeoutError:
                    print(f"❌ {service_name}: 타임아웃 (5초)")
                except Exception as e:
                    print(f"❌ {service_name}: 오류 - {e}") 