-- 상담 분석 통계 뷰
CREATE VIEW IF NOT EXISTS consultation_statistics AS
SELECT 
    ca.business_type,
    ca.classification_type,
    ca.consultation_result,
    COUNT(*) as total_count,
    AVG(ca.confidence) as avg_confidence,
    AVG(ca.processing_time) as avg_processing_time,
    MIN(ca.created_at) as first_analysis,
    MAX(ca.created_at) as last_analysis
FROM consultation_analysis ca
GROUP BY ca.business_type, ca.classification_type, ca.consultation_result;

-- 일별 상담 분석 통계 뷰
CREATE VIEW IF NOT EXISTS daily_consultation_stats AS
SELECT 
    DATE(ca.created_at) as analysis_date,
    COUNT(*) as total_analyses,
    COUNT(DISTINCT ca.audio_properties_id) as unique_files,
    AVG(ca.confidence) as avg_confidence,
    AVG(ca.processing_time) as avg_processing_time
FROM consultation_analysis ca
GROUP BY DATE(ca.created_at)
ORDER BY analysis_date DESC; 