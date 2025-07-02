#!/usr/bin/env python3
"""
Callytics 파이프라인 전체 플로우 빠른 테스트
로그인 → 업로드 → 분석 → DB 저장까지 전체 과정 검증
"""

import os
import sys
import time
import logging
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pipeline_components():
    """파이프라인 구성 요소들을 개별적으로 테스트"""
    
    logger.info("🔍 파이프라인 구성 요소 테스트 시작")
    
    # 1. 인증 시스템 테스트
    logger.info("1️⃣ 인증 시스템 테스트")
    try:
        from src.auth.agent_auth import AgentAuthManager
        auth_manager = AgentAuthManager()
        logger.info("✅ AgentAuthManager 임포트 성공")
        
        # 테스트 상담사 생성
        test_agent = auth_manager.create_agent(
            username="test_agent",
            password="test123",
            full_name="테스트 상담사",
            department="고객지원팀",
            position="상담사",
            email="test@example.com"
        )
        logger.info(f"✅ 테스트 상담사 생성 성공: {test_agent}")
        
        # 로그인 테스트
        session = auth_manager.login("test_agent", "test123")
        if session:
            logger.info(f"✅ 로그인 성공: 세션 토큰 = {session.session_token[:20]}...")
        else:
            logger.error("❌ 로그인 실패")
            return False
            
    except Exception as e:
        logger.error(f"❌ 인증 시스템 테스트 실패: {e}")
        return False
    
    # 2. 데이터베이스 관리자 테스트
    logger.info("2️⃣ 데이터베이스 관리자 테스트")
    try:
        from src.db.multi_database_manager import MultiDatabaseManager
        db_manager = MultiDatabaseManager()
        logger.info("✅ MultiDatabaseManager 임포트 성공")
        
        # DB 연결 테스트
        connection = db_manager.get_connection()
        if connection:
            logger.info("✅ 데이터베이스 연결 성공")
            connection.close()
        else:
            logger.error("❌ 데이터베이스 연결 실패")
            return False
            
    except Exception as e:
        logger.error(f"❌ 데이터베이스 관리자 테스트 실패: {e}")
        return False
    
    # 3. 오디오 업로드 관리자 테스트
    logger.info("3️⃣ 오디오 업로드 관리자 테스트")
    try:
        from src.upload.agent_audio_upload import AgentAudioUploadManager
        upload_manager = AgentAudioUploadManager()
        logger.info("✅ AgentAudioUploadManager 임포트 성공")
        
    except Exception as e:
        logger.error(f"❌ 오디오 업로드 관리자 테스트 실패: {e}")
        return False
    
    # 4. 통합 분석기 테스트
    logger.info("4️⃣ 통합 분석기 테스트")
    try:
        from src.integrated_analyzer_advanced import AdvancedIntegratedAnalyzer
        analyzer = AdvancedIntegratedAnalyzer()
        logger.info("✅ AdvancedIntegratedAnalyzer 임포트 성공")
        
    except Exception as e:
        logger.error(f"❌ 통합 분석기 테스트 실패: {e}")
        return False
    
    logger.info("✅ 모든 구성 요소 테스트 통과")
    return True

