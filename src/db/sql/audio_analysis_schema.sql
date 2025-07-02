-- 🎵 Callytics 오디오 분석 데이터베이스 스키마
-- 목적: 오디오 파일 기반 기술적 분석 결과 저장

-- 오디오 파일 테이블
CREATE TABLE IF NOT EXISTS audio_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    file_size INTEGER,
    duration_seconds REAL,
    sample_rate INTEGER,
    channels INTEGER,
    format TEXT,
    upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    processing_status TEXT DEFAULT 'pending',
    processing_completed_at DATETIME,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 화자 분리 결과 테이블
CREATE TABLE IF NOT EXISTS speaker_segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audio_file_id INTEGER NOT NULL,
    speaker_id TEXT NOT NULL,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    confidence REAL,
    speaker_type TEXT CHECK(speaker_type IN ('customer', 'agent', 'unknown')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (audio_file_id) REFERENCES audio_files(id) ON DELETE CASCADE
);

-- 음성 인식 결과 테이블
CREATE TABLE IF NOT EXISTS transcriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audio_file_id INTEGER NOT NULL,
    speaker_segment_id INTEGER,
    text_content TEXT NOT NULL,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    confidence REAL,
    language TEXT DEFAULT 'ko',
    punctuation_restored BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (audio_file_id) REFERENCES audio_files(id) ON DELETE CASCADE,
    FOREIGN KEY (speaker_segment_id) REFERENCES speaker_segments(id) ON DELETE CASCADE
);

-- 오디오 품질 지표 테이블
CREATE TABLE IF NOT EXISTS audio_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audio_file_id INTEGER NOT NULL UNIQUE,
    snr_db REAL, -- 신호 대 잡음비 (Signal-to-Noise Ratio)
    clarity_score REAL CHECK(clarity_score >= 0 AND clarity_score <= 1), -- 명확도 점수
    volume_level REAL, -- 볼륨 레벨 (dB)
    background_noise_level REAL, -- 배경 잡음 레벨 (dB)
    speech_rate REAL, -- 말하기 속도 (단어/분)
    pause_frequency REAL, -- 휴식 빈도 (횟수/분)
    audio_quality_score REAL CHECK(audio_quality_score >= 0 AND audio_quality_score <= 1),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (audio_file_id) REFERENCES audio_files(id) ON DELETE CASCADE
);

-- 처리 로그 테이블
CREATE TABLE IF NOT EXISTS processing_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audio_file_id INTEGER NOT NULL,
    processing_step TEXT NOT NULL,
    status TEXT CHECK(status IN ('started', 'completed', 'failed', 'skipped')),
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    duration_seconds REAL,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (audio_file_id) REFERENCES audio_files(id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_audio_files_status ON audio_files(processing_status);
CREATE INDEX IF NOT EXISTS idx_audio_files_upload_time ON audio_files(upload_timestamp);
CREATE INDEX IF NOT EXISTS idx_speaker_segments_audio_file ON speaker_segments(audio_file_id);
CREATE INDEX IF NOT EXISTS idx_speaker_segments_speaker_type ON speaker_segments(speaker_type);
CREATE INDEX IF NOT EXISTS idx_transcriptions_audio_file ON transcriptions(audio_file_id);
CREATE INDEX IF NOT EXISTS idx_transcriptions_speaker_segment ON transcriptions(speaker_segment_id);
CREATE INDEX IF NOT EXISTS idx_processing_logs_audio_file ON processing_logs(audio_file_id);
CREATE INDEX IF NOT EXISTS idx_processing_logs_step ON processing_logs(processing_step);

-- 뷰 생성
CREATE VIEW IF NOT EXISTS audio_processing_summary AS
SELECT 
    af.id,
    af.file_name,
    af.duration_seconds,
    af.processing_status,
    af.upload_timestamp,
    af.processing_completed_at,
    COUNT(ss.id) as speaker_segments_count,
    COUNT(t.id) as transcription_count,
    am.clarity_score,
    am.audio_quality_score,
    CASE 
        WHEN af.processing_completed_at IS NOT NULL THEN 'completed'
        WHEN af.error_message IS NOT NULL THEN 'failed'
        ELSE 'processing'
    END as overall_status
FROM audio_files af
LEFT JOIN speaker_segments ss ON af.id = ss.audio_file_id
LEFT JOIN transcriptions t ON af.id = t.audio_file_id
LEFT JOIN audio_metrics am ON af.id = am.audio_file_id
GROUP BY af.id;

-- 트리거 생성 (updated_at 자동 업데이트)
CREATE TRIGGER IF NOT EXISTS update_audio_files_timestamp 
    AFTER UPDATE ON audio_files
    FOR EACH ROW
BEGIN
    UPDATE audio_files SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END; 