#!/bin/bash
# wait-for-services.sh - Callytics 마이크로서비스 시작 대기 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 서비스 목록 (시작 순서대로)
declare -A SERVICES=(
    ["database-service"]="8007"
    ["audio-processor"]="8001"
    ["punctuation-restorer"]="8004"
    ["sentiment-analyzer"]="8005"
    ["speaker-diarizer"]="8002"
    ["speech-recognizer"]="8003"
    ["llm-analyzer"]="8006"
    ["api-gateway"]="8000"
)

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 헬스체크 함수
check_health() {
    local service_name=$1
    local port=$2
    local max_attempts=${3:-30}
    local wait_seconds=${4:-5}
    
    log_info "🔍 $service_name 서비스 헬스체크 시작 (포트: $port)"
    
    for i in $(seq 1 $max_attempts); do
        if curl -f -s "http://localhost:$port/health" > /dev/null 2>&1; then
            log_success "✅ $service_name 서비스 준비 완료 ($i/$max_attempts)"
            return 0
        else
            if [ $i -eq $max_attempts ]; then
                log_error "❌ $service_name 서비스 시작 실패 (타임아웃)"
                return 1
            else
                log_warning "⏳ $service_name 서비스 대기 중... ($i/$max_attempts)"
                sleep $wait_seconds
            fi
        fi
    done
}

# GPU 서비스 확장 대기
check_gpu_service() {
    local service_name=$1
    local port=$2
    
    log_info "🎯 GPU 서비스 $service_name 확장 대기 (최대 5분)"
    check_health "$service_name" "$port" 60 5
}

# 메인 실행
main() {
    log_info "🚀 Callytics 마이크로서비스 시작 대기 시작"
    
    # 1단계: 기본 서비스들
    log_info "📋 1단계: 기본 서비스 시작 대기"
    
    for service in "database-service" "audio-processor" "punctuation-restorer" "sentiment-analyzer"; do
        if ! check_health "$service" "${SERVICES[$service]}" 20 3; then
            log_error "서비스 시작 실패: $service"
            exit 1
        fi
    done
    
    # 2단계: GPU 서비스들 (더 긴 대기 시간)
    log_info "🎮 2단계: GPU 서비스 시작 대기"
    
    for service in "speaker-diarizer" "speech-recognizer"; do
        if ! check_gpu_service "$service" "${SERVICES[$service]}"; then
            log_error "GPU 서비스 시작 실패: $service"
            exit 1
        fi
    done
    
    # 3단계: LLM 서비스
    log_info "🤖 3단계: LLM 서비스 시작 대기"
    
    if ! check_health "llm-analyzer" "${SERVICES[llm-analyzer]}" 15 3; then
        log_error "LLM 서비스 시작 실패"
        exit 1
    fi
    
    # 4단계: API Gateway (최종)
    log_info "🌐 4단계: API Gateway 시작 대기"
    
    if ! check_health "api-gateway" "${SERVICES[api-gateway]}" 10 2; then
        log_error "API Gateway 시작 실패"
        exit 1
    fi
    
    # 최종 확인
    log_info "🔍 최종 시스템 상태 확인"
    
    if curl -f -s "http://localhost:8000/health" > /dev/null 2>&1; then
        log_success "🎉 모든 서비스가 성공적으로 시작되었습니다!"
        log_info "📊 시스템 상태:"
        log_info "   • API Gateway: http://localhost:8000"
        log_info "   • 헬스체크: http://localhost:8000/health"
        log_info "   • API 문서: http://localhost:8000/docs"
        return 0
    else
        log_error "❌ 최종 시스템 확인 실패"
        return 1
    fi
}

# 스크립트 실행
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 