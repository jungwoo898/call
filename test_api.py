import requests
import json
import time

def test_api_endpoints():
    base_url = "http://localhost:8000"
    
    print("=== Callytics API 테스트 시작 ===")
    
    # 1. 헬스체크 테스트
    try:
        print("\n1. 헬스체크 테스트...")
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"   상태 코드: {response.status_code}")
        print(f"   응답: {response.text}")
    except Exception as e:
        print(f"   오류: {e}")
    
    # 2. 메트릭스 테스트
    try:
        print("\n2. 메트릭스 테스트...")
        response = requests.get(f"{base_url}/metrics", timeout=10)
        print(f"   상태 코드: {response.status_code}")
        print(f"   응답 길이: {len(response.text)} 문자")
    except Exception as e:
        print(f"   오류: {e}")
    
    # 3. 오디오 파일 분석 테스트
    try:
        print("\n3. 오디오 파일 분석 테스트...")
        # audio 폴더의 40186.mp3 파일을 분석
        with open("audio/40186.mp3", "rb") as f:
            files = {"file": ("40186.mp3", f, "audio/mpeg")}
            response = requests.post(f"{base_url}/analyze", files=files, timeout=60)
            print(f"   상태 코드: {response.status_code}")
            print(f"   응답: {response.text}")
    except Exception as e:
        print(f"   오류: {e}")
    
    # 4. 분석 결과 조회 테스트
    try:
        print("\n4. 분석 결과 조회 테스트...")
        response = requests.get(f"{base_url}/results", timeout=10)
        print(f"   상태 코드: {response.status_code}")
        print(f"   응답: {response.text}")
    except Exception as e:
        print(f"   오류: {e}")

if __name__ == "__main__":
    test_api_endpoints() 