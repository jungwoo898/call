-- ========================================================================
-- 🚀 Callytics PostgreSQL 마이그레이션 스키마
-- ========================================================================
-- 목적: 기존 SQLite 데이터를 PostgreSQL로 완전 이전
-- 특징: 데이터 손실 없음, 효율성 개선, 정규화 최적화

-- ========================================================================
-- 1. 확장 기능 활성화
-- ========================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ========================================================================
-- 2. 🎵 오디오 분석 스키마 (audio_analysis)
-- ========================================================================

-- 오디오 파일 테이블 (PostgreSQL 최적화)
CREATE TABLE audio_files (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    file_size BIGINT CHECK (file_size > 0),
    duration_seconds DECIMAL(10,3) CHECK (duration_seconds > 0),
    sample_rate INTEGER CHECK (sample_rate > 0),
    channels SMALLINT CHECK (channels BETWEEN 1 AND 8),
    format VARCHAR(10) NOT NULL,
    upload_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    processing_status audio_status DEFAULT 'pending',
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ENUM 타입 정의
CREATE TYPE audio_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'reprocessing');
CREATE TYPE speaker_type AS ENUM ('customer', 'agent', 'unknown', 'system');
CREATE TYPE processing_status AS ENUM ('started', 'completed', 'failed', 'skipped');

