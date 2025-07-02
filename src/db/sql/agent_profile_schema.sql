-- 👤 Callytics 상담사 프로필 및 로그인 시스템 스키마
-- 목적: 상담사 로그인, 프로필 관리, 분석 이력 추적

-- 상담사 계정 테이블
CREATE TABLE IF NOT EXISTS agent_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE, -- 로그인 아이디
    email TEXT UNIQUE, -- 이메일
    password_hash TEXT NOT NULL, -- 암호화된 비밀번호
    account_status TEXT DEFAULT 'active' CHECK(account_status IN ('active', 'inactive', 'suspended', 'pending')),
    last_login_at DATETIME,
    login_attempts INTEGER DEFAULT 0, -- 로그인 시도 횟수
    account_locked_until DATETIME, -- 계정 잠금 해제 시간
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 상담사 프로필 테이블
CREATE TABLE IF NOT EXISTS agent_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL UNIQUE,
    employee_id TEXT UNIQUE, -- 사원번호
    full_name TEXT NOT NULL, -- 전체 이름
    first_name TEXT NOT NULL, -- 이름
    last_name TEXT NOT NULL, -- 성
    department TEXT NOT NULL, -- 부서
    position TEXT NOT NULL, -- 직급
    team TEXT, -- 팀
    supervisor_id INTEGER, -- 상사 ID
    hire_date DATE, -- 입사일
    experience_years INTEGER, -- 경력 연수
    specialization TEXT, -- 전문 분야
    contact_number TEXT, -- 연락처
    profile_image_path TEXT, -- 프로필 이미지 경로
    bio TEXT, -- 자기소개
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES agent_accounts(id) ON DELETE CASCADE,
    FOREIGN KEY (supervisor_id) REFERENCES agent_profiles(id)
);

-- 상담사 권한 테이블
CREATE TABLE IF NOT EXISTS agent_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER NOT NULL,
    permission_type TEXT NOT NULL CHECK(permission_type IN ('audio_upload', 'analysis_view', 'report_generation', 'admin', 'supervisor', 'trainer')),
    permission_level TEXT CHECK(permission_level IN ('read', 'write', 'admin')),
    granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    granted_by INTEGER, -- 권한 부여자
    expires_at DATETIME, -- 권한 만료일
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (agent_id) REFERENCES agent_profiles(id) ON DELETE CASCADE,
    FOREIGN KEY (granted_by) REFERENCES agent_profiles(id)
);

-- 상담사 성과 이력 테이블
CREATE TABLE IF NOT EXISTS agent_performance_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER NOT NULL,
    session_id INTEGER NOT NULL,
    performance_score REAL CHECK(performance_score >= 0 AND performance_score <= 1),
    quality_score REAL CHECK(quality_score >= 0 AND quality_score <= 1),
    customer_satisfaction_score REAL CHECK(customer_satisfaction_score >= 0 AND customer_satisfaction_score <= 1),
    resolution_rate REAL CHECK(resolution_rate >= 0 AND resolution_rate <= 1),
    average_handling_time REAL, -- 평균 처리 시간 (분)
    session_count INTEGER DEFAULT 1, -- 해당 기간 세션 수
    strengths_identified TEXT, -- 확인된 강점 (JSON 배열)
    areas_for_improvement TEXT, -- 개선 영역 (JSON 배열)
    training_recommendations TEXT, -- 교육 추천사항 (JSON 배열)
    evaluation_date DATE NOT NULL, -- 평가 날짜
    evaluator_id INTEGER, -- 평가자 ID
    evaluation_notes TEXT, -- 평가 노트
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agent_profiles(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES consultation_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (evaluator_id) REFERENCES agent_profiles(id)
);

-- 상담사 교육 이력 테이블
CREATE TABLE IF NOT EXISTS agent_training_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER NOT NULL,
    training_type TEXT NOT NULL CHECK(training_type IN ('communication', 'technical', 'product_knowledge', 'customer_service', 'soft_skills', 'compliance')),
    training_name TEXT NOT NULL,
    training_provider TEXT, -- 교육 제공자
    training_date DATE NOT NULL,
    training_duration_hours REAL, -- 교육 시간
    completion_status TEXT CHECK(completion_status IN ('completed', 'in_progress', 'not_started', 'failed')),
    score REAL CHECK(score >= 0 AND score <= 100), -- 교육 점수
    certificate_path TEXT, -- 자격증 경로
    training_notes TEXT, -- 교육 노트
    impact_on_performance TEXT, -- 성과에 미친 영향
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agent_profiles(id) ON DELETE CASCADE
);

-- 상담사 활동 로그 테이블
CREATE TABLE IF NOT EXISTS agent_activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER NOT NULL,
    activity_type TEXT NOT NULL CHECK(activity_type IN ('login', 'logout', 'audio_upload', 'analysis_view', 'report_generation', 'profile_update', 'training_completion')),
    activity_description TEXT,
    ip_address TEXT, -- IP 주소
    user_agent TEXT, -- 브라우저 정보
    session_id TEXT, -- 웹 세션 ID
    activity_data TEXT, -- 활동 데이터 (JSON)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agent_profiles(id) ON DELETE CASCADE
);

-- 상담사 설정 테이블
CREATE TABLE IF NOT EXISTS agent_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER NOT NULL UNIQUE,
    language_preference TEXT DEFAULT 'ko', -- 언어 설정
    timezone TEXT DEFAULT 'Asia/Seoul', -- 시간대 설정
    notification_preferences TEXT, -- 알림 설정 (JSON)
    dashboard_preferences TEXT, -- 대시보드 설정 (JSON)
    analysis_preferences TEXT, -- 분석 설정 (JSON)
    privacy_settings TEXT, -- 개인정보 설정 (JSON)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agent_profiles(id) ON DELETE CASCADE
);

