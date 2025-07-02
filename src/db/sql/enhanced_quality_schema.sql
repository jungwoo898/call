-- 🎯 Callytics 향상된 품질 분석 스키마
-- 목적: 품질지표 세분화, 감정 타임라인, 상세 분석 지원

-- 기존 quality_metrics 테이블에 metric_group 필드 추가
ALTER TABLE quality_metrics ADD COLUMN metric_group TEXT CHECK(metric_group IN ('audio', 'communication', 'ai_analysis', 'business', 'technical'));

-- 감정 변화 타임라인 테이블 (기존 sentiment_analysis와 별도)
CREATE TABLE IF NOT EXISTS sentiment_timeline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    speaker_type TEXT NOT NULL CHECK(speaker_type IN ('customer', 'agent')),
    time_start REAL NOT NULL, -- 시작 시간 (초)
    time_end REAL NOT NULL, -- 끝 시간 (초)
    dominant_emotion TEXT NOT NULL CHECK(dominant_emotion IN ('happy', 'satisfied', 'neutral', 'frustrated', 'angry', 'anxious', 'confused', 'surprised', 'disappointed')),
    emotion_intensity REAL CHECK(emotion_intensity >= 0 AND emotion_intensity <= 1),
    sentiment_score REAL CHECK(sentiment_score >= -1 AND sentiment_score <= 1),
    confidence REAL CHECK(confidence >= 0 AND confidence <= 1),
    emotion_triggers TEXT, -- 감정 변화 원인 (JSON 배열)
    context_description TEXT, -- 해당 구간의 상황 설명
    communication_quality REAL CHECK(communication_quality >= 0 AND communication_quality <= 1),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES consultation_sessions(id) ON DELETE CASCADE
);

-- 상담 품질 세부 지표 테이블
CREATE TABLE IF NOT EXISTS detailed_quality_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    metric_category TEXT NOT NULL CHECK(metric_category IN ('communication', 'technical', 'process', 'attitude', 'resolution', 'customer_experience')),
    metric_subcategory TEXT, -- 세부 카테고리
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metric_unit TEXT, -- 단위 (%, score, count, seconds 등)
    metric_description TEXT,
    measurement_method TEXT, -- 측정 방법
    weight REAL DEFAULT 1.0 CHECK(weight >= 0 AND weight <= 1),
    threshold_min REAL, -- 최소 임계값
    threshold_max REAL, -- 최대 임계값
    is_critical BOOLEAN DEFAULT FALSE, -- 중요 지표 여부
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES consultation_sessions(id) ON DELETE CASCADE
);

-- 상담 패턴 분석 테이블 (기존 communication_patterns 확장)
CREATE TABLE IF NOT EXISTS communication_pattern_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    pattern_type TEXT NOT NULL CHECK(pattern_type IN ('interruption', 'long_silence', 'rapid_speech', 'repetition', 'clarification_request', 'empathy_expression', 'solution_proposal', 'active_listening', 'question_technique', 'closing_technique')),
    pattern_subtype TEXT, -- 패턴 세부 유형
    occurrence_count INTEGER DEFAULT 0,
    total_duration REAL, -- 총 지속 시간 (초)
    average_duration REAL, -- 평균 지속 시간 (초)
    severity_score REAL CHECK(severity_score >= 0 AND severity_score <= 1),
    impact_on_quality TEXT CHECK(impact_on_quality IN ('positive', 'negative', 'neutral')),
    effectiveness_score REAL CHECK(effectiveness_score >= 0 AND effectiveness_score <= 1),
    context_description TEXT, -- 패턴 발생 상황 설명
    improvement_suggestion TEXT, -- 개선 제안
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES consultation_sessions(id) ON DELETE CASCADE
);

