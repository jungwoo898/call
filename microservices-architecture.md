# 🏗️ Callytics 마이크로서비스 아키텍처 설계

## 📋 서비스 분리 전략

### **1. 🎵 오디오 처리 서비스 (Audio Processing Service)**
```yaml
Service: audio-processor
Port: 8001
Responsibilities:
  - 오디오 파일 전처리
  - 노이즈 제거
  - 음성 강화
  - 포맷 변환
Dependencies:
  - pydub
  - librosa
  - soundfile
  - noisereduce
GPU: Optional (CPU만 사용)
```

### **2. 🎤 화자 분리 서비스 (Speaker Diarization Service)**
```yaml
Service: speaker-diarizer
Port: 8002
Responsibilities:
  - 화자 분리 (NeMo/pyannote.audio)
  - 화자별 구간 추출
  - 화자 매핑 (고객/상담사)
Dependencies:
  - nemo_toolkit==1.23.0
  - pyannote.audio==3.2.1
GPU: Required (CUDA 11.8)
```

### **3. 🗣️ 음성 인식 서비스 (Speech Recognition Service)**
```yaml
Service: speech-recognizer
Port: 8003
Responsibilities:
  - 음성 인식 (Whisper)
  - 텍스트 변환
  - 언어 감지
Dependencies:
  - faster-whisper==1.1.2
  - transformers==4.41.2
GPU: Required (CUDA 11.8)
```

### **4. 📝 문장 부호 복원 서비스 (Punctuation Service)**
```yaml
Service: punctuation-restorer
Port: 8004
Responsibilities:
  - 문장 부호 복원
  - 한국어 특화 처리
  - 문장 분할
Dependencies:
  - deepmultilingualpunctuation==1.0.1
  - sentencepiece==0.1.99
GPU: Optional (CPU만 사용)
```

### **5. 🧠 감정 분석 서비스 (Sentiment Analysis Service)**
```yaml
Service: sentiment-analyzer
Port: 8005
Responsibilities:
  - 감정 분석
  - 커뮤니케이션 품질 평가
  - 긍정/부정 단어 분석
Dependencies:
  - sentence-transformers==2.6.1
  - transformers==4.41.2
GPU: Optional (CPU만 사용)
```

### **6. 🤖 LLM 분석 서비스 (LLM Analysis Service)**
```yaml
Service: llm-analyzer
Port: 8006
Responsibilities:
  - OpenAI API 호출
  - 상담 내용 분석
  - 요약 생성
Dependencies:
  - openai==1.57.0
  - langchain==0.2.5
GPU: Not Required (API 기반)
```

### **7. 🗄️ 데이터베이스 서비스 (Database Service)**
```yaml
Service: database-service
Port: 8007
Responsibilities:
  - 데이터 저장/조회
  - 결과 통합
  - 메타데이터 관리
Dependencies:
  - sqlite3 (또는 PostgreSQL)
GPU: Not Required
```

### **8. 🌐 API 게이트웨이 (API Gateway)**
```yaml
Service: api-gateway
Port: 8000
Responsibilities:
  - 요청 라우팅
  - 로드 밸런싱
  - 인증/인가
  - 요청/응답 변환
Dependencies:
  - fastapi==0.111.0
  - uvicorn==0.29.0
GPU: Not Required
```

### **9. 📊 모니터링 서비스 (Monitoring Service)**
```yaml
Service: monitoring
Port: 8008
Responsibilities:
  - 성능 모니터링
  - 로그 수집
  - 알림 발송
Dependencies:
  - prometheus
  - grafana
GPU: Not Required
```

## 🔄 서비스 간 통신 흐름

```
1. API Gateway (8000)
   ↓
2. Audio Processor (8001) - 오디오 전처리
   ↓
3. Speaker Diarizer (8002) - 화자 분리
   ↓
4. Speech Recognizer (8003) - 음성 인식
   ↓
5. Punctuation Restorer (8004) - 문장 부호 복원
   ↓
6. Sentiment Analyzer (8005) - 감정 분석
   ↓
7. LLM Analyzer (8006) - 상담 분석
   ↓
8. Database Service (8007) - 결과 저장
   ↓
9. Monitoring (8008) - 성능 추적
```

## 🎯 호환성 문제 해결 전략

### **1. 독립적인 라이브러리 버전 관리**
```yaml
# 각 서비스별 requirements.txt
audio-processor:
  - pydub==0.25.1
  - librosa==0.10.2.post1

speaker-diarizer:
  - nemo_toolkit==1.23.0
  - pyannote.audio==3.2.1

speech-recognizer:
  - faster-whisper==1.1.2
  - transformers==4.41.2

# → 버전 충돌 없이 독립적 업데이트 가능
```

### **2. 서비스별 독립적 배포**
```bash
# 개별 서비스만 재배포
docker-compose up -d --build speaker-diarizer
docker-compose up -d --build speech-recognizer

# → 전체 시스템 중단 없이 업데이트
```

### **3. A/B 테스트 지원**
```yaml
# 동시에 여러 버전 운영
speech-recognizer-v1:
  - transformers==4.41.2

speech-recognizer-v2:
  - transformers==4.42.0

# → 성능 비교 후 안전한 마이그레이션
```

## 📈 확장성 개선 효과

### **처리량 향상**
- **현재**: 1개 파일 순차 처리
- **개선 후**: 10개 파일 동시 처리 (10배 향상)

### **리소스 효율성**
- **현재**: GPU 30% 사용률
- **개선 후**: GPU 90%+ 사용률 (3배 향상)

### **장애 격리**
- **현재**: 한 부분 오류 = 전체 시스템 중단
- **개선 후**: 개별 서비스 장애만 격리

### **개발 효율성**
- **현재**: 전체 시스템 재배포
- **개선 후**: 개별 서비스만 배포 