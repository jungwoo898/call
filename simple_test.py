#!/usr/bin/env python3
"""
간단한 Callytics 기능 테스트 스크립트
"""

import sys
import os

def test_imports():
    """기본 라이브러리 import 테스트"""
    print("=== 라이브러리 Import 테스트 ===")
    
    try:
        import torch
        print(f"✅ PyTorch: {torch.__version__}")
        print(f"   CUDA 사용 가능: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"   CUDA 버전: {torch.version.cuda}")
            print(f"   GPU 개수: {torch.cuda.device_count()}")
    except Exception as e:
        print(f"❌ PyTorch import 실패: {e}")
    
    try:
        import torchaudio
        print(f"✅ TorchAudio: {torchaudio.__version__}")
    except Exception as e:
        print(f"❌ TorchAudio import 실패: {e}")
    
    try:
        import transformers
        print(f"✅ Transformers: {transformers.__version__}")
    except Exception as e:
        print(f"❌ Transformers import 실패: {e}")
    
    try:
        import fastapi
        print(f"✅ FastAPI: {fastapi.__version__}")
    except Exception as e:
        print(f"❌ FastAPI import 실패: {e}")
    
    try:
        import nemo
        print(f"✅ NeMo: {nemo.__version__}")
    except Exception as e:
        print(f"❌ NeMo import 실패: {e}")

def test_audio_file():
    """오디오 파일 존재 확인"""
    print("\n=== 오디오 파일 확인 ===")
    
    audio_file = "audio/40186.mp3"
    if os.path.exists(audio_file):
        print(f"✅ 오디오 파일 존재: {audio_file}")
        file_size = os.path.getsize(audio_file)
        print(f"   파일 크기: {file_size / (1024*1024):.2f} MB")
    else:
        print(f"❌ 오디오 파일 없음: {audio_file}")
        print("   사용 가능한 오디오 파일:")
        if os.path.exists("audio"):
            for file in os.listdir("audio"):
                if file.endswith(('.mp3', '.wav', '.flac')):
                    print(f"   - {file}")

def test_config_files():
    """설정 파일 확인"""
    print("\n=== 설정 파일 확인 ===")
    
    config_files = [
        "config/config.yaml",
        "config/prompt.yaml",
        "config/nemo/diar_infer_telephonic.yaml"
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ 설정 파일 존재: {config_file}")
        else:
            print(f"❌ 설정 파일 없음: {config_file}")

def test_database():
    """데이터베이스 확인"""
    print("\n=== 데이터베이스 확인 ===")
    
    db_files = [
        "Callytics_new.sqlite",
        "Callytics_docker.sqlite"
    ]
    
    for db_file in db_files:
        if os.path.exists(db_file):
            print(f"✅ 데이터베이스 존재: {db_file}")
            file_size = os.path.getsize(db_file)
            print(f"   파일 크기: {file_size / 1024:.2f} KB")
        else:
            print(f"❌ 데이터베이스 없음: {db_file}")

def main():
    """메인 테스트 함수"""
    print("🚀 Callytics 기본 기능 테스트 시작")
    print("=" * 50)
    
    test_imports()
    test_audio_file()
    test_config_files()
    test_database()
    
    print("\n" + "=" * 50)
    print("✅ 기본 테스트 완료")

if __name__ == "__main__":
    main() 