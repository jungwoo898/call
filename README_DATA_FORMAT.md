# Callytics 데이터 포맷 & 프로토콜 연동 가이드

## 1. 인코딩 표준

### UTF-8 통일
- **모든 텍스트 데이터**: UTF-8 인코딩 사용
- **파일 I/O**: `encoding="utf-8"` 명시
- **HTTP 헤더**: `Content-Type: application/json; charset=utf-8`
- **문자열 처리**: `.encode("utf-8")`, `.decode("utf-8")` 명시

### 예시
```python
# 파일 읽기/쓰기
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

# HTTP 응답
return JSONResponse(
    content=json.dumps(data, ensure_ascii=False),
    headers={"Content-Type": "application/json; charset=utf-8"}
)
```

## 2. 로케일 설정

### 표준 설정
- **시간대**: Asia/Seoul (UTC+9)
- **로케일**: ko_KR.UTF-8
- **언어**: ko (한국어)
- **날짜/시간 포맷**: YYYY-MM-DD HH:MM:SS

### 사용법
```python
from src.utils.locale_config import get_current_time, format_datetime

# 현재 시간 (한국 시간대)
current_time = get_current_time()

# 표준 포맷
formatted_time = format_datetime(current_time)
```

## 3. 응답 구조 표준

### 성공 응답
```json
{
    "status": "success",
    "message": null,
    "data": {
        "result": "처리 결과",
        "processing_time": 1.23
    },
    "timestamp": "2024-01-01T12:00:00+09:00"
}
```

### 오류 응답
```json
{
    "status": "error",
    "message": "오류 메시지",
    "error_code": "E001",
    "details": {
        "field": "오류 필드",
        "reason": "오류 이유"
    },
    "timestamp": "2024-01-01T12:00:00+09:00"
}
```

### 필수 필드
- `status`: "success" 또는 "error" (필수)
- `timestamp`: ISO 8601 형식 (필수)
- `message`: 문자열 또는 null (선택)
- `data`: 성공 시 결과 데이터 (선택)
- `error_code`: 오류 시 코드 (선택)

## 4. JSON Schema 검증

### 요청 검증
```python
from src.utils.schema_validation import AudioRequest, TextRequest

# 오디오 요청 검증
audio_data = {
    "audio_data": "base64_encoded_data",
    "sample_rate": 16000,
    "format": "wav"
}
validated = AudioRequest(**audio_data)

# 텍스트 요청 검증
text_data = {
    "text": "분석할 텍스트",
    "language": "ko"
}
validated = TextRequest(**text_data)
```

### 응답 검증
```python
from src.utils.schema_validation import AnalysisResponse

# 응답 생성 및 검증
response = AnalysisResponse(
    status="success",
    data={"result": "분석 결과"},
    processing_time=1.23
)
```

## 5. 중간 변환 계층 (Adapter)

### API Adapter 사용법
```python
from src.utils.api_adapter import APIAdapter

# 요청 데이터 검증 및 변환
adapter = APIAdapter()

# 오디오 요청 처리
validated_request = adapter.validate_request(request_data, "audio")

# 응답 포맷 변환
formatted_response = adapter.format_response(
    data=result_data,
    status="success",
    message="처리 완료"
)

# 인코딩 변환
converted_text = adapter.convert_encoding(
    text="텍스트",
    from_encoding="utf-8",
    to_encoding="utf-8"
)

# 데이터 타입 정규화
normalized_data = adapter.normalize_data_types(raw_data)
```

## 6. 데이터 타입 정책

### null vs 빈값 정책
- **문자열**: 빈 문자열("") → null
- **리스트**: 빈 리스트([]) 유지
- **딕셔너리**: 빈 딕셔너리({}) 유지
- **숫자**: 0 또는 null (명세에 따름)

### 타입 변환 규칙
```python
# 문자열 처리
text = "" if text is None else str(text)

# 리스트 처리
items = [] if items is None else list(items)

# 숫자 처리
number = 0 if number is None else int(number)
```

## 7. 서비스 간 연동

### 요청 전송
```python
import requests

# 표준 요청 헤더
headers = {
    "Content-Type": "application/json; charset=utf-8",
    "Accept": "application/json"
}

# 요청 데이터
data = {
    "text": "분석할 텍스트",
    "language": "ko",
    "timestamp": get_current_time().isoformat()
}

# API 호출
response = requests.post(
    "http://localhost:8002/analyze",
    json=data,
    headers=headers
)
```

### 응답 처리
```python
# 응답 검증
if response.status_code == 200:
    result = response.json()
    
    # 응답 구조 검증
    if result.get("status") == "success":
        data = result.get("data", {})
        # 데이터 처리
    else:
        error_message = result.get("message", "알 수 없는 오류")
        # 오류 처리
```

## 8. 테스트 및 검증

### 데이터 포맷 테스트
```bash
# 분석 스크립트 실행
python data_format_analyzer.py

# 표준화 스크립트 실행
python data_format_standardizer.py

# API 계약 테스트 실행
python test_api_contracts.py
```

### 검증 체크리스트
- [ ] 모든 텍스트가 UTF-8 인코딩 사용
- [ ] 시간대가 Asia/Seoul로 통일
- [ ] 응답 구조가 표준 형식 준수
- [ ] JSON Schema 검증 적용
- [ ] null/빈값 정책 통일
- [ ] Adapter 계층 활용

## 9. 문제 해결

### 일반적인 문제
1. **인코딩 오류**: UTF-8 인코딩 확인
2. **시간대 불일치**: Asia/Seoul 시간대 설정 확인
3. **응답 구조 오류**: 표준 응답 형식 확인
4. **데이터 타입 오류**: JSON Schema 검증 확인

### 디버깅 도구
- `data_format_analyzer.py`: 현재 상태 분석
- `data_format_standardizer.py`: 자동 수정
- `test_api_contracts.py`: 통합 테스트

## 10. 참고 자료

- [OpenAPI 명세](./README_API.md)
- [JSON Schema 파일](./schemas/)
- [API Adapter 모듈](./src/utils/api_adapter.py)
- [로케일 설정 모듈](./src/utils/locale_config.py)
- [스키마 검증 모듈](./src/utils/schema_validation.py) 