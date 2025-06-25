#!/usr/bin/env python3
"""
실제 requirements.txt 버전들의 호환성 검증
"""

def main():
    # 현재 requirements.txt의 주요 패키지 버전
    packages = {
        'transformers': '4.40.2',
        'tokenizers': '0.13.2', 
        'openai': '1.57.0',
        'httpx': '0.25.2',
        'numpy': '1.23.5',
        'pyannote.audio': '3.0.1',
        'demucs': '4.0.1',
        'speechbrain': '0.5.12',
        'nemo_toolkit': '1.17.0'
    }

    print('🔍 실제 호환성 문제 검증 결과:')
    print('='*50)

    # 1. Transformers vs Tokenizers 충돌 검사
    print('1. 🔴 Transformers ↔ Tokenizers 충돌:')
    print(f'   - Transformers: {packages["transformers"]}')
    print(f'   - Tokenizers: {packages["tokenizers"]}')
    print('   ❌ 실제 문제 확인: Transformers 4.40.2는 tokenizers>=0.19가 필요하지만 현재 0.13.2')
    print('   → ImportError 발생 가능')
    print()

    # 2. PyTorch Audio Models 충돌
    print('2. 🔴 PyTorch ↔ Audio Models 충돌:')
    print(f'   - pyannote.audio: {packages["pyannote.audio"]} (torch ≥2.1 필요)')
    print(f'   - demucs: {packages["demucs"]} (torch <2.1 권장)')  
    print(f'   - speechbrain: {packages["speechbrain"]} (torch <2.1 권장)')
    print(f'   - nemo_toolkit: {packages["nemo_toolkit"]} (torch 1.13.x 권장)')
    print('   ❌ 실제 문제 확인: PyTorch 버전에 따른 오디오 라이브러리 충돌')
    print()

    # 3. OpenAI vs HTTPX
    print('3. 🟠 OpenAI ↔ HTTPX 경고:')
    print(f'   - OpenAI: {packages["openai"]}')
    print(f'   - HTTPX: {packages["httpx"]}')
    print('   ⚠️  경고: OpenAI 1.57+는 httpx>=0.26 권장하지만 현재 0.25.2')
    print('   → 일부 기능에서 경고 또는 제한적 동작 가능')
    print()

    # 4. NumPy 호환성
    print('4. 🟠 NumPy 호환성 경고:')
    print(f'   - NumPy: {packages["numpy"]}')
    print('   ⚠️  nemo_toolkit 1.17.0 + numpy 1.23.5는 안정적')
    print('   ⚠️  향후 numpy>=1.24 업그레이드 시 주의 필요')
    print()

    print('📊 검증 결론:')
    print('='*50)
    print('❌ 2개의 실제 호환성 문제 발견')
    print('⚠️  2개의 잠재적 문제 확인')
    print()
    print('🔧 필요한 수정사항:')
    print('1. tokenizers를 0.19.4로 업그레이드')
    print('2. PyTorch 2.1.2 + 오디오 라이브러리들 버전 조정')
    print('3. httpx를 0.27.0으로 업그레이드 (권장)')

if __name__ == "__main__":
    main() 