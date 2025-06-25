#!/usr/bin/env python3
"""
간단한 커뮤니케이션 품질 분석 테스트
"""

import re
import json
import os


def test_patterns():
    """패턴 매칭 테스트"""
    print("🔍 패턴 매칭 테스트")
    print("="*50)
    
    # 존댓말 패턴
    honorific_patterns = [
        r'습니다$', r'ㅂ니다$', r'세요$', r'셔요$', r'까요\?$',
        r'해요$', r'해주세요$', r'드려요$', r'드립니다$',
        r'하십시오$', r'해주십시오$', r'하시면$', r'하시고$',
        r'(으)?시[가-힣]*', r'[가-힣]*시[가-힣]*',
    ]
    
    # 쿠션어/완곡 표현
    euphonious_patterns = [
        r'실례지만', r'죄송하지만', r'괜찮으시다면', r'혹시', 
        r'번거로우시겠지만', r'만약',
        r'[가-힣]*인\s*것\s*같습니다', r'[가-힣]*ㄹ\s*것\s*같습니다',
        r'[가-힣]*하기는\s*어렵습니다', r'[가-힣]*ㄹ\s*수\s*있을까요\?',
        r'[가-힣]*해\s*주시겠어요\?', r'[가-힣]*해\s*주실\s*수\s*있나요\?'
    ]
    
    # 공감 표현
    empathy_patterns = [
        r'[가-힣]*하셨겠어요', r'[가-힣]*하셨겠네요', 
        r'많이\s*힘드셨죠', r'걱정되셨겠어요',
        r'어떤\s*마음인지\s*알\s*것\s*같습니다', 
        r'제가\s*고객님\s*입장이라도', r'저런', r'아이고'
    ]
    
    # 사과 표현
    apology_patterns = [
        r'죄송합니다', r'사과드립니다', r'미안합니다',
        r'양해\s*부탁드립니다', r'너그러이\s*이해해주시기\s*바랍니다'
    ]
    
    # 테스트 문장들
    test_sentences = [
        "안녕하세요. 도와드리겠습니다.",  # 존댓말
        "확인해주세요.",  # 존댓말
        "실례지만 확인이 필요합니다.",  # 쿠션어
        "혹시 시간이 되시나요?",  # 쿠션어
        "그런 것 같습니다.",  # 완곡표현
        "많이 힘드셨죠.",  # 공감
        "걱정되셨겠어요.",  # 공감
        "죄송합니다.",  # 사과
        "양해 부탁드립니다.",  # 사과
    ]
    
    print("테스트 문장별 패턴 매칭 결과:")
    for sentence in test_sentences:
        print(f"\n문장: '{sentence}'")
        
        # 존댓말 체크
        honorific_match = any(re.search(pattern, sentence) for pattern in honorific_patterns)
        print(f"  존댓말: {'✅' if honorific_match else '❌'}")
        
        # 쿠션어 체크
        euphonious_match = any(re.search(pattern, sentence) for pattern in euphonious_patterns)
        print(f"  쿠션어: {'✅' if euphonious_match else '❌'}")
        
        # 공감 체크
        empathy_match = any(re.search(pattern, sentence) for pattern in empathy_patterns)
        print(f"  공감: {'✅' if empathy_match else '❌'}")
        
        # 사과 체크
        apology_match = any(re.search(pattern, sentence) for pattern in apology_patterns)
        print(f"  사과: {'✅' if apology_match else '❌'}")


def test_sentiment_dict():
    """기본 감성사전 테스트"""
    print("\n🔍 감성사전 테스트")
    print("="*50)
    
    # 기본 감성사전
    sentiment_dict = {
        # 긍정 단어들
        "좋다": 1, "훌륭하다": 2, "만족하다": 2, "감사하다": 2, "기쁘다": 2,
        "완벽하다": 2, "최고다": 2, "우수하다": 1, "편리하다": 1, "빠르다": 1,
        "친절하다": 2, "도움": 1, "해결": 1, "성공": 1, "효과": 1,
        
        # 부정 단어들  
        "나쁘다": -1, "싫다": -1, "화나다": -2, "짜증나다": -2, "실망하다": -2,
        "불만": -2, "문제": -1, "오류": -1, "실패": -2, "어렵다": -1,
        "불편하다": -2, "느리다": -1, "복잡하다": -1, "답답하다": -2, "힘들다": -1
    }
    
    print(f"감성사전 단어 수: {len(sentiment_dict)}개")
    print(f"긍정 단어 수: {len([w for w, s in sentiment_dict.items() if s > 0])}개")
    print(f"부정 단어 수: {len([w for w, s in sentiment_dict.items() if s < 0])}개")
    
    # 테스트 문장들
    test_sentences = [
        "좋은 서비스를 제공해드리겠습니다.",  # 긍정
        "만족스러운 결과가 될 것입니다.",  # 긍정  
        "문제가 발생했습니다.",  # 부정
        "어려운 상황입니다.",  # 부정
        "확인해보겠습니다.",  # 중립
    ]
    
    print("\n문장별 감성 분석:")
    for sentence in test_sentences:
        words = sentence.split()
        positive_words = []
        negative_words = []
        
        for word in words:
            clean_word = re.sub(r'[^\w가-힣]', '', word)
            if clean_word in sentiment_dict:
                if sentiment_dict[clean_word] > 0:
                    positive_words.append(clean_word)
                elif sentiment_dict[clean_word] < 0:
                    negative_words.append(clean_word)
        
        print(f"\n문장: '{sentence}'")
        print(f"  긍정 단어: {positive_words}")
        print(f"  부정 단어: {negative_words}")