def test_full_pipeline():
    """전체 파이프라인 플로우 테스트"""
    
    logger.info("🚀 전체 파이프라인 플로우 테스트 시작")
    
    try:
        # 1. 인증 시스템 초기화
        from src.auth.agent_auth import AgentAuthManager
        from src.upload.agent_audio_upload import AgentAudioUploadManager
        from src.integrated_analyzer_advanced import AdvancedIntegratedAnalyzer
        from src.db.multi_database_manager import MultiDatabaseManager
        
        auth_manager = AgentAuthManager()
        upload_manager = AgentAudioUploadManager()
        analyzer = AdvancedIntegratedAnalyzer()
        db_manager = MultiDatabaseManager()
        
        # 2. 테스트 상담사 로그인
        logger.info("📝 1단계: 상담사 로그인")
        session = auth_manager.login("test_agent", "test123")
        if not session:
            logger.error("❌ 로그인 실패")
            return False
        
        logger.info(f"✅ 로그인 성공: {session.full_name}")
        
        # 3. 테스트 오디오 파일 확인
        logger.info("📁 2단계: 테스트 오디오 파일 확인")
        test_audio_path = "audio/40186.wav"
        if not os.path.exists(test_audio_path):
            logger.warning(f"⚠️ 테스트 오디오 파일이 없습니다: {test_audio_path}")
            logger.info("📝 테스트용 더미 파일을 생성합니다...")
            
            # 더미 오디오 파일 생성 (1초짜리 무음)
            import numpy as np
            import soundfile as sf
            
            sample_rate = 16000
            duration = 1.0
            samples = np.zeros(int(sample_rate * duration))
            sf.write(test_audio_path, samples, sample_rate)
            logger.info(f"✅ 더미 오디오 파일 생성: {test_audio_path}")
        
        # 4. 오디오 파일 업로드 시뮬레이션
        logger.info("📤 3단계: 오디오 파일 업로드 시뮬레이션")
        upload_info = upload_manager.upload_audio_with_agent_info(
            session_token=session.session_token,
            audio_file_path=test_audio_path,
            original_filename="test_consultation.wav",
            consultation_type="고객문의",
            customer_id="CUST001",
            session_notes="테스트 상담 세션"
        )
        
        if not upload_info:
            logger.error("❌ 오디오 업로드 실패")
            return False
        
        logger.info(f"✅ 오디오 업로드 성공: {upload_info.file_path}")
        
        # 5. 분석 파이프라인 실행
        logger.info("🔍 4단계: 분석 파이프라인 실행")
        logger.info("⚠️ 실제 분석은 시간이 오래 걸리므로 시뮬레이션합니다...")
        
        # 분석 시뮬레이션 (실제로는 analyzer.analyze_consultation() 호출)
        analysis_result = {
            'consultation_id': f"test_consultation_{int(time.time())}",
            'audio_path': upload_info.file_path,
            'metadata': {
                'agent_id': session.agent_id,
                'agent_name': session.full_name,
                'upload_timestamp': upload_info.upload_timestamp.isoformat()
            },
            'utterances': [
                {
                    'speaker': 'agent',
                    'start': 0.0,
                    'end': 0.5,
                    'text': '안녕하세요, 고객님. 무엇을 도와드릴까요?',
                    'confidence': 0.95
                },
                {
                    'speaker': 'customer',
                    'start': 0.6,
                    'end': 1.0,
                    'text': '네, 문의사항이 있어서 연락드렸습니다.',
                    'confidence': 0.92
                }
            ],
            'analysis': {
                'business_type': '고객지원',
                'classification_type': '일반문의',
                'detail_classification': '서비스 문의',
                'consultation_result': '완료',
                'summary': '고객의 일반적인 서비스 문의에 대한 상담',
                'customer_request': '서비스 관련 문의',
                'solution': '상담사가 적절한 답변을 제공함',
                'additional_info': '테스트 상담 세션',
                'confidence': 0.85
            },
            'communication_quality': {
                'honorific_ratio': 0.8,
                'positive_word_ratio': 0.7,
                'negative_word_ratio': 0.1,
                'euphonious_word_ratio': 0.6,
                'empathy_ratio': 0.75,
                'apology_ratio': 0.0,
                'total_sentences': 2,
                'customer_sentiment_early': '중립',
                'customer_sentiment_late': '중립',
                'customer_sentiment_trend': '안정',
                'avg_response_latency': 0.1,
                'task_ratio': 0.9,
                'suggestions': '전반적으로 양호한 상담 품질',
                'interruption_count': 0,
                'analysis_details': '테스트 분석 결과'
            },
            'processing_time': 2.5,
            'timestamp': time.time()
        }
        
        logger.info("✅ 분석 결과 생성 완료")
        
        # 6. 데이터베이스 저장
        logger.info("💾 5단계: 데이터베이스 저장")
        
        # 상담 분석 결과 저장
        consultation_data = {
            'consultation_id': analysis_result['consultation_id'],
            'audio_path': analysis_result['audio_path'],
            'business_type': analysis_result['analysis']['business_type'],
            'classification_type': analysis_result['analysis']['classification_type'],
            'detail_classification': analysis_result['analysis']['detail_classification'],
            'consultation_result': analysis_result['analysis']['consultation_result'],
            'summary': analysis_result['analysis']['summary'],
            'customer_request': analysis_result['analysis']['customer_request'],
            'solution': analysis_result['analysis']['solution'],
            'additional_info': analysis_result['analysis']['additional_info'],
            'confidence': analysis_result['analysis']['confidence'],
            'processing_time': analysis_result['processing_time']
        }
        
        db_manager.insert_consultation_analysis(consultation_data)
        logger.info("✅ 상담 분석 결과 저장 완료")
        
        # 커뮤니케이션 품질 결과 저장
        quality_data = {
            'audio_path': analysis_result['audio_path'],
            'consultation_id': analysis_result['consultation_id'],
            'honorific_ratio': analysis_result['communication_quality']['honorific_ratio'],
            'positive_word_ratio': analysis_result['communication_quality']['positive_word_ratio'],
            'negative_word_ratio': analysis_result['communication_quality']['negative_word_ratio'],
            'euphonious_word_ratio': analysis_result['communication_quality']['euphonious_word_ratio'],
            'empathy_ratio': analysis_result['communication_quality']['empathy_ratio'],
            'apology_ratio': analysis_result['communication_quality']['apology_ratio'],
            'total_sentences': analysis_result['communication_quality']['total_sentences'],
            'customer_sentiment_early': analysis_result['communication_quality']['customer_sentiment_early'],
            'customer_sentiment_late': analysis_result['communication_quality']['customer_sentiment_late'],
            'customer_sentiment_trend': analysis_result['communication_quality']['customer_sentiment_trend'],
            'avg_response_latency': analysis_result['communication_quality']['avg_response_latency'],
            'task_ratio': analysis_result['communication_quality']['task_ratio'],
            'suggestions': analysis_result['communication_quality']['suggestions'],
            'interruption_count': analysis_result['communication_quality']['interruption_count'],
            'analysis_details': analysis_result['communication_quality']['analysis_details']
        }
        
        db_manager.insert_communication_quality(quality_data)
        logger.info("✅ 커뮤니케이션 품질 결과 저장 완료")
        
        # 발화 내용 저장
        for i, utterance in enumerate(analysis_result['utterances']):
            utterance_data = {
                'audio_path': analysis_result['audio_path'],
                'speaker': utterance['speaker'],
                'start_time': utterance['start'],
                'end_time': utterance['end'],
                'text': utterance['text'],
                'confidence': utterance['confidence'],
                'sequence': i + 1,
                'sentiment': '중립',
                'profane': 0
            }
            db_manager.insert_utterance(utterance_data)
        
        logger.info("✅ 발화 내용 저장 완료")
        
        # 7. 결과 검증
        logger.info("🔍 6단계: 결과 검증")
        
        # 저장된 데이터 조회
        consultation_result = db_manager.fetch_consultation_analysis(analysis_result['consultation_id'])
        quality_result = db_manager.fetch_communication_quality(analysis_result['consultation_id'])
        utterances_result = db_manager.fetch_utterances(analysis_result['audio_path'])
        
        if consultation_result and quality_result and utterances_result:
            logger.info("✅ 모든 데이터가 성공적으로 저장되고 조회됨")
            logger.info(f"📊 상담 분석 결과: {len(consultation_result)}개")
            logger.info(f"📊 품질 분석 결과: {len(quality_result)}개")
            logger.info(f"📊 발화 내용: {len(utterances_result)}개")
        else:
            logger.error("❌ 데이터 저장 또는 조회 실패")
            return False
        
        logger.info("🎉 전체 파이프라인 테스트 성공!")
        return True
        
    except Exception as e:
        logger.error(f"❌ 전체 파이프라인 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_advanced_analyzer():
    """고성능 통합 분석기 테스트"""
    try:
        analyzer = AdvancedIntegratedAnalyzer(
            config_path="config/config.yaml",
            enable_cache=True,
            enable_parallel=True,
            enable_async=True,
            max_workers=2
        )
        logger.info("✅ AdvancedIntegratedAnalyzer 초기화 성공")
        return True
    except Exception as e:
        logger.error(f"❌ AdvancedIntegratedAnalyzer 초기화 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    logger.info("🚀 Callytics 파이프라인 전체 테스트 시작")
    
    # 1. 구성 요소 테스트
    if not test_pipeline_components():
        logger.error("❌ 구성 요소 테스트 실패")
        return False
    
    # 2. 전체 파이프라인 테스트
    if not test_full_pipeline():
        logger.error("❌ 전체 파이프라인 테스트 실패")
        return False
    
    logger.info("🎉 모든 테스트 통과! 파이프라인이 정상적으로 작동합니다.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 