@echo off
echo ========================================
echo 간단한 서비스들 빌드 시작
echo ========================================

echo 1단계: Redis 시작...
docker-compose -f docker-compose-microservices.yml up -d --remove-orphans redis
if %errorlevel% neq 0 (
    echo Redis 시작 실패
    pause
    exit /b 1
)

echo 2단계: Database Service 빌드...
docker-compose -f docker-compose-microservices.yml up -d --build --remove-orphans database-service
if %errorlevel% neq 0 (
    echo Database Service 빌드 실패
    pause
    exit /b 1
)

echo 3단계: API Gateway 빌드...
docker-compose -f docker-compose-microservices.yml up -d --build --remove-orphans api-gateway
if %errorlevel% neq 0 (
    echo API Gateway 빌드 실패
    pause
    exit /b 1
)

echo ========================================
echo 기본 서비스들 빌드 완료!
echo ========================================
echo.
echo 접속 주소:
echo - API Gateway: http://localhost:8000
echo.
pause 