@echo off
chcp 65001>nul
echo 📊 모니터링 서비스들 빌드 시작
echo ==============================
echo 시작 시간: %date% %time%
echo.

echo 📈 1단계: 모니터링 서비스 빌드
echo 시작: %time%
docker build -f Dockerfile.monitoring -t callytics-monitoring:latest .
if %errorlevel% neq 0 (
    echo ❌ 모니터링 서비스 빌드 실패
    echo 실패 시간: %time%
    pause
    exit /b 1
)
echo ✅ 모니터링 서비스 빌드 완료: %time%

echo.
echo 📊 2단계: Prometheus 이미지 풀
echo 시작: %time%
docker pull prom/prometheus:latest
if %errorlevel% neq 0 (
    echo ❌ Prometheus 이미지 풀 실패
    pause
    exit /b 1
)
echo ✅ Prometheus 이미지 풀 완료: %time%

echo.
echo 📈 3단계: Grafana 이미지 풀
echo 시작: %time%
docker pull grafana/grafana:latest
if %errorlevel% neq 0 (
    echo ❌ Grafana 이미지 풀 실패
    pause
    exit /b 1
)
echo ✅ Grafana 이미지 풀 완료: %time%

echo.
echo ✅ 모니터링 서비스들 빌드 완료!
echo 완료 시간: %time%
echo.
echo 📋 모니터링 이미지 목록:
docker images | findstr -E "(callytics-monitoring|prometheus|grafana)"
echo.
echo 📊 모니터링 대시보드 준비 완료!
pause 