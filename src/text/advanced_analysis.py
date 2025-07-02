# Standard library imports
import os
import json
import threading
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Annotated, List, Dict, Any, Optional
from pathlib import Path
import re
from dataclasses import dataclass
from collections import defaultdict
import logging

# Related third-party imports
import torch
import openai
from openai import OpenAI

# Local imports
from src.text.model import LanguageModelManager
from src.text.korean_models import KoreanModels

logger = logging.getLogger(__name__)

@dataclass
class QualityScore:
    score: float
    details: Dict[str, any]
    examples: List[str]

class KoreanPunctuationAnalyzer:
    """한국어 문장 부호 사용 규칙 분석기"""
    
    def __init__(self):
        # 한국어 문장 부호 규칙 사전
        self.punctuation_rules = {
            'period': {
                'correct': ['요', '니다', '다', '어', '아', '네', '죠'],
                'incorrect': ['요.', '니다.', '다.', '어.', '아.', '네.', '죠.'],
                'score_weight': 0.3
            },
            'comma': {
                'correct_patterns': [
                    r'[가-힣]+[은는이가을를]?,',  # 명사 + 조사 + 쉼표
                    r'[가-힣]+[고며나]',  # 연결어미
                    r'[가-힣]+[는데]',  # 종결어미
                ],
                'incorrect_patterns': [
                    r'[가-힣]+[은는이가을를]?[고며나],',  # 조사 + 어미 + 쉼표
                    r'[가-힣]+[는데],',  # 종결어미 + 쉼표
                ],
                'score_weight': 0.2
            },
            'question': {
                'correct': ['까', '죠', '나', '니', '어', '아'],
                'incorrect': ['까?', '죠?', '나?', '니?', '어?', '아?'],
                'score_weight': 0.25
            },
            'exclamation': {
                'correct': ['네', '어', '아', '다'],
                'incorrect': ['네!', '어!', '아!', '다!'],
                'score_weight': 0.25
            }
        }
    
    def analyze_punctuation(self, text: str) -> QualityScore:
        """문장 부호 사용 규칙 분석"""
        total_score = 0
        total_weight = 0
        details = {}
        examples = []
        
        for rule_type, rules in self.punctuation_rules.items():
            score = 0
            rule_examples = []
            
            if rule_type == 'comma':
                score, rule_examples = self._analyze_comma_usage(text, rules)
            else:
                score, rule_examples = self._analyze_basic_punctuation(text, rules)
            
            details[rule_type] = {
                'score': score,
                'examples': rule_examples
            }
            examples.extend(rule_examples)
            total_score += score * rules['score_weight']
            total_weight += rules['score_weight']
        
        final_score = total_score / total_weight if total_weight > 0 else 0
        
        return QualityScore(
            score=final_score,
            details=details,
            examples=examples
        )
    
    def _analyze_basic_punctuation(self, text: str, rules: Dict) -> Tuple[float, List[str]]:
        """기본 문장 부호 분석"""
        correct_count = 0
        incorrect_count = 0
        examples = []
        
        for correct in rules['correct']:
            pattern = re.escape(correct)
            correct_count += len(re.findall(pattern, text))
        
        for incorrect in rules['incorrect']:
            pattern = re.escape(incorrect)
            matches = re.findall(pattern, text)
            incorrect_count += len(matches)
            if matches:
                examples.append(f"잘못된 사용: {incorrect}")
        
        total = correct_count + incorrect_count
        score = correct_count / total if total > 0 else 1.0
        
        return score, examples
    
    def _analyze_comma_usage(self, text: str, rules: Dict) -> Tuple[float, List[str]]:
        """쉼표 사용 규칙 분석"""
        correct_count = 0
        incorrect_count = 0
        examples = []
        
        for pattern in rules['correct_patterns']:
            matches = re.findall(pattern, text)
            correct_count += len(matches)
        
        for pattern in rules['incorrect_patterns']:
            matches = re.findall(pattern, text)
            incorrect_count += len(matches)
            if matches:
                examples.append(f"잘못된 쉼표 사용: {matches[:3]}")
        
        total = correct_count + incorrect_count
        score = correct_count / total if total > 0 else 1.0
        
        return score, examples

