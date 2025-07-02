@echo off
echo ========================================
echo CPU 서비스들 빌드 시작
echo ========================================

echo 1단계: Redis 시작...
docker-compose -f docker-compose-microservices.yml up -d --remove-orphans redis
if %errorlevel% neq 0 (
    echo Redis 빌드 실패
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

echo 3단계: Audio Processor 빌드...
docker-compose -f docker-compose-microservices.yml up -d --build --remove-orphans audio-processor
if %errorlevel% neq 0 (
    echo Audio Processor 빌드 실패
    pause
    exit /b 1
)

echo 4단계: Punctuation Restorer 빌드...
docker-compose -f docker-compose-microservices.yml up -d --build --remove-orphans punctuation-restorer
if %errorlevel% neq 0 (
    echo Punctuation Restorer 빌드 실패
    pause
    exit /b 1
)

echo 5단계: Sentiment Analyzer 빌드...
docker-compose -f docker-compose-microservices.yml up -d --build --remove-orphans sentiment-analyzer
if %errorlevel% neq 0 (
    echo Sentiment Analyzer 빌드 실패
    pause
    exit /b 1
)

echo 6단계: API Gateway 빌드...
docker-compose -f docker-compose-microservices.yml up -d --build --remove-orphans api-gateway
if %errorlevel% neq 0 (
    echo API Gateway 빌드 실패
    pause
    exit /b 1
)

echo ========================================
echo CPU 서비스들 빌드 완료!
echo ========================================
echo.
echo 다음 명령어로 GPU 서비스들을 빌드하세요:
echo build_gpu_services.bat
echo.
pause 