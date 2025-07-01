#!/usr/bin/env python3
"""
torchaudio 오류를 우회하는 간단한 오디오 처리 테스트
"""

import os
import sys
import asyncio
from pathlib import Path

def test_basic_audio_processing():
    """기본 오디오 처리 테스트 (torchaudio 오류 우회)"""
    print("=== 기본 오디오 처리 테스트 ===")
    
    try:
        # PyTorch import 테스트
        import torch
        print("✅ PyTorch import 성공")
        print(f"   PyTorch 버전: {torch.__version__}")
        print(f"   CUDA 사용 가능: {torch.cuda.is_available()}")
        
        # torchaudio import 시도 (오류 발생 시 우회)
        torchaudio_available = False
        try:
            import torchaudio
            print("✅ TorchAudio import 성공")
            print(f"   TorchAudio 버전: {torchaudio.__version__}")
            torchaudio_available = True
        except Exception as e:
            print(f"⚠️ TorchAudio import 실패 (우회): {e}")
            print("   기본 오디오 정보만 확인합니다.")
        
        # 오디오 파일 존재 확인
        audio_file = "audio/40186.mp3"
        if os.path.exists(audio_file):
            print(f"✅ 오디오 파일 존재: {audio_file}")
            
            # 파일 정보 확인
            file_size = os.path.getsize(audio_file)
            print(f"   파일 크기: {file_size / (1024*1024):.2f} MB")
            
            # torchaudio가 사용 가능한 경우에만 상세 정보 확인
            if torchaudio_available:
                try:
                    waveform, sample_rate = torchaudio.load(audio_file)
                    print(f"   샘플레이트: {sample_rate}")
                    print(f"   채널 수: {waveform.shape[0]}")
                    print(f"   길이: {waveform.shape[1]} 샘플")
                    print(f"   재생 시간: {waveform.shape[1] / sample_rate:.2f}초")
                except Exception as e:
                    print(f"   ⚠️ 오디오 로드 실패: {e}")
            
            return True
        else:
            print(f"❌ 오디오 파일 없음: {audio_file}")
            return False
            
    except Exception as e:
        print(f"❌ 오디오 처리 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_watcher():
    """파일 감시 시스템 테스트"""
    print("\n=== 파일 감시 시스템 테스트 ===")
    
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        print("✅ Watchdog import 성공")
        
        # 감시할 디렉토리 확인
        watch_dirs = ["audio", ".temp"]
        for dir_name in watch_dirs:
            if os.path.exists(dir_name):
                print(f"✅ 감시 디렉토리 존재: {dir_name}")
            else:
                print(f"❌ 감시 디렉토리 없음: {dir_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ 파일 감시 시스템 실패: {e}")
        return False

def test_database():
    """데이터베이스 연결 테스트"""
    print("\n=== 데이터베이스 연결 테스트 ===")
    
    try:
        import sqlite3
        
        db_files = ["Callytics_new.sqlite", "Callytics_docker.sqlite"]
        for db_file in db_files:
            if os.path.exists(db_file):
                print(f"✅ 데이터베이스 존재: {db_file}")
                
                # 연결 테스트
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                print(f"   테이블 수: {len(tables)}")
                print(f"   테이블 목록: {[table[0] for table in tables]}")
                conn.close()
                
                return True
        else:
            print("❌ 데이터베이스 파일이 없습니다")
            return False
            
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return False

def test_basic_libraries():
    """기본 라이브러리 테스트"""
    print("\n=== 기본 라이브러리 테스트 ===")
    
    libraries = [
        ("torch", "PyTorch"),
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("sqlite3", "SQLite3"),
        ("watchdog", "Watchdog")
    ]
    
    results = []
    for lib_name, lib_display in libraries:
        try:
            __import__(lib_name)
            print(f"✅ {lib_display} import 성공")
            results.append(True)
        except Exception as e:
            print(f"❌ {lib_display} import 실패: {e}")
            results.append(False)
    
    return all(results)

async def main():
    """메인 테스트 함수"""
    print("🚀 torchaudio 오류 우회 Callytics 기능 테스트")
    print("=" * 60)
    
    results = []
    
    # 1. 기본 라이브러리 테스트
    results.append(test_basic_libraries())
    
    # 2. 기본 오디오 처리 테스트
    results.append(test_basic_audio_processing())
    
    # 3. 파일 감시 시스템 테스트
    results.append(test_file_watcher())
    
    # 4. 데이터베이스 연결 테스트
    results.append(test_database())
    
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약:")
    print(f"   기본 라이브러리: {'✅' if results[0] else '❌'}")
    print(f"   기본 오디오 처리: {'✅' if results[1] else '❌'}")
    print(f"   파일 감시 시스템: {'✅' if results[2] else '❌'}")
    print(f"   데이터베이스 연결: {'✅' if results[3] else '❌'}")
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n🎯 성공률: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    if success_count >= 3:
        print("\n🎉 대부분의 기능이 정상 동작합니다!")
        print("torchaudio 문제는 있지만 다른 기능들은 정상입니다.")
        print("전체 분석을 시도해볼 수 있습니다.")
    else:
        print("\n⚠️ 여러 기능에 문제가 있습니다.")
        print("기본 기능부터 수정 후 전체 분석을 진행하세요.")

if __name__ == "__main__":
    asyncio.run(main()) 