class KNUSentimentAnalyzer:
    """KNU 한국어 감성사전 기반 감성 분석기"""
    
    def __init__(self):
        # KNU 한국어 감성사전 데이터 (실제로는 파일에서 로드)
        self.positive_words = {
            # 긍정적 감정
            '좋다', '훌륭하다', '완벽하다', '최고다', '최상이다', '완벽하다',
            '만족하다', '기쁘다', '행복하다', '즐겁다', '신나다', '설레다',
            '감사하다', '고맙다', '사랑하다', '좋아하다', '즐기다', '즐겁다',
            '편하다', '편안하다', '안전하다', '안정적이다', '믿음직하다',
            '정확하다', '정밀하다', '완벽하다', '완성도가 높다', '품질이 좋다',
            '효과적이다', '효율적이다', '빠르다', '정확하다', '정시에',
            '친절하다', '따뜻하다', '관대하다', '너그럽다', '이해심이 많다',
            '전문적이다', '전문가다', '능력이 있다', '실력이 좋다', '경험이 많다',
            '해결하다', '도와주다', '지원하다', '협조하다', '협력하다',
            '개선하다', '향상시키다', '발전시키다', '성장하다', '진보하다',
            '혜택', '할인', '프로모션', '이벤트', '특가', '특별가', '무료',
            '보너스', '추가', '증정', '사은품', '선물', '경품', '당첨',
            '성공', '달성', '완료', '처리', '해결', '확인', '승인', '허가',
            '정상', '양호', '좋음', '우수', '최고', '최상', '완벽', '완전'
        }
        
        self.negative_words = {
            # 부정적 감정
            '나쁘다', '최악이다', '끔찍하다', '무섭다', '두렵다', '걱정되다',
            '불안하다', '긴장하다', '스트레스받다', '짜증나다', '화나다',
            '분노하다', '화가 나다', '열받다', '빡치다', '열받다', '화가 치밀다',
            '실망하다', '절망하다', '우울하다', '슬프다', '우울하다',
            '답답하다', '답답하다', '답답하다', '답답하다', '답답하다',
            '힘들다', '어렵다', '복잡하다', '어려움', '문제', '장애', '오류',
            '고장', '차단', '해지', '폐지', '중단', '지연', '지체', '늦다',
            '불편하다', '불편하다', '불편하다', '불편하다', '불편하다',
            '불만', '불평', '항의', '민원', '불만', '불평', '항의', '민원',
            '실패', '실패', '실패', '실패', '실패', '실패', '실패', '실패',
            '오류', '오류', '오류', '오류', '오류', '오류', '오류', '오류',
            '장애', '장애', '장애', '장애', '장애', '장애', '장애', '장애',
            '불량', '불량', '불량', '불량', '불량', '불량', '불량', '불량',
            '차단', '차단', '차단', '차단', '차단', '차단', '차단', '차단',
            '해지', '해지', '해지', '해지', '해지', '해지', '해지', '해지',
            '폐지', '폐지', '폐지', '폐지', '폐지', '폐지', '폐지', '폐지',
            '중단', '중단', '중단', '중단', '중단', '중단', '중단', '중단',
            '지연', '지연', '지연', '지연', '지연', '지연', '지연', '지연',
            '지체', '지체', '지체', '지체', '지체', '지체', '지체', '지체',
            '늦다', '늦다', '늦다', '늦다', '늦다', '늦다', '늦다', '늦다'
        }
        
        # 감정 강도 사전
        self.emotion_intensity = {
            # 긍정 강도
            '좋다': 1, '훌륭하다': 2, '완벽하다': 3, '최고다': 3, '최상이다': 3,
            '만족하다': 2, '기쁘다': 2, '행복하다': 3, '즐겁다': 2, '신나다': 2,
            '감사하다': 2, '고맙다': 2, '사랑하다': 3, '좋아하다': 1,
            '편하다': 1, '편안하다': 2, '안전하다': 2, '안정적이다': 2,
            '정확하다': 2, '정밀하다': 2, '효과적이다': 2, '효율적이다': 2,
            '친절하다': 2, '따뜻하다': 2, '전문적이다': 2, '능력이 있다': 2,
            '해결하다': 2, '도와주다': 2, '개선하다': 2, '향상시키다': 2,
            
            # 부정 강도
            '나쁘다': 1, '최악이다': 3, '끔찍하다': 3, '무섭다': 2, '두렵다': 2,
            '걱정되다': 1, '불안하다': 2, '스트레스받다': 2, '짜증나다': 2,
            '화나다': 2, '분노하다': 3, '열받다': 2, '실망하다': 2, '절망하다': 3,
            '우울하다': 2, '슬프다': 2, '답답하다': 1, '힘들다': 1, '어렵다': 1,
            '복잡하다': 1, '불편하다': 1, '불만': 1, '실패': 2, '오류': 1,
            '장애': 2, '불량': 2, '차단': 2, '해지': 2, '폐지': 2, '중단': 2,
            '지연': 1, '지체': 1, '늦다': 1
        }
    
    def analyze_sentiment(self, text: str) -> QualityScore:
        """KNU 감성사전 기반 감성 분석"""
        positive_count = 0
        negative_count = 0
        positive_words_found = []
        negative_words_found = []
        positive_intensity = 0
        negative_intensity = 0
        
        # 텍스트를 단어로 분리
        words = re.findall(r'[가-힣]+', text)
        total_words = len(words)
        
        if total_words == 0:
            return QualityScore(
                score=0.5,
                details={'positive_ratio': 0, 'negative_ratio': 0, 'sentiment_score': 0.5},
                examples=[]
            )
        
        # 긍정/부정 단어 카운트
        for word in words:
            if word in self.positive_words:
                positive_count += 1
                positive_words_found.append(word)
                positive_intensity += self.emotion_intensity.get(word, 1)
            
            if word in self.negative_words:
                negative_count += 1
                negative_words_found.append(word)
                negative_intensity += self.emotion_intensity.get(word, 1)
        
        # 비율 계산
        positive_ratio = positive_count / total_words
        negative_ratio = negative_count / total_words
        
        # 감성 점수 계산 (긍정 비율 - 부정 비율, 0~1 범위로 정규화)
        sentiment_score = (positive_ratio - negative_ratio + 1) / 2
        
        # 강도 가중치 적용
        intensity_score = 0.5
        if positive_intensity > 0 or negative_intensity > 0:
            intensity_score = positive_intensity / (positive_intensity + negative_intensity)
        
        # 최종 점수 (감성 점수와 강도 점수의 가중 평균)
        final_score = sentiment_score * 0.7 + intensity_score * 0.3
        
        details = {
            'positive_count': positive_count,
            'negative_count': negative_count,
            'positive_ratio': positive_ratio,
            'negative_ratio': negative_ratio,
            'sentiment_score': sentiment_score,
            'positive_intensity': positive_intensity,
            'negative_intensity': negative_intensity,
            'intensity_score': intensity_score,
            'total_words': total_words
        }
        
        examples = []
        if positive_words_found:
            examples.append(f"긍정 단어: {', '.join(set(positive_words_found[:5]))}")
        if negative_words_found:
            examples.append(f"부정 단어: {', '.join(set(negative_words_found[:5]))}")
        
        return QualityScore(
            score=final_score,
            details=details,
            examples=examples
        )

