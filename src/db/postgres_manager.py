#!/usr/bin/env python3
"""
PostgreSQL 연결 풀링 매니저
비동기 처리, 연결 풀링, 트랜잭션 관리 지원
"""

import os
import asyncio
import asyncpg
import logging
import time
from typing import Optional, Dict, Any, List, Union
from contextlib import asynccontextmanager
from dataclasses import dataclass
import json
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """데이터베이스 설정"""
    host: str = "localhost"
    port: int = 5432
    database: str = "callytics"
    username: str = "callytics_user"
    password: str = None
    
    # 연결 풀 설정
    min_connections: int = 5
    max_connections: int = 20
    max_queries: int = 50000
    max_inactive_connection_lifetime: float = 300.0  # 5분
    
    # 연결 타임아웃 설정
    command_timeout: float = 60.0
    server_settings: Dict[str, str] = None
    
    def __post_init__(self):
        if self.server_settings is None:
            self.server_settings = {
                'application_name': 'callytics-service',
                'timezone': 'Asia/Seoul'
            }

class PostgreSQLManager:
    """PostgreSQL 연결 풀링 매니저"""
    
    def __init__(self, config: DatabaseConfig = None):
        """
        PostgreSQL 매니저 초기화
        
        Parameters
        ----------
        config : DatabaseConfig, optional
            데이터베이스 설정 (환경변수에서 로드)
        """
        self.config = config or self._load_config_from_env()
        self.pool: Optional[asyncpg.Pool] = None
        self.is_connected = False
        
        # 성능 모니터링
        self.stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'connection_errors': 0,
            'avg_query_time': 0.0,
            'pool_acquired_count': 0,
            'pool_released_count': 0
        }
    
    def _load_config_from_env(self) -> DatabaseConfig:
        """환경변수에서 데이터베이스 설정 로드"""
        return DatabaseConfig(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "callytics"),
            username=os.getenv("POSTGRES_USER", "callytics_user"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
            min_connections=int(os.getenv("POSTGRES_MIN_CONNECTIONS", "5")),
            max_connections=int(os.getenv("POSTGRES_MAX_CONNECTIONS", "20")),
            command_timeout=float(os.getenv("POSTGRES_COMMAND_TIMEOUT", "60.0"))
        )
    
    async def initialize(self) -> None:
        """연결 풀 초기화"""
        if self.is_connected:
            logger.warning("PostgreSQL 풀이 이미 초기화되어 있습니다")
            return
        
        try:
            logger.info(f"PostgreSQL 연결 풀 초기화 시작: {self.config.host}:{self.config.port}")
            
            # 연결 풀 생성
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                max_queries=self.config.max_queries,
                max_inactive_connection_lifetime=self.config.max_inactive_connection_lifetime,
                command_timeout=self.config.command_timeout,
                server_settings=self.config.server_settings
            )
            
            # 연결 테스트
            async with self.pool.acquire() as conn:
                result = await conn.fetchval('SELECT 1')
                if result == 1:
                    self.is_connected = True
                    logger.info("✅ PostgreSQL 연결 풀 초기화 완료")
                else:
                    raise Exception("연결 테스트 실패")
                    
        except Exception as e:
            self.stats['connection_errors'] += 1
            logger.error(f"❌ PostgreSQL 연결 풀 초기화 실패: {e}")
            raise e
    
    async def close(self) -> None:
        """연결 풀 종료"""
        if self.pool and not self.pool._closed:
            await self.pool.close()
            self.is_connected = False
            logger.info("PostgreSQL 연결 풀 종료됨")
    
    @asynccontextmanager
    async def get_connection(self):
        """연결 풀에서 연결 획득 (컨텍스트 매니저)"""
        if not self.is_connected:
            raise Exception("PostgreSQL 풀이 초기화되지 않았습니다")
        
        conn = None
        try:
            conn = await self.pool.acquire()
            self.stats['pool_acquired_count'] += 1
            yield conn
        finally:
            if conn:
                await self.pool.release(conn)
                self.stats['pool_released_count'] += 1
    
    async def execute_query(self, query: str, *args, fetch_mode: str = "all") -> Any:
        """
        쿼리 실행
        
        Parameters
        ----------
        query : str
            실행할 SQL 쿼리
        args : tuple
            쿼리 파라미터
        fetch_mode : str
            결과 반환 모드 ('all', 'one', 'val', 'none')
        
        Returns
        -------
        Any
            쿼리 실행 결과
        """
        start_time = time.time()
        
        try:
            async with self.get_connection() as conn:
                self.stats['total_queries'] += 1
                
                if fetch_mode == "all":
                    result = await conn.fetch(query, *args)
                elif fetch_mode == "one":
                    result = await conn.fetchrow(query, *args)
                elif fetch_mode == "val":
                    result = await conn.fetchval(query, *args)
                elif fetch_mode == "none":
                    result = await conn.execute(query, *args)
                else:
                    raise ValueError(f"지원하지 않는 fetch_mode: {fetch_mode}")
                
                # 성능 통계 업데이트
                query_time = time.time() - start_time
                self.stats['successful_queries'] += 1
                self.stats['avg_query_time'] = (
                    (self.stats['avg_query_time'] * (self.stats['successful_queries'] - 1) + query_time)
                    / self.stats['successful_queries']
                )
                
                return result
                
        except Exception as e:
            self.stats['failed_queries'] += 1
            logger.error(f"쿼리 실행 실패: {query[:100]}... - {e}")
            raise e
    
    @asynccontextmanager
    async def transaction(self):
        """트랜잭션 컨텍스트 매니저"""
        async with self.get_connection() as conn:
            transaction = conn.transaction()
            try:
                await transaction.start()
                yield conn
                await transaction.commit()
            except Exception as e:
                await transaction.rollback()
                logger.error(f"트랜잭션 롤백: {e}")
                raise e
    
    async def bulk_insert(self, table: str, columns: List[str], data: List[List[Any]]) -> None:
        """대량 데이터 삽입"""
        if not data:
            return
        
        try:
            async with self.get_connection() as conn:
                await conn.copy_records_to_table(
                    table, 
                    records=data, 
                    columns=columns
                )
                logger.info(f"✅ 대량 삽입 완료: {table} ({len(data)}건)")
                
        except Exception as e:
            logger.error(f"❌ 대량 삽입 실패: {table} - {e}")
            raise e
    
    async def health_check(self) -> Dict[str, Any]:
        """데이터베이스 헬스체크"""
        try:
            if not self.is_connected:
                return {
                    "status": "unhealthy",
                    "error": "연결 풀이 초기화되지 않음"
                }
            
            start_time = time.time()
            async with self.get_connection() as conn:
                await conn.fetchval('SELECT 1')
            
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "pool_stats": {
                    "size": self.pool.get_size(),
                    "min_size": self.pool.get_min_size(),
                    "max_size": self.pool.get_max_size(),
                    "idle_connections": self.pool.get_idle_size()
                },
                "query_stats": self.stats.copy()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "query_stats": self.stats.copy()
            }
    
    def db_get_stats(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        return {
            **self.stats,
            "pool_info": {
                "is_connected": self.is_connected,
                "config": {
                    "host": self.config.host,
                    "port": self.config.port,
                    "database": self.config.database,
                    "min_connections": self.config.min_connections,
                    "max_connections": self.config.max_connections
                }
            } if self.is_connected else {}
        }

# 전역 인스턴스 (싱글톤 패턴)
_postgres_manager: Optional[PostgreSQLManager] = None

async def get_postgres_manager() -> PostgreSQLManager:
    """PostgreSQL 매니저 인스턴스 반환"""
    global _postgres_manager
    if _postgres_manager is None:
        _postgres_manager = PostgreSQLManager()
        await _postgres_manager.initialize()
    return _postgres_manager

async def close_postgres_manager():
    """PostgreSQL 매니저 종료"""
    global _postgres_manager
    if _postgres_manager:
        await _postgres_manager.close()
        _postgres_manager = None 