# Standard library imports
import sqlite3
import time
import yaml
import logging
import os
from typing import Annotated, List, Tuple, Optional, Dict, Any
from pathlib import Path


class DatabaseManager:
    """
    데이터베이스 관리자 - 상담 분석 결과 및 발화 내용 저장/조회
    """
    
    def __init__(self, config_path: str = "config/config_enhanced.yaml"):
        """
        데이터베이스 매니저 초기화
        
        Parameters
        ----------
        config_path : str
            설정 파일 경로
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.db_path = self._load_db_path()
        
        # 데이터베이스 초기화
        self._init_database()
    
    def _load_db_path(self) -> str:
        """설정 파일에서 데이터베이스 경로 로드"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config.get('database', {}).get('path', 'Callytics_new.sqlite')
        except Exception as e:
            self.logger.warning(f"설정 파일 로드 실패, 기본 경로 사용: {e}")
            return 'Callytics_new.sqlite'
    
    def _init_database(self):
        """데이터베이스 및 테이블 초기화 - EnhancedSchema.sql 사용"""
        try:
            # EnhancedSchema.sql 파일을 사용하여 데이터베이스 초기화
            schema_path = Path("src/db/sql/EnhancedSchema.sql")
            if schema_path.exists():
                with sqlite3.connect(self.db_path) as conn:
                    with open(schema_path, 'r', encoding='utf-8') as f:
                        schema_sql = f.read()
                    
                    # SQL 문장들을 분리하여 실행
                    conn.executescript(schema_sql)
                    conn.commit()
                    
                    self.logger.info("데이터베이스 스키마 초기화 완료")
                    
                    # 뷰 생성
                    views_path = Path("src/db/sql/CreateViews.sql")
                    if views_path.exists():
                        with open(views_path, 'r', encoding='utf-8') as f:
                            views_sql = f.read()
                        conn.executescript(views_sql)
                        conn.commit()
                        self.logger.info("데이터베이스 뷰 생성 완료")
            else:
                self.logger.error(f"스키마 파일을 찾을 수 없습니다: {schema_path}")
                raise FileNotFoundError(f"Schema file not found: {schema_path}")
                
        except Exception as e:
            self.logger.error(f"데이터베이스 초기화 실패: {e}")
            raise
    
    def insert_consultation_analysis(self, data: Dict[str, Any]) -> bool:
        """
        상담 분석 결과 저장
        
        Parameters
        ----------
        data : Dict[str, Any]
            상담 분석 데이터
            
        Returns
        -------
        bool
            저장 성공 여부
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 먼저 audio_properties에 오디오 파일 정보 저장
                cursor.execute("""
                    INSERT INTO audio_properties (
                        file_path, file_name, duration, sample_rate, channels
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    data.get('audio_path', ''),
                    os.path.basename(data.get('audio_path', '')),
                    data.get('duration', 0.0),
                    data.get('sample_rate', 16000),
                    data.get('channels', 1)
                ))
                
                audio_properties_id = cursor.lastrowid
                
                # consultation_analysis에 분석 결과 저장
                cursor.execute("""
                    INSERT INTO consultation_analysis (
                        audio_properties_id, business_type, classification_type,
                        detail_classification, consultation_result, summary,
                        customer_request, solution, additional_info, confidence,
                        processing_time
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    audio_properties_id,
                    data.get('business_type', '그 외 업무유형'),
                    data.get('classification_type', '상담 주제'),
                    data.get('detail_classification', '기타'),
                    data.get('consultation_result', '미흡'),
                    data.get('summary', ''),
                    data.get('customer_request', ''),
                    data.get('solution', ''),
                    data.get('additional_info', ''),
                    data.get('confidence', 0.0),
                    data.get('processing_time', 0.0)
                ))
                
                conn.commit()
                self.logger.info(f"상담 분석 결과 저장 완료: {data.get('consultation_id', 'unknown')}")
                return True
                
        except Exception as e:
            self.logger.error(f"상담 분석 결과 저장 실패: {e}")
            return False
    
    def insert_utterance(self, data: Dict[str, Any]) -> bool:
        """
        발화 내용 저장
        
        Parameters
        ----------
        data : Dict[str, Any]
            발화 데이터
            
        Returns
        -------
        bool
            저장 성공 여부
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # audio_properties_id를 찾기 위해 file_path로 조회
                cursor.execute("""
                    SELECT id FROM audio_properties WHERE file_path = ?
                """, (data.get('audio_path', ''),))
                
                result = cursor.fetchone()
                if not result:
                    self.logger.error(f"오디오 파일을 찾을 수 없습니다: {data.get('audio_path', '')}")
                    return False
                
                audio_properties_id = result[0]
                
                cursor.execute("""
                    INSERT INTO utterances (
                        audio_properties_id, speaker, start_time, end_time, text, confidence,
                        sequence, sentiment, profane
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    audio_properties_id,
                    data.get('speaker', 'Unknown'),
                    data.get('start_time', 0.0),
                    data.get('end_time', 0.0),
                    data.get('text', ''),
                    data.get('confidence', 0.0),
                    data.get('sequence', 0),
                    data.get('sentiment', '중립'),
                    data.get('profane', 0)
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"발화 내용 저장 실패: {e}")
            return False
    
    def get_consultation_analysis(self, consultation_id: str) -> Optional[Dict[str, Any]]:
        """
        상담 분석 결과 조회
        
        Parameters
        ----------
        consultation_id : str
            상담 ID
            
        Returns
        -------
        Optional[Dict[str, Any]]
            상담 분석 결과
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM consultation_analysis 
                    WHERE consultation_id = ?
                """, (consultation_id,))
                
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                
                return None
                
        except Exception as e:
            self.logger.error(f"상담 분석 결과 조회 실패: {e}")
            return None
    
    def get_utterances(self, consultation_id: str) -> List[Dict[str, Any]]:
        """
        발화 내용 조회
        
        Parameters
        ----------
        consultation_id : str
            상담 ID
            
        Returns
        -------
        List[Dict[str, Any]]
            발화 내용 리스트
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM utterances 
                    WHERE consultation_id = ?
                    ORDER BY start_time
                """, (consultation_id,))
                
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            self.logger.error(f"발화 내용 조회 실패: {e}")
            return []
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """
        분석 통계 조회
        
        Returns
        -------
        Dict[str, Any]
            분석 통계
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 전체 상담 수
                cursor.execute("SELECT COUNT(*) FROM consultation_analysis")
                total_consultations = cursor.fetchone()[0]
                
                # 업무 유형별 통계
                cursor.execute("""
                    SELECT business_type, COUNT(*) as count 
                    FROM consultation_analysis 
                    GROUP BY business_type 
                    ORDER BY count DESC
                """)
                business_type_stats = dict(cursor.fetchall())
                
                # 분류 유형별 통계
                cursor.execute("""
                    SELECT classification_type, COUNT(*) as count 
                    FROM consultation_analysis 
                    GROUP BY classification_type 
                    ORDER BY count DESC
                """)
                classification_stats = dict(cursor.fetchall())
                
                # 평균 처리 시간
                cursor.execute("SELECT AVG(processing_time) FROM consultation_analysis")
                avg_processing_time = cursor.fetchone()[0] or 0.0
                
                # 전체 발화 수
                cursor.execute("SELECT COUNT(*) FROM utterances")
                total_utterances = cursor.fetchone()[0]
                
                return {
                    'total_consultations': total_consultations,
                    'total_utterances': total_utterances,
                    'business_type_distribution': business_type_stats,
                    'classification_type_distribution': classification_stats,
                    'average_processing_time': avg_processing_time
                }
                
        except Exception as e:
            self.logger.error(f"통계 조회 실패: {e}")
            return {}
    
    def search_consultations(
        self,
        business_type: Optional[str] = None,
        classification_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        상담 검색
        
        Parameters
        ----------
        business_type : str, optional
            업무 유형 필터
        classification_type : str, optional
            분류 유형 필터
        limit : int
            결과 제한 수
            
        Returns
        -------
        List[Dict[str, Any]]
            검색 결과
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM consultation_analysis WHERE 1=1"
                params = []
                
                if business_type:
                    query += " AND business_type = ?"
                    params.append(business_type)
                
                if classification_type:
                    query += " AND classification_type = ?"
                    params.append(classification_type)
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            self.logger.error(f"상담 검색 실패: {e}")
            return []
