#!/usr/bin/env python3
"""
버전 및 환경 일치 점검 스크립트
Dockerfile, requirements.txt에서 버전 불일치 및 호환성 문제 분석
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Any

class VersionCompatibilityAnalyzer:
    def __init__(self):
        self.dockerfile_versions = {}
        self.requirements_versions = {}
        self.version_conflicts = []
        self.compatibility_issues = []
        self.runtime_versions = {}
        
    def analyze_project(self):
        print("🔍 버전 및 환경 일치 점검 시작...")
        
        # 1. Dockerfile 분석
        self._analyze_dockerfiles()
        
        # 2. Requirements 분석
        self._analyze_requirements()
        
        # 3. 버전 충돌 검사
        self._check_version_conflicts()
        
        # 4. 호환성 문제 검사
        self._check_compatibility_issues()
        
        # 5. 리포트 생성
        self._generate_report()
    
    def _analyze_dockerfiles(self):
        """Dockerfile에서 런타임 버전 분석"""
        print("🐳 Dockerfile 런타임 버전 분석 중...")
        
        dockerfile_patterns = [
            # Python 버전
            (r'FROM\s+python:([\d.]+)', 'Python'),
            (r'FROM\s+([^:]+):([\d.]+)', 'Base Image'),
            
            # CUDA 버전
            (r'FROM\s+nvidia/cuda:([\d.]+)', 'CUDA'),
            (r'cuda-version=([\d.]+)', 'CUDA Version'),
            
            # Node.js 버전
            (r'FROM\s+node:([\d.]+)', 'Node.js'),
            
            # 기타 런타임
            (r'ENV\s+PYTHON_VERSION=([\d.]+)', 'Python ENV'),
            (r'ENV\s+NODE_VERSION=([\d.]+)', 'Node ENV'),
        ]
        
        for dockerfile in Path(".").glob("Dockerfile*"):
            try:
                with open(dockerfile, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                versions = {}
                for pattern, version_type in dockerfile_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        if version_type not in versions:
                            versions[version_type] = []
                        versions[version_type].extend(matches)
                
                if versions:
                    self.dockerfile_versions[str(dockerfile)] = versions
                    
            except Exception as e:
                print(f"⚠️ Dockerfile 분석 실패: {dockerfile}, 오류: {e}")
    
    def _analyze_requirements(self):
        """Requirements 파일에서 라이브러리 버전 분석"""
        print("📦 Requirements 라이브러리 버전 분석 중...")
        
        # requirements 파일들 찾기
        requirements_files = list(Path(".").glob("requirements*.txt"))
        
        for req_file in requirements_files:
            try:
                with open(req_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                versions = {}
                lines = content.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # 패키지명과 버전 추출
                        match = re.match(r'^([a-zA-Z0-9_-]+)([<>=!~]+)([\d.a-zA-Z]+)', line)
                        if match:
                            package, operator, version = match.groups()
                            if package not in versions:
                                versions[package] = []
                            versions[package].append(f"{operator}{version}")
                
                if versions:
                    self.requirements_versions[str(req_file)] = versions
                    
            except Exception as e:
                print(f"⚠️ Requirements 분석 실패: {req_file}, 오류: {e}")
    
    def _check_version_conflicts(self):
        """버전 충돌 검사"""
        print("⚠️ 버전 충돌 검사 중...")
        
        # 알려진 호환성 문제 패턴
        known_conflicts = [
            # Transformers 관련
            ("transformers", "4.40.0", "tokenizers", "<0.14.0"),
            ("transformers", "4.35.0", "tokenizers", "<0.13.0"),
            
            # PyTorch 관련
            ("torch", "2.0.0", "torchvision", "<0.15.0"),
            ("torch", "1.13.0", "torchaudio", "<0.13.0"),
            
            # TensorFlow 관련
            ("tensorflow", "2.12.0", "keras", "!=2.12.0"),
            
            # NumPy 관련
            ("numpy", ">=1.24.0", "pandas", "<2.0.0"),
            
            # CUDA 관련
            ("torch", "2.0.0", "cuda", "!=11.8"),
        ]
        
        # 모든 requirements 파일에서 패키지 버전 수집
        all_packages = {}
        for req_file, versions in self.requirements_versions.items():
            for package, version_list in versions.items():
                if package not in all_packages:
                    all_packages[package] = []
                all_packages[package].extend([(req_file, v) for v in version_list])
        
        # 충돌 검사
        for package, versions in all_packages.items():
            if len(versions) > 1:
                # 같은 패키지가 여러 파일에서 다른 버전으로 정의됨
                self.version_conflicts.append({
                    'package': package,
                    'conflicts': versions,
                    'type': 'multiple_versions'
                })
        
        # 알려진 호환성 문제 검사
        for pkg1, ver1, pkg2, ver2 in known_conflicts:
            if pkg1 in all_packages and pkg2 in all_packages:
                # 호환성 문제 가능성 체크
                self.version_conflicts.append({
                    'package': f"{pkg1} vs {pkg2}",
                    'conflicts': [(pkg1, ver1), (pkg2, ver2)],
                    'type': 'known_compatibility_issue'
                })
    
    def _check_compatibility_issues(self):
        """호환성 문제 검사"""
        print("🔧 호환성 문제 검사 중...")
        
        # Python 버전 호환성
        python_versions = set()
        for dockerfile, versions in self.dockerfile_versions.items():
            if 'Python' in versions:
                python_versions.update(versions['Python'])
        
        if len(python_versions) > 1:
            self.compatibility_issues.append({
                'type': 'python_version_mismatch',
                'versions': list(python_versions),
                'description': '여러 Python 버전이 사용됨'
            })
        
        # CUDA 버전 호환성
        cuda_versions = set()
        for dockerfile, versions in self.dockerfile_versions.items():
            if 'CUDA' in versions:
                cuda_versions.update(versions['CUDA'])
        
        if len(cuda_versions) > 1:
            self.compatibility_issues.append({
                'type': 'cuda_version_mismatch',
                'versions': list(cuda_versions),
                'description': '여러 CUDA 버전이 사용됨'
            })
        
        # 라이브러리 버전 범위 검사
        for req_file, versions in self.requirements_versions.items():
            for package, version_list in versions.items():
                for version in version_list:
                    # 너무 광범위한 버전 범위 체크
                    if '>=' in version and '<' not in version:
                        self.compatibility_issues.append({
                            'type': 'unbounded_version',
                            'package': package,
                            'version': version,
                            'file': req_file,
                            'description': '상한선이 없는 버전 범위'
                        })
    
    def _generate_report(self):
        """분석 리포트 생성"""
        print("\n" + "="*60)
        print("📊 버전 및 환경 일치 점검 리포트")
        print("="*60)
        
        # 1. Dockerfile 런타임 버전
        print(f"\n🐳 Dockerfile 런타임 버전:")
        for dockerfile, versions in self.dockerfile_versions.items():
            print(f"   📁 {dockerfile}")
            for runtime, version_list in versions.items():
                # 버전이 튜플이면 문자열로 변환
                version_strs = []
                for v in version_list:
                    if isinstance(v, tuple):
                        version_strs.append(':'.join(v))
                    else:
                        version_strs.append(str(v))
                print(f"      - {runtime}: {', '.join(version_strs)}")
        
        # 2. Requirements 라이브러리 버전
        print(f"\n📦 Requirements 라이브러리 버전:")
        for req_file, versions in self.requirements_versions.items():
            print(f"   📁 {req_file}")
            for package, version_list in versions.items():
                print(f"      - {package}: {', '.join(version_list)}")
        
        # 3. 버전 충돌
        print(f"\n⚠️ 버전 충돌: {len(self.version_conflicts)}개")
        for conflict in self.version_conflicts[:5]:
            print(f"   - {conflict['package']}: {conflict['type']}")
            for file, version in conflict['conflicts']:
                print(f"     {file}: {version}")
        
        # 4. 호환성 문제
        print(f"\n🔧 호환성 문제: {len(self.compatibility_issues)}개")
        for issue in self.compatibility_issues[:5]:
            print(f"   - {issue['type']}: {issue['description']}")
        
        # 5. 권장사항
        print(f"\n💡 권장사항:")
        print(f"   1. 모든 Dockerfile에서 동일한 Python 버전 사용")
        print(f"   2. CUDA 버전 통일 (11.8 권장)")
        print(f"   3. 라이브러리 버전을 == 로 고정")
        print(f"   4. 호환성 문제가 있는 라이브러리 조합 해결")
        print(f"   5. Multi-stage build 또는 베이스 이미지 통일")
        
        # 6. 상세 리포트 저장
        self._save_detailed_report()
    
    def _save_detailed_report(self):
        """상세 리포트 저장"""
        report = {
            'summary': {
                'dockerfiles': len(self.dockerfile_versions),
                'requirements_files': len(self.requirements_versions),
                'version_conflicts': len(self.version_conflicts),
                'compatibility_issues': len(self.compatibility_issues)
            },
            'dockerfile_versions': self.dockerfile_versions,
            'requirements_versions': self.requirements_versions,
            'version_conflicts': self.version_conflicts,
            'compatibility_issues': self.compatibility_issues
        }
        
        with open('version_compatibility_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 상세 리포트 저장: version_compatibility_report.json")

def main():
    analyzer = VersionCompatibilityAnalyzer()
    analyzer.analyze_project()
    print("\n🎉 버전 및 환경 일치 점검 완료!")

if __name__ == "__main__":
    main() 