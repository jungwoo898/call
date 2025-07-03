@echo off
echo ========================================
echo 🚀 Callytics 전체 재빌드 및 통합 테스트
echo ========================================
echo.

echo 📋 1단계: 환경 검증
echo ----------------------------------------
python verify_version_unification.py
if %errorlevel% neq 0 (
    echo ❌ 환경 검증 실패
    pause
    exit /b 1
)
echo ✅ 환경 검증 완료
echo.

echo 🧹 2단계: 기존 컨테이너 정리
echo ----------------------------------------
docker-compose down --remove-orphans
docker system prune -f
echo ✅ 컨테이너 정리 완료
echo.

echo 🐳 3단계: Docker 이미지 재빌드
echo ----------------------------------------
echo 🔧 audio-processor 빌드 중...
docker build -f Dockerfile.audio-processor -t callytics/audio-processor:latest .
if %errorlevel% neq 0 (
    echo ❌ audio-processor 빌드 실패
    pause
    exit /b 1
)

echo 🔧 llm-analyzer 빌드 중...
docker build -f Dockerfile.llm-analyzer -t callytics/llm-analyzer:latest .
if %errorlevel% neq 0 (
    echo ❌ llm-analyzer 빌드 실패
    pause
    exit /b 1
)

echo 🔧 speech-recognizer 빌드 중...
docker build -f Dockerfile.speech-recognizer -t callytics/speech-recognizer:latest .
if %errorlevel% neq 0 (
    echo ❌ speech-recognizer 빌드 실패
    pause
    exit /b 1
)

echo 🔧 speaker-diarizer 빌드 중...
docker build -f Dockerfile.speaker-diarizer -t callytics/speaker-diarizer:latest .
if %errorlevel% neq 0 (
    echo ❌ speaker-diarizer 빌드 실패
    pause
    exit /b 1
)

echo 🔧 database-service 빌드 중...
docker build -f Dockerfile.database-service -t callytics/database-service:latest .
if %errorlevel% neq 0 (
    echo ❌ database-service 빌드 실패
    pause
    exit /b 1
)

echo 🔧 gateway 빌드 중...
docker build -f Dockerfile.gateway -t callytics/gateway:latest .
if %errorlevel% neq 0 (
    echo ❌ gateway 빌드 실패
    pause
    exit /b 1
)

echo 🔧 punctuation-restorer 빌드 중...
docker build -f Dockerfile.punctuation-restorer -t callytics/punctuation-restorer:latest .
if %errorlevel% neq 0 (
    echo ❌ punctuation-restorer 빌드 실패
    pause
    exit /b 1
)

echo 🔧 sentiment-analyzer 빌드 중...
docker build -f Dockerfile.sentiment-analyzer -t callytics/sentiment-analyzer:latest .
if %errorlevel% neq 0 (
    echo ❌ sentiment-analyzer 빌드 실패
    pause
    exit /b 1
)

echo 🔧 monitoring 빌드 중...
docker build -f Dockerfile.monitoring -t callytics/monitoring:latest .
if %errorlevel% neq 0 (
    echo ❌ monitoring 빌드 실패
    pause
    exit /b 1
)

echo ✅ 모든 Docker 이미지 빌드 완료
echo.

echo 🚀 4단계: 마이크로서비스 시작
echo ----------------------------------------
docker-compose up -d
if %errorlevel% neq 0 (
    echo ❌ 마이크로서비스 시작 실패
    pause
    exit /b 1
)
echo ✅ 마이크로서비스 시작 완료
echo.

echo ⏳ 5단계: 서비스 준비 대기 (30초)
echo ----------------------------------------
timeout /t 30 /nobreak > nul
echo ✅ 대기 완료
echo.

echo 🧪 6단계: 통합 테스트 실행
echo ----------------------------------------
python verify_all_services.py
if %errorlevel% neq 0 (
    echo ❌ 통합 테스트 실패
    echo.
    echo 📊 서비스 상태 확인:
    docker-compose ps
    pause
    exit /b 1
)
echo ✅ 통합 테스트 완료
echo.

echo 🎯 7단계: API 연동 테스트
echo ----------------------------------------
python test_api_contracts.py
if %errorlevel% neq 0 (
    echo ❌ API 연동 테스트 실패
    pause
    exit /b 1
)
echo ✅ API 연동 테스트 완료
echo.

echo 📊 8단계: 최종 상태 확인
echo ----------------------------------------
docker-compose ps
echo.
echo 🎉 전체 재빌드 및 통합 테스트 완료!
echo.
echo 📋 다음 단계:
echo    - 서비스 모니터링: docker-compose logs -f
echo    - 개별 서비스 로그: docker-compose logs [서비스명]
echo    - 서비스 중지: docker-compose down
echo.
pause 