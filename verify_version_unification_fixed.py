#!/usr/bin/env python3
"""
버전 통일 작업 검증 스크립트 (수정된 버전)
생성된 파일들의 일관성과 완전성을 검증합니다.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

class VersionUnificationVerifier:
    def __init__(self):
        self.project_root = Path(".")
        self.reports = {}
        
    def verify_common_requirements(self) -> Dict:
        """requirements_common.txt 검증"""
        print("🔍 requirements_common.txt 검증 중...")
        
        common_file = self.project_root / "requirements_common.txt"
        if not common_file.exists():
            return {"status": "error", "message": "requirements_common.txt 파일이 없습니다."}
        
        with open(common_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 카테고리 구분자 확인
        categories = re.findall(r'# ={10,}\n# ([^\n]+)\n# ={10,}', content)
        
        # 버전 형식 확인 (x.y.z 또는 yyyymmdd 등 숫자만도 허용)
        version_pattern = r'^[a-zA-Z0-9_-]+==([0-9]+\.[0-9]+\.[0-9]+|[0-9]{8})'
        lines = content.split('\n')
        packages = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and '==' in line:
                if re.match(version_pattern, line):
                    packages.append(line.split('==')[0])
                else:
                    return {"status": "error", "message": f"잘못된 버전 형식: {line}"}
        
        return {
            "status": "success",
            "categories": len(categories),
            "packages": len(packages),
            "categories_list": categories
        }
    
    def verify_service_requirements(self) -> Dict:
        """서비스별 requirements.txt 검증"""
        print("🔍 서비스별 requirements.txt 검증 중...")
        
        service_files = list(self.project_root.glob("requirements.*.txt"))
        results = {}
        
        for file_path in service_files:
            service_name = file_path.stem.replace('requirements.', '')
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 공통 requirements 포함 확인
            if '-r requirements_common.txt' not in content:
                results[service_name] = {"status": "error", "message": "공통 requirements 포함 안됨"}
                continue
            
            # 서비스별 패키지 확인
            lines = content.split('\n')
            service_packages = []
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and '==' in line and not line.startswith('-r'):
                    service_packages.append(line.split('==')[0])
            
            results[service_name] = {
                "status": "success",
                "packages": len(service_packages),
                "package_list": service_packages
            }
        
        return results
    
    def verify_dockerfiles(self) -> Dict:
        """Dockerfile 표준화 검증"""
        print("🔍 Dockerfile 표준화 검증 중...")
        
        dockerfiles = list(self.project_root.glob("Dockerfile.*"))
        results = {}
        
        for file_path in dockerfiles:
            service_name = file_path.name.replace('Dockerfile.', '')
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # CUDA 버전 확인 (CUDA 베이스 이미지 사용 시)
            cuda_match = re.search(r'nvidia/cuda:(\d+\.\d+\.\d+)', content)
            if not cuda_match:
                # 11.8 형태도 허용
                cuda_match = re.search(r'nvidia/cuda:(\d+\.\d+)', content)
            cuda_version = cuda_match.group(1) if cuda_match else None
            
            # Python 베이스 이미지 확인 (db-migrator, test 등)
            python_base_match = re.search(r'FROM python:(\d+\.\d+)', content)
            python_base_version = python_base_match.group(1) if python_base_match else None
            
            # Python 버전 확인 (python3.11 형태)
            python_match = re.search(r'python3\.(\d+)', content)
            if not python_match:
                # python3.11-pip 형태도 확인
                python_match = re.search(r'python3\.(\d+)-', content)
            python_version = python_match.group(1) if python_match else None
            
            # 공통 requirements 설치 확인
            has_common_requirements = 'requirements_common.txt' in content
            
            # 헬스체크 확인
            has_healthcheck = 'HEALTHCHECK' in content
            
            # 특별한 서비스들 (CUDA 불필요)
            special_services = ['db-migrator', 'test']
            
            if service_name in special_services:
                # db-migrator, test는 Python 베이스 이미지 허용
                is_valid = (python_base_version == '3.11' and 
                           has_common_requirements and 
                           has_healthcheck)
                results[service_name] = {
                    "status": "success" if is_valid else "warning",
                    "base_image": f"python:{python_base_version}" if python_base_version else "unknown",
                    "python_version": python_version,
                    "has_common_requirements": has_common_requirements,
                    "has_healthcheck": has_healthcheck
                }
            else:
                # 일반 서비스는 CUDA 베이스 이미지 필요
                is_valid = ((cuda_version == '11.8' or cuda_version == '11.8.0') and 
                           python_version == '11' and 
                           has_common_requirements and 
                           has_healthcheck)
                results[service_name] = {
                    "status": "success" if is_valid else "warning",
                    "cuda_version": cuda_version,
                    "python_version": python_version,
                    "has_common_requirements": has_common_requirements,
                    "has_healthcheck": has_healthcheck
                }
        
        return results
    
    def verify_ci_config(self) -> Dict:
        """CI 설정 검증 (수정된 버전)"""
        print("🔍 CI 설정 검증 중...")
        
        ci_files = [
            ".github/workflows/version-check.yml",
            ".gitlab-ci.yml"
        ]
        
        results = {}
        
        for file_path in ci_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Python 버전 확인 (GitHub Actions와 GitLab CI 모두 지원)
                python_version = None
                
                # GitHub Actions 형식: python-version: "3.11"
                github_match = re.search(r'python-version:\s*[\'"]([^\'"]+)[\'"]', content)
                if github_match:
                    python_version = github_match.group(1)
                
                # GitLab CI 형식: PYTHON_VERSION: "3.11"
                if not python_version:
                    gitlab_match = re.search(r'PYTHON_VERSION:\s*[\'"]([^\'"]+)[\'"]', content)
                    if gitlab_match:
                        python_version = gitlab_match.group(1)
                
                # 자동화 기능 확인 (더 포괄적으로)
                automation_keywords = [
                    'version_compatibility_analyzer',
                    'version_unifier', 
                    'verify_version_unification',
                    'version_check',
                    'version_compatibility_check'
                ]
                has_automation = any(keyword in content for keyword in automation_keywords)
                
                # GitLab CI의 경우 stages와 jobs 구조도 확인
                if file_path == ".gitlab-ci.yml":
                    has_stages = 'stages:' in content
                    has_jobs = any(job in content for job in ['version_compatibility_check', 'version_unification_verify'])
                    has_automation = has_automation and has_stages and has_jobs
                
                results[file_path] = {
                    "status": "success" if python_version and has_automation else "warning",
                    "python_version": python_version,
                    "has_automation": has_automation
                }
            else:
                results[file_path] = {"status": "error", "message": "파일이 없습니다."}
        
        return results
    
    def run_verification(self) -> Dict:
        """전체 검증 실행"""
        print("🚀 버전 통일 검증 시작...\n")
        
        self.reports = {
            "common_requirements": self.verify_common_requirements(),
            "service_requirements": self.verify_service_requirements(),
            "dockerfiles": self.verify_dockerfiles(),
            "ci_config": self.verify_ci_config()
        }
        
        return self.reports
    
    def generate_report(self) -> str:
        """검증 리포트 생성"""
        print("\n" + "="*60)
        print("📊 버전 통일 검증 리포트")
        print("="*60)
        
        # 공통 requirements 검증 결과
        common_result = self.reports["common_requirements"]
        print(f"\n📦 공통 Requirements:")
        if common_result["status"] == "success":
            print(f"   ✅ 상태: 성공")
            print(f"   📋 카테고리 수: {common_result['categories']}")
            print(f"   📦 패키지 수: {common_result['packages']}")
        else:
            print(f"   ❌ 상태: 실패 - {common_result['message']}")
        
        # 서비스별 requirements 검증 결과
        print(f"\n🔧 서비스별 Requirements:")
        service_results = self.reports["service_requirements"]
        for service, result in service_results.items():
            if result["status"] == "success":
                print(f"   ✅ {service}: {result['packages']}개 패키지")
            else:
                print(f"   ❌ {service}: {result['message']}")
        
        # Dockerfile 검증 결과
        print(f"\n🐳 Dockerfile 표준화:")
        docker_results = self.reports["dockerfiles"]
        for service, result in docker_results.items():
            if result["status"] == "success":
                if service in ['db-migrator', 'test']:
                    print(f"   ✅ {service}: {result['base_image']}, Python {result['python_version']}")
                else:
                    print(f"   ✅ {service}: CUDA {result['cuda_version']}, Python {result['python_version']}")
            else:
                print(f"   ⚠️ {service}: 일부 표준화 미완료")
        
        # CI 설정 검증 결과
        print(f"\n🔧 CI 설정:")
        ci_results = self.reports["ci_config"]
        for file_path, result in ci_results.items():
            if result["status"] == "success":
                print(f"   ✅ {file_path}: Python {result['python_version']}")
            else:
                msg = result['message'] if 'message' in result else result.get('status', '오류')
                print(f"   ❌ {file_path}: {msg}")
        
        # 전체 통계
        total_services = len(service_results)
        successful_services = sum(1 for r in service_results.values() if r["status"] == "success")
        
        print(f"\n📈 전체 통계:")
        print(f"   📦 총 서비스 수: {total_services}")
        print(f"   ✅ 성공한 서비스: {successful_services}")
        print(f"   ❌ 실패한 서비스: {total_services - successful_services}")
        
        return "검증 완료"
    
    def save_report(self, filename: str = "version_unification_verification_report.json"):
        """검증 리포트 저장"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.reports, f, ensure_ascii=False, indent=2)
        print(f"\n💾 검증 리포트 저장: {filename}")

def main():
    verifier = VersionUnificationVerifier()
    verifier.run_verification()
    verifier.generate_report()
    verifier.save_report()

if __name__ == "__main__":
    main() 