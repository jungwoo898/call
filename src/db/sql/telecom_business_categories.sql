-- 📱 통신사 업무 분야별 세분화 스키마
-- 목적: 실제 통신사 상담 업무에 맞는 세분화된 분류

-- ========================================================================
-- 1. 업무 분야 ENUM 타입 정의
-- ========================================================================

-- 대분류: 업무 영역
CREATE TYPE business_area AS ENUM (
    '요금관리',      -- 요금 관련 모든 업무
    '기기관리',      -- 휴대폰, 기기 관련
    '서비스관리',    -- 부가서비스, 요금제 관련
    '계정관리',      -- 명의, 번호, USIM 관련
    '기술지원',      -- 기술적 문제 해결
    '기타'           -- 기타 업무
);

-- 중분류: 세부 업무
CREATE TYPE detail_business_type AS ENUM (
    -- 요금관리
    '요금안내', '요금납부', '요금제변경', '선택약정할인', '납부방법변경',
    
    -- 기기관리  
    '휴대폰정지', '휴대폰분실', '휴대폰파손', '기기변경', '소액결제',
    
    -- 서비스관리
    '부가서비스안내', '부가서비스가입', '부가서비스해지', '부가서비스변경',
    
    -- 계정관리
    '명의변경', '번호변경', 'USIM해지', '계정해지', '번호이동',
    
    -- 기술지원
    '네트워크문제', '앱설치', '설정변경', '데이터복구',
    
    -- 기타
    '문의', '불만', '제안', '기타'
);

-- 소분류: 구체적 업무
CREATE TYPE specific_task_type AS ENUM (
    -- 요금 관련
    '월정액요금안내', '데이터요금안내', '통화요금안내', '문자요금안내',
    '신용카드납부', '계좌이체납부', '편의점납부', '자동이체설정',
    '5G요금제변경', '4G요금제변경', '선택약정24개월', '선택약정12개월',
    
    -- 기기 관련
    '휴대폰일시정지', '휴대폰영구정지', '분실신고', '파손신고',
    '기기할부변경', '기기할부해지', '소액결제한도설정', '소액결제차단',
    
    -- 서비스 관련
    '부가서비스목록안내', '부가서비스가입신청', '부가서비스해지신청',
    '부가서비스요금변경', '부가서비스기능설정',
    
    -- 계정 관련
    '개인명의변경', '법인명의변경', '번호변경신청', 'USIM재발급',
    '계정해지신청', '번호이동신청', '번호이동해지'
);

-- ========================================================================
-- 2. 업무 분야 매핑 테이블
-- ========================================================================

CREATE TABLE business_category_mapping (
    id SERIAL PRIMARY KEY,
    business_area business_area NOT NULL,
    detail_business_type detail_business_type NOT NULL,
    specific_task_type specific_task_type,
    description TEXT,
    priority_level INTEGER DEFAULT 1 CHECK (priority_level BETWEEN 1 AND 5),
    estimated_handling_time_minutes INTEGER DEFAULT 10,
    required_skills TEXT[], -- 필요한 스킬 배열
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(detail_business_type, specific_task_type)
);

-- ========================================================================
-- 3. 상담 세션 테이블 업데이트
-- ========================================================================

-- 기존 consultation_sessions 테이블에 새로운 컬럼 추가
ALTER TABLE consultation_sessions 
ADD COLUMN IF NOT EXISTS business_area business_area,
ADD COLUMN IF NOT EXISTS detail_business_type detail_business_type,
ADD COLUMN IF NOT EXISTS specific_task_type specific_task_type,
ADD COLUMN IF NOT EXISTS handling_time_minutes INTEGER,
ADD COLUMN IF NOT EXISTS complexity_level INTEGER CHECK (complexity_level BETWEEN 1 AND 5);

-- ========================================================================
-- 4. 업무 분야별 품질 지표 테이블
-- ========================================================================

