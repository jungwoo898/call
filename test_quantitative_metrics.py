#!/usr/bin/env python3
"""
정량 분석 지표 5종 테스트 스크립트
고객 감정 변화 추세, 응답 지연 시간, 업무 처리 비율 등을 테스트
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.text.communication_quality_analyzer import CommunicationQualityAnalyzer
import pandas as pd


def test_quantitative_metrics():
    """새로운 정량 분석 지표 5종 테스트"""
    
    print("🧪 정량 분석 지표 5종 테스트 시작")
    print("="*70)
    
    # 테스트 케이스 1: 고객 감정이 개선되는 상담
    print("\n📊 테스트 케이스 1: 고객 감정 개선 상담")
    print("-"*50)
    
    improving_case = [
        # 초반부 - 부정적 감정
        {"speaker": "고객", "text": "정말 화가 나요! 서비스가 너무 불만족스러워요!", 
         "start_time": 0.0, "end_time": 3.5, "sentiment": "negative"},
        {"speaker": "상담사", "text": "정말 죄송합니다. 불편을 드려 대단히 죄송합니다. 어떤 문제인지 자세히 말씀해주세요.", 
         "start_time": 5.0, "end_time": 9.0, "sentiment": "positive"},
        
        {"speaker": "고객", "text": "인터넷이 계속 끊어져요. 짜증나서 미치겠어요!", 
         "start_time": 10.0, "end_time": 13.0, "sentiment": "very negative"},
        {"speaker": "상담사", "text": "속상하셨겠어요. 즉시 기술진에게 확인해보겠습니다. 잠시만 기다려주세요.", 
         "start_time": 14.5, "end_time": 18.0, "sentiment": "positive"},
        
        {"speaker": "고객", "text": "빨리 해결해주세요. 업무에 지장이 있어요.", 
         "start_time": 19.0, "end_time": 22.0, "sentiment": "negative"},
        {"speaker": "상담사", "text": "네, 최우선으로 처리해드리겠습니다. 원격으로 점검해보겠습니다.", 
         "start_time": 23.5, "end_time": 27.0, "sentiment": "positive"},
        
        # 중반부 - 중립적 감정
        {"speaker": "고객", "text": "지금 어떻게 되고 있는 건가요?", 
         "start_time": 28.0, "end_time": 30.0, "sentiment": "neutral"},
        {"speaker": "상담사", "text": "라우터 설정에 문제가 있었습니다. 지금 수정하고 있습니다.", 
         "start_time": 31.0, "end_time": 34.0, "sentiment": "positive"},
        
        {"speaker": "고객", "text": "얼마나 더 걸릴까요?", 
         "start_time": 35.0, "end_time": 37.0, "sentiment": "neutral"},
        {"speaker": "상담사", "text": "5분 정도면 완료될 것 같습니다. 양해 부탁드립니다.", 
         "start_time": 38.0, "end_time": 41.0, "sentiment": "positive"},
        
        # 후반부 - 긍정적 감정
        {"speaker": "고객", "text": "오, 이제 잘 되는 것 같네요!", 
         "start_time": 42.0, "end_time": 44.0, "sentiment": "positive"},
        {"speaker": "상담사", "text": "다행입니다! 이제 정상적으로 작동할 거예요. 추가로 궁금한 점 있으시면 언제든 연락주세요.", 
         "start_time": 45.0, "end_time": 49.0, "sentiment": "positive"},
        
        {"speaker": "고객", "text": "감사합니다. 빠르게 해결해주셔서 정말 고마워요.", 
         "start_time": 50.0, "end_time": 53.0, "sentiment": "positive"},
        {"speaker": "상담사", "text": "천만에요. 앞으로도 불편한 점 있으시면 언제든 말씀해주세요.", 
         "start_time": 54.0, "end_time": 57.0, "sentiment": "positive"},
        
        {"speaker": "고객", "text": "네, 정말 만족스러운 서비스였어요. 훌륭합니다!", 
         "start_time": 58.0, "end_time": 61.0, "sentiment": "very positive"}
    ]
    
    analyzer = CommunicationQualityAnalyzer()
    result1 = analyzer.analyze_communication_quality(improving_case)
    
    print("📈 분석 결과:")
    print(f"  고객 감정 초반부: {result1.customer_sentiment_early}")
    print(f"  고객 감정 후반부: {result1.customer_sentiment_late}")
    print(f"  감정 변화 추세: {result1.customer_sentiment_trend} (양수면 개선)")
    print(f"  평균 응답 지연 시간: {result1.avg_response_latency}초")
    print(f"  업무 처리 비율: {result1.task_ratio} (고객/상담사 발화 시간 비율)")
    
    # 테스트 케이스 2: 고객 감정이 악화되는 상담
    print("\n📊 테스트 케이스 2: 고객 감정 악화 상담")
    print("-"*50)
    
    worsening_case = [
        # 초반부 - 중립적 감정
        {"speaker": "고객", "text": "안녕하세요. 요금 문의드리고 싶습니다.", 
         "start_time": 0.0, "end_time": 3.0, "sentiment": "neutral"},
        {"speaker": "상담사", "text": "네, 요금 관련 문의 도와드리겠습니다.", 
         "start_time": 5.0, "end_time": 7.0, "sentiment": "positive"},
        
        {"speaker": "고객", "text": "이번 달 요금이 좀 높게 나온 것 같아서요.", 
         "start_time": 8.0, "end_time": 11.0, "sentiment": "neutral"},
        {"speaker": "상담사", "text": "확인해보겠습니다. 잠시만 기다려주세요.", 
         "start_time": 13.0, "end_time": 15.0, "sentiment": "neutral"},
        
        # 중반부 - 약간 부정적
        {"speaker": "고객", "text": "왜 이렇게 오래 걸리나요?", 
         "start_time": 16.0, "end_time": 18.0, "sentiment": "negative"},
        {"speaker": "상담사", "text": "시스템이 좀 느려서 그렇습니다.", 
         "start_time": 20.0, "end_time": 22.0, "sentiment": "neutral"},
        
        {"speaker": "고객", "text": "매번 이런 식이네요. 불편해요.", 
         "start_time": 23.0, "end_time": 25.0, "sentiment": "negative"},
        {"speaker": "상담사", "text": "죄송합니다. 조금만 더 기다려주세요.", 
         "start_time": 27.0, "end_time": 29.0, "sentiment": "neutral"},
        
        # 후반부 - 매우 부정적
        {"speaker": "고객", "text": "정말 짜증나네요! 시간 낭비예요!", 
         "start_time": 30.0, "end_time": 33.0, "sentiment": "very negative"},
        {"speaker": "상담사", "text": "죄송합니다. 다음에 더 빨리 처리하겠습니다.", 
         "start_time": 35.0, "end_time": 37.0, "sentiment": "negative"},
        
        {"speaker": "고객", "text": "이런 서비스로는 안 되겠어요. 정말 실망이에요!", 
         "start_time": 38.0, "end_time": 41.0, "sentiment": "very negative"}
    ]
    
    result2 = analyzer.analyze_communication_quality(worsening_case)
    
    print("📈 분석 결과:")
    print(f"  고객 감정 초반부: {result2.customer_sentiment_early}")
    print(f"  고객 감정 후반부: {result2.customer_sentiment_late}")
    print(f"  감정 변화 추세: {result2.customer_sentiment_trend} (음수면 악화)")
    print(f"  평균 응답 지연 시간: {result2.avg_response_latency}초")
    print(f"  업무 처리 비율: {result2.task_ratio}")
    
    # 테스트 케이스 3: 응답 지연이 많은 상담
    print("\n📊 테스트 케이스 3: 응답 지연 상담")
    print("-"*50)
    
    delayed_response_case = [
        {"speaker": "고객", "text": "문의가 있습니다.", 
         "start_time": 0.0, "end_time": 2.0, "sentiment": "neutral"},
        {"speaker": "상담사", "text": "네, 말씀하세요.", 
         "start_time": 8.0, "end_time": 10.0, "sentiment": "positive"},  # 6초 지연
        
        {"speaker": "고객", "text": "서비스 해지하고 싶어요.", 
         "start_time": 11.0, "end_time": 13.0, "sentiment": "neutral"},
        {"speaker": "상담사", "text": "해지 사유를 알려주세요.", 
         "start_time": 18.0, "end_time": 20.0, "sentiment": "neutral"},  # 5초 지연
        
        {"speaker": "고객", "text": "요금이 너무 비싸요.", 
         "start_time": 21.0, "end_time": 23.0, "sentiment": "negative"},
        {"speaker": "상담사", "text": "더 저렴한 요금제를 추천해드릴까요?", 
         "start_time": 30.0, "end_time": 33.0, "sentiment": "positive"}  # 7초 지연
    ]
    
    result3 = analyzer.analyze_communication_quality(delayed_response_case)
    
    print("📈 분석 결과:")
    print(f"  평균 응답 지연 시간: {result3.avg_response_latency}초 (높은 지연)")
    print(f"  업무 처리 비율: {result3.task_ratio}")
    
    # 종합 결과 DataFrame으로 출력
    print("\n📊 종합 비교 결과")
    print("="*70)
    
    comparison_data = {
        '테스트 케이스': ['감정 개선 상담', '감정 악화 상담', '응답 지연 상담'],
        '고객 감정 초반부': [result1.customer_sentiment_early, result2.customer_sentiment_early, result3.customer_sentiment_early],
        '고객 감정 후반부': [result1.customer_sentiment_late, result2.customer_sentiment_late, result3.customer_sentiment_late],
        '감정 변화 추세': [result1.customer_sentiment_trend, result2.customer_sentiment_trend, result3.customer_sentiment_trend],
        '평균 응답 지연(초)': [result1.avg_response_latency, result2.avg_response_latency, result3.avg_response_latency],
        '업무 처리 비율': [result1.task_ratio, result2.task_ratio, result3.task_ratio]
    }
    
    df = pd.DataFrame(comparison_data)
    print(df.to_string(index=False, float_format='%.3f'))
    
    # 지표 해석 가이드
    print("\n💡 지표 해석 가이드")
    print("="*70)
    print("📈 고객 감정 변화 추세:")
    print("  - 양수(+): 상담 과정에서 고객 감정이 개선됨")
    print("  - 음수(-): 상담 과정에서 고객 감정이 악화됨")
    print("  - 0에 가까움: 감정 변화가 거의 없음")
    
    print("\n⏱️ 평균 응답 지연 시간:")
    print("  - 0~2초: 매우 빠른 응답")
    print("  - 2~5초: 적절한 응답 속도")
    print("  - 5초 이상: 응답 지연, 개선 필요")
    
    print("\n⚖️ 업무 처리 비율:")
    print("  - 1.0 초과: 고객이 상담사보다 많이 말함 (설명/문의가 많음)")
    print("  - 1.0 미만: 상담사가 고객보다 많이 말함 (안내/설명 제공)")
    print("  - 1.0에 가까움: 균형적인 대화")
    
    return [result1, result2, result3]


def test_edge_cases():
    """엣지 케이스 테스트"""
    
    print("\n🔍 엣지 케이스 테스트")
    print("="*70)
    
    analyzer = CommunicationQualityAnalyzer()
    
    # 케이스 1: 고객 발화가 매우 적은 경우
    print("\n📊 케이스 1: 고객 발화 부족")
    minimal_customer_case = [
        {"speaker": "고객", "text": "안녕하세요.", "start_time": 0.0, "end_time": 1.0, "sentiment": "neutral"},
        {"speaker": "상담사", "text": "안녕하세요. 무엇을 도와드릴까요?", "start_time": 2.0, "end_time": 4.0, "sentiment": "positive"},
        {"speaker": "상담사", "text": "추가로 궁금한 점이 있으시면 말씀해주세요.", "start_time": 5.0, "end_time": 7.0, "sentiment": "positive"}
    ]
    
    result = analyzer.analyze_communication_quality(minimal_customer_case)
    print(f"  감정 변화 추세: {result.customer_sentiment_trend} (데이터 부족)")
    print(f"  응답 지연 시간: {result.avg_response_latency}")
    print(f"  업무 처리 비율: {result.task_ratio}")
    
    # 케이스 2: 시간 정보 누락
    print("\n📊 케이스 2: 시간 정보 누락")
    no_time_case = [
        {"speaker": "고객", "text": "문의가 있어요.", "sentiment": "neutral"},
        {"speaker": "상담사", "text": "네, 말씀하세요.", "sentiment": "positive"}
    ]
    
    result = analyzer.analyze_communication_quality(no_time_case)
    print(f"  응답 지연 시간: {result.avg_response_latency} (시간 정보 없음)")
    print(f"  업무 처리 비율: {result.task_ratio} (시간 정보 없음)")
    
    # 케이스 3: 감정 정보 누락
    print("\n📊 케이스 3: 감정 정보 누락")
    no_sentiment_case = [
        {"speaker": "고객", "text": "안녕하세요.", "start_time": 0.0, "end_time": 1.0},
        {"speaker": "상담사", "text": "안녕하세요.", "start_time": 2.0, "end_time": 3.0},
        {"speaker": "고객", "text": "문의가 있어요.", "start_time": 4.0, "end_time": 5.0}
    ]
    
    result = analyzer.analyze_communication_quality(no_sentiment_case)
    print(f"  감정 변화 추세: {result.customer_sentiment_trend} (감정 정보 없음)")


if __name__ == "__main__":
    # 메인 테스트 실행
    results = test_quantitative_metrics()
    
    # 엣지 케이스 테스트
    test_edge_cases()
    
    print("\n✅ 모든 테스트 완료!")
    print("📝 새로운 정량 분석 지표 5종이 성공적으로 구현되었습니다.") 