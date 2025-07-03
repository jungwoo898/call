@echo off
echo 🚀 Callytics CPU 서비스 빌드 시작
echo =================================

echo.
echo 📊 1단계: 데이터베이스 서비스 빌드
docker build -f Dockerfile.database-service -t callytics-database:latest .
if %errorlevel% neq 0 (
    echo ❌ 데이터베이스 서비스 빌드 실패
    pause
    exit /b 1
)

echo.
echo 🌐 2단계: 게이트웨이 서비스 빌드
docker build -f Dockerfile.gateway -t callytics-gateway:latest .
if %errorlevel% neq 0 (
    echo ❌ 게이트웨이 서비스 빌드 실패
    pause
    exit /b 1
)

echo.
echo 🎵 3단계: 오디오 프로세서 빌드
docker build -f Dockerfile.audio-processor -t callytics-audio-processor:latest .
if %errorlevel% neq 0 (
    echo ❌ 오디오 프로세서 빌드 실패
    pause
    exit /b 1
)

echo.
echo 😊 4단계: 감정 분석 서비스 빌드 (CPU 전용)
docker build -f Dockerfile.sentiment-analyzer -t callytics-sentiment:latest .
if %errorlevel% neq 0 (
    echo ❌ 감정 분석 서비스 빌드 실패
    pause
    exit /b 1
)

echo.
echo 📝 5단계: 문장부호 복원 서비스 빌드 (CPU 전용)
docker build -f Dockerfile.punctuation-restorer -t callytics-punctuation:latest .
if %errorlevel% neq 0 (
    echo ❌ 문장부호 복원 서비스 빌드 실패
    pause
    exit /b 1
)

echo.
echo ✅ CPU 서비스 빌드 완료!
echo.
echo 📋 빌드된 이미지 목록:
docker images | findstr callytics
echo.
echo 🚀 CPU 서비스 실행 준비 완료!
echo docker-compose up database gateway audio-processor sentiment-analyzer punctuation-restorer -d
pause 