#!/usr/bin/env python3
"""
Redis 기반 메시지 큐 시스템
비동기 처리 및 메시지 손실 방지
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict
from enum import Enum
import redis.asyncio as redis
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MessageStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"

@dataclass
class Message:
    """메시지 구조"""
    id: str
    topic: str
    data: Dict[str, Any]
    status: MessageStatus
    created_at: float
    processed_at: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    error: Optional[str] = None
    priority: int = 0  # 높을수록 우선순위 높음

class MessageQueue:
    """Redis 기반 메시지 큐"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.consumers: Dict[str, Callable] = {}
        self.processing_tasks: Dict[str, asyncio.Task] = {}
        
    async def connect(self):
        """Redis 연결"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Redis 연결 성공")
        except Exception as e:
            logger.error(f"Redis 연결 실패: {e}")
            raise
    
    async def disconnect(self):
        """Redis 연결 해제"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis 연결 해제")
    
    async def publish(self, topic: str, data: Dict[str, Any], priority: int = 0) -> str:
        """
        메시지 발행
        
        Parameters
        ----------
        topic : str
            토픽명
        data : Dict[str, Any]
            메시지 데이터
        priority : int
            우선순위 (높을수록 우선)
            
        Returns
        -------
        str
            메시지 ID
        """
        
        if not self.redis_client:
            raise RuntimeError("Redis 연결이 필요합니다")
        
        message = Message(
            id=str(uuid.uuid4()),
            topic=topic,
            data=data,
            status=MessageStatus.PENDING,
            created_at=time.time(),
            priority=priority
        )
        
        # Redis에 메시지 저장
        message_key = f"message:{message.id}"
        await self.redis_client.hset(message_key, mapping=asdict(message))
        
        # 우선순위를 고려한 큐에 추가
        queue_key = f"queue:{topic}"
        score = priority * 1000000 + time.time()  # 우선순위 + 타임스탬프
        await self.redis_client.zadd(queue_key, {message.id: score})
        
        # 메시지 만료 시간 설정 (24시간)
        await self.redis_client.expire(message_key, 86400)
        
        logger.info(f"메시지 발행: {message.id} -> {topic}")
        return message.id
    
    async def subscribe(self, topic: str, handler: Callable):
        """
        토픽 구독
        
        Parameters
        ----------
        topic : str
            구독할 토픽
        handler : Callable
            메시지 처리 함수
        """
        self.consumers[topic] = handler
        logger.info(f"토픽 구독: {topic}")
    
    async def start_consuming(self, topic: str, batch_size: int = 10, poll_interval: float = 1.0):
        """
        메시지 소비 시작
        
        Parameters
        ----------
        topic : str
            소비할 토픽
        batch_size : int
            배치 크기
        poll_interval : float
            폴링 간격 (초)
        """
        
        if topic not in self.consumers:
            raise ValueError(f"토픽 {topic}에 대한 핸들러가 등록되지 않았습니다")
        
        handler = self.consumers[topic]
        queue_key = f"queue:{topic}"
        
        logger.info(f"메시지 소비 시작: {topic}")
        
        while True:
            try:
                # 대기 중인 메시지 조회 (우선순위 순)
                message_ids = await self.redis_client.zrange(queue_key, 0, batch_size - 1)
                
                if not message_ids:
                    await asyncio.sleep(poll_interval)
                    continue
                
                # 메시지 처리
                for message_id in message_ids:
                    if message_id in self.processing_tasks:
                        continue  # 이미 처리 중
                    
                    # 메시지 정보 조회
                    message_key = f"message:{message_id.decode()}"
                    message_data = await self.redis_client.hgetall(message_key)
                    
                    if not message_data:
                        # 메시지가 삭제된 경우 큐에서 제거
                        await self.redis_client.zrem(queue_key, message_id)
                        continue
                    
                    # Message 객체로 변환
                    message = Message(
                        id=message_data[b'id'].decode(),
                        topic=message_data[b'topic'].decode(),
                        data=json.loads(message_data[b'data'].decode()),
                        status=MessageStatus(message_data[b'status'].decode()),
                        created_at=float(message_data[b'created_at'].decode()),
                        retry_count=int(message_data[b'retry_count'].decode()),
                        max_retries=int(message_data[b'max_retries'].decode()),
                        priority=int(message_data[b'priority'].decode())
                    )
                    
                    # 처리 태스크 시작
                    task = asyncio.create_task(self._process_message(message, handler))
                    self.processing_tasks[message_id.decode()] = task
                
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                logger.error(f"메시지 소비 중 오류: {e}")
                await asyncio.sleep(poll_interval)
    
    async def _process_message(self, message: Message, handler: Callable):
        """개별 메시지 처리"""
        
        try:
            # 메시지 상태를 처리 중으로 변경
            await self._update_message_status(message.id, MessageStatus.PROCESSING)
            
            # 핸들러 실행
            result = await handler(message.data)
            
            # 성공 시 메시지 완료
            await self._update_message_status(message.id, MessageStatus.COMPLETED, result=result)
            
            # 큐에서 메시지 제거
            queue_key = f"queue:{message.topic}"
            await self.redis_client.zrem(queue_key, message.id)
            
            logger.info(f"메시지 처리 완료: {message.id}")
            
        except Exception as e:
            logger.error(f"메시지 처리 실패: {message.id} - {e}")
            
            # 재시도 로직
            if message.retry_count < message.max_retries:
                message.retry_count += 1
                await self._update_message_status(message.id, MessageStatus.RETRY, error=str(e))
                
                # 지수 백오프로 재시도
                retry_delay = 2 ** message.retry_count
                await asyncio.sleep(retry_delay)
                
                # 큐에 다시 추가
                queue_key = f"queue:{message.topic}"
                score = message.priority * 1000000 + time.time()
                await self.redis_client.zadd(queue_key, {message.id: score})
                
            else:
                # 최대 재시도 횟수 초과
                await self._update_message_status(message.id, MessageStatus.FAILED, error=str(e))
                
                # 실패한 메시지는 별도 큐로 이동
                failed_queue_key = f"failed:{message.topic}"
                await self.redis_client.lpush(failed_queue_key, message.id)
        
        finally:
            # 처리 태스크 정리
            if message.id in self.processing_tasks:
                del self.processing_tasks[message.id]
    
    async def _update_message_status(self, message_id: str, status: MessageStatus, 
                                   result: Optional[Dict[str, Any]] = None, 
                                   error: Optional[str] = None):
        """메시지 상태 업데이트"""
        
        message_key = f"message:{message_id}"
        updates = {
            'status': status.value,
            'processed_at': time.time()
        }
        
        if result:
            updates['result'] = json.dumps(result)
        
        if error:
            updates['error'] = error
        
        await self.redis_client.hset(message_key, mapping=updates)
    
    async def get_message_status(self, message_id: str) -> Optional[Dict[str, Any]]:
        """메시지 상태 조회"""
        
        if not self.redis_client:
            return None
        
        message_key = f"message:{message_id}"
        message_data = await self.redis_client.hgetall(message_key)
        
        if not message_data:
            return None
        
        return {
            'id': message_data[b'id'].decode(),
            'topic': message_data[b'topic'].decode(),
            'status': message_data[b'status'].decode(),
            'created_at': float(message_data[b'created_at'].decode()),
            'processed_at': float(message_data[b'processed_at'].decode()) if b'processed_at' in message_data else None,
            'retry_count': int(message_data[b'retry_count'].decode()),
            'error': message_data[b'error'].decode() if b'error' in message_data else None
        }
    
    async def get_queue_stats(self, topic: str) -> Dict[str, Any]:
        """큐 통계 조회"""
        
        if not self.redis_client:
            return {}
        
        queue_key = f"queue:{topic}"
        failed_queue_key = f"failed:{topic}"
        
        pending_count = await self.redis_client.zcard(queue_key)
        failed_count = await self.redis_client.llen(failed_queue_key)
        
        return {
            'topic': topic,
            'pending_messages': pending_count,
            'failed_messages': failed_count,
            'processing_tasks': len([t for t in self.processing_tasks.values() if not t.done()])
        }

# 전역 메시지 큐 인스턴스
message_queue = MessageQueue() 