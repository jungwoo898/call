-- 🧠 Callytics 상담 품질 분석 데이터베이스 스키마
-- 목적: LLM 기반 상담 내용 분석 및 품질 평가 결과 저장

-- 상담 세션 테이블
CREATE TABLE IF NOT EXISTS consultation_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audio_file_id INTEGER NOT NULL,
    session_date DATE NOT NULL,
    duration_minutes REAL NOT NULL,
    agent_name TEXT,
    customer_id TEXT,
    consultation_type TEXT CHECK(consultation_type IN ('inquiry', 'complaint', 'support', 'sales', 'technical', 'billing', 'other')),
    overall_quality_score REAL CHECK(overall_quality_score >= 0 AND overall_quality_score <= 1),
    analysis_status TEXT DEFAULT 'pending' CHECK(analysis_status IN ('pending', 'processing', 'completed', 'failed', 'reprocessing')),
    analysis_started_at DATETIME,
    analysis_completed_at DATETIME,
    analysis_error_message TEXT,
    summary TEXT,
    key_issues TEXT,
    resolution_status TEXT CHECK(resolution_status IN ('resolved', 'partially_resolved', 'unresolved', 'escalated')),
    customer_satisfaction_score REAL CHECK(customer_satisfaction_score >= 0 AND customer_satisfaction_score <= 1),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 품질 평가 지표 테이블
CREATE TABLE IF NOT EXISTS quality_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metric_description TEXT,
    weight REAL DEFAULT 1.0 CHECK(weight >= 0 AND weight <= 1),
    category TEXT CHECK(category IN ('communication', 'technical', 'process', 'attitude', 'resolution')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES consultation_sessions(id) ON DELETE CASCADE
);

-- 감정 분석 결과 테이블
CREATE TABLE IF NOT EXISTS sentiment_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    speaker_type TEXT NOT NULL CHECK(speaker_type IN ('customer', 'agent')),
    sentiment_score REAL NOT NULL CHECK(sentiment_score >= -1 AND sentiment_score <= 1),
    emotion_category TEXT CHECK(emotion_category IN ('happy', 'satisfied', 'neutral', 'frustrated', 'angry', 'anxious', 'confused')),
    confidence REAL CHECK(confidence >= 0 AND confidence <= 1),
    analysis_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES consultation_sessions(id) ON DELETE CASCADE
);

-- 커뮤니케이션 패턴 테이블
CREATE TABLE IF NOT EXISTS communication_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    pattern_type TEXT NOT NULL CHECK(pattern_type IN ('interruption', 'long_silence', 'rapid_speech', 'repetition', 'clarification_request', 'empathy_expression', 'solution_proposal')),
    frequency INTEGER DEFAULT 0,
    severity_score REAL CHECK(severity_score >= 0 AND severity_score <= 1),
    description TEXT,
    impact_on_quality TEXT CHECK(impact_on_quality IN ('positive', 'negative', 'neutral')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES consultation_sessions(id) ON DELETE CASCADE
);

-- 개선 제안사항 테이블
CREATE TABLE IF NOT EXISTS improvement_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    suggestion_category TEXT NOT NULL CHECK(suggestion_category IN ('communication', 'technical', 'process', 'attitude', 'knowledge', 'system')),
    suggestion_text TEXT NOT NULL,
    priority TEXT NOT NULL CHECK(priority IN ('high', 'medium', 'low')),
    implementation_difficulty TEXT CHECK(implementation_difficulty IN ('easy', 'medium', 'hard')),
    expected_impact TEXT CHECK(expected_impact IN ('high', 'medium', 'low')),
    target_audience TEXT CHECK(target_audience IN ('agent', 'supervisor', 'system', 'process')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES consultation_sessions(id) ON DELETE CASCADE
);

