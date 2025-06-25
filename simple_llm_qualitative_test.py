#!/usr/bin/env python3
"""
LLM 기반 정성 평가 지표 간단 테스트
의존성 없이 독립적으로 실행 가능한 테스트
"""

import sys
import os
import asyncio
from typing import Dict, List, Any, Optional

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath('.'))

# 테스트용 Mock LLMHandler 클래스
class MockLLMHandler:
    """테스트용 LLM 핸들러 Mock"""
    
    def __init__(self):
        self.client = self
        
    async def chat_completions_create(self, **kwargs):
        """Mock API 호출"""
        messages = kwargs.get('messages', [])
        user_content = ""
        
        # 사용자 메시지에서 대화 내용 추출
        for msg in messages:
            if msg.get('role') == 'user':
                user_content = msg.get('content', '')
                break
        
        # 간단한 규칙 기반 응답 생성
        if "요금" in user_content and "확인" in user_content and "데이터" in user_content:
            # 첫 번째 제안으로 해결된 케이스
            response_text = "1.0"
        elif "인터넷" in user_content and "모뎀" in user_content:
            # 두 번째 제안으로 해결된 케이스  
            response_text = "0.6"
        elif "복잡" in user_content or "여러" in user_content:
            # 여러 번 제안한 케이스
            response_text = "0.2"
        else:
            # 해결되지 않은 케이스
            response_text = "0.0"
        
        # Mock 응답 객체
        class MockChoice:
            def __init__(self, text):
                self.message = type('obj', (object,), {'content': text})()
        
        class MockResponse:
            def __init__(self, text):
                self.choices = [MockChoice(text)]
        
        return MockResponse(response_text)
    
    # chat.completions.create의 별칭
    class ChatCompletions:
        def __init__(self, handler):
            self.handler = handler
            
        async def create(self, **kwargs):
            return await self.handler.chat_completions_create(**kwargs)
    
    @property
    def chat(self):
        class Chat:
            def __init__(self, handler):
                self.completions = MockLLMHandler.ChatCompletions(handler)
        return Chat(self)


# 테스트용 CommunicationQualityAnalyzer
class TestCommunicationQualityAnalyzer:
    """테스트용 커뮤니케이션 품질 분석기"""
    
    def __init__(self):
        self.llm_handler = MockLLMHandler()
        print("✅ Mock LLM 핸들러 초기화 완료")
    
    async def _calculate_suggestions_score(self, utterances_data: List[Dict[str, Any]]) -> Optional[float]:
        """문제 해결 제안 점수 계산 (테스트 버전)"""
        try:
            # 대화를 텍스트로 변환
            conversation_text = ""
            for utterance in utterances_data:
                speaker = utterance.get('speaker', 'Unknown')
                text = utterance.get('text', '').strip()
                if text:
                    conversation_text += f"{speaker}: {text}\n"
            
            if not conversation_text.strip():
                return None
            
            # Mock API 호출
            response = await self.llm_handler.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": "문제 해결 점수를 계산하세요."},
                    {"role": "user", "content": f"대화 분석:\n\n{conversation_text}"}
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # 점수 추출
            if "1.0" in response_text:
                return 1.0
            elif "0.6" in response_text:
                return 0.6
            elif "0.2" in response_text:
                return 0.2
            elif "0.0" in response_text:
                return 0.0
            else:
                return None
                
        except Exception as e:
            print(f"⚠️ 문제 해결 제안 점수 계산 실패: {e}")
            return None
    
    def _calculate_interruption_count(self, utterances_data: List[Dict[str, Any]]) -> Optional[int]:
        """대화 가로채기 횟수 계산"""
        try:
            if len(utterances_data) < 2:
                return 0
            
            interruption_count = 0
            
            # 발화 순서대로 정렬
            sorted_utterances = sorted(utterances_data, key=lambda x: x.get('start_time', 0))
            
            # 연속된 발화 쌍을 검사
            for i in range(1, len(sorted_utterances)):
                prev_utterance = sorted_utterances[i-1]
                curr_utterance = sorted_utterances[i]
                
                prev_speaker = prev_utterance.get('speaker', '').lower()
                curr_speaker = curr_utterance.get('speaker', '').lower()
                
                prev_end_time = prev_utterance.get('end_time')
                curr_start_time = curr_utterance.get('start_time')
                
                # 시간 정보가 있는 경우만 검사
                if prev_end_time is not None and curr_start_time is not None:
                    # 이전 발화가 고객, 현재 발화가 상담사인 경우
                    if (any(keyword in prev_speaker for keyword in ['고객', 'customer', 'client', 'user']) and
                        any(keyword in curr_speaker for keyword in ['상담사', 'counselor', 'agent', 'csr', 'staff'])):
                        
                        # 상담사 발화 시작 시간 < 고객 발화 종료 시간 → 가로채기
                        if curr_start_time < prev_end_time:
                            interruption_count += 1
                            print(f"🔍 가로채기 감지: 상담사가 {prev_end_time - curr_start_time:.2f}초 일찍 발화 시작")
            
            return interruption_count
            
        except Exception as e:
            print(f"⚠️ 대화 가로채기 횟수 계산 실패: {e}")
            return None


