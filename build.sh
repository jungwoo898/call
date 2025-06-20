#!/bin/bash

# Callytics Docker 빌드 및 실행 스크립트
# 사용법: ./build.sh [build|run|clean|logs]

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 환경 확인
check_environment() {
    log_info "환경 확인 중..."
    
    # Docker 확인
    if ! command -v docker &> /dev/null; then
        log_error "Docker가 설치되지 않았습니다."
        exit 1
    fi
    
    # Docker Compose 확인
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose가 설치되지 않았습니다."
        exit 1
    fi
    
    # .env 파일 확인
    if [ ! -f ".env" ]; then
        log_warning ".env 파일이 없습니다. 환경변수를 확인해주세요."
    fi
    
    log_success "환경 확인 완료"
}

# Docker 이미지 빌드
build_image() {
    log_info "Docker 이미지 빌드 시작..."
    
    # 기존 이미지 제거 (선택사항)
    if [ "$1" == "--clean" ]; then
        log_info "기존 이미지 정리 중..."
        docker-compose down --rmi all --volumes --remove-orphans 2>/dev/null || true
    fi
    
    # 빌드 시작
    log_info "빌드 중... (약 15-20분 소요)"
    start_time=$(date +%s)
    
    if docker-compose build --no-cache; then
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        minutes=$((duration / 60))
        seconds=$((duration % 60))
        log_success "빌드 완료! (소요시간: ${minutes}분 ${seconds}초)"
    else
        log_error "빌드 실패"
        exit 1
    fi
}

# 서비스 실행
run_services() {
    log_info "Callytics 서비스 시작..."
    
    # 데이터베이스 초기화 확인
    if [ ! -f "Callytics_new.sqlite" ]; then
        log_info "데이터베이스 초기화 중..."
        python init_database.py
    fi
    
    # 서비스 시작
    if docker-compose up -d; then
        log_success "서비스 시작 완료"
        log_info "서비스 상태 확인 중..."
        sleep 5
        docker-compose ps
        
        echo ""
        log_info "접속 정보:"
        log_info "- Callytics API: http://localhost:8000"
        log_info "- API 문서: http://localhost:8000/docs"
        log_info "- Grafana: http://localhost:3000 (admin/admin)"
        log_info "- Prometheus: http://localhost:9090"
        
        echo ""
        log_info "로그 확인: docker-compose logs -f callytics"
    else
        log_error "서비스 시작 실패"
        exit 1
    fi
}

# 로그 확인
show_logs() {
    local service=${1:-callytics}
    log_info "${service} 서비스 로그 확인..."
    docker-compose logs -f "$service"
}

# 서비스 정리
clean_up() {
    log_info "서비스 정리 중..."
    
    if [ "$1" == "--all" ]; then
        log_warning "모든 데이터를 삭제합니다..."
        docker-compose down --rmi all --volumes --remove-orphans
        docker system prune -f
        log_success "완전 정리 완료"
    else
        docker-compose down
        log_success "서비스 정지 완료"
    fi
}

# 상태 확인
check_status() {
    log_info "서비스 상태 확인..."
    docker-compose ps
    
    echo ""
    log_info "헬스체크..."
    if curl -s http://localhost:8000/health > /dev/null; then
        log_success "Callytics API 정상 동작"
    else
        log_warning "Callytics API 응답 없음"
    fi
}

# 도움말
show_help() {
    echo "Callytics Docker 빌드 및 실행 스크립트"
    echo ""
    echo "사용법: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  build [--clean]    Docker 이미지 빌드 (--clean: 기존 이미지 삭제)"
    echo "  run               서비스 실행"
    echo "  logs [SERVICE]    로그 확인 (기본: callytics)"
    echo "  status            서비스 상태 확인"
    echo "  stop              서비스 정지"
    echo "  clean [--all]     정리 (--all: 완전 삭제)"
    echo "  help              도움말 표시"
    echo ""
    echo "Examples:"
    echo "  $0 build          # 이미지 빌드"
    echo "  $0 build --clean  # 기존 이미지 삭제 후 빌드"
    echo "  $0 run            # 서비스 실행"
    echo "  $0 logs           # callytics 로그 확인"
    echo "  $0 logs grafana   # grafana 로그 확인"
    echo "  $0 status         # 상태 확인"
    echo "  $0 clean --all    # 완전 정리"
}

# 메인 로직
main() {
    case "${1:-help}" in
        "build")
            check_environment
            build_image "$2"
            ;;
        "run")
            check_environment
            run_services
            ;;
        "logs")
            show_logs "$2"
            ;;
        "status")
            check_status
            ;;
        "stop")
            docker-compose down
            log_success "서비스 정지 완료"
            ;;
        "clean")
            clean_up "$2"
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 스크립트 실행
main "$@" 