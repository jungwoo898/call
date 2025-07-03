# Callytics - API 기반 음성 분석 시스템

## 🚀 **API 우선 전략**

Callytics는 **로컬 모델 대신 API 기반**으로 동작하도록 설계되었습니다. 다음 API들을 지원합니다:

- **OpenAI API** (GPT-3.5-turbo, GPT-4)
- **Azure OpenAI API** 
- **Hugging Face Inference API**

## 📋 **필요한 API 키 설정**

### 1. .env 파일 설정

프로젝트 루트에 `.env` 파일을 생성하고 API 키를 설정하세요:

```bash
# .env 파일 생성
cat > .env << EOF
# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here

# Azure OpenAI API
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# Hugging Face API
HUGGINGFACE_API_TOKEN=your_huggingface_token_here

# Database Configuration
DATABASE_URL=sqlite:///app/.db/Callytics.sqlite

# Runtime Configuration
DEVICE=cuda
COMPUTE_TYPE=float16
CUDA_ALLOC_CONF=max_split_size_mb:512

# Logging
LOG_LEVEL=INFO
EOF
```

### 2. 환경 변수 설정 (선택사항)

```bash
# OpenAI API
export OPENAI_API_KEY="your_openai_api_key_here"

# Azure OpenAI API
export AZURE_OPENAI_API_KEY="your_azure_openai_api_key_here"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"

# Hugging Face API
export HUGGINGFACE_API_TOKEN="your_huggingface_token_here"
```

### 3. Docker 환경에서 실행

```bash
# .env 파일과 함께 실행
docker run -d \
  --env-file .env \
  -v $(pwd)/audio:/app/audio \
  -v $(pwd)/logs:/app/logs \
  callytics
```

### 4. docker-compose 사용

```bash
# .env 파일이 있으면 자동으로 로드됨
docker-compose up -d
```

## 🔧 **API 우선순위**

시스템은 다음 순서로 API를 사용합니다:

1. **OpenAI API** (가장 안정적)
2. **Azure OpenAI API** (엔터프라이즈용)
3. **Hugging Face API** (오픈소스 모델)

## 📊 **지원하는 기능**

### 감정 분석
- 긍정/부정/중립 분류
- API를 통한 실시간 분석

### 비속어 감지
- 한국어 비속어 자동 감지
- API 기반 정확한 판별

### 화자 분류
- 고객/상담원 역할 분류
- 대화 맥락 기반 분석

### 언어 감지
- 한국어 자동 감지
- 다국어 지원 준비

## 🚀 **빠른 시작**

### 1. .env 파일 생성
```bash
# .env 파일 생성
echo "OPENAI_API_KEY=sk-..." > .env
```

### 2. Docker 실행
```bash
docker-compose up -d
```

### 3. 오디오 파일 처리
```bash
# 오디오 파일을 /app/audio 디렉토리에 복사
cp your_audio.wav ./audio/

# 자동으로 처리됨
```

## 📈 **성능 최적화**

### API 호출 최적화
- 배치 처리로 API 호출 최소화
- 캐싱 시스템으로 중복 요청 방지
- 폴백 시스템으로 안정성 확보

### 메모리 효율성
- 로컬 모델 제거로 메모리 사용량 대폭 감소
- API 기반으로 무제한 확장 가능

## 🔍 **모니터링**

### API 상태 확인
```bash
# 컨테이너 로그 확인
docker logs callytics

# API 사용량 모니터링
curl http://localhost:8000/health
```

### Grafana 대시보드
- http://localhost:3000 (admin/admin)
- API 호출 통계
- 시스템 성능 모니터링

## ⚠️ **주의사항**

1. **API 키 보안**: `.env` 파일을 `.gitignore`에 포함하여 보안 유지
2. **API 제한**: 각 API의 요청 제한 확인
3. **비용 관리**: API 사용량 모니터링 필요
4. **네트워크**: 안정적인 인터넷 연결 필요

## 🛠️ **문제 해결**

### API 키 오류
```bash
# .env 파일 확인
cat .env

# 컨테이너 재시작
docker-compose restart
```

### 네트워크 오류
```bash
# API 연결 테스트
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

### 메모리 부족
```bash
# 시스템 리소스 확인
docker stats callytics
```

## 📞 **지원**

- **이슈 리포트**: GitHub Issues
- **문서**: 이 README 파일
- **설정**: `.env` 파일 참조

---

**🎯 목표**: 로컬 모델 없이 API만으로 완전한 음성 분석 시스템 구축

# Callytics API 통합 명세 및 연동 가이드

## 1. OpenAPI 명세
- `openapi.json` 파일 참고 (Swagger Editor에서 시각화 가능)
- 주요 엔드포인트: `/preprocess`, `/enhance`, `/segment`, `/analyze`, `/sentiment`, `/punctuation`, `/health`, `/save_result`, `/process` 등

## 2. JSON Schema
- `schemas/` 디렉토리 내 각 API별 입력/출력 스키마(JSON Schema) 제공
- 예시: `schemas/audioinput.json`, `schemas/textinput.json`, `schemas/analysisresult.json` 등

## 3. Null/빈값/타입 정책
- **문자열**: 값이 없으면 `None` (빈 문자열 "" 사용 금지)
- **리스트**: 값이 없으면 `[]` (None 사용 금지)
- **숫자**: 값이 없으면 `None` 또는 `0` (혼용 금지, 명세에 따름)
- **타입**: 명세와 100% 일치 (예: int, str, list, object 등)
- **응답 구조**: `{ "status": "success|error", "message": str, "data": object, ... }` 고정

## 4. 연동 가이드
- 모든 서비스는 명세/스키마에 맞춰 request/response를 구현해야 함
- 신규 API 추가 시 반드시 명세(OpenAPI/JSON Schema)부터 작성
- 서비스 간 연동 시 명세/스키마를 기준으로 값 전달/수신
- Swagger Editor(https://editor.swagger.io/)에서 `openapi.json` 업로드하여 예시 확인 가능

## 5. 테스트 방법
- `test_api_contracts.py` 실행 (Python 3.8+ 필요, `requests` 패키지 필요)
- 실제 각 마이크로서비스가 실행 중이어야 함
- 실행 예시:

```bash
python test_api_contracts.py
```

- 모든 테스트가 통과하면 명세/정책이 실제 서비스에 잘 적용된 것임

## 6. 참고/공유
- 본 문서와 명세/스키마 파일을 모든 개발자 및 연동팀과 공유
- 정책 위반/불일치 발견 시 즉시 수정 및 명세 동기화 