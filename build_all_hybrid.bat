@echo off
echo 🚀 Callytics 하이브리드 마이크로서비스 전체 빌드 시작
echo ===================================================
echo Python 3.11 (웹/데이터) + Python 3.8 (음성/오디오)
echo 시작 시간: %date% %time%
echo.

echo 🧹 기존 이미지 정리 중...
for /f "tokens=3" %%i in ('docker images ^| findstr callytics') do (
    echo 기존 이미지 제거: %%i
    docker rmi %%i 2>nul
)

echo.
echo ===================================================
echo 🐍 Python 3.11 서비스들 빌드 시작
echo ===================================================

echo.
echo 📊 1단계: 데이터베이스 서비스 빌드 (Python 3.11)
echo 시작: %time%
docker build -f Dockerfile.database-service -t callytics-database:latest .
if %errorlevel% neq 0 (
    echo ❌ 데이터베이스 서비스 빌드 실패
    pause
    exit /b 1
)
echo ✅ 데이터베이스 서비스 빌드 완료: %time%

echo.
echo 😊 2단계: 감정 분석 서비스 빌드 (Python 3.11)
echo 시작: %time%
docker build -f Dockerfile.sentiment-analyzer -t callytics-sentiment:latest .
if %errorlevel% neq 0 (
    echo ❌ 감정 분석 서비스 빌드 실패
    pause
    exit /b 1
)
echo ✅ 감정 분석 서비스 빌드 완료: %time%

echo.
echo 📝 3단계: 문장부호 복원 서비스 빌드 (Python 3.11)
echo 시작: %time%
docker build -f Dockerfile.punctuation-restorer -t callytics-punctuation:latest .
if %errorlevel% neq 0 (
    echo ❌ 문장부호 복원 서비스 빌드 실패
    pause
    exit /b 1
)
echo ✅ 문장부호 복원 서비스 빌드 완료: %time%

echo.
echo 🤖 4단계: LLM 분석 서비스 빌드 (Python 3.11)
echo 시작: %time%
docker build -f Dockerfile.llm-analyzer -t callytics-llm-analyzer:latest .
if %errorlevel% neq 0 (
    echo ❌ LLM 분석 서비스 빌드 실패
    pause
    exit /b 1
)
echo ✅ LLM 분석 서비스 빌드 완료: %time%

echo.
echo 🌐 5단계: 게이트웨이 서비스 빌드 (Python 3.11)
echo 시작: %time%
docker build -f Dockerfile.gateway -t callytics-gateway:latest .
if %errorlevel% neq 0 (
    echo ❌ 게이트웨이 서비스 빌드 실패
    pause
    exit /b 1
)
echo ✅ 게이트웨이 서비스 빌드 완료: %time%

echo.
echo ===================================================
echo 🎵 Python 3.8 서비스들 빌드 시작
echo ===================================================

echo.
echo 🎵 6단계: 오디오 프로세서 빌드 (Python 3.8)
echo 시작: %time%
docker build -f Dockerfile.audio-processor -t callytics-audio-processor:latest .
if %errorlevel% neq 0 (
    echo ❌ 오디오 프로세서 빌드 실패
    pause
    exit /b 1
)
echo ✅ 오디오 프로세서 빌드 완료: %time%

echo.
echo 🎤 7단계: 화자 분리 서비스 빌드 (Python 3.8)
echo 시작: %time%
docker build -f Dockerfile.speaker-diarizer -t callytics-speaker-diarizer:latest .
if %errorlevel% neq 0 (
    echo ❌ 화자 분리 서비스 빌드 실패
    pause
    exit /b 1
)
echo ✅ 화자 분리 서비스 빌드 완료: %time%

echo.
echo 🗣️ 8단계: 음성 인식 서비스 빌드 (Python 3.8)
echo 시작: %time%
docker build -f Dockerfile.speech-recognizer -t callytics-speech-recognizer:latest .
if %errorlevel% neq 0 (
    echo ❌ 음성 인식 서비스 빌드 실패
    pause
    exit /b 1
)
echo ✅ 음성 인식 서비스 빌드 완료: %time%

echo.
echo ===================================================
echo 🎉 모든 서비스 빌드 완료!
echo ===================================================
echo 완료 시간: %time%
echo.
echo 📋 빌드된 이미지 목록:
docker images | findstr callytics
echo.
echo 🚀 하이브리드 마이크로서비스 준비 완료!
echo Python 3.11 서비스: 5개 (웹/데이터/LLM)
echo Python 3.8 서비스: 3개 (음성/오디오)
echo.
echo 🎵 내일 아침 음성 파일 테스트 준비 완료!
echo docker-compose up -d
pause 