-- 상담 단계별 분석 테이블
CREATE TABLE IF NOT EXISTS consultation_phase_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    phase_name TEXT NOT NULL CHECK(phase_name IN ('greeting', 'problem_identification', 'information_gathering', 'solution_proposal', 'objection_handling', 'resolution', 'closing')),
    phase_start_time REAL NOT NULL, -- 단계 시작 시간 (초)
    phase_end_time REAL NOT NULL, -- 단계 끝 시간 (초)
    phase_duration REAL, -- 단계 지속 시간 (초)
    phase_quality_score REAL CHECK(phase_quality_score >= 0 AND phase_quality_score <= 1),
    phase_effectiveness_score REAL CHECK(phase_effectiveness_score >= 0 AND phase_effectiveness_score <= 1),
    key_activities TEXT, -- 주요 활동 (JSON 배열)
    challenges_encountered TEXT, -- 직면한 어려움 (JSON 배열)
    strengths_demonstrated TEXT, -- 보여준 강점 (JSON 배열)
    areas_for_improvement TEXT, -- 개선 영역 (JSON 배열)
    customer_satisfaction_phase REAL CHECK(customer_satisfaction_phase >= 0 AND customer_satisfaction_phase <= 1),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES consultation_sessions(id) ON DELETE CASCADE
);

-- 상담사 행동 분석 테이블
CREATE TABLE IF NOT EXISTS agent_behavior_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    behavior_type TEXT NOT NULL CHECK(behavior_type IN ('listening', 'questioning', 'explaining', 'problem_solving', 'empathy', 'professionalism', 'efficiency', 'adaptability')),
    behavior_score REAL CHECK(behavior_score >= 0 AND behavior_score <= 1),
    behavior_frequency INTEGER DEFAULT 0,
    behavior_duration REAL, -- 행동 지속 시간 (초)
    behavior_effectiveness REAL CHECK(behavior_effectiveness >= 0 AND behavior_effectiveness <= 1),
    behavior_context TEXT, -- 행동 발생 상황
    customer_response TEXT, -- 고객 반응
    improvement_opportunity TEXT, -- 개선 기회
    best_practice_demonstrated BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES consultation_sessions(id) ON DELETE CASCADE
);

