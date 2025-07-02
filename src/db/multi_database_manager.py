#!/usr/bin/env python3
"""
Callytics 다중 데이터베이스 관리자
오디오 분석 DB, 상담 품질 분석 DB, 대시보드 DB를 통합 관리
"""

import sqlite3
import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from contextlib import contextmanager
from datetime import datetime
import json
import yaml

logger = logging.getLogger(__name__)

class MultiDatabaseManager:
    """다중 데이터베이스 관리자"""
    
    def __init__(self, db_dir: str = "data", config_path: str = "config/config.yaml"):
        self.db_dir = db_dir
        self.config_path = config_path
        
        # 설정에서 데이터베이스 경로 로드
        db_paths = self._load_db_paths()
        
        self.audio_db_path = db_paths['audio_analysis']
        self.quality_db_path = db_paths['consultation_quality']
        
        # 데이터베이스 디렉토리 생성
        os.makedirs(db_dir, exist_ok=True)
        
        # 데이터베이스 연결 초기화
        self.audio_conn = None
        self.quality_conn = None
        
        # 데이터베이스 초기화
        self._init_databases()
        
        logger.info(f"다중 데이터베이스 관리자 초기화 완료")
        logger.info(f"오디오 분석 DB: {self.audio_db_path}")
        logger.info(f"상담 품질 DB: {self.quality_db_path}")
    
    def _init_databases(self):
        """데이터베이스 초기화 및 스키마 생성"""
        try:
            # 오디오 분석 데이터베이스 초기화
            self._init_audio_database()
            
            # 상담 품질 분석 데이터베이스 초기화
            self._init_quality_database()
            
            logger.info("모든 데이터베이스 초기화 완료")
            
        except Exception as e:
            logger.error(f"데이터베이스 초기화 실패: {e}")
            raise
    
    def _init_audio_database(self):
        """오디오 분석 데이터베이스 초기화"""
        try:
            conn = sqlite3.connect(self.audio_db_path)
            cursor = conn.cursor()
            
            # 오디오 분석 스키마 로드 및 실행
            schema_file = "src/db/sql/audio_analysis_schema.sql"
            if os.path.exists(schema_file):
                with open(schema_file, 'r', encoding='utf-8') as f:
                    schema = f.read()
                cursor.executescript(schema)
                conn.commit()
                logger.info("오디오 분석 데이터베이스 스키마 생성 완료")
            else:
                logger.warning(f"오디오 분석 스키마 파일을 찾을 수 없음: {schema_file}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"오디오 분석 데이터베이스 초기화 실패: {e}")
            raise
    
    def _init_quality_database(self):
        """상담 품질 분석 데이터베이스 초기화"""
        try:
            conn = sqlite3.connect(self.quality_db_path)
            cursor = conn.cursor()
            
            # 상담 품질 분석 스키마 로드 및 실행
            schema_file = "src/db/sql/consultation_quality_schema.sql"
            if os.path.exists(schema_file):
                with open(schema_file, 'r', encoding='utf-8') as f:
                    schema = f.read()
                cursor.executescript(schema)
                conn.commit()
                logger.info("상담 품질 분석 데이터베이스 스키마 생성 완료")
            else:
                logger.warning(f"상담 품질 분석 스키마 파일을 찾을 수 없음: {schema_file}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"상담 품질 분석 데이터베이스 초기화 실패: {e}")
            raise
    

    
    # 🎵 오디오 분석 DB 메서드들
    
    def save_audio_file(self, file_path: str, file_name: str, file_size: int, 
                       duration_seconds: float, sample_rate: int, channels: int, 
                       format_type: str) -> int:
        """오디오 파일 정보 저장"""
        conn = self.get_connection("audio")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audio_files (file_path, file_name, file_size, duration_seconds, 
                                   sample_rate, channels, format)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (file_path, file_name, file_size, duration_seconds, sample_rate, channels, format_type))
        conn.commit()
        return cursor.lastrowid
    
    def save_speaker_segments(self, audio_file_id: int, segments: List[Dict[str, Any]]):
        """화자 분리 결과 저장"""
        conn = self.get_connection("audio")
        cursor = conn.cursor()
        for segment in segments:
            cursor.execute("""
                INSERT INTO speaker_segments (audio_file_id, speaker_id, start_time, 
                                            end_time, confidence, speaker_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (audio_file_id, segment['speaker_id'], segment['start_time'], 
                 segment['end_time'], segment.get('confidence'), segment.get('speaker_type')))
        conn.commit()
    
    def save_transcriptions(self, audio_file_id: int, transcriptions: List[Dict[str, Any]]):
        """음성 인식 결과 저장"""
        conn = self.get_connection("audio")
        cursor = conn.cursor()
        for trans in transcriptions:
            cursor.execute("""
                INSERT INTO transcriptions (audio_file_id, speaker_segment_id, text_content,
                                          start_time, end_time, confidence, language)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (audio_file_id, trans.get('speaker_segment_id'), trans['text_content'],
                 trans['start_time'], trans['end_time'], trans.get('confidence'), trans.get('language', 'ko')))
        conn.commit()
    
    def save_audio_metrics(self, audio_file_id: int, metrics: Dict[str, Any]):
        """오디오 품질 지표 저장"""
        conn = self.get_connection("audio")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audio_metrics (audio_file_id, snr_db, clarity_score, volume_level,
                                     background_noise_level, speech_rate, pause_frequency, audio_quality_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (audio_file_id, metrics.get('snr_db'), metrics.get('clarity_score'),
             metrics.get('volume_level'), metrics.get('background_noise_level'),
             metrics.get('speech_rate'), metrics.get('pause_frequency'), metrics.get('audio_quality_score')))
        conn.commit()
    
    def update_audio_processing_status(self, audio_file_id: int, status: str, error_message: str = None):
        """오디오 처리 상태 업데이트"""
        conn = self.get_connection("audio")
        cursor = conn.cursor()
        if status == 'completed':
            cursor.execute("""
                UPDATE audio_files 
                SET processing_status = ?, processing_completed_at = CURRENT_TIMESTAMP, error_message = ?
                WHERE id = ?
            """, (status, error_message, audio_file_id))
        else:
            cursor.execute("""
                UPDATE audio_files 
                SET processing_status = ?, error_message = ?
                WHERE id = ?
            """, (status, error_message, audio_file_id))
        conn.commit()
    
    # 🧠 상담 품질 분석 DB 메서드들
    
    def create_consultation_session(self, audio_file_id: int, session_date: str, 
                                  duration_minutes: float, agent_name: str = None, 
                                  customer_id: str = None, consultation_type: str = 'other') -> int:
        """상담 세션 생성"""
        conn = self.get_connection("quality")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO consultation_sessions (audio_file_id, session_date, duration_minutes,
                                             agent_name, customer_id, consultation_type)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (audio_file_id, session_date, duration_minutes, agent_name, customer_id, consultation_type))
        conn.commit()
        return cursor.lastrowid
    
    def save_quality_metrics(self, session_id: int, metrics: List[Dict[str, Any]]):
        """품질 평가 지표 저장"""
        conn = self.get_connection("quality")
        cursor = conn.cursor()
        for metric in metrics:
            cursor.execute("""
                INSERT INTO quality_metrics (session_id, metric_name, metric_value, 
                                           metric_description, weight, category)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, metric['name'], metric['value'], metric.get('description'),
                 metric.get('weight', 1.0), metric.get('category')))
        conn.commit()
    
    def save_sentiment_analysis(self, session_id: int, sentiment_data: List[Dict[str, Any]]):
        """감정 분석 결과 저장"""
        conn = self.get_connection("quality")
        cursor = conn.cursor()
        for sentiment in sentiment_data:
            cursor.execute("""
                INSERT INTO sentiment_analysis (session_id, speaker_type, sentiment_score,
                                              emotion_category, confidence)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, sentiment['speaker_type'], sentiment['sentiment_score'],
                 sentiment.get('emotion_category'), sentiment.get('confidence')))
        conn.commit()
    
    def save_communication_patterns(self, session_id: int, patterns: List[Dict[str, Any]]):
        """커뮤니케이션 패턴 저장"""
        conn = self.get_connection("quality")
        cursor = conn.cursor()
        for pattern in patterns:
            cursor.execute("""
                INSERT INTO communication_patterns (session_id, pattern_type, frequency,
                                                  severity_score, description, impact_on_quality)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, pattern['pattern_type'], pattern.get('frequency', 0),
                 pattern.get('severity_score'), pattern.get('description'), pattern.get('impact_on_quality')))
        conn.commit()
    
    def save_improvement_suggestions(self, session_id: int, suggestions: List[Dict[str, Any]]):
        """개선 제안사항 저장"""
        conn = self.get_connection("quality")
        cursor = conn.cursor()
        for suggestion in suggestions:
            cursor.execute("""
                INSERT INTO improvement_suggestions (session_id, suggestion_category, suggestion_text,
                                                   priority, implementation_difficulty, expected_impact, target_audience)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (session_id, suggestion['category'], suggestion['text'], suggestion['priority'],
                 suggestion.get('implementation_difficulty'), suggestion.get('expected_impact'),
                 suggestion.get('target_audience')))
        conn.commit()
    
    def update_consultation_analysis_status(self, session_id: int, status: str, 
                                          overall_quality_score: float = None, 
                                          customer_satisfaction_score: float = None,
                                          summary: str = None, key_issues: str = None,
                                          resolution_status: str = None):
        """상담 분석 상태 업데이트"""
        conn = self.get_connection("quality")
        cursor = conn.cursor()
        if status == 'completed':
            cursor.execute("""
                UPDATE consultation_sessions 
                SET analysis_status = ?, analysis_completed_at = CURRENT_TIMESTAMP,
                    overall_quality_score = ?, customer_satisfaction_score = ?,
                    summary = ?, key_issues = ?, resolution_status = ?
                WHERE id = ?
            """, (status, overall_quality_score, customer_satisfaction_score,
                 summary, key_issues, resolution_status, session_id))
        else:
            cursor.execute("""
                UPDATE consultation_sessions 
                SET analysis_status = ?
                WHERE id = ?
            """, (status, session_id))
        conn.commit()
    

    
    # 🔍 통합 조회 메서드들
    
    def get_audio_file_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """파일 경로로 오디오 파일 정보 조회"""
        conn = self.get_connection("audio")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audio_files WHERE file_path = ?", (file_path,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_session_by_audio_file_id(self, audio_file_id: int) -> Optional[Dict[str, Any]]:
        """오디오 파일 ID로 상담 세션 조회"""
        conn = self.get_connection("quality")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM consultation_sessions WHERE audio_file_id = ?", (audio_file_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_complete_analysis_result(self, audio_file_id: int) -> Dict[str, Any]:
        """완전한 분석 결과 조회 (오디오 + 상담 품질)"""
        result = {
            'audio_analysis': {},
            'consultation_quality': {}
        }
        
        # 오디오 분석 결과
        conn = self.get_connection("audio")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT af.*, am.*, 
                   COUNT(ss.id) as speaker_segments_count,
                   COUNT(t.id) as transcription_count
            FROM audio_files af
            LEFT JOIN audio_metrics am ON af.id = am.audio_file_id
            LEFT JOIN speaker_segments ss ON af.id = ss.audio_file_id
            LEFT JOIN transcriptions t ON af.id = t.audio_file_id
            WHERE af.id = ?
            GROUP BY af.id
        """, (audio_file_id,))
        row = cursor.fetchone()
        if row:
            result['audio_analysis'] = dict(row)
        
        # 상담 품질 분석 결과
        conn = self.get_connection("quality")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cs.*, 
                   COUNT(qm.id) as metrics_count,
                   COUNT(sa.id) as sentiment_analyses_count,
                   COUNT(cp.id) as communication_patterns_count,
                   COUNT(is.id) as improvement_suggestions_count
            FROM consultation_sessions cs
            LEFT JOIN quality_metrics qm ON cs.id = qm.session_id
            LEFT JOIN sentiment_analysis sa ON cs.id = sa.session_id
            LEFT JOIN communication_patterns cp ON cs.id = cp.session_id
            LEFT JOIN improvement_suggestions is ON cs.id = is.session_id
            WHERE cs.audio_file_id = ?
            GROUP BY cs.id
        """, (audio_file_id,))
        row = cursor.fetchone()
        if row:
            result['consultation_quality'] = dict(row)
        
        return result
    
    def get_database_stats(self) -> Dict[str, Any]:
        """데이터베이스 통계 정보 반환"""
        stats = {}
        
        try:
            # 오디오 분석 DB 통계
            audio_conn = self.get_connection("audio")
            audio_cursor = audio_conn.cursor()
            
            # 테이블 목록 조회
            audio_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            audio_tables = [row[0] for row in audio_cursor.fetchall()]
            
            audio_stats = {}
            for table in audio_tables:
                audio_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = audio_cursor.fetchone()[0]
                audio_stats[table] = count
            
            stats['audio_analysis'] = {
                'database_path': self.audio_db_path,
                'tables': audio_stats
            }
            
            # 상담 품질 DB 통계
            quality_conn = self.get_connection("quality")
            quality_cursor = quality_conn.cursor()
            
            # 테이블 목록 조회
            quality_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            quality_tables = [row[0] for row in quality_cursor.fetchall()]
            
            quality_stats = {}
            for table in quality_tables:
                quality_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = quality_cursor.fetchone()[0]
                quality_stats[table] = count
            
            stats['consultation_quality'] = {
                'database_path': self.quality_db_path,
                'tables': quality_stats
            }
            
        except Exception as e:
            logger.error(f"데이터베이스 통계 조회 실패: {e}")
            stats['error'] = str(e)
        
        return stats

    def _load_db_paths(self) -> Dict[str, str]:
        """설정에서 데이터베이스 경로 로드 (환경 변수 우선순위)"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 환경 변수 우선 확인
            env_db_url = os.getenv('DATABASE_URL')
            if env_db_url:
                # SQLite URL 형식 처리: sqlite:///path/to/db.sqlite
                if env_db_url.startswith('sqlite:///'):
                    db_path = env_db_url.replace('sqlite:///', '')
                    logger.info(f"환경 변수에서 데이터베이스 경로 로드: {db_path}")
                    return {
                        'audio_analysis': db_path,
                        'consultation_quality': db_path
                    }
            
            # 설정 파일에서 로드
            db_config = config.get('database', {})
            
            # 상담 품질 분석 DB (새로 신설)
            consultation_quality_db = db_config.get('consultation_quality_db', 'data/callytics_consultation_quality.db')
            
            # 오디오 분석 DB (기존)
            audio_analysis_db = db_config.get('audio_analysis_db', 'Callytics_new.sqlite')
            
            # 기본값 설정
            defaults = config.get('environment', {}).get('defaults', {})
            if not consultation_quality_db:
                consultation_quality_db = defaults.get('DATABASE_URL', 'data/callytics_consultation_quality.db')
                if consultation_quality_db.startswith('sqlite:///'):
                    consultation_quality_db = consultation_quality_db.replace('sqlite:///', '')
            
            logger.info(f"설정 파일에서 데이터베이스 경로 로드: audio={audio_analysis_db}, quality={consultation_quality_db}")
            
            return {
                'audio_analysis': audio_analysis_db,
                'consultation_quality': consultation_quality_db
            }
            
        except Exception as e:
            logger.warning(f"설정 파일 로드 실패, 기본 경로 사용: {e}")
            return {
                'audio_analysis': 'Callytics_new.sqlite',
                'consultation_quality': 'data/callytics_consultation_quality.db'
            }

    def get_connection(self, db_type: str) -> sqlite3.Connection:
        """데이터베이스 연결 반환"""
        if db_type == "audio":
            if not self.audio_conn:
                self.audio_conn = sqlite3.connect(self.audio_db_path)
                self.audio_conn.row_factory = sqlite3.Row
            return self.audio_conn
        elif db_type == "quality":
            if not self.quality_conn:
                self.quality_conn = sqlite3.connect(self.quality_db_path)
                self.quality_conn.row_factory = sqlite3.Row
            return self.quality_conn
        else:
            raise ValueError(f"지원하지 않는 데이터베이스 타입: {db_type}")
    
    def close_connections(self):
        """모든 데이터베이스 연결 종료"""
        if self.audio_conn:
            self.audio_conn.close()
            self.audio_conn = None
        if self.quality_conn:
            self.quality_conn.close()
            self.quality_conn = None
        logger.info("모든 데이터베이스 연결 종료")

    def __del__(self):
        """소멸자: 연결 종료"""
        self.close_connections()
    
    # 🔄 구 버전 호환성 메서드들 (기존 코드와의 호환성 유지)
    
    def insert_analysis_history(self, data: Dict[str, Any]) -> bool:
        """분석 이력 저장 (구 버전 호환성)"""
        try:
            conn = self.get_connection("quality")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO analysis_history (
                    session_id, analysis_type, status, started_at, completed_at,
                    result_summary, error_message, triggered_by, parameters
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('session_id'), data.get('analysis_type'), data.get('status'),
                data.get('started_at'), data.get('completed_at'), data.get('result_summary'),
                data.get('error_message'), data.get('triggered_by'), data.get('parameters')
            ))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"분석 이력 저장 실패: {e}")
            return False
    
    def insert_consultation_analysis(self, data: Dict[str, Any]) -> bool:
        """상담 분석 결과 저장 (구 버전 호환성)"""
        try:
            conn = self.get_connection("quality")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO consultation_analysis (
                    consultation_id, audio_path, business_type, classification_type,
                    detail_classification, consultation_result, summary, customer_request,
                    solution, additional_info, confidence, processing_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('consultation_id'), data.get('audio_path'), data.get('business_type'),
                data.get('classification_type'), data.get('detail_classification'),
                data.get('consultation_result'), data.get('summary'), data.get('customer_request'),
                data.get('solution'), data.get('additional_info'), data.get('confidence'),
                data.get('processing_time')
            ))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"상담 분석 결과 저장 실패: {e}")
            return False
    
    def insert_communication_quality(self, data: Dict[str, Any]) -> bool:
        """커뮤니케이션 품질 분석 결과 저장 (구 버전 호환성)"""
        try:
            conn = self.get_connection("quality")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO communication_quality (
                    audio_path, consultation_id, honorific_ratio, positive_word_ratio,
                    negative_word_ratio, euphonious_word_ratio, empathy_ratio, apology_ratio,
                    total_sentences, customer_sentiment_early, customer_sentiment_late,
                    customer_sentiment_trend, avg_response_latency, task_ratio,
                    suggestions, interruption_count, silence_ratio, talk_ratio, analysis_details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('audio_path'), data.get('consultation_id'), data.get('honorific_ratio'),
                data.get('positive_word_ratio'), data.get('negative_word_ratio'),
                data.get('euphonious_word_ratio'), data.get('empathy_ratio'), data.get('apology_ratio'),
                data.get('total_sentences'), data.get('customer_sentiment_early'),
                data.get('customer_sentiment_late'), data.get('customer_sentiment_trend'),
                data.get('avg_response_latency'), data.get('task_ratio'), data.get('suggestions'),
                data.get('interruption_count'), data.get('silence_ratio'), data.get('talk_ratio'),
                data.get('analysis_details')
            ))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"커뮤니케이션 품질 분석 결과 저장 실패: {e}")
            return False
    
    def insert_utterance(self, data: Dict[str, Any]) -> bool:
        """발화 내용 저장 (구 버전 호환성)"""
        try:
            conn = self.get_connection("quality")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO utterances (
                    audio_path, speaker, start_time, end_time, text, confidence,
                    sequence, sentiment, profane
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('audio_path'), data.get('speaker'), data.get('start_time'),
                data.get('end_time'), data.get('text'), data.get('confidence'),
                data.get('sequence'), data.get('sentiment'), data.get('profane')
            ))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"발화 내용 저장 실패: {e}")
            return False
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """분석 통계 조회 (구 버전 호환성)"""
        try:
            conn = self.get_connection("quality")
            cursor = conn.cursor()
            
            # 전체 상담 수
            cursor.execute("SELECT COUNT(*) FROM consultation_analysis")
            total_consultations = cursor.fetchone()[0]
            
            # 업무 유형별 통계
            cursor.execute("""
                SELECT business_type, COUNT(*) as count 
                FROM consultation_analysis 
                GROUP BY business_type 
                ORDER BY count DESC
            """)
            business_type_stats = dict(cursor.fetchall())
            
            # 분류 유형별 통계
            cursor.execute("""
                SELECT classification_type, COUNT(*) as count 
                FROM consultation_analysis 
                GROUP BY classification_type 
                ORDER BY count DESC
            """)
            classification_stats = dict(cursor.fetchall())
            
            # 평균 처리 시간
            cursor.execute("SELECT AVG(processing_time) FROM consultation_analysis")
            avg_processing_time = cursor.fetchone()[0] or 0.0
            
            # 전체 발화 수
            cursor.execute("SELECT COUNT(*) FROM utterances")
            total_utterances = cursor.fetchone()[0]
            
            return {
                'total_consultations': total_consultations,
                'total_utterances': total_utterances,
                'business_type_distribution': business_type_stats,
                'classification_type_distribution': classification_stats,
                'average_processing_time': avg_processing_time
            }
            
        except Exception as e:
            logger.error(f"통계 조회 실패: {e}")
            return {}
    
    # 🔄 구 버전 SQL 파일 실행 메서드들
    
    def fetch(self, sql_file_path: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """SQL 파일을 실행하고 결과를 반환 (구 버전 호환성)"""
        try:
            # SQL 파일 읽기
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_query = f.read().strip()
            
            if not sql_query:
                logger.warning(f"빈 SQL 파일: {sql_file_path}")
                return []
            
            conn = self.get_connection("quality")
            cursor = conn.cursor()
            
            if params:
                cursor.execute(sql_query, params)
            else:
                cursor.execute(sql_query)
            
            rows = cursor.fetchall()
            
            if rows:
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            else:
                return []
                
        except FileNotFoundError:
            logger.error(f"SQL 파일을 찾을 수 없습니다: {sql_file_path}")
            return []
        except Exception as e:
            logger.error(f"SQL 실행 실패 ({sql_file_path}): {e}")
            return []
    
    def insert(self, sql_file_path: str, params: Optional[tuple] = None) -> Optional[int]:
        """SQL 파일을 실행하고 마지막 ID 반환 (구 버전 호환성)"""
        try:
            # SQL 파일 읽기
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_query = f.read().strip()
            
            if not sql_query:
                logger.warning(f"빈 SQL 파일: {sql_file_path}")
                return None
            
            conn = self.get_connection("quality")
            cursor = conn.cursor()
            
            if params:
                cursor.execute(sql_query, params)
            else:
                cursor.execute(sql_query)
            
            conn.commit()
            last_id = cursor.lastrowid
            logger.info(f"SQL 실행 완료: {sql_file_path}, last_id: {last_id}")
            return last_id
                
        except FileNotFoundError:
            logger.error(f"SQL 파일을 찾을 수 없습니다: {sql_file_path}")
            return None
        except Exception as e:
            logger.error(f"SQL 실행 실패 ({sql_file_path}): {e}")
            return None
    
    def execute(self, sql_file_path: str, params: Optional[tuple] = None) -> bool:
        """SQL 파일을 실행 (구 버전 호환성)"""
        try:
            # SQL 파일 읽기
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_query = f.read().strip()
            
            if not sql_query:
                logger.warning(f"빈 SQL 파일: {sql_file_path}")
                return False
            
            conn = self.get_connection("quality")
            cursor = conn.cursor()
            
            if params:
                cursor.execute(sql_query, params)
            else:
                cursor.execute(sql_query)
            
            conn.commit()
            logger.info(f"SQL 실행 완료: {sql_file_path}")
            return True
                
        except FileNotFoundError:
            logger.error(f"SQL 파일을 찾을 수 없습니다: {sql_file_path}")
            return False
        except Exception as e:
            logger.error(f"SQL 실행 실패 ({sql_file_path}): {e}")
            return False 