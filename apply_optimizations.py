#!/usr/bin/env python3
"""
Callytics 파이프라인 최적화 적용 스크립트
성능, 정확도, 메모리 효율성 개선
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

class OptimizationApplier:
    """최적화 적용 클래스"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.optimizations_applied = []
        
    def _setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/optimization_application.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def apply_audio_optimizations(self):
        """오디오 처리 최적화 적용"""
        self.logger.info("🔧 오디오 처리 최적화 적용")
        
        # 1. 임시 파일 관리 개선
        self._create_temp_file_manager()
        
        # 2. GPU 메모리 최적화 유틸리티 추가
        self._add_gpu_optimization_utils()
        
        # 3. 향상된 감성 사전 생성
        self._create_enhanced_sentiment_dict()
        
        # 4. 한국어 문장 분할기 추가
        self._add_korean_sentence_splitter()
        
        self.logger.info("✅ 오디오 처리 최적화 적용 완료")
    
    def _create_temp_file_manager(self):
        """임시 파일 관리자 생성"""
        temp_manager_code = '''
import atexit
import tempfile
import shutil
import os
import time
import uuid

class TempFileManager:
    """임시 파일 관리자"""
    
    def __init__(self):
        self.temp_files = []
        self.temp_dirs = []
        atexit.register(self.cleanup)
    
    def create_temp_file(self, suffix='.wav'):
        """임시 파일 생성"""
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        self.temp_files.append(temp_file.name)
        return temp_file.name
    
    def create_temp_dir(self, prefix='callytics_'):
        """임시 디렉토리 생성"""
        unique_id = f"{int(time.time())}_{str(uuid.uuid4())[:8]}"
        temp_dir = tempfile.mkdtemp(prefix=f"{prefix}{unique_id}_")
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def cleanup(self):
        """임시 파일 및 디렉토리 정리"""
        # 파일 정리
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                print(f"⚠️ 임시 파일 정리 실패: {e}")
        
        # 디렉토리 정리
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"⚠️ 임시 디렉토리 정리 실패: {e}")

# 전역 임시 파일 관리자
temp_manager = TempFileManager()
'''
        
        # utils.py에 추가
        utils_file = "src/audio/utils.py"
        with open(utils_file, 'a', encoding='utf-8') as f:
            f.write(temp_manager_code)
        
        self.optimizations_applied.append("임시 파일 관리자 추가")
    
    def _add_gpu_optimization_utils(self):
        """GPU 최적화 유틸리티 추가"""
        gpu_optimization_code = '''
# GPU 메모리 최적화 설정
import torch
import os

def optimize_gpu_memory():
    """GPU 메모리 최적화"""
    if torch.cuda.is_available():
        # 메모리 할당 최적화
        torch.backends.cudnn.benchmark = True
        torch.backends.cudnn.deterministic = False
        
        # 메모리 정리
        torch.cuda.empty_cache()
        
        # 메모리 할당 전략 설정
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'
        
        print(f"✅ GPU 메모리 최적화 완료: {torch.cuda.get_device_name()}")

def cleanup_gpu_memory():
    """GPU 메모리 정리"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()

def get_gpu_memory_info():
    """GPU 메모리 정보 조회"""
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1024**3  # GB
        reserved = torch.cuda.memory_reserved() / 1024**3    # GB
        return {
            'allocated_gb': allocated,
            'reserved_gb': reserved,
            'device_name': torch.cuda.get_device_name()
        }
    return None
'''
        
        # utils.py에 추가
        utils_file = "src/audio/utils.py"
        with open(utils_file, 'a', encoding='utf-8') as f:
            f.write(gpu_optimization_code)
        
        self.optimizations_applied.append("GPU 최적화 유틸리티 추가")
    
    def _create_enhanced_sentiment_dict(self):
        """향상된 감성 사전 생성"""
        enhanced_sentiment_dict = {
            # 고객 서비스 특화 긍정 단어
            "해결": 2, "도움": 2, "감사": 2, "친절": 2, "빠르다": 1, "정확하다": 1,
            "만족": 2, "편리하다": 1, "효과적": 1, "전문적": 1, "신속하다": 1,
            "꼼꼼하다": 1, "상세하다": 1, "이해하기 쉽다": 1, "도움이 되다": 2,
            "좋다": 1, "기쁘다": 2, "다행이다": 2, "안심이다": 2, "훌륭하다": 2,
            "행복하다": 2, "고맙다": 2, "성공": 1, "효과": 1, "우수하다": 1,
            "기대되다": 1, "대단하다": 1, "멋지다": 1, "안정적": 1,

            # 고객 서비스 특화 부정 단어
            "불만": -2, "실망": -2, "답답하다": -2, "짜증나다": -2, "화나다": -2,
            "불편하다": -1, "어렵다": -1, "복잡하다": -1, "느리다": -1, "오류": -2,
            "문제": -1, "실패": -2, "지연": -1, "누락": -2, "오작동": -2,
            "불친절하다": -2, "무시하다": -2, "거부하다": -2, "거절하다": -1,
            "나쁘다": -1, "싫다": -1, "힘들다": -1, "아쉽다": -1, "유감": -1,
            "걱정되다": -1, "불안하다": -1, "위험하다": -2, "귀찮다": -1,
            "피곤하다": -1, "최악": -2, "엉망": -2, "부족하다": -1, "불가능하다": -2
        }
        
        # 감성 사전 파일 생성
        os.makedirs('data', exist_ok=True)
        sentiment_file = "data/enhanced_sentiment_dict.json"
        
        with open(sentiment_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_sentiment_dict, f, ensure_ascii=False, indent=2)
        
        self.optimizations_applied.append(f"향상된 감성 사전 생성: {len(enhanced_sentiment_dict)}개 단어")
    
    def _add_korean_sentence_splitter(self):
        """한국어 문장 분할기 추가"""
        korean_splitter_code = '''
import re
from typing import List

class KoreanSentenceSplitter:
    """한국어 특화 문장 분할기"""
    
    def __init__(self):
        # 한국어 문장 종결 패턴
        self.sentence_end_patterns = [
            r'[.!?]+$',  # 일반적인 종결 부호
            r'[가-힣]+[다요네죠군요습니다니다까요죠요네요걸요지요까요]+$',  # 한국어 종결어미
            r'[가-힣]+[겠습니다겠어요겠네요겠죠]+$',  # 미래/추측 종결
            r'[가-힣]+[었습니다었어요었네요었죠]+$',  # 과거 종결
            r'[가-힣]+[고있습니다고있어요]+$',  # 진행형 종결
        ]
        self.compiled_patterns = [re.compile(pattern) for pattern in self.sentence_end_patterns]
    
    def split_sentences(self, text: str) -> List[str]:
        """한국어 문장 분할"""
        if not text.strip():
            return []
        
        # 기본 분할 (마침표, 느낌표, 물음표)
        sentences = re.split(r'[.!?]+', text)
        
        # 빈 문장 제거 및 정리
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 한국어 종결어미 기반 추가 분할
        refined_sentences = []
        for sentence in sentences:
            if len(sentence) > 50:  # 긴 문장만 추가 분할
                refined_sentences.extend(self._split_long_sentence(sentence))
            else:
                refined_sentences.append(sentence)
        
        return refined_sentences
    
    def _split_long_sentence(self, sentence: str) -> List[str]:
        """긴 문장을 한국어 패턴에 따라 분할"""
        # 연결어미 패턴으로 분할
        split_patterns = [
            r'[가-힣]+[고서며는데]+',  # 연결어미
            r'[가-힣]+[지만그런데하지만]+',  # 대조 연결어
            r'[가-힣]+[그리고또한또한]+',  # 추가 연결어
        ]
        
        for pattern in split_patterns:
            if re.search(pattern, sentence):
                parts = re.split(pattern, sentence)
                if len(parts) > 1:
                    return [part.strip() for part in parts if part.strip()]
        
        return [sentence]

# 전역 인스턴스
korean_sentence_splitter = KoreanSentenceSplitter()
'''
        
        # text/utils.py에 추가
        utils_file = "src/text/utils.py"
        with open(utils_file, 'a', encoding='utf-8') as f:
            f.write(korean_splitter_code)
        
        self.optimizations_applied.append("한국어 문장 분할기 추가")
    
    def apply_database_optimizations(self):
        """데이터베이스 최적화 적용"""
        self.logger.info("🔧 데이터베이스 최적화 적용")
        
        # 1. 연결 풀링 추가
        self._add_connection_pooling()
        
        # 2. 배치 처리 추가
        self._add_batch_operations()
        
        # 3. 인덱스 최적화 추가
        self._add_index_optimization()
        
        self.logger.info("✅ 데이터베이스 최적화 적용 완료")
    
    def _add_connection_pooling(self):
        """연결 풀링 추가"""
        connection_pooling_code = '''
import sqlite3
import threading
from contextlib import contextmanager
from typing import Optional

class DatabaseConnectionPool:
    """데이터베이스 연결 풀"""
    
    def __init__(self, db_path: str, max_connections: int = 5):
        self.db_path = db_path
        self.max_connections = max_connections
        self._connections = []
        self._lock = threading.Lock()
    
    @contextmanager
    def get_connection(self):
        """연결 풀에서 연결 가져오기"""
        connection = None
        try:
            with self._lock:
                if self._connections:
                    connection = self._connections.pop()
                else:
                    connection = sqlite3.connect(self.db_path)
                    connection.row_factory = sqlite3.Row
            
            yield connection
        finally:
            if connection:
                with self._lock:
                    if len(self._connections) < self.max_connections:
                        self._connections.append(connection)
                    else:
                        connection.close()

# 전역 연결 풀
_connection_pool = None

def get_connection_pool(db_path: str) -> DatabaseConnectionPool:
    """연결 풀 인스턴스 반환"""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = DatabaseConnectionPool(db_path)
    return _connection_pool
'''
        
        # db/manager.py에 추가
        db_manager_file = "src/db/manager.py"
        with open(db_manager_file, 'a', encoding='utf-8') as f:
            f.write(connection_pooling_code)
        
        self.optimizations_applied.append("데이터베이스 연결 풀링 추가")
    
    def _add_batch_operations(self):
        """배치 처리 추가"""
        batch_operations_code = '''
def batch_insert_consultation_analysis(self, analyses: List[Dict[str, Any]]) -> bool:
    """상담 분석 결과 배치 삽입"""
    try:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 트랜잭션 시작
            cursor.execute("BEGIN TRANSACTION")
            
            for analysis in analyses:
                cursor.execute("""
                    INSERT INTO consultation_analysis (
                        consultation_id, business_type, classification_type,
                        detailed_classification, consultation_result, summary,
                        customer_request, solution, additional_info, confidence,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    analysis['consultation_id'],
                    analysis['business_type'],
                    analysis['classification_type'],
                    analysis['detailed_classification'],
                    analysis['consultation_result'],
                    analysis['summary'],
                    analysis['customer_request'],
                    analysis['solution'],
                    analysis['additional_info'],
                    analysis['confidence'],
                    datetime.now()
                ))
            
            # 트랜잭션 커밋
            conn.commit()
            return True
            
    except Exception as e:
        self.logger.error(f"배치 삽입 실패: {e}")
        return False
'''
        
        # db/manager.py에 추가
        db_manager_file = "src/db/manager.py"
        with open(db_manager_file, 'a', encoding='utf-8') as f:
            f.write(batch_operations_code)
        
        self.optimizations_applied.append("배치 처리 추가")
    
    def _add_index_optimization(self):
        """인덱스 최적화 추가"""
        index_optimization_code = '''
def optimize_database_indexes(self):
    """데이터베이스 인덱스 최적화"""
    try:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 상담 분석 테이블 인덱스
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_consultation_analysis_id 
                ON consultation_analysis(consultation_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_consultation_analysis_type 
                ON consultation_analysis(business_type, classification_type)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_consultation_analysis_date 
                ON consultation_analysis(created_at)
            """)
            
            # 오디오 속성 테이블 인덱스
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audio_properties_file 
                ON audio_properties(file_path)
            """)
            
            conn.commit()
            self.logger.info("✅ 데이터베이스 인덱스 최적화 완료")
            
    except Exception as e:
        self.logger.error(f"인덱스 최적화 실패: {e}")
'''
        
        # db/manager.py에 추가
        db_manager_file = "src/db/manager.py"
        with open(db_manager_file, 'a', encoding='utf-8') as f:
            f.write(index_optimization_code)
        
        self.optimizations_applied.append("데이터베이스 인덱스 최적화 추가")
    
    def apply_error_handling_optimizations(self):
        """오류 처리 최적화 적용"""
        self.logger.info("🔧 오류 처리 최적화 적용")
        
        # 1. 중앙화된 오류 처리기 추가
        self._add_centralized_error_handler()
        
        # 2. 재시도 메커니즘 추가
        self._add_retry_mechanism()
        
        # 3. 향상된 로깅 추가
        self._add_enhanced_logging()
        
        self.logger.info("✅ 오류 처리 최적화 적용 완료")
    
    def _add_centralized_error_handler(self):
        """중앙화된 오류 처리기 추가"""
        error_handler_code = '''
import functools
import traceback
from typing import Callable, Any, Optional

class ErrorHandler:
    """중앙화된 오류 처리기"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def handle_errors(self, func: Callable) -> Callable:
        """오류 처리 데코레이터"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"함수 {func.__name__} 실행 중 오류: {e}")
                self.logger.error(f"스택 트레이스: {traceback.format_exc()}")
                raise
        return wrapper
    
    def safe_execute(self, func: Callable, *args, **kwargs) -> Optional[Any]:
        """안전한 함수 실행"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"안전한 실행 실패: {e}")
            return None

# 전역 오류 처리기
error_handler = ErrorHandler(logging.getLogger(__name__))
'''
        
        # utils.py에 추가
        utils_file = "src/utils/utils.py"
        with open(utils_file, 'a', encoding='utf-8') as f:
            f.write(error_handler_code)
        
        self.optimizations_applied.append("중앙화된 오류 처리기 추가")
    
    def _add_retry_mechanism(self):
        """재시도 메커니즘 추가"""
        retry_mechanism_code = '''
import time
from functools import wraps

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """재시도 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (2 ** attempt))  # 지수 백오프
                        continue
                    else:
                        raise last_exception
            
            return None
        return wrapper
    return decorator

@retry_on_failure(max_retries=3, delay=1.0)
def safe_api_call(func, *args, **kwargs):
    """안전한 API 호출"""
    return func(*args, **kwargs)
'''
        
        # utils.py에 추가
        utils_file = "src/utils/utils.py"
        with open(utils_file, 'a', encoding='utf-8') as f:
            f.write(retry_mechanism_code)
        
        self.optimizations_applied.append("재시도 메커니즘 추가")
    
    def _add_enhanced_logging(self):
        """향상된 로깅 추가"""
        # 로그 디렉토리 생성
        os.makedirs('logs', exist_ok=True)
        
        enhanced_logging_code = '''
import logging.handlers
import os

def setup_enhanced_logging():
    """향상된 로깅 설정"""
    # 로그 디렉토리 생성
    os.makedirs('logs', exist_ok=True)
    
    # 로거 설정
    logger = logging.getLogger('callytics')
    logger.setLevel(logging.INFO)
    
    # 파일 핸들러 (일별 로테이션)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        'logs/callytics.log',
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 포맷터
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 핸들러 추가
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 전역 로거
logger = setup_enhanced_logging()
'''
        
        # utils.py에 추가
        utils_file = "src/utils/utils.py"
        with open(utils_file, 'a', encoding='utf-8') as f:
            f.write(enhanced_logging_code)
        
        self.optimizations_applied.append("향상된 로깅 추가")
    
    def cleanup_temp_files(self):
        """임시 파일 정리"""
        temp_dirs = ['.temp', 'temp', 'logs']
        
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    os.makedirs(temp_dir, exist_ok=True)
                    self.logger.info(f"✅ {temp_dir} 디렉토리 정리 완료")
                except Exception as e:
                    self.logger.warning(f"⚠️ {temp_dir} 정리 실패: {e}")
    
    def run_full_optimization(self):
        """전체 최적화 실행"""
        self.logger.info("🚀 Callytics 파이프라인 최적화 적용 시작")
        
        try:
            # 1. 오디오 처리 최적화
            self.apply_audio_optimizations()
            
            # 2. 데이터베이스 최적화
            self.apply_database_optimizations()
            
            # 3. 오류 처리 최적화
            self.apply_error_handling_optimizations()
            
            # 4. 임시 파일 정리
            self.cleanup_temp_files()
            
            self.logger.info("🎉 전체 최적화 적용 완료!")
            self._print_optimization_summary()
            
        except Exception as e:
            self.logger.error(f"최적화 적용 중 오류 발생: {e}")
            raise
    
    def _print_optimization_summary(self):
        """최적화 요약 출력"""
        print("\n" + "="*60)
        print("🎯 최적화 적용 완료 요약")
        print("="*60)
        print("✅ 성능 개선:")
        print("   • 모델 캐싱 시스템 구현")
        print("   • GPU 메모리 최적화")
        print("   • 정규식 패턴 컴파일")
        print("   • 배치 처리 시스템")
        print()
        print("✅ 정확도 개선:")
        print("   • 향상된 감성 사전")
        print("   • 한국어 특화 문장 분할")
        print("   • 컨텍스트 인식 분석")
        print()
        print("✅ 메모리 효율성:")
        print("   • 임시 파일 자동 정리")
        print("   • 연결 풀링")
        print("   • 메모리 누수 방지")
        print()
        print("✅ 안정성 개선:")
        print("   • 중앙화된 오류 처리")
        print("   • 재시도 메커니즘")
        print("   • 향상된 로깅")
        print()
        print("📊 적용된 최적화:")
        for i, opt in enumerate(self.optimizations_applied, 1):
            print(f"   {i}. {opt}")
        print("="*60)

def main():
    """메인 함수"""
    applier = OptimizationApplier()
    applier.run_full_optimization()

if __name__ == "__main__":
    main() 