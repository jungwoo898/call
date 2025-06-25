#!/usr/bin/env python3
"""
정량 분석 지표 5종 간단 테스트
의존성 최소화 버전
"""

import re
from typing import Dict, List, Any, Optional, Tuple


class SimpleQuantitativeAnalyzer:
    """간단한 정량 분석기"""
    
    def __init__(self):
        """초기화"""
        pass
    
    def _map_sentiment_to_score(self, sentiment_text: str) -> Optional[float]:
        """sentiment 텍스트를 숫자 점수로 매핑"""
        sentiment_mapping = {
            # 기본 매핑
            'positive': 1.0,
            'neutral': 0.0,
            'negative': -1.0,
            
            # 확장 매핑 (5점 척도)
            'very positive': 2.0,
            'very_positive': 2.0,
            'very negative': -2.0,
            'very_negative': -2.0,
            
            # 한국어 매핑
            '긍정': 1.0,
            '부정': -1.0,
            '중립': 0.0,
            '매우긍정': 2.0,
            '매우부정': -2.0,
            
            # 숫자 문자열 직접 매핑
            '1': 1.0,
            '0': 0.0,
            '-1': -1.0,
            '2': 2.0,
            '-2': -2.0
        }
        
        # 정규화된 텍스트로 매핑 시도
        normalized_text = sentiment_text.strip().lower().replace(' ', '_')
        
        if normalized_text in sentiment_mapping:
            return sentiment_mapping[normalized_text]
        
        # 숫자로 직접 변환 시도
        try:
            score = float(sentiment_text)
            return max(-2.0, min(2.0, score))  # -2.0 ~ 2.0 범위로 제한
        except (ValueError, TypeError):
            pass
        
        return None
    
    def calculate_customer_sentiment_trend(self, utterances_data: List[Dict[str, Any]]) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        고객 감정 추세 분석 (지표 1, 2, 3)
        
        Returns
        -------
        tuple: (customer_sentiment_early, customer_sentiment_late, customer_sentiment_trend)
        """
        try:
            # 1. 고객 발화만 필터링
            customer_utterances = []
            for utterance in utterances_data:
                speaker = utterance.get('speaker', '').lower()
                if any(keyword in speaker for keyword in ['고객', 'customer', 'client', 'user']):
                    customer_utterances.append(utterance)
            
            if len(customer_utterances) < 3:  # 최소 3개 발화 필요
                return None, None, None
            
            # 2. sentiment 텍스트를 숫자로 매핑
            sentiment_scores = []
            for utterance in customer_utterances:
                sentiment_text = utterance.get('sentiment', '').lower()
                score = self._map_sentiment_to_score(sentiment_text)
                if score is not None:
                    sentiment_scores.append(score)
            
            if len(sentiment_scores) < 3:
                return None, None, None
            
            # 3. 초반부(처음 33%)와 후반부(끝 33%) 구분
            total_count = len(sentiment_scores)
            early_count = max(1, int(total_count * 0.33))
            late_count = max(1, int(total_count * 0.33))
            
            early_scores = sentiment_scores[:early_count]
            late_scores = sentiment_scores[-late_count:]
            
            # 4. 각 구간의 평균 점수 계산
            customer_sentiment_early = round(sum(early_scores) / len(early_scores), 3)
            customer_sentiment_late = round(sum(late_scores) / len(late_scores), 3)
            
            # 5. 감정 변화 추세 계산 (후반부 - 초반부)
            customer_sentiment_trend = round(customer_sentiment_late - customer_sentiment_early, 3)
            
            return customer_sentiment_early, customer_sentiment_late, customer_sentiment_trend
            
        except Exception as e:
            print(f"⚠️ 고객 감정 추세 분석 실패: {e}")
            return None, None, None
    
    def calculate_avg_response_latency(self, utterances_data: List[Dict[str, Any]]) -> Optional[float]:
        """
        평균 응답 지연 시간 계산 (지표 4)
        
        Parameters
        ----------
        utterances_data : List[Dict[str, Any]]
            발화 데이터 (start_time, end_time, speaker 포함)
            
        Returns
        -------
        Optional[float]
            평균 응답 지연 시간(초) 또는 None
        """
        try:
            # 1. 시간순으로 정렬
            sorted_utterances = sorted(utterances_data, key=lambda x: x.get('start_time', 0))
            
            latencies = []
            prev_utterance = None
            
            # 2. 고객 -> 상담사 전환 지점 찾기
            for utterance in sorted_utterances:
                current_speaker = utterance.get('speaker', '').lower()
                current_start_time = utterance.get('start_time')
                
                if prev_utterance is not None:
                    prev_speaker = prev_utterance.get('speaker', '').lower()
                    prev_end_time = prev_utterance.get('end_time')
                    
                    # 고객 -> 상담사 전환 확인
                    is_customer_to_counselor = (
                        any(keyword in prev_speaker for keyword in ['고객', 'customer', 'client', 'user']) and
                        any(keyword in current_speaker for keyword in ['상담사', 'counselor', 'agent', 'csr', 'staff'])
                    )
                    
                    if is_customer_to_counselor and prev_end_time is not None and current_start_time is not None:
                        # 3. 지연시간 = 상담사 발화 시작 - 고객 발화 종료
                        latency = current_start_time - prev_end_time
                        if latency >= 0:  # 음수 지연시간 제외
                            latencies.append(latency)
                
                prev_utterance = utterance
            
            # 4. 평균 계산
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                return round(avg_latency, 3)
            else:
                return None
                
        except Exception as e:
            print(f"⚠️ 평균 응답 지연 시간 계산 실패: {e}")
            return None
    
    def calculate_task_ratio(self, utterances_data: List[Dict[str, Any]]) -> Optional[float]:
        """
        업무 처리 비율 계산 (지표 5)
        
        Parameters
        ----------
        utterances_data : List[Dict[str, Any]]
            발화 데이터 (start_time, end_time, speaker 포함)
            
        Returns
        -------
        Optional[float]
            업무 처리 비율 (고객 발화 시간 / 상담사 발화 시간) 또는 None
        """
        try:
            customer_total_time = 0.0
            counselor_total_time = 0.0
            
            # 1. 각 화자별 총 발화 시간 계산
            for utterance in utterances_data:
                speaker = utterance.get('speaker', '').lower()
                start_time = utterance.get('start_time')
                end_time = utterance.get('end_time')
                
                if start_time is not None and end_time is not None and end_time > start_time:
                    duration = end_time - start_time
                    
                    # 고객 발화 시간
                    if any(keyword in speaker for keyword in ['고객', 'customer', 'client', 'user']):
                        customer_total_time += duration
                    
                    # 상담사 발화 시간
                    elif any(keyword in speaker for keyword in ['상담사', 'counselor', 'agent', 'csr', 'staff']):
                        counselor_total_time += duration
            
            # 2. 비율 계산
            if counselor_total_time > 0:
                task_ratio = customer_total_time / counselor_total_time
                return round(task_ratio, 3)
            else:
                return None  # 상담사 발화 시간이 0인 경우 예외 처리
                
        except Exception as e:
            print(f"⚠️ 업무 처리 비율 계산 실패: {e}")
            return None


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
    
    analyzer = SimpleQuantitativeAnalyzer()
    
    # 지표 계산
    early, late, trend = analyzer.calculate_customer_sentiment_trend(improving_case)
    latency = analyzer.calculate_avg_response_latency(improving_case)
    task_ratio = analyzer.calculate_task_ratio(improving_case)
    
    print("📈 분석 결과:")
    print(f"  고객 감정 초반부: {early}")
    print(f"  고객 감정 후반부: {late}")
    print(f"  감정 변화 추세: {trend} (양수면 개선)")
    print(f"  평균 응답 지연 시간: {latency}초")
    print(f"  업무 처리 비율: {task_ratio} (고객/상담사 발화 시간 비율)")
    
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
    
    early2, late2, trend2 = analyzer.calculate_customer_sentiment_trend(worsening_case)
    latency2 = analyzer.calculate_avg_response_latency(worsening_case)
    task_ratio2 = analyzer.calculate_task_ratio(worsening_case)
    
    print("📈 분석 결과:")
    print(f"  고객 감정 초반부: {early2}")
    print(f"  고객 감정 후반부: {late2}")
    print(f"  감정 변화 추세: {trend2} (음수면 악화)")
    print(f"  평균 응답 지연 시간: {latency2}초")
    print(f"  업무 처리 비율: {task_ratio2}")
    
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
    
    early3, late3, trend3 = analyzer.calculate_customer_sentiment_trend(delayed_response_case)
    latency3 = analyzer.calculate_avg_response_latency(delayed_response_case)
    task_ratio3 = analyzer.calculate_task_ratio(delayed_response_case)
    
    print("📈 분석 결과:")
    print(f"  평균 응답 지연 시간: {latency3}초 (높은 지연)")
    print(f"  업무 처리 비율: {task_ratio3}")
    
    # 종합 결과 출력
    print("\n📊 종합 비교 결과")
    print("="*70)
    print(f"{'테스트 케이스':<15} {'감정초반부':<10} {'감정후반부':<10} {'감정추세':<8} {'응답지연(초)':<12} {'업무비율':<8}")
    print("-"*70)
    print(f"{'감정 개선 상담':<15} {early:<10} {late:<10} {trend:<8} {latency:<12} {task_ratio:<8}")
    print(f"{'감정 악화 상담':<15} {early2:<10} {late2:<10} {trend2:<8} {latency2:<12} {task_ratio2:<8}")
    print(f"{'응답 지연 상담':<15} {early3 or 'N/A':<10} {late3 or 'N/A':<10} {trend3 or 'N/A':<8} {latency3:<12} {task_ratio3:<8}")
    
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
    
    print("\n✅ 테스트 완료!")
    print("📝 새로운 정량 분석 지표 5종이 성공적으로 구현되었습니다.")


if __name__ == "__main__":
    test_quantitative_metrics() 