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

# Local imports
from src.db.multi_database_manager import MultiDatabaseManager


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
            query = """
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
            query = """
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
            query = """
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
    
    def add_to_batch(self, operation_type: str, data: Dict[str, Any]):
        """배치 버퍼에 데이터 추가"""
        if operation_type not in self.batch_buffers:
            print(f"⚠️ 알 수 없는 작업 타입: {operation_type}")
            return
        
        with self.batch_locks[operation_type]:
            self.batch_buffers[operation_type].append(data)
            
            # 배치 크기 도달 시 자동 저장
            if len(self.batch_buffers[operation_type]) >= self.batch_size:
                self.flush_batch(operation_type)
    
    def flush_batch(self, operation_type: str):
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
    
    def flush_all_batches(self):
        """모든 배치 버퍼 플러시"""
        for operation_type in self.batch_buffers.keys():
            self.flush_batch(operation_type)
    
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
    
    def bulk_save_audio_analysis(self, data_list: List[Dict[str, Any]]) -> bool:
        """오디오 분석 결과 bulk 저장"""
        try:
            success = self._perform_save_operation("audio_analysis", data_list)
            if success:
                self.performance_stats["bulk_operations"] += 1
            return success
        except Exception as e:
            print(f"⚠️ Bulk 저장 실패: {e}")
            return False
    
    def bulk_save_quality_analysis(self, data_list: List[Dict[str, Any]]) -> bool:
        """품질 분석 결과 bulk 저장"""
        try:
            success = self._perform_save_operation("quality_analysis", data_list)
            if success:
                self.performance_stats["bulk_operations"] += 1
            return success
        except Exception as e:
            print(f"⚠️ Bulk 저장 실패: {e}")
            return False
    
    def bulk_save_llm_analysis(self, data_list: List[Dict[str, Any]]) -> bool:
        """LLM 분석 결과 bulk 저장"""
        try:
            success = self._perform_save_operation("llm_analysis", data_list)
            if success:
                self.performance_stats["bulk_operations"] += 1
            return success
        except Exception as e:
            print(f"⚠️ Bulk 저장 실패: {e}")
            return False
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        return self.performance_stats.copy()
    
    def get_recovery_log(self, limit: int = 100) -> List[str]:
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
    
    def cleanup(self):
        """리소스 정리"""
        # 모든 배치 플러시
        self.flush_all_batches()
        
        # 비동기 저장 워커 종료
        if self.save_queue:
            self.save_queue.put(None)  # 종료 신호
        
        # Executor 종료
        if self.executor:
            self.executor.shutdown(wait=True)
        
        print("✅ AdvancedDatabaseManager 정리 완료") 