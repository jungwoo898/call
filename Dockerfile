# 멀티스테이지 빌드로 이미지 크기 최적화
FROM nvidia/cuda:12.1-devel-ubuntu20.04 AS builder

# 환경 변수 설정
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3.10-distutils \
    python3-pip \
    build-essential \
    gcc-9 \
    g++-9 \
    cmake \
    git \
    wget \
    curl \
    ffmpeg \
    libsndfile1 \
    sox \
    libsox-fmt-all \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# GCC 버전 설정 (NeMo 및 Demucs 호환성)
RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-9 90 \
    && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-9 90

# Python 심볼릭 링크 설정
RUN ln -sf /usr/bin/python3.10 /usr/bin/python

# pip 업그레이드
RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel

# PyTorch 설치 (CUDA 12.1과 호환되는 버전)
RUN pip install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cu121

# 나머지 의존성 설치
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# NLTK 데이터 다운로드
RUN python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True)"

# 런타임 스테이지
FROM nvidia/cuda:12.1-runtime-ubuntu20.04

# 환경 변수 설정
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

# 런타임 패키지 설치
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    libsndfile1 \
    sox \
    libsox-fmt-all \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 심볼릭 링크 설정
RUN ln -sf /usr/bin/python3.10 /usr/bin/python

# Builder 스테이지에서 Python 패키지 복사
COPY --from=builder /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 작업 디렉토리 설정
WORKDIR /app

# 애플리케이션 파일 복사
COPY . .

# GPU 및 CPU 모드 자동 감지를 위한 환경 변수
ENV DEVICE=auto
ENV COMPUTE_TYPE=auto

# 포트 노출
EXPOSE 8000

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# API 키 검증 스크립트
RUN echo '#!/bin/bash\n\
if [ -z "$OPENAI_API_KEY" ] && [ -z "$AZURE_OPENAI_API_KEY" ] && [ -z "$HUGGINGFACE_TOKEN" ]; then\n\
    echo "Warning: No API keys found. Some features may be limited."\n\
fi\n\
exec "$@"' > /entrypoint.sh && chmod +x /entrypoint.sh

# 엔트리포인트 설정
ENTRYPOINT ["/entrypoint.sh"]

# 기본 명령어
CMD ["python", "main.py"]