-- 상담 키워드 테이블
CREATE TABLE IF NOT EXISTS consultation_keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    keyword TEXT NOT NULL,
    frequency INTEGER DEFAULT 1,
    importance_score REAL CHECK(importance_score >= 0 AND importance_score <= 1),
    category TEXT CHECK(category IN ('product', 'service', 'issue', 'emotion', 'action', 'technical')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES consultation_sessions(id) ON DELETE CASCADE
);

-- 상담사 성과 테이블
CREATE TABLE IF NOT EXISTS agent_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    session_id INTEGER NOT NULL,
    performance_score REAL CHECK(performance_score >= 0 AND performance_score <= 1),
    strengths TEXT,
    areas_for_improvement TEXT,
    training_recommendations TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES consultation_sessions(id) ON DELETE CASCADE
);

-- 분석 이력 및 상태 관리 테이블 (상담 품질 DB)
CREATE TABLE IF NOT EXISTS analysis_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    analysis_type TEXT NOT NULL, -- 예: 'diarization', 'llm', 'quality', ...
    status TEXT NOT NULL CHECK(status IN ('pending', 'processing', 'completed', 'failed', 'reprocessing')),
    started_at DATETIME,
    completed_at DATETIME,
    error_message TEXT,
    reprocess_count INTEGER DEFAULT 0,
    triggered_by TEXT, -- 'auto', 'manual', 'system'
    parameters TEXT, -- JSON
    result_summary TEXT, -- 요약(성공시)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES consultation_sessions(id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_consultation_sessions_audio_file ON consultation_sessions(audio_file_id);
CREATE INDEX IF NOT EXISTS idx_consultation_sessions_date ON consultation_sessions(session_date);
CREATE INDEX IF NOT EXISTS idx_consultation_sessions_agent ON consultation_sessions(agent_name);
CREATE INDEX IF NOT EXISTS idx_consultation_sessions_type ON consultation_sessions(consultation_type);
CREATE INDEX IF NOT EXISTS idx_consultation_sessions_status ON consultation_sessions(analysis_status);
CREATE INDEX IF NOT EXISTS idx_quality_metrics_session ON quality_metrics(session_id);
CREATE INDEX IF NOT EXISTS idx_quality_metrics_category ON quality_metrics(category);
CREATE INDEX IF NOT EXISTS idx_sentiment_analysis_session ON sentiment_analysis(session_id);
CREATE INDEX IF NOT EXISTS idx_sentiment_analysis_speaker ON sentiment_analysis(speaker_type);
CREATE INDEX IF NOT EXISTS idx_communication_patterns_session ON communication_patterns(session_id);
CREATE INDEX IF NOT EXISTS idx_communication_patterns_type ON communication_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_improvement_suggestions_session ON improvement_suggestions(session_id);
CREATE INDEX IF NOT EXISTS idx_improvement_suggestions_priority ON improvement_suggestions(priority);
CREATE INDEX IF NOT EXISTS idx_analysis_history_session ON analysis_history(session_id);
CREATE INDEX IF NOT EXISTS idx_analysis_history_type ON analysis_history(analysis_type);
CREATE INDEX IF NOT EXISTS idx_analysis_history_status ON analysis_history(status);

-- 뷰 생성
CREATE VIEW IF NOT EXISTS consultation_quality_summary AS
SELECT 
    cs.id,
    cs.session_date,
    cs.duration_minutes,
    cs.agent_name,
    cs.consultation_type,
    cs.overall_quality_score,
    cs.customer_satisfaction_score,
    cs.resolution_status,
    COUNT(qm.id) as metrics_count,
    COUNT(sa.id) as sentiment_analyses_count,
    COUNT(cp.id) as communication_patterns_count,
    COUNT(is.id) as improvement_suggestions_count,
    AVG(sa.sentiment_score) as avg_sentiment_score,
    COUNT(CASE WHEN is.priority = 'high' THEN 1 END) as high_priority_suggestions
FROM consultation_sessions cs
LEFT JOIN quality_metrics qm ON cs.id = qm.session_id
LEFT JOIN sentiment_analysis sa ON cs.id = sa.session_id
LEFT JOIN communication_patterns cp ON cs.id = cp.session_id
LEFT JOIN improvement_suggestions is ON cs.id = is.session_id
GROUP BY cs.id;

-- 상담사 성과 뷰
CREATE VIEW IF NOT EXISTS agent_performance_summary AS
SELECT 
    cs.agent_name,
    COUNT(cs.id) as total_sessions,
    AVG(cs.overall_quality_score) as avg_quality_score,
    AVG(cs.customer_satisfaction_score) as avg_satisfaction_score,
    AVG(cs.duration_minutes) as avg_session_duration,
    COUNT(CASE WHEN cs.resolution_status = 'resolved' THEN 1 END) as resolved_sessions,
    COUNT(CASE WHEN cs.resolution_status = 'unresolved' THEN 1 END) as unresolved_sessions,
    ROUND(COUNT(CASE WHEN cs.resolution_status = 'resolved' THEN 1 END) * 100.0 / COUNT(cs.id), 2) as resolution_rate
FROM consultation_sessions cs
WHERE cs.analysis_status = 'completed'
GROUP BY cs.agent_name;

-- 트리거 생성 (updated_at 자동 업데이트)
CREATE TRIGGER IF NOT EXISTS update_consultation_sessions_timestamp 
    AFTER UPDATE ON consultation_sessions
    FOR EACH ROW
BEGIN
    UPDATE consultation_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- 🔄 구 버전 호환성을 위한 추가 테이블들

-- 상담 분석 결과 테이블 (구 버전 호환성)
CREATE TABLE IF NOT EXISTS consultation_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consultation_id TEXT NOT NULL UNIQUE,
    audio_path TEXT NOT NULL,
    business_type TEXT,
    classification_type TEXT,
    detail_classification TEXT,
    consultation_result TEXT,
    summary TEXT,
    customer_request TEXT,
    solution TEXT,
    additional_info TEXT,
    confidence REAL DEFAULT 0.0,
    processing_time REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 커뮤니케이션 품질 테이블 (구 버전 호환성)
CREATE TABLE IF NOT EXISTS communication_quality (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audio_path TEXT NOT NULL,
    consultation_id TEXT NOT NULL,
    honorific_ratio REAL DEFAULT 0.0,
    positive_word_ratio REAL DEFAULT 0.0,
    negative_word_ratio REAL DEFAULT 0.0,
    euphonious_word_ratio REAL DEFAULT 0.0,
    empathy_ratio REAL DEFAULT 0.0,
    apology_ratio REAL DEFAULT 0.0,
    total_sentences INTEGER DEFAULT 0,
    customer_sentiment_early REAL DEFAULT 0.0,
    customer_sentiment_late REAL DEFAULT 0.0,
    customer_sentiment_trend REAL DEFAULT 0.0,
    avg_response_latency REAL DEFAULT 0.0,
    task_ratio REAL DEFAULT 0.0,
    suggestions INTEGER DEFAULT 0,
    interruption_count INTEGER DEFAULT 0,
    analysis_details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 발화 내용 테이블 (구 버전 호환성)
CREATE TABLE IF NOT EXISTS utterances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audio_path TEXT NOT NULL,
    speaker TEXT,
    start_time REAL,
    end_time REAL,
    text TEXT,
    confidence REAL DEFAULT 0.0,
    sequence INTEGER,
    sentiment TEXT DEFAULT '중립',
    profane INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 추가 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_consultation_analysis_id ON consultation_analysis(consultation_id);
CREATE INDEX IF NOT EXISTS idx_consultation_analysis_path ON consultation_analysis(audio_path);
CREATE INDEX IF NOT EXISTS idx_communication_quality_path ON communication_quality(audio_path);
CREATE INDEX IF NOT EXISTS idx_communication_quality_id ON communication_quality(consultation_id);
CREATE INDEX IF NOT EXISTS idx_utterances_path ON utterances(audio_path);
CREATE INDEX IF NOT EXISTS idx_utterances_speaker ON utterances(speaker); 