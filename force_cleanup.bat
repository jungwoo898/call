@echo off
echo ========================================
echo 강제 정리 시작
echo ========================================

echo 1단계: 모든 컨테이너 강제 중지...
for /f "tokens=*" %%i in ('docker ps -aq') do docker stop %%i 2>nul
if %errorlevel% neq 0 (
    echo 일부 컨테이너 중지 실패
)

echo 2단계: 모든 컨테이너 강제 제거...
for /f "tokens=*" %%i in ('docker ps -aq') do docker rm -f %%i 2>nul
if %errorlevel% neq 0 (
    echo 일부 컨테이너 제거 실패
)

echo 3단계: callytics 관련 컨테이너 특별 처리...
docker rm -f callytics-redis 2>nul
docker rm -f callytics-api-gateway 2>nul
docker rm -f callytics-audio-processor 2>nul
docker rm -f callytics-speaker-diarizer 2>nul
docker rm -f callytics-speech-recognizer 2>nul
docker rm -f callytics-punctuation-restorer 2>nul
docker rm -f callytics-sentiment-analyzer 2>nul
docker rm -f callytics-llm-analyzer 2>nul
docker rm -f callytics-database-service 2>nul
docker rm -f callytics-monitoring 2>nul
docker rm -f prometheus 2>nul
docker rm -f grafana 2>nul

echo 4단계: 모든 컨테이너 정리...
docker container prune -f

echo 5단계: 모든 이미지 정리...
docker image prune -f

echo 6단계: 모든 볼륨 정리...
docker volume prune -f

echo 7단계: 모든 네트워크 정리...
docker network prune -f

echo ========================================
echo 강제 정리 완료!
echo ========================================
echo.
echo 이제 build_cpu_services.bat를 실행하세요.
echo.
pause 