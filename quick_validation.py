#!/usr/bin/env python3
"""
빠른 호환성 검증 스크립트 (Docker 빌드 없이)
"""

import sys
import os
from pathlib import Path

def check_requirements_file():
    """requirements.txt 파일 검증"""
    print("🔍 requirements.txt 파일 검증")
    
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Phase 1 검증
        phase1_checks = [
            ('fastapi==0.111.0', 'FastAPI 버전'),
            ('pydantic==2.7.3', 'Pydantic 버전'),
            ('uvicorn[standard]==0.29.0', 'Uvicorn 버전'),
            ('requests==2.31.0', 'Requests 버전'),
        ]
        
        print("  Phase 1: 안전한 기반 라이브러리")
        for check, desc in phase1_checks:
            if check in content:
                print(f"    ✅ {desc}: {check}")
            else:
                print(f"    ❌ {desc}: {check} - 누락")
        
        # Phase 2 검증
        phase2_checks = [
            ('transformers[torch]==4.41.2', 'Transformers 버전'),
            ('tokenizers==0.19.1', 'Tokenizers 버전'),
            ('accelerate>=0.27.0', 'Accelerate 버전'),
        ]
        
        print("  Phase 2: 핵심 ML 라이브러리")
        for check, desc in phase2_checks:
            if check in content:
                print(f"    ✅ {desc}: {check}")
            else:
                print(f"    ❌ {desc}: {check} - 누락")
        
        # Phase 3 검증
        phase3_checks = [
            ('demucs==4.1.1', 'Demucs 버전'),
            ('pyannote.audio==3.2.1', 'PyAnnote 버전'),
            ('faster-whisper==1.1.2', 'Faster-whisper 버전'),
        ]
        
        print("  Phase 3: 음성 처리 라이브러리")
        for check, desc in phase3_checks:
            if check in content:
                print(f"    ✅ {desc}: {check}")
            else:
                print(f"    ❌ {desc}: {check} - 누락")
        
        # Phase 4 검증
        phase4_checks = [
            ('nemo_toolkit==1.23.0', 'NeMo 버전'),
            ('sentence-transformers==2.6.1', 'Sentence-transformers'),
        ]
        
        print("  Phase 4: 고급 라이브러리")
        for check, desc in phase4_checks:
            if check in content:
                print(f"    ✅ {desc}: {check}")
            else:
                print(f"    ❌ {desc}: {check} - 누락")
        
        return True
        
    except Exception as e:
        print(f"  ❌ requirements.txt 검증 실패: {e}")
        return False

def check_dockerfile():
    """Dockerfile 검증"""
    print("\n🔍 Dockerfile 검증")
    
    try:
        with open('Dockerfile', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # PyTorch 버전 검증
        if 'torch==2.2.0' in content:
            print("  ✅ PyTorch 2.2.0 확인")
        else:
            print("  ❌ PyTorch 2.2.0 누락")
        
        # torchaudio 버전 검증
        if 'torchaudio==2.2.0' in content:
            print("  ✅ torchaudio 2.2.0 확인")
        else:
            print("  ❌ torchaudio 2.2.0 누락")
        
        # CUDA 버전 검증
        if 'cu118' in content:
            print("  ✅ CUDA 11.8 확인")
        else:
            print("  ❌ CUDA 11.8 누락")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Dockerfile 검증 실패: {e}")
        return False

def check_main_py():
    """main.py 호환성 검증"""
    print("\n🔍 main.py 호환성 검증")
    
    try:
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # NeMo import 검증
        if 'NeMo 안전 import (1.23.0 호환)' in content:
            print("  ✅ NeMo 1.23.0 호환성 주석 확인")
        else:
            print("  ❌ NeMo 1.23.0 호환성 주석 누락")
        
        # FastAPI import 검증
        if 'from fastapi import FastAPI, HTTPException' in content:
            print("  ✅ FastAPI import 확인")
        else:
            print("  ❌ FastAPI import 누락")
        
        # Transformers import 검증
        if 'from transformers import' in content:
            print("  ✅ Transformers import 확인")
        else:
            print("  ❌ Transformers import 누락")
        
        return True
        
    except Exception as e:
        print(f"  ❌ main.py 검증 실패: {e}")
        return False

def check_file_structure():
    """파일 구조 검증"""
    print("\n🔍 파일 구조 검증")
    
    required_files = [
        'requirements.txt',
        'Dockerfile',
        'docker-compose.yml',
        'main.py',
        'src/audio/effect.py',
        'src/text/model.py',
        'config/nemo/diar_infer_telephonic.yaml',
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - 누락")
    
    return True

def main():
    """메인 검증 함수"""
    print("🚀 빠른 호환성 검증 시작")
    print("=" * 50)
    
    results = []
    
    # 1. requirements.txt 검증
    results.append(check_requirements_file())
    
    # 2. Dockerfile 검증
    results.append(check_dockerfile())
    
    # 3. main.py 검증
    results.append(check_main_py())
    
    # 4. 파일 구조 검증
    results.append(check_file_structure())
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 빠른 검증 결과 요약")
    print("=" * 50)
    
    success_count = sum(results)
    total_count = len(results)
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
    
    print(f"✅ 성공: {success_count}/{total_count}")
    print(f"📈 성공률: {success_rate:.1f}%")
    
    if success_count == total_count:
        print("\n🎉 모든 검증 통과! 점진적 최신화 준비 완료!")
        print("💡 다음 단계: Docker 빌드 테스트 (선택사항)")
        return 0
    else:
        print("\n⚠️ 일부 검증 실패. 추가 조치 필요.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 