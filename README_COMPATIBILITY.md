# Callytics Docker 호환성 가이드

## 🎯 호환성 문제 해결 완료

이 문서는 Callytics Docker 환경의 주요 호환성 문제들을 해결한 내용을 설명합니다.

## 🔧 해결된 주요 문제들

### 1. Python 런타임 선택 (✅ 해결됨)

**문제**: Python 3.9 사용으로 Gradio 4.19.2 호환성 문제
**해결**: Python 3.10 LTS로 업그레이드

```dockerfile
# 변경 전
RUN apt-get install python3.9 python3.9-dev

# 변경 후  
RUN add-apt-repository ppa:deadsnakes/ppa \
    && apt-get install python3.10 python3.10-dev
```

**근거**:
- Gradio 4.19.2는 Python 3.10 이상 필수
- Python 3.10 LTS는 장기 지원 및 안정성 보장
- AI/ML 라이브러리들의 최적 호환성

### 2. 중복 패키지 정의 (✅ 해결됨)

**문제**: `python-dotenv` 1.0.1과 1.0.0 중복 정의
**해결**: 최신 버전(1.0.1)으로 통일

```txt
# 변경 전
python-dotenv==1.0.1
# ... 다른 패키지들 ...
python-dotenv==1.0.0  # 중복!

# 변경 후
python-dotenv==1.0.1  # 단일 정의
```

### 3. FastAPI ↔ Gradio ↔ Pydantic 삼각 충돌 (✅ 해결됨)

**문제**: FastAPI 0.104.1 + Pydantic 2.x 호환성 충돌
**해결**: FastAPI 최신화 및 Pydantic 버전 명시

```txt
# 변경 전
fastapi==0.104.1  # Pydantic 2.x와 충돌

# 변경 후
pydantic==2.7.4
fastapi>=0.115.0,<0.116.0  # Pydantic V2 패치 포함
```

**기술적 근거**:
- FastAPI 0.115+는 내부적으로 Pydantic V2 API 패치 포함
- Gradio 4.19.2는 pydantic>=2.0 요구
- 안정적인 호환성을 위해 pydantic==2.7.4로 고정

### 4. NumPy 범위 문제 (✅ 해결됨)

**문제**: NVIDIA NeMo 1.17.0이 numpy>=1.24에서 깨짐
**해결**: numpy==1.23.5로 고정

```txt
# 변경 전
numpy>=1.21.0,<2.0.0  # 너무 넓은 범위

# 변경 후
numpy==1.23.5  # NeMo 호환 보장
```

**호환성 매트릭스**:
- ✅ pandas 2.0.3 호환
- ✅ scikit-learn 1.3.0 호환  
- ✅ NVIDIA NeMo 1.17.0 호환

### 5. CUDA 이미지 ↔ PyTorch Wheel 일치 (✅ 해결됨)

**문제**: CUDA 11.8 이미지 + CUDA 12.1 PyTorch wheel 불일치
**해결**: 전체 스택을 CUDA 12.1으로 통일

```dockerfile
# 일관된 CUDA 12.1 스택
FROM nvidia/cuda:12.1-devel-ubuntu20.04
RUN pip install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 \
    --index-url https://download.pytorch.org/whl/cu121
```

### 6. 추가 최적화 사항들 (✅ 해결됨)

#### Transformers 업그레이드
```txt
transformers==4.40.2  # 4.28.0 → 4.40.2 (최신 모델 지원)
```

#### Datasets 최신화
```txt
datasets==2.19.2  # Arrow 포맷 개선, Pydantic V2 지원
```

#### Watchdog 최적화
```txt
watchdog[watchmedo]==6.0.0  # Windows 호환성 개선
```

#### GCC 버전 호환성
```dockerfile
# NeMo & Demucs 빌드를 위한 GCC 9 설정
RUN apt-get install gcc-9 g++-9 \
    && update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-9 90
```

## 🚀 설치 및 검증

### 자동 설정 (권장)

```bash
# 실행 권한 부여
chmod +x setup_docker.sh

# 자동 설정 실행
./setup_docker.sh
```

### 수동 검증

```bash
# 호환성 검증
docker-compose --profile check run --rm compatibility-check

# 서비스 시작
docker-compose up -d

# 상태 확인
docker-compose ps
curl http://localhost:8000/health
```

## 📊 성능 최적화

### GPU 메모리 관리
```yaml
environment:
  - PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:2048,expandable_segments:True
  - PYTORCH_CUDA_MEMORY_FRACTION=0.8
  - CUDA_MEMORY_FRACTION=0.8
```

### Python 최적화
```yaml
environment:
  - PYTHONOPTIMIZE=2
  - PYTHONDONTWRITEBYTECODE=1  
  - PYTHON_CACHE_SIZE=4096
```

### 토크나이저 최적화
```yaml
environment:
  - TOKENIZERS_PARALLELISM=false  # 멀티프로세싱 충돌 방지
  - TRANSFORMERS_CACHE=/app/.cache/transformers
```

## 🔍 트러블슈팅

### 일반적인 문제들

#### 1. GPU 메모리 부족
```bash
# 메모리 사용량 확인
nvidia-smi

# 개발 모드 (메모리 사용량 감소)
docker-compose --profile dev up -d
```

#### 2. 패키지 설치 실패
```bash
# 캐시 없이 재빌드
docker-compose build --no-cache callytics
```

#### 3. 헬스체크 실패
```bash
# 로그 확인
docker-compose logs -f callytics

# 컨테이너 내부 확인
docker-compose exec callytics bash
```

### 호환성 문제 진단

```bash
# 전체 진단 실행
python compatibility_check.py

# 특정 패키지 확인
pip show fastapi pydantic gradio numpy torch
```

## 📈 모니터링

### 시스템 모니터링
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090  
- **Node Exporter**: http://localhost:9100
- **cAdvisor**: http://localhost:8080

### GPU 모니터링
```bash
# 실시간 GPU 사용률
docker-compose exec callytics gpustat -i 1

# NVIDIA 모니터링
docker-compose exec callytics nvidia-ml-py3
```

## 🔄 업데이트 가이드

### 의존성 업데이트 시 주의사항

1. **NumPy 업데이트**: NeMo 호환성 확인 필수
2. **PyTorch 업데이트**: CUDA 버전과 일치 확인
3. **FastAPI 업데이트**: Pydantic 호환성 검증
4. **Transformers 업데이트**: 모델 호환성 테스트

### 안전한 업데이트 절차

```bash
# 1. 백업
docker-compose down
docker image save callytics:latest -o backup.tar

# 2. 업데이트
docker-compose build --no-cache

# 3. 검증
docker-compose --profile check run --rm compatibility-check

# 4. 배포
docker-compose up -d
```

## 📚 참고 자료

- [Gradio Python 요구사항](https://pypi.org/project/gradio/)
- [FastAPI + Pydantic 호환성](https://github.com/tiangolo/fastapi/releases)
- [NVIDIA NeMo 호환성](https://github.com/NVIDIA/NeMo)
- [PyTorch CUDA 호환성](https://pytorch.org/get-started/locally/)

## 🆘 지원

문제가 발생하면:

1. `compatibility_check.py` 실행
2. `docker-compose logs callytics` 확인
3. 해당 로그와 함께 이슈 리포트

---

**✅ 모든 주요 호환성 문제가 해결되었습니다!** 