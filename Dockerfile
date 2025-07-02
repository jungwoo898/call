# 멀티스테이지 빌드로 이미지 크기 최적화
FROM ubuntu:20.04 AS builder

# 환경 변수 설정 (최우선)
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:/usr/local/lib

# NLTK 데이터 경로 설정
ENV NLTK_DATA=/usr/local/nltk_data
RUN mkdir -p /usr/local/nltk_data

# CUDA 키링 및 저장소 추가
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && wget -qO - https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/3bf863cc.pub | apt-key add - \
    && echo "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64 /" > /etc/apt/sources.list.d/cuda.list \
    && rm -rf /var/lib/apt/lists/*

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3.10-distutils \
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
    cuda-runtime-11-8 \
    libfreetype6-dev \
    libpng-dev \
    libjpeg-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# GCC 버전 설정 (NeMo 및 Demucs 호환성)
RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-9 90 \
    && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-9 90

# Python 심볼릭 링크 설정
RUN ln -sf /usr/bin/python3.10 /usr/bin/python

# pip 설치 및 업그레이드 (메모리 효율적)
RUN curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py && \
    python /tmp/get-pip.py "pip==23.3.1" && \
    python -m pip install --no-cache-dir --upgrade setuptools wheel && \
    rm /tmp/get-pip.py

# PyTorch 설치 (2023-2024 안정 버전으로 통일)
RUN pip install --no-cache-dir torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cu118

# mamba-ssm 사전 빌드된 wheel 설치 (nvcc 없이 설치 가능)
RUN pip install --prefer-binary --no-cache-dir \
    https://github.com/state-spaces/mamba/releases/download/v2.2.2/mamba_ssm-2.2.2+cu118torch2.1cxx11abiFALSE-cp310-cp310-linux_x86_64.whl

# 나머지 의존성 설치
COPY requirements.txt /tmp/requirements.txt
RUN pip install --prefer-binary --no-cache-dir -r /tmp/requirements.txt

# 의존성 충돌 검사 (testresources 누락 문제 해결)
RUN pip install --no-cache-dir pip-tools testresources && pip check

# 핵심 패키지 import 검증 (빌드 시 조기 오류 감지)
RUN python -c "import torch; print(f'PyTorch: {torch.__version__}')" && \
    python -c "import torchaudio; print(f'TorchAudio: {torchaudio.__version__}')" && \
    python -c "import mamba_ssm; print('Mamba-SSM import successful')" && \
    python -c "import demucs; print('Demucs import successful')" && \
    python -c "import speechbrain; print('SpeechBrain import successful')" && \
    python -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')" && \
    python -c "import pydantic; print(f'Pydantic: {pydantic.__version__}')" && \
    python -c "import nemo; print('NeMo import successful')" && \
    python -c "import pyannote.audio; print('PyAnnote.audio import successful')" && \
    python -c "import accelerate; print('Accelerate import successful')" && \
    python -c "import transformers; print(f'Transformers: {transformers.__version__}')" && \
    python -c "import faster_whisper; print('Faster-Whisper import successful')"

# NLTK 데이터 다운로드 (빌드 시간 단축을 위해 최소한만)
RUN python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True)"

# 런타임 스테이지  
FROM ubuntu:20.04

# 환경 변수 설정
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:/usr/local/lib

# NLTK 데이터 경로 설정 (런타임에서도 필요)
ENV NLTK_DATA=/usr/local/nltk_data

# CUDA 키링 및 저장소 추가 (런타임)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && wget -qO - https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/3bf863cc.pub | apt-key add - \
    && echo "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64 /" > /etc/apt/sources.list.d/cuda.list \
    && rm -rf /var/lib/apt/lists/*

# 런타임 패키지 설치 (최소한만)
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.10 \
    ffmpeg \
    libsndfile1 \
    sox \
    libsox-fmt-all \
    curl \
    libportaudio2 \
    cuda-runtime-11-8 \
    libfreetype6 \
    libpng16-16 \
    libjpeg8 \
    && apt-get purge -y software-properties-common \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Python 심볼릭 링크 설정
RUN ln -sf /usr/bin/python3.10 /usr/bin/python

# Builder 스테이지에서 Python 패키지, 실행 파일 및 NLTK 데이터 복사
COPY --from=builder /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /usr/local/nltk_data /usr/local/nltk_data

# 공유 라이브러리 경로 업데이트
RUN ldconfig

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

# 기본 명령어
CMD ["python", "main.py"]
