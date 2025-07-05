@echo off
chcp 65001>nul
echo 🚀 Python 3.8 서비스들 빌드 시작
echo =================================
echo 시작 시간: %date% %time%
echo.

echo 🔍 1단계: Python 3.8 오디오 서비스 호환성 검증
echo 시작: %time%
python verify_py38_audio_only.py
if %errorlevel% neq 0 (
    echo ❌ Python 3.8 오디오 서비스 호환성 검증 실패
    echo 실패 시간: %time%
    pause
    exit /b 1
)
echo ✅ Python 3.8 오디오 서비스 호환성 검증 완료: %time%

echo.
echo 🎵 2단계: 오디오 프로세서 빌드 (Python 3.8)
echo 시작: %time%
docker build -f Dockerfile.audio-processor -t callytics-audio-processor:latest .
if %errorlevel% neq 0 (
    echo ❌ 오디오 프로세서 빌드 실패
    echo 실패 시간: %time%
    pause
    exit /b 1
)
echo ✅ 오디오 프로세서 빌드 완료: %time%

echo.
echo 🎤 3단계: 화자 분리 서비스 빌드 (Python 3.8)
echo 시작: %time%
docker build -f Dockerfile.speaker-diarizer -t callytics-speaker-diarizer:latest .
if %errorlevel% neq 0 (
    echo ❌ 화자 분리 서비스 빌드 실패
    echo 실패 시간: %time%
    pause
    exit /b 1
)
echo ✅ 화자 분리 서비스 빌드 완료: %time%

echo.
echo 🗣️ 4단계: 음성 인식 서비스 빌드 (Python 3.8)
echo 시작: %time%
docker build -f Dockerfile.speech-recognizer -t callytics-speech-recognizer:latest .
if %errorlevel% neq 0 (
    echo ❌ 음성 인식 서비스 빌드 실패
    echo 실패 시간: %time%
    pause
    exit /b 1
)
echo ✅ 음성 인식 서비스 빌드 완료: %time%

echo.
echo ✅ Python 3.8 서비스들 빌드 완료!
echo 완료 시간: %time%
echo.
echo 📋 빌드된 Python 3.8 이미지 목록:
docker images | findstr callytics
echo.
echo 🎉 모든 서비스 빌드 완료!
echo 🚀 음성 파일 테스트 준비 완료!
echo.
echo docker-compose up -d
pause 