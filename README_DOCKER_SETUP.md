# Callytics Docker 설치 및 실행 가이드

## 🐳 Docker 설치 (Windows)

### 1. **Docker Desktop 설치**

#### **방법 1: 공식 사이트에서 다운로드**
1. [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) 방문
2. "Download for Windows" 클릭
3. `Docker Desktop Installer.exe` 다운로드 및 실행
4. 설치 완료 후 재부팅

#### **방법 2: Winget 사용 (Windows 10/11)**
```powershell
# PowerShell을 관리자 권한으로 실행
winget install Docker.DockerDesktop
```

#### **방법 3: Chocolatey 사용**
```powershell
# Chocolatey가 설치되어 있다면
choco install docker-desktop
```

### 2. **Docker Desktop 설정**

1. **Docker Desktop 실행**
2. **Settings → General**
   - "Use the WSL 2 based engine" 체크
   - "Start Docker Desktop when you log in" 체크

3. **Settings → Resources → WSL Integration**
   - "Enable integration with my default WSL distro" 체크
   - 사용할 WSL 배포판 활성화

4. **Settings → Resources → Advanced**
   - Memory: 최소 8GB (권장: 12GB+)
   - CPUs: 4개 이상
   - Disk image size: 최소 64GB

### 3. **WSL 2 설치 및 설정** (필요시)

```powershell
# PowerShell을 관리자 권한으로 실행

# WSL 기능 활성화
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# Virtual Machine Platform 활성화
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# 재부팅 후 WSL 2 커널 업데이트
# https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi 다운로드 및 설치

# WSL 2를 기본값으로 설정
wsl --set-default-version 2

# Ubuntu 설치 (선택사항)
wsl --install -d Ubuntu
```

## 🚀 Callytics Docker 빌드 및 실행

### 1. **환경 변수 설정**

```bash
# .env 파일 생성
echo OPENAI_API_KEY=your_openai_api_key_here > .env
echo HUGGINGFACE_TOKEN=your_huggingface_token_here >> .env
```

### 2. **Docker 빌드**

```bash
# 기본 빌드
docker build -t callytics:latest .

# 캐시 없이 빌드 (문제 발생 시)
docker build --no-cache -t callytics:latest .

# 빌드 진행상황 자세히 보기
docker build --progress=plain -t callytics:latest .
```

### 3. **Docker 실행**

#### **GPU 사용 (NVIDIA GPU 필요)**
```bash
# NVIDIA Container Toolkit 설치 필요
docker run --gpus all \
  --env-file .env \
  -p 8000:8000 \
  -v "%cd%/audio:/app/audio" \
  -v "%cd%/logs:/app/logs" \
  -v "%cd%/data:/app/data" \
  callytics:latest
```

#### **CPU 전용 실행**
```bash
docker run \
  --env-file .env \
  -p 8000:8000 \
  -v "%cd%/audio:/app/audio" \
  -v "%cd%/logs:/app/logs" \
  -v "%cd%/data:/app/data" \
  callytics:latest
```

### 4. **Docker Compose 사용 (권장)**

```bash
# 모든 서비스 실행 (Callytics + 모니터링)
docker-compose up -d

# 특정 서비스만 실행
docker-compose up -d callytics

# 로그 확인
docker-compose logs -f callytics

# 서비스 중지
docker-compose down
```

## 🔧 문제 해결

### **Docker Desktop이 시작되지 않는 경우**

1. **Windows 기능 확인**
   ```powershell
   # PowerShell에서 확인
   Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
   Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform
   ```

2. **Hyper-V 활성화**
   ```powershell
   # PowerShell 관리자 권한으로 실행
   Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
   ```

3. **BIOS 설정 확인**
   - Virtualization Technology (VT-x/AMD-V) 활성화
   - Hyper-V 지원 활성화

### **빌드 오류 해결**

1. **네트워크 문제**
   ```bash
   # DNS 설정 확인
   docker run --rm alpine nslookup docker.io
   
   # 프록시 설정 (필요시)
   docker build --build-arg http_proxy=http://proxy:port --build-arg https_proxy=https://proxy:port -t callytics:latest .
   ```

2. **메모리 부족**
   - Docker Desktop Settings에서 메모리 할당량 증가
   - 불필요한 Docker 이미지 정리: `docker system prune -a`

3. **권한 문제**
   ```bash
   # Docker Desktop을 관리자 권한으로 실행
   # 또는 사용자를 docker-users 그룹에 추가
   ```

### **실행 오류 해결**

1. **GPU 인식 안됨**
   ```bash
   # NVIDIA Container Toolkit 설치 확인
   docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi
   ```

2. **포트 충돌**
   ```bash
   # 다른 포트 사용
   docker run -p 8001:8000 callytics:latest
   ```

3. **볼륨 마운트 오류**
   ```bash
   # 절대 경로 사용
   docker run -v "C:/silent/Callytics/audio:/app/audio" callytics:latest
   ```

## 📊 성능 최적화

### **GPU 메모리 최적화**
```bash
# 환경 변수 추가
docker run \
  -e PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:2048 \
  -e CUDA_LAUNCH_BLOCKING=1 \
  --gpus all callytics:latest
```

### **CPU 최적화**
```bash
# CPU 코어 수 제한
docker run --cpus="4.0" callytics:latest

# 메모리 제한
docker run --memory="8g" callytics:latest
```

## 🔍 상태 확인

```bash
# 실행 중인 컨테이너 확인
docker ps

# 컨테이너 로그 확인
docker logs callytics

# 컨테이너 내부 접속
docker exec -it callytics bash

# 리소스 사용량 확인
docker stats callytics
```

## 📝 추가 참고사항

- **최소 시스템 요구사항**: Windows 10 Pro/Enterprise/Education (Build 19041+) 또는 Windows 11
- **권장 사양**: 16GB RAM, NVIDIA GTX 1660 이상, 50GB 여유 공간
- **네트워크**: 초기 빌드 시 약 5-10GB 다운로드 필요 