-- 상담사 팀 관리 테이블
CREATE TABLE IF NOT EXISTS agent_teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_name TEXT NOT NULL UNIQUE,
    department TEXT NOT NULL,
    team_leader_id INTEGER, -- 팀장 ID
    team_description TEXT,
    team_size INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_leader_id) REFERENCES agent_profiles(id)
);

-- 상담사-팀 연결 테이블
CREATE TABLE IF NOT EXISTS agent_team_memberships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    role_in_team TEXT CHECK(role_in_team IN ('member', 'leader', 'mentor', 'trainee')),
    joined_date DATE DEFAULT CURRENT_DATE,
    left_date DATE, -- 팀 탈퇴일
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agent_profiles(id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES agent_teams(id) ON DELETE CASCADE,
    UNIQUE(agent_id, team_id)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_agent_accounts_username ON agent_accounts(username);
CREATE INDEX IF NOT EXISTS idx_agent_accounts_email ON agent_accounts(email);
CREATE INDEX IF NOT EXISTS idx_agent_accounts_status ON agent_accounts(account_status);
CREATE INDEX IF NOT EXISTS idx_agent_profiles_employee_id ON agent_profiles(employee_id);
CREATE INDEX IF NOT EXISTS idx_agent_profiles_department ON agent_profiles(department);
CREATE INDEX IF NOT EXISTS idx_agent_profiles_position ON agent_profiles(position);
CREATE INDEX IF NOT EXISTS idx_agent_profiles_supervisor ON agent_profiles(supervisor_id);
CREATE INDEX IF NOT EXISTS idx_agent_permissions_agent ON agent_permissions(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_permissions_type ON agent_permissions(permission_type);
CREATE INDEX IF NOT EXISTS idx_agent_performance_agent ON agent_performance_history(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_performance_date ON agent_performance_history(evaluation_date);
CREATE INDEX IF NOT EXISTS idx_agent_training_agent ON agent_training_history(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_training_type ON agent_training_history(training_type);
CREATE INDEX IF NOT EXISTS idx_agent_activity_agent ON agent_activity_logs(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_activity_type ON agent_activity_logs(activity_type);
CREATE INDEX IF NOT EXISTS idx_agent_activity_created ON agent_activity_logs(created_at);

-- 뷰 생성
CREATE VIEW IF NOT EXISTS agent_summary_view AS
SELECT 
    ap.id,
    ap.employee_id,
    ap.full_name,
    ap.department,
    ap.position,
    ap.team,
    ap.experience_years,
    aa.account_status,
    aa.last_login_at,
    COUNT(DISTINCT cs.id) as total_sessions,
    AVG(cs.overall_quality_score) as avg_quality_score,
    AVG(cs.customer_satisfaction_score) as avg_satisfaction_score,
    COUNT(DISTINCT aph.id) as performance_evaluations,
    COUNT(DISTINCT ath.id) as training_completions,
    COUNT(DISTINCT aal.id) as recent_activities
FROM agent_profiles ap
LEFT JOIN agent_accounts aa ON ap.account_id = aa.id
LEFT JOIN consultation_sessions cs ON ap.id = cs.agent_id
LEFT JOIN agent_performance_history aph ON ap.id = aph.agent_id
LEFT JOIN agent_training_history ath ON ap.id = ath.agent_id AND ath.completion_status = 'completed'
LEFT JOIN agent_activity_logs aal ON ap.id = aal.agent_id AND aal.created_at >= date('now', '-30 days')
WHERE ap.is_active = 1
GROUP BY ap.id;

-- 상담사 성과 트렌드 뷰
CREATE VIEW IF NOT EXISTS agent_performance_trends AS
SELECT 
    agent_id,
    DATE(evaluation_date) as date,
    AVG(performance_score) as avg_performance,
    AVG(quality_score) as avg_quality,
    AVG(customer_satisfaction_score) as avg_satisfaction,
    AVG(resolution_rate) as avg_resolution_rate,
    COUNT(*) as evaluation_count
FROM agent_performance_history
GROUP BY agent_id, DATE(evaluation_date)
ORDER BY agent_id, date DESC;

-- 트리거 생성
CREATE TRIGGER IF NOT EXISTS update_agent_accounts_timestamp 
    AFTER UPDATE ON agent_accounts
    FOR EACH ROW
BEGIN
    UPDATE agent_accounts SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_agent_profiles_timestamp 
    AFTER UPDATE ON agent_profiles
    FOR EACH ROW
BEGIN
    UPDATE agent_profiles SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_agent_settings_timestamp 
    AFTER UPDATE ON agent_settings
    FOR EACH ROW
BEGIN
    UPDATE agent_settings SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- 팀 크기 자동 업데이트 트리거
CREATE TRIGGER IF NOT EXISTS update_team_size_insert
    AFTER INSERT ON agent_team_memberships
    FOR EACH ROW
BEGIN
    UPDATE agent_teams 
    SET team_size = (
        SELECT COUNT(*) 
        FROM agent_team_memberships 
        WHERE team_id = NEW.team_id AND is_active = 1
    )
    WHERE id = NEW.team_id;
END;

CREATE TRIGGER IF NOT EXISTS update_team_size_update
    AFTER UPDATE ON agent_team_memberships
    FOR EACH ROW
BEGIN
    UPDATE agent_teams 
    SET team_size = (
        SELECT COUNT(*) 
        FROM agent_team_memberships 
        WHERE team_id = NEW.team_id AND is_active = 1
    )
    WHERE id = NEW.team_id;
END; 