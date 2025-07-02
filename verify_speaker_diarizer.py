#!/usr/bin/env python3
"""
Speaker Diarizer 서비스 호환성 검증 스크립트
"""

import sys
import importlib

def test_imports():
    """필요한 라이브러리들이 정상적으로 import되는지 테스트"""
    
    required_modules = [
        'fastapi',
        'uvicorn', 
        'pydantic',
        'torch',
        'nemo_toolkit',
        'numpy'
    ]
    
    failed_imports = []
    
    print("🔍 Speaker Diarizer 서비스 import 테스트 시작...")
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module} - 정상")
        except ImportError as e:
            print(f"❌ {module} - 실패: {e}")
            failed_imports.append(module)
        except Exception as e:
            print(f"⚠️ {module} - 경고: {e}")
    
    if failed_imports:
        print(f"\n❌ 실패한 import: {failed_imports}")
        return False
    else:
        print("\n✅ 모든 import 성공!")
        return True

def test_speaker_diarizer_code():
    """Speaker Diarizer 관련 코드가 정상적으로 동작하는지 테스트"""
    
    try:
        # src.audio.error 모듈 테스트
        from src.audio.error import AdvancedDialogueDetecting
        print("✅ AdvancedDialogueDetecting import 성공")
        
        # 기본 초기화 테스트
        detector = AdvancedDialogueDetecting(max_workers=1, enable_parallel=False)
        print("✅ AdvancedDialogueDetecting 초기화 성공")
        
        return True
        
    except Exception as e:
        print(f"❌ Speaker Diarizer 코드 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    print("🎤 Speaker Diarizer 서비스 호환성 검증")
    print("=" * 50)
    
    import_success = test_imports()
    code_success = test_speaker_diarizer_code()
    
    if import_success and code_success:
        print("\n🎉 Speaker Diarizer 서비스 호환성 검증 완료!")
        sys.exit(0)
    else:
        print("\n💥 Speaker Diarizer 서비스 호환성 검증 실패!")
        sys.exit(1) 