#!/bin/bash

# Docker 환경 설정 및 호환성 검증 스크립트
# Python 3.10 + CUDA 12.1 + 의존성 최적화

set -e

echo "=== Callytics Docker 환경 설정 및 호환성 검증 ==="
echo

# 1. 시스템 요구사항 확인
echo "1. 시스템 요구사항 확인 중..."

# Docker 설치 확인
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되지 않았습니다"
    exit 1
fi

# Docker Compose 설치 확인
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose가 설치되지 않았습니다"
    exit 1
fi

# NVIDIA Docker 확인 (GPU 사용 시)
if command -v nvidia-docker &> /dev/null || docker info | grep -q nvidia; then
    echo "✅ NVIDIA Docker 지원 확인됨"
    GPU_AVAILABLE=true
else
    echo "⚠️  NVIDIA Docker가 없습니다. CPU 모드로 실행됩니다"
    GPU_AVAILABLE=false
fi

echo

# 2. 환경 파일 생성
echo "2. 환경 설정 파일 생성 중..."

if [ ! -f .env ]; then
    cat > .env << EOF
# API 키 설정 (필요에 따라 수정)
OPENAI_API_KEY=your_openai_api_key_here
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
HUGGINGFACE_TOKEN=your_huggingface_token_here

# GPU 설정
CUDA_VISIBLE_DEVICES=0
PYTORCH_CUDA_MEMORY_FRACTION=0.8

# 로그 레벨
LOG_LEVEL=INFO
EOF
    echo "✅ .env 파일 생성됨 (API 키를 수정하세요)"
else
    echo "✅ .env 파일이 이미 존재합니다"
fi

echo

# 3. 디렉토리 생성
echo "3. 필요 디렉토리 생성 중..."

mkdir -p audio temp logs data .cache
chmod 755 audio temp logs data .cache

echo "✅ 디렉토리 생성 완료"
echo

# 4. Docker 이미지 빌드
echo "4. Docker 이미지 빌드 중... (시간이 오래 걸릴 수 있습니다)"

if docker-compose build callytics; then
    echo "✅ Docker 이미지 빌드 성공"
else
    echo "❌ Docker 이미지 빌드 실패"
    exit 1
fi

echo

# 5. 호환성 검증 실행
echo "5. 호환성 검증 실행 중..."

if docker-compose run --rm compatibility-check; then
    echo "✅ 호환성 검증 통과"
else
    echo "❌ 호환성 검증 실패 - 설정을 확인하세요"
    exit 1
fi

echo

# 6. 헬스체크 및 서비스 시작
echo "6. 서비스 시작 및 상태 확인 중..."

# 백그라운드에서 서비스 시작
docker-compose up -d callytics

echo "서비스 시작됨. 헬스체크 대기 중..."

# 헬스체크 대기 (최대 3분)
for i in {1..18}; do
    if docker-compose ps callytics | grep -q "healthy"; then
        echo "✅ 서비스가 정상적으로 시작되었습니다"
        break
    elif [ $i -eq 18 ]; then
        echo "❌ 서비스 시작 타임아웃"
        docker-compose logs callytics | tail -20
        exit 1
    else
        echo "헬스체크 대기 중... ($i/18)"
        sleep 10
    fi
done

echo

# 7. 최종 상태 확인
echo "7. 최종 상태 확인..."

# 컨테이너 상태
echo "컨테이너 상태:"
docker-compose ps

echo

# API 엔드포인트 테스트
echo "API 엔드포인트 테스트:"
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API 서버 정상 동작"
else
    echo "⚠️  API 서버 응답 없음 - 로그를 확인하세요"
fi

echo

# 8. 사용 안내
echo "=== 설정 완료 ==="
echo
echo "🎉 Callytics Docker 환경이 성공적으로 설정되었습니다!"
echo
echo "사용 방법:"
echo "  • API 서버: http://localhost:8000"
echo "  • 개발 모드: docker-compose --profile dev up -d"
echo "  • 로그 확인: docker-compose logs -f callytics"  
echo "  • 서비스 중지: docker-compose down"
echo "  • 모니터링: http://localhost:3000 (Grafana)"
echo
echo "주요 명령어:"
echo "  • 호환성 재검증: docker-compose --profile check run --rm compatibility-check"
echo "  • 컨테이너 재시작: docker-compose restart callytics"
echo "  • 이미지 재빌드: docker-compose build --no-cache callytics"
echo
echo "⚠️  중요 사항:"
echo "  • .env 파일에서 API 키를 설정하세요"
echo "  • GPU 사용 시 NVIDIA Docker가 필요합니다"
echo "  • 첫 실행 시 모델 다운로드로 시간이 걸릴 수 있습니다"

if [ "$GPU_AVAILABLE" = true ]; then
    echo "  • GPU 메모리: $(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)MB 사용 가능"
fi

echo 