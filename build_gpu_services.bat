@echo off
echo ========================================
echo GPU 서비스들 빌드 시작
echo ========================================

echo 1단계: Speaker Diarizer 빌드...
docker-compose -f docker-compose-microservices.yml up -d --build --remove-orphans speaker-diarizer
if %errorlevel% neq 0 (
    echo Speaker Diarizer 빌드 실패
    pause
    exit /b 1
)

echo 2단계: Speech Recognizer 빌드...
docker-compose -f docker-compose-microservices.yml up -d --build --remove-orphans speech-recognizer
if %errorlevel% neq 0 (
    echo Speech Recognizer 빌드 실패
    pause
    exit /b 1
)

echo 3단계: LLM Analyzer 빌드...
docker-compose -f docker-compose-microservices.yml up -d --build --remove-orphans llm-analyzer
if %errorlevel% neq 0 (
    echo LLM Analyzer 빌드 실패
    pause
    exit /b 1
)

echo ========================================
echo GPU 서비스들 빌드 완료!
echo ========================================
echo.
echo 다음 명령어로 모니터링 서비스들을 빌드하세요:
echo build_monitoring.bat
echo.
pause 