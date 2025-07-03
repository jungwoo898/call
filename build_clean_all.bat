@echo off
echo 🚀 Callytics 마이크로서비스 전체 빌드 시작 (깨끗한 빌드)
echo ========================================================

echo.
echo 🧹 기존 이미지 정리 중...
for /f "tokens=3" %%i in ('docker images ^| findstr callytics') do (
    echo 기존 이미지 제거: %%i
    docker rmi %%i 2>nul
)

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
echo 😊 4단계: 감정 분석 서비스 빌드 (CPU)
docker build -f Dockerfile.sentiment-analyzer -t callytics-sentiment:latest .
if %errorlevel% neq 0 (
    echo ❌ 감정 분석 서비스 빌드 실패
    pause
    exit /b 1
)

echo.
echo 📝 5단계: 문장부호 복원 서비스 빌드 (CPU)
docker build -f Dockerfile.punctuation-restorer -t callytics-punctuation:latest .
if %errorlevel% neq 0 (
    echo ❌ 문장부호 복원 서비스 빌드 실패
    pause
    exit /b 1
)

echo.
echo 🎤 6단계: 화자 분리 서비스 빌드 (GPU)
docker build -f Dockerfile.speaker-diarizer -t callytics-speaker-diarizer:latest .
if %errorlevel% neq 0 (
    echo ❌ 화자 분리 서비스 빌드 실패
    pause
    exit /b 1
)

echo.
echo 🗣️ 7단계: 음성 인식 서비스 빌드 (GPU)
docker build -f Dockerfile.speech-recognizer -t callytics-speech-recognizer:latest .
if %errorlevel% neq 0 (
    echo ❌ 음성 인식 서비스 빌드 실패
    pause
    exit /b 1
)

echo.
echo 🤖 8단계: LLM 분석 서비스 빌드 (GPU)
docker build -f Dockerfile.llm-analyzer -t callytics-llm-analyzer:latest .
if %errorlevel% neq 0 (
    echo ❌ LLM 분석 서비스 빌드 실패
    pause
    exit /b 1
)

echo.
echo 📊 9단계: 모니터링 서비스 빌드
docker build -f Dockerfile.monitoring -t callytics-monitoring:latest .
if %errorlevel% neq 0 (
    echo ❌ 모니터링 서비스 빌드 실패
    pause
    exit /b 1
)

echo.
echo ✅ 모든 서비스 빌드 완료!
echo.
echo 📋 빌드된 이미지 목록:
docker images | findstr callytics
echo.
echo 🚀 서비스 실행 준비 완료!
echo docker-compose up -d
pause 