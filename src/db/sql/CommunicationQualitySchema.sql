-- =====================================================
-- 커뮤니케이션 품질 분석 테이블
-- 상담사의 6가지 품질 지표를 저장
-- =====================================================

-- 커뮤니케이션 품질 분석 결과 테이블
CREATE TABLE IF NOT EXISTS communication_quality (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audio_properties_id INTEGER,
    consultation_id TEXT,
    
    -- 6가지 품질 지표 (비율 %)
    honorific_ratio REAL DEFAULT 0.0,              -- 존댓말 사용 비율
    positive_word_ratio REAL DEFAULT 0.0,          -- 긍정 단어 비율
    negative_word_ratio REAL DEFAULT 0.0,          -- 부정 단어 비율
    euphonious_word_ratio REAL DEFAULT 0.0,        -- 쿠션어/완곡 표현 비율
    empathy_ratio REAL DEFAULT 0.0,                -- 공감 표현 비율
    apology_ratio REAL DEFAULT 0.0,                -- 사과 표현 비율
    
    -- 기본 통계 정보
    total_sentences INTEGER DEFAULT 0,              -- 총 상담사 발화 문장 수
    
    -- 새로운 정량 분석 지표 5종
    customer_sentiment_early REAL,                  -- 고객 감정 초반부 평균 (-2.0 ~ 2.0)
    customer_sentiment_late REAL,                   -- 고객 감정 후반부 평균 (-2.0 ~ 2.0)
    customer_sentiment_trend REAL,                  -- 고객 감정 변화 추세 (후반부 - 초반부)
    avg_response_latency REAL,                      -- 평균 응답 지연 시간 (초)
    task_ratio REAL,                                -- 업무 처리 비율 (고객/상담사 발화 시간)
    
    -- 새로운 LLM 기반 정성 평가 지표 2종
    suggestions REAL,                               -- 문제 해결 제안 점수 (1.0, 0.6, 0.2, 0.0)
    interruption_count INTEGER,                     -- 대화 가로채기 횟수
    
    -- 세부 분석 정보 (JSON 형태)
    analysis_details TEXT,                          -- 상세 분석 정보 (JSON)
    
    -- 메타데이터
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (audio_properties_id) REFERENCES audio_properties(id)
);

-- =====================================================
-- 커뮤니케이션 품질 세부 분석 테이블 (선택적)
-- =====================================================

-- 개별 문장별 품질 분석 결과 (상세 분석용)
CREATE TABLE IF NOT EXISTS communication_quality_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    communication_quality_id INTEGER,
    sentence_text TEXT NOT NULL,
    sentence_order INTEGER,
    
    -- 문장별 품질 지표 (0/1 플래그)
    has_honorific INTEGER DEFAULT 0,               -- 존댓말 포함 여부
    has_positive_word INTEGER DEFAULT 0,           -- 긍정 단어 포함 여부
    has_negative_word INTEGER DEFAULT 0,           -- 부정 단어 포함 여부
    has_euphonious_word INTEGER DEFAULT 0,         -- 쿠션어 포함 여부
    has_empathy INTEGER DEFAULT 0,                 -- 공감 표현 포함 여부
    has_apology INTEGER DEFAULT 0,                 -- 사과 표현 포함 여부
    
    -- 매칭된 패턴 정보
    matched_patterns TEXT,                          -- 매칭된 패턴들 (JSON)
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (communication_quality_id) REFERENCES communication_quality(id)
);

-- =====================================================
-- 성능 최적화 인덱스
-- =====================================================

-- 커뮤니케이션 품질 관련 인덱스
CREATE INDEX IF NOT EXISTS idx_communication_quality_audio_id ON communication_quality(audio_properties_id);
CREATE INDEX IF NOT EXISTS idx_communication_quality_consultation_id ON communication_quality(consultation_id);
CREATE INDEX IF NOT EXISTS idx_communication_quality_created_at ON communication_quality(created_at);

-- 품질 지표별 인덱스 (분석 및 리포팅용)
CREATE INDEX IF NOT EXISTS idx_communication_quality_honorific_ratio ON communication_quality(honorific_ratio);
CREATE INDEX IF NOT EXISTS idx_communication_quality_positive_word_ratio ON communication_quality(positive_word_ratio);
CREATE INDEX IF NOT EXISTS idx_communication_quality_negative_word_ratio ON communication_quality(negative_word_ratio);
CREATE INDEX IF NOT EXISTS idx_communication_quality_empathy_ratio ON communication_quality(empathy_ratio);