CREATE TABLE business_specific_metrics (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES consultation_sessions(id) ON DELETE CASCADE,
    business_area business_area NOT NULL,
    detail_business_type detail_business_type NOT NULL,
    specific_task_type specific_task_type,
    
    -- 업무별 특화 지표
    accuracy_score DECIMAL(5,4) CHECK (accuracy_score BETWEEN 0 AND 1), -- 정확성
    efficiency_score DECIMAL(5,4) CHECK (efficiency_score BETWEEN 0 AND 1), -- 효율성
    customer_satisfaction DECIMAL(5,4) CHECK (customer_satisfaction BETWEEN 0 AND 1), -- 고객 만족도
    resolution_rate DECIMAL(5,4) CHECK (resolution_rate BETWEEN 0 AND 1), -- 해결률
    first_call_resolution BOOLEAN DEFAULT FALSE, -- 첫 통화 해결 여부
    
    -- 업무별 특화 평가
    knowledge_accuracy DECIMAL(5,4) CHECK (knowledge_accuracy BETWEEN 0 AND 1), -- 지식 정확성
    procedure_following DECIMAL(5,4) CHECK (procedure_following BETWEEN 0 AND 1), -- 절차 준수
    communication_clarity DECIMAL(5,4) CHECK (communication_clarity BETWEEN 0 AND 1), -- 설명 명확성
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, business_area, detail_business_type)
);

-- ========================================================================
-- 5. 업무 분야별 개선 제안 테이블
-- ========================================================================

