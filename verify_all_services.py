#!/usr/bin/env python3
"""
모든 마이크로서비스 호환성 통합 검증 스크립트
"""

import sys
import subprocess
import os

def run_verification_script(script_name, service_name):
    """개별 서비스 검증 스크립트 실행"""
    
    print(f"\n{'='*60}")
    print(f"🔍 {service_name} 서비스 검증 시작")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✅ {service_name} 서비스 검증 성공!")
            return True
        else:
            print(f"❌ {service_name} 서비스 검증 실패!")
            print(f"에러 출력: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {service_name} 서비스 검증 시간 초과!")
        return False
    except Exception as e:
        print(f"💥 {service_name} 서비스 검증 중 예외 발생: {e}")
        return False

def main():
    """모든 서비스 검증 실행"""
    
    print("🚀 마이크로서비스 호환성 통합 검증 시작")
    print("=" * 60)
    
    # 검증할 서비스 목록
    services = [
        ("verify_audio_processor.py", "Audio Processor"),
        ("verify_speaker_diarizer.py", "Speaker Diarizer"),
        ("verify_speech_recognizer.py", "Speech Recognizer"),
        ("verify_punctuation_restorer.py", "Punctuation Restorer"),
        ("verify_sentiment_analyzer.py", "Sentiment Analyzer"),
        ("verify_llm_analyzer.py", "LLM Analyzer"),
        ("verify_database_service.py", "Database Service")
    ]
    
    success_count = 0
    total_count = len(services)
    
    for script_name, service_name in services:
        if os.path.exists(script_name):
            if run_verification_script(script_name, service_name):
                success_count += 1
        else:
            print(f"⚠️ {script_name} 파일이 존재하지 않습니다.")
    
    # 결과 요약
    print(f"\n{'='*60}")
    print("📊 검증 결과 요약")
    print(f"{'='*60}")
    print(f"총 서비스 수: {total_count}")
    print(f"성공한 서비스: {success_count}")
    print(f"실패한 서비스: {total_count - success_count}")
    
    if success_count == total_count:
        print("\n🎉 모든 서비스 호환성 검증 완료!")
        print("✅ 마이크로서비스 빌드 준비 완료!")
        return True
    else:
        print(f"\n💥 {total_count - success_count}개 서비스에서 문제 발생!")
        print("❌ 빌드 전 문제 해결 필요!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 