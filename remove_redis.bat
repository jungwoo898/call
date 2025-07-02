@echo off
echo ========================================
echo Redis 컨테이너 제거
echo ========================================

echo Redis 컨테이너 강제 제거...
docker rm -f callytics-redis
if %errorlevel% neq 0 (
    echo Redis 컨테이너가 이미 제거되었거나 존재하지 않습니다.
)

echo Redis 관련 볼륨 제거...
docker volume rm callytics_redis_data 2>nul
if %errorlevel% neq 0 (
    echo Redis 볼륨이 이미 제거되었거나 존재하지 않습니다.
)

echo ========================================
echo Redis 정리 완료!
echo ========================================
echo.
echo 이제 build_cpu_services.bat를 실행하세요.
echo.
pause 