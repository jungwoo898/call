# 📊 정량 분석 지표 5종 (Quantitative Analysis Metrics)

## 🎯 개요

Callytics 시스템에 새롭게 추가된 **정량 분석 지표 5종**은 고객 감정의 변화, 상담사의 응답 속도, 발화 시간 비율 등을 수치 데이터로 분석하여 상담 품질을 객관적으로 평가할 수 있게 합니다.

기존의 6가지 커뮤니케이션 품질 지표(존댓말, 긍정/부정 단어, 쿠션어, 공감, 사과 표현)에 더해, 이번 5가지 정량 지표는 **시간 기반 분석**과 **감정 추세 분석**을 통해 상담의 동적 특성을 파악합니다.

---

## 📈 5가지 정량 분석 지표

### 1️⃣ 고객 감정 초반부 (customer_sentiment_early)
- **정의**: 상담 초반부(처음 50%)에서 고객 감정 점수의 평균값
- **범위**: -2.0 ~ 2.0 (Very Negative: -2, Negative: -1, Neutral: 0, Positive: 1, Very Positive: 2)
- **활용**: 고객의 초기 감정 상태 파악
- **안정성**: 50% 구분으로 발화가 적어도 안정적인 계산 가능

### 2️⃣ 고객 감정 후반부 (customer_sentiment_late)
- **정의**: 상담 후반부(끝 50%)에서 고객 감정 점수의 평균값
- **범위**: -2.0 ~ 2.0
- **활용**: 상담 종료 시점의 고객 감정 상태 파악
- **안정성**: 50% 구분으로 발화가 적어도 안정적인 계산 가능

### 3️⃣ 고객 감정 변화 추세 (customer_sentiment_trend)
- **정의**: 고객 감정의 변화 추세 (후반부 - 초반부)
- **계산식**: `customer_sentiment_late - customer_sentiment_early`
- **해석**:
  - **양수(+)**: 상담 과정에서 고객 감정이 개선됨 ✅
  - **음수(-)**: 상담 과정에서 고객 감정이 악화됨 ⚠️
  - **0에 가까움**: 감정 변화가 거의 없음
- **개선사항**: 33% → 50% 구분으로 안정성 향상, 발화 2개만 있어도 계산 가능

### 4️⃣ 평균 응답 지연 시간 (avg_response_latency)
- **정의**: 고객의 말이 끝난 후 상담사가 응답하기까지 걸리는 평균 시간(초)
- **계산 방법**:
  1. 전체 발화를 시간순으로 정렬
  2. 고객 → 상담사 전환 지점 탐지
  3. 지연시간 = (상담사 발화 시작시간) - (고객 발화 종료시간)
  4. 모든 지연시간의 평균 계산
- **평가 기준**:
  - **0~2초**: 매우 빠른 응답 ✅
  - **2~5초**: 적절한 응답 속도 ⚡
  - **5초 이상**: 응답 지연, 개선 필요 ⚠️

### 5️⃣ 업무 처리 비율 (task_ratio)
- **정의**: 전체 상담 시간 중 고객과 상담사의 발화 시간 비율
- **계산식**: `(고객 총 발화 시간) / (상담사 총 발화 시간)`
- **해석**:
  - **1.0 초과**: 고객이 상담사보다 많이 말함 (설명/문의가 많음)
  - **1.0 미만**: 상담사가 고객보다 많이 말함 (안내/설명 제공)
  - **1.0에 가까움**: 균형적인 대화

---

## 🔧 기술적 구현

### 데이터 요구사항
```json
{
  "speaker": "고객 또는 상담사",
  "text": "발화 내용",
  "sentiment": "positive/negative/neutral/very_positive/very_negative",
  "start_time": 0.0,
  "end_time": 3.5
}
```

### 감정 점수 매핑
```python
sentiment_mapping = {
    'positive': 1.0,
    'neutral': 0.0, 
    'negative': -1.0,
    'very positive': 2.0,
    'very negative': -2.0,
    # 한국어 지원
    '긍정': 1.0,
    '중립': 0.0,
    '부정': -1.0,
    '매우긍정': 2.0,
    '매우부정': -2.0
}
```

### 화자 식별 키워드
- **고객**: ['고객', 'customer', 'client', 'user']
- **상담사**: ['상담사', 'counselor', 'agent', 'csr', 'staff']

---

## 📊 데이터베이스 스키마

### communication_quality 테이블 확장
```sql
-- 새로운 정량 분석 지표 5종
customer_sentiment_early REAL,      -- 고객 감정 초반부 평균 (-2.0 ~ 2.0)
customer_sentiment_late REAL,       -- 고객 감정 후반부 평균 (-2.0 ~ 2.0)  
customer_sentiment_trend REAL,      -- 고객 감정 변화 추세 (후반부 - 초반부)
avg_response_latency REAL,          -- 평균 응답 지연 시간 (초)
task_ratio REAL,                    -- 업무 처리 비율 (고객/상담사 발화 시간)
```

### 성능 최적화 인덱스
```sql
CREATE INDEX idx_sentiment_trend ON communication_quality(customer_sentiment_trend);
CREATE INDEX idx_response_latency ON communication_quality(avg_response_latency);
CREATE INDEX idx_task_ratio ON communication_quality(task_ratio);
```

---

## 🧪 테스트 결과 예시

### 테스트 케이스 1: 감정 개선 상담
```
고객 감정 초반부: -1.5 (부정적 시작)
고객 감정 후반부: 1.5 (긍정적 종료)
감정 변화 추세: 3.0 (큰 개선) ✅
평균 응답 지연: 1.214초 (빠른 응답) ✅
업무 처리 비율: 0.896 (상담사 주도적 안내)
```