-- 화자 분리 결과 테이블
CREATE TABLE speaker_segments (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    audio_file_id INTEGER NOT NULL REFERENCES audio_files(id) ON DELETE CASCADE,
    speaker_id VARCHAR(50) NOT NULL,
    start_time DECIMAL(10,3) NOT NULL CHECK (start_time >= 0),
    end_time DECIMAL(10,3) NOT NULL CHECK (end_time > start_time),
    confidence DECIMAL(5,4) CHECK (confidence BETWEEN 0 AND 1),
    speaker_type speaker_type DEFAULT 'unknown',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 음성 인식 결과 테이블
CREATE TABLE transcriptions (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    audio_file_id INTEGER NOT NULL REFERENCES audio_files(id) ON DELETE CASCADE,
    speaker_segment_id INTEGER REFERENCES speaker_segments(id) ON DELETE CASCADE,
    text_content TEXT NOT NULL,
    start_time DECIMAL(10,3) NOT NULL CHECK (start_time >= 0),
    end_time DECIMAL(10,3) NOT NULL CHECK (end_time > start_time),
    confidence DECIMAL(5,4) CHECK (confidence BETWEEN 0 AND 1),
    language VARCHAR(5) DEFAULT 'ko',
    punctuation_restored BOOLEAN DEFAULT FALSE,
    word_count INTEGER GENERATED ALWAYS AS (
        array_length(string_to_array(trim(text_content), ' '), 1)
    ) STORED,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 오디오 품질 지표 테이블
CREATE TABLE audio_metrics (
    id SERIAL PRIMARY KEY,
    audio_file_id INTEGER NOT NULL UNIQUE REFERENCES audio_files(id) ON DELETE CASCADE,
    snr_db DECIMAL(6,2), -- 신호 대 잡음비
    clarity_score DECIMAL(5,4) CHECK (clarity_score BETWEEN 0 AND 1),
    volume_level DECIMAL(6,2), -- 볼륨 레벨 (dB)
    background_noise_level DECIMAL(6,2), -- 배경 잡음 레벨 (dB)
    speech_rate DECIMAL(6,2) CHECK (speech_rate > 0), -- 말하기 속도 (단어/분)
    pause_frequency DECIMAL(6,2) CHECK (pause_frequency >= 0), -- 휴식 빈도
    audio_quality_score DECIMAL(5,4) CHECK (audio_quality_score BETWEEN 0 AND 1),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ========================================================================
-- 3. 🧠 상담 품질 분석 스키마 (consultation_quality)
-- ========================================================================

-- ENUM 타입 정의
CREATE TYPE consultation_type AS ENUM ('inquiry', 'complaint', 'support', 'sales', 'technical', 'billing', 'other');
CREATE TYPE analysis_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'reprocessing');
CREATE TYPE resolution_status AS ENUM ('resolved', 'partially_resolved', 'unresolved', 'escalated');
CREATE TYPE metric_category AS ENUM ('communication', 'technical', 'process', 'attitude', 'resolution');
CREATE TYPE emotion_category AS ENUM ('happy', 'satisfied', 'neutral', 'frustrated', 'angry', 'anxious', 'confused');
CREATE TYPE pattern_type AS ENUM ('interruption', 'long_silence', 'rapid_speech', 'repetition', 'clarification_request', 'empathy_expression', 'solution_proposal');
CREATE TYPE impact_type AS ENUM ('positive', 'negative', 'neutral');
CREATE TYPE priority_level AS ENUM ('high', 'medium', 'low');
CREATE TYPE difficulty_level AS ENUM ('easy', 'medium', 'hard');
CREATE TYPE target_audience AS ENUM ('agent', 'supervisor', 'system', 'process');
CREATE TYPE suggestion_category AS ENUM ('communication', 'technical', 'process', 'attitude', 'knowledge', 'system');
CREATE TYPE keyword_category AS ENUM ('product', 'service', 'issue', 'emotion', 'action', 'technical');

-- 상담 세션 테이블 (메인 테이블)
CREATE TABLE consultation_sessions (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    audio_file_id INTEGER NOT NULL REFERENCES audio_files(id) ON DELETE RESTRICT,
    session_date DATE NOT NULL,
    duration_minutes DECIMAL(8,2) NOT NULL CHECK (duration_minutes > 0),
    agent_name VARCHAR(100),
    agent_id VARCHAR(50), -- 새로 추가: 상담사 ID
    customer_id VARCHAR(100),
    customer_phone VARCHAR(20), -- 새로 추가: 고객 전화번호 (마스킹)
    consultation_type consultation_type,
    overall_quality_score DECIMAL(5,4) CHECK (overall_quality_score BETWEEN 0 AND 1),
    analysis_status analysis_status DEFAULT 'pending',
    analysis_started_at TIMESTAMPTZ,
    analysis_completed_at TIMESTAMPTZ,
    analysis_duration_seconds INTEGER GENERATED ALWAYS AS (
        CASE 
            WHEN analysis_completed_at IS NOT NULL AND analysis_started_at IS NOT NULL 
            THEN EXTRACT(EPOCH FROM (analysis_completed_at - analysis_started_at))::INTEGER
            ELSE NULL 
        END
    ) STORED,
    analysis_error_message TEXT,
    summary TEXT,
    key_issues JSONB, -- JSON으로 구조화
    resolution_status resolution_status,
    customer_satisfaction_score DECIMAL(5,4) CHECK (customer_satisfaction_score BETWEEN 0 AND 1),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 품질 평가 지표 테이블
CREATE TABLE quality_metrics (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES consultation_sessions(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(8,4) NOT NULL,
    metric_description TEXT,
    weight DECIMAL(3,2) DEFAULT 1.0 CHECK (weight BETWEEN 0 AND 1),
    category metric_category,
    normalized_value DECIMAL(5,4) GENERATED ALWAYS AS (
        LEAST(metric_value * weight, 1.0)
    ) STORED,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, metric_name) -- 중복 방지
);

-- 감정 분석 결과 테이블
CREATE TABLE sentiment_analysis (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES consultation_sessions(id) ON DELETE CASCADE,
    speaker_type speaker_type NOT NULL,
    time_segment_start DECIMAL(10,3) CHECK (time_segment_start >= 0), -- 새로 추가
    time_segment_end DECIMAL(10,3) CHECK (time_segment_end > time_segment_start), -- 새로 추가
    sentiment_score DECIMAL(6,4) NOT NULL CHECK (sentiment_score BETWEEN -1 AND 1),
    emotion_category emotion_category,
    confidence DECIMAL(5,4) CHECK (confidence BETWEEN 0 AND 1),
    emotion_intensity DECIMAL(5,4) CHECK (emotion_intensity BETWEEN 0 AND 1), -- 새로 추가
    analysis_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 커뮤니케이션 패턴 테이블
CREATE TABLE communication_patterns (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES consultation_sessions(id) ON DELETE CASCADE,
    pattern_type pattern_type NOT NULL,
    frequency INTEGER DEFAULT 0 CHECK (frequency >= 0),
    severity_score DECIMAL(5,4) CHECK (severity_score BETWEEN 0 AND 1),
    description TEXT,
    impact_on_quality impact_type,
    time_segments JSONB, -- 패턴 발생 시간대들
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 개선 제안사항 테이블
CREATE TABLE improvement_suggestions (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES consultation_sessions(id) ON DELETE CASCADE,
    suggestion_category suggestion_category NOT NULL,
    suggestion_text TEXT NOT NULL,
    priority priority_level NOT NULL,
    implementation_difficulty difficulty_level,
    expected_impact priority_level,
    target_audience target_audience,
    estimated_effort_hours INTEGER CHECK (estimated_effort_hours > 0), -- 새로 추가
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 상담 키워드 테이블
CREATE TABLE consultation_keywords (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES consultation_sessions(id) ON DELETE CASCADE,
    keyword VARCHAR(100) NOT NULL,
    frequency INTEGER DEFAULT 1 CHECK (frequency > 0),
    importance_score DECIMAL(5,4) CHECK (importance_score BETWEEN 0 AND 1),
    category keyword_category,
    context_snippets JSONB, -- 키워드가 사용된 문맥들
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, keyword) -- 중복 방지
);

-- 상담사 성과 테이블
CREATE TABLE agent_performance (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,
    agent_id VARCHAR(50), -- 새로 추가
    session_id INTEGER NOT NULL REFERENCES consultation_sessions(id) ON DELETE CASCADE,
    performance_score DECIMAL(5,4) CHECK (performance_score BETWEEN 0 AND 1),
    strengths JSONB, -- JSON 배열로 구조화
    areas_for_improvement JSONB, -- JSON 배열로 구조화  
    training_recommendations JSONB, -- JSON 배열로 구조화
    performance_trend VARCHAR(20) CHECK (performance_trend IN ('improving', 'stable', 'declining')), -- 새로 추가
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ========================================================================
-- 4. 📊 분석 이력 및 처리 로그
-- ========================================================================

-- 분석 이력 테이블 (통합)
CREATE TABLE analysis_history (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES consultation_sessions(id) ON DELETE CASCADE,
    audio_file_id INTEGER REFERENCES audio_files(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL,
    status analysis_status NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER GENERATED ALWAYS AS (
        CASE 
            WHEN completed_at IS NOT NULL AND started_at IS NOT NULL 
            THEN EXTRACT(EPOCH FROM (completed_at - started_at))::INTEGER
            ELSE NULL 
        END
    ) STORED,
    error_message TEXT,
    reprocess_count INTEGER DEFAULT 0 CHECK (reprocess_count >= 0),
    triggered_by VARCHAR(20) CHECK (triggered_by IN ('auto', 'manual', 'system', 'scheduler')),
    parameters JSONB,
    result_summary JSONB,
    resource_usage JSONB, -- CPU, 메모리 사용량 등
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_reference CHECK (
        (session_id IS NOT NULL AND audio_file_id IS NULL) OR 
        (session_id IS NULL AND audio_file_id IS NOT NULL)
    )
);

-- 처리 로그 테이블 (상세)
CREATE TABLE processing_logs (
    id SERIAL PRIMARY KEY,
    audio_file_id INTEGER NOT NULL REFERENCES audio_files(id) ON DELETE CASCADE,
    processing_step VARCHAR(100) NOT NULL,
    status processing_status,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    duration_seconds INTEGER GENERATED ALWAYS AS (
        CASE 
            WHEN end_time IS NOT NULL 
            THEN EXTRACT(EPOCH FROM (end_time - start_time))::INTEGER
            ELSE NULL 
        END
    ) STORED,
    error_message TEXT,
    step_order INTEGER, -- 처리 순서
    retry_count INTEGER DEFAULT 0 CHECK (retry_count >= 0),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ========================================================================
-- 5. 🔄 기존 호환성 테이블들 (마이그레이션용)
-- ========================================================================

-- 기존 consultation_analysis 테이블 (호환성)
CREATE TABLE consultation_analysis (
    id SERIAL PRIMARY KEY,
    consultation_id VARCHAR(100) NOT NULL UNIQUE,
    audio_path TEXT NOT NULL,
    business_type VARCHAR(100),
    classification_type VARCHAR(100),
    detail_classification VARCHAR(200),
    consultation_result TEXT,
    summary TEXT,
    customer_request TEXT,
    solution TEXT,
    additional_info JSONB,
    sentiment_score DECIMAL(6,4),
    topic_keywords JSONB,
    quality_score DECIMAL(5,4),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 기존 utterances 테이블 (호환성)
CREATE TABLE utterances (
    id SERIAL PRIMARY KEY,
    consultation_id VARCHAR(100) NOT NULL,
    speaker VARCHAR(20) NOT NULL,
    start_time DECIMAL(10,3) NOT NULL,
    end_time DECIMAL(10,3) NOT NULL,
    text_content TEXT NOT NULL,
    confidence DECIMAL(5,4),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (consultation_id) REFERENCES consultation_analysis(consultation_id) ON DELETE CASCADE
);

-- 기존 topics 테이블 (호환성)
CREATE TABLE topics (
    id SERIAL PRIMARY KEY,
    consultation_id VARCHAR(100) NOT NULL,
    topic VARCHAR(200) NOT NULL,
    confidence DECIMAL(5,4),
    keywords JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (consultation_id) REFERENCES consultation_analysis(consultation_id) ON DELETE CASCADE
);

-- 기존 audio_properties 테이블 (호환성)
CREATE TABLE audio_properties (
    id SERIAL PRIMARY KEY,
    consultation_id VARCHAR(100) NOT NULL,
    file_path TEXT NOT NULL,
    duration DECIMAL(10,3),
    sample_rate INTEGER,
    channels SMALLINT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (consultation_id) REFERENCES consultation_analysis(consultation_id) ON DELETE CASCADE
);

-- ========================================================================
-- 6. 인덱스 생성 (성능 최적화)
-- ========================================================================

-- 기본 인덱스들
CREATE INDEX CONCURRENTLY idx_audio_files_status ON audio_files(processing_status);
CREATE INDEX CONCURRENTLY idx_audio_files_upload_time ON audio_files(upload_timestamp);
CREATE INDEX CONCURRENTLY idx_audio_files_uuid ON audio_files(uuid);

CREATE INDEX CONCURRENTLY idx_speaker_segments_audio_file ON speaker_segments(audio_file_id);
CREATE INDEX CONCURRENTLY idx_speaker_segments_speaker_type ON speaker_segments(speaker_type);
CREATE INDEX CONCURRENTLY idx_speaker_segments_time ON speaker_segments(audio_file_id, start_time, end_time);

CREATE INDEX CONCURRENTLY idx_transcriptions_audio_file ON transcriptions(audio_file_id);
CREATE INDEX CONCURRENTLY idx_transcriptions_segment ON transcriptions(speaker_segment_id);
CREATE INDEX CONCURRENTLY idx_transcriptions_time ON transcriptions(audio_file_id, start_time, end_time);
CREATE INDEX CONCURRENTLY idx_transcriptions_text_gin ON transcriptions USING gin(to_tsvector('korean', text_content));

CREATE INDEX CONCURRENTLY idx_consultation_sessions_audio_file ON consultation_sessions(audio_file_id);
CREATE INDEX CONCURRENTLY idx_consultation_sessions_date ON consultation_sessions(session_date);
CREATE INDEX CONCURRENTLY idx_consultation_sessions_agent ON consultation_sessions(agent_name);
CREATE INDEX CONCURRENTLY idx_consultation_sessions_agent_id ON consultation_sessions(agent_id);
CREATE INDEX CONCURRENTLY idx_consultation_sessions_status ON consultation_sessions(analysis_status);
CREATE INDEX CONCURRENTLY idx_consultation_sessions_uuid ON consultation_sessions(uuid);

CREATE INDEX CONCURRENTLY idx_quality_metrics_session ON quality_metrics(session_id);
CREATE INDEX CONCURRENTLY idx_quality_metrics_category ON quality_metrics(category);
CREATE INDEX CONCURRENTLY idx_quality_metrics_name ON quality_metrics(metric_name);

CREATE INDEX CONCURRENTLY idx_sentiment_analysis_session ON sentiment_analysis(session_id);
CREATE INDEX CONCURRENTLY idx_sentiment_analysis_speaker ON sentiment_analysis(speaker_type);
CREATE INDEX CONCURRENTLY idx_sentiment_analysis_time ON sentiment_analysis(session_id, time_segment_start);

CREATE INDEX CONCURRENTLY idx_analysis_history_session ON analysis_history(session_id);
CREATE INDEX CONCURRENTLY idx_analysis_history_audio ON analysis_history(audio_file_id);
CREATE INDEX CONCURRENTLY idx_analysis_history_type ON analysis_history(analysis_type);
CREATE INDEX CONCURRENTLY idx_analysis_history_status ON analysis_history(status);

-- JSONB 인덱스 (GIN)
CREATE INDEX CONCURRENTLY idx_consultation_sessions_key_issues_gin ON consultation_sessions USING gin(key_issues);
CREATE INDEX CONCURRENTLY idx_communication_patterns_time_gin ON communication_patterns USING gin(time_segments);
CREATE INDEX CONCURRENTLY idx_consultation_keywords_context_gin ON consultation_keywords USING gin(context_snippets);

-- ========================================================================
-- 7. 뷰 생성 (데이터 접근 최적화)
-- ========================================================================

-- 종합 상담 품질 요약 뷰
CREATE VIEW consultation_quality_summary AS
SELECT 
    cs.id,
    cs.uuid,
    cs.session_date,
    cs.duration_minutes,
    cs.agent_name,
    cs.agent_id,
    cs.consultation_type,
    cs.overall_quality_score,
    cs.customer_satisfaction_score,
    cs.resolution_status,
    cs.analysis_status,
    af.file_name,
    af.duration_seconds as audio_duration,
    COUNT(DISTINCT qm.id) as metrics_count,
    COUNT(DISTINCT sa.id) as sentiment_analyses_count,
    COUNT(DISTINCT cp.id) as communication_patterns_count,
    COUNT(DISTINCT is.id) as improvement_suggestions_count,
    AVG(sa.sentiment_score) as avg_sentiment_score,
    COUNT(CASE WHEN is.priority = 'high' THEN 1 END) as high_priority_suggestions,
    am.audio_quality_score,
    am.clarity_score
FROM consultation_sessions cs
LEFT JOIN audio_files af ON cs.audio_file_id = af.id
LEFT JOIN audio_metrics am ON af.id = am.audio_file_id
LEFT JOIN quality_metrics qm ON cs.id = qm.session_id
LEFT JOIN sentiment_analysis sa ON cs.id = sa.session_id
LEFT JOIN communication_patterns cp ON cs.id = cp.session_id
LEFT JOIN improvement_suggestions is ON cs.id = is.session_id
GROUP BY cs.id, af.id, am.id;

-- 상담사 성과 요약 뷰
CREATE VIEW agent_performance_summary AS
SELECT 
    cs.agent_name,
    cs.agent_id,
    COUNT(cs.id) as total_sessions,
    AVG(cs.overall_quality_score) as avg_quality_score,
    AVG(cs.customer_satisfaction_score) as avg_satisfaction_score,
    AVG(cs.duration_minutes) as avg_session_duration,
    COUNT(CASE WHEN cs.resolution_status = 'resolved' THEN 1 END) as resolved_sessions,
    COUNT(CASE WHEN cs.resolution_status = 'unresolved' THEN 1 END) as unresolved_sessions,
    ROUND(
        COUNT(CASE WHEN cs.resolution_status = 'resolved' THEN 1 END)::DECIMAL * 100.0 / 
        NULLIF(COUNT(cs.id), 0), 2
    ) as resolution_rate,
    MIN(cs.session_date) as first_session_date,
    MAX(cs.session_date) as last_session_date,
    AVG(CASE WHEN sa.speaker_type = 'agent' THEN sa.sentiment_score END) as avg_agent_sentiment
FROM consultation_sessions cs
LEFT JOIN sentiment_analysis sa ON cs.id = sa.session_id
WHERE cs.analysis_status = 'completed'
GROUP BY cs.agent_name, cs.agent_id;

-- 오디오 처리 현황 뷰
CREATE VIEW audio_processing_summary AS
SELECT 
    af.id,
    af.uuid,
    af.file_name,
    af.duration_seconds,
    af.processing_status,
    af.upload_timestamp,
    af.processing_completed_at,
    COUNT(DISTINCT ss.id) as speaker_segments_count,
    COUNT(DISTINCT t.id) as transcription_count,
    SUM(t.word_count) as total_word_count,
    am.clarity_score,
    am.audio_quality_score,
    am.snr_db,
    CASE 
        WHEN af.processing_completed_at IS NOT NULL THEN 'completed'
        WHEN af.error_message IS NOT NULL THEN 'failed'
        WHEN af.processing_started_at IS NOT NULL THEN 'processing'
        ELSE 'pending'
    END as overall_status
FROM audio_files af
LEFT JOIN speaker_segments ss ON af.id = ss.audio_file_id
LEFT JOIN transcriptions t ON af.id = t.audio_file_id
LEFT JOIN audio_metrics am ON af.id = am.audio_file_id
GROUP BY af.id, am.id;

-- ========================================================================
-- 8. 트리거 생성 (자동 업데이트)
-- ========================================================================

-- updated_at 자동 업데이트 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거 적용
CREATE TRIGGER update_audio_files_updated_at 
    BEFORE UPDATE ON audio_files 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_consultation_sessions_updated_at 
    BEFORE UPDATE ON consultation_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ========================================================================
-- 9. 권한 및 보안 설정
-- ========================================================================

-- 읽기 전용 역할
CREATE ROLE callytics_readonly;
GRANT USAGE ON SCHEMA public TO callytics_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO callytics_readonly;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO callytics_readonly;

-- 분석가 역할 
CREATE ROLE callytics_analyst;
GRANT USAGE ON SCHEMA public TO callytics_analyst;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO callytics_analyst;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO callytics_analyst;

-- 관리자 역할
CREATE ROLE callytics_admin;
GRANT ALL PRIVILEGES ON SCHEMA public TO callytics_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO callytics_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO callytics_admin;

-- ========================================================================
-- 10. 파티셔닝 설정 (대용량 데이터 대비)
-- ========================================================================

-- consultation_sessions 테이블 파티셔닝 (월별)
-- 나중에 필요시 적용:
-- ALTER TABLE consultation_sessions 
-- PARTITION BY RANGE (session_date);

COMMENT ON SCHEMA public IS 'Callytics 통합 데이터베이스 스키마';
COMMENT ON TABLE audio_files IS '오디오 파일 메타데이터 및 처리 상태';
COMMENT ON TABLE consultation_sessions IS '상담 세션 메인 테이블';
COMMENT ON TABLE sentiment_analysis IS '감정 분석 결과 (시간대별)';
COMMENT ON TABLE quality_metrics IS '품질 평가 지표';
COMMENT ON VIEW consultation_quality_summary IS '상담 품질 종합 요약';
COMMENT ON VIEW agent_performance_summary IS '상담사 성과 요약';