-- 새로운 정량 분석 지표 인덱스
CREATE INDEX IF NOT EXISTS idx_communication_quality_sentiment_trend ON communication_quality(customer_sentiment_trend);
CREATE INDEX IF NOT EXISTS idx_communication_quality_response_latency ON communication_quality(avg_response_latency);
CREATE INDEX IF NOT EXISTS idx_communication_quality_task_ratio ON communication_quality(task_ratio);

-- 새로운 LLM 기반 정성 평가 지표 인덱스
CREATE INDEX IF NOT EXISTS idx_communication_quality_suggestions ON communication_quality(suggestions);
CREATE INDEX IF NOT EXISTS idx_communication_quality_interruption_count ON communication_quality(interruption_count);

-- 세부 분석 관련 인덱스
CREATE INDEX IF NOT EXISTS idx_communication_quality_details_quality_id ON communication_quality_details(communication_quality_id);
CREATE INDEX IF NOT EXISTS idx_communication_quality_details_sentence_order ON communication_quality_details(sentence_order);

-- =====================================================
-- 뷰 생성 (분석 편의성)
-- =====================================================

-- 통합 상담 분석 뷰 (기존 분석 + 커뮤니케이션 품질)
CREATE VIEW IF NOT EXISTS v_integrated_consultation_analysis AS
SELECT 
    ap.id as audio_id,
    ap.file_path,
    ap.file_name,
    ap.duration,
    ca.business_type,
    ca.classification_type,
    ca.detail_classification,
    ca.consultation_result,
    ca.summary,
    ca.confidence as analysis_confidence,
    cq.honorific_ratio,
    cq.positive_word_ratio,
    cq.negative_word_ratio,
    cq.euphonious_word_ratio,
    cq.empathy_ratio,
    cq.apology_ratio,
    cq.total_sentences,
    cq.customer_sentiment_early,
    cq.customer_sentiment_late,
    cq.customer_sentiment_trend,
    cq.avg_response_latency,
    cq.task_ratio,
    cq.suggestions,
    cq.interruption_count,
    ap.created_at
FROM audio_properties ap
LEFT JOIN consultation_analysis ca ON ap.id = ca.audio_properties_id
LEFT JOIN communication_quality cq ON ap.id = cq.audio_properties_id
ORDER BY ap.created_at DESC;

-- 커뮤니케이션 품질 요약 뷰
CREATE VIEW IF NOT EXISTS v_communication_quality_summary AS
SELECT 
    COUNT(*) as total_consultations,
    AVG(honorific_ratio) as avg_honorific_ratio,
    AVG(positive_word_ratio) as avg_positive_word_ratio,
    AVG(negative_word_ratio) as avg_negative_word_ratio,
    AVG(euphonious_word_ratio) as avg_euphonious_word_ratio,
    AVG(empathy_ratio) as avg_empathy_ratio,
    AVG(apology_ratio) as avg_apology_ratio,
    AVG(total_sentences) as avg_total_sentences,
    AVG(customer_sentiment_early) as avg_customer_sentiment_early,
    AVG(customer_sentiment_late) as avg_customer_sentiment_late,
    AVG(customer_sentiment_trend) as avg_customer_sentiment_trend,
    AVG(avg_response_latency) as avg_response_latency,
    AVG(task_ratio) as avg_task_ratio,
    AVG(suggestions) as avg_suggestions,
    AVG(interruption_count) as avg_interruption_count,
    MIN(created_at) as earliest_date,
    MAX(created_at) as latest_date
FROM communication_quality
WHERE created_at >= date('now', '-30 days');  -- 최근 30일 기준

-- =====================================================
-- 트리거 생성 (데이터 무결성)
-- =====================================================

-- 업데이트 시간 자동 갱신 트리거
CREATE TRIGGER IF NOT EXISTS tr_communication_quality_update_timestamp
    AFTER UPDATE ON communication_quality
    FOR EACH ROW
BEGIN
    UPDATE communication_quality 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END; 