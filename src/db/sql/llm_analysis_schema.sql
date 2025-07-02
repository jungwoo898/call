-- 🤖 Callytics LLM/AI 분석 결과 구조화 스키마
-- 목적: LLM/AI 분석 결과를 JSON 구조로 저장하여 복합적 분석 결과 활용

-- LLM 분석 결과 테이블
CREATE TABLE IF NOT EXISTS llm_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    analysis_type TEXT NOT NULL CHECK(analysis_type IN ('summary', 'quality_assessment', 'sentiment_timeline', 'improvement_recommendations', 'communication_analysis', 'issue_detection', 'comprehensive_report')),
    result_json TEXT NOT NULL, -- JSON 구조화된 분석 결과
    model_version TEXT, -- 사용된 LLM 모델 버전
    analysis_parameters TEXT, -- 분석 파라미터 (JSON)
    confidence_score REAL CHECK(confidence_score >= 0 AND confidence_score <= 1),
    processing_time_seconds REAL, -- 분석 소요 시간
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES consultation_sessions(id) ON DELETE CASCADE
);

-- LLM 분석 결과 타입별 상세 테이블들
CREATE TABLE IF NOT EXISTS llm_summary_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    llm_analysis_id INTEGER NOT NULL,
    overall_summary TEXT NOT NULL, -- 전체 요약
    key_points TEXT, -- 핵심 포인트 (JSON 배열)
    customer_concerns TEXT, -- 고객 우려사항 (JSON 배열)
    agent_actions TEXT, -- 상담사 행동 (JSON 배열)
    resolution_status TEXT CHECK(resolution_status IN ('resolved', 'partially_resolved', 'unresolved', 'escalated')),
    satisfaction_indicators TEXT, -- 만족도 지표 (JSON)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (llm_analysis_id) REFERENCES llm_analysis(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS llm_issue_detection (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    llm_analysis_id INTEGER NOT NULL,
    issue_type TEXT NOT NULL CHECK(issue_type IN ('technical', 'communication', 'process', 'attitude', 'knowledge', 'system')),
    issue_description TEXT NOT NULL,
    severity_level TEXT CHECK(severity_level IN ('critical', 'high', 'medium', 'low')),
    occurrence_time REAL, -- 발생 시점 (초)
    impact_description TEXT, -- 영향 설명
    suggested_solution TEXT, -- 제안 해결책
    priority_score REAL CHECK(priority_score >= 0 AND priority_score <= 1),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (llm_analysis_id) REFERENCES llm_analysis(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS llm_sentiment_timeline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    llm_analysis_id INTEGER NOT NULL,
    speaker_type TEXT NOT NULL CHECK(speaker_type IN ('customer', 'agent')),
    time_segment_start REAL NOT NULL, -- 시간 구간 시작 (초)
    time_segment_end REAL NOT NULL, -- 시간 구간 끝 (초)
    dominant_emotion TEXT, -- 주요 감정
    emotion_intensity REAL CHECK(emotion_intensity >= 0 AND emotion_intensity <= 1),
    sentiment_score REAL CHECK(sentiment_score >= -1 AND sentiment_score <= 1),
    emotion_triggers TEXT, -- 감정 변화 원인 (JSON 배열)
    communication_quality REAL CHECK(communication_quality >= 0 AND communication_quality <= 1),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (llm_analysis_id) REFERENCES llm_analysis(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS llm_improvement_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    llm_analysis_id INTEGER NOT NULL,
    recommendation_category TEXT NOT NULL CHECK(recommendation_category IN ('immediate', 'short_term', 'long_term', 'training', 'process', 'system')),
    recommendation_text TEXT NOT NULL,
    rationale TEXT, -- 추천 이유
    expected_impact TEXT CHECK(expected_impact IN ('high', 'medium', 'low')),
    implementation_difficulty TEXT CHECK(implementation_difficulty IN ('easy', 'medium', 'hard')),
    target_audience TEXT CHECK(target_audience IN ('agent', 'supervisor', 'system', 'process')),
    priority_level TEXT CHECK(priority_level IN ('critical', 'high', 'medium', 'low')),
    cost_estimate TEXT, -- 비용 추정
    timeline_estimate TEXT, -- 시간 추정
    success_metrics TEXT, -- 성공 지표 (JSON)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (llm_analysis_id) REFERENCES llm_analysis(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS llm_communication_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    llm_analysis_id INTEGER NOT NULL,
    communication_style TEXT, -- 커뮤니케이션 스타일
    empathy_level REAL CHECK(empathy_level >= 0 AND empathy_level <= 1),
    professionalism_score REAL CHECK(professionalism_score >= 0 AND professionalism_score <= 1),
    clarity_score REAL CHECK(clarity_score >= 0 AND clarity_score <= 1),
    responsiveness_score REAL CHECK(responsiveness_score >= 0 AND responsiveness_score <= 1),
    active_listening_score REAL CHECK(active_listening_score >= 0 AND active_listening_score <= 1),
    problem_solving_approach TEXT, -- 문제 해결 접근법
    customer_engagement_level REAL CHECK(customer_engagement_level >= 0 AND customer_engagement_level <= 1),
    communication_breakdowns TEXT, -- 커뮤니케이션 문제점 (JSON 배열)
    strengths_identified TEXT, -- 강점 (JSON 배열)
    areas_for_improvement TEXT, -- 개선 영역 (JSON 배열)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (llm_analysis_id) REFERENCES llm_analysis(id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_llm_analysis_session ON llm_analysis(session_id);
CREATE INDEX IF NOT EXISTS idx_llm_analysis_type ON llm_analysis(analysis_type);
CREATE INDEX IF NOT EXISTS idx_llm_analysis_created ON llm_analysis(created_at);
CREATE INDEX IF NOT EXISTS idx_llm_issue_detection_type ON llm_issue_detection(issue_type);
CREATE INDEX IF NOT EXISTS idx_llm_issue_detection_severity ON llm_issue_detection(severity_level);
CREATE INDEX IF NOT EXISTS idx_llm_sentiment_timeline_speaker ON llm_sentiment_timeline(speaker_type);
CREATE INDEX IF NOT EXISTS idx_llm_sentiment_timeline_time ON llm_sentiment_timeline(time_segment_start, time_segment_end);
CREATE INDEX IF NOT EXISTS idx_llm_improvement_category ON llm_improvement_recommendations(recommendation_category);
CREATE INDEX IF NOT EXISTS idx_llm_improvement_priority ON llm_improvement_recommendations(priority_level);

-- 뷰 생성
CREATE VIEW IF NOT EXISTS llm_analysis_summary AS
SELECT 
    la.id,
    la.session_id,
    la.analysis_type,
    la.confidence_score,
    la.processing_time_seconds,
    la.created_at,
    lsa.overall_summary,
    lsa.resolution_status,
    COUNT(lid.id) as issues_count,
    COUNT(lst.id) as sentiment_segments_count,
    COUNT(lir.id) as recommendations_count,
    lca.empathy_level,
    lca.professionalism_score,
    lca.clarity_score
FROM llm_analysis la
LEFT JOIN llm_summary_analysis lsa ON la.id = lsa.llm_analysis_id
LEFT JOIN llm_issue_detection lid ON la.id = lid.llm_analysis_id
LEFT JOIN llm_sentiment_timeline lst ON la.id = lst.llm_analysis_id
LEFT JOIN llm_communication_analysis lca ON la.id = lca.llm_analysis_id
GROUP BY la.id;

-- 트리거 생성 (updated_at 자동 업데이트)
CREATE TRIGGER IF NOT EXISTS update_llm_analysis_timestamp 
    AFTER UPDATE ON llm_analysis
    FOR EACH ROW
BEGIN
    UPDATE llm_analysis SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END; 