class CommunicationQualityAnalyzer:
    """통신사 상담사 수준의 의사소통 품질 분석기"""
    
    def __init__(self):
        # KNU 감성 분석기 초기화
        self.knu_analyzer = KNUSentimentAnalyzer()
        
        # 존댓말 사용 패턴
        self.polite_patterns = {
            'formal_endings': [
                r'[가-힣]+습니다', r'[가-힣]+니다', r'[가-힣]+요',
                r'[가-힣]+겠습니다', r'[가-힣]+시겠습니다'
            ],
            'honorific_verbs': [
                '드리다', '해드리다', '말씀드리다', '안내드리다',
                '도와드리다', '확인해드리다', '연결해드리다'
            ],
            'honorific_nouns': [
                '고객님', '손님', '선생님', '고객분', '고객'
            ],
            'polite_expressions': [
                '죄송합니다', '감사합니다', '부탁드립니다', '알겠습니다',
                '이해했습니다', '확인해보겠습니다', '도움을 드리겠습니다'
            ]
        }
        
        # 부정적 표현 패턴 (KNU 사전과 연동)
        self.negative_patterns = {
            'direct_negative': [
                '안 됩니다', '불가능합니다', '할 수 없습니다', '안 되겠습니다',
                '못합니다', '어렵습니다', '불가합니다'
            ],
            'negative_words': [
                '문제', '오류', '장애', '불량', '고장', '차단', '해지',
                '폐지', '중단', '지연', '오류', '실패'
            ],
            'negative_emotions': [
                '짜증', '화남', '불만', '답답', '힘듦', '어려움', '복잡'
            ]
        }
        
        # 공감 표현 패턴
        self.empathy_patterns = {
            'understanding': [
                '이해합니다', '알겠습니다', '말씀하신 대로', '그렇군요',
                '충분히 이해됩니다', '고민이 되시겠네요'
            ],
            'emotional_support': [
                '힘드셨겠어요', '답답하셨겠어요', '불편하셨겠어요',
                '걱정되셨겠어요', '괴로우셨겠어요'
            ],
            'positive_reinforcement': [
                '잘 하셨습니다', '정말 좋습니다', '훌륭합니다',
                '맞습니다', '정확합니다'
            ]
        }
        
        # 전문성 표현 패턴
        self.expertise_patterns = {
            'technical_terms': [
                '데이터', '통화량', '요금제', '할인', '혜택', '프로모션',
                '정책', '규정', '절차', '방법', '해결책'
            ],
            'precise_explanations': [
                '구체적으로', '정확히', '상세히', '자세히', '명확히',
                '단계별로', '순서대로', '방법은'
            ],
            'solution_oriented': [
                '해결해드리겠습니다', '도움을 드리겠습니다', '방법을 알려드리겠습니다',
                '확인해보겠습니다', '처리해드리겠습니다'
            ]
        }
        
        # 구체적 정보 제공 패턴
        self.specific_info_patterns = {
            'numbers': [
                r'\d+원', r'\d+%', r'\d+일', r'\d+시간', r'\d+분',
                r'\d+개', r'\d+회', r'\d+번'
            ],
            'time_specific': [
                '오늘', '내일', '이번 주', '다음 주', '이번 달', '다음 달',
                '3일 후', '1주일 후', '1개월 후'
            ],
            'process_steps': [
                '첫째', '둘째', '셋째', '1단계', '2단계', '3단계',
                '먼저', '그 다음', '마지막으로'
            ]
        }
        
        # 문장 부호 분석기 초기화
        self.punctuation_analyzer = KoreanPunctuationAnalyzer()
    
    def analyze_communication_quality(self, text: str) -> Dict[str, QualityScore]:
        """통신사 상담사 수준의 의사소통 품질 종합 분석"""
        results = {}
        
        # 1. 존댓말 사용 분석
        results['politeness'] = self._analyze_politeness(text)
        
        # 2. 부정적 표현 분석 (KNU 감성 분석과 연동)
        results['negative_expression'] = self._analyze_negative_expressions(text)
        
        # 3. 공감 표현 분석
        results['empathy'] = self._analyze_empathy(text)
        
        # 4. 전문성 분석
        results['expertise'] = self._analyze_expertise(text)
        
        # 5. 구체적 정보 제공 분석
        results['specific_info'] = self._analyze_specific_info(text)
        
        # 6. 문장 부호 사용 분석
        results['punctuation'] = self.punctuation_analyzer.analyze_punctuation(text)
        
        # 7. KNU 감성 분석
        results['sentiment'] = self.knu_analyzer.analyze_sentiment(text)
        
        return results
    
    def _analyze_politeness(self, text: str) -> QualityScore:
        """존댓말 사용 분석"""
        total_score = 0
        total_weight = 0
        details = {}
        examples = []
        
        # 공식 종결어미 사용
        formal_count = 0
        for pattern in self.polite_patterns['formal_endings']:
            formal_count += len(re.findall(pattern, text))
        
        # 경어 동사 사용
        honorific_verb_count = 0
        for verb in self.polite_patterns['honorific_verbs']:
            honorific_verb_count += text.count(verb)
        
        # 경어 명사 사용
        honorific_noun_count = 0
        for noun in self.polite_patterns['honorific_nouns']:
            honorific_noun_count += text.count(noun)
        
        # 공손한 표현 사용
        polite_expression_count = 0
        for expression in self.polite_patterns['polite_expressions']:
            polite_expression_count += text.count(expression)
        
        # 전체 문장 수 추정 (마침표 기준)
        total_sentences = len(re.findall(r'[.!?]', text)) + 1
        
        # 점수 계산
        formal_score = min(formal_count / total_sentences * 2, 1.0) if total_sentences > 0 else 0
        honorific_score = min((honorific_verb_count + honorific_noun_count) / total_sentences, 1.0) if total_sentences > 0 else 0
        polite_score = min(polite_expression_count / total_sentences, 1.0) if total_sentences > 0 else 0
        
        # 가중 평균
        final_score = (formal_score * 0.4 + honorific_score * 0.4 + polite_score * 0.2)
        
        details = {
            'formal_endings': formal_score,
            'honorific_usage': honorific_score,
            'polite_expressions': polite_score
        }
        
        if formal_count > 0:
            examples.append(f"공식 종결어미 사용: {formal_count}회")
        if honorific_verb_count > 0:
            examples.append(f"경어 동사 사용: {honorific_verb_count}회")
        if polite_expression_count > 0:
            examples.append(f"공손한 표현 사용: {polite_expression_count}회")
        
        return QualityScore(score=final_score, details=details, examples=examples)
    
    def _analyze_negative_expressions(self, text: str) -> QualityScore:
        """부정적 표현 분석 (KNU 감성 분석과 연동)"""
        # KNU 감성 분석 결과 활용
        knu_result = self.knu_analyzer.analyze_sentiment(text)
        knu_negative_ratio = knu_result.details.get('negative_ratio', 0)
        knu_negative_intensity = knu_result.details.get('negative_intensity', 0)
        
        # 기존 패턴 기반 분석
        pattern_negative_count = 0
        examples = []
        
        # 직접적 부정 표현
        for expression in self.negative_patterns['direct_negative']:
            count = text.count(expression)
            pattern_negative_count += count
            if count > 0:
                examples.append(f"직접적 부정: {expression}")
        
        # 부정적 단어
        for word in self.negative_patterns['negative_words']:
            count = text.count(word)
            pattern_negative_count += count * 0.5  # 가중치 적용
            if count > 0:
                examples.append(f"부정적 단어: {word}")
        
        # 부정적 감정 표현
        for emotion in self.negative_patterns['negative_emotions']:
            count = text.count(emotion)
            pattern_negative_count += count * 0.3
            if count > 0:
                examples.append(f"부정적 감정: {emotion}")
        
        # KNU 분석 결과와 패턴 분석 결과 결합
        total_words = len(text.split())
        pattern_negative_ratio = pattern_negative_count / total_words if total_words > 0 else 0
        
        # 가중 평균으로 최종 부정 비율 계산
        final_negative_ratio = (knu_negative_ratio * 0.6 + pattern_negative_ratio * 0.4)
        
        # 점수 계산 (부정적 표현이 적을수록 높은 점수)
        score = max(0, 1 - final_negative_ratio * 8)  # 부정적 표현 비율에 따른 감점
        
        # KNU 감정 강도 반영
        if knu_negative_intensity > 0:
            intensity_penalty = min(0.2, knu_negative_intensity * 0.05)
            score = max(0, score - intensity_penalty)
        
        details = {
            'knu_negative_ratio': knu_negative_ratio,
            'pattern_negative_ratio': pattern_negative_ratio,
            'final_negative_ratio': final_negative_ratio,
            'knu_negative_intensity': knu_negative_intensity,
            'pattern_negative_count': pattern_negative_count,
            'total_words': total_words,
            'intensity_penalty': min(0.2, knu_negative_intensity * 0.05) if knu_negative_intensity > 0 else 0
        }
        
        # KNU에서 발견된 부정 단어도 예시에 추가
        knu_examples = knu_result.examples
        examples.extend([ex for ex in knu_examples if '부정 단어' in ex])
        
        return QualityScore(score=score, details=details, examples=examples)
    
    def _analyze_empathy(self, text: str) -> QualityScore:
        """공감 표현 분석"""
        empathy_count = 0
        examples = []
        
        # 이해 표현
        for expression in self.empathy_patterns['understanding']:
            count = text.count(expression)
            empathy_count += count
            if count > 0:
                examples.append(f"이해 표현: {expression}")
        
        # 감정적 지지
        for expression in self.empathy_patterns['emotional_support']:
            count = text.count(expression)
            empathy_count += count * 1.5  # 더 높은 가중치
            if count > 0:
                examples.append(f"감정적 지지: {expression}")
        
        # 긍정적 강화
        for expression in self.empathy_patterns['positive_reinforcement']:
            count = text.count(expression)
            empathy_count += count
            if count > 0:
                examples.append(f"긍정적 강화: {expression}")
        
        # 점수 계산
        total_sentences = len(re.findall(r'[.!?]', text)) + 1
        empathy_ratio = empathy_count / total_sentences if total_sentences > 0 else 0
        score = min(empathy_ratio * 2, 1.0)  # 적절한 공감 표현 비율
        
        details = {
            'empathy_count': empathy_count,
            'empathy_ratio': empathy_ratio,
            'total_sentences': total_sentences
        }
        
        return QualityScore(score=score, details=details, examples=examples)
    
    def _analyze_expertise(self, text: str) -> QualityScore:
        """전문성 분석"""
        expertise_count = 0
        examples = []
        
        # 전문 용어 사용
        for term in self.expertise_patterns['technical_terms']:
            count = text.count(term)
            expertise_count += count
            if count > 0:
                examples.append(f"전문 용어: {term}")
        
        # 정확한 설명
        for expression in self.expertise_patterns['precise_explanations']:
            count = text.count(expression)
            expertise_count += count * 1.2
            if count > 0:
                examples.append(f"정확한 설명: {expression}")
        
        # 해결책 제시
        for expression in self.expertise_patterns['solution_oriented']:
            count = text.count(expression)
            expertise_count += count * 1.5
            if count > 0:
                examples.append(f"해결책 제시: {expression}")
        
        # 점수 계산
        total_words = len(text.split())
        expertise_ratio = expertise_count / total_words if total_words > 0 else 0
        score = min(expertise_ratio * 5, 1.0)  # 전문성 표현 비율
        
        details = {
            'expertise_count': expertise_count,
            'expertise_ratio': expertise_ratio,
            'total_words': total_words
        }
        
        return QualityScore(score=score, details=details, examples=examples)
    
    def _analyze_specific_info(self, text: str) -> QualityScore:
        """구체적 정보 제공 분석"""
        specific_count = 0
        examples = []
        
        # 숫자 정보
        for pattern in self.specific_info_patterns['numbers']:
            matches = re.findall(pattern, text)
            specific_count += len(matches)
            if matches:
                examples.append(f"숫자 정보: {matches[:3]}")
        
        # 시간 정보
        for time_expr in self.specific_info_patterns['time_specific']:
            count = text.count(time_expr)
            specific_count += count
            if count > 0:
                examples.append(f"시간 정보: {time_expr}")
        
        # 단계별 설명
        for step_expr in self.specific_info_patterns['process_steps']:
            count = text.count(step_expr)
            specific_count += count * 1.5
            if count > 0:
                examples.append(f"단계별 설명: {step_expr}")
        
        # 점수 계산
        total_sentences = len(re.findall(r'[.!?]', text)) + 1
        specific_ratio = specific_count / total_sentences if total_sentences > 0 else 0
        score = min(specific_ratio * 1.5, 1.0)
        
        details = {
            'specific_count': specific_count,
            'specific_ratio': specific_ratio,
            'total_sentences': total_sentences
        }
        
        return QualityScore(score=score, details=details, examples=examples)

