#!/usr/bin/env python3
"""
Callytics 전체 파이프라인 테스트 스크립트
오디오 입력부터 DB 저장까지 전 과정을 검증
"""

import os
import sys
import time
import logging
import sqlite3
from pathlib import Path
from typing import Dict, Any

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """로깅 설정"""
    Path("logs").mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/pipeline_test.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def check_environment():
    """환경 설정 확인"""
    logger = logging.getLogger(__name__)
    
    # API 키 확인
    api_keys = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "HUGGINGFACE_TOKEN": os.getenv("HUGGINGFACE_TOKEN"),
        "AZURE_OPENAI_API_KEY": os.getenv("AZURE_OPENAI_API_KEY")
    }
    
    logger.info("=== 환경 설정 확인 ===")
    for key, value in api_keys.items():
        status = "✅ 설정됨" if value else "❌ 미설정"
        logger.info(f"{key}: {status}")
    
    if not any(api_keys.values()):
        logger.error("❌ API 키가 설정되지 않았습니다!")
        return False
    
    # 필수 디렉토리 확인
    required_dirs = ["audio", "logs", "config", "src"]
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            logger.error(f"❌ 필수 디렉토리가 없습니다: {dir_name}")
            return False
        logger.info(f"✅ {dir_name} 디렉토리 존재")
    
    # 오디오 파일 확인
    audio_files = list(Path("audio").glob("*.mp3")) + list(Path("audio").glob("*.wav"))
    if not audio_files:
        logger.error("❌ audio/ 디렉토리에 테스트할 오디오 파일이 없습니다!")
        return False
    
    logger.info(f"✅ {len(audio_files)}개의 오디오 파일 발견")
    for audio_file in audio_files[:3]:  # 처음 3개만 출력
        logger.info(f"   - {audio_file.name}")
    
    return True

def check_database():
    """데이터베이스 상태 확인"""
    logger = logging.getLogger(__name__)
    
    db_path = "Callytics_new.sqlite"
    
    if not Path(db_path).exists():
        logger.error(f"❌ 데이터베이스 파일이 없습니다: {db_path}")
        logger.info("데이터베이스를 초기화합니다...")
        
        # 데이터베이스 초기화 실행
        try:
            from init_database import init_database
            if init_database():
                logger.info("✅ 데이터베이스 초기화 완료")
            else:
                logger.error("❌ 데이터베이스 초기화 실패")
                return False
        except Exception as e:
            logger.error(f"❌ 데이터베이스 초기화 중 오류: {e}")
            return False
    
    # 데이터베이스 연결 테스트
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 테이블 목록 확인
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ["audio_properties", "consultation_analysis", "utterances"]
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                logger.error(f"❌ 필수 테이블이 없습니다: {missing_tables}")
                return False
            
            logger.info(f"✅ 데이터베이스 연결 성공, {len(tables)}개 테이블 확인")
            
            # 각 테이블의 레코드 수 확인
            for table in required_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                logger.info(f"   - {table}: {count}개 레코드")
            
    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 실패: {e}")
        return False
    
    return True

