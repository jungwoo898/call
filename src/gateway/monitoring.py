#!/usr/bin/env python3
"""
모니터링 및 로깅 시스템
Prometheus 메트릭 수집 및 중앙화된 로깅
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
import structlog
from structlog.stdlib import LoggerFactory

# Prometheus 메트릭 정의
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
SERVICE_CALL_COUNT = Counter('service_calls_total', 'Total service calls', ['service_name', 'status'])
SERVICE_CALL_DURATION = Histogram('service_call_duration_seconds', 'Service call duration', ['service_name'])
QUEUE_MESSAGE_COUNT = Counter('queue_messages_total', 'Total queue messages', ['topic', 'status'])
ACTIVE_SAGAS = Gauge('active_sagas', 'Number of active sagas')
PROCESSING_TIME = Summary('processing_time_seconds', 'Processing time for audio analysis')

class MonitoringMiddleware:
    """FastAPI 미들웨어 - 요청/응답 모니터링"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        # 요청 정보 추출
        method = scope.get('method', 'UNKNOWN')
        path = scope.get('path', '/')
        
        # 원본 send 함수 래핑
        async def send_wrapper(message):
            if message['type'] == 'http.response.start':
                status = message.get('status', 500)
                REQUEST_COUNT.labels(method=method, endpoint=path, status=status).inc()
                
                duration = time.time() - start_time
                REQUEST_DURATION.labels(method=method, endpoint=path).observe(duration)
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)

class ServiceMonitor:
    """서비스 모니터링"""
    
    def __init__(self):
        self.service_health = {}
        self.last_check = {}
    
    def record_service_call(self, service_name: str, duration: float, success: bool):
        """서비스 호출 기록"""
        status = 'success' if success else 'failed'
        SERVICE_CALL_COUNT.labels(service_name=service_name, status=status).inc()
        SERVICE_CALL_DURATION.labels(service_name=service_name).observe(duration)
    
    def record_queue_message(self, topic: str, status: str):
        """큐 메시지 기록"""
        QUEUE_MESSAGE_COUNT.labels(topic=topic, status=status).inc()
    
    def update_saga_count(self, count: int):
        """Saga 개수 업데이트"""
        ACTIVE_SAGAS.set(count)
    
    def record_processing_time(self, duration: float):
        """처리 시간 기록"""
        PROCESSING_TIME.observe(duration)

class CentralizedLogger:
    """중앙화된 로깅 시스템"""
    
    def __init__(self, service_name: str, log_level: str = "INFO"):
        self.service_name = service_name
        
        # structlog 설정
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        self.logger = structlog.get_logger()
        
        # 로그 레벨 설정
        logging.basicConfig(level=getattr(logging, log_level.upper()))
    
    def log_request(self, request: Request, response: Response, duration: float):
        """HTTP 요청 로깅"""
        self.logger.info(
            "HTTP Request",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            duration=duration,
            user_agent=request.headers.get("user-agent"),
            client_ip=request.client.host if request.client else None
        )
    
    def log_service_call(self, service_name: str, endpoint: str, duration: float, success: bool, error: Optional[str] = None):
        """서비스 호출 로깅"""
        self.logger.info(
            "Service Call",
            service=service_name,
            endpoint=endpoint,
            duration=duration,
            success=success,
            error=error
        )
    
    def log_saga_event(self, saga_id: str, step_name: str, status: str, duration: Optional[float] = None, error: Optional[str] = None):
        """Saga 이벤트 로깅"""
        self.logger.info(
            "Saga Event",
            saga_id=saga_id,
            step=step_name,
            status=status,
            duration=duration,
            error=error
        )
    
    def log_queue_event(self, topic: str, message_id: str, event_type: str, data: Optional[Dict[str, Any]] = None):
        """큐 이벤트 로깅"""
        self.logger.info(
            "Queue Event",
            topic=topic,
            message_id=message_id,
            event_type=event_type,
            data=data
        )
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """에러 로깅"""
        self.logger.error(
            "Error occurred",
            error_type=type(error).__name__,
            error_message=str(error),
            context=context or {}
        )
    
    def log_metric(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """메트릭 로깅"""
        self.logger.info(
            "Metric",
            metric=metric_name,
            value=value,
            labels=labels or {}
        )

class HealthChecker:
    """헬스체크 관리"""
    
    def __init__(self, services: Dict[str, str]):
        self.services = services
        self.health_status = {}
        self.last_check = {}
    
    async def check_all_services(self) -> Dict[str, Any]:
        """모든 서비스 헬스체크"""
        import httpx
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            tasks = []
            for service_name, url in self.services.items():
                task = asyncio.create_task(self._check_service(client, service_name, url))
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, (service_name, _) in enumerate(self.services.items()):
                if isinstance(results[i], Exception):
                    self.health_status[service_name] = {
                        'status': 'unhealthy',
                        'error': str(results[i]),
                        'last_check': time.time()
                    }
                else:
                    self.health_status[service_name] = results[i]
        
        return self.health_status
    
    async def _check_service(self, client: httpx.AsyncClient, service_name: str, url: str) -> Dict[str, Any]:
        """개별 서비스 헬스체크"""
        try:
            start_time = time.time()
            response = await client.get(f"{url}/health")
            duration = time.time() - start_time
            
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'response_time': duration,
                    'last_check': time.time()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'response_time': duration,
                    'error': f"HTTP {response.status_code}",
                    'last_check': time.time()
                }
                
        except Exception as e:
            return {
                'status': 'unreachable',
                'error': str(e),
                'last_check': time.time()
            }

class MetricsExporter:
    """메트릭 내보내기"""
    
    @staticmethod
    async def get_metrics() -> Response:
        """Prometheus 메트릭 내보내기"""
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    
    @staticmethod
    def get_service_metrics() -> Dict[str, Any]:
        """서비스별 메트릭 수집"""
        return {
            'http_requests': {
                'total': REQUEST_COUNT._value.sum(),
                'duration_avg': REQUEST_DURATION.observe(0),  # 평균 계산 필요
            },
            'service_calls': {
                'total': SERVICE_CALL_COUNT._value.sum(),
                'duration_avg': SERVICE_CALL_DURATION.observe(0),
            },
            'queue_messages': {
                'total': QUEUE_MESSAGE_COUNT._value.sum(),
            },
            'sagas': {
                'active': ACTIVE_SAGAS._value.get(),
            },
            'processing': {
                'avg_time': PROCESSING_TIME.observe(0),
            }
        }

# 전역 인스턴스들
service_monitor = ServiceMonitor()
centralized_logger = CentralizedLogger("gateway")
health_checker = HealthChecker({})  # 서비스 URL은 나중에 설정
metrics_exporter = MetricsExporter() 