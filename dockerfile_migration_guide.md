# Dockerfile 마이그레이션 가이드

## Phase 1: 즉시 적용 (CRITICAL)

### 런타임 스테이지에 추가:
```dockerfile
# PortAudio 런타임 라이브러리
RUN apt-get update && apt-get install -y \
    libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

# NLTK 데이터 복사
ENV NLTK_DATA=/usr/local/nltk_data
COPY --from=builder /root/nltk_data /usr/local/nltk_data
```

## Phase 2: FastAPI 호환성

### requirements 교체:
```dockerfile
COPY requirements_phase2.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
```

### API 호환성 테스트 추가:
```dockerfile
RUN python -c 'import fastapi; import pydantic; import gradio; print("호환성 OK")'
```

## Phase 3: 전면 최적화

### 의존성 검증 추가:
```dockerfile
RUN pip install pip-tools && pip check
```

## 주의사항

1. 각 Phase마다 별도 이미지 빌드 테스트
2. Phase 2에서 API 변경사항 확인
3. Phase 3는 충분한 테스트 후 적용