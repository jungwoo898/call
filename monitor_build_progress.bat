@echo off
chcp 65001>nul
echo 📊 빌드 진행 상황 모니터링
echo ===========================
echo 시작 시간: %time%
echo.

:loop
cls
echo 📊 빌드 진행 상황 모니터링
echo ===========================
echo 현재 시간: %time%
echo.

echo 🐍 Python 3.11 서비스들:
docker images | findstr "callytics-database" >nul && echo ✅ 데이터베이스 서비스 || echo ❌ 데이터베이스 서비스
docker images | findstr "callytics-sentiment" >nul && echo ✅ 감정 분석 서비스 || echo ❌ 감정 분석 서비스
docker images | findstr "callytics-punctuation" >nul && echo ✅ 문장부호 복원 서비스 || echo ❌ 문장부호 복원 서비스
docker images | findstr "callytics-llm-analyzer" >nul && echo ✅ LLM 분석 서비스 || echo ❌ LLM 분석 서비스
docker images | findstr "callytics-gateway" >nul && echo ✅ 게이트웨이 서비스 || echo ❌ 게이트웨이 서비스

echo.
echo 🎵 Python 3.8 서비스들:
docker images | findstr "callytics-audio-processor" >nul && echo ✅ 오디오 프로세서 || echo ❌ 오디오 프로세서
docker images | findstr "callytics-speaker-diarizer" >nul && echo ✅ 화자 분리 서비스 || echo ❌ 화자 분리 서비스
docker images | findstr "callytics-speech-recognizer" >nul && echo ✅ 음성 인식 서비스 || echo ❌ 음성 인식 서비스

echo.
echo 📊 모니터링 서비스들:
docker images | findstr "callytics-monitoring" >nul && echo ✅ 모니터링 서비스 || echo ❌ 모니터링 서비스
docker images | findstr "prometheus" >nul && echo ✅ Prometheus || echo ❌ Prometheus
docker images | findstr "grafana" >nul && echo ✅ Grafana || echo ❌ Grafana

echo.
echo 📋 전체 이미지 목록:
docker images | findstr callytics

echo.
echo 🔄 30초 후 다시 확인...
timeout /t 30 /nobreak >nul
goto loop 