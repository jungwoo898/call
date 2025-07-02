@echo off
echo ========================================
echo 모니터링 서비스들 빌드 시작
echo ========================================

echo 1단계: Prometheus 시작...
docker-compose -f docker-compose-microservices.yml up -d --remove-orphans prometheus
if %errorlevel% neq 0 (
    echo Prometheus 시작 실패
    pause
    exit /b 1
)

echo 2단계: Grafana 시작...
docker-compose -f docker-compose-microservices.yml up -d --remove-orphans grafana
if %errorlevel% neq 0 (
    echo Grafana 시작 실패
    pause
    exit /b 1
)

echo ========================================
echo 모니터링 서비스들 빌드 완료!
echo ========================================
echo.
echo 모든 서비스가 실행 중입니다!
echo.
echo 접속 주소:
echo - API Gateway: http://localhost:8000
echo - Grafana: http://localhost:3000 (admin/admin)
echo - Prometheus: http://localhost:9090
echo.
pause 