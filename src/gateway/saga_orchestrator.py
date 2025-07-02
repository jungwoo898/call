#!/usr/bin/env python3
"""
Saga 패턴 오케스트레이터
트랜잭션 관리 및 보상 로직
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, List, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SagaStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"

@dataclass
class SagaStep:
    """Saga 단계 정의"""
    name: str
    execute: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
    compensate: Callable[[Dict[str, Any]], Awaitable[None]]

class SagaOrchestrator:
    """Saga 패턴 오케스트레이터"""
    
    def __init__(self):
        self.sagas: Dict[str, Dict[str, Any]] = {}
    
    async def execute_saga(self, 
                          saga_id: str, 
                          steps: List[SagaStep], 
                          initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Saga 실행"""
        
        # Saga 초기화
        self.sagas[saga_id] = {
            "status": SagaStatus.RUNNING,
            "steps": steps,
            "current_step": 0,
            "data": initial_data,
            "compensated_steps": [],
            "start_time": asyncio.get_event_loop().time()
        }
        
        logger.info(f"Saga {saga_id} 시작: {len(steps)}단계")
        
        try:
            # 각 단계 실행
            for i, step in enumerate(steps):
                self.sagas[saga_id]["current_step"] = i
                
                logger.info(f"Saga {saga_id} 단계 {i+1}/{len(steps)}: {step.name}")
                
                # 단계 실행
                step_result = await step.execute(self.sagas[saga_id]["data"])
                
                # 결과를 데이터에 병합
                self.sagas[saga_id]["data"].update(step_result)
                
                logger.info(f"Saga {saga_id} 단계 {step.name} 완료")
            
            # 모든 단계 성공
            self.sagas[saga_id]["status"] = SagaStatus.COMPLETED
            logger.info(f"Saga {saga_id} 완료")
            
            return self.sagas[saga_id]["data"]
            
        except Exception as e:
            logger.error(f"Saga {saga_id} 실패: {e}")
            self.sagas[saga_id]["status"] = SagaStatus.FAILED
            
            # 보상 실행
            await self._compensate_saga(saga_id)
            
            raise e
    
    async def _compensate_saga(self, saga_id: str):
        """Saga 보상 실행"""
        if saga_id not in self.sagas:
            return
        
        saga = self.sagas[saga_id]
        saga["status"] = SagaStatus.COMPENSATING
        
        logger.info(f"Saga {saga_id} 보상 시작")
        
        # 완료된 단계들을 역순으로 보상
        completed_steps = saga["current_step"]
        steps = saga["steps"]
        
        for i in range(completed_steps, -1, -1):
            step = steps[i]
            try:
                logger.info(f"Saga {saga_id} 보상: {step.name}")
                await step.compensate(saga["data"])
                saga["compensated_steps"].append(i)
            except Exception as e:
                logger.error(f"Saga {saga_id} 보상 실패 {step.name}: {e}")
        
        logger.info(f"Saga {saga_id} 보상 완료")
    
    def get_saga_status(self, saga_id: str) -> Dict[str, Any]:
        """Saga 상태 조회"""
        if saga_id not in self.sagas:
            return None
        
        saga = self.sagas[saga_id]
        return {
            "saga_id": saga_id,
            "status": saga["status"].value,
            "current_step": saga["current_step"],
            "total_steps": len(saga["steps"]),
            "compensated_steps": saga["compensated_steps"],
            "start_time": saga["start_time"],
            "duration": asyncio.get_event_loop().time() - saga["start_time"]
        }
    
    def get_all_sagas(self) -> List[Dict[str, Any]]:
        """모든 Saga 상태 조회"""
        return [self.get_saga_status(saga_id) for saga_id in self.sagas.keys()]
    
    def cleanup_completed_sagas(self, max_age_hours: int = 24):
        """완료된 Saga 정리"""
        current_time = asyncio.get_event_loop().time()
        max_age_seconds = max_age_hours * 3600
        
        to_remove = []
        for saga_id, saga in self.sagas.items():
            if saga["status"] in [SagaStatus.COMPLETED, SagaStatus.FAILED]:
                if current_time - saga["start_time"] > max_age_seconds:
                    to_remove.append(saga_id)
        
        for saga_id in to_remove:
            del self.sagas[saga_id]
            logger.info(f"Saga {saga_id} 정리됨") 