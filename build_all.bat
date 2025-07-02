@echo off
echo ========================================
echo Callytics 마이크로서비스 전체 빌드
echo ========================================

echo 모든 서비스 빌드 시작...
docker-compose -f docker-compose-microservices.yml up -d --build

if %errorlevel% neq 0 (
    echo 빌드 실패!
    pause
    exit /b 1
)

echo ========================================
echo 모든 서비스 빌드 완료!
echo ========================================
echo.
echo 접속 주소:
echo - API Gateway: http://localhost:8000
echo - Grafana: http://localhost:3000 (admin/admin)
echo - Prometheus: http://localhost:9090
echo.
echo 서비스 상태 확인:
echo docker-compose -f docker-compose-microservices.yml ps
echo.
pause 