def test_integrated_analysis():
    """통합 분석 테스트"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("=== 통합 분석기 초기화 ===")
        
        # 통합 분석기 import 및 초기화
        from src.integrated_analyzer import IntegratedAnalyzer
        
        # 환경 변수에서 토큰 가져오기
        huggingface_token = os.getenv("HUGGINGFACE_TOKEN")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not openai_api_key:
            logger.error("❌ OPENAI_API_KEY가 필요합니다")
            return False
        
        analyzer = IntegratedAnalyzer(
            config_path="config/config_enhanced.yaml",
            diarization_token=huggingface_token
        )
        
        logger.info("✅ 통합 분석기 초기화 완료")
        
        # 테스트할 오디오 파일 선택
        audio_files = list(Path("audio").glob("*.mp3")) + list(Path("audio").glob("*.wav"))
        test_file = str(audio_files[0])
        
        logger.info(f"=== 오디오 분석 시작: {Path(test_file).name} ===")
        start_time = time.time()
        
        # 상담 분석 실행
        result = analyzer.analyze_consultation(
            audio_path=test_file,
            consultation_id=f"test_{int(time.time())}",
            metadata={
                "source": "pipeline_test",
                "description": "전체 파이프라인 테스트"
            }
        )
        
        processing_time = time.time() - start_time
        
        # 결과 검증
        logger.info("=== 분석 결과 검증 ===")
        
        # 기본 구조 확인
        required_keys = ["consultation_id", "utterances", "analysis", "processing_time"]
        for key in required_keys:
            if key not in result:
                logger.error(f"❌ 결과에 필수 키가 없습니다: {key}")
                return False
            logger.info(f"✅ {key} 존재")
        
        # 발화 내용 확인
        utterances = result["utterances"]
        if not utterances:
            logger.error("❌ 발화 내용이 없습니다")
            return False
        
        logger.info(f"✅ {len(utterances)}개 발화 추출")
        
        # 발화 내용 샘플 출력
        for i, utterance in enumerate(utterances[:3], 1):
            logger.info(f"   발화 {i}: {utterance['speaker']} - {utterance['text'][:50]}...")
        
        # 분석 결과 확인
        analysis = result["analysis"]
        analysis_fields = [
            "business_type", "classification_type", "detailed_classification",
            "consultation_result", "summary", "customer_request", "solution"
        ]
        
        logger.info("=== 분석 내용 검증 ===")
        for field in analysis_fields:
            value = analysis.get(field, "Unknown")
            is_valid = value and value != "Unknown" and len(str(value).strip()) > 0
            status = "✅" if is_valid else "⚠️"
            logger.info(f"{status} {field}: {value}")
        
        # 성능 정보
        logger.info(f"✅ 처리 시간: {processing_time:.2f}초")
        logger.info(f"✅ 상담 ID: {result['consultation_id']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 통합 분석 테스트 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_database_storage():
    """데이터베이스 저장 확인"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("=== 데이터베이스 저장 확인 ===")
        
        db_path = "Callytics_new.sqlite"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 최근 저장된 데이터 확인
            cursor.execute("""
                SELECT COUNT(*) FROM consultation_analysis 
                WHERE created_at > datetime('now', '-1 hour')
            """)
            recent_consultations = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM utterances 
                WHERE created_at > datetime('now', '-1 hour')
            """)
            recent_utterances = cursor.fetchone()[0]
            
            logger.info(f"✅ 최근 1시간 내 저장된 상담: {recent_consultations}건")
            logger.info(f"✅ 최근 1시간 내 저장된 발화: {recent_utterances}개")
            
            if recent_consultations > 0:
                # 최신 상담 분석 결과 조회
                cursor.execute("""
                    SELECT business_type, classification_type, detail_classification, 
                           consultation_result, confidence, processing_time
                    FROM consultation_analysis 
                    ORDER BY created_at DESC LIMIT 1
                """)
                
                result = cursor.fetchone()
                if result:
                    business_type, classification_type, detail_classification, consultation_result, confidence, processing_time = result
                    
                    logger.info("=== 최신 분석 결과 ===")
                    logger.info(f"업무 유형: {business_type}")
                    logger.info(f"분류 유형: {classification_type}")
                    logger.info(f"세부 분류: {detail_classification}")
                    logger.info(f"상담 결과: {consultation_result}")
                    logger.info(f"신뢰도: {confidence}")
                    logger.info(f"처리 시간: {processing_time}초")
                    
                    # 분석 결과 품질 평가
                    quality_score = 0
                    if business_type and business_type != "Unknown":
                        quality_score += 1
                    if classification_type and classification_type != "Unknown":
                        quality_score += 1
                    if detail_classification and detail_classification != "Unknown":
                        quality_score += 1
                    if consultation_result and consultation_result != "Unknown":
                        quality_score += 1
                    if confidence and confidence > 0.5:
                        quality_score += 1
                    
                    logger.info(f"✅ 분석 품질 점수: {quality_score}/5")
                    
                    if quality_score >= 3:
                        logger.info("✅ 분석 결과가 합리적으로 산출되었습니다!")
                        return True
                    else:
                        logger.warning("⚠️ 분석 결과 품질이 낮습니다. 모델 설정을 확인해주세요.")
                        return False
            
            return recent_consultations > 0
            
    except Exception as e:
        logger.error(f"❌ 데이터베이스 저장 확인 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    logger = setup_logging()
    
    logger.info("🚀 Callytics 파이프라인 테스트 시작")
    
    # 1단계: 환경 확인
    if not check_environment():
        logger.error("❌ 환경 설정 확인 실패")
        return 1
    
    # 2단계: 데이터베이스 확인
    if not check_database():
        logger.error("❌ 데이터베이스 확인 실패")
        return 1
    
    # 3단계: 통합 분석 테스트
    if not test_integrated_analysis():
        logger.error("❌ 통합 분석 테스트 실패")
        return 1
    
    # 4단계: 데이터베이스 저장 확인
    if not test_database_storage():
        logger.error("❌ 데이터베이스 저장 확인 실패")
        return 1
    
    logger.info("🎉 모든 테스트가 성공적으로 완료되었습니다!")
    logger.info("✅ 오디오 입력부터 DB 저장까지 전체 파이프라인이 정상 작동합니다.")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 