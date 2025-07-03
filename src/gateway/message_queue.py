#!/usr/bin/env python3
"""
메시지 큐 시스템
Redis 기반 비동기 메시지 처리
"""

import asyncio
import logging
import json
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class Message:
    """메시지 구조"""
    id: str
    topic: str
    data: Dict[str, Any]
    priority: int = 1
    timestamp: float = None
    retry_count: int = 0
    max_retries: int = 3

class MessageQueue:
    """메시지 큐 관리자"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.queues: Dict[str, List[Message]] = {}
        self.processing_messages: Dict[str, Message] = {}
        self.consumers: Dict[str, List[callable]] = {}
        
        # 메트릭
        self.metrics = {
            "published": 0,
            "consumed": 0,
            "failed": 0,
            "retried": 0
        }
    
    async def connect(self):
        """Redis 연결"""
        try:
            # 실제 Redis 연결은 여기에 구현
            # 현재는 메모리 기반 큐 사용
            logger.info("메시지 큐 초기화 완료")
        except Exception as e:
            logger.warning(f"Redis 연결 실패, 메모리 큐 사용: {e}")
    
    async def disconnect(self):
        """연결 해제"""
        logger.info("메시지 큐 연결 해제")
    
    async def publish(self, topic: str, data: Dict[str, Any], priority: int = 1) -> str:
        """메시지 발행"""
        message_id = str(uuid.uuid4())
        message = Message(
            id=message_id,
            topic=topic,
            data=data,
            priority=priority,
            timestamp=asyncio.get_event_loop().time()
        )
        
        # 큐 초기화
        if topic not in self.queues:
            self.queues[topic] = []
        
        # 우선순위에 따라 삽입
        self.queues[topic].append(message)
        self.queues[topic].sort(key=lambda x: x.priority, reverse=True)
        
        self.metrics["published"] += 1
        logger.info(f"메시지 발행: {topic} - {message_id}")
        
        return message_id
    
    async def subscribe(self, topic: str, callback: callable):
        """메시지 구독"""
        if topic not in self.consumers:
            self.consumers[topic] = []
        self.consumers[topic].append(callback)
        logger.info(f"메시지 구독: {topic}")
    
    async def consume(self, topic: str) -> Optional[Message]:
        """메시지 소비"""
        if topic not in self.queues or not self.queues[topic]:
            return None
        
        message = self.queues[topic].pop(0)
        self.processing_messages[message.id] = message
        
        self.metrics["consumed"] += 1
        logger.info(f"메시지 소비: {topic} - {message.id}")
        
        return message
    
    async def acknowledge(self, message_id: str):
        """메시지 확인"""
        if message_id in self.processing_messages:
            del self.processing_messages[message_id]
            logger.info(f"메시지 확인: {message_id}")
    
    async def reject(self, message_id: str, requeue: bool = True):
        """메시지 거부"""
        if message_id in self.processing_messages:
            message = self.processing_messages[message_id]
            
            if requeue and message.retry_count < message.max_retries:
                message.retry_count += 1
                message.timestamp = asyncio.get_event_loop().time()
                
                # 재시도 대기 시간 (지수 백오프)
                await asyncio.sleep(2 ** message.retry_count)
                
                # 큐에 다시 추가
                if message.topic in self.queues:
                    self.queues[message.topic].append(message)
                    self.queues[message.topic].sort(key=lambda x: x.priority, reverse=True)
                
                self.metrics["retried"] += 1
                logger.info(f"메시지 재시도: {message_id} (시도 {message.retry_count})")
            else:
                self.metrics["failed"] += 1
                logger.warning(f"메시지 최종 실패: {message_id}")
            
            del self.processing_messages[message_id]
    
    async def get_queue_stats(self, topic: str) -> Dict[str, Any]:
        """큐 통계 조회"""
        queue_size = len(self.queues.get(topic, []))
        processing_size = len([m for m in self.processing_messages.values() if m.topic == topic])
        
        return {
            "topic": topic,
            "queue_size": queue_size,
            "processing_size": processing_size,
            "total_messages": queue_size + processing_size,
            "metrics": self.metrics.copy()
        }
    
    async def purge_queue(self, topic: str):
        """큐 비우기"""
        if topic in self.queues:
            self.queues[topic].clear()
            logger.info(f"큐 비우기: {topic}")
    
    async def get_message(self, message_id: str) -> Optional[Message]:
        """메시지 조회"""
        # 처리 중인 메시지에서 찾기
        if message_id in self.processing_messages:
            return self.processing_messages[message_id]
        
        # 큐에서 찾기
        for topic, messages in self.queues.items():
            for message in messages:
                if message.id == message_id:
                    return message
        
        return None
    
    async def start_consumer(self, topic: str, worker_count: int = 1):
        """컨슈머 시작"""
        logger.info(f"컨슈머 시작: {topic} (워커 {worker_count}개)")
        
        for i in range(worker_count):
            asyncio.create_task(self._consumer_worker(topic, i))
    
    async def _consumer_worker(self, topic: str, worker_id: int):
        """컨슈머 워커"""
        logger.info(f"컨슈머 워커 시작: {topic} - {worker_id}")
        
        while True:
            try:
                # 메시지 소비
                message = await self.consume(topic)
                if not message:
                    await asyncio.sleep(1)
                    continue
                
                # 콜백 실행
                if topic in self.consumers:
                    for callback in self.consumers[topic]:
                        try:
                            await callback(message)
                            await self.acknowledge(message.id)
                            break
                        except Exception as e:
                            logger.error(f"콜백 실행 실패: {e}")
                            await self.reject(message.id, requeue=True)
                
            except Exception as e:
                logger.error(f"컨슈머 워커 오류: {e}")
                await asyncio.sleep(1)
    
    def gateway_get_overall_stats(self) -> Dict[str, Any]:
        """전체 통계"""
        total_queued = sum(len(queue) for queue in self.queues.values())
        total_processing = len(self.processing_messages)
        
        return {
            "total_queued": total_queued,
            "total_processing": total_processing,
            "total_messages": total_queued + total_processing,
            "topics": list(self.queues.keys()),
            "metrics": self.metrics.copy()
        } 