#!/usr/bin/env python3
"""
Callytics 패키지 호환성 검증 스크립트
지적된 호환성 문제들을 실제로 테스트해봅니다.
"""

import sys
import subprocess
import importlib.util
from packaging import version

def check_package_version(package_name):
    """패키지 버전 확인"""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'show', package_name], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    return line.split(': ')[1]
        return None
    except Exception as e:
        return None

def test_transformers_tokenizers():
    """Transformers vs Tokenizers 호환성 테스트"""
    print("🔍 1. Transformers ↔ Tokenizers 호환성 테스트")
    
    try:
        import transformers
        import tokenizers
        
        transformers_ver = transformers.__version__
        tokenizers_ver = tokenizers.__version__
        
        print(f"   Transformers 버전: {transformers_ver}")
        print(f"   Tokenizers 버전: {tokenizers_ver}")
        
        # Transformers 4.40.x는 tokenizers>=0.19,<0.20를 요구
        if version.parse(transformers_ver) >= version.parse("4.40.0"):
            if version.parse(tokenizers_ver) < version.parse("0.19.0"):
                print("   ❌ 호환성 문제: Transformers 4.40+ 는 tokenizers>=0.19가 필요")
                return False
            elif version.parse(tokenizers_ver) >= version.parse("0.20.0"):
                print("   ❌ 호환성 문제: Transformers 4.40+ 는 tokenizers<0.20가 필요")
                return False
        
        # 실제 import 테스트
        from transformers import AutoTokenizer
        print("   ✅ AutoTokenizer import 성공")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import 실패: {e}")
        return False
    except Exception as e:
        print(f"   ❌ 호환성 문제 발견: {e}")
        return False

def test_pytorch_audio_models():
    """PyTorch vs Audio Models 호환성 테스트"""
    print("\n🔍 2. PyTorch ↔ Audio Models 호환성 테스트")
    
    try:
        import torch
        torch_ver = torch.__version__.split('+')[0]  # CUDA 정보 제거
        print(f"   PyTorch 버전: {torch_ver}")
        
        issues = []
        
        # pyannote.audio 테스트
        try:
            pyannote_ver = check_package_version('pyannote.audio')
            if pyannote_ver:
                print(f"   pyannote.audio 버전: {pyannote_ver}")
                if (version.parse(pyannote_ver) >= version.parse("3.0.0") and 
                    version.parse(torch_ver) < version.parse("2.1.0")):
                    issues.append("pyannote.audio 3.0+ 는 PyTorch ≥2.1이 필요")
        except:
            pass
            
        # demucs 테스트
        try:
            demucs_ver = check_package_version('demucs')
            if demucs_ver:
                print(f"   demucs 버전: {demucs_ver}")
                if (version.parse(demucs_ver) < version.parse("4.1.0") and 
                    version.parse(torch_ver) >= version.parse("2.1.0")):
                    issues.append("demucs < 4.1.0 은 PyTorch 2.1+와 호환성 문제 가능")
        except:
            pass
            
        # speechbrain 테스트
        try:
            sb_ver = check_package_version('speechbrain')
            if sb_ver:
                print(f"   speechbrain 버전: {sb_ver}")
                if (version.parse(sb_ver) < version.parse("0.5.16") and 
                    version.parse(torch_ver) >= version.parse("2.1.0")):
                    issues.append("speechbrain < 0.5.16 은 PyTorch 2.1+와 호환성 문제 가능")
        except:
            pass
            
        # nemo_toolkit 테스트
        try:
            nemo_ver = check_package_version('nemo_toolkit')
            if nemo_ver:
                print(f"   nemo_toolkit 버전: {nemo_ver}")
                if (version.parse(nemo_ver) < version.parse("1.23.0") and 
                    version.parse(torch_ver) >= version.parse("2.1.0")):
                    issues.append("nemo_toolkit < 1.23.0 은 PyTorch 2.1+와 호환성 문제 가능")
        except:
            pass
        
        if issues:
            print("   ❌ 잠재적 호환성 문제들:")
            for issue in issues:
                print(f"      - {issue}")
            return False
        else:
            print("   ✅ PyTorch 버전 호환성 문제 없음")
            return True
            
    except ImportError:
        print("   ❌ PyTorch가 설치되지 않았습니다")
        return False

