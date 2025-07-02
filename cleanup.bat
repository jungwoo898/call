@echo off
echo ========================================
echo 기존 컨테이너 정리 시작
echo ========================================

echo 1단계: 모든 컨테이너 중지...
docker-compose -f docker-compose-microservices.yml down
if %errorlevel% neq 0 (
    echo 일부 컨테이너 중지 실패
)

echo 2단계: 모든 컨테이너 제거...
docker container prune -f
if %errorlevel% neq 0 (
    echo 컨테이너 정리 실패
)

echo 3단계: 사용하지 않는 이미지 정리...
docker image prune -f
if %errorlevel% neq 0 (
    echo 이미지 정리 실패
)

echo 4단계: 사용하지 않는 볼륨 정리...
docker volume prune -f
if %errorlevel% neq 0 (
    echo 볼륨 정리 실패
)

echo ========================================
echo 정리 완료!
echo ========================================
echo.
echo 이제 build_cpu_services.bat를 실행하세요.
echo.
pause 