def analyze_communication_quality_advanced(text: str) -> Dict[str, any]:
    """고급 의사소통 품질 분석 (통신사 상담사 수준)"""
    analyzer = CommunicationQualityAnalyzer()
    results = analyzer.analyze_communication_quality(text)
    
    # 종합 점수 계산 (KNU 감성 분석 포함)
    weights = {
        'politeness': 0.20,
        'negative_expression': 0.15,
        'empathy': 0.15,
        'expertise': 0.15,
        'specific_info': 0.10,
        'punctuation': 0.05,
        'sentiment': 0.20  # KNU 감성 분석 추가
    }
    
    total_score = 0
    for category, weight in weights.items():
        if category in results:
            total_score += results[category].score * weight
    
    # 결과 정리
    analysis_result = {
        'overall_score': total_score,
        'category_scores': {},
        'detailed_analysis': {},
        'recommendations': []
    }
    
    for category, result in results.items():
        analysis_result['category_scores'][category] = result.score
        analysis_result['detailed_analysis'][category] = {
            'score': result.score,
            'details': result.details,
            'examples': result.examples
        }
    
    # 개선 권장사항 생성 (KNU 감성 분석 결과 반영)
    recommendations = []
    
    if results['politeness'].score < 0.7:
        recommendations.append("존댓말 사용을 더 적극적으로 하세요. '-습니다', '-니다', '-요' 종결어미를 활용하세요.")
    
    if results['negative_expression'].score < 0.8:
        recommendations.append("부정적 표현을 줄이고 긍정적 대안을 제시하세요.")
    
    if results['empathy'].score < 0.6:
        recommendations.append("고객의 감정에 공감하는 표현을 더 사용하세요.")
    
    if results['expertise'].score < 0.6:
        recommendations.append("전문 용어와 정확한 설명을 더 활용하세요.")
    
    if results['specific_info'].score < 0.5:
        recommendations.append("구체적인 숫자, 시간, 단계별 정보를 제공하세요.")
    
    if results['punctuation'].score < 0.8:
        recommendations.append("한국어 문장 부호 규칙을 준수하세요.")
    
    # KNU 감성 분석 기반 권장사항
    sentiment_result = results.get('sentiment', QualityScore(0.5, {}, []))
    sentiment_details = sentiment_result.details
    
    if sentiment_details.get('negative_ratio', 0) > 0.1:
        recommendations.append("부정적 단어 사용을 줄이고 긍정적 표현을 늘리세요.")
    
    if sentiment_details.get('positive_ratio', 0) < 0.05:
        recommendations.append("긍정적 단어와 표현을 더 적극적으로 사용하세요.")
    
    if sentiment_details.get('negative_intensity', 0) > 5:
        recommendations.append("강한 부정적 감정 표현을 줄이고 중립적 표현을 사용하세요.")
    
    analysis_result['recommendations'] = recommendations
    
    return analysis_result

