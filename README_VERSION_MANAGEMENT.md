# Callytics 버전 관리 가이드

## 1. 표준 버전 설정

### 런타임 환경
- **Python**: 3.11 (모든 서비스 통일)
- **CUDA**: 11.8.2 (실제 존재하는 버전으로 통일)
- **cuDNN**: 8
- **Ubuntu**: 20.04
- **Base Image**: `nvidia/cuda:11.8.2-cudnn8-runtime-ubuntu20.04`

### 주요 라이브러리 버전
- **FastAPI**: 0.104.1
- **PyTorch**: 2.1.2
- **Transformers**: 4.35.2
- **Tokenizers**: 0.14.1
- **NumPy**: 1.24.4

## 2. Requirements 파일 구조

### 공통 라이브러리
```
requirements_common.txt  # 모든 서비스에서 공통 사용
```

### 서비스별 라이브러리
```
requirements.audio-processor.txt      # 오디오 처리 전용
requirements.database-service.txt     # 데이터베이스 전용
requirements.gateway.txt             # 게이트웨이 전용
requirements.llm-analyzer.txt        # LLM 분석 전용
requirements.punctuation-restorer.txt # 문장 부호 복원 전용
requirements.sentiment-analyzer.txt   # 감정 분석 전용
requirements.speaker-diarizer.txt     # 화자 분리 전용
requirements.speech-recognizer.txt    # 음성 인식 전용
```

### 서비스별 requirements.txt 구조
```txt
# 서비스 전용 라이브러리
# 공통 라이브러리는 requirements_common.txt에서 관리

# 공통 라이브러리 포함
-r requirements_common.txt

# 서비스 전용 라이브러리
service-specific-package==1.0.0
```

## 3. Dockerfile 표준화

### 표준 Dockerfile 구조
```dockerfile
# 표준화된 Dockerfile 템플릿
FROM nvidia/cuda:11.8.2-cudnn8-runtime-ubuntu20.04

# 시스템 패키지 업데이트
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-pip \
    python3.11-dev \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 환경 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 공통 requirements 설치
COPY requirements_common.txt .
RUN pip install --no-cache-dir -r requirements_common.txt

# 서비스별 requirements 설치
COPY requirements.<service>.txt .
RUN pip install --no-cache-dir -r requirements.<service>.txt

# 애플리케이션 코드 복사
COPY src/ ./src/

# 포트 노출
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 실행 명령
CMD ["python", "-m", "src.<service>.main"]
```

## 4. 버전 관리 자동화

### 자동화 스크립트
```bash
# 버전 통일 자동화
python version_unifier.py

# 버전 호환성 점검
python version_compatibility_analyzer.py
```

### CI/CD 통합

#### GitHub Actions
```yaml
name: Version Compatibility Check

on:
  push:
    paths:
      - 'requirements*.txt'
      - 'Dockerfile*'
      - 'src/**'
  pull_request:
    paths:
      - 'requirements*.txt'
      - 'Dockerfile*'
      - 'src/**'

jobs:
  version-check:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Run version compatibility check
      run: python version_compatibility_analyzer.py
```

#### GitLab CI
```yaml
version_compatibility_check:
  stage: version_check
  image: python:3.11
  script:
    - pip install requests
    - python version_compatibility_analyzer.py
  rules:
    - changes:
        - requirements*.txt
        - Dockerfile*
        - src/**/*
```

## 5. 버전 업그레이드 절차

### 1. 호환성 검사
```bash
# 현재 상태 분석
python version_compatibility_analyzer.py

# 호환성 문제 확인
cat version_compatibility_report.json
```

### 2. 버전 업데이트
```bash
# requirements_common.txt에서 버전 업데이트
# 서비스별 requirements.txt에서 특화 패키지 업데이트
```

### 3. 자동화 실행
```bash
# 버전 통일 자동화
python version_unifier.py
```

### 4. 테스트 및 검증
```bash
# 빌드 테스트
docker-compose build

# 통합 테스트
python test_api_contracts.py
```

## 6. 문제 해결

### 일반적인 문제
1. **CUDA 버전 불일치**: `nvidia/cuda:11.8.2-cudnn8-runtime-ubuntu20.04`로 통일
2. **Python 버전 불일치**: 모든 Dockerfile에서 Python 3.11 사용
3. **라이브러리 버전 충돌**: `requirements_common.txt`에서 공통 버전 관리
4. **호환성 문제**: `version_compatibility_analyzer.py`로 사전 점검

### 디버깅 도구
- `version_compatibility_analyzer.py`: 현재 상태 분석
- `version_unifier.py`: 자동 수정
- `version_compatibility_report.json`: 상세 리포트
- `version_unification_report.json`: 통일 작업 리포트

## 7. 모범 사례

### 버전 관리 원칙
1. **명시적 버전 지정**: `==` 사용으로 정확한 버전 고정
2. **공통 라이브러리 통합**: `requirements_common.txt`로 중복 제거
3. **서비스별 특화**: 필요한 패키지만 서비스별 requirements에 추가
4. **정기적 점검**: CI/CD에서 자동 호환성 검사
5. **문서화**: 버전 변경 시 README 업데이트

### 개발 워크플로우
1. 새 기능 개발 시 `requirements_common.txt` 먼저 확인
2. 서비스별 패키지 필요 시 해당 requirements 파일에 추가
3. PR 생성 전 `version_compatibility_analyzer.py` 실행
4. CI 통과 후 머지

## 8. 참고 자료

- [OpenAPI 명세](./README_API.md)
- [데이터 포맷 가이드](./README_DATA_FORMAT.md)
- [버전 호환성 리포트](./version_compatibility_report.json)
- [버전 통일 리포트](./version_unification_report.json) 