CREATE TABLE business_improvement_suggestions (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES consultation_sessions(id) ON DELETE CASCADE,
    business_area business_area NOT NULL,
    detail_business_type detail_business_type NOT NULL,
    specific_task_type specific_task_type,
    
    suggestion_category TEXT NOT NULL, -- '절차개선', '지식보완', '커뮤니케이션', '시스템개선'
    suggestion_text TEXT NOT NULL,
    priority_level INTEGER CHECK (priority_level BETWEEN 1 AND 5),
    expected_impact TEXT, -- '높음', '보통', '낮음'
    implementation_difficulty TEXT, -- '쉬움', '보통', '어려움'
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ========================================================================
-- 6. 인덱스 생성
-- ========================================================================

CREATE INDEX CONCURRENTLY idx_consultation_sessions_business_area 
ON consultation_sessions(business_area);

CREATE INDEX CONCURRENTLY idx_consultation_sessions_detail_business 
ON consultation_sessions(detail_business_type);

CREATE INDEX CONCURRENTLY idx_consultation_sessions_specific_task 
ON consultation_sessions(specific_task_type);

CREATE INDEX CONCURRENTLY idx_business_specific_metrics_area 
ON business_specific_metrics(business_area, detail_business_type);

-- ========================================================================
-- 7. 뷰 생성
-- ========================================================================

-- 업무 분야별 성과 요약 뷰
CREATE VIEW business_performance_summary AS
SELECT 
    cs.business_area,
    cs.detail_business_type,
    cs.specific_task_type,
    COUNT(*) as total_sessions,
    AVG(cs.overall_quality_score) as avg_quality_score,
    AVG(cs.customer_satisfaction_score) as avg_satisfaction,
    AVG(cs.handling_time_minutes) as avg_handling_time,
    AVG(bsm.resolution_rate) as avg_resolution_rate,
    AVG(bsm.first_call_resolution::INTEGER) as first_call_resolution_rate
FROM consultation_sessions cs
LEFT JOIN business_specific_metrics bsm ON cs.id = bsm.session_id
WHERE cs.business_area IS NOT NULL
GROUP BY cs.business_area, cs.detail_business_type, cs.specific_task_type
ORDER BY cs.business_area, cs.detail_business_type;

-- ========================================================================
-- 8. 샘플 데이터 삽입
-- ========================================================================

-- 업무 분야 매핑 데이터
INSERT INTO business_category_mapping (business_area, detail_business_type, specific_task_type, description, priority_level, estimated_handling_time_minutes, required_skills) VALUES
-- 요금관리
('요금관리', '요금안내', '월정액요금안내', '월정액 요금 상세 안내', 1, 5, ARRAY['요금지식', '설명능력']),
('요금관리', '요금안내', '데이터요금안내', '데이터 사용량별 요금 안내', 1, 5, ARRAY['요금지식', '설명능력']),
('요금관리', '요금납부', '신용카드납부', '신용카드 납부 방법 안내', 2, 8, ARRAY['결제시스템', '고객지원']),
('요금관리', '요금납부', '계좌이체납부', '계좌이체 납부 방법 안내', 2, 8, ARRAY['결제시스템', '고객지원']),
('요금관리', '요금제변경', '5G요금제변경', '5G 요금제 변경 처리', 3, 15, ARRAY['요금제지식', '시스템조작']),
('요금관리', '요금제변경', '4G요금제변경', '4G 요금제 변경 처리', 3, 15, ARRAY['요금제지식', '시스템조작']),
('요금관리', '선택약정할인', '선택약정24개월', '24개월 선택약정 할인 신청', 3, 12, ARRAY['약정지식', '계약처리']),
('요금관리', '선택약정할인', '선택약정12개월', '12개월 선택약정 할인 신청', 3, 12, ARRAY['약정지식', '계약처리']),

-- 기기관리
('기기관리', '휴대폰정지', '휴대폰일시정지', '휴대폰 일시 정지 처리', 4, 10, ARRAY['기기관리', '보안절차']),
('기기관리', '휴대폰정지', '휴대폰영구정지', '휴대폰 영구 정지 처리', 4, 10, ARRAY['기기관리', '보안절차']),
('기기관리', '휴대폰분실', '분실신고', '휴대폰 분실 신고 처리', 5, 20, ARRAY['분실처리', '보안절차']),
('기기관리', '휴대폰파손', '파손신고', '휴대폰 파손 신고 처리', 4, 15, ARRAY['파손처리', '보험절차']),
('기기관리', '기기변경', '기기할부변경', '기기 할부 변경 처리', 3, 20, ARRAY['기기지식', '계약처리']),
('기기관리', '기기변경', '기기할부해지', '기기 할부 해지 처리', 3, 15, ARRAY['기기지식', '계약처리']),
('기기관리', '소액결제', '소액결제한도설정', '소액결제 한도 설정', 2, 8, ARRAY['결제시스템', '보안설정']),
('기기관리', '소액결제', '소액결제차단', '소액결제 차단 설정', 2, 8, ARRAY['결제시스템', '보안설정']),

-- 서비스관리
('서비스관리', '부가서비스안내', '부가서비스목록안내', '부가서비스 목록 안내', 1, 5, ARRAY['서비스지식', '설명능력']),
('서비스관리', '부가서비스가입', '부가서비스가입신청', '부가서비스 가입 신청 처리', 2, 10, ARRAY['서비스지식', '가입처리']),
('서비스관리', '부가서비스해지', '부가서비스해지신청', '부가서비스 해지 신청 처리', 2, 10, ARRAY['서비스지식', '해지처리']),
('서비스관리', '부가서비스변경', '부가서비스요금변경', '부가서비스 요금 변경 처리', 3, 12, ARRAY['서비스지식', '변경처리']),

-- 계정관리
('계정관리', '명의변경', '개인명의변경', '개인 명의 변경 처리', 4, 25, ARRAY['명의변경', '서류처리']),
('계정관리', '명의변경', '법인명의변경', '법인 명의 변경 처리', 5, 30, ARRAY['명의변경', '서류처리']),
('계정관리', '번호변경', '번호변경신청', '번호 변경 신청 처리', 4, 20, ARRAY['번호관리', '신청처리']),
('계정관리', 'USIM해지', 'USIM재발급', 'USIM 재발급 처리', 3, 15, ARRAY['USIM관리', '발급처리']),
('계정관리', '계정해지', '계정해지신청', '계정 해지 신청 처리', 5, 30, ARRAY['계정관리', '해지처리']),
('계정관리', '번호이동', '번호이동신청', '번호이동 신청 처리', 4, 25, ARRAY['번호이동', '신청처리']);

-- ========================================================================
-- 9. 트리거 생성
-- ========================================================================

-- 업무 분야 자동 매핑 트리거
CREATE OR REPLACE FUNCTION auto_map_business_category()
RETURNS TRIGGER AS $$
BEGIN
    -- detail_business_type이 설정되면 자동으로 business_area 매핑
    IF NEW.detail_business_type IS NOT NULL AND NEW.business_area IS NULL THEN
        SELECT bcm.business_area INTO NEW.business_area
        FROM business_category_mapping bcm
        WHERE bcm.detail_business_type = NEW.detail_business_type
        LIMIT 1;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auto_map_business_category
    BEFORE INSERT OR UPDATE ON consultation_sessions
    FOR EACH ROW
    EXECUTE FUNCTION auto_map_business_category(); 