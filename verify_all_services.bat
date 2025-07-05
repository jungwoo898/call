@echo off
echo 🔍 모든 서비스 빌드 검증
echo ========================
echo 시작 시간: %time%
echo.

echo 📋 빌드된 이미지 확인:
echo.
docker images | findstr callytics
echo.

echo 🐍 Python 3.11 서비스 검증:
set /a py311_count=0
docker images | findstr "callytics-database" >nul && set /a py311_count+=1 && echo ✅ 데이터베이스 서비스
docker images | findstr "callytics-sentiment" >nul && set /a py311_count+=1 && echo ✅ 감정 분석 서비스
docker images | findstr "callytics-punctuation" >nul && set /a py311_count+=1 && echo ✅ 문장부호 복원 서비스
docker images | findstr "callytics-llm-analyzer" >nul && set /a py311_count+=1 && echo ✅ LLM 분석 서비스
docker images | findstr "callytics-gateway" >nul && set /a py311_count+=1 && echo ✅ 게이트웨이 서비스

echo.
echo 🎵 Python 3.8 서비스 검증:
set /a py38_count=0
docker images | findstr "callytics-audio-processor" >nul && set /a py38_count+=1 && echo ✅ 오디오 프로세서
docker images | findstr "callytics-speaker-diarizer" >nul && set /a py38_count+=1 && echo ✅ 화자 분리 서비스
docker images | findstr "callytics-speech-recognizer" >nul && set /a py38_count+=1 && echo ✅ 음성 인식 서비스

echo.
echo 📊 모니터링 서비스 검증:
set /a monitoring_count=0
docker images | findstr "callytics-monitoring" >nul && set /a monitoring_count+=1 && echo ✅ 모니터링 서비스
docker images | findstr "prometheus" >nul && set /a monitoring_count+=1 && echo ✅ Prometheus
docker images | findstr "grafana" >nul && set /a monitoring_count+=1 && echo ✅ Grafana

echo.
echo ===================================================
echo 📊 검증 결과 요약
echo ===================================================
echo Python 3.11 서비스: %py311_count%/5
echo Python 3.8 서비스: %py38_count%/3
echo 모니터링 서비스: %monitoring_count%/3
echo.

if %py311_count%==5 (
    echo ✅ Python 3.11 서비스들 모두 빌드 완료
) else (
    echo ❌ Python 3.11 서비스 %py311_count%/5 빌드됨
)

if %py38_count%==3 (
    echo ✅ Python 3.8 서비스들 모두 빌드 완료
) else (
    echo ❌ Python 3.8 서비스 %py38_count%/3 빌드됨
)

if %monitoring_count%==3 (
    echo ✅ 모니터링 서비스들 모두 빌드 완료
) else (
    echo ❌ 모니터링 서비스 %monitoring_count%/3 빌드됨
)

echo.
if %py311_count%==5 if %py38_count%==3 if %monitoring_count%==3 (
    echo 🎉 모든 서비스 빌드 완료!
    echo 🚀 음성 파일 테스트 준비 완료!
    echo.
    echo 다음 명령어로 서비스 시작:
    echo docker-compose up -d
) else (
    echo ⚠️ 일부 서비스 빌드 실패
    echo 누락된 서비스 확인 후 재빌드 필요
)

echo.
echo 완료 시간: %time%
pause 