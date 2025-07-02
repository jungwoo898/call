@echo off
echo ========================================
echo 🚀 Callytics 마이크로서비스 시작
echo ========================================

REM 환경 변수 설정
set HUGGINGFACE_TOKEN=your_huggingface_token_here
set OPENAI_API_KEY=your_openai_api_key_here
set AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
set AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint_here

echo.
echo 📋 환경 변수 설정 완료
echo.

REM 기존 컨테이너 정리
echo 🧹 기존 컨테이너 정리 중...
docker-compose down

REM 마이크로서비스 시작
echo 🚀 마이크로서비스 시작 중...
docker-compose -f docker-compose-microservices.yml up -d

echo.
echo ✅ 마이크로서비스 시작 완료!
echo.
echo 📊 서비스 상태 확인:
echo   - API Gateway: http://localhost:8000
echo   - 오디오 처리: http://localhost:8001
echo   - 화자 분리: http://localhost:8002
echo   - 음성 인식: http://localhost:8003
echo   - 문장 부호: http://localhost:8004
echo   - 감정 분석: http://localhost:8005
echo   - LLM 분석: http://localhost:8006
echo   - 데이터베이스: http://localhost:8007
echo   - 모니터링: http://localhost:8008
echo   - Prometheus: http://localhost:9090
echo   - Grafana: http://localhost:3000
echo.
echo 🔍 로그 확인:
echo   docker-compose -f docker-compose-microservices.yml logs -f
echo.
echo 🛑 서비스 중지:
echo   docker-compose -f docker-compose-microservices.yml down
echo.

pause 