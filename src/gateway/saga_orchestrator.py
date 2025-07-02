#!/usr/bin/env python3
"""
Saga 패턴 기반 분산 트랜잭션 관리자
데이터 일관성 보장 및 롤백 처리
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class SagaStepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"

class SagaStatus(Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"

@dataclass
class SagaStep:
    """Saga 단계 정의"""
    name: str
    execute_func: Callable
    compensate_func: Callable
    timeout: float = 300.0
    retry_count: int = 3
    retry_delay: float = 1.0

@dataclass
class SagaStepResult:
    """Saga 단계 실행 결과"""
    step_name: str
    status: SagaStepStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    compensation_data: Optional[Dict[str, Any]] = None

class SagaOrchestrator:
    """Saga 패턴 오케스트레이터"""
    
    def __init__(self):
        self.sagas: Dict[str, Dict[str, Any]] = {}
        self.step_results: Dict[str, List[SagaStepResult]] = {}
    
    async def execute_saga(self, 
                          saga_id: str, 
                          steps: List[SagaStep], 
                          initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Saga 실행
        
        Parameters
        ----------
        saga_id : str
            Saga 고유 ID
        steps : List[SagaStep]
            실행할 단계들
        initial_data : Dict[str, Any]
            초기 데이터
            
        Returns
        -------
        Dict[str, Any]
            최종 결과
        """
        
        # Saga 초기화
        self.sagas[saga_id] = {
            'status': SagaStatus.RUNNING,
            'start_time': time.time(),
            'steps': steps,
            'current_step': 0,
            'data': initial_data.copy()
        }
        
        self.step_results[saga_id] = []
        
        logger.info(f"Saga {saga_id} 시작: {len(steps)}개 단계")
        
        try:
            # 각 단계 순차 실행
            for i, step in enumerate(steps):
                step_result = await self._execute_step(saga_id, step, i)
                self.step_results[saga_id].append(step_result)
                
                if step_result.status == SagaStepStatus.FAILED:
                    # 실패 시 보상 처리
                    await self._compensate_saga(saga_id)
                    return {
                        'saga_id': saga_id,
                        'status': 'failed',
                        'error': step_result.error,
                        'failed_step': step.name,
                        'compensated': True
                    }
                
                # 다음 단계에 결과 데이터 전달
                if step_result.result:
                    self.sagas[saga_id]['data'].update(step_result.result)
            
            # 모든 단계 성공
            self.sagas[saga_id]['status'] = SagaStatus.COMPLETED
            self.sagas[saga_id]['end_time'] = time.time()
            
            logger.info(f"Saga {saga_id} 완료")
            
            return {
                'saga_id': saga_id,
                'status': 'completed',
                'data': self.sagas[saga_id]['data'],
                'execution_time': self.sagas[saga_id]['end_time'] - self.sagas[saga_id]['start_time']
            }
            
        except Exception as e:
            logger.error(f"Saga {saga_id} 실행 중 예외 발생: {e}")
            await self._compensate_saga(saga_id)
            
            return {
                'saga_id': saga_id,
                'status': 'failed',
                'error': str(e),
                'compensated': True
            }
    
    async def _execute_step(self, saga_id: str, step: SagaStep, step_index: int) -> SagaStepResult:
        """개별 단계 실행"""
        
        step_result = SagaStepResult(
            step_name=step.name,
            status=SagaStepStatus.IN_PROGRESS,
            start_time=time.time()
        )
        
        logger.info(f"Saga {saga_id} - 단계 {step_index + 1}: {step.name} 실행 시작")
        
        # 재시도 로직
        for attempt in range(step.retry_count + 1):
            try:
                # 단계 실행
                result = await asyncio.wait_for(
                    step.execute_func(self.sagas[saga_id]['data']),
                    timeout=step.timeout
                )
                
                step_result.status = SagaStepStatus.COMPLETED
                step_result.result = result
                step_result.end_time = time.time()
                
                logger.info(f"Saga {saga_id} - 단계 {step.name} 성공")
                return step_result
                
            except asyncio.TimeoutError:
                error_msg = f"단계 {step.name} 타임아웃 (시도 {attempt + 1}/{step.retry_count + 1})"
                logger.warning(error_msg)
                step_result.error = error_msg
                
            except Exception as e:
                error_msg = f"단계 {step.name} 실패: {e} (시도 {attempt + 1}/{step.retry_count + 1})"
                logger.error(error_msg)
                step_result.error = error_msg
            
            # 마지막 시도가 아니면 대기
            if attempt < step.retry_count:
                await asyncio.sleep(step.retry_delay * (2 ** attempt))
        
        # 모든 재시도 실패
        step_result.status = SagaStepStatus.FAILED
        step_result.end_time = time.time()
        
        logger.error(f"Saga {saga_id} - 단계 {step.name} 최종 실패")
        return step_result
    
    async def _compensate_saga(self, saga_id: str):
        """Saga 보상 처리 (롤백)"""
        
        if saga_id not in self.step_results:
            return
        
        logger.info(f"Saga {saga_id} 보상 처리 시작")
        
        self.sagas[saga_id]['status'] = SagaStatus.COMPENSATING
        
        # 완료된 단계들을 역순으로 보상 처리
        completed_steps = [
            result for result in self.step_results[saga_id] 
            if result.status == SagaStepStatus.COMPLETED
        ]
        
        for step_result in reversed(completed_steps):
            try:
                # 해당 단계의 보상 함수 찾기
                step = next(
                    (s for s in self.sagas[saga_id]['steps'] if s.name == step_result.step_name),
                    None
                )
                
                if step and step.compensate_func:
                    logger.info(f"Saga {saga_id} - 단계 {step_result.step_name} 보상 처리")
                    
                    await step.compensate_func(
                        self.sagas[saga_id]['data'],
                        step_result.compensation_data or step_result.result
                    )
                    
                    step_result.status = SagaStepStatus.COMPENSATED
                    
            except Exception as e:
                logger.error(f"Saga {saga_id} - 단계 {step_result.step_name} 보상 처리 실패: {e}")
                # 보상 실패는 로그만 남기고 계속 진행
        
        self.sagas[saga_id]['status'] = SagaStatus.FAILED
        self.sagas[saga_id]['end_time'] = time.time()
        
        logger.info(f"Saga {saga_id} 보상 처리 완료")
    
    def get_saga_status(self, saga_id: str) -> Optional[Dict[str, Any]]:
        """Saga 상태 조회"""
        
        if saga_id not in self.sagas:
            return None
        
        saga = self.sagas[saga_id]
        step_results = self.step_results.get(saga_id, [])
        
        return {
            'saga_id': saga_id,
            'status': saga['status'].value,
            'start_time': saga['start_time'],
            'end_time': saga.get('end_time'),
            'current_step': saga['current_step'],
            'total_steps': len(saga['steps']),
            'completed_steps': len([r for r in step_results if r.status == SagaStepStatus.COMPLETED]),
            'failed_steps': len([r for r in step_results if r.status == SagaStepStatus.FAILED]),
            'compensated_steps': len([r for r in step_results if r.status == SagaStepStatus.COMPENSATED]),
            'step_details': [
                {
                    'name': r.step_name,
                    'status': r.status.value,
                    'error': r.error,
                    'execution_time': r.end_time - r.start_time if r.end_time else None
                }
                for r in step_results
            ]
        }
    
    def cleanup_saga(self, saga_id: str):
        """Saga 정리"""
        if saga_id in self.sagas:
            del self.sagas[saga_id]
        if saga_id in self.step_results:
            del self.step_results[saga_id]
        logger.info(f"Saga {saga_id} 정리 완료")

# 전역 Saga 오케스트레이터 인스턴스
saga_orchestrator = SagaOrchestrator() 