#!/usr/bin/env python3
"""
버전 통일 자동화 스크립트
CUDA 버전 통일, 공통 requirements.txt 구조 생성, Dockerfile 표준화
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Any

class VersionUnifier:
    def __init__(self):
        self.backup_dir = Path("backups/version_unification")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.fixes_applied = []
        
        # 표준 버전 설정
        self.standard_versions = {
            'python': '3.11',
            'cuda': '11.8.2',  # 실제 존재하는 CUDA 버전
            'cudnn': '8',
            'ubuntu': '20.04'
        }
        
    def unify_all_versions(self):
        """모든 버전 통일 작업"""
        print("🔧 버전 통일 자동화 시작...")
        
        # 1. CUDA 버전 통일
        self._unify_cuda_versions()
        
        # 2. 공통 requirements.txt 구조 생성
        self._create_common_requirements()
        
        # 3. 서비스별 requirements.txt 리팩토링
        self._refactor_service_requirements()
        
        # 4. Dockerfile 표준화
        self._standardize_dockerfiles()
        
        # 5. CI 설정 생성
        self._create_ci_config()
        
        # 6. 수정 리포트 생성
        self._generate_unification_report()
        
        print("✅ 버전 통일 자동화 완료!")
    
    def _unify_cuda_versions(self):
        """CUDA 버전 통일"""
        print("🔧 CUDA 버전 통일 중...")
        
        # 표준 CUDA 베이스 이미지
        standard_cuda_image = f"nvidia/cuda:{self.standard_versions['cuda']}-cudnn{self.standard_versions['cudnn']}-runtime-ubuntu{self.standard_versions['ubuntu']}"
        
        cuda_replacements = [
            (r'FROM\s+nvidia/cuda:11\.8\.0', f'FROM {standard_cuda_image}'),
            (r'FROM\s+nvidia/cuda:11\.8\.2', f'FROM {standard_cuda_image}'),
            (r'cuda-version=11\.8\.0', f'cuda-version={self.standard_versions["cuda"]}'),
            (r'cuda-version=11\.8\.2', f'cuda-version={self.standard_versions["cuda"]}'),
        ]
        
        for dockerfile in Path(".").glob("Dockerfile*"):
            try:
                with open(dockerfile, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                for pattern, replacement in cuda_replacements:
                    content = re.sub(pattern, replacement, content)
                
                if content != original_content:
                    # 백업 생성
                    backup_file = self.backup_dir / f"{dockerfile.name}.backup"
                    with open(backup_file, 'w', encoding='utf-8') as f:
                        f.write(original_content)
                    
                    # 수정된 내용 저장
                    with open(dockerfile, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    self.fixes_applied.append({
                        'file': str(dockerfile),
                        'type': 'cuda_unification',
                        'description': f'CUDA 버전 {self.standard_versions["cuda"]}로 통일'
                    })
                    
            except Exception as e:
                print(f"⚠️ CUDA 버전 통일 실패: {dockerfile}, 오류: {e}")
    
    def _create_common_requirements(self):
        """공통 requirements.txt 생성"""
        print("📦 공통 requirements.txt 생성 중...")
        
        # 모든 requirements 파일에서 공통 패키지 수집
        common_packages = {}
        all_requirements_files = list(Path(".").glob("requirements*.txt"))
        
        for req_file in all_requirements_files:
            try:
                with open(req_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        match = re.match(r'^([a-zA-Z0-9_-]+)([<>=!~]+)([\d.a-zA-Z]+)', line)
                        if match:
                            package, operator, version = match.groups()
                            if package not in common_packages:
                                common_packages[package] = []
                            common_packages[package].append(f"{operator}{version}")
                            
            except Exception as e:
                print(f"⚠️ requirements 분석 실패: {req_file}, 오류: {e}")
        
        # 공통 패키지 중 가장 많이 사용되는 버전 선택
        final_common_packages = {}
        for package, versions in common_packages.items():
            if len(versions) > 1:
                # 가장 많이 사용되는 버전 선택
                version_counts = {}
                for version in versions:
                    if version not in version_counts:
                        version_counts[version] = 0
                    version_counts[version] += 1
                
                most_common_version = max(version_counts.items(), key=lambda x: x[1])[0]
                final_common_packages[package] = most_common_version
            else:
                final_common_packages[package] = versions[0]
        
        # 공통 requirements.txt 생성
        common_requirements_content = """# 공통 라이브러리 (모든 서비스에서 사용)
# 이 파일을 수정할 때는 모든 서비스에 영향을 주므로 주의

# 웹 프레임워크
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.2

# HTTP 클라이언트
httpx==0.25.2
requests==2.31.0
aiohttp==3.9.1

# 시스템 모니터링
psutil==5.9.6

# 데이터 처리
numpy==1.24.4
scipy==1.11.4
pandas==2.1.4
scikit-learn==1.3.2

# 오디오 처리
librosa==0.10.1
soundfile==0.12.1
pydub==0.25.1
noisereduce==3.0.0

# 딥러닝 프레임워크
torch==2.1.2
torchaudio==2.1.2
torchvision==0.16.2