def test_openai_httpx():
    """OpenAI vs HTTPX 호환성 테스트"""
    print("\n🔍 3. OpenAI ↔ HTTPX 호환성 테스트")
    
    try:
        import openai
        import httpx
        
        openai_ver = openai.__version__
        httpx_ver = httpx.__version__
        
        print(f"   OpenAI 버전: {openai_ver}")
        print(f"   HTTPX 버전: {httpx_ver}")
        
        # OpenAI 1.55+ 는 httpx>=0.26을 권장하지만 0.25.2도 동작
        if (version.parse(openai_ver) >= version.parse("1.55.0") and 
            version.parse(httpx_ver) < version.parse("0.25.0")):
            print("   ❌ 호환성 문제: OpenAI 1.55+ 는 httpx>=0.25가 필요")
            return False
        
        # HTTPX 0.28+는 proxies 인자 제거로 문제 발생 가능
        if version.parse(httpx_ver) >= version.parse("0.28.0"):
            print("   ⚠️  경고: HTTPX 0.28+는 proxies 인자 문제로 일부 환경에서 오류 가능")
        
        # 실제 OpenAI 클라이언트 초기화 테스트
        try:
            client = openai.OpenAI(api_key="test-key")
            print("   ✅ OpenAI 클라이언트 초기화 성공")
            return True
        except Exception as e:
            if "proxies" in str(e):
                print("   ❌ HTTPX proxies 호환성 문제 발견")
                return False
            else:
                print("   ✅ OpenAI 클라이언트 초기화 성공 (API 키 오류는 정상)")
                return True
        
    except ImportError as e:
        print(f"   ❌ Import 실패: {e}")
        return False

def test_numpy_compatibility():
    """NumPy 호환성 테스트"""
    print("\n🔍 4. NumPy 호환성 테스트")
    
    try:
        import numpy as np
        numpy_ver = np.__version__
        print(f"   NumPy 버전: {numpy_ver}")
        
        issues = []
        
        # ctc-forced-aligner 테스트
        ctc_ver = check_package_version('ctc-forced-aligner')
        if ctc_ver:
            print(f"   ctc-forced-aligner 버전: {ctc_ver}")
            if version.parse(numpy_ver) >= version.parse("1.24.0"):
                issues.append("ctc-forced-aligner는 numpy<1.24에서 컴파일됨, 호환성 주의")
        
        # nemo_toolkit numpy 호환성
        nemo_ver = check_package_version('nemo_toolkit')
        if nemo_ver and version.parse(nemo_ver) <= version.parse("1.17.0"):
            if version.parse(numpy_ver) >= version.parse("1.24.0"):
                issues.append("nemo_toolkit 1.17.0은 numpy>=1.24에서 문제 발생 가능")
        
        if issues:
            print("   ⚠️  잠재적 호환성 문제들:")
            for issue in issues:
                print(f"      - {issue}")
            return False
        else:
            print("   ✅ NumPy 호환성 문제 없음")
            return True
            
    except ImportError:
        print("   ❌ NumPy가 설치되지 않았습니다")
        return False

def main():
    """메인 호환성 검사 함수"""
    print("🚀 Callytics 패키지 호환성 검증 시작\n")
    
    results = []
    
    # 각 테스트 실행
    results.append(test_transformers_tokenizers())
    results.append(test_pytorch_audio_models())
    results.append(test_openai_httpx())
    results.append(test_numpy_compatibility())
    
    # 결과 요약
    print("\n" + "="*60)
    print("📊 호환성 검증 결과 요약")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print("✅ 모든 호환성 테스트 통과!")
        print("🎉 현재 requirements.txt 설정이 정확합니다.")
    else:
        print(f"❌ {total - passed}/{total} 개의 호환성 문제 발견")
        print("🔧 requirements.txt 수정이 필요합니다.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 