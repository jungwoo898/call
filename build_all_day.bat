@echo off
echo 🌅 Callytics 하루종일 빌드 시작
echo ================================
echo 시작 시간: %date% %time%
echo 예상 완료: 내일 아침
echo.

echo 🧹 시스템 정리 중...
docker system prune -f
echo.

echo ===================================================
echo 🐍 1단계: Python 3.11 서비스들 빌드
echo ===================================================
echo 예상 시간: 2-3시간
echo.

call build_all_py311_services.bat
if %errorlevel% neq 0 (
    echo ❌ Python 3.11 서비스들 빌드 실패
    echo 실패 시간: %time%
    pause
    exit /b 1
)

echo.
echo ===================================================
echo 🎵 2단계: Python 3.8 서비스들 빌드
echo ===================================================
echo 예상 시간: 1-2시간
echo.

call build_all_py38_services.bat
if %errorlevel% neq 0 (
    echo ❌ Python 3.8 서비스들 빌드 실패
    echo 실패 시간: %time%
    pause
    exit /b 1
)

echo.
echo ===================================================
echo 📊 3단계: 모니터링 서비스들 빌드
echo ===================================================
echo 예상 시간: 30분
echo.

call build_monitoring.bat
if %errorlevel% neq 0 (
    echo ❌ 모니터링 서비스들 빌드 실패
    echo 실패 시간: %time%
    pause
    exit /b 1
)

echo.
echo ===================================================
echo 🎉 하루종일 빌드 완료!
echo ===================================================
echo 완료 시간: %time%
echo.
echo 📋 전체 빌드된 이미지 목록:
docker images | findstr callytics
echo.
echo 🚀 내일 아침 음성 파일 테스트 준비 완료!
echo.
echo 다음 명령어로 서비스 시작:
echo docker-compose up -d
echo.
echo 🎵 음성 파일 테스트 준비 완료!
pause 