### 테스트 케이스 2: 감정 악화 상담
```
고객 감정 초반부: 0.0 (중립적 시작)
고객 감정 후반부: -2.0 (매우 부정적 종료)
감정 변화 추세: -2.0 (악화) ⚠️
평균 응답 지연: 2.0초 (적절한 응답)
업무 처리 비율: 1.6 (고객 불만 표출 많음)
```

### 테스트 케이스 3: 응답 지연 상담
```
평균 응답 지연: 6.0초 (지연 문제) ⚠️
업무 처리 비율: 0.857 (상담사 설명 중심)
```

---

## 🚀 사용 방법

### 1. Python 코드에서 직접 사용
```python
from src.text.communication_quality_analyzer import CommunicationQualityAnalyzer

# 분석기 초기화
analyzer = CommunicationQualityAnalyzer()

# 발화 데이터 (시간 정보와 감정 정보 포함)
utterances = [
    {
        "speaker": "고객",
        "text": "서비스에 문제가 있어요",
        "start_time": 0.0,
        "end_time": 2.5,
        "sentiment": "negative"
    },
    {
        "speaker": "상담사", 
        "text": "죄송합니다. 어떤 문제인지 말씀해주세요",
        "start_time": 3.0,
        "end_time": 6.0,
        "sentiment": "positive"
    }
    # ... 추가 발화들
]

# 분석 실행
result = analyzer.analyze_communication_quality(utterances)

# 새로운 지표 확인
print(f"고객 감정 변화 추세: {result.customer_sentiment_trend}")
print(f"평균 응답 지연 시간: {result.avg_response_latency}초")
print(f"업무 처리 비율: {result.task_ratio}")
```

### 2. 통합 분석기 사용
```python
from src.integrated_analyzer import IntegratedAnalyzer

# 통합 분석기 초기화
analyzer = IntegratedAnalyzer()

# 오디오 파일 분석 (자동으로 모든 지표 계산)
result = analyzer.analyze_consultation("audio/consultation.wav")

# 결과 확인
quality = result['communication_quality']
print(f"감정 변화 추세: {quality['customer_sentiment_trend']}")
print(f"응답 지연 시간: {quality['avg_response_latency']}초")
print(f"업무 처리 비율: {quality['task_ratio']}")
```

### 3. 데이터베이스에서 조회
```python
from src.db.manager import DatabaseManager

db = DatabaseManager()

# 특정 상담의 정량 지표 조회
quality_data = db.get_communication_quality("consultation_123")

if quality_data:
    print(f"감정 변화 추세: {quality_data['customer_sentiment_trend']}")
    print(f"응답 지연 시간: {quality_data['avg_response_latency']}초")
    print(f"업무 처리 비율: {quality_data['task_ratio']}")
```

---

## 📋 활용 시나리오

### 1. 상담사 성과 평가
- **응답 지연 시간**으로 상담사의 신속성 평가
- **감정 변화 추세**로 문제 해결 능력 평가
- **업무 처리 비율**로 상담 스타일 분석

### 2. 상담 품질 모니터링
- 실시간 감정 변화 추적으로 상담 개입 시점 판단
- 응답 지연 알림으로 서비스 품질 관리
- 업무 처리 비율로 상담 효율성 분석

### 3. 교육 및 개선
- 감정 악화 상담 케이스 분석으로 교육 자료 생성
- 응답 지연 패턴 분석으로 시스템 개선점 도출
- 우수 상담 사례 발굴 및 공유

### 4. 리포팅 및 분석
- 일/주/월별 정량 지표 트렌드 분석
- 상담사별, 팀별 성과 비교
- 고객 만족도와 정량 지표 상관관계 분석

---

## ⚠️ 주의사항

### 데이터 품질 요구사항
1. **시간 정보**: `start_time`, `end_time`이 정확해야 응답 지연 시간과 업무 처리 비율 계산 가능
2. **감정 정보**: `sentiment` 필드가 있어야 감정 변화 추세 계산 가능
3. **화자 정보**: `speaker` 필드에서 고객/상담사 구분이 명확해야 함

### 최소 데이터 요구사항
- **감정 분석**: 고객 발화 최소 3개 이상
- **응답 지연 분석**: 고객→상담사 전환 최소 1회 이상
- **업무 처리 비율**: 고객과 상담사 발화 각각 최소 1개 이상

### 예외 처리
- 데이터 부족 시 해당 지표는 `None` 값 반환
- 시간 정보 누락 시 시간 기반 지표 계산 불가
- 감정 정보 누락 시 감정 관련 지표 계산 불가

---

## 🔮 향후 계획

### 단기 계획
- [ ] 실시간 지표 모니터링 대시보드 구축
- [ ] 지표별 임계값 설정 및 알림 기능
- [ ] 상담사별 성과 리포트 자동 생성

### 중기 계획  
- [ ] 머신러닝 기반 감정 예측 모델 통합
- [ ] 음성 톤 분석과 정량 지표 연계
- [ ] 고객 만족도 예측 모델 개발

### 장기 계획
- [ ] 실시간 상담 코칭 시스템 구축
- [ ] 개인화된 상담 스타일 추천
- [ ] 업계 벤치마크 비교 기능

---

## 📞 지원 및 문의

- **개발팀**: Callytics Development Team
- **문서 버전**: v1.0
- **최종 업데이트**: 2024-12-24

정량 분석 지표 관련 문의사항이나 개선 제안이 있으시면 언제든 연락주세요! 🚀 