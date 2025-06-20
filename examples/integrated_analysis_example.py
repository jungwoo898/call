#!/usr/bin/env python3
"""
통합 상담 분석 사용 예제

이 예제는 오디오 파일을 입력받아 화자 분리, 음성 인식, ChatGPT 분석을 수행하고
결과를 데이터베이스에 저장하는 전체 파이프라인을 보여줍니다.
"""

import os
import sys
import time
from typing import Dict, Any

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.integrated_analyzer import IntegratedAnalyzer, AnalysisConfig
from src.database_manager import DatabaseManager

def example_single_file_analysis():
    """단일 파일 분석 예제"""
    print("=" * 60)
    print("단일 파일 분석 예제")
    print("=" * 60)
    
    # OpenAI API 키 설정 (환경 변수에서 가져오거나 직접 설정)
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY 환경 변수를 설정해주세요.")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # 분석 설정
    config = AnalysisConfig(
        openai_api_key=api_key,
        model="gpt-4",
        max_tokens=2000,
        temperature=0.1,
        db_path="Callytics_new.sqlite",
        language="ko",
        device="auto"
    )
    
    # 데이터베이스 매니저 초기화
    db_manager = DatabaseManager(
        config_path="config/config_enhanced.yaml",
        db_path="Callytics_new.sqlite",
    )
    
    # 통합 분석기 초기화
    print("🚀 통합 분석기 초기화 중...")
    analyzer = IntegratedAnalyzer(config)
    
    # 테스트 오디오 파일 경로 (실제 파일 경로로 변경하세요)
    audio_file = "audio/40186.wav"  # 예시 파일
    
    if not os.path.exists(audio_file):
        print(f"❌ 오디오 파일을 찾을 수 없습니다: {audio_file}")
        print("실제 오디오 파일 경로로 변경해주세요.")
        return
    
    # 파일 처리
    print(f"\n📁 파일 처리 시작: {audio_file}")
    start_time = time.time()
    
    result = analyzer.process_audio_file(audio_file)
    
    processing_time = time.time() - start_time
    
    # 결과 출력
    if result.get("success"):
        print(f"\n✅ 처리 완료! (총 소요시간: {processing_time:.2f}초)")
        print(f"\n📊 분석 결과:")
        print(f"   - 오디오 파일 ID: {result['audio_properties_id']}")
        print(f"   - 발화 수: {result['utterances_count']}")
        print(f"   - 업무 유형: {result['analysis_result']['business_type']}")
        print(f"   - 분류 유형: {result['analysis_result']['classification_type']}")
        print(f"   - 세부 분류: {result['analysis_result']['detail_classification']}")
        print(f"   - 상담 결과: {result['analysis_result']['consultation_result']}")
        print(f"   - 요약: {result['analysis_result']['summary']}")
        print(f"   - 고객 요청사항: {result['analysis_result']['customer_request']}")
        print(f"   - 해결방안: {result['analysis_result']['solution']}")
        print(f"   - 추가 안내사항: {result['analysis_result']['additional_info']}")
        print(f"   - 신뢰도: {result['analysis_result']['confidence']:.2f}")
        
        # 대화 내용 미리보기
        conversation_preview = result['conversation_text'][:200] + "..." if len(result['conversation_text']) > 200 else result['conversation_text']
        print(f"\n💬 대화 내용 미리보기:")
        print(f"   {conversation_preview}")
        
    else:
        print(f"\n❌ 처리 실패: {result.get('error', '알 수 없는 오류')}")

