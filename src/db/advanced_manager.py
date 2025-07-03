# Standard library imports
import os
import json
import sqlite3
import threading
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Annotated, List, Dict, Any, Optional, Tuple
from pathlib import Path
from queue import Queue
import logging
import psycopg2
import psycopg2.extras
from psycopg2.extensions import connection, cursor
from datetime import datetime, date
import uuid

# Local imports
from src.db.multi_database_manager import MultiDatabaseManager

logger = logging.getLogger(__name__)

class AdvancedDatabaseManager:
    """
    고성능 DB 관리 클래스
    bulk insert, 비동기 저장, 장애 복구 로직 지원
    """
    
    def __init__(self, 
                 config_path: str = "config/config.yaml",
                 max_workers: int = 4,
                 batch_size: int = 100,
                 enable_async: bool = True,
                 enable_recovery: bool = True):
        """
        AdvancedDatabaseManager 초기화
        
        Parameters
        ----------
        config_path : str
            설정 파일 경로
        max_workers : int
            병렬 처리 워커 수
        batch_size : int
            배치 크기
        enable_async : bool
            비동기 처리 활성화 여부
        enable_recovery : bool
            장애 복구 활성화 여부
        """
        self.config_path = config_path
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.enable_async = enable_async
        self.enable_recovery = enable_recovery
        
        # 기본 DB 매니저 초기화
        self.db_manager = MultiDatabaseManager(config_path)
        
        # 병렬 처리 executor
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # 비동기 저장 큐
        self.save_queue = Queue()
        self.save_thread = None
        if self.enable_async:
            self.save_thread = threading.Thread(target=self._async_save_worker, daemon=True)
            self.save_thread.start()
        
        # 장애 복구 로그
        self.recovery_log_file = Path("logs/db_recovery.log")
        self.recovery_log_file.parent.mkdir(exist_ok=True)
        
        # 성능 모니터링
        self.performance_stats = {
            "total_operations": 0,
            "bulk_operations": 0,
            "async_operations": 0,
            "failed_operations": 0,
            "recovery_operations": 0,
            "avg_operation_time": 0.0
        }
        
        # 배치 버퍼
        self.batch_buffers = {
            "audio_analysis": [],
            "quality_analysis": [],
            "llm_analysis": []
        }
        self.batch_locks = {
            "audio_analysis": threading.Lock(),
            "quality_analysis": threading.Lock(),
            "llm_analysis": threading.Lock()
        }
        
        print(f"✅ AdvancedDatabaseManager 초기화 완료")
    
    def _log_recovery(self, operation: str, error: str, recovery_action: str):
        """장애 복구 로그 기록"""
        if not self.enable_recovery:
            return
        
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {operation} - Error: {error} - Recovery: {recovery_action}\n"
            
            with open(self.recovery_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
        except Exception as e:
            print(f"⚠️ 복구 로그 기록 실패: {e}")
    
    def _async_save_worker(self):
        """비동기 저장 워커 스레드"""
        while True:
            try:
                # 큐에서 작업 가져오기
                operation = self.save_queue.get(timeout=1)
                if operation is None:  # 종료 신호
                    break
                
                operation_type, data, callback = operation
                
                # 실제 저장 수행
                start_time = time.time()
                success = self._perform_save_operation(operation_type, data)
                processing_time = time.time() - start_time
                
                # 성능 통계 업데이트
                self.performance_stats["total_operations"] += 1
                self.performance_stats["async_operations"] += 1
                self.performance_stats["avg_operation_time"] = (
                    (self.performance_stats["avg_operation_time"] * (self.performance_stats["total_operations"] - 1) + processing_time) 
                    / self.performance_stats["total_operations"]
                )
                
                if not success:
                    self.performance_stats["failed_operations"] += 1
                
                # 콜백 호출
                if callback:
                    try:
                        callback(success, processing_time)
                    except Exception as e:
                        print(f"⚠️ 콜백 호출 실패: {e}")
                
                self.save_queue.task_done()
                
            except Exception as e:
                print(f"⚠️ 비동기 저장 워커 오류: {e}")
                time.sleep(1)
    
    def _perform_save_operation(self, operation_type: str, data: Dict[str, Any]) -> bool:
        """실제 저장 작업 수행"""
        try:
            if operation_type == "audio_analysis":
                return self._save_audio_analysis_bulk(data)
            elif operation_type == "quality_analysis":
                return self._save_quality_analysis_bulk(data)
            elif operation_type == "llm_analysis":
                return self._save_llm_analysis_bulk(data)
            else:
                print(f"⚠️ 알 수 없는 작업 타입: {operation_type}")
                return False
                
        except Exception as e:
            print(f"⚠️ 저장 작업 실패: {operation_type}, {e}")
            self._log_recovery(operation_type, str(e), "retry_later")
            return False
    
    def _save_audio_analysis_bulk(self, data_list: List[Dict[str, Any]]) -> bool:
        """오디오 분석 결과 bulk 저장"""
        try:
            if not data_list:
                return True
            
            connection = self.db_manager.get_connection("audio_analysis")
            cursor = connection.cursor()
            
            # Bulk insert 쿼리 구성
            query = None"
                INSERT INTO audio_analysis (
                    file_path, duration, sample_rate, channels, 
                    transcription, language, confidence_score,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # 데이터 준비
            values = []
            current_time = time.time()
            
            for data in data_list:
                values.append((
                    data.get('file_path', ''),
                    data.get('duration', 0.0),
                    data.get('sample_rate', 16000),
                    data.get('channels', 1),
                    data.get('transcription', ''),
                    data.get('language', 'ko'),
                    data.get('confidence_score', 0.0),
                    current_time,
                    current_time
                ))
            
            # Bulk insert 실행
            cursor.executemany(query, values)
            connection.commit()
            
            print(f"✅ 오디오 분석 bulk 저장 완료: {len(data_list)}개")
            return True
            
        except Exception as e:
            print(f"⚠️ 오디오 분석 bulk 저장 실패: {e}")
            self._log_recovery("audio_analysis_bulk_save", str(e), "rollback_and_retry")
            return False
    
    def _save_quality_analysis_bulk(self, data_list: List[Dict[str, Any]]) -> bool:
        """품질 분석 결과 bulk 저장"""
        try:
            if not data_list:
                return True
            
            connection = self.db_manager.get_connection("quality_analysis")
            cursor = connection.cursor()
            
            # Bulk insert 쿼리 구성
            query = None"
                INSERT INTO consultation_quality (
                    audio_analysis_id, clarity_score, politeness_score,
                    empathy_score, professionalism_score, response_quality_score,
                    overall_score, sentiment_analysis, profanity_detected,
                    speaker_classification, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # 데이터 준비
            values = []
            current_time = time.time()
            
            for data in data_list:
                values.append((
                    data.get('audio_analysis_id', 0),
                    data.get('clarity_score', 0.5),
                    data.get('politeness_score', 0.5),
                    data.get('empathy_score', 0.5),
                    data.get('professionalism_score', 0.5),
                    data.get('response_quality_score', 0.5),
                    data.get('overall_score', 0.5),
                    json.dumps(data.get('sentiment_analysis', {}), ensure_ascii=False),
                    data.get('profanity_detected', False),
                    data.get('speaker_classification', '고객'),
                    current_time,
                    current_time
                ))
            
            # Bulk insert 실행
            cursor.executemany(query, values)
            connection.commit()
            
            print(f"✅ 품질 분석 bulk 저장 완료: {len(data_list)}개")
            return True
            
        except Exception as e:
            print(f"⚠️ 품질 분석 bulk 저장 실패: {e}")
            self._log_recovery("quality_analysis_bulk_save", str(e), "rollback_and_retry")
            return False
    
    def _save_llm_analysis_bulk(self, data_list: List[Dict[str, Any]]) -> bool:
        """LLM 분석 결과 bulk 저장"""
        try:
            if not data_list:
                return True
            
            connection = self.db_manager.get_connection("quality_analysis")
            cursor = connection.cursor()
            
            # Bulk insert 쿼리 구성
            query = None"
                INSERT INTO llm_analysis (
                    audio_analysis_id, analysis_type, analysis_result,
                    confidence_score, model_used, processing_time,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # 데이터 준비
            values = []
            current_time = time.time()
            
            for data in data_list:
                values.append((
                    data.get('audio_analysis_id', 0),
                    data.get('analysis_type', 'general'),
                    json.dumps(data.get('analysis_result', {}), ensure_ascii=False),
                    data.get('confidence_score', 0.5),
                    data.get('model_used', 'default'),
                    data.get('processing_time', 0.0),
                    current_time,
                    current_time
                ))
            
            # Bulk insert 실행
            cursor.executemany(query, values)
            connection.commit()
            
            print(f"✅ LLM 분석 bulk 저장 완료: {len(data_list)}개")
            return True
            
        except Exception as e:
            print(f"⚠️ LLM 분석 bulk 저장 실패: {e}")
            self._log_recovery("llm_analysis_bulk_save", str(e), "rollback_and_retry")
            return False
    
    def db_add_to_batch(self, operation_type: str, data: Dict[str, Any]):
        """배치 버퍼에 데이터 추가"""
        if operation_type not in self.batch_buffers:
            print(f"⚠️ 알 수 없는 작업 타입: {operation_type}")
            return
        
        with self.batch_locks[operation_type]:
            self.batch_buffers[operation_type].append(data)
            
            # 배치 크기 도달 시 자동 저장
            if len(self.batch_buffers[operation_type]) >= self.batch_size:
                self.db_flush_batch(operation_type)
    
    def db_flush_batch(self, operation_type: str):
        """배치 버퍼 플러시"""
        if operation_type not in self.batch_buffers:
            return
        
        with self.batch_locks[operation_type]:
            if not self.batch_buffers[operation_type]:
                return
            
            data_list = self.batch_buffers[operation_type].copy()
            self.batch_buffers[operation_type].clear()
        
        # 비동기 저장 또는 즉시 저장
        if self.enable_async:
            self.save_queue.put((operation_type, data_list, None))
        else:
            self._perform_save_operation(operation_type, data_list)
    
    def db_flush_all_batches(self):
        """모든 배치 버퍼 플러시"""
        for operation_type in self.batch_buffers.keys():
            self.db_flush_batch(operation_type)
    
    async def save_audio_analysis_async(self, data: Dict[str, Any], callback=None):
        """비동기 오디오 분석 저장"""
        if self.enable_async:
            self.save_queue.put(("audio_analysis", [data], callback))
        else:
            success = self._perform_save_operation("audio_analysis", [data])
            if callback:
                callback(success, 0.0)
    
    async def save_quality_analysis_async(self, data: Dict[str, Any], callback=None):
        """비동기 품질 분석 저장"""
        if self.enable_async:
            self.save_queue.put(("quality_analysis", [data], callback))
        else:
            success = self._perform_save_operation("quality_analysis", [data])
            if callback:
                callback(success, 0.0)
    
    async def save_llm_analysis_async(self, data: Dict[str, Any], callback=None):
        """비동기 LLM 분석 저장"""
        if self.enable_async:
            self.save_queue.put(("llm_analysis", [data], callback))
        else:
            success = self._perform_save_operation("llm_analysis", [data])
            if callback:
                callback(success, 0.0)
    
    def db_bulk_save_audio_analysis(self, data_list: List[Dict[str, Any]]) -> bool:
        """오디오 분석 결과 bulk 저장"""
        try:
            success = self._perform_save_operation("audio_analysis", data_list)
            if success:
                self.performance_stats["bulk_operations"] += 1
            return success
        except Exception as e:
            print(f"⚠️ Bulk 저장 실패: {e}")
            return False
    
    def db_bulk_save_quality_analysis(self, data_list: List[Dict[str, Any]]) -> bool:
        """품질 분석 결과 bulk 저장"""
        try:
            success = self._perform_save_operation("quality_analysis", data_list)
            if success:
                self.performance_stats["bulk_operations"] += 1
            return success
        except Exception as e:
            print(f"⚠️ Bulk 저장 실패: {e}")
            return False
    
    def db_bulk_save_llm_analysis(self, data_list: List[Dict[str, Any]]) -> bool:
        """LLM 분석 결과 bulk 저장"""
        try:
            success = self._perform_save_operation("llm_analysis", data_list)
            if success:
                self.performance_stats["bulk_operations"] += 1
            return success
        except Exception as e:
            print(f"⚠️ Bulk 저장 실패: {e}")
            return False
    
    def db_get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        return self.performance_stats.copy()
    
    def db_get_recovery_log(self, limit: int = 100) -> List[str]:
        """복구 로그 조회"""
        try:
            if not self.recovery_log_file.exists():
                return []
            
            with open(self.recovery_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return lines[-limit:] if len(lines) > limit else lines
                
        except Exception as e:
            print(f"⚠️ 복구 로그 조회 실패: {e}")
            return []
    
    def db_cleanup(self):
        """리소스 정리"""
        # 모든 배치 플러시
        self.db_flush_all_batches()
        
        # 비동기 저장 워커 종료
        if self.save_queue:
            self.save_queue.put(None)  # 종료 신호
        
        # Executor 종료
        if self.executor:
            self.executor.shutdown(wait=True)
        
        print("✅ AdvancedDatabaseManager 정리 완료")

class SimplifiedDBManager:
    """간소화된 DB 관리자"""
    
    def __init__(self, connection_params: Dict[str, str]):
        self.connection_params = connection_params
        self.conn: Optional[connection] = None
        
    def db_connect(self) -> connection:
        """DB 연결"""
        try:
            if not self.conn or self.conn.closed:
                self.conn = psycopg2.db_connect(**self.connection_params)
                self.conn.autocommit = False
            return self.conn
        except Exception as e:
            logger.error(f"DB 연결 실패: {e}")
            raise
    
    def db_disconnect(self):
        """DB 연결 해제"""
        if self.conn and not self.conn.closed:
            self.conn.close()
    
    def db_save_consultation_classification(self, 
                                       audio_file_id: int,
                                       classification_result: Dict[str, Any],
                                       session_date: date = None) -> int:
        """상담 분류 결과 저장"""
        try:
            conn = self.db_connect()
            cursor = conn.cursor()
            
            # 기본값 설정
            if session_date is None:
                session_date = date.today()
            
            # consultation_sessions 테이블에 저장
            insert_query = None"
                INSERT INTO consultation_sessions (
                    audio_file_id, session_date, duration_minutes,
                    business_area, consultation_subject, consultation_requirement,
                    consultation_content, consultation_reason, consultation_result,
                    overall_quality_score, analysis_status, analysis_completed_at,
                    summary, key_issues, resolution_status, customer_satisfaction_score
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """
            
            cursor.execute(insert_query, (
                audio_file_id,
                session_date,
                classification_result.get('duration_minutes', 0.0),
                classification_result.get('business_area', '기타'),
                classification_result.get('consultation_subject', '기타'),
                classification_result.get('consultation_requirement', '단일 요건 민원'),
                classification_result.get('consultation_content', '일반 문의 상담'),
                classification_result.get('consultation_reason', '민원인'),
                classification_result.get('consultation_result', '추가상담필요'),
                classification_result.get('overall_quality_score', 0.0),
                'completed',
                get_current_time(),
                classification_result.get('summary', ''),
                json.dumps(classification_result.get('key_issues', {}), ensure_ascii=False),
                classification_result.get('resolution_status', 'unresolved'),
                classification_result.get('customer_satisfaction_score', 0.0)
            ))
            
            session_id = cursor.fetchone()[0]
            conn.commit()
            
            logger.info(f"상담 분류 결과 저장 완료: session_id={session_id}")
            return session_id
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"상담 분류 결과 저장 실패: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def db_save_quality_metrics(self, session_id: int, metrics: Dict[str, float]):
        """품질 지표 저장"""
        try:
            conn = self.db_connect()
            cursor = conn.cursor()
            
            # 기존 지표 삭제
            cursor.execute("DELETE FROM quality_metrics WHERE session_id = %s", (session_id,))
            
            # 새 지표 저장
            for metric_name, metric_value in metrics.items():
                insert_query = None"
                    INSERT INTO quality_metrics (
                        session_id, metric_name, metric_value, metric_description, category
                    ) VALUES (%s, %s, %s, %s, %s)
                """
                
                cursor.execute(insert_query, (
                    session_id,
                    metric_name,
                    metric_value,
                    f"{metric_name} 지표",
                    'communication'  # 기본 카테고리
                ))
            
            conn.commit()
            logger.info(f"품질 지표 저장 완료: session_id={session_id}")
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"품질 지표 저장 실패: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def db_save_sentiment_analysis(self, session_id: int, sentiment_data: List[Dict[str, Any]]):
        """감정 분석 결과 저장"""
        try:
            conn = self.db_connect()
            cursor = conn.cursor()
            
            # 기존 감정 분석 삭제
            cursor.execute("DELETE FROM sentiment_analysis WHERE session_id = %s", (session_id,))
            
            # 새 감정 분석 저장
            for sentiment in sentiment_data:
                insert_query = None"
                    INSERT INTO sentiment_analysis (
                        session_id, speaker_type, time_segment_start, time_segment_end,
                        sentiment_score, emotion_category, confidence, emotion_intensity
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(insert_query, (
                    session_id,
                    sentiment.get('speaker_type', 'unknown'),
                    sentiment.get('time_segment_start', 0.0),
                    sentiment.get('time_segment_end', 0.0),
                    sentiment.get('sentiment_score', 0.0),
                    sentiment.get('emotion_category', 'neutral'),
                    sentiment.get('confidence', 0.0),
                    sentiment.get('emotion_intensity', 0.0)
                ))
            
            conn.commit()
            logger.info(f"감정 분석 저장 완료: session_id={session_id}")
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"감정 분석 저장 실패: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def db_get_consultation_summary(self, session_id: int) -> Dict[str, Any]:
        """상담 요약 정보 조회"""
        try:
            conn = self.db_connect()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            query = None"
                SELECT 
                    cs.*,
                    af.file_name,
                    af.duration_seconds,
                    COUNT(qm.id) as metrics_count,
                    COUNT(sa.id) as sentiment_count
                FROM consultation_sessions cs
                LEFT JOIN audio_files af ON cs.audio_file_id = af.id
                LEFT JOIN quality_metrics qm ON cs.id = qm.session_id
                LEFT JOIN sentiment_analysis sa ON cs.id = sa.session_id
                WHERE cs.id = %s
                GROUP BY cs.id, af.file_name, af.duration_seconds
            """
            
            cursor.execute(query, (session_id,))
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            else:
                return {}
                
        except Exception as e:
            logger.error(f"상담 요약 조회 실패: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def db_get_business_area_statistics(self) -> List[Dict[str, Any]]:
        """업무 분야별 통계 조회"""
        try:
            conn = self.db_connect()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            query = None"
                SELECT 
                    business_area,
                    COUNT(*) as total_sessions,
                    AVG(overall_quality_score) as avg_quality_score,
                    AVG(customer_satisfaction_score) as avg_satisfaction,
                    AVG(duration_minutes) as avg_duration,
                    COUNT(CASE WHEN resolution_status = 'resolved' THEN 1 END) as resolved_count,
                    COUNT(CASE WHEN resolution_status = 'unresolved' THEN 1 END) as unresolved_count
                FROM consultation_sessions
                WHERE business_area IS NOT NULL
                GROUP BY business_area
                ORDER BY total_sessions DESC
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"업무 분야 통계 조회 실패: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def db_get_classification_accuracy_report(self) -> Dict[str, Any]:
        """분류 정확도 리포트"""
        try:
            conn = self.db_connect()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # 상담 주제별 분포
            subject_query = None"
                SELECT 
                    consultation_subject,
                    COUNT(*) as count,
                    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
                FROM consultation_sessions
                WHERE consultation_subject IS NOT NULL
                GROUP BY consultation_subject
                ORDER BY count DESC
            """
            
            cursor.execute(subject_query)
            subject_stats = [dict(row) for row in cursor.fetchall()]
            
            # 상담 결과별 분포
            result_query = None"
                SELECT 
                    consultation_result,
                    COUNT(*) as count,
                    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
                FROM consultation_sessions
                WHERE consultation_result IS NOT NULL
                GROUP BY consultation_result
                ORDER BY count DESC
            """
            
            cursor.execute(result_query)
            result_stats = [dict(row) for row in cursor.fetchall()]
            
            # 전체 통계
            total_query = None"
                SELECT 
                    COUNT(*) as total_sessions,
                    AVG(overall_quality_score) as avg_quality,
                    AVG(customer_satisfaction_score) as avg_satisfaction,
                    COUNT(CASE WHEN resolution_status = 'resolved' THEN 1 END) as resolved_count
                FROM consultation_sessions
            """
            
            cursor.execute(total_query)
            total_stats = dict(cursor.fetchone())
            
            return {
                'total_statistics': total_stats,
                'subject_distribution': subject_stats,
                'result_distribution': result_stats
            }
            
        except Exception as e:
            logger.error(f"분류 정확도 리포트 조회 실패: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def db_update_audio_processing_status(self, audio_file_id: int, status: str, error_message: str = None):
        """오디오 처리 상태 업데이트"""
        try:
            conn = self.db_connect()
            cursor = conn.cursor()
            
            if status == 'completed':
                query = None"
                    UPDATE audio_files 
                    SET processing_status = %s, processing_completed_at = %s
                    WHERE id = %s
                """
                cursor.execute(query, (status, get_current_time(), audio_file_id))
            else:
                query = None"
                    UPDATE audio_files 
                    SET processing_status = %s, error_message = %s
                    WHERE id = %s
                """
                cursor.execute(query, (status, error_message, audio_file_id))
            
            conn.commit()
            logger.info(f"오디오 처리 상태 업데이트: audio_file_id={audio_file_id}, status={status}")
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"오디오 처리 상태 업데이트 실패: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

# 사용 예시
if __name__ == "__main__":
    # DB 연결 설정
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'callytics',
        'user': 'callytics_user',
        'password': '1234'
    }
    
    db_manager = SimplifiedDBManager(db_config)
    
    # 테스트 데이터
    classification_result = {
        'business_area': '요금제 변경',
        'consultation_subject': '주문/결제/확인',
        'consultation_requirement': '단일 요건 민원',
        'consultation_content': '업무 처리 상담',
        'consultation_reason': '민원인',
        'consultation_result': '만족',
        'overall_quality_score': 0.85,
        'customer_satisfaction_score': 0.9,
        'duration_minutes': 5.5,
        'summary': '요금제 변경 요청으로 만족스러운 상담 완료',
        'key_issues': {'main_issue': '요금제 변경', 'resolution': '성공'}
    }
    
    try:
        # 상담 분류 결과 저장
        session_id = db_manager.db_save_consultation_classification(1, classification_result)
        print(f"상담 분류 결과 저장 완료: session_id={session_id}")
        
        # 요약 정보 조회
        summary = db_manager.db_get_consultation_summary(session_id)
        print(f"상담 요약: {summary}")
        
        # 업무 분야 통계 조회
        stats = db_manager.db_get_business_area_statistics()
        print(f"업무 분야 통계: {stats}")
        
    finally:
        db_manager.db_disconnect() 