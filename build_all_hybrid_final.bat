@echo off
echo 🚀 Callytics 하이브리드 마이크로서비스 최종 빌드 시작
echo ===================================================
echo Python 3.11 (웹/데이터/LLM) + Python 3.8 (음성/오디오)
echo 시작 시간: %date% %time%
echo.

echo 🔍 1단계: Python 3.8 오디오 서비스 호환성 검증
echo 시작: %time%
python verify_py38_audio_only.py
if %errorlevel% neq 0 (
    echo ❌ Python 3.8 오디오 서비스 호환성 검증 실패
    echo 실패 시간: %time%
    pause
    exit /b 1
)
echo ✅ Python 3.8 오디오 서비스 호환성 검증 완료: %time%

echo.
echo 🧹 2단계: 기존 이미지 정리
echo 시작: %time%
for /f "tokens=3" %%i in ('docker images ^| findstr callytics') do (
    echo 기존 이미지 제거: %%i
    docker rmi %%i 2>nul
)
echo ✅ 기존 이미지 정리 완료: %time%

echo.
echo ===================================================
echo 🐍 3단계: Python 3.11 서비스들 빌드 시작
echo ===================================================
echo 예상 시간: 2-3시간
echo.

echo.
echo 📊 3-1단계: 데이터베이스 서비스 빌드 (Python 3.11)
echo 시작: %time%
docker build -f Dockerfile.database-service -t callytics-database:latest .
if %errorlevel% neq 0 (
    echo ❌ 데이터베이스 서비스 빌드 실패
    pause
    exit /b 1
)
echo ✅ 데이터베이스 서비스 빌드 완료: %time%

echo.
echo 😊 3-2단계: 감정 분석 서비스 빌드 (Python 3.11)
echo 시작: %time%
docker build -f Dockerfile.sentiment-analyzer -t callytics-sentiment:latest .
if %errorlevel% neq 0 (
    echo ❌ 감정 분석 서비스 빌드 실패
    pause
    exit /b 1
)
echo ✅ 감정 분석 서비스 빌드 완료: %time%

echo.
echo 📝 3-3단계: 문장부호 복원 서비스 빌드 (Python 3.11)
echo 시작: %time%
docker build -f Dockerfile.punctuation-restorer -t callytics-punctuation:latest .
if %errorlevel% neq 0 (
    echo ❌ 문장부호 복원 서비스 빌드 실패
    pause
    exit /b 1
)
echo ✅ 문장부호 복원 서비스 빌드 완료: %time%

echo.
echo 🤖 3-4단계: LLM 분석 서비스 빌드 (Python 3.11)
echo 시작: %time%
docker build -f Dockerfile.llm-analyzer -t callytics-llm-analyzer:latest .
if %errorlevel% neq 0 (
    echo ❌ LLM 분석 서비스 빌드 실패
    pause
    exit /b 1
)
echo ✅ LLM 분석 서비스 빌드 완료: %time%

echo.
echo 🌐 3-5단계: 게이트웨이 서비스 빌드 (Python 3.11)
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
echo 🎵 4단계: Python 3.8 서비스들 빌드 시작
echo ===================================================
echo 예상 시간: 1-2시간
echo.

echo.
echo 🎵 4-1단계: 오디오 프로세서 빌드 (Python 3.8)
echo 시작: %time%
docker build -f Dockerfile.audio-processor -t callytics-audio-processor:latest .
if %errorlevel% neq 0 (
    echo ❌ 오디오 프로세서 빌드 실패
    pause
    exit /b 1
)
echo ✅ 오디오 프로세서 빌드 완료: %time%

echo.
echo 🎤 4-2단계: 화자 분리 서비스 빌드 (Python 3.8)
echo 시작: %time%
docker build -f Dockerfile.speaker-diarizer -t callytics-speaker-diarizer:latest .
if %errorlevel% neq 0 (
    echo ❌ 화자 분리 서비스 빌드 실패
    pause
    exit /b 1
)
echo ✅ 화자 분리 서비스 빌드 완료: %time%

echo.
echo 🗣️ 4-3단계: 음성 인식 서비스 빌드 (Python 3.8)
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
echo 📊 5단계: 모니터링 서비스들 빌드
echo ===================================================
echo 예상 시간: 30분
echo.

call build_monitoring.bat
if %errorlevel% neq 0 (
    echo ❌ 모니터링 서비스들 빌드 실패
    pause
    exit /b 1
)

echo.
echo ===================================================
echo 🎉 하이브리드 마이크로서비스 빌드 완료!
echo ===================================================
echo 완료 시간: %time%
echo.
echo 📋 빌드된 이미지 목록:
docker images | findstr callytics
echo.
echo 🚀 하이브리드 마이크로서비스 준비 완료!
echo Python 3.11 서비스: 5개 (웹/데이터/LLM)
echo Python 3.8 서비스: 3개 (음성/오디오)
echo 모니터링 서비스: 3개
echo.
echo 🎵 내일 아침 음성 파일 테스트 준비 완료!
echo.
echo 다음 명령어로 서비스 시작:
echo docker-compose up -d
echo.
echo 🎉 하루종일 빌드 성공!
pause 