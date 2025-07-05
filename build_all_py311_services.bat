@echo off
chcp 65001>nul
echo 🚀 Python 3.11 서비스들 하루종일 빌드 시작
echo ============================================
echo 시작 시간: %date% %time%
echo.

REM 기존 이미지 제거 (기본 비활성화). 필요 시 "set REMOVE_OLD_IMAGES=yes" 로 설정.
if /i "%REMOVE_OLD_IMAGES%"=="yes" (
    echo 🧹 기존 Python 3.11 이미지 정리 중...
    for /f "tokens=3" %%i in ('docker images ^| findstr callytics') do (
        echo 기존 이미지 제거: %%i
        docker rmi %%i 2>nul
    )
)

echo.
echo 📊 1단계: 데이터베이스 서비스 빌드 (Python 3.11)
echo 시작: %time%
docker build -f Dockerfile.database-service -t callytics-database:latest .
if %errorlevel% neq 0 (
    echo ❌ 데이터베이스 서비스 빌드 실패
    echo 실패 시간: %time%
    pause
    exit /b 1
)
echo ✅ 데이터베이스 서비스 빌드 완료: %time%

echo.
echo 😊 2단계: 감정 분석 서비스 빌드 (Python 3.11)
echo 시작: %time%
docker build -f Dockerfile.sentiment-analyzer -t callytics-sentiment:latest .
if %errorlevel% neq 0 (
    echo ❌ 감정 분석 서비스 빌드 실패
    echo 실패 시간: %time%
    pause
    exit /b 1
)
echo ✅ 감정 분석 서비스 빌드 완료: %time%

echo.
echo 📝 3단계: 문장부호 복원 서비스 빌드 (Python 3.11)
echo 시작: %time%
docker build -f Dockerfile.punctuation-restorer -t callytics-punctuation:latest .
if %errorlevel% neq 0 (
    echo ❌ 문장부호 복원 서비스 빌드 실패
    echo 실패 시간: %time%
    pause
    exit /b 1
)
echo ✅ 문장부호 복원 서비스 빌드 완료: %time%

echo.
echo 🤖 4단계: LLM 분석 서비스 빌드 (Python 3.11)
echo 시작: %time%
docker build -f Dockerfile.llm-analyzer -t callytics-llm-analyzer:latest .
if %errorlevel% neq 0 (
    echo ❌ LLM 분석 서비스 빌드 실패
    echo 실패 시간: %time%
    pause
    exit /b 1
)
echo ✅ LLM 분석 서비스 빌드 완료: %time%

echo.
echo 🌐 5단계: 게이트웨이 서비스 빌드 (Python 3.11)
echo 시작: %time%
docker build -f Dockerfile.gateway -t callytics-gateway:latest .
if %errorlevel% neq 0 (
    echo ❌ 게이트웨이 서비스 빌드 실패
    echo 실패 시간: %time%
    pause
    exit /b 1
)
echo ✅ 게이트웨이 서비스 빌드 완료: %time%

echo.
echo ✅ Python 3.11 서비스들 빌드 완료!
echo 완료 시간: %time%
echo.
echo 📋 빌드된 Python 3.11 이미지 목록:
docker images | findstr callytics
echo.
echo 🚀 내일 아침 음성 파일 테스트 준비 완료!
echo.
echo 다음 단계: Python 3.8 서비스들 빌드
echo build_all_py38_services.bat
pause 