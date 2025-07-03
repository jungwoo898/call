#!/usr/bin/env python3
"""
공통 함수 모듈
중복되는 함수들을 통합하여 재사용 가능하게 만듦
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

# 로거 설정
logger = logging.getLogger(__name__)

class CommonFunctions:
    """공통 함수 클래스"""
    
    @staticmethod
    def util_ensure_directory(path: str) -> bool:
        """디렉토리 존재 확인 및 생성"""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"디렉토리 생성 실패: {path}, 오류: {e}")
            return False
    
    @staticmethod
    def util_load_config(config_path: str) -> Dict[str, Any]:
        """설정 파일 로드"""
        try:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                import yaml
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            elif config_path.endswith('.json'):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.error(f"지원하지 않는 설정 파일 형식: {config_path}")
                return {}
        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {config_path}, 오류: {e}")
            return {}
    
    @staticmethod
    def util_save_json(data: Dict[str, Any], file_path: str) -> bool:
        """JSON 파일 저장"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"JSON 파일 저장 실패: {file_path}, 오류: {e}")
            return False
    
    @staticmethod
    def util_load_json(file_path: str) -> Dict[str, Any]:
        """JSON 파일 로드"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"JSON 파일 로드 실패: {file_path}, 오류: {e}")
            return {}
    
    @staticmethod
    def util_get_timestamp() -> str:
        """현재 타임스탬프 반환"""
        return get_current_time().isoformat()
    
    @staticmethod
    def util_validate_file_path(file_path: str) -> bool:
        """파일 경로 유효성 검사"""
        return os.path.exists(file_path) and os.path.isfile(file_path)
    
    @staticmethod
    def util_get_file_size(file_path: str) -> int:
        """파일 크기 반환 (바이트)"""
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            logger.error(f"파일 크기 확인 실패: {file_path}, 오류: {e}")
            return 0
    
    @staticmethod
    def util_cleanup_temp_files(temp_dir: str, max_age_hours: int = 24) -> int:
        """임시 파일 정리"""
        try:
            temp_path = Path(temp_dir)
            if not temp_path.exists():
                return 0
            
            current_time = get_current_time()
            deleted_count = 0
            
            for file_path in temp_path.rglob("*"):
                if file_path.is_file():
                    file_age = current_time - datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_age.total_seconds() > max_age_hours * 3600:
                        file_path.unlink()
                        deleted_count += 1
            
            return deleted_count
        except Exception as e:
            logger.error(f"임시 파일 정리 실패: {temp_dir}, 오류: {e}")
            return 0
    
    @staticmethod
    async def async_operation_with_timeout(operation, timeout: float = 30.0):
        """비동기 작업을 타임아웃과 함께 실행"""
        try:
            return await asyncio.wait_for(operation, timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"작업 타임아웃: {timeout}초")
            raise
        except Exception as e:
            logger.error(f"비동기 작업 실패: {e}")
            raise

# 전역 인스턴스
common_functions = CommonFunctions() 