-- 고객 반응 분석 테이블
CREATE TABLE IF NOT EXISTS customer_response_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    response_type TEXT NOT NULL CHECK(response_type IN ('positive', 'negative', 'neutral', 'confused', 'satisfied', 'frustrated', 'appreciative', 'dismissive')),
    response_intensity REAL CHECK(response_intensity >= 0 AND response_intensity <= 1),
    response_duration REAL, -- 반응 지속 시간 (초)
    trigger_action TEXT, -- 반응을 유발한 행동
    response_impact TEXT CHECK(response_impact IN ('constructive', 'destructive', 'neutral')),
    follow_up_required BOOLEAN DEFAULT FALSE,
    escalation_risk REAL CHECK(escalation_risk >= 0 AND escalation_risk <= 1),
    response_description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES consultation_sessions(id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_sentiment_timeline_session ON sentiment_timeline(session_id);
CREATE INDEX IF NOT EXISTS idx_sentiment_timeline_speaker ON sentiment_timeline(speaker_type);
CREATE INDEX IF NOT EXISTS idx_sentiment_timeline_time ON sentiment_timeline(time_start, time_end);
CREATE INDEX IF NOT EXISTS idx_sentiment_timeline_emotion ON sentiment_timeline(dominant_emotion);
CREATE INDEX IF NOT EXISTS idx_detailed_quality_metrics_session ON detailed_quality_metrics(session_id);
CREATE INDEX IF NOT EXISTS idx_detailed_quality_metrics_category ON detailed_quality_metrics(metric_category);
CREATE INDEX IF NOT EXISTS idx_detailed_quality_metrics_critical ON detailed_quality_metrics(is_critical);
CREATE INDEX IF NOT EXISTS idx_communication_pattern_session ON communication_pattern_analysis(session_id);
CREATE INDEX IF NOT EXISTS idx_communication_pattern_type ON communication_pattern_analysis(pattern_type);
CREATE INDEX IF NOT EXISTS idx_consultation_phase_session ON consultation_phase_analysis(session_id);
CREATE INDEX IF NOT EXISTS idx_consultation_phase_name ON consultation_phase_analysis(phase_name);
CREATE INDEX IF NOT EXISTS idx_agent_behavior_session ON agent_behavior_analysis(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_behavior_type ON agent_behavior_analysis(behavior_type);
CREATE INDEX IF NOT EXISTS idx_customer_response_session ON customer_response_analysis(session_id);
CREATE INDEX IF NOT EXISTS idx_customer_response_type ON customer_response_analysis(response_type);

-- 뷰 생성
CREATE VIEW IF NOT EXISTS enhanced_quality_summary AS
SELECT 
    cs.id as session_id,
    cs.agent_name,
    cs.consultation_type,
    cs.overall_quality_score,
    cs.duration_minutes,
    -- 감정 타임라인 통계
    COUNT(DISTINCT st.id) as sentiment_segments_count,
    AVG(st.sentiment_score) as avg_sentiment_score,
    COUNT(CASE WHEN st.dominant_emotion = 'angry' THEN 1 END) as angry_segments,
    COUNT(CASE WHEN st.dominant_emotion = 'satisfied' THEN 1 END) as satisfied_segments,
    -- 상세 품질 지표 통계
    COUNT(dqm.id) as detailed_metrics_count,
    AVG(dqm.metric_value) as avg_metric_value,
    COUNT(CASE WHEN dqm.is_critical = 1 THEN 1 END) as critical_metrics_count,
    -- 커뮤니케이션 패턴 통계
    COUNT(cpa.id) as communication_patterns_count,
    AVG(cpa.effectiveness_score) as avg_pattern_effectiveness,
    -- 상담 단계 통계
    COUNT(cpha.id) as consultation_phases_count,
    AVG(cpha.phase_quality_score) as avg_phase_quality,
    -- 상담사 행동 통계
    COUNT(aba.id) as agent_behaviors_count,
    AVG(aba.behavior_effectiveness) as avg_behavior_effectiveness,
    -- 고객 반응 통계
    COUNT(cra.id) as customer_responses_count,
    AVG(cra.response_intensity) as avg_response_intensity,
    COUNT(CASE WHEN cra.escalation_risk > 0.7 THEN 1 END) as high_escalation_risk_count
FROM consultation_sessions cs
LEFT JOIN sentiment_timeline st ON cs.id = st.session_id
LEFT JOIN detailed_quality_metrics dqm ON cs.id = dqm.session_id
LEFT JOIN communication_pattern_analysis cpa ON cs.id = cpa.session_id
LEFT JOIN consultation_phase_analysis cpha ON cs.id = cpha.session_id
LEFT JOIN agent_behavior_analysis aba ON cs.id = aba.session_id
LEFT JOIN customer_response_analysis cra ON cs.id = cra.session_id
GROUP BY cs.id;

-- 감정 변화 트렌드 뷰
CREATE VIEW IF NOT EXISTS sentiment_trend_analysis AS
SELECT 
    session_id,
    speaker_type,
    time_start,
    time_end,
    dominant_emotion,
    sentiment_score,
    emotion_intensity,
    LAG(sentiment_score) OVER (PARTITION BY session_id, speaker_type ORDER BY time_start) as previous_sentiment,
    sentiment_score - LAG(sentiment_score) OVER (PARTITION BY session_id, speaker_type ORDER BY time_start) as sentiment_change,
    CASE 
        WHEN sentiment_score - LAG(sentiment_score) OVER (PARTITION BY session_id, speaker_type ORDER BY time_start) > 0.2 THEN 'improved'
        WHEN sentiment_score - LAG(sentiment_score) OVER (PARTITION BY session_id, speaker_type ORDER BY time_start) < -0.2 THEN 'worsened'
        ELSE 'stable'
    END as sentiment_trend
FROM sentiment_timeline
ORDER BY session_id, speaker_type, time_start; 