def example_batch_analysis():
    """일괄 분석 예제"""
    print("\n" + "=" * 60)
    print("일괄 분석 예제")
    print("=" * 60)
    
    # OpenAI API 키 설정
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY 환경 변수를 설정해주세요.")
        return
    
    # 분석 설정
    config = AnalysisConfig(
        openai_api_key=api_key,
        model="gpt-4",
        max_tokens=2000,
        temperature=0.1,
        db_path="Callytics_new.sqlite",
        language="ko",
        device="auto"
    )
    
    # 데이터베이스 매니저 초기화
    db_manager = DatabaseManager(
        config_path="config/config_enhanced.yaml",
        db_path="Callytics_new.sqlite",
    )
    
    # 통합 분석기 초기화
    print("🚀 통합 분석기 초기화 중...")
    analyzer = IntegratedAnalyzer(config)
    
    # 테스트 디렉토리 경로 (실제 디렉토리 경로로 변경하세요)
    audio_directory = "audio"
    
    if not os.path.exists(audio_directory):
        print(f"❌ 오디오 디렉토리를 찾을 수 없습니다: {audio_directory}")
        print("실제 오디오 파일이 있는 디렉토리 경로로 변경해주세요.")
        return
    
    # 지원하는 오디오 파일 찾기
    supported_formats = ['.wav', '.mp3', '.m4a', '.flac', '.ogg']
    audio_files = []
    
    for file in os.listdir(audio_directory):
        if any(file.lower().endswith(fmt) for fmt in supported_formats):
            audio_files.append(os.path.join(audio_directory, file))
    
    if not audio_files:
        print("처리할 오디오 파일을 찾을 수 없습니다.")
        return
    
    print(f"📁 발견된 오디오 파일: {len(audio_files)}개")
    for file in audio_files:
        print(f"   - {os.path.basename(file)}")
    
    # 일괄 처리
    print(f"\n🔄 일괄 처리 시작...")
    start_time = time.time()
    
    results = analyzer.batch_process(audio_files)
    
    total_time = time.time() - start_time
    
    # 결과 요약
    success_count = sum(1 for r in results if r.get("success"))
    print(f"\n📈 일괄 처리 결과 요약:")
    print(f"   - 총 파일 수: {len(audio_files)}")
    print(f"   - 성공: {success_count}")
    print(f"   - 실패: {len(audio_files) - success_count}")
    print(f"   - 총 소요시간: {total_time:.2f}초")
    print(f"   - 평균 처리시간: {total_time/len(audio_files):.2f}초/파일")
    
    # 성공한 결과들의 분석 통계
    if success_count > 0:
        business_types = {}
        classification_types = {}
        consultation_results = {}
        
        for result in results:
            if result.get("success"):
                analysis = result['analysis_result']
                
                # 업무 유형 통계
                business_type = analysis['business_type']
                business_types[business_type] = business_types.get(business_type, 0) + 1
                
                # 분류 유형 통계
                classification_type = analysis['classification_type']
                classification_types[classification_type] = classification_types.get(classification_type, 0) + 1
                
                # 상담 결과 통계
                consultation_result = analysis['consultation_result']
                consultation_results[consultation_result] = consultation_results.get(consultation_result, 0) + 1
        
        print(f"\n📊 분석 통계:")
        print(f"   업무 유형 분포:")
        for bt, count in business_types.items():
            print(f"     - {bt}: {count}건")
        
        print(f"   분류 유형 분포:")
        for ct, count in classification_types.items():
            print(f"     - {ct}: {count}건")
        
        print(f"   상담 결과 분포:")
        for cr, count in consultation_results.items():
            print(f"     - {cr}: {count}건")

def example_analysis_summary():
    """분석 요약 조회 예제"""
    print("\n" + "=" * 60)
    print("분석 요약 조회 예제")
    print("=" * 60)
    
    # 분석 설정
    config = AnalysisConfig(
        openai_api_key="dummy",  # 요약 조회에는 API 키가 필요 없음
        db_path="Callytics_new.sqlite"
    )
    
    # 데이터베이스 매니저 초기화
    db_manager = DatabaseManager(
        config_path="config/config_enhanced.yaml",
        db_path="Callytics_new.sqlite",
    )
    
    # 통합 분석기 초기화
    print("🚀 통합 분석기 초기화 중...")
    analyzer = IntegratedAnalyzer(config)
    
    # 특정 오디오 파일의 분석 요약 조회 (실제 ID로 변경하세요)
    audio_properties_id = 1  # 예시 ID
    
    print(f"\n📋 오디오 파일 ID {audio_properties_id}의 분석 요약 조회...")
    summary = analyzer.get_analysis_summary(audio_properties_id)
    
    if "error" not in summary:
        print(f"✅ 분석 요약 조회 성공!")
        print(f"   - 오디오 정보: {summary.get('audio_info', [])}")
        print(f"   - 발화 수: {summary.get('utterances_count', 0)}")
        print(f"   - 분석 결과: {summary.get('analysis_result', [])}")
    else:
        print(f"❌ 분석 요약 조회 실패: {summary['error']}")

def main():
    """메인 함수"""
    print("🎯 Callytics 통합 상담 분석 시스템 예제")
    print("이 예제는 오디오 파일을 분석하여 상담 내용을 분류하고 평가합니다.")
    
    # 환경 설정 확인
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("\n⚠️  주의사항:")
        print("   - OpenAI API 키가 설정되지 않았습니다.")
        print("   - ChatGPT 분석 기능을 사용하려면 API 키가 필요합니다.")
        print("   - 환경 변수 설정: export OPENAI_API_KEY='your-api-key-here'")
        print("   - 또는 코드에서 직접 설정하세요.")
    
    # 예제 실행
    try:
        # 1. 단일 파일 분석 예제
        example_single_file_analysis()
        
        # 2. 일괄 분석 예제
        example_batch_analysis()
        
        # 3. 분석 요약 조회 예제
        example_analysis_summary()
        
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 예제 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 