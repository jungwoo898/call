#!/usr/bin/env python3
"""
환경 설정 도우미 스크립트
비용 최소화 및 단계별 설정 안내
"""

import os
import sys
import subprocess
from typing import Dict, List, Optional

class EnvironmentSetup:
    """환경 설정 관리"""
    
    def __init__(self):
        self.required_env_vars = {
            'OPENAI_API_KEY': 'OpenAI API 키 (선택사항 - 비용 발생)',
            'AZURE_OPENAI_API_KEY': 'Azure OpenAI API 키 (선택사항 - 비용 발생)',
            'AZURE_OPENAI_ENDPOINT': 'Azure OpenAI 엔드포인트 (선택사항)',
            'HUGGINGFACE_TOKEN': 'HuggingFace 토큰 (선택사항 - 무료)',
            'REDIS_URL': 'Redis URL (기본값: redis://localhost:6379)',
            'DATABASE_URL': '데이터베이스 URL (기본값: sqlite:///Callytics_new.sqlite)'
        }
    
    def check_current_environment(self) -> Dict[str, bool]:
        """현재 환경 설정 확인"""
        print("🔍 현재 환경 설정 확인 중...")
        
        status = {}
        for var, description in self.required_env_vars.items():
            value = os.getenv(var)
            status[var] = bool(value)
            
            if value:
                print(f"✅ {var}: 설정됨")
            else:
                print(f"❌ {var}: 설정되지 않음 - {description}")
        
        return status
    
    def setup_basic_environment(self):
        """기본 환경 설정 (무료)"""
        print("\n🚀 기본 환경 설정 시작 (무료)")
        
        # .env 파일 생성
        env_content = """# Callytics 환경 설정
# 기본 설정 (무료)

# Redis 설정 (로컬)
REDIS_URL=redis://localhost:6379

# 데이터베이스 설정 (로컬 SQLite)
DATABASE_URL=sqlite:///Callytics_new.sqlite

# API 키들 (선택사항 - 비용 발생)
# OPENAI_API_KEY=your-openai-key-here
# AZURE_OPENAI_API_KEY=your-azure-key-here
# AZURE_OPENAI_ENDPOINT=your-azure-endpoint-here
# HUGGINGFACE_TOKEN=your-huggingface-token-here

# 개발 모드
DEV_MODE=true
MOCK_APIS=true
"""
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ .env 파일 생성 완료")
        print("📝 기본 설정으로 무료 테스트 가능")
    
    def setup_redis_local(self):
        """로컬 Redis 설정"""
        print("\n🔴 로컬 Redis 설정")
        
        try:
            # Docker로 Redis 실행
            subprocess.run([
                'docker', 'run', '-d', 
                '--name', 'callytics-redis',
                '-p', '6379:6379',
                'redis:7.2-alpine'
            ], check=True)
            
            print("✅ Redis 컨테이너 시작 완료")
            print("📍 Redis URL: redis://localhost:6379")
            
        except subprocess.CalledProcessError:
            print("⚠️ Redis 컨테이너 시작 실패")
            print("💡 docker-compose로 시도해보세요:")
            print("   docker-compose -f docker-compose-microservices.yml up -d redis")
    
    def test_basic_services(self):
        """기본 서비스 테스트"""
        print("\n🧪 기본 서비스 테스트")
        
        services = [
            'api-gateway',
            'audio-processor', 
            'database-service'
        ]
        
        print("다음 명령어로 기본 서비스 실행:")
        print("docker-compose -f docker-compose-microservices.yml up -d " + " ".join(services))
        
        print("\n📋 테스트 가능한 기능:")
        print("- 서비스 간 연결 확인")
        print("- 기본 API 엔드포인트 테스트")
        print("- 데이터베이스 연결 확인")
    
    def setup_api_keys(self):
        """API 키 설정 (선택사항)"""
        print("\n🔑 API 키 설정 (선택사항 - 비용 발생)")
        
        print("다음 API 키들을 설정하면 추가 기능 사용 가능:")
        print("1. OpenAI API Key: GPT 분석 기능")
        print("2. Azure OpenAI: 대안 GPT 서비스")
        print("3. HuggingFace Token: 모델 다운로드 (무료)")
        
        print("\n💰 예상 비용:")
        print("- OpenAI: $0.002 / 1K tokens (약 750단어)")
        print("- Azure OpenAI: 비슷한 가격대")
        print("- HuggingFace: 기본 무료")
        
        response = input("\nAPI 키를 설정하시겠습니까? (y/N): ")
        if response.lower() == 'y':
            self._interactive_api_setup()
    
    def _interactive_api_setup(self):
        """대화형 API 키 설정"""
        print("\n🔧 API 키 설정")
        
        # .env 파일 읽기
        env_content = ""
        if os.path.exists('.env'):
            with open('.env', 'r', encoding='utf-8') as f:
                env_content = f.read()
        
        # API 키 입력
        openai_key = input("OpenAI API Key (Enter로 건너뛰기): ").strip()
        azure_key = input("Azure OpenAI API Key (Enter로 건너뛰기): ").strip()
        azure_endpoint = input("Azure OpenAI Endpoint (Enter로 건너뛰기): ").strip()
        huggingface_token = input("HuggingFace Token (Enter로 건너뛰기): ").strip()
        
        # .env 파일 업데이트
        lines = env_content.split('\n')
        updated_lines = []
        
        for line in lines:
            if line.startswith('# OPENAI_API_KEY='):
                if openai_key:
                    updated_lines.append(f'OPENAI_API_KEY={openai_key}')
                else:
                    updated_lines.append(line)
            elif line.startswith('# AZURE_OPENAI_API_KEY='):
                if azure_key:
                    updated_lines.append(f'AZURE_OPENAI_API_KEY={azure_key}')
                else:
                    updated_lines.append(line)
            elif line.startswith('# AZURE_OPENAI_ENDPOINT='):
                if azure_endpoint:
                    updated_lines.append(f'AZURE_OPENAI_ENDPOINT={azure_endpoint}')
                else:
                    updated_lines.append(line)
            elif line.startswith('# HUGGINGFACE_TOKEN='):
                if huggingface_token:
                    updated_lines.append(f'HUGGINGFACE_TOKEN={huggingface_token}')
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        # MOCK_APIS 설정 업데이트
        has_api_keys = any([openai_key, azure_key, huggingface_token])
        mock_apis = 'false' if has_api_keys else 'true'
        
        # MOCK_APIS 라인 찾아서 업데이트
        for i, line in enumerate(updated_lines):
            if line.startswith('MOCK_APIS='):
                updated_lines[i] = f'MOCK_APIS={mock_apis}'
                break
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write('\n'.join(updated_lines))
        
        print("✅ API 키 설정 완료")
        if has_api_keys:
            print("🎉 실제 API 기능 활성화됨")
        else:
            print("🤖 Mock API 모드로 실행됨 (비용 없음)")
    
    def show_cost_estimation(self):
        """비용 추정"""
        print("\n💰 비용 추정")
        print("=" * 50)
        
        print("📊 월 예상 비용 (1000건 분석 기준):")
        print("- OpenAI API: $10-50 (사용량에 따라)")
        print("- Azure OpenAI: $10-50 (사용량에 따라)")
        print("- Redis (로컬): $0")
        print("- 데이터베이스 (SQLite): $0")
        print("- 서버 인프라: $0 (로컬)")
        
        print("\n💡 비용 절약 팁:")
        print("1. Mock API 모드로 개발/테스트")
        print("2. 실제 API는 필요시에만 활성화")
        print("3. 로컬 환경에서 개발")
        print("4. 배치 처리로 API 호출 최소화")
    
    def run_full_setup(self):
        """전체 설정 실행"""
        print("🚀 Callytics 환경 설정 시작")
        print("=" * 50)
        
        # 1. 현재 환경 확인
        status = self.check_current_environment()
        
        # 2. 기본 환경 설정
        self.setup_basic_environment()
        
        # 3. Redis 설정
        self.setup_redis_local()
        
        # 4. API 키 설정 (선택사항)
        self.setup_api_keys()
        
        # 5. 비용 추정
        self.show_cost_estimation()
        
        # 6. 테스트 안내
        self.test_basic_services()
        
        print("\n🎉 환경 설정 완료!")
        print("다음 단계: docker-compose로 서비스 실행")

def main():
    """메인 함수"""
    setup = EnvironmentSetup()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'check':
            setup.check_current_environment()
        elif command == 'basic':
            setup.setup_basic_environment()
        elif command == 'redis':
            setup.setup_redis_local()
        elif command == 'api':
            setup.setup_api_keys()
        elif command == 'cost':
            setup.show_cost_estimation()
        else:
            print("사용법: python setup_environment.py [check|basic|redis|api|cost|full]")
    else:
        # 전체 설정 실행
        setup.run_full_setup()

if __name__ == "__main__":
    main() 