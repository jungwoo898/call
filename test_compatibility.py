#!/usr/bin/env python3
"""
점진적 최신화 후 호환성 검증 스크립트
"""

import sys
import importlib
import traceback
from typing import Dict, List, Tuple

def test_import(module_name: str, package_name: str = None) -> Tuple[bool, str]:
    """모듈 import 테스트"""
    try:
        if package_name:
            module = importlib.import_module(package_name)
            version = getattr(module, '__version__', 'Unknown')
        else:
            module = importlib.import_module(module_name)
            version = getattr(module, '__version__', 'Unknown')
        return True, f"✅ {module_name}: {version}"
    except Exception as e:
        return False, f"❌ {module_name}: {str(e)}"

def test_critical_imports() -> Dict[str, List[str]]:
    """핵심 라이브러리 import 테스트"""
    results = {
        'success': [],
        'failed': []
    }
    
    # Phase 1: 안전한 기반 라이브러리
    print("🔍 Phase 1: 안전한 기반 라이브러리 테스트")
    phase1_modules = [
        ('fastapi', 'fastapi'),
        ('pydantic', 'pydantic'),
        ('uvicorn', 'uvicorn'),
        ('requests', 'requests'),
    ]
    
    for module_name, package_name in phase1_modules:
        success, message = test_import(module_name, package_name)
        if success:
            results['success'].append(message)
        else:
            results['failed'].append(message)
        print(f"  {message}")
    
    # Phase 2: 핵심 ML 라이브러리
    print("\n🔍 Phase 2: 핵심 ML 라이브러리 테스트")
    phase2_modules = [
        ('torch', 'torch'),
        ('torchaudio', 'torchaudio'),
        ('transformers', 'transformers'),
        ('tokenizers', 'tokenizers'),
        ('accelerate', 'accelerate'),
    ]
    
    for module_name, package_name in phase2_modules:
        success, message = test_import(module_name, package_name)
        if success:
            results['success'].append(message)
        else:
            results['failed'].append(message)
        print(f"  {message}")
    
    # Phase 3: 음성 처리 라이브러리
    print("\n🔍 Phase 3: 음성 처리 라이브러리 테스트")
    phase3_modules = [
        ('demucs', 'demucs'),
        ('pyannote.audio', 'pyannote.audio'),
        ('faster_whisper', 'faster_whisper'),
    ]
    
    for module_name, package_name in phase3_modules:
        success, message = test_import(module_name, package_name)
        if success:
            results['success'].append(message)
        else:
            results['failed'].append(message)
        print(f"  {message}")
    
    # Phase 4: 고급 라이브러리
    print("\n🔍 Phase 4: 고급 라이브러리 테스트")
    phase4_modules = [
        ('nemo', 'nemo'),
        ('sentence_transformers', 'sentence_transformers'),
    ]
    
    for module_name, package_name in phase4_modules:
        success, message = test_import(module_name, package_name)
        if success:
            results['success'].append(message)
        else:
            results['failed'].append(message)
        print(f"  {message}")
    
    return results

def test_nemo_specific_imports() -> Dict[str, List[str]]:
    """NeMo 특정 import 테스트"""
    results = {
        'success': [],
        'failed': []
    }
    
    print("\n🔍 NeMo 특정 import 테스트")
    
    # NeMo 1.23.0 호환성 테스트
    nemo_imports = [
        ('nemo.collections.asr.models.msdd_models', 'NeuralDiarizer'),
        ('nemo.collections.asr.models.clustering_diarizer', 'ClusteringDiarizer'),
    ]
    
    for module_path, class_name in nemo_imports:
        try:
            module = importlib.import_module(module_path)
            class_obj = getattr(module, class_name)
            results['success'].append(f"✅ {module_path}.{class_name}")
            print(f"  ✅ {module_path}.{class_name}")
        except Exception as e:
            results['failed'].append(f"❌ {module_path}.{class_name}: {str(e)}")
            print(f"  ❌ {module_path}.{class_name}: {str(e)}")
    
    return results

def test_cuda_compatibility() -> Dict[str, List[str]]:
    """CUDA 호환성 테스트"""
    results = {
        'success': [],
        'failed': []
    }
    
    print("\n🔍 CUDA 호환성 테스트")
    
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            cuda_version = torch.version.cuda
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0) if device_count > 0 else "No GPU"
            
            results['success'].append(f"✅ CUDA: {cuda_version}, Devices: {device_count}, GPU: {device_name}")
            print(f"  ✅ CUDA: {cuda_version}, Devices: {device_count}, GPU: {device_name}")
        else:
            results['failed'].append("❌ CUDA not available")
            print("  ❌ CUDA not available")
    except Exception as e:
        results['failed'].append(f"❌ CUDA test failed: {str(e)}")
        print(f"  ❌ CUDA test failed: {str(e)}")
    
    return results

def test_fastapi_compatibility() -> Dict[str, List[str]]:
    """FastAPI 호환성 테스트"""
    results = {
        'success': [],
        'failed': []
    }
    
    print("\n🔍 FastAPI 호환성 테스트")
    
    try:
        from fastapi import FastAPI
        from pydantic import BaseModel
        
        # Pydantic v2 호환성 테스트
        class TestModel(BaseModel):
            name: str
            value: int
        
        app = FastAPI()
        test_data = TestModel(name="test", value=42)
        
        results['success'].append("✅ FastAPI + Pydantic v2 호환성 확인")
        print("  ✅ FastAPI + Pydantic v2 호환성 확인")
    except Exception as e:
        results['failed'].append(f"❌ FastAPI 호환성 실패: {str(e)}")
        print(f"  ❌ FastAPI 호환성 실패: {str(e)}")
    
    return results

def main():
    """메인 테스트 함수"""
    print("🚀 점진적 최신화 호환성 검증 시작")
    print("=" * 50)
    
    all_results = {
        'success': [],
        'failed': []
    }
    
    # 1. 핵심 라이브러리 import 테스트
    results = test_critical_imports()
    all_results['success'].extend(results['success'])
    all_results['failed'].extend(results['failed'])
    
    # 2. NeMo 특정 import 테스트
    results = test_nemo_specific_imports()
    all_results['success'].extend(results['success'])
    all_results['failed'].extend(results['failed'])
    
    # 3. CUDA 호환성 테스트
    results = test_cuda_compatibility()
    all_results['success'].extend(results['success'])
    all_results['failed'].extend(results['failed'])
    
    # 4. FastAPI 호환성 테스트
    results = test_fastapi_compatibility()
    all_results['success'].extend(results['success'])
    all_results['failed'].extend(results['failed'])
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약")
    print("=" * 50)
    
    print(f"✅ 성공: {len(all_results['success'])}개")
    for success in all_results['success']:
        print(f"  {success}")
    
    print(f"\n❌ 실패: {len(all_results['failed'])}개")
    for failure in all_results['failed']:
        print(f"  {failure}")
    
    # 전체 성공률
    total_tests = len(all_results['success']) + len(all_results['failed'])
    success_rate = (len(all_results['success']) / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n📈 전체 성공률: {success_rate:.1f}%")
    
    if len(all_results['failed']) == 0:
        print("🎉 모든 테스트 통과! 점진적 최신화 성공!")
        return 0
    else:
        print("⚠️ 일부 테스트 실패. 추가 조치 필요.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 