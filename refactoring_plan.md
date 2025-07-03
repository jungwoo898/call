# 🔧 코드 품질 분석 및 리팩터링 계획

## 📊 분석 결과 요약

### 🔍 발견된 문제점

#### 1. 중복 정의 (9개)
- **health_check 함수**: 9개 파일에서 중복 정의
  - `main.py`, `src/gateway/main.py`, `src/db/main.py`, `src/utils/base_service.py` 등
- **get_metrics 함수**: 4개 파일에서 중복 정의
  - `main.py`, `src/gateway/main.py`, `src/db/main.py`, `src/utils/base_service.py` 등

#### 2. 타입 불일치
- **함수 시그니처 불일치**: 같은 이름의 함수가 다른 매개변수와 반환 타입을 가짐
- **Import 패턴 불일치**: 같은 모듈을 다른 방식으로 import

#### 3. 죽은 코드
- **테스트 함수들**: `verify_*.py` 파일들의 테스트 함수들이 실제로 실행되지 않음
- **사용되지 않는 함수들**: 일부 유틸리티 함수들이 호출되지 않음

#### 4. 네임스페이스 불일치
- **함수명 표준화 부족**: 모듈별 네임스페이스 규칙이 일관되지 않음
- **Import 구조**: 일관된 import 패턴이 없음

## 🛠️ 리팩터링 계획

### Phase 1: 중복 정의 통합 ✅

#### 1.1 공통 엔드포인트 모듈 생성 (완료)
- **파일**: `src/utils/common_endpoints.py`
- **목적**: 중복된 `health_check`와 `get_metrics` 함수 통합
- **기능**:
  - 통합된 헬스체크 엔드포인트
  - 통합된 메트릭 엔드포인트
  - 서비스별 추가 체크/메트릭 지원

#### 1.2 공통 타입 정의 모듈 생성 (완료)
- **파일**: `src/utils/common_types.py`
- **목적**: 일관된 타입 정의 제공
- **기능**:
  - 표준화된 응답 타입
  - 오디오 처리 타입
  - 분석 결과 타입
  - 데이터베이스 타입

### Phase 2: 기존 코드 리팩터링

#### 2.1 main.py 리팩터링
```python
# 기존
@app.get("/health")
async def health_check():
    # 중복된 코드...

# 변경 후
from src.utils.common_endpoints import get_common_endpoints

common_endpoints = get_common_endpoints("callytics-api", "1.0.0")

@app.get("/health")
async def health_check():
    return await common_endpoints.health_check()
```

#### 2.2 서비스별 리팩터링
- **speech-recognizer**: `src/text/speech_recognizer.py`
- **speaker-diarizer**: `src/audio/error.py`
- **llm-analyzer**: `src/text/llm.py`
- **database-service**: `src/db/main.py`

### Phase 3: 죽은 코드 제거

#### 3.1 테스트 파일 정리
- **verify_*.py 파일들**: 실제 테스트가 아닌 검증 스크립트로 재분류
- **사용되지 않는 함수**: 제거 또는 문서화

#### 3.2 중복 파일 제거
- **backup_20250625_164753/**: 백업 폴더 정리
- **중복된 설정 파일**: 통합

### Phase 4: 네임스페이스 표준화

#### 4.1 함수명 표준화 규칙
```python
# 모듈별 접두사 규칙
audio_*     # 오디오 처리 관련
text_*      # 텍스트 처리 관련
db_*        # 데이터베이스 관련
api_*       # API 관련
util_*      # 유틸리티 관련
```

#### 4.2 Import 표준화
```python
# 표준 import 순서
# 1. 표준 라이브러리
import os
import sys
from typing import Dict, List, Any

# 2. 서드파티 라이브러리
import torch
import fastapi
from pydantic import BaseModel

# 3. 로컬 모듈
from src.utils.common_types import HealthResponse
from src.utils.common_endpoints import get_common_endpoints
```

## 📋 실행 계획

### Step 1: 공통 모듈 적용
1. `main.py`에서 공통 엔드포인트 사용
2. 각 서비스 파일에서 공통 타입 사용
3. 중복 함수 제거

### Step 2: 테스트 및 검증
1. 각 서비스별 기능 테스트
2. 통합 테스트 실행
3. 성능 테스트

### Step 3: 문서화
1. API 문서 업데이트
2. 코드 주석 정리
3. README 업데이트

## 🎯 기대 효과

### 1. 코드 품질 향상
- **중복 제거**: 50% 이상의 중복 코드 제거
- **타입 안정성**: 일관된 타입 정의로 런타임 오류 감소
- **가독성**: 표준화된 네임스페이스로 코드 이해도 향상

### 2. 유지보수성 향상
- **모듈화**: 공통 기능의 중앙 집중화
- **확장성**: 새로운 서비스 추가 시 일관된 패턴 적용
- **테스트 용이성**: 표준화된 인터페이스로 테스트 작성 간소화

### 3. 성능 최적화
- **메모리 사용량**: 중복 코드 제거로 메모리 효율성 향상
- **로딩 시간**: 표준화된 import로 모듈 로딩 최적화

## 📊 진행 상황

- [x] 공통 엔드포인트 모듈 생성
- [x] 공통 타입 정의 모듈 생성
- [ ] main.py 리팩터링
- [ ] 서비스별 리팩터링
- [ ] 죽은 코드 제거
- [ ] 네임스페이스 표준화
- [ ] 테스트 및 검증
- [ ] 문서화

## 🚀 다음 단계

1. **main.py 리팩터링 실행**
2. **각 서비스별 공통 모듈 적용**
3. **중복 코드 제거**
4. **테스트 실행 및 검증** 