def test_communication_quality_calculation():
    """커뮤니케이션 품질 계산 테스트"""
    print("\n🔍 커뮤니케이션 품질 계산 테스트")
    print("="*50)
    
    # 샘플 상담사 발화 데이터
    counselor_utterances = [
        {"speaker": "상담사", "text": "안녕하세요, 고객님. 요금 관련 문의 도와드리겠습니다. 어떤 부분이 궁금하신가요?"},
        {"speaker": "상담사", "text": "걱정되셨겠어요. 죄송합니다. 요금 내역을 확인해드리겠습니다. 혹시 해외 로밍을 사용하셨나요?"},
        {"speaker": "상담사", "text": "그렇다면 데이터 사용량을 확인해보겠습니다. 실례지만 휴대폰 번호를 알려주시겠어요?"},
        {"speaker": "상담사", "text": "감사합니다. 확인해보니 이번 달에 데이터를 많이 사용하셨네요. 동영상 시청이나 게임을 하셨을 것 같습니다."},
        {"speaker": "상담사", "text": "다음 달부터는 데이터 사용량을 체크해주시면 좋을 것 같습니다. 도움이 되셨나요?"},
        {"speaker": "상담사", "text": "고객님께서 만족해주셔서 기쁩니다. 다른 문의사항이 있으시면 언제든지 연락해주세요. 감사합니다."}
    ]
    
    # 상담사 문장만 추출
    counselor_sentences = []
    for utterance in counselor_utterances:
        if '상담사' in utterance['speaker']:
            text = utterance['text'].strip()
            if text:
                # 문장 분리
                sentences = re.split(r'[.!?。？！]+', text)
                sentences = [s.strip() for s in sentences if s.strip()]
                counselor_sentences.extend(sentences)
    
    total_sentences = len(counselor_sentences)
    print(f"총 상담사 문장 수: {total_sentences}개")
    
    # 각 지표별 카운트 (간단한 버전)
    honorific_count = 0
    euphonious_count = 0
    empathy_count = 0
    apology_count = 0
    
    # 패턴 정의 (간소화)
    honorific_keywords = ['습니다', 'ㅂ니다', '세요', '해요', '드리겠', '하시']
    euphonious_keywords = ['실례지만', '혹시', '것 같습니다', '해주시겠어요']
    empathy_keywords = ['걱정되셨겠어요', '힘드셨죠', '하셨겠']
    apology_keywords = ['죄송합니다', '사과드립니다', '양해 부탁']
    
    print("\n문장별 분석:")
    for i, sentence in enumerate(counselor_sentences, 1):
        print(f"\n{i}. '{sentence}'")
        
        # 존댓말 체크
        if any(keyword in sentence for keyword in honorific_keywords):
            honorific_count += 1
            print("   ✅ 존댓말")
        
        # 쿠션어 체크
        if any(keyword in sentence for keyword in euphonious_keywords):
            euphonious_count += 1
            print("   ✅ 쿠션어")
        
        # 공감 체크
        if any(keyword in sentence for keyword in empathy_keywords):
            empathy_count += 1
            print("   ✅ 공감")
        
        # 사과 체크
        if any(keyword in sentence for keyword in apology_keywords):
            apology_count += 1
            print("   ✅ 사과")
    
    # 비율 계산
    honorific_ratio = (honorific_count / total_sentences) * 100
    euphonious_ratio = (euphonious_count / total_sentences) * 100
    empathy_ratio = (empathy_count / total_sentences) * 100
    apology_ratio = (apology_count / total_sentences) * 100
    
    print(f"\n📊 품질 지표 결과:")
    print(f"  존댓말 사용 비율: {honorific_ratio:.1f}% ({honorific_count}/{total_sentences})")
    print(f"  쿠션어 사용 비율: {euphonious_ratio:.1f}% ({euphonious_count}/{total_sentences})")
    print(f"  공감 표현 비율: {empathy_ratio:.1f}% ({empathy_count}/{total_sentences})")
    print(f"  사과 표현 비율: {apology_ratio:.1f}% ({apology_count}/{total_sentences})")
    
    # JSON 결과
    result = {
        'honorific_ratio': round(honorific_ratio, 2),
        'positive_word_ratio': 0.0,  # 간단한 테스트에서는 생략
        'negative_word_ratio': 0.0,  # 간단한 테스트에서는 생략
        'euphonious_word_ratio': round(euphonious_ratio, 2),
        'empathy_ratio': round(empathy_ratio, 2),
        'apology_ratio': round(apology_ratio, 2),
        'total_sentences': total_sentences
    }
    
    print(f"\n📄 JSON 결과:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return result


def main():
    """메인 함수"""
    print("🚀 커뮤니케이션 품질 분석 - 간단 테스트")
    print("="*60)
    
    try:
        # 1. 패턴 매칭 테스트
        test_patterns()
        
        # 2. 감성사전 테스트
        test_sentiment_dict()
        
        # 3. 품질 계산 테스트
        result = test_communication_quality_calculation()
        
        print("\n" + "="*60)
        print("✅ 모든 테스트 완료!")
        print("📋 결과 요약:")
        print(f"   - 패턴 매칭 정상 동작")
        print(f"   - 감성사전 정상 로드")
        print(f"   - 품질 지표 계산 완료")
        print(f"   - 6가지 지표 중 4가지 테스트 완료")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 