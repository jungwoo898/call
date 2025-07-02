# 🗄️ Callytics 데이터베이스 아키텍처 설계

## 📊 데이터베이스 분리 전략

### **1. 🎵 오디오 분석 데이터베이스 (Audio Analysis DB)**
```yaml
Database: callytics_audio_analysis.db
Purpose: 오디오 파일 기반 기술적 분석 결과 저장
Tables:
  - audio_files: 오디오 파일 메타데이터
  - speaker_segments: 화자 분리 결과
  - transcriptions: 음성 인식 결과
  - audio_metrics: 오디오 품질 지표
  - processing_logs: 처리 과정 로그
```

### **2. 🧠 상담 품질 분석 데이터베이스 (Consultation Quality DB)**
```yaml
Database: callytics_consultation_quality.db
Purpose: LLM 기반 상담 내용 분석 및 품질 평가 결과 저장
Tables:
  - consultation_sessions: 상담 세션 정보
  - quality_metrics: 품질 평가 지표
  - sentiment_analysis: 감정 분석 결과
  - communication_patterns: 커뮤니케이션 패턴
  - improvement_suggestions: 개선 제안사항
```

### **3. 📈 통합 대시보드 데이터베이스 (Dashboard DB)**
```yaml
Database: callytics_dashboard.db
Purpose: 두 DB의 데이터를 통합하여 대시보드용 뷰 제공
Views:
  - consultation_summary: 상담 요약 뷰
  - quality_trends: 품질 트렌드 뷰
  - performance_metrics: 성능 지표 뷰
```

## 🏗️ 테이블 구조 설계

### **🎵 오디오 분석 DB 스키마**

```sql
-- 오디오 파일 테이블
CREATE TABLE audio_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER,
    duration_seconds REAL,
    sample_rate INTEGER,
    channels INTEGER,
    format TEXT,
    upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    processing_status TEXT DEFAULT 'pending',
    processing_completed_at DATETIME,
    error_message TEXT
);

-- 화자 분리 결과 테이블
CREATE TABLE speaker_segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audio_file_id INTEGER,
    speaker_id TEXT,
    start_time REAL,
    end_time REAL,
    confidence REAL,
    speaker_type TEXT, -- 'customer' or 'agent'
    FOREIGN KEY (audio_file_id) REFERENCES audio_files(id)
);

-- 음성 인식 결과 테이블
CREATE TABLE transcriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audio_file_id INTEGER,
    speaker_segment_id INTEGER,
    text_content TEXT,
    start_time REAL,
    end_time REAL,
    confidence REAL,
    language TEXT DEFAULT 'ko',
    FOREIGN KEY (audio_file_id) REFERENCES audio_files(id),
    FOREIGN KEY (speaker_segment_id) REFERENCES speaker_segments(id)
);

-- 오디오 품질 지표 테이블
CREATE TABLE audio_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audio_file_id INTEGER,
    snr_db REAL, -- 신호 대 잡음비
    clarity_score REAL, -- 명확도 점수
    volume_level REAL, -- 볼륨 레벨
    background_noise_level REAL, -- 배경 잡음 레벨
    speech_rate REAL, -- 말하기 속도
    pause_frequency REAL, -- 휴식 빈도
    FOREIGN KEY (audio_file_id) REFERENCES audio_files(id)
);

-- 처리 로그 테이블
CREATE TABLE processing_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audio_file_id INTEGER,
    processing_step TEXT,
    status TEXT,
    start_time DATETIME,
    end_time DATETIME,
    duration_seconds REAL,
    error_message TEXT,
    FOREIGN KEY (audio_file_id) REFERENCES audio_files(id)
);
```

### **🧠 상담 품질 분석 DB 스키마**

