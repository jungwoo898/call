#!/usr/bin/env python3
"""
간단한 오디오 처리 테스트
"""

import os
import sys
import asyncio
from pathlib import Path

def test_basic_audio_processing():
    """기본 오디오 처리 테스트"""
    print("=== 기본 오디오 처리 테스트 ===")
    
    try:
        # 기본 라이브러리 import 테스트
        import torch
        import torchaudio
        print("✅ PyTorch & TorchAudio import 성공")
        
        # 오디오 파일 로드 테스트
        audio_file = "audio/40186.mp3"
        if os.path.exists(audio_file):
            print(f"✅ 오디오 파일 존재: {audio_file}")
            
            # 기본 오디오 정보 확인
            waveform, sample_rate = torchaudio.load(audio_file)
            print(f"   샘플레이트: {sample_rate}")
            print(f"   채널 수: {waveform.shape[0]}")
            print(f"   길이: {waveform.shape[1]} 샘플")
            print(f"   재생 시간: {waveform.shape[1] / sample_rate:.2f}초")
            
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
                conn.close()
                
                return True
        else:
            print("❌ 데이터베이스 파일이 없습니다")
            return False
            
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return False

async def main():
    """메인 테스트 함수"""
    print("🚀 간단한 Callytics 기능 테스트")
    print("=" * 50)
    
    results = []
    
    # 1. 기본 오디오 처리 테스트
    results.append(test_basic_audio_processing())
    
    # 2. 파일 감시 시스템 테스트
    results.append(test_file_watcher())
    
    # 3. 데이터베이스 연결 테스트
    results.append(test_database())
    
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약:")
    print(f"   기본 오디오 처리: {'✅' if results[0] else '❌'}")
    print(f"   파일 감시 시스템: {'✅' if results[1] else '❌'}")
    print(f"   데이터베이스 연결: {'✅' if results[2] else '❌'}")
    
    if all(results):
        print("\n🎉 모든 기본 기능이 정상 동작합니다!")
        print("이제 전체 분석을 시도할 수 있습니다.")
    else:
        print("\n⚠️ 일부 기능에 문제가 있습니다.")
        print("기본 기능부터 수정 후 전체 분석을 진행하세요.")

if __name__ == "__main__":
    asyncio.run(main()) 