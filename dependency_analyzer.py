#!/usr/bin/env python3
"""
종속성 충돌 자동 탐지 및 수정 스크립트
모든 패키지를 고정 버전으로 설정하고 상호 충돌을 해결합니다.
"""

import subprocess
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
import yaml

class DependencyAnalyzer:
    def __init__(self):
        self.conflicts = []
        self.dependency_graph = {}
        self.resolved_versions = {}
        
    def analyze_requirements_files(self) -> Dict[str, Dict[str, str]]:
        """모든 requirements 파일 분석"""
        requirements_files = {
            'main': 'requirements.txt',
            'speech-recognizer': 'requirements.speech-recognizer.txt',
            'speaker-diarizer': 'requirements.speaker-diarizer.txt',
            'llm-analyzer': 'requirements.llm-analyzer.txt',
            'sentiment-analyzer': 'requirements.sentiment-analyzer.txt',
            'punctuation-restorer': 'requirements.punctuation-restorer.txt',
            'audio-processor': 'requirements.audio-processor.txt',
            'database-service': 'requirements.database-service.txt',
            'gateway': 'requirements.gateway.txt',
            'test': 'requirements.test.txt'
        }
        
        all_dependencies = {}
        
        for service, file_path in requirements_files.items():
            if Path(file_path).exists():
                deps = self.parse_requirements_file(file_path)
                all_dependencies[service] = deps
                print(f"📦 {service}: {len(deps)} 패키지 분석 완료")
        
        return all_dependencies
    
    def parse_requirements_file(self, file_path: str) -> Dict[str, str]:
        """requirements 파일 파싱"""
        dependencies = {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '==' in line:
                    # 패키지명과 버전 추출
                    match = re.match(r'^([a-zA-Z0-9_-]+)==([0-9.]+[a-zA-Z0-9._-]*)$', line)
                    if match:
                        package, version = match.groups()
                        dependencies[package] = version
        
        return dependencies
    
    def detect_version_conflicts(self, all_dependencies: Dict[str, Dict[str, str]]) -> List[Dict]:
        """버전 충돌 탐지"""
        conflicts = []
        package_versions = {}
        
        # 모든 서비스에서 패키지 버전 수집
        for service, deps in all_dependencies.items():
            for package, version in deps.items():
                if package not in package_versions:
                    package_versions[package] = {}
                package_versions[package][service] = version
        
        # 충돌 탐지
        for package, versions in package_versions.items():
            unique_versions = set(versions.values())
            if len(unique_versions) > 1:
                conflict = {
                    'package': package,
                    'versions': versions,
                    'unique_versions': list(unique_versions)
                }
                conflicts.append(conflict)
                print(f"⚠️ 충돌 발견: {package} - {list(unique_versions)}")
        
        return conflicts
    
    def resolve_conflicts(self, conflicts: List[Dict]) -> Dict[str, str]:
        """충돌 해결 - 최신 안정 버전 선택"""
        resolved = {}
        
        # 우선순위 규칙 정의
        priority_rules = {
            'torch': '2.1.2',  # CUDA 11.8 호환
            'torchaudio': '2.1.2',
            'torchvision': '0.16.2',
            'transformers': '4.35.2',
            'tokenizers': '0.14.1',
            'accelerate': '0.25.0',
            'huggingface-hub': '0.19.4',
            'numpy': '1.24.4',
            'scipy': '1.11.4',
            'pandas': '2.1.4',
            'fastapi': '0.104.1',
            'uvicorn': '0.24.0',
            'pydantic': '2.5.2',
            'pyannote-audio': '3.1.1',
            'nemo-toolkit': '1.23.0',
            'demucs': '4.0.0',
            'MPSENet': '1.0.3',
            'ctc-forced-aligner': '1.0.2',
            'openai': '1.6.1',
            'langchain': '0.1.0',
            'langchain-openai': '0.0.2',
            'konlpy': '0.6.0',
            'soynlp': '0.0.493',
            'deepmultilingualpunctuation': '1.0.1',
            'librosa': '0.10.1',
            'soundfile': '0.12.1',
            'faster-whisper': '0.10.0',
            'openai-whisper': '20231117',
            'sentence-transformers': '2.2.2',
            'speechbrain': '0.5.16',
            'python-dotenv': '1.0.0',
            'omegaconf': '2.3.0',
            'tqdm': '4.66.1',
            'structlog': '23.2.0',
            'prometheus-client': '0.19.0',
            'aiosqlite': '0.19.0',
            'sqlalchemy': '2.0.23',
            'redis': '5.0.1'
        }
        
        for conflict in conflicts:
            package = conflict['package']
            versions = conflict['unique_versions']
            
            # 우선순위 규칙 적용
            if package in priority_rules:
                resolved_version = priority_rules[package]
                resolved[package] = resolved_version
                print(f"✅ {package}: {resolved_version} (우선순위 규칙 적용)")
            else:
                # 최신 버전 선택 (안정성 고려)
                resolved_version = self.select_best_version(versions)
                resolved[package] = resolved_version
                print(f"✅ {package}: {resolved_version} (최신 안정 버전)")
        
        return resolved
    
    def select_best_version(self, versions: List[str]) -> str:
        """최적 버전 선택 (안정성 우선)"""
        # 버전 정렬 (semantic versioning)
        def version_key(v):
            parts = v.split('.')
            return [int(p) if p.isdigit() else p for p in parts]
        
        sorted_versions = sorted(versions, key=version_key)
        
        # 안정 버전 우선 (alpha, beta, rc 제외)
        stable_versions = [v for v in sorted_versions if not any(x in v.lower() for x in ['alpha', 'beta', 'rc', 'dev'])]
        
        if stable_versions:
            return stable_versions[-1]  # 최신 안정 버전
        else:
            return sorted_versions[-1]  # 최신 버전
    
    def update_requirements_files(self, all_dependencies: Dict[str, Dict[str, str]], resolved_versions: Dict[str, str]):
        """requirements 파일 업데이트"""
        for service, deps in all_dependencies.items():
            file_path = f"requirements.{service}.txt" if service != 'main' else "requirements.txt"
            
            if Path(file_path).exists():
                self.update_single_requirements_file(file_path, deps, resolved_versions)
                print(f"📝 {file_path} 업데이트 완료")
    
    def update_single_requirements_file(self, file_path: str, original_deps: Dict[str, str], resolved_versions: Dict[str, str]):
        """단일 requirements 파일 업데이트"""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        updated_lines = []
        updated_packages = set()
        
        for line in lines:
            if line.strip() and not line.startswith('#') and '==' in line:
                match = re.match(r'^([a-zA-Z0-9_-]+)==([0-9.]+[a-zA-Z0-9._-]*)$', line.strip())
                if match:
                    package, _ = match.groups()
                    if package in resolved_versions:
                        new_version = resolved_versions[package]
                        updated_lines.append(f"{package}=={new_version}\n")
                        updated_packages.add(package)
                        continue
            
            updated_lines.append(line)
        
        # 누락된 패키지 추가
        for package, version in resolved_versions.items():
            if package not in updated_packages and package in original_deps:
                updated_lines.append(f"{package}=={version}\n")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(updated_lines)
    
    def generate_dependency_report(self, all_dependencies: Dict[str, Dict[str, str]], conflicts: List[Dict], resolved_versions: Dict[str, str]):
        """종속성 분석 보고서 생성"""
        report = {
            'summary': {
                'total_services': len(all_dependencies),
                'total_packages': len(set().union(*[set(deps.keys()) for deps in all_dependencies.values()])),
                'conflicts_found': len(conflicts),
                'resolved_conflicts': len(resolved_versions)
            },
            'conflicts': conflicts,
            'resolved_versions': resolved_versions,
            'service_dependencies': all_dependencies
        }
        
        with open('dependency_analysis_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📊 종속성 분석 보고서 생성: dependency_analysis_report.json")
    
    def run(self):
        """메인 실행 함수"""
        print("🔍 종속성 충돌 자동 탐지 및 수정 시작...")
        
        # 1. 모든 requirements 파일 분석
        all_dependencies = self.analyze_requirements_files()
        
        # 2. 버전 충돌 탐지
        conflicts = self.detect_version_conflicts(all_dependencies)
        
        if not conflicts:
            print("✅ 버전 충돌이 발견되지 않았습니다!")
            return
        
        # 3. 충돌 해결
        resolved_versions = self.resolve_conflicts(conflicts)
        
        # 4. requirements 파일 업데이트
        self.update_requirements_files(all_dependencies, resolved_versions)
        
        # 5. 보고서 생성
        self.generate_dependency_report(all_dependencies, conflicts, resolved_versions)
        
        print(f"🎉 종속성 충돌 해결 완료!")
        print(f"   - 발견된 충돌: {len(conflicts)}개")
        print(f"   - 해결된 충돌: {len(resolved_versions)}개")

if __name__ == "__main__":
    analyzer = DependencyAnalyzer()
    analyzer.run() 