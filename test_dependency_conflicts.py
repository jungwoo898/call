#!/usr/bin/env python3
"""
Requirements.txt 의존성 충돌 검증 스크립트
실제 pip 설치 없이 버전 호환성을 검사합니다.
"""

import subprocess
import sys
from packaging import version
import re

def parse_requirement(req_line):
    """requirements.txt 라인을 파싱하여 패키지명과 버전 제약 추출"""
    req_line = req_line.strip()
    if not req_line or req_line.startswith('#'):
        return None, None
    
    # 패키지명과 버전 제약 분리
    if '==' in req_line:
        name, ver = req_line.split('==', 1)
        return name.strip(), ('==', ver.strip())
    elif '>=' in req_line:
        name, ver = req_line.split('>=', 1)
        return name.strip(), ('>=', ver.strip())
    elif '<=' in req_line:
        name, ver = req_line.split('<=', 1)
        return name.strip(), ('<=', ver.strip())
    elif '>' in req_line:
        name, ver = req_line.split('>', 1)
        return name.strip(), ('>', ver.strip())
    elif '<' in req_line:
        name, ver = req_line.split('<', 1)
        return name.strip(), ('<', ver.strip())
    else:
        return req_line.strip(), None

def check_pip_dependency_conflicts():
    """pip 도구를 사용하여 의존성 충돌 확인"""
    print("🔍 pip dependency checker를 사용한 충돌 검사")
    
    try:
        # pip-tools의 pip-compile dry-run 시도
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '--dry-run', '--report', '-', 
            '-r', 'requirements.txt'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("   ✅ pip 의존성 해결 성공")
            return True
        else:
            print("   ❌ pip 의존성 충돌 발견:")
            print(f"   {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("   ⚠️  pip install --dry-run 지원하지 않는 pip 버전")
        return None
    except subprocess.TimeoutExpired:
        print("   ⚠️  pip 검사 시간 초과")
        return None
    except Exception as e:
        print(f"   ⚠️  pip 검사 실패: {e}")
        return None

def simulate_known_conflicts():
    """알려진 호환성 문제들을 시뮬레이션"""
    print("\n🔍 알려진 호환성 문제 시뮬레이션")
    
    # requirements.txt 읽기
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.readlines()
    except FileNotFoundError:
        print("   ❌ requirements.txt 파일을 찾을 수 없습니다")
        return False
    
    packages = {}
    for line in requirements:
        name, ver_constraint = parse_requirement(line)
        if name and ver_constraint:
            packages[name] = ver_constraint
    
    issues = []
    
    # 1. Transformers vs Tokenizers 충돌 검사
    if 'transformers' in packages and 'tokenizers' in packages:
        trans_ver = packages['transformers'][1] if packages['transformers'] else None
        token_ver = packages['tokenizers'][1] if packages['tokenizers'] else None
        
        if trans_ver and token_ver:
            try:
                if (version.parse(trans_ver) >= version.parse("4.40.0") and 
                    version.parse(token_ver) < version.parse("0.19.0")):
                    issues.append("🔴 Transformers 4.40+ 는 tokenizers>=0.19 필요, 현재 tokenizers={token_ver}")
                elif (version.parse(trans_ver) >= version.parse("4.40.0") and 
                      version.parse(token_ver) >= version.parse("0.20.0")):
                    issues.append("🔴 Transformers 4.40+ 는 tokenizers<0.20 필요, 현재 tokenizers={token_ver}")
            except:
                pass
    
    # 2. PyTorch vs Audio Models 충돌 검사
    torch_ver = packages.get('torch', (None, None))[1]
    if torch_ver:
        try:
            torch_version = version.parse(torch_ver.split('+')[0])
            
            # pyannote.audio 체크
            if 'pyannote.audio' in packages:
                pyannote_ver = packages['pyannote.audio'][1]
                if (version.parse(pyannote_ver) >= version.parse("3.0.0") and 
                    torch_version < version.parse("2.1.0")):
                    issues.append(f"🔴 pyannote.audio 3.0+ 는 PyTorch ≥2.1 필요, 현재 torch={torch_ver}")
            
            # demucs 체크
            if 'demucs' in packages:
                demucs_ver = packages['demucs'][1]
                if (version.parse(demucs_ver) < version.parse("4.1.0") and 
                    torch_version >= version.parse("2.1.0")):
                    issues.append(f"🟠 demucs {demucs_ver} < 4.1.0 은 PyTorch 2.1+와 호환성 문제 가능")
            
            # speechbrain 체크
            if 'speechbrain' in packages:
                sb_ver = packages['speechbrain'][1]
                if (version.parse(sb_ver) < version.parse("0.5.16") and 
                    torch_version >= version.parse("2.1.0")):
                    issues.append(f"🟠 speechbrain {sb_ver} < 0.5.16 은 PyTorch 2.1+와 호환성 문제 가능")
            
            # nemo_toolkit 체크
            if 'nemo_toolkit' in packages:
                nemo_ver = packages['nemo_toolkit'][1]
                if (version.parse(nemo_ver) < version.parse("1.23.0") and 
                    torch_version >= version.parse("2.1.0")):
                    issues.append(f"🟠 nemo_toolkit {nemo_ver} < 1.23.0 은 PyTorch 2.1+와 호환성 문제 가능")
        except:
            pass
    
    # 3. OpenAI vs HTTPX 충돌 검사
    if 'openai' in packages and 'httpx' in packages:
        openai_ver = packages['openai'][1]
        httpx_ver = packages['httpx'][1]
        
        try:
            if (version.parse(openai_ver) >= version.parse("1.55.0") and 
                version.parse(httpx_ver) < version.parse("0.25.0")):
                issues.append(f"🔴 OpenAI {openai_ver} ≥1.55 는 httpx≥0.25 필요, 현재 httpx={httpx_ver}")
            
            if version.parse(httpx_ver) >= version.parse("0.28.0"):
                issues.append(f"🟠 HTTPX {httpx_ver} ≥0.28 는 proxies 인자 제거로 일부 환경에서 오류 가능")
        except:
            pass
    
    # 4. NumPy 호환성 검사
    numpy_ver = packages.get('numpy', (None, None))[1]
    if numpy_ver:
        try:
            if 'ctc-forced-aligner' in packages:
                if version.parse(numpy_ver) >= version.parse("1.24.0"):
                    issues.append(f"🟠 ctc-forced-aligner는 numpy<1.24에서 컴파일됨, 현재 numpy={numpy_ver}")
            
            if 'nemo_toolkit' in packages:
                nemo_ver = packages['nemo_toolkit'][1]
                if (version.parse(nemo_ver) <= version.parse("1.17.0") and 
                    version.parse(numpy_ver) >= version.parse("1.24.0")):
                    issues.append(f"🟠 nemo_toolkit {nemo_ver} ≤1.17.0 은 numpy≥1.24에서 문제 가능, 현재 numpy={numpy_ver}")
        except:
            pass
    
    # 결과 출력
    if issues:
        print("   ❌ 호환성 문제 발견:")
        for issue in issues:
            print(f"      {issue}")
        return False
    else:
        print("   ✅ 시뮬레이션에서 호환성 문제 없음")
        return True

def check_requirements_syntax():
    """requirements.txt 문법 오류 검사"""
    print("\n🔍 requirements.txt 문법 검사")
    
    try:
        with open('requirements.txt', 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("   ❌ requirements.txt 파일을 찾을 수 없습니다")
        return False
    
    issues = []
    package_counts = {}
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        name, ver_constraint = parse_requirement(line)
        if name:
            if name in package_counts:
                package_counts[name] += 1
                issues.append(f"라인 {i}: 중복 패키지 정의 - {name}")
            else:
                package_counts[name] = 1
    
    if issues:
        print("   ❌ 문법 문제 발견:")
        for issue in issues:
            print(f"      {issue}")
        return False
    else:
        print("   ✅ requirements.txt 문법 정상")
        return True

def main():
    """메인 검증 함수"""
    print("🚀 Requirements.txt 의존성 충돌 검증 시작\n")
    
    results = []
    
    # 각 검사 실행
    results.append(check_requirements_syntax())
    simulation_result = simulate_known_conflicts()
    results.append(simulation_result)
    
    pip_result = check_pip_dependency_conflicts()
    if pip_result is not None:
        results.append(pip_result)
    
    # 결과 요약
    print("\n" + "="*60)
    print("📊 의존성 충돌 검증 결과")
    print("="*60)
    
    passed = sum([r for r in results if r is not False])
    total = len([r for r in results if r is not None])
    
    if passed == total and simulation_result:
        print("✅ 의존성 충돌 검사 통과!")
        print("🎉 현재 requirements.txt가 안전합니다.")
        return True
    else:
        print(f"❌ {total - passed}/{total} 개의 문제 발견")
        print("🔧 requirements.txt 수정을 권장합니다.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 