class AdvancedAnalysisManager:
    """
    고성능 분석 관리 클래스
    캐싱, LLM 호출 병렬화, 품질지표 세분화 지원
    """
    
    def __init__(self, 
                 config_path: str = "config/config.yaml",
                 cache_dir: str = "/app/.cache/analysis",
                 max_workers: int = 4,
                 enable_cache: bool = True,
                 enable_parallel: bool = True):
        """
        AdvancedAnalysisManager 초기화
        
        Parameters
        ----------
        config_path : str
            설정 파일 경로
        cache_dir : str
            캐시 디렉토리
        max_workers : int
            병렬 처리 워커 수
        enable_cache : bool
            캐시 활성화 여부
        enable_parallel : bool
            병렬 처리 활성화 여부
        """
        self.config_path = config_path
        self.cache_dir = Path(cache_dir)
        self.max_workers = max_workers
        self.enable_cache = enable_cache
        self.enable_parallel = enable_parallel
        
        # 캐시 디렉토리 생성
        if self.enable_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 캐시 메타데이터 관리
        self.cache_metadata_file = self.cache_dir / "metadata.json"
        self.cache_metadata = self._load_cache_metadata()
        self.cache_lock = threading.Lock()
        
        # 모델 매니저 초기화
        self.llm_manager = LanguageModelManager(config_path)
        self.korean_models = KoreanModels()
        
        # 병렬 처리 executor
        if self.enable_parallel:
            self.executor = ThreadPoolExecutor(max_workers=max_workers)
        else:
            self.executor = None
        
        # 성능 모니터링
        self.performance_stats = {
            "total_analyses": 0,
            "cache_hits": 0,
            "parallel_analyses": 0,
            "avg_processing_time": 0.0
        }
        
        print(f"✅ AdvancedAnalysisManager 초기화 완료")
    
    def _load_cache_metadata(self) -> Dict[str, Any]:
        """캐시 메타데이터 로드"""
        try:
            if self.cache_metadata_file.exists():
                with open(self.cache_metadata_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ 캐시 메타데이터 로드 실패: {e}")
        return {}
    
    def _save_cache_metadata(self):
        """캐시 메타데이터 저장"""
        try:
            with open(self.cache_metadata_file, 'w') as f:
                json.dump(self.cache_metadata, f, indent=2)
        except Exception as e:
            print(f"⚠️ 캐시 메타데이터 저장 실패: {e}")
    
    def _get_cache_key(self, analysis_type: str, content: str, params: Dict[str, Any] = None) -> str:
        """캐시 키 생성"""
        import hashlib
        
        # 분석 타입과 내용으로 키 생성
        key_content = f"{analysis_type}_{content}"
        if params:
            key_content += f"_{json.dumps(params, sort_keys=True)}"
        
        content_hash = hashlib.md5(key_content.encode('utf-8')).hexdigest()
        return f"{content_hash}_{analysis_type}"
    
    def _is_cached(self, analysis_type: str, content: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """캐시된 결과 확인"""
        if not self.enable_cache:
            return None
        
        cache_key = self._get_cache_key(analysis_type, content, params)
        
        with self.cache_lock:
            if cache_key in self.cache_metadata:
                cache_info = self.cache_metadata[cache_key]
                cache_path = self.cache_dir / cache_info["filename"]
                
                if cache_path.exists() and os.path.getsize(cache_path) > 0:
                    return cache_info
        
        return None
    
    def _save_to_cache(self, analysis_type: str, content: str, result: Dict[str, Any], params: Dict[str, Any] = None):
        """결과를 캐시에 저장"""
        if not self.enable_cache:
            return
        
        try:
            cache_key = self._get_cache_key(analysis_type, content, params)
            cache_filename = f"{cache_key}.json"
            cache_path = self.cache_dir / cache_filename
            
            # 결과 저장
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            # 메타데이터 업데이트
            with self.cache_lock:
                self.cache_metadata[cache_key] = {
                    "filename": cache_filename,
                    "analysis_type": analysis_type,
                    "created_at": time.time(),
                    "file_size": os.path.getsize(cache_path)
                }
                self._save_cache_metadata()
            
            print(f"💾 분석 캐시 저장: {cache_filename}")
            
        except Exception as e:
            print(f"⚠️ 분석 캐시 저장 실패: {e}")
    
    def _load_from_cache(self, cache_info: Dict[str, Any]) -> Dict[str, Any]:
        """캐시에서 결과 로드"""
        try:
            cache_path = self.cache_dir / cache_info["filename"]
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 캐시 로드 실패: {e}")
            return {}
    
    async def _analyze_sentiment_parallel(self, text: str) -> Dict[str, Any]:
        """병렬 감정 분석"""
        try:
            result = await self.korean_models.analyze_sentiment_with_api(text)
            return {
                "sentiment": result,
                "confidence": 0.8,
                "method": "api"
            }
        except Exception as e:
            print(f"⚠️ 감정 분석 실패: {e}")
            return {
                "sentiment": "중립",
                "confidence": 0.5,
                "method": "fallback"
            }
    
    async def _analyze_profanity_parallel(self, text: str) -> Dict[str, Any]:
        """병렬 비속어 감지"""
        try:
            result = await self.korean_models.detect_profanity_with_api(text)
            return {
                "has_profanity": result,
                "confidence": 0.8,
                "method": "api"
            }
        except Exception as e:
            print(f"⚠️ 비속어 감지 실패: {e}")
            return {
                "has_profanity": False,
                "confidence": 0.5,
                "method": "fallback"
            }
    
    async def _analyze_speaker_classification_parallel(self, text: str) -> Dict[str, Any]:
        """병렬 화자 분류"""
        try:
            result = await self.korean_models.classify_speaker_with_api(text)
            return {
                "speaker_type": result,
                "confidence": 0.8,
                "method": "api"
            }
        except Exception as e:
            print(f"⚠️ 화자 분류 실패: {e}")
            return {
                "speaker_type": "고객",
                "confidence": 0.5,
                "method": "fallback"
            }
    
    async def _analyze_communication_quality_parallel(self, text: str) -> Dict[str, Any]:
        """병렬 의사소통 품질 분석 (통신사 상담사 수준)"""
        try:
            # 캐시 확인
            cached_info = self._is_cached("communication_quality", text)
            if cached_info:
                return self._load_from_cache(cached_info)
            
            # 새로운 고급 분석 시스템 사용
            analysis_result = analyze_communication_quality_advanced(text)
            analysis_result["method"] = "parallel_advanced"
            
            # 캐시에 저장
            self._save_to_cache("communication_quality", text, analysis_result)
            
            return analysis_result
            
        except Exception as e:
            print(f"⚠️ 병렬 의사소통 품질 분석 실패: {e}")
            return {
                "error": str(e),
                "method": "fallback"
            }
    
    def _analyze_clarity(self, text: str) -> float:
        """명확성 분석 (통신사 상담사 수준)"""
        analyzer = CommunicationQualityAnalyzer()
        results = analyzer.analyze_communication_quality(text)
        
        # 명확성은 전문성과 구체적 정보 제공의 조합
        expertise_score = results.get('expertise', QualityScore(0, {}, [])).score
        specific_info_score = results.get('specific_info', QualityScore(0, {}, [])).score
        
        # 가중 평균으로 명확성 점수 계산
        clarity_score = (expertise_score * 0.6 + specific_info_score * 0.4)
        
        return clarity_score
    
    def _analyze_politeness(self, text: str) -> float:
        """예의성 분석 (통신사 상담사 수준)"""
        analyzer = CommunicationQualityAnalyzer()
        results = analyzer.analyze_communication_quality(text)
        
        # 예의성은 존댓말 사용과 부정적 표현 회피의 조합
        politeness_score = results.get('politeness', QualityScore(0, {}, [])).score
        negative_score = results.get('negative_expression', QualityScore(0, {}, [])).score
        
        # 가중 평균으로 예의성 점수 계산
        final_score = (politeness_score * 0.7 + negative_score * 0.3)
        
        return final_score
    
    def _analyze_empathy(self, text: str) -> float:
        """공감성 분석 (통신사 상담사 수준)"""
        analyzer = CommunicationQualityAnalyzer()
        results = analyzer.analyze_communication_quality(text)
        
        # 공감성 점수 반환
        empathy_score = results.get('empathy', QualityScore(0, {}, [])).score
        
        return empathy_score
    
    def _analyze_professionalism(self, text: str) -> float:
        """전문성 분석 (통신사 상담사 수준)"""
        analyzer = CommunicationQualityAnalyzer()
        results = analyzer.analyze_communication_quality(text)
        
        # 전문성 점수 반환
        expertise_score = results.get('expertise', QualityScore(0, {}, [])).score
        
        return expertise_score
    
    def _analyze_response_quality(self, text: str) -> float:
        """응답 품질 분석 (통신사 상담사 수준)"""
        analyzer = CommunicationQualityAnalyzer()
        results = analyzer.analyze_communication_quality(text)
        
        # 응답 품질은 모든 지표의 종합
        weights = {
            'politeness': 0.25,
            'negative_expression': 0.15,
            'empathy': 0.20,
            'expertise': 0.25,
            'specific_info': 0.10,
            'punctuation': 0.05
        }
        
        total_score = 0
        for category, weight in weights.items():
            if category in results:
                total_score += results[category].score * weight
        
        return total_score
    
    async def analyze_text_comprehensive(self, text: str) -> Dict[str, Any]:
        """
        종합 텍스트 분석
        
        Parameters
        ----------
        text : str
            분석할 텍스트
            
        Returns
        -------
        Dict[str, Any]
            종합 분석 결과
        """
        try:
            print(f"🔍 종합 텍스트 분석 시작: {len(text)}자")
            start_time = time.time()
            
            # 캐시 확인
            cached_info = self._is_cached("comprehensive", text)
            if cached_info:
                result = self._load_from_cache(cached_info)
                self.performance_stats["cache_hits"] += 1
                print(f"💾 캐시에서 로드: 종합 분석")
                return result
            
            # 병렬 분석 태스크 생성
            analysis_tasks = [
                self._analyze_sentiment_parallel(text),
                self._analyze_profanity_parallel(text),
                self._analyze_speaker_classification_parallel(text),
                self._analyze_communication_quality_parallel(text)
            ]
            
            # 병렬 실행
            if self.enable_parallel:
                print("🚀 병렬 분석 시작")
                results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
                self.performance_stats["parallel_analyses"] += 1
            else:
                print("🐌 순차 분석 시작")
                results = []
                for task in analysis_tasks:
                    try:
                        result = await task
                        results.append(result)
                    except Exception as e:
                        print(f"⚠️ 분석 실패: {e}")
                        results.append({"error": str(e)})
            
            # 결과 정리
            analysis_result = {
                "sentiment_analysis": results[0] if len(results) > 0 else {},
                "profanity_detection": results[1] if len(results) > 1 else {},
                "speaker_classification": results[2] if len(results) > 2 else {},
                "communication_quality": results[3] if len(results) > 3 else {},
                "analysis_metadata": {
                    "text_length": len(text),
                    "processing_time": time.time() - start_time,
                    "analysis_method": "parallel" if self.enable_parallel else "sequential"
                }
            }
            
            # 캐시에 저장
            self._save_to_cache("comprehensive", text, analysis_result)
            
            # 성능 통계 업데이트
            processing_time = time.time() - start_time
            self.performance_stats["total_analyses"] += 1
            self.performance_stats["avg_processing_time"] = (
                (self.performance_stats["avg_processing_time"] * (self.performance_stats["total_analyses"] - 1) + processing_time) 
                / self.performance_stats["total_analyses"]
            )
            
            print(f"✅ 종합 분석 완료: {processing_time:.2f}초")
            return analysis_result
            
        except Exception as e:
            print(f"⚠️ 종합 분석 실패: {e}")
            return {
                "error": str(e),
                "analysis_metadata": {
                    "text_length": len(text),
                    "processing_time": 0,
                    "analysis_method": "error"
                }
            }
    
    async def analyze_batch_parallel(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        배치 병렬 분석
        
        Parameters
        ----------
        texts : List[str]
            분석할 텍스트 리스트
            
        Returns
        -------
        List[Dict[str, Any]]
            분석 결과 리스트
        """
        try:
            print(f"🚀 배치 병렬 분석 시작: {len(texts)}개 텍스트")
            start_time = time.time()
            
            # 병렬 태스크 생성
            tasks = [self.analyze_text_comprehensive(text) for text in texts]
            
            # 병렬 실행
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 정리
            final_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"⚠️ 텍스트 {i} 분석 실패: {result}")
                    final_results.append({
                        "error": str(result),
                        "text_index": i
                    })
                else:
                    final_results.append(result)
            
            processing_time = time.time() - start_time
            print(f"✅ 배치 분석 완료: {processing_time:.2f}초")
            
            return final_results
            
        except Exception as e:
            print(f"⚠️ 배치 분석 실패: {e}")
            return [{"error": str(e)} for _ in texts]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        return self.performance_stats.copy()
    
    def cleanup_cache(self, max_age_hours: int = 24):
        """오래된 캐시 정리"""
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            with self.cache_lock:
                keys_to_remove = []
                
                for cache_key, cache_info in self.cache_metadata.items():
                    if current_time - cache_info["created_at"] > max_age_seconds:
                        keys_to_remove.append(cache_key)
                
                for cache_key in keys_to_remove:
                    cache_info = self.cache_metadata[cache_key]
                    cache_path = self.cache_dir / cache_info["filename"]
                    
                    try:
                        if cache_path.exists():
                            os.remove(cache_path)
                            print(f"🧹 분석 캐시 정리: {cache_info['filename']}")
                    except Exception as e:
                        print(f"⚠️ 캐시 파일 삭제 실패: {cache_path}, {e}")
                    
                    del self.cache_metadata[cache_key]
                
                if keys_to_remove:
                    self._save_cache_metadata()
                    print(f"🧹 {len(keys_to_remove)}개 분석 캐시 파일 정리 완료")
                    
        except Exception as e:
            print(f"⚠️ 분석 캐시 정리 실패: {e}")
    
    def cleanup(self):
        """리소스 정리"""
        if self.executor:
            self.executor.shutdown(wait=True) 