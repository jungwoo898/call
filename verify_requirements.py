#!/usr/bin/env python3
"""
Requirements 파일 검증 스크립트
모든 패키지가 실제로 존재하는지 확인
"""

import subprocess
import sys
import re
from pathlib import Path

def check_package_exists(package_name, version=None):
    """패키지가 PyPI에 존재하는지 확인"""
    try:
        if version:
            cmd = [sys.executable, "-m", "pip", "index", "versions", package_name]
        else:
            cmd = [sys.executable, "-m", "pip", "search", package_name]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            if version:
                # 버전 확인
                if version in result.stdout:
                    return True, f"✓ {package_name}=={version} 존재"
                else:
                    return False, f"✗ {package_name}=={version} 존재하지 않음"
            else:
                return True, f"✓ {package_name} 존재"
        else:
            return False, f"✗ {package_name} 확인 실패: {result.stderr}"
            
    except subprocess.TimeoutExpired:
        return False, f"✗ {package_name} 확인 타임아웃"
    except Exception as e:
        return False, f"✗ {package_name} 확인 오류: {e}"

def parse_requirements_file(file_path):
    """Requirements 파일 파싱"""
    packages = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('asyncio'):
                    # 버전 정보 추출
                    match = re.match(r'^([a-zA-Z0-9_-]+)(?:==([0-9.]+))?', line)
                    if match:
                        package_name = match.group(1)
                        version = match.group(2) if match.group(2) else None
                        packages.append((package_name, version))
    except Exception as e:
        print(f"파일 읽기 오류 {file_path}: {e}")
    
    return packages

def verify_requirements_file(file_path):
    """Requirements 파일 검증"""
    print(f"\n🔍 검증 중: {file_path}")
    print("=" * 50)
    
    packages = parse_requirements_file(file_path)
    
    if not packages:
        print("❌ 패키지를 찾을 수 없습니다")
        return False
    
    all_valid = True
    
    for package_name, version in packages:
        is_valid, message = check_package_exists(package_name, version)
        print(message)
        if not is_valid:
            all_valid = False
    
    if all_valid:
        print(f"\n✅ {file_path} - 모든 패키지가 유효합니다")
    else:
        print(f"\n❌ {file_path} - 일부 패키지에 문제가 있습니다")
    
    return all_valid

def main():
    """메인 함수"""
    print("🚀 Requirements 파일 검증 시작")
    print("=" * 60)
    
    # 검증할 requirements 파일들
    requirements_files = [
        "requirements.audio-processor.txt",
        "requirements.punctuation-restorer.txt", 
        "requirements.sentiment-analyzer.txt",
        "requirements.database-service.txt",
        "requirements.speaker-diarizer.txt",
        "requirements.speech-recognizer.txt",
        "requirements.llm-analyzer.txt",
        "requirements.gateway.txt"
    ]
    
    all_files_valid = True
    
    for req_file in requirements_files:
        if Path(req_file).exists():
            if not verify_requirements_file(req_file):
                all_files_valid = False
        else:
            print(f"\n⚠️  파일 없음: {req_file}")
    
    print("\n" + "=" * 60)
    if all_files_valid:
        print("🎉 모든 requirements 파일이 유효합니다!")
        print("이제 빌드를 진행할 수 있습니다.")
    else:
        print("❌ 일부 requirements 파일에 문제가 있습니다.")
        print("문제를 수정한 후 다시 검증하세요.")
    
    return all_files_valid

if __name__ == "__main__":
    main() 