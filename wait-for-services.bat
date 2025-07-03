@echo off
REM wait-for-services.bat - Callytics 마이크로서비스 시작 대기 스크립트 (Windows)

setlocal enabledelayedexpansion

echo [INFO] 🚀 Callytics 마이크로서비스 시작 대기 시작

REM 서비스 목록 (시작 순서대로)
set services=database-service:8007 audio-processor:8001 punctuation-restorer:8004 sentiment-analyzer:8005 speaker-diarizer:8002 speech-recognizer:8003 llm-analyzer:8006 api-gateway:8000

echo [INFO] 📋 1단계: 기본 서비스 시작 대기

REM 기본 서비스들
for %%s in (database-service:8007 audio-processor:8001 punctuation-restorer:8004 sentiment-analyzer:8005) do (
    call :check_health %%s 20 3
    if !errorlevel! neq 0 (
        echo [ERROR] ❌ 서비스 시작 실패: %%s
        exit /b 1
    )
)

echo [INFO] 🎮 2단계: GPU 서비스 시작 대기 (더 긴 대기 시간)

REM GPU 서비스들
for %%s in (speaker-diarizer:8002 speech-recognizer:8003) do (
    call :check_gpu_service %%s
    if !errorlevel! neq 0 (
        echo [ERROR] ❌ GPU 서비스 시작 실패: %%s
        exit /b 1
    )
)

echo [INFO] 🤖 3단계: LLM 서비스 시작 대기

call :check_health llm-analyzer:8006 15 3
if !errorlevel! neq 0 (
    echo [ERROR] ❌ LLM 서비스 시작 실패
    exit /b 1
)

echo [INFO] 🌐 4단계: API Gateway 시작 대기

call :check_health api-gateway:8000 10 2
if !errorlevel! neq 0 (
    echo [ERROR] ❌ API Gateway 시작 실패
    exit /b 1
)

echo [INFO] 🔍 최종 시스템 상태 확인

curl -f -s "http://localhost:8000/health" >nul 2>&1
if !errorlevel! equ 0 (
    echo [SUCCESS] 🎉 모든 서비스가 성공적으로 시작되었습니다!
    echo [INFO] 📊 시스템 상태:
    echo [INFO]    • API Gateway: http://localhost:8000
    echo [INFO]    • 헬스체크: http://localhost:8000/health
    echo [INFO]    • API 문서: http://localhost:8000/docs
    exit /b 0
) else (
    echo [ERROR] ❌ 최종 시스템 확인 실패
    exit /b 1
)

:check_health
setlocal
set service_info=%1
for /f "tokens=1,2 delims=:" %%a in ("%service_info%") do (
    set service_name=%%a
    set port=%%b
)
set max_attempts=%2
set wait_seconds=%3

echo [INFO] 🔍 !service_name! 서비스 헬스체크 시작 (포트: !port!)

for /l %%i in (1,1,!max_attempts!) do (
    curl -f -s "http://localhost:!port!/health" >nul 2>&1
    if !errorlevel! equ 0 (
        echo [SUCCESS] ✅ !service_name! 서비스 준비 완료 (%%i/!max_attempts!)
        exit /b 0
    ) else (
        if %%i equ !max_attempts! (
            echo [ERROR] ❌ !service_name! 서비스 시작 실패 (타임아웃)
            exit /b 1
        ) else (
            echo [WARNING] ⏳ !service_name! 서비스 대기 중... (%%i/!max_attempts!)
            timeout /t !wait_seconds! /nobreak >nul
        )
    )
)
exit /b 1

:check_gpu_service
setlocal
set service_info=%1
for /f "tokens=1,2 delims=:" %%a in ("%service_info%") do (
    set service_name=%%a
    set port=%%b
)

echo [INFO] 🎯 GPU 서비스 !service_name! 확장 대기 (최대 5분)
call :check_health !service_name!:!port! 60 5
exit /b !errorlevel! 