# Transformers
transformers==4.35.2
tokenizers==0.14.1
accelerate==0.25.0
huggingface-hub==0.19.4

# 음성 인식
faster-whisper==0.10.0
openai-whisper==20231117

# 음성 분석
pyannote-audio==3.1.1
demucs==4.0.0
nemo-toolkit==1.23.0

# 텍스트 처리
sentence-transformers==2.2.2
datasets==2.16.1
langdetect==1.0.9

# 한국어 처리
konlpy==0.6.0
soynlp==0.0.493

# 유틸리티
python-dotenv==1.0.0
tqdm==4.66.1
structlog==23.2.0
prometheus-client==0.19.0

# 개발 도구
pytest==7.4.3
black==23.11.0
isort==5.12.0
"""
        
        # 공통 requirements.txt 저장
        with open('requirements_common.txt', 'w', encoding='utf-8') as f:
            f.write(common_requirements_content)
        
        self.fixes_applied.append({
            'file': 'requirements_common.txt',
            'type': 'common_requirements',
            'description': '공통 requirements.txt 생성'
        })
    
    def _refactor_service_requirements(self):
        """서비스별 requirements.txt 리팩토링"""
        print("📦 서비스별 requirements.txt 리팩토링 중...")
        
        # 서비스별 특화 패키지 정의
        service_specific_packages = {
            'audio-processor': [
                'joblib==1.3.2',
            ],
            'database-service': [
                'aiosqlite==0.19.0',
                'sqlalchemy==2.0.23',
            ],
            'gateway': [
                'redis==5.0.1',
                'aioredis==2.0.1',
                'aiofiles==23.2.1',
            ],
            'llm-analyzer': [
                'openai==1.6.1',
                'langchain==0.1.0',
                'langchain-openai==0.0.2',
            ],
            'punctuation-restorer': [
                'deepmultilingualpunctuation==1.0.1',
            ],
            'sentiment-analyzer': [
                # konlpy, soynlp는 공통에 포함됨
            ],
            'speaker-diarizer': [
                'MPSENet==1.0.3',
                'ctc-forced-aligner==1.0.2',
                'omegaconf==2.3.0',
            ],
            'speech-recognizer': [
                # faster-whisper, openai-whisper는 공통에 포함됨
            ],
        }
        
        # 각 서비스별 requirements.txt 리팩토링
        for service, packages in service_specific_packages.items():
            req_file = Path(f"requirements.{service}.txt")
            if req_file.exists():
                try:
                    # 백업 생성
                    backup_file = self.backup_dir / f"{req_file.name}.backup"
                    with open(backup_file, 'w', encoding='utf-8') as f:
                        with open(req_file, 'r', encoding='utf-8') as src:
                            f.write(src.read())
                    
                    # 새로운 구조로 작성
                    new_content = f"""# {service} 서비스 전용 라이브러리
# 공통 라이브러리는 requirements_common.txt에서 관리

# 공통 라이브러리 포함
-r requirements_common.txt

# 서비스 전용 라이브러리
"""
                    
                    for package in packages:
                        new_content += f"{package}\n"
                    
                    # 파일 저장
                    with open(req_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    self.fixes_applied.append({
                        'file': str(req_file),
                        'type': 'service_requirements_refactor',
                        'description': f'{service} 서비스 requirements 리팩토링'
                    })
                    
                except Exception as e:
                    print(f"⚠️ {service} requirements 리팩토링 실패: {e}")
    
    def _standardize_dockerfiles(self):
        """Dockerfile 표준화"""
        print("🐳 Dockerfile 표준화 중...")
        
        # 표준 베이스 이미지
        standard_base_image = f"nvidia/cuda:{self.standard_versions['cuda']}-cudnn{self.standard_versions['cudnn']}-runtime-ubuntu{self.standard_versions['ubuntu']}"
        
        # 표준 Dockerfile 템플릿
        dockerfile_template = f"""# 표준화된 Dockerfile 템플릿
FROM {standard_base_image}

# 시스템 패키지 업데이트
RUN apt-get update && apt-get install -y \\
    python{self.standard_versions['python']} \\
    python{self.standard_versions['python']}-pip \\
    python{self.standard_versions['python']}-dev \\
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 환경 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 공통 requirements 설치
COPY requirements_common.txt .
RUN pip install --no-cache-dir -r requirements_common.txt

# 서비스별 requirements 설치 (서비스에 따라 다름)
# COPY requirements.<service>.txt .
# RUN pip install --no-cache-dir -r requirements.<service>.txt

# 애플리케이션 코드 복사
COPY src/ ./src/

# 포트 노출
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# 실행 명령 (서비스에 따라 다름)
# CMD ["python", "-m", "src.<service>.main"]
"""
        
        # 표준 Dockerfile 템플릿 저장
        with open('Dockerfile.template', 'w', encoding='utf-8') as f:
            f.write(dockerfile_template)
        
        self.fixes_applied.append({
            'file': 'Dockerfile.template',
            'type': 'dockerfile_standardization',
            'description': '표준 Dockerfile 템플릿 생성'
        })
    
    def _create_ci_config(self):
        """CI 설정 생성"""
        print("🔧 CI 설정 생성 중...")
        
        # GitHub Actions 워크플로우
        github_workflow = """name: Version Compatibility Check

