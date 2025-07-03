#!/usr/bin/env python3
"""
API 계약 테스트 스크립트
각 마이크로서비스의 API가 명세와 일치하는지 검증
"""

import requests
import json
import time
from pathlib import Path

def check_service_status(service_name, port):
    """서비스 상태 확인"""
    try:
        url = f'http://localhost:{port}/health'
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return True
    except:
        pass
    return False

def load_schema(schema_name):
    """JSON Schema 로드"""
    schema_path = Path('schemas') / f'{schema_name}.json'
    if not schema_path.exists():
        return None
    with open(schema_path, encoding='utf-8') as f:
        return json.load(f)

def test_audio_preprocess():
    """오디오 전처리 API 테스트"""
    print("🔍 오디오 전처리 API 테스트 중...")
    
    if not check_service_status("audio-processor", 8001):
        print("❌ 오디오 처리 서비스가 실행되지 않았습니다.")
        print("   해결방법: docker-compose up audio-processor -d")
        return False
    
    url = 'http://localhost:8001/preprocess'
    payload = {
        "audio_data": "dGVzdA==",  # "test" in base64
        "sample_rate": 16000,
        "format": "wav"
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=30)
        assert resp.status_code == 200
        data = resp.json()
        
        # 명세 검증
        assert 'status' in data, "응답에 'status' 필드가 없습니다"
        assert data['status'] in ['success', 'error'], "status는 'success' 또는 'error'여야 합니다"
        
        if data['status'] == 'success':
            assert 'data' in data, "성공 응답에 'data' 필드가 없습니다"
        
        print("✅ 오디오 전처리 API 테스트 통과")
        return True
        
    except Exception as e:
        print(f"❌ 오디오 전처리 API 테스트 실패: {e}")
        return False

def test_text_analyze():
    """텍스트 분석 API 테스트"""
    print("🔍 텍스트 분석 API 테스트 중...")
    
    if not check_service_status("text-analyzer", 8002):
        print("❌ 텍스트 분석 서비스가 실행되지 않았습니다.")
        print("   해결방법: docker-compose up text-analyzer -d")
        return False
    
    url = 'http://localhost:8002/analyze'
    payload = {
        "text": "이것은 테스트 문장입니다.",
        "language": "ko"
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=30)
        assert resp.status_code == 200
        data = resp.json()
        
        # 명세 검증
        assert 'status' in data, "응답에 'status' 필드가 없습니다"
        assert data['status'] in ['success', 'error'], "status는 'success' 또는 'error'여야 합니다"
        
        if data['status'] == 'success':
            assert 'data' in data, "성공 응답에 'data' 필드가 없습니다"
        
        print("✅ 텍스트 분석 API 테스트 통과")
        return True
        
    except Exception as e:
        print(f"❌ 텍스트 분석 API 테스트 실패: {e}")
        return False

def test_db_health():
    """데이터베이스 헬스체크 API 테스트"""
    print("🔍 데이터베이스 헬스체크 API 테스트 중...")
    
    if not check_service_status("database-service", 8003):
        print("❌ 데이터베이스 서비스가 실행되지 않았습니다.")
        print("   해결방법: docker-compose up database-service -d")
        return False
    
    url = 'http://localhost:8003/health'
    
    try:
        resp = requests.get(url, timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        
        # 명세 검증
        assert 'status' in data, "응답에 'status' 필드가 없습니다"
        assert data['status'] in ['success', 'error'], "status는 'success' 또는 'error'여야 합니다"
        
        print("✅ 데이터베이스 헬스체크 API 테스트 통과")
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 헬스체크 API 테스트 실패: {e}")
        return False

def test_gateway_process():
    """게이트웨이 통합 처리 API 테스트"""
    print("🔍 게이트웨이 통합 처리 API 테스트 중...")
    
    if not check_service_status("gateway", 8000):
        print("❌ 게이트웨이 서비스가 실행되지 않았습니다.")
        print("   해결방법: docker-compose up gateway -d")
        return False
    
    url = 'http://localhost:8000/process'
    payload = {
        "audio_data": "dGVzdA==",  # "test" in base64
        "sample_rate": 16000,
        "format": "wav"
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=60)  # 통합 처리이므로 더 긴 타임아웃
        assert resp.status_code == 200
        data = resp.json()
        
        # 명세 검증
        assert 'status' in data, "응답에 'status' 필드가 없습니다"
        assert data['status'] in ['success', 'error'], "status는 'success' 또는 'error'여야 합니다"
        
        if data['status'] == 'success':
            assert 'data' in data, "성공 응답에 'data' 필드가 없습니다"
        
        print("✅ 게이트웨이 통합 처리 API 테스트 통과")
        return True
        
    except Exception as e:
        print(f"❌ 게이트웨이 통합 처리 API 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 실행"""
    print("🚀 Callytics API 계약 테스트 시작")
    print("=" * 50)
    
    # 서비스 상태 사전 확인
    print("\n📋 서비스 상태 확인 중...")
    services = [
        ("오디오 처리", 8001),
        ("텍스트 분석", 8002), 
        ("데이터베이스", 8003),
        ("게이트웨이", 8000)
    ]
    
    all_services_running = True
    for service_name, port in services:
        if check_service_status(service_name, port):
            print(f"✅ {service_name} 서비스 실행 중 (포트 {port})")
        else:
            print(f"❌ {service_name} 서비스 미실행 (포트 {port})")
            all_services_running = False
    
    if not all_services_running:
        print("\n⚠️  일부 서비스가 실행되지 않았습니다.")
        print("   해결방법: docker-compose up -d")
        print("   또는 run_api_tests.bat 실행")
        return
    
    print("\n🧪 API 테스트 실행 중...")
    
    # 각 API 테스트 실행
    tests = [
        test_audio_preprocess,
        test_text_analyze,
        test_db_health,
        test_gateway_process
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    # 결과 요약
    print("=" * 50)
    print(f"📊 테스트 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("🎉 모든 API 계약 테스트 통과!")
        print("   명세와 정책이 실제 서비스에 잘 적용되었습니다.")
    else:
        print("⚠️  일부 테스트가 실패했습니다.")
        print("   API 명세와 실제 구현을 확인해주세요.")

if __name__ == '__main__':
    main() 