```sql
-- 상담 세션 테이블
CREATE TABLE consultation_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audio_file_id INTEGER,
    session_date DATE,
    duration_minutes REAL,
    agent_name TEXT,
    customer_id TEXT,
    consultation_type TEXT, -- 'inquiry', 'complaint', 'support', etc.
    overall_quality_score REAL,
    analysis_status TEXT DEFAULT 'pending',
    analysis_completed_at DATETIME,
    summary TEXT,
    key_issues TEXT,
    resolution_status TEXT
);

-- 품질 평가 지표 테이블
CREATE TABLE quality_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    metric_name TEXT,
    metric_value REAL,
    metric_description TEXT,
    weight REAL DEFAULT 1.0,
    FOREIGN KEY (session_id) REFERENCES consultation_sessions(id)
);

-- 감정 분석 결과 테이블
CREATE TABLE sentiment_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    speaker_type TEXT, -- 'customer' or 'agent'
    sentiment_score REAL, -- -1.0 to 1.0
    emotion_category TEXT, -- 'happy', 'angry', 'neutral', etc.
    confidence REAL,
    analysis_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES consultation_sessions(id)
);

-- 커뮤니케이션 패턴 테이블
CREATE TABLE communication_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    pattern_type TEXT, -- 'interruption', 'long_silence', 'rapid_speech', etc.
    frequency INTEGER,
    severity_score REAL,
    description TEXT,
    FOREIGN KEY (session_id) REFERENCES consultation_sessions(id)
);

-- 개선 제안사항 테이블
CREATE TABLE improvement_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    suggestion_category TEXT, -- 'communication', 'technical', 'process', etc.
    suggestion_text TEXT,
    priority TEXT, -- 'high', 'medium', 'low'
    implementation_difficulty TEXT, -- 'easy', 'medium', 'hard'
    expected_impact TEXT, -- 'high', 'medium', 'low'
    FOREIGN KEY (session_id) REFERENCES consultation_sessions(id)
);
```

### **📈 통합 대시보드 DB 뷰**

```sql
-- 상담 요약 뷰
CREATE VIEW consultation_summary AS
SELECT 
    cs.id,
    cs.session_date,
    cs.duration_minutes,
    cs.agent_name,
    cs.consultation_type,
    cs.overall_quality_score,
    af.file_name,
    COUNT(speaker_segments.id) as speaker_segments_count,
    COUNT(transcriptions.id) as transcription_count,
    AVG(am.clarity_score) as avg_clarity,
    AVG(sa.sentiment_score) as avg_sentiment
FROM consultation_sessions cs
LEFT JOIN audio_files af ON cs.audio_file_id = af.id
LEFT JOIN speaker_segments ON af.id = speaker_segments.audio_file_id
LEFT JOIN transcriptions ON af.id = transcriptions.audio_file_id
LEFT JOIN audio_metrics am ON af.id = am.audio_file_id
LEFT JOIN sentiment_analysis sa ON cs.id = sa.session_id
GROUP BY cs.id;

-- 품질 트렌드 뷰
CREATE VIEW quality_trends AS
SELECT 
    DATE(cs.session_date) as date,
    AVG(cs.overall_quality_score) as avg_quality_score,
    COUNT(*) as session_count,
    AVG(am.clarity_score) as avg_clarity,
    AVG(sa.sentiment_score) as avg_sentiment
FROM consultation_sessions cs
LEFT JOIN audio_files af ON cs.audio_file_id = af.id
LEFT JOIN audio_metrics am ON af.id = am.audio_file_id
LEFT JOIN sentiment_analysis sa ON cs.id = sa.session_id
GROUP BY DATE(cs.session_date)
ORDER BY date DESC;
```

## 🔄 데이터 흐름

```
1. 오디오 파일 업로드
   ↓
2. 오디오 분석 DB에 메타데이터 저장
   ↓
3. 오디오 처리 파이프라인 실행
   ↓
4. 오디오 분석 결과를 오디오 분석 DB에 저장
   ↓
5. 상담 품질 분석 DB에 세션 정보 생성
   ↓
6. LLM 분석 실행
   ↓
7. 상담 품질 분석 결과를 상담 품질 분석 DB에 저장
   ↓
8. 통합 대시보드 DB에서 뷰 생성
   ↓
9. 대시보드에서 통합 결과 표시
```

## 🎯 분리 효과

### **기술적 분석 (오디오 분석 DB)**
- 화자 분리 정확도
- 음성 인식 정확도
- 오디오 품질 지표
- 처리 성능 메트릭

### **비즈니스 분석 (상담 품질 분석 DB)**
- 상담 만족도
- 문제 해결율
- 고객 감정 변화
- 상담사 성과 평가
- 개선 제안사항

### **통합 인사이트 (대시보드 DB)**
- 기술적 품질과 비즈니스 성과의 상관관계
- 종합적인 상담 품질 평가
- 트렌드 분석 및 예측 