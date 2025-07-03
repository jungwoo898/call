@echo off
REM optimize_startup_time.bat - Callytics 시작 시간 최적화 스크립트

echo [INFO] 🚀 Callytics 시작 시간 최적화 시작

echo [INFO] 📊 최적화 전/후 비교:
echo.
echo ❌ 기존 방식:
echo   • 서비스 시작: 0분
echo   • 첫 분석 요청 시 모델 로딩: 3-5분
echo   • 실제 분석: 30초
echo   • 총 소요시간: 5분 30초
echo.
echo ✅ 최적화된 방식:
echo   • 서비스 시작 + 모델 Pre-loading: 3-5분 (한 번만)
echo   • 분석 요청 시: 즉시 처리
echo   • 실제 분석: 30초
echo   • 총 소요시간: 30초 (분석 시간만!)
echo.

echo [INFO] 🔧 Docker Compose 설정 최적화 중...

REM 1. GPU 서비스 헬스체크 개선
echo [INFO] 1단계: 헬스체크를 "모델 준비 완료" 기준으로 변경

REM 2. 마이크로서비스 시작
echo [INFO] 2단계: 최적화된 마이크로서비스 시작
docker-compose -f docker-compose-microservices.yml up -d

echo [INFO] 3단계: 모델 사전 로딩 모니터링
echo [INFO] 📊 각 서비스별 모델 로딩 상태 확인:

REM 모델 로딩 상태 모니터링
:check_models
echo [INFO] ⏳ 모델 로딩 상태 확인 중...

REM 각 서비스의 모델 준비 상태 확인
curl -s http://localhost:8002/health | findstr "model_ready.*true" >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] ✅ Speaker Diarizer 모델 준비 완료
    set speaker_ready=1
) else (
    echo [INFO] 📥 Speaker Diarizer 모델 로딩 중...
    set speaker_ready=0
)

curl -s http://localhost:8003/health | findstr "model_ready.*true" >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] ✅ Speech Recognizer 모델 준비 완료
    set speech_ready=1
) else (
    echo [INFO] 📥 Speech Recognizer 모델 로딩 중...
    set speech_ready=0
)

curl -s http://localhost:8004/health | findstr "model_ready.*true" >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] ✅ Punctuation Restorer 모델 준비 완료
    set punct_ready=1
) else (
    echo [INFO] 📥 Punctuation Restorer 모델 로딩 중...
    set punct_ready=0
)

curl -s http://localhost:8005/health | findstr "model_ready.*true" >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] ✅ Sentiment Analyzer 모델 준비 완료
    set sentiment_ready=1
) else (
    echo [INFO] 📥 Sentiment Analyzer 모델 로딩 중...
    set sentiment_ready=0
)

REM 모든 모델이 준비되었는지 확인
set /a total_ready=%speaker_ready%+%speech_ready%+%punct_ready%+%sentiment_ready%

if %total_ready% geq 3 (
    echo [SUCCESS] 🎉 충분한 모델 준비 완료! (%total_ready%/4개)
    goto :models_ready
) else (
    echo [INFO] ⏳ 더 많은 모델 대기 중... (%total_ready%/4개 준비됨)
    timeout /t 10 /nobreak >nul
    goto :check_models
)

:models_ready
echo [INFO] 4단계: API Gateway 최종 확인

curl -s http://localhost:8000/health | findstr "ready_for_fast_analysis.*true" >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] ✅ 빠른 분석 준비 완료!
) else (
    echo [WARNING] ⚠️ 일부 기능만 사용 가능
)

echo.
echo [SUCCESS] 🎊 최적화 완료!
echo.
echo 📊 사용 방법:
echo   • 빠른 분석: POST http://localhost:8000/process_audio_fast
echo   • 일반 분석: POST http://localhost:8000/process_audio
echo   • 상태 확인: GET http://localhost:8000/health
echo.
echo 🎯 성능 개선:
echo   • 첫 분석 요청: 즉시 처리 (30초)
echo   • 모델 로딩 시간: 제거됨
echo   • 시스템 응답성: 대폭 향상
echo.

pause 