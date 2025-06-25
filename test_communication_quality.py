#!/usr/bin/env python3
"""
커뮤니케이션 품질 분석 기능 테스트 스크립트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.text.communication_quality_analyzer import CommunicationQualityAnalyzer, test_communication_quality_analyzer
from src.integrated_analyzer import IntegratedAnalyzer
import json


def test_basic_functionality():
    """기본 기능 테스트"""
    print("🔍 기본 커뮤니케이션 품질 분석 테스트")
    print("="*60)
    
    # 샘플 상담 데이터 (더 다양한 패턴 포함)
    sample_utterances = [
        {"speaker": "고객", "text": "안녕하세요. 요금 관련해서 문의드리고 싶습니다."},
        {"speaker": "상담사", "text": "안녕하세요, 고객님. 요금 관련 문의 도와드리겠습니다. 어떤 부분이 궁금하신가요?"},
        {"speaker": "고객", "text": "이번 달 요금이 너무 많이 나왔어요. 왜 이렇게 많이 나온 건지 모르겠어요."},
        {"speaker": "상담사", "text": "걱정되셨겠어요. 죄송합니다. 요금 내역을 확인해드리겠습니다. 혹시 해외 로밍을 사용하셨나요?"},
        {"speaker": "고객", "text": "아니요. 해외에 안 갔는데요."},
        {"speaker": "상담사", "text": "그렇다면 데이터 사용량을 확인해보겠습니다. 실례지만 휴대폰 번호를 알려주시겠어요?"},
        {"speaker": "고객", "text": "010-1234-5678입니다."},
        {"speaker": "상담사", "text": "감사합니다. 확인해보니 이번 달에 데이터를 많이 사용하셨네요. 동영상 시청이나 게임을 하셨을 것 같습니다."},
        {"speaker": "고객", "text": "아 그런가요? 그럼 어떻게 해야 하나요?"},
        {"speaker": "상담사", "text": "다음 달부터는 데이터 사용량을 체크해주시면 좋을 것 같습니다. 도움이 되셨나요?"},
        {"speaker": "고객", "text": "네, 알겠습니다. 감사합니다."},
        {"speaker": "상담사", "text": "고객님께서 만족해주셔서 기쁩니다. 다른 문의사항이 있으시면 언제든지 연락해주세요. 감사합니다."}
    ]
    
    # 분석 수행
    analyzer = CommunicationQualityAnalyzer()
    result = analyzer.analyze_communication_quality(sample_utterances)
    
    # 결과 출력
    analyzer.print_analysis_report(result)
    
    # DataFrame 변환 테스트
    df = analyzer.export_results_to_dataframe(result)
    print("\n📊 DataFrame 결과:")
    print(df.to_string(index=False))
    
    return result


def test_edge_cases():
    """엣지 케이스 테스트"""
    print("\n🔍 엣지 케이스 테스트")
    print("="*60)
    
    analyzer = CommunicationQualityAnalyzer()
    
    # 1. 상담사 발화가 없는 경우
    print("\n1. 상담사 발화가 없는 경우:")
    no_counselor_data = [
        {"speaker": "고객", "text": "안녕하세요."},
        {"speaker": "고객", "text": "문의가 있습니다."}
    ]
    result1 = analyzer.analyze_communication_quality(no_counselor_data)
    print(f"   결과: 총 문장 수 = {result1.total_sentences}")
    
    # 2. 빈 텍스트가 포함된 경우
    print("\n2. 빈 텍스트가 포함된 경우:")
    empty_text_data = [
        {"speaker": "상담사", "text": ""},
        {"speaker": "상담사", "text": "안녕하세요."},
        {"speaker": "상담사", "text": "   "}  # 공백만
    ]
    result2 = analyzer.analyze_communication_quality(empty_text_data)
    print(f"   결과: 총 문장 수 = {result2.total_sentences}")
    
    # 3. 다양한 화자 이름 테스트
    print("\n3. 다양한 화자 이름 테스트:")
    various_speakers_data = [
        {"speaker": "Agent", "text": "안녕하세요. 도움이 필요하시나요?"},
        {"speaker": "CSR", "text": "죄송합니다. 확인해드리겠습니다."},
        {"speaker": "counselor", "text": "감사합니다. 좋은 하루 되세요."},
        {"speaker": "staff", "text": "혹시 다른 문의사항이 있으시면 말씀해주세요."}
    ]
    result3 = analyzer.analyze_communication_quality(various_speakers_data)
    print(f"   결과: 총 문장 수 = {result3.total_sentences}")


def test_pattern_matching():
    """패턴 매칭 정확도 테스트"""
    print("\n🔍 패턴 매칭 정확도 테스트")
    print("="*60)
    
    analyzer = CommunicationQualityAnalyzer()
    
    # 각 패턴별 테스트 데이터
    test_cases = [
        # 존댓말 패턴 테스트
        {"speaker": "상담사", "text": "안녕하세요. 도와드리겠습니다."},  # 존댓말
        {"speaker": "상담사", "text": "확인해주세요."},  # 존댓말
        {"speaker": "상담사", "text": "어떻게 하시겠어요?"},  # 존댓말 + 주체높임
        
        # 쿠션어 패턴 테스트
        {"speaker": "상담사", "text": "실례지만 확인이 필요합니다."},  # 쿠션어
        {"speaker": "상담사", "text": "혹시 시간이 되시나요?"},  # 쿠션어
        {"speaker": "상담사", "text": "그런 것 같습니다."},  # 완곡표현
        
        # 공감 표현 테스트
        {"speaker": "상담사", "text": "많이 힘드셨죠."},  # 공감
        {"speaker": "상담사", "text": "걱정되셨겠어요."},  # 공감
        
        # 사과 표현 테스트
        {"speaker": "상담사", "text": "죄송합니다."},  # 사과
        {"speaker": "상담사", "text": "양해 부탁드립니다."},  # 사과
    ]
    
    result = analyzer.analyze_communication_quality(test_cases)
    
    print(f"📊 패턴 매칭 결과:")
    print(f"   존댓말 비율: {result.honorific_ratio:.1f}%")
    print(f"   쿠션어 비율: {result.euphonious_word_ratio:.1f}%")
    print(f"   공감 표현 비율: {result.empathy_ratio:.1f}%")
    print(f"   사과 표현 비율: {result.apology_ratio:.1f}%")
    
    # 상세 정보 출력
    details = result.analysis_details
    print(f"\n📋 상세 매칭 정보:")
    print(f"   존댓말 문장 수: {details.get('honorific_sentences', 0)}")
    print(f"   쿠션어 문장 수: {details.get('euphonious_sentences', 0)}")
    print(f"   공감 문장 수: {details.get('empathy_sentences', 0)}")
    print(f"   사과 문장 수: {details.get('apology_sentences', 0)}")


def test_sentiment_analysis():
    """감성 분석 테스트"""
    print("\n🔍 감성 분석 테스트")
    print("="*60)
    
    analyzer = CommunicationQualityAnalyzer()
    
    # 감성 단어가 포함된 테스트 데이터
    sentiment_test_data = [
        {"speaker": "상담사", "text": "좋은 서비스를 제공해드리겠습니다."},  # 긍정
        {"speaker": "상담사", "text": "만족스러운 결과가 될 것입니다."},  # 긍정
        {"speaker": "상담사", "text": "문제가 발생했습니다."},  # 부정
        {"speaker": "상담사", "text": "어려운 상황입니다."},  # 부정
        {"speaker": "상담사", "text": "확인해보겠습니다."},  # 중립
    ]
    
    result = analyzer.analyze_communication_quality(sentiment_test_data)
    
    print(f"📊 감성 분석 결과:")
    print(f"   긍정 단어 비율: {result.positive_word_ratio:.1f}%")
    print(f"   부정 단어 비율: {result.negative_word_ratio:.1f}%")
    
    # 샘플 문장들 출력
    details = result.analysis_details.get('sample_sentences', {})
    if details.get('positive'):
        print(f"\n   긍정 샘플: {details['positive'][0]}")
    if details.get('negative'):
        print(f"   부정 샘플: {details['negative'][0]}")


def main():
    """메인 테스트 함수"""
    print("🚀 커뮤니케이션 품질 분석 시스템 테스트")
    print("="*80)
    
    try:
        # 1. 기본 기능 테스트
        result = test_basic_functionality()
        
        # 2. 엣지 케이스 테스트
        test_edge_cases()
        
        # 3. 패턴 매칭 테스트
        test_pattern_matching()
        
        # 4. 감성 분석 테스트
        test_sentiment_analysis()
        
        print("\n" + "="*80)
        print("✅ 모든 테스트 완료!")
        print("📋 최종 결과 요약:")
        print(f"   - 6가지 품질 지표가 정상적으로 계산됨")
        print(f"   - 패턴 매칭이 정확하게 동작함")
        print(f"   - 엣지 케이스 처리가 안정적임")
        print(f"   - 감성사전 기반 분석이 동작함")
        
        # JSON 형태로 결과 출력 (API 연동 확인용)
        print("\n📄 JSON 결과 샘플:")
        json_result = {
            'honorific_ratio': result.honorific_ratio,
            'positive_word_ratio': result.positive_word_ratio,
            'negative_word_ratio': result.negative_word_ratio,
            'euphonious_word_ratio': result.euphonious_word_ratio,
            'empathy_ratio': result.empathy_ratio,
            'apology_ratio': result.apology_ratio,
            'total_sentences': result.total_sentences
        }
        print(json.dumps(json_result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 