#!/usr/bin/env python3
"""
검증 스크립트 디버깅용
"""

import re

# audio-processor Dockerfile 내용
content = """# audio-processor 서비스 Dockerfile
# 표준화된 Dockerfile.template 기반

FROM nvidia/cuda:11.8-runtime-ubuntu20.04

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \\
    python3.11 \\
    python3.11-pip \\
    python3.11-dev \\
    ffmpeg \\
    libsndfile1 \\
    libportaudio2 \\
    portaudio19-dev \\
    locales \\
    tzdata \\
    && rm -rf /var/lib/apt/lists/*

# 로케일 및 시간대 설정
ENV TZ=Asia/Seoul
ENV LANG=ko_KR.UTF-8
ENV LC_ALL=ko_KR.UTF-8
ENV PYTHONIOENCODING=utf-8
RUN echo "ko_KR.UTF-8 UTF-8" > /etc/locale.gen && \\
    locale-gen ko_KR.UTF-8 && \\
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \\
    echo $TZ > /etc/timezone

# 작업 디렉토리 설정
WORKDIR /app

# Python 환경 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0

# 공통 requirements 설치
COPY requirements_common.txt .
RUN pip install --no-cache-dir -r requirements_common.txt

# 서비스별 requirements 설치
COPY requirements.audio-processor.txt .
RUN pip install --no-cache-dir -r requirements.audio-processor.txt

# 애플리케이션 코드 복사
COPY src/ ./src/
COPY config/ ./config/

# 포트 노출
EXPOSE 8001

# 헬스체크
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8001/health || exit 1

# 실행 명령
CMD ["python", "-m", "src.audio.main"]
"""

print("🔍 디버깅 시작...")

# CUDA 버전 확인
cuda_match = re.search(r'nvidia/cuda:(\d+\.\d+)', content)
cuda_version = cuda_match.group(1) if cuda_match else None
print(f"CUDA 버전: {cuda_version}")

# Python 버전 확인
python_match = re.search(r'python3\.(\d+)', content)
python_version = python_match.group(1) if python_match else None
print(f"Python 버전: {python_version}")

# 공통 requirements 확인
has_common_requirements = 'requirements_common.txt' in content
print(f"공통 requirements 포함: {has_common_requirements}")

# 헬스체크 확인
has_healthcheck = 'HEALTHCHECK' in content
print(f"헬스체크 포함: {has_healthcheck}")

# 검증 결과
is_valid = (cuda_version == '11.8' and 
           python_version == '11' and 
           has_common_requirements and 
           has_healthcheck)
print(f"검증 결과: {is_valid}")

print(f"상세:")
print(f"  - CUDA 11.8: {cuda_version == '11.8'}")
print(f"  - Python 11: {python_version == '11'}")
print(f"  - 공통 requirements: {has_common_requirements}")
print(f"  - 헬스체크: {has_healthcheck}") 