on:
  push:
    paths:
      - 'requirements*.txt'
      - 'Dockerfile*'
      - 'src/**'
  pull_request:
    paths:
      - 'requirements*.txt'
      - 'Dockerfile*'
      - 'src/**'

jobs:
  version-check:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install requests
    
    - name: Run version compatibility check
      run: |
        python version_compatibility_analyzer.py
    
    - name: Check for version conflicts
      run: |
        if [ -f "version_compatibility_report.json" ]; then
          conflicts=$(python -c "import json; data=json.load(open('version_compatibility_report.json')); print(data['summary']['version_conflicts'])")
          if [ "$conflicts" -gt 0 ]; then
            echo "❌ Version conflicts detected: $conflicts"
            exit 1
          else
            echo "✅ No version conflicts detected"
          fi
        fi
    
    - name: Check for compatibility issues
      run: |
        if [ -f "version_compatibility_report.json" ]; then
          issues=$(python -c "import json; data=json.load(open('version_compatibility_report.json')); print(data['summary']['compatibility_issues'])")
          if [ "$issues" -gt 0 ]; then
            echo "⚠️ Compatibility issues detected: $issues"
            echo "Please review the report"
          else
            echo "✅ No compatibility issues detected"
          fi
        fi
"""
        
        # .github/workflows 디렉토리 생성
        workflows_dir = Path(".github/workflows")
        workflows_dir.mkdir(parents=True, exist_ok=True)
        
        # 워크플로우 파일 저장
        with open(workflows_dir / "version-check.yml", 'w', encoding='utf-8') as f:
            f.write(github_workflow)
        
        self.fixes_applied.append({
            'file': '.github/workflows/version-check.yml',
            'type': 'ci_integration',
            'description': 'GitHub Actions CI 설정 생성'
        })
        
        # GitLab CI 설정
        gitlab_ci = """# GitLab CI 설정
stages:
  - version_check

version_compatibility_check:
  stage: version_check
  image: python:3.11
  script:
    - pip install requests
    - python version_compatibility_analyzer.py
    - |
      if [ -f "version_compatibility_report.json" ]; then
        conflicts=$(python -c "import json; data=json.load(open('version_compatibility_report.json')); print(data['summary']['version_conflicts'])")
        if [ "$conflicts" -gt 0 ]; then
          echo "❌ Version conflicts detected: $conflicts"
          exit 1
        fi
      fi
  rules:
    - changes:
        - requirements*.txt
        - Dockerfile*
        - src/**/*
"""
        
        with open('.gitlab-ci.yml', 'w', encoding='utf-8') as f:
            f.write(gitlab_ci)
        
        self.fixes_applied.append({
            'file': '.gitlab-ci.yml',
            'type': 'ci_integration',
            'description': 'GitLab CI 설정 생성'
        })
    
    def _generate_unification_report(self):
        """통일 리포트 생성"""
        print("\n" + "="*60)
        print("📊 버전 통일 자동화 리포트")
        print("="*60)
        
        print(f"\n🔧 총 수정 사항: {len(self.fixes_applied)}개")
        
        # 타입별 수정 사항 요약
        fix_types = {}
        for fix in self.fixes_applied:
            fix_type = fix['type']
            if fix_type not in fix_types:
                fix_types[fix_type] = 0
            fix_types[fix_type] += 1
        
        for fix_type, count in fix_types.items():
            print(f"   - {fix_type}: {count}개")
        
        # 상세 수정 사항
        print(f"\n📋 상세 수정 사항:")
        for fix in self.fixes_applied:
            print(f"   - {fix['file']}: {fix['description']}")
        
        # 표준 버전 정보
        print(f"\n📋 표준 버전 설정:")
        for component, version in self.standard_versions.items():
            print(f"   - {component}: {version}")
        
        # 백업 정보
        print(f"\n💾 백업 파일 위치: {self.backup_dir}")
        
        # 다음 단계 안내
        print(f"\n💡 다음 단계:")
        print(f"   1. requirements_common.txt 검토 및 수정")
        print(f"   2. 서비스별 requirements.txt 확인")
        print(f"   3. Dockerfile.template 기반으로 서비스별 Dockerfile 수정")
        print(f"   4. CI 설정 테스트")
        print(f"   5. 전체 빌드 및 테스트 실행")
        
        # 상세 리포트 저장
        report = {
            'summary': {
                'total_fixes': len(self.fixes_applied),
                'fix_types': fix_types,
                'standard_versions': self.standard_versions
            },
            'fixes': self.fixes_applied,
            'backup_location': str(self.backup_dir)
        }
        
        with open('version_unification_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 상세 리포트 저장: version_unification_report.json")

def main():
    unifier = VersionUnifier()
    unifier.unify_all_versions()
    print("\n🎉 버전 통일 자동화 완료!")

if __name__ == "__main__":
    main() 