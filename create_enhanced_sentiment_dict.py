#!/usr/bin/env python3
"""
향상된 감성 사전 생성 스크립트
"""

import json
import os

def create_enhanced_sentiment_dict():
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
    
    # 디렉토리 생성
    os.makedirs('data', exist_ok=True)
    
    # 파일 저장
    sentiment_file = "data/enhanced_sentiment_dict.json"
    with open(sentiment_file, 'w', encoding='utf-8') as f:
        json.dump(enhanced_sentiment_dict, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 향상된 감성 사전 생성 완료: {len(enhanced_sentiment_dict)}개 단어")
    print(f"📁 저장 위치: {sentiment_file}")

if __name__ == "__main__":
    create_enhanced_sentiment_dict() 