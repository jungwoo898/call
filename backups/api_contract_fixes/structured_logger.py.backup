#!/usr/bin/env python3
"""
구조화된 로깅 시스템
JSON 형식, 성능 추적, 오류 분석, 감사 로그 지원
"""

import os
import json
import logging
import logging.handlers
import traceback
import time
from typing import Dict, Any, Optional, Union, List
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from contextlib import contextmanager
from enum import Enum
import threading
import uuid

class LogLevel(Enum):
    """로그 레벨"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogType(Enum):
    """로그 타입"""
    APPLICATION = "application"
    ACCESS = "access"
    AUDIT = "audit"
    PERFORMANCE = "performance"
    SECURITY = "security"
    BUSINESS = "business"

@dataclass
class LogContext:
    """로그 컨텍스트"""
    service_name: str
    service_version: str = "1.0.0"
    environment: str = "development"
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None

@dataclass
class PerformanceMetrics:
    """성능 메트릭"""
    duration_ms: float
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    db_query_count: Optional[int] = None
    cache_hit_count: Optional[int] = None
    cache_miss_count: Optional[int] = None

class StructuredLogger:
    """구조화된 로거"""
    
    def __init__(self, 
                 service_name: str,
                 log_level: str = "INFO",
                 output_format: str = "json",
                 enable_console: bool = True,
                 enable_file: bool = True,
                 log_file_path: str = None,
                 max_file_size: int = 100 * 1024 * 1024,  # 100MB
                 backup_count: int = 5):
        """구조화된 로거 초기화"""
        self.service_name = service_name
        self.output_format = output_format
        self.enable_console = enable_console
        self.enable_file = enable_file
        
        # 기본 컨텍스트 설정
        self.base_context = LogContext(
            service_name=service_name,
            service_version=os.getenv("SERVICE_VERSION", "1.0.0"),
            environment=os.getenv("ENVIRONMENT", "development")
        )
        
        # 스레드 로컬 컨텍스트
        self._local = threading.local()
        
        # 로거 설정
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        self.logger.handlers.clear()  # 기존 핸들러 제거
        
        # 핸들러 설정
        self._setup_handlers(log_file_path, max_file_size, backup_count)
        
        # 성능 메트릭 추적
        self.performance_metrics = {}
        
    def _setup_handlers(self, log_file_path: str, max_file_size: int, backup_count: int):
        """로그 핸들러 설정"""
        formatter = self._create_formatter()
        
        # 콘솔 핸들러
        if self.enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # 파일 핸들러
        if self.enable_file:
            if log_file_path is None:
                log_file_path = f"logs/{self.service_name}.log"
            
            # 로그 디렉토리 생성
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file_path,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def _create_formatter(self):
        """로그 포매터 생성"""
        if self.output_format == "json":
            return JSONFormatter()
        else:
            return logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
    
    def util_set_context(self, **kwargs):
        """현재 스레드의 로그 컨텍스트 설정"""
        if not hasattr(self._local, 'context'):
            self._local.context = {}
        
        self._local.context.update(kwargs)
    
    def util_get_context(self) -> Dict[str, Any]:
        """현재 스레드의 로그 컨텍스트 반환"""
        base_context = asdict(self.base_context)
        
        if hasattr(self._local, 'context'):
            base_context.update(self._local.context)
        
        return base_context
    
    def util_clear_context(self):
        """현재 스레드의 로그 컨텍스트 초기화"""
        if hasattr(self._local, 'context'):
            self._local.context.clear()
    
    def _create_log_record(self, 
                          level: LogLevel, 
                          message: str, 
                          log_type: LogType = LogType.APPLICATION,
                          extra_data: Dict[str, Any] = None,
                          error: Exception = None,
                          performance_metrics: PerformanceMetrics = None) -> Dict[str, Any]:
        """로그 레코드 생성"""
        
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.value,
            "log_type": log_type.value,
            "message": message,
            **self.util_get_context()
        }
        
        # 추가 데이터
        if extra_data:
            record["data"] = extra_data
        
        # 에러 정보
        if error:
            record["error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc()
            }
        
        # 성능 메트릭
        if performance_metrics:
            record["metrics"] = asdict(performance_metrics)
        
        return record
    
    def util_info(self, message: str, **kwargs):
        """정보 로그"""
        record = self._create_log_record(LogLevel.INFO, message, **kwargs)
        self.logger.util_info(json.dumps(record, ensure_ascii=False))
    
    def util_error(self, message: str, error: Exception = None, **kwargs):
        """에러 로그"""
        record = self._create_log_record(LogLevel.ERROR, message, error=error, **kwargs)
        self.logger.util_error(json.dumps(record, ensure_ascii=False))
    
    @contextmanager
    def util_performance_context(self, operation: str, **kwargs):
        """성능 측정 컨텍스트 매니저"""
        start_time = time.time()
        
        try:
            yield
        except Exception as e:
            self.util_error(f"Operation failed: {operation}", error=e, **kwargs)
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            
            metrics = PerformanceMetrics(duration_ms=duration_ms)
            
            record = self._create_log_record(
                LogLevel.INFO,
                f"Performance: {operation} completed in {duration_ms}ms",
                log_type=LogType.PERFORMANCE,
                performance_metrics=metrics,
                **kwargs
            )
            self.logger.util_info(json.dumps(record, ensure_ascii=False))

class JSONFormatter(logging.Formatter):
    """JSON 포매터"""
    
    def util_format(self, record: logging.LogRecord) -> str:
        """로그 레코드를 JSON 형식으로 포매팅"""
        try:
            # 이미 JSON 문자열인 경우 그대로 반환
            if hasattr(record, 'msg') and isinstance(record.msg, str):
                try:
                    json.loads(record.msg)
                    return record.msg
                except (json.JSONDecodeError, ValueError):
                    pass
            
            # 일반 로그 메시지를 JSON으로 변환
            log_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            
            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)
            
            return json.dumps(log_data, ensure_ascii=False)
            
        except Exception as e:
            # 포매팅 실패 시 기본 포맷 사용
            return f"{{\"timestamp\": \"{datetime.now(timezone.utc).isoformat()}\", \"level\": \"ERROR\", \"message\": \"Logging format error: {str(e)}\"}}"

# 전역 로거 인스턴스들
_loggers: Dict[str, StructuredLogger] = {}

def util_get_logger(service_name: str, **kwargs) -> StructuredLogger:
    """구조화된 로거 인스턴스 반환"""
    if service_name not in _loggers:
        _loggers[service_name] = StructuredLogger(service_name, **kwargs)
    return _loggers[service_name]

def util_setup_logging_for_service(service_name: str, **kwargs) -> StructuredLogger:
    """서비스용 로깅 설정"""
    logger = util_get_logger(service_name, **kwargs)
    
    # 환경별 로그 레벨 설정
    environment = os.getenv("ENVIRONMENT", "development")
    if environment == "production":
        logger.logger.setLevel(logging.INFO)
    elif environment == "development":
        logger.logger.setLevel(logging.DEBUG)
    else:
        logger.logger.setLevel(logging.WARNING)
    
    return logger 