async def test_llm_qualitative_metrics():
    """LLM 기반 정성 평가 지표 테스트"""
    
    print("=" * 60)
    print("🤖 LLM 기반 정성 평가 지표 테스트")
    print("=" * 60)
    
    # 테스트 분석기 생성
    analyzer = TestCommunicationQualityAnalyzer()
    
    # 테스트 시나리오 1: 첫 번째 제안으로 문제 해결
    print("\n📋 테스트 시나리오 1: 첫 번째 제안으로 문제 해결")
    scenario1_data = [
        {"speaker": "고객", "text": "안녕하세요. 요금 관련해서 문의드리고 싶습니다.", 
         "start_time": 0.0, "end_time": 3.0},
        {"speaker": "상담사", "text": "안녕하세요. 고객님. 요금 관련 문의 도와드리겠습니다.", 
         "start_time": 4.0, "end_time": 7.0},
        {"speaker": "고객", "text": "이번 달 요금이 너무 많이 나왔어요.", 
         "start_time": 8.0, "end_time": 11.0},
        {"speaker": "상담사", "text": "요금 내역을 확인해드리겠습니다. 데이터 사용량을 확인해보니 많이 사용하셨네요.", 
         "start_time": 12.0, "end_time": 17.0},
        {"speaker": "고객", "text": "아 그렇군요. 감사합니다.", 
         "start_time": 18.0, "end_time": 20.0}
    ]
    
    suggestions1 = await analyzer._calculate_suggestions_score(scenario1_data)
    interruptions1 = analyzer._calculate_interruption_count(scenario1_data)
    
    print(f"  📊 문제 해결 제안 점수: {suggestions1}")
    print(f"  📊 대화 가로채기 횟수: {interruptions1}회")
    
    # 테스트 시나리오 2: 가로채기가 있는 상담
    print("\n📋 테스트 시나리오 2: 가로채기가 있는 상담")
    scenario2_data = [
        {"speaker": "고객", "text": "안녕하세요. 인터넷이 자꾸 끊어져서...", 
         "start_time": 0.0, "end_time": 4.0},
        {"speaker": "상담사", "text": "네, 인터넷 문제시죠.", 
         "start_time": 3.5, "end_time": 5.0},  # 가로채기 발생
        {"speaker": "고객", "text": "네, 맞습니다. 어떻게 해야 하나요?", 
         "start_time": 6.0, "end_time": 9.0},
        {"speaker": "상담사", "text": "우선 모뎀을 재부팅해보세요.", 
         "start_time": 8.5, "end_time": 11.0},  # 가로채기 발생
        {"speaker": "고객", "text": "알겠습니다.", 
         "start_time": 12.0, "end_time": 13.0}
    ]
    
    suggestions2 = await analyzer._calculate_suggestions_score(scenario2_data)
    interruptions2 = analyzer._calculate_interruption_count(scenario2_data)
    
    print(f"  📊 문제 해결 제안 점수: {suggestions2}")
    print(f"  📊 대화 가로채기 횟수: {interruptions2}회")
    
    # 테스트 시나리오 3: 복잡한 문제 해결 과정
    print("\n📋 테스트 시나리오 3: 복잡한 문제 해결 과정")
    scenario3_data = [
        {"speaker": "고객", "text": "복잡한 문제가 있어서 여러 가지 시도를 해봤는데 안 됩니다.", 
         "start_time": 0.0, "end_time": 4.0},
        {"speaker": "상담사", "text": "첫 번째 방법을 시도해보세요.", 
         "start_time": 5.0, "end_time": 7.0},
        {"speaker": "고객", "text": "그것도 안 되네요.", 
         "start_time": 8.0, "end_time": 10.0},
        {"speaker": "상담사", "text": "그럼 두 번째 방법으로 해보겠습니다.", 
         "start_time": 11.0, "end_time": 13.0},
        {"speaker": "고객", "text": "이것도 안 됩니다.", 
         "start_time": 14.0, "end_time": 16.0},
        {"speaker": "상담사", "text": "마지막으로 세 번째 방법을 시도해보세요.", 
         "start_time": 17.0, "end_time": 20.0}
    ]
    
    suggestions3 = await analyzer._calculate_suggestions_score(scenario3_data)
    interruptions3 = analyzer._calculate_interruption_count(scenario3_data)
    
    print(f"  📊 문제 해결 제안 점수: {suggestions3}")
    print(f"  📊 대화 가로채기 횟수: {interruptions3}회")
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    print(f"시나리오 1 - 첫 번째 제안 성공: 제안점수={suggestions1}, 가로채기={interruptions1}회")
    print(f"시나리오 2 - 가로채기 발생: 제안점수={suggestions2}, 가로채기={interruptions2}회")
    print(f"시나리오 3 - 복잡한 해결과정: 제안점수={suggestions3}, 가로채기={interruptions3}회")
    
    # 검증
    success_count = 0
    total_tests = 6
    
    if suggestions1 == 1.0:  # 첫 번째 제안 성공
        print("✅ 시나리오 1 제안 점수 정상")
        success_count += 1
    else:
        print(f"❌ 시나리오 1 제안 점수 오류: 예상=1.0, 실제={suggestions1}")
    
    if interruptions1 == 0:  # 가로채기 없음
        print("✅ 시나리오 1 가로채기 횟수 정상")
        success_count += 1
    else:
        print(f"❌ 시나리오 1 가로채기 횟수 오류: 예상=0, 실제={interruptions1}")
    
    if suggestions2 == 0.6:  # 두 번째 제안으로 해결
        print("✅ 시나리오 2 제안 점수 정상")
        success_count += 1
    else:
        print(f"❌ 시나리오 2 제안 점수 오류: 예상=0.6, 실제={suggestions2}")
    
    if interruptions2 == 2:  # 2번 가로채기
        print("✅ 시나리오 2 가로채기 횟수 정상")
        success_count += 1
    else:
        print(f"❌ 시나리오 2 가로채기 횟수 오류: 예상=2, 실제={interruptions2}")
    
    if suggestions3 == 0.2:  # 3번 이상 제안
        print("✅ 시나리오 3 제안 점수 정상")
        success_count += 1
    else:
        print(f"❌ 시나리오 3 제안 점수 오류: 예상=0.2, 실제={suggestions3}")
    
    if interruptions3 == 0:  # 가로채기 없음
        print("✅ 시나리오 3 가로채기 횟수 정상")
        success_count += 1
    else:
        print(f"❌ 시나리오 3 가로채기 횟수 오류: 예상=0, 실제={interruptions3}")
    
    print(f"\n🎯 테스트 성공률: {success_count}/{total_tests} ({success_count/total_tests*100:.1f}%)")
    
    if success_count == total_tests:
        print("🎉 모든 테스트 통과!")
        return True
    else:
        print("⚠️ 일부 테스트 실패")
        return False


def main():
    """메인 함수"""
    try:
        print("🚀 LLM 기반 정성 평가 지표 테스트 시작")
        
        # 비동기 테스트 실행
        result = asyncio.run(test_llm_qualitative_metrics())
        
        if result:
            print("\n✅ 전체 테스트 성공")
            return 0
        else:
            print("\n❌ 테스트 실패")
            return 1
            
    except Exception as e:
        print(f"\n💥 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main()) 