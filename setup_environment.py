#!/usr/bin/env python3
"""
환경 설정 도우미 스크립트 (PostgreSQL 우선)
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
            'POSTGRES_HOST': 'PostgreSQL 호스트 (기본값: localhost)',
            'POSTGRES_DB': 'PostgreSQL 데이터베이스 (기본값: callytics)',
            'POSTGRES_USER': 'PostgreSQL 사용자 (기본값: callytics_user)',
            'POSTGRES_PASSWORD': 'PostgreSQL 비밀번호 (필수)',
            'DATABASE_URL': '데이터베이스 URL (PostgreSQL 우선, SQLite 폴백)'
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
        
        # PostgreSQL 연결 테스트
        postgres_configured = all([
            os.getenv('POSTGRES_HOST'),
            os.getenv('POSTGRES_DB'),
            os.getenv('POSTGRES_USER'),
            os.getenv('POSTGRES_PASSWORD')
        ])
        
        if postgres_configured:
            print("✅ PostgreSQL: 완전히 구성됨")
        else:
            print("❌ PostgreSQL: 설정 부족 - 필수 환경변수가 없습니다")
            print("다음 환경변수를 설정하세요:")
            print("POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD")
        
        return status
    
    def setup_basic_environment(self):
        """기본 환경 설정 (PostgreSQL 우선)"""
        print("\n🚀 기본 환경 설정 시작 (PostgreSQL 우선)")
        
        # .env 파일 생성
        env_content = """# Callytics 환경 설정 (PostgreSQL 우선)
# 기본 설정 (무료)

# 🔐 보안 설정
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
SESSION_DURATION_HOURS=8
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCK_MINUTES=30
JWT_ISSUER=callytics-auth
JWT_AUDIENCE=callytics-api

# 🗄️ PostgreSQL 설정 (우선)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=callytics
POSTGRES_USER=callytics_user
POSTGRES_PASSWORD=secure_postgres_password_change_me
POSTGRES_MIN_CONNECTIONS=5
POSTGRES_MAX_CONNECTIONS=20

# 🗄️ SQLite 설정 (폴백용)
DATABASE_URL=sqlite:///Callytics_new.sqlite

# 🔴 Redis 설정
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_MAX_CONNECTIONS=50

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
        print("📝 PostgreSQL 전용 설정으로 구성됨")
        print("🔧 PostgreSQL 환경변수가 필수로 설정됨")
    
    def setup_postgresql_local(self):
        """로컬 PostgreSQL 설정"""
        print("\n🐘 로컬 PostgreSQL 설정")
        
        try:
            # Docker로 PostgreSQL 실행
            subprocess.run([
                'docker', 'run', '-d', 
                '--name', 'callytics-postgres',
                '-e', 'POSTGRES_DB=callytics',
                '-e', 'POSTGRES_USER=callytics_user',
                '-e', 'POSTGRES_PASSWORD=secure_postgres_password_change_me',
                '-p', '5432:5432',
                'postgres:15-alpine'
            ], check=True)
            
            print("✅ PostgreSQL 컨테이너 시작 완료")
            print("📍 PostgreSQL URL: postgresql://callytics_user:secure_postgres_password_change_me@localhost:5432/callytics")
            
        except subprocess.CalledProcessError:
            print("⚠️ PostgreSQL 컨테이너 시작 실패")
            print("💡 docker-compose로 시도해보세요:")
            print("   docker-compose -f docker-compose-microservices.yml up -d postgres")
    
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
            'postgres',  # PostgreSQL 우선
            'redis',
            'api-gateway',
            'audio-processor', 
            'database-service'
        ]
        
        print("다음 명령어로 기본 서비스 실행:")
        print("docker-compose -f docker-compose-microservices.yml up -d " + " ".join(services))
        
        print("\n📋 테스트 가능한 기능:")
        print("- PostgreSQL 연결 확인")
        print("- 서비스 간 연결 확인")
        print("- 기본 API 엔드포인트 테스트")
        print("- 데이터베이스 마이그레이션 확인")
    
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
        print("- PostgreSQL (로컬): $0")
        print("- Redis (로컬): $0")
        print("- 총 예상 비용: $10-100 (API 사용량에 따라)")
        
        print("\n💡 비용 절약 팁:")
        print("1. HuggingFace 무료 모델 우선 사용")
        print("2. Mock API 모드로 개발/테스트")
        print("3. 배치 처리로 API 호출 최소화")
        print("4. 캐싱 활용으로 중복 분석 방지")
    
    def run_full_setup(self):
        """전체 설정 실행"""
        print("🚀 Callytics 전체 환경 설정")
        print("=" * 50)
        
        # 1. 기본 환경 설정
        self.setup_basic_environment()
        
        # 2. PostgreSQL 설정
        self.setup_postgresql_local()
        
        # 3. Redis 설정
        self.setup_redis_local()
        
        # 4. API 키 설정 (선택사항)
        self.setup_api_keys()
        
        # 5. 비용 추정
        self.show_cost_estimation()
        
        print("\n✅ 전체 설정 완료!")
        print("다음 단계:")
        print("1. docker-compose -f docker-compose-microservices.yml up -d")
        print("2. python src/db/migrate_to_postgresql.py")
        print("3. API 테스트: curl http://localhost:8000/health")

def main():
    """메인 실행 함수"""
    setup = EnvironmentSetup()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "check":
            setup.check_current_environment()
        elif command == "basic":
            setup.setup_basic_environment()
        elif command == "postgresql":
            setup.setup_postgresql_local()
        elif command == "redis":
            setup.setup_redis_local()
        elif command == "api-keys":
            setup.setup_api_keys()
        elif command == "test":
            setup.test_basic_services()
        elif command == "cost":
            setup.show_cost_estimation()
        elif command == "full":
            setup.run_full_setup()
        else:
            print("❌ 알 수 없는 명령어")
            print("사용법: python setup_environment.py [check|basic|postgresql|redis|api-keys|test|cost|full]")
    else:
        # 대화형 모드
        print("🔧 Callytics 환경 설정 도우미")
        print("=" * 50)
        
        while True:
            print("\n선택하세요:")
            print("1. 현재 환경 확인")
            print("2. 기본 환경 설정")
            print("3. PostgreSQL 설정")
            print("4. Redis 설정")
            print("5. API 키 설정")
            print("6. 서비스 테스트")
            print("7. 비용 추정")
            print("8. 전체 설정")
            print("0. 종료")
            
            choice = input("\n선택 (0-8): ").strip()
            
            if choice == "1":
                setup.check_current_environment()
            elif choice == "2":
                setup.setup_basic_environment()
            elif choice == "3":
                setup.setup_postgresql_local()
            elif choice == "4":
                setup.setup_redis_local()
            elif choice == "5":
                setup.setup_api_keys()
            elif choice == "6":
                setup.test_basic_services()
            elif choice == "7":
                setup.show_cost_estimation()
            elif choice == "8":
                setup.run_full_setup()
            elif choice == "0":
                print("👋 설정 도우미를 종료합니다")
                break
            else:
                print("❌ 잘못된 선택입니다")

if __name__ == "__main__":
    main() 