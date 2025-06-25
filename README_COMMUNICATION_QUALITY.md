# 📊 상담사 커뮤니케이션 품질 분석 시스템

## 🎯 개요

Callytics 프로젝트에 **상담사 커뮤니케이션 품질 분석 기능**이 추가되었습니다. 이 기능은 화자 분리된 상담 음성 데이터를 분석하여 상담사의 커뮤니케이션 스킬을 6가지 정량적 지표로 평가합니다.

## 📋 6가지 품질 지표

### 1. 🎭 존댓말 사용 비율 (`honorific_ratio`)
- **정의**: 상담사가 존댓말을 일관되게 사용하는지 평가
- **판별 기준**: 
  - 높임의 종결 어미: ~습니다, ~ㅂ니다, ~세요, ~셔요, ~까요? 등
  - 주체 높임 선어말 어미: -(으)시- (예: "확인하시고", "오시면")
- **계산식**: (존댓말 포함 문장 수 / 상담사 총 문장 수) × 100

### 2. 😊 긍정 단어 비율 (`positive_word_ratio`)
- **정의**: 긍정적인 어휘를 사용하여 고객에게 안정감을 주는지 평가
- **판별 기준**: KNU 한국어 감성사전의 polarity 점수가 0보다 큰(> 0) 단어
- **계산식**: (긍정 단어 포함 문장 수 / 상담사 총 문장 수) × 100

### 3. 😟 부정 단어 비율 (`negative_word_ratio`)
- **정의**: 부정적인 어휘 사용을 지양하고 긍정 화법을 사용하는지 평가
- **판별 기준**: KNU 한국어 감성사전의 polarity 점수가 0보다 작은(< 0) 단어
- **계산식**: (부정 단어 포함 문장 수 / 상담사 총 문장 수) × 100

### 4. 🛡️ 쿠션어/완곡 표현 비율 (`euphonious_word_ratio`)
- **정의**: 고객이 느낄 수 있는 부담이나 불쾌감을 줄여주는 표현 사용 평가
- **판별 기준**:
  - 쿠션어: 실례지만, 죄송하지만, 괜찮으시다면, 혹시, 번거로우시겠지만, 만약
  - 완곡 표현: ~인 것 같습니다, ~ㄹ 것 같습니다, ~하기는 어렵습니다, ~ㄹ 수 있을까요?, ~해 주시겠어요?
- **계산식**: (쿠션어/완곡 표현 포함 문장 수 / 상담사 총 문장 수) × 100

### 5. 🤝 공감 표현 비율 (`empathy_ratio`)
- **정의**: 고객의 감정과 상황을 이해하고 있음을 표현하는지 평가
- **판별 기준**: ~하셨겠어요, ~하셨겠네요, 많이 힘드셨죠, 걱정되셨겠어요, 어떤 마음인지 알 것 같습니다, 제가 고객님 입장이라도, 저런, 아이고
- **계산식**: (공감 표현 포함 문장 수 / 상담사 총 문장 수) × 100

### 6. 🙏 사과 표현 비율 (`apology_ratio`)
- **정의**: 불편이나 문제 상황에 대해 적절하게 사과 표현을 사용하는지 평가
- **판별 기준**: 죄송합니다, 사과드립니다, 미안합니다, 양해 부탁드립니다, 너그러이 이해해주시기 바랍니다
- **계산식**: (사과 표현 포함 문장 수 / 상담사 총 문장 수) × 100

## 🚀 사용 방법

### 1. 기본 사용법

```python
from src.text.communication_quality_analyzer import CommunicationQualityAnalyzer

# 분석기 초기화
analyzer = CommunicationQualityAnalyzer()

# 화자 분리된 발화 데이터 (JSON 형태)
utterances_data = [
    {"speaker": "고객", "text": "안녕하세요. 요금 문의드리고 싶습니다."},
    {"speaker": "상담사", "text": "안녕하세요, 고객님. 도와드리겠습니다."},
    {"speaker": "상담사", "text": "실례지만 휴대폰 번호를 알려주시겠어요?"},
    # ... 더 많은 발화 데이터
]

# 커뮤니케이션 품질 분석 수행
result = analyzer.analyze_communication_quality(utterances_data)

# 결과 출력
analyzer.print_analysis_report(result)
```

### 2. 통합 분석기 사용법

```python
from src.integrated_analyzer import IntegratedAnalyzer

# 통합 분석기 초기화
analyzer = IntegratedAnalyzer()

# 오디오 파일 분석 (자동으로 커뮤니케이션 품질 분석 포함)
result = analyzer.analyze_consultation("path/to/audio.wav")

# 커뮤니케이션 품질 결과 확인
quality_metrics = result['communication_quality']
print(f"존댓말 사용 비율: {quality_metrics['honorific_ratio']}%")
print(f"긍정 단어 비율: {quality_metrics['positive_word_ratio']}%")
```

### 3. 데이터베이스 저장

분석 결과는 자동으로 `communication_quality` 테이블에 저장됩니다:

```sql
-- 커뮤니케이션 품질 조회
SELECT 
    honorific_ratio,
    positive_word_ratio,
    negative_word_ratio,
    euphonious_word_ratio,
    empathy_ratio,
    apology_ratio,
    total_sentences
FROM communication_quality
WHERE consultation_id = 'your_consultation_id';
```

## 📊 결과 형태

### JSON 출력 예시

