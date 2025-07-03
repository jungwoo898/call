@echo off
echo 🔧 Callytics API 테스트 자동화 스크립트
echo ========================================

echo.
echo 1️⃣ 마이크로서비스 실행 중...
docker-compose up -d

echo.
echo 2️⃣ 서비스 시작 대기 중... (30초)
timeout /t 30 /nobreak > nul

echo.
echo 3️⃣ 서비스 상태 확인...
docker-compose ps

echo.
echo 4️⃣ API 테스트 실행...
python test_api_contracts.py

echo.
echo 5️⃣ 테스트 완료!
echo.
pause 