```json
{
  "honorific_ratio": 85.71,
  "positive_word_ratio": 28.57,
  "negative_word_ratio": 14.29,
  "euphonious_word_ratio": 42.86,
  "empathy_ratio": 14.29,
  "apology_ratio": 14.29,
  "total_sentences": 7,
  "analysis_details": {
    "honorific_sentences": 6,
    "positive_word_sentences": 2,
    "negative_word_sentences": 1,
    "euphonious_sentences": 3,
    "empathy_sentences": 1,
    "apology_sentences": 1,
    "sample_sentences": {
      "honorific": ["안녕하세요, 고객님", "도와드리겠습니다"],
      "euphonious": ["실례지만", "혹시"],
      "empathy": ["걱정되셨겠어요"],
      "apology": ["죄송합니다"]
    }
  }
}
```

### DataFrame 형태

```python
# DataFrame으로 변환
df = analyzer.export_results_to_dataframe(result)
print(df)

#    honorific_ratio  positive_word_ratio  negative_word_ratio  ...
# 0            85.71                28.57                14.29  ...
```

## 🎯 품질 평가 기준

### 우수 (✅)
- **존댓말 사용**: 80% 이상
- **긍정 단어**: 30% 이상  
- **부정 단어**: 10% 이하
- **쿠션어**: 20% 이상

### 개선 필요 (⚠️)
- **존댓말 사용**: 60-80%
- **긍정 단어**: 15-30%
- **부정 단어**: 10-20%
- **쿠션어**: 10-20%

### 부족 (❌)
- **존댓말 사용**: 60% 미만
- **긍정 단어**: 15% 미만
- **부정 단어**: 20% 초과
- **쿠션어**: 10% 미만

## 🛠️ 테스트 및 검증

### 간단 테스트 실행

```bash
# 기본 기능 테스트
python simple_quality_test.py

# 전체 시스템 테스트 (의존성 설치 필요)
python test_communication_quality.py
```

### 테스트 결과 예시

```
🚀 커뮤니케이션 품질 분석 - 간단 테스트
============================================================
📊 품질 지표 결과:
  존댓말 사용 비율: 41.2% (7/17)
  쿠션어 사용 비율: 23.5% (4/17)
  공감 표현 비율: 5.9% (1/17)
  사과 표현 비율: 5.9% (1/17)
```

## 📁 파일 구조

```
src/
├── text/
│   ├── communication_quality_analyzer.py  # 메인 분석기
│   └── ...
├── db/
│   ├── sql/
│   │   ├── CommunicationQualitySchema.sql  # DB 스키마
│   │   └── ...
│   └── manager.py  # DB 매니저 (품질 저장/조회 메서드 추가)
├── integrated_analyzer.py  # 통합 분석기 (품질 분석 통합)
└── ...

# 테스트 파일들
simple_quality_test.py           # 간단한 기능 테스트
test_communication_quality.py   # 전체 기능 테스트
```

## 🔧 설정 및 커스터마이징

### KNU 감성사전 설정

```python
# 자동 다운로드 (기본)
analyzer = CommunicationQualityAnalyzer()

# 로컬 파일 사용
# data/knu_sentiment_dict.json 파일이 있으면 자동으로 로드
```

### 패턴 커스터마이징

```python
# 분석기 초기화 후 패턴 수정 가능
analyzer = CommunicationQualityAnalyzer()

# 존댓말 패턴 추가
analyzer.honorific_patterns.append(r'새로운패턴')

# 쿠션어 패턴 추가
analyzer.euphonious_patterns.append(r'새로운쿠션어')
```

## 📈 활용 사례

### 1. 실시간 상담 품질 모니터링
```python
# 실시간으로 상담 품질 분석 및 피드백
for consultation in real_time_consultations:
    quality = analyzer.analyze_communication_quality(consultation.utterances)
    if quality.honorific_ratio < 60:
        send_alert("존댓말 사용 개선 필요", consultation.id)
```

### 2. 상담사 교육 자료 생성
```python
# 낮은 점수 문장들을 교육 자료로 활용
low_quality_samples = quality_result.analysis_details['sample_sentences']
generate_training_material(low_quality_samples)
```

### 3. 품질 트렌드 분석
```sql
-- 월별 품질 트렌드 분석
SELECT 
    strftime('%Y-%m', created_at) as month,
    AVG(honorific_ratio) as avg_honorific,
    AVG(empathy_ratio) as avg_empathy
FROM communication_quality
GROUP BY month
ORDER BY month;
```

## 🚨 주의사항

1. **화자 식별**: 상담사 발화가 정확히 식별되어야 합니다 (speaker 필드에 '상담사', 'agent', 'csr' 등 포함)
2. **문장 분리**: 긴 발화는 자동으로 문장 단위로 분리되어 분석됩니다
3. **감성사전**: 인터넷 연결이 필요할 수 있습니다 (최초 다운로드 시)
4. **성능**: 대량 데이터 처리 시 시간이 소요될 수 있습니다

## 🔄 업데이트 내역

### v1.0.0 (2024-01-XX)
- ✅ 6가지 품질 지표 분석 기능 추가
- ✅ KNU 한국어 감성사전 연동
- ✅ 데이터베이스 저장/조회 기능
- ✅ 통합 분석기에 품질 분석 통합
- ✅ 테스트 스크립트 및 문서 작성

## 🤝 기여하기

새로운 패턴이나 개선사항이 있으시면 다음과 같이 기여해주세요:

1. 새로운 패턴 제안: `communication_quality_analyzer.py`의 패턴 리스트 수정
2. 감성사전 확장: 기본 감성사전에 단어 추가
3. 테스트 케이스 추가: `test_communication_quality.py`에 새로운 테스트 추가

---

📞 **문의사항이 있으시면 언제든지 연락해주세요!** 