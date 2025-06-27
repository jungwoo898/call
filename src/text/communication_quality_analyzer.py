#!/usr/bin/env python3
"""
상담사 커뮤니케이션 품질 분석 모듈
8가지 품질 지표를 계산하여 상담사의 커뮤니케이션 스킬을 정량 평가
"""

import re
import json
import requests
import os
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import pandas as pd

# LLM 기능 import
try:
    from src.text.llm import LLMHandler
except ImportError:
    print("⚠️ LLM 기능을 사용할 수 없습니다. LLM 기반 지표는 None으로 반환됩니다.")
    LLMHandler = None


@dataclass
class CommunicationQualityResult:
    """커뮤니케이션 품질 분석 결과"""
    honorific_ratio: float
    positive_word_ratio: float
    negative_word_ratio: float
    euphonious_word_ratio: float
    empathy_ratio: float
    apology_ratio: float
    total_sentences: int
    analysis_details: Dict[str, Any]
    
    # 새로운 정량 분석 지표 5종
    customer_sentiment_early: Optional[float] = None  # 고객 감정 초반부 평균
    customer_sentiment_late: Optional[float] = None   # 고객 감정 후반부 평균  
    customer_sentiment_trend: Optional[float] = None  # 고객 감정 변화 추세
    avg_response_latency: Optional[float] = None      # 평균 응답 지연 시간
    task_ratio: Optional[float] = None                # 업무 처리 비율
    
    # 새로운 LLM 기반 정성 평가 지표 2종
    suggestions: Optional[float] = None               # 문제 해결 제안 점수 (0.0, 0.2, 0.6, 1.0)
    interruption_count: Optional[int] = None          # 대화 가로채기 횟수


class CommunicationQualityAnalyzer:
    """
    상담사 커뮤니케이션 품질 분석기
    
    화자 분리된 JSON 데이터에서 상담사 발화를 추출하고
    6가지 품질 지표를 계산합니다.
    """
    
    def __init__(self):
        """분석기 초기화"""
        self.sentiment_dict = None
        self._load_sentiment_dictionary()
        
        # 패턴 정의
        self._define_patterns()
        
        # LLM 핸들러 초기화
        self.llm_handler = None
        if LLMHandler is not None:
            try:
                self.llm_handler = LLMHandler()
                print("✅ LLM 핸들러 초기화 완료")
            except Exception as e:
                print(f"⚠️ LLM 핸들러 초기화 실패: {e}")
                self.llm_handler = None
        else:
            print("⚠️ LLM 핸들러를 사용할 수 없습니다.")
    
    def _load_sentiment_dictionary(self):
        """KNU 한국어 감성사전 로드"""
        try:
            # 감성사전 파일 경로
            dict_path = "data/knu_sentiment_dict.json"
            
            if os.path.exists(dict_path):
                print("✅ 로컬 감성사전 로드")
                with open(dict_path, 'r', encoding='utf-8') as f:
                    self.sentiment_dict = json.load(f)
            else:
                print("🔄 KNU 한국어 감성사전 다운로드 중...")
                self._download_sentiment_dictionary(dict_path)
                
        except Exception as e:
            print(f"⚠️ 감성사전 로드 실패: {e}")
            print("기본 감성사전을 사용합니다.")
            self._create_fallback_sentiment_dict()
    
    def _download_sentiment_dictionary(self, save_path: str):
        """KNU 한국어 감성사전 다운로드"""
        try:
            # KNU 감성사전 URL (GitHub 또는 공식 저장소)
            url = "https://raw.githubusercontent.com/park1200656/KnuSentiLex/master/KnuSentiLex.json"
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # 디렉토리 생성
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # JSON 파싱 및 저장
            sentiment_data = response.json()
            
            # 사전 형태로 변환 (단어: polarity)
            self.sentiment_dict = {}
            for word, info in sentiment_data.items():
                if isinstance(info, dict) and 'polarity' in info:
                    self.sentiment_dict[word] = info['polarity']
                elif isinstance(info, (int, float)):
                    self.sentiment_dict[word] = info
            
            # 파일 저장
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.sentiment_dict, f, ensure_ascii=False, indent=2)
                
            print(f"✅ 감성사전 다운로드 완료: {len(self.sentiment_dict)}개 단어")
            
        except Exception as e:
            print(f"❌ 감성사전 다운로드 실패: {e}")
            self._create_fallback_sentiment_dict()
    
    def _create_fallback_sentiment_dict(self):
        """기본 감성사전 생성 (다운로드 실패 시)"""
        self.sentiment_dict = {
            # 긍정 단어 (Positive Words) - 30개
            "좋다": 1, "감사하다": 2, "기쁘다": 2, "다행이다": 2, "만족하다": 2, 
            "안심이다": 2, "친절하다": 2, "훌륭하다": 2, "행복하다": 2, "고맙다": 2,
            "도움": 1, "성공": 1, "해결": 1, "효과": 1, "편리하다": 1, 
            "빠르다": 1, "쉽다": 1, "정확하다": 1, "간편하다": 1, "뛰어나다": 1,
            "완벽하다": 2, "최고다": 2, "우수하다": 1, "기대되다": 1, "대단하다": 1,
            "멋지다": 1, "상세하다": 1, "신속하다": 1, "안정적": 1,

            # 부정 단어 (Negative Words) - 30개
            "나쁘다": -1, "싫다": -1, "문제": -1, "오류": -1, "어렵다": -1,
            "느리다": -1, "복잡하다": -1, "힘들다": -1, "아쉽다": -1, "유감": -1,
            "실망하다": -2, "화나다": -2, "짜증나다": -2, "불편하다": -2, "불만": -2, 
            "실패": -2, "답답하다": -2, "속상하다": -2, "걱정되다": -1, "불안하다": -1,
            "위험하다": -2, "귀찮다": -1, "피곤하다": -1, "최악": -2, "엉망": -2,
            "부족하다": -1, "불가능하다": -2, "불친절하다": -2, "지연": -1, "누락": -1, "오작동":-2
        }
        print(f"✅ 강화된 기본 감성사전 생성: {len(self.sentiment_dict)}개 단어")

    def _define_patterns(self):
        """분석용 패턴 정의 (강화 버전)"""
        
        # 1. 존댓말 패턴 (Honorific Patterns)
        self.honorific_patterns = [
            # 공식적 종결어미 (하십시오체)
            r'습니다$', r'ㅂ니다$', r'ㅂ니까\?$', r'시죠$', r'하십시오$', r'해주십시오$',
            # 보편적 종결어미 (해요체)
            r'해요$', r'세요$', r'셔요$', r'네요$', r'걸요$', r'지요\?$', r'까요\?$',
            # 서비스 제공 표현
            r'드립니다$', r'드려요$', r'해드릴게요$', r'도와드릴까요\?$',
            # 주체 높임 선어말 어미 '-(으)시-'
            r'(으)시겠습니다$', r'(으)셨습니다$', r'(으)십니다$', r'(으)시죠$', r'(으)시네요$', 
            r'(으)시는군요$', r'이십니다$',
            # 연결형
            r'하시면$', r'하시고$', r'이시고$'
        ]
        
        # 4. 쿠션어/완곡 표현 (Euphonious Patterns)
        self.euphonious_patterns = [
            # [쿠션어] 양해/요청
            r'실례지만', r'죄송하지만', r'괜찮으시다면', r'혹시라도', r'바쁘시겠지만', 
            r'번거로우시겠지만', r'염려스러우시겠지만', r'다름이 아니오라',
            # [쿠션어] 제안/의견
            r'만약', r'예를 들어', r'아쉽지만', r'유감이지만',
            
            # [완곡 표현] 단정 회피
            r'인 것 같습니다$', r'ㄹ 것 같습니다$', r'듯합니다$', r'ㄹ 듯합니다$', r'로 보입니다$',
            # [완곡 표현] 부드러운 거절/부정
            r'도움드리기 어렵습니다$', r'처리가 곤란합니다$', r'확인이 필요합니다$', 
            r'검토 후 말씀드리겠습니다$', r'규정상 어렵습니다$',
            # [완곡 표현] 부드러운 요청
            r'ㄹ 수 있을까요\?$', r'해 주시겠어요\?$', r'해 주실 수 있나요\?$', 
            r'부탁드려도 될까요\?$', r'확인해주시면 감사하겠습니다$'
        ]
        
        # 5. 공감 표현 (Empathy Patterns)
        self.empathy_patterns = [
            # [감정 읽기] 고객의 감정 상태를 짐작하고 언급
            r'속상하셨겠어요', r'답답하셨겠네요', r'많이 놀라셨겠어요', r'불편하셨겠어요',
            r'걱정 많이 하셨겠네요', r'많이 힘드셨죠', r'신경 쓰이셨겠어요',
            # [감정 인정] 고객의 감정에 타당성 부여
            r'어떤 마음인지 알 것 같습니다', r'충분히 이해됩니다', r'그렇게 생각하실 수 있습니다',
            r'오죽하면 그러셨겠어요',
            # [관점 수용] 고객의 입장에서 생각
            r'제가 고객님 입장이라도', r'제가 같은 상황이었더라도',
            # [공감적 추임새] 대화에 집중하고 있음을 표현
            r'아이고(,)? 저런', r'어머나', r'그랬군요'
        ]
        
        # 6. 사과 표현 (Apology Patterns)
        self.apology_patterns = [
            # [직접 사과] 직접적인 사과 표현
            r'죄송합니다', r'정말 죄송합니다', r'대단히 죄송합니다', r'사과드립니다', r'진심으로 사과드립니다',
            # [상황 유감 표현] 불편을 끼친 상황에 대한 유감
            r'불편을 드려 죄송합니다', r'심려를 끼쳐드려 죄송합니다', r'혼란을 드려 죄송합니다',
            r'오래 기다리게 해드려 죄송합니다',
            # [책임 인정] 자신의 과실을 인정
            r'저의 불찰입니다', r'저희의 잘못입니다',
            # [이해 요청] 고객의 이해를 구함
            r'양해 부탁드립니다', r'너그러이 이해해주시기 바랍니다'
        ]
    
    def analyze_communication_quality(self, utterances_data: List[Dict[str, Any]]) -> CommunicationQualityResult:
        """
        커뮤니케이션 품질 분석 수행
        
        Parameters
        ----------
        utterances_data : List[Dict[str, Any]]
            화자 분리된 발화 데이터
            각 항목은 {'speaker': str, 'text': str, ...} 형태
            
        Returns
        -------
        CommunicationQualityResult
            6가지 품질 지표 분석 결과
        """
        
        # 상담사 발화만 추출
        counselor_sentences = self._extract_counselor_sentences(utterances_data)
        
        if not counselor_sentences:
            return CommunicationQualityResult(
                honorific_ratio=0.0,
                positive_word_ratio=0.0,
                negative_word_ratio=0.0,
                euphonious_word_ratio=0.0,
                empathy_ratio=0.0,
                apology_ratio=0.0,
                total_sentences=0,
                analysis_details={"error": "상담사 발화를 찾을 수 없습니다."}
            )
        
        total_sentences = len(counselor_sentences)
        
        # 각 지표 계산
        honorific_count = self._count_honorific_sentences(counselor_sentences)
        positive_count = self._count_positive_word_sentences(counselor_sentences)
        negative_count = self._count_negative_word_sentences(counselor_sentences)
        euphonious_count = self._count_euphonious_sentences(counselor_sentences)
        empathy_count = self._count_empathy_sentences(counselor_sentences)
        apology_count = self._count_apology_sentences(counselor_sentences)
        
        # 비율 계산 (%)
        honorific_ratio = (honorific_count / total_sentences) * 100
        positive_word_ratio = (positive_count / total_sentences) * 100
        negative_word_ratio = (negative_count / total_sentences) * 100
        euphonious_word_ratio = (euphonious_count / total_sentences) * 100
        empathy_ratio = (empathy_count / total_sentences) * 100
        apology_ratio = (apology_count / total_sentences) * 100
        
        # 상세 분석 정보
        analysis_details = {
            "honorific_sentences": honorific_count,
            "positive_word_sentences": positive_count,
            "negative_word_sentences": negative_count,
            "euphonious_sentences": euphonious_count,
            "empathy_sentences": empathy_count,
            "apology_sentences": apology_count,
            "sample_sentences": {
                "honorific": self._get_sample_sentences(counselor_sentences, self.honorific_patterns, "존댓말"),
                "positive": self._get_sample_sentences_by_sentiment(counselor_sentences, "positive"),
                "negative": self._get_sample_sentences_by_sentiment(counselor_sentences, "negative"),
                "euphonious": self._get_sample_sentences(counselor_sentences, self.euphonious_patterns, "쿠션어"),
                "empathy": self._get_sample_sentences(counselor_sentences, self.empathy_patterns, "공감"),
                "apology": self._get_sample_sentences(counselor_sentences, self.apology_patterns, "사과")
            }
        }
        
        # 새로운 정량 분석 지표 5종 계산
        customer_sentiment_early, customer_sentiment_late, customer_sentiment_trend = self._calculate_customer_sentiment_trend(utterances_data)
        avg_response_latency = self._calculate_avg_response_latency(utterances_data)
        task_ratio = self._calculate_task_ratio(utterances_data)
        
        # 새로운 LLM 기반 정성 평가 지표 2종 계산
        suggestions = asyncio.run(self._calculate_suggestions_score(utterances_data))
        interruption_count = self._calculate_interruption_count(utterances_data)
        
        return CommunicationQualityResult(
            honorific_ratio=round(honorific_ratio, 2),
            positive_word_ratio=round(positive_word_ratio, 2),
            negative_word_ratio=round(negative_word_ratio, 2),
            euphonious_word_ratio=round(euphonious_word_ratio, 2),
            empathy_ratio=round(empathy_ratio, 2),
            apology_ratio=round(apology_ratio, 2),
            total_sentences=total_sentences,
            analysis_details=analysis_details,
            # 새로운 정량 분석 지표
            customer_sentiment_early=customer_sentiment_early,
            customer_sentiment_late=customer_sentiment_late,
            customer_sentiment_trend=customer_sentiment_trend,
            avg_response_latency=avg_response_latency,
            task_ratio=task_ratio,
            # 새로운 LLM 기반 정성 평가 지표
            suggestions=suggestions,
            interruption_count=interruption_count
        )
    
    def _extract_counselor_sentences(self, utterances_data: List[Dict[str, Any]]) -> List[str]:
        """상담사 발화만 추출하여 문장 단위로 분리"""
        counselor_sentences = []
        
        for utterance in utterances_data:
            speaker = utterance.get('speaker', '').lower()
            text = utterance.get('text', '').strip()
            
            # 상담사 발화 식별
            if any(keyword in speaker for keyword in ['상담사', 'counselor', 'agent', 'csr', 'staff']):
                if text:
                    # 문장 분리
                    sentences = self._split_sentences(text)
                    counselor_sentences.extend(sentences)
        
        return counselor_sentences
    
    def _split_sentences(self, text: str) -> List[str]:
        """텍스트를 문장 단위로 분리"""
        # 한국어 문장 부호 기준 분리
        sentences = re.split(r'[.!?。？！]+', text)
        
        # 빈 문장 제거 및 정리
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _count_honorific_sentences(self, sentences: List[str]) -> int:
        """존댓말 사용 문장 수 계산"""
        count = 0
        for sentence in sentences:
            for pattern in self.honorific_patterns:
                if re.search(pattern, sentence):
                    count += 1
                    break  # 하나의 문장에서 여러 패턴 매치되어도 1번만 카운트
        return count
    
    def _count_positive_word_sentences(self, sentences: List[str]) -> int:
        """긍정 단어 포함 문장 수 계산"""
        if not self.sentiment_dict:
            return 0
            
        count = 0
        for sentence in sentences:
            words = sentence.split()
            for word in words:
                # 형태소 분석 없이 단순 매칭 (추후 개선 가능)
                clean_word = re.sub(r'[^\w가-힣]', '', word)
                if clean_word in self.sentiment_dict and self.sentiment_dict[clean_word] > 0:
                    count += 1
                    break  # 하나의 문장에서 긍정 단어 발견 시 1번만 카운트
        return count
    
    def _count_negative_word_sentences(self, sentences: List[str]) -> int:
        """부정 단어 포함 문장 수 계산"""
        if not self.sentiment_dict:
            return 0
            
        count = 0
        for sentence in sentences:
            words = sentence.split()
            for word in words:
                # 형태소 분석 없이 단순 매칭 (추후 개선 가능)
                clean_word = re.sub(r'[^\w가-힣]', '', word)
                if clean_word in self.sentiment_dict and self.sentiment_dict[clean_word] < 0:
                    count += 1
                    break  # 하나의 문장에서 부정 단어 발견 시 1번만 카운트
        return count
    
    def _count_euphonious_sentences(self, sentences: List[str]) -> int:
        """쿠션어/완곡 표현 포함 문장 수 계산"""
        count = 0
        for sentence in sentences:
            for pattern in self.euphonious_patterns:
                if re.search(pattern, sentence):
                    count += 1
                    break  # 하나의 문장에서 여러 패턴 매치되어도 1번만 카운트
        return count
    
    def _count_empathy_sentences(self, sentences: List[str]) -> int:
        """공감 표현 포함 문장 수 계산"""
        count = 0
        for sentence in sentences:
            for pattern in self.empathy_patterns:
                if re.search(pattern, sentence):
                    count += 1
                    break  # 하나의 문장에서 여러 패턴 매치되어도 1번만 카운트
        return count
    
    def _count_apology_sentences(self, sentences: List[str]) -> int:
        """사과 표현 포함 문장 수 계산"""
        count = 0
        for sentence in sentences:
            for pattern in self.apology_patterns:
                if re.search(pattern, sentence):
                    count += 1
                    break  # 하나의 문장에서 여러 패턴 매치되어도 1번만 카운트
        return count
    
    def _get_sample_sentences(self, sentences: List[str], patterns: List[str], category: str) -> List[str]:
        """해당 패턴에 매치되는 샘플 문장들 반환 (최대 3개)"""
        samples = []
        for sentence in sentences:
            if len(samples) >= 3:
                break
            for pattern in patterns:
                if re.search(pattern, sentence):
                    samples.append(sentence)
                    break
        return samples
    
    def _get_sample_sentences_by_sentiment(self, sentences: List[str], sentiment_type: str) -> List[str]:
        """감정별 샘플 문장들 반환 (최대 3개)"""
        if not self.sentiment_dict:
            return []
            
        samples = []
        target_polarity = 1 if sentiment_type == "positive" else -1
        
        for sentence in sentences:
            if len(samples) >= 3:
                break
            words = sentence.split()
            for word in words:
                clean_word = re.sub(r'[^\w가-힣]', '', word)
                if (clean_word in self.sentiment_dict and 
                    ((sentiment_type == "positive" and self.sentiment_dict[clean_word] > 0) or
                     (sentiment_type == "negative" and self.sentiment_dict[clean_word] < 0))):
                    samples.append(sentence)
                    break
        return samples
    
    def _calculate_customer_sentiment_trend(self, utterances_data: List[Dict[str, Any]]) -> tuple:
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
    
    def _map_sentiment_to_score(self, sentiment_text: str) -> Optional[float]:
        """
        sentiment 텍스트를 숫자 점수로 매핑
        
        Parameters
        ----------
        sentiment_text : str
            감정 텍스트 (예: 'positive', 'negative', 'neutral')
            
        Returns
        -------
        Optional[float]
            감정 점수 또는 None
        """
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
    
    def _calculate_avg_response_latency(self, utterances_data: List[Dict[str, Any]]) -> Optional[float]:
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
    
    def _calculate_task_ratio(self, utterances_data: List[Dict[str, Any]]) -> Optional[float]:
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
    
    async def _calculate_suggestions_score(self, utterances_data: List[Dict[str, Any]]) -> Optional[float]:
        """
        LLM 기반 문제 해결 제안 점수 계산 (지표 6)
        
        Parameters
        ----------
        utterances_data : List[Dict[str, Any]]
            화자 분리된 발화 데이터
            
        Returns
        -------
        Optional[float]
            문제 해결 제안 점수 (1.0, 0.6, 0.2, 0.0) 또는 None
        """
        if self.llm_handler is None:
            print("⚠️ LLM 핸들러가 없어 문제 해결 제안 점수를 계산할 수 없습니다.")
            return None
            
        try:
            # 1. 전체 대화를 텍스트로 변환
            conversation_text = ""
            for utterance in utterances_data:
                speaker = utterance.get('speaker', 'Unknown')
                text = utterance.get('text', '').strip()
                if text:
                    conversation_text += f"{speaker}: {text}\n"
            
            if not conversation_text.strip():
                return None
            
            # 2. LLM 프롬프트 생성
            system_prompt = """당신은 상담 품질 평가 전문가입니다. 
상담 대화를 분석하고, 문제 해결 과정에 따라 아래 규칙에 맞춰 점수를 부여해주세요.

점수 기준:
- 1.0점: 최초로 제시한 아이디어로 문제가 해결됨
- 0.6점: 첫 번째 아이디어는 실패했지만, 두 번째로 제시한 아이디어로 해결됨  
- 0.2점: 세 번 이상의 아이디어를 제시하여 문제를 해결함
- 0.0점: 대화가 끝날 때까지 문제가 해결되지 못함

반드시 '1.0', '0.6', '0.2', '0.0' 중 하나의 숫자로만 답변해주세요."""

            user_prompt = f"다음 상담 대화를 분석하여 문제 해결 제안 점수를 부여해주세요:\n\n{conversation_text}"
            
            # 3. LLM API 호출
            response = await self.llm_handler.client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            # 4. 응답 파싱
            response_text = response.choices[0].message.content.strip()
            
            # 5. 점수 추출
            if "1.0" in response_text:
                return 1.0
            elif "0.6" in response_text:
                return 0.6
            elif "0.2" in response_text:
                return 0.2
            elif "0.0" in response_text:
                return 0.0
            else:
                print(f"⚠️ LLM 응답 파싱 실패: {response_text}")
                return None
                
        except Exception as e:
            print(f"⚠️ 문제 해결 제안 점수 계산 실패: {e}")
            return None
    
    def _calculate_interruption_count(self, utterances_data: List[Dict[str, Any]]) -> Optional[int]:
        """
        대화 가로채기 횟수 계산 (지표 7)
        
        Parameters
        ----------
        utterances_data : List[Dict[str, Any]]
            화자 분리된 발화 데이터 (start_time, end_time 필수)
            
        Returns
        -------
        Optional[int]
            대화 가로채기 횟수 또는 None
        """
        try:
            if len(utterances_data) < 2:
                return 0
            
            interruption_count = 0
            
            # 1. 발화 순서대로 정렬 (start_time 기준)
            sorted_utterances = sorted(utterances_data, key=lambda x: x.get('start_time', 0))
            
            # 2. 연속된 발화 쌍을 검사
            for i in range(1, len(sorted_utterances)):
                prev_utterance = sorted_utterances[i-1]
                curr_utterance = sorted_utterances[i]
                
                prev_speaker = prev_utterance.get('speaker', '').lower()
                curr_speaker = curr_utterance.get('speaker', '').lower()
                
                prev_end_time = prev_utterance.get('end_time')
                curr_start_time = curr_utterance.get('start_time')
                
                # 3. 시간 정보가 있는 경우만 검사
                if prev_end_time is not None and curr_start_time is not None:
                    # 4. 이전 발화가 고객, 현재 발화가 상담사인 경우
                    if (any(keyword in prev_speaker for keyword in ['고객', 'customer', 'client', 'user']) and
                        any(keyword in curr_speaker for keyword in ['상담사', 'counselor', 'agent', 'csr', 'staff'])):
                        
                        # 5. 상담사 발화 시작 시간 < 고객 발화 종료 시간 → 가로채기
                        if curr_start_time < prev_end_time:
                            interruption_count += 1
                            print(f"🔍 가로채기 감지: 상담사가 {prev_end_time - curr_start_time:.2f}초 일찍 발화 시작")
            
            return interruption_count
            
        except Exception as e:
            print(f"⚠️ 대화 가로채기 횟수 계산 실패: {e}")
            return None
    
    def export_results_to_dataframe(self, result: CommunicationQualityResult) -> pd.DataFrame:
        """분석 결과를 DataFrame으로 변환"""
        data = {
            'honorific_ratio': [result.honorific_ratio],
            'positive_word_ratio': [result.positive_word_ratio],
            'negative_word_ratio': [result.negative_word_ratio],
            'euphonious_word_ratio': [result.euphonious_word_ratio],
            'empathy_ratio': [result.empathy_ratio],
            'apology_ratio': [result.apology_ratio],
            'total_sentences': [result.total_sentences],
            # 새로운 정량 분석 지표 5종
            'customer_sentiment_early': [result.customer_sentiment_early],
            'customer_sentiment_late': [result.customer_sentiment_late],
            'customer_sentiment_trend': [result.customer_sentiment_trend],
            'avg_response_latency': [result.avg_response_latency],
            'task_ratio': [result.task_ratio],
            # 새로운 LLM 기반 정성 평가 지표 2종
            'suggestions': [result.suggestions],
            'interruption_count': [result.interruption_count]
        }
        
        return pd.DataFrame(data)
    
    def print_analysis_report(self, result: CommunicationQualityResult):
        """분석 결과 리포트 출력"""
        print("\n" + "="*60)
        print("📊 상담사 커뮤니케이션 품질 분석 결과")
        print("="*60)
        
        print(f"📝 총 상담사 발화 문장 수: {result.total_sentences}개")
        print()
        
        print("📈 품질 지표 (%):")
        print(f"  1. 존댓말 사용 비율:     {result.honorific_ratio:6.2f}%")
        print(f"  2. 긍정 단어 비율:       {result.positive_word_ratio:6.2f}%")
        print(f"  3. 부정 단어 비율:       {result.negative_word_ratio:6.2f}%")
        print(f"  4. 쿠션어/완곡 표현:     {result.euphonious_word_ratio:6.2f}%")
        print(f"  5. 공감 표현 비율:       {result.empathy_ratio:6.2f}%")
        print(f"  6. 사과 표현 비율:       {result.apology_ratio:6.2f}%")
        
        print("\n📊 정량 분석 지표:")
        if result.customer_sentiment_early is not None:
            print(f"  1. 고객 감정 초반부:     {result.customer_sentiment_early:6.3f}")
        else:
            print(f"  1. 고객 감정 초반부:     {'N/A':>6}")
            
        if result.customer_sentiment_late is not None:
            print(f"  2. 고객 감정 후반부:     {result.customer_sentiment_late:6.3f}")
        else:
            print(f"  2. 고객 감정 후반부:     {'N/A':>6}")
            
        if result.customer_sentiment_trend is not None:
            print(f"  3. 고객 감정 변화 추세:  {result.customer_sentiment_trend:6.3f}")
            trend_desc = "개선됨" if result.customer_sentiment_trend > 0 else "악화됨" if result.customer_sentiment_trend < 0 else "변화없음"
            print(f"     → {trend_desc}")
        else:
            print(f"  3. 고객 감정 변화 추세:  {'N/A':>6}")
            
        if result.avg_response_latency is not None:
            print(f"  4. 평균 응답 지연 시간:  {result.avg_response_latency:6.3f}초")
        else:
            print(f"  4. 평균 응답 지연 시간:  {'N/A':>6}")
            
        if result.task_ratio is not None:
            print(f"  5. 업무 처리 비율:       {result.task_ratio:6.3f}")
            ratio_desc = "고객 발화 > 상담사 발화" if result.task_ratio > 1 else "상담사 발화 > 고객 발화" if result.task_ratio < 1 else "균형적"
            print(f"     → {ratio_desc}")
        else:
            print(f"  5. 업무 처리 비율:       {'N/A':>6}")
        
        print("\n🤖 LLM 기반 정성 평가 지표:")
        if result.suggestions is not None:
            print(f"  6. 문제 해결 제안 점수:  {result.suggestions:6.1f}")
            if result.suggestions == 1.0:
                print(f"     → 최초 제안으로 문제 해결")
            elif result.suggestions == 0.6:
                print(f"     → 두 번째 제안으로 문제 해결")
            elif result.suggestions == 0.2:
                print(f"     → 세 번 이상 제안으로 문제 해결")
            else:
                print(f"     → 문제 해결 실패")
        else:
            print(f"  6. 문제 해결 제안 점수:  {'N/A':>6}")
            
        if result.interruption_count is not None:
            print(f"  7. 대화 가로채기 횟수:   {result.interruption_count:6d}회")
            if result.interruption_count == 0:
                print(f"     → 가로채기 없음 (양호)")
            elif result.interruption_count <= 2:
                print(f"     → 가로채기 적음 (보통)")
            else:
                print(f"     → 가로채기 많음 (개선 필요)")
        else:
            print(f"  7. 대화 가로채기 횟수:   {'N/A':>6}")
        
        print("\n💡 품질 평가:")
        self._print_quality_assessment(result)
        
        print("\n📋 샘플 문장들:")
        details = result.analysis_details.get('sample_sentences', {})
        for category, samples in details.items():
            if samples:
                print(f"\n  {category.upper()}:")
                for i, sample in enumerate(samples[:2], 1):  # 최대 2개만 출력
                    print(f"    {i}. {sample}")
    
    def _print_quality_assessment(self, result: CommunicationQualityResult):
        """품질 평가 코멘트 출력"""
        assessments = []
        
        if result.honorific_ratio >= 80:
            assessments.append("✅ 존댓말 사용이 우수함")
        elif result.honorific_ratio >= 60:
            assessments.append("⚠️ 존댓말 사용 개선 필요")
        else:
            assessments.append("❌ 존댓말 사용이 부족함")
        
        if result.positive_word_ratio >= 30:
            assessments.append("✅ 긍정적 언어 사용이 우수함")
        elif result.positive_word_ratio >= 15:
            assessments.append("⚠️ 긍정적 언어 사용 개선 필요")
        else:
            assessments.append("❌ 긍정적 언어 사용이 부족함")
        
        if result.negative_word_ratio <= 10:
            assessments.append("✅ 부정적 언어 사용이 적절함")
        elif result.negative_word_ratio <= 20:
            assessments.append("⚠️ 부정적 언어 사용 주의 필요")
        else:
            assessments.append("❌ 부정적 언어 사용이 과다함")
        
        if result.euphonious_word_ratio >= 20:
            assessments.append("✅ 쿠션어 사용이 우수함")
        elif result.euphonious_word_ratio >= 10:
            assessments.append("⚠️ 쿠션어 사용 개선 필요")
        else:
            assessments.append("❌ 쿠션어 사용이 부족함")
        
        for assessment in assessments:
            print(f"    {assessment}")


# 사용 예시 및 테스트 함수
def test_communication_quality_analyzer():
    """분석기 테스트"""
    
    # 샘플 데이터 (시간 정보와 감정 정보 포함)
    sample_utterances = [
        {"speaker": "고객", "text": "안녕하세요. 요금 관련해서 문의드리고 싶습니다.", 
         "start_time": 0.0, "end_time": 3.0, "sentiment": "neutral"},
        {"speaker": "상담사", "text": "안녕하세요. 고객님. 요금 관련 문의 도와드리겠습니다. 어떤 부분이 궁금하신가요?", 
         "start_time": 4.0, "end_time": 8.0, "sentiment": "positive"},
        {"speaker": "고객", "text": "이번 달 요금이 너무 많이 나왔어요. 왜 이렇게 많이 나온 건지 모르겠어요.", 
         "start_time": 9.0, "end_time": 13.0, "sentiment": "negative"},
        {"speaker": "상담사", "text": "걱정되셨겠어요. 죄송합니다. 요금 내역을 확인해드리겠습니다. 혹시 해외 로밍을 사용하셨나요?", 
         "start_time": 14.5, "end_time": 19.0, "sentiment": "positive"},
        {"speaker": "고객", "text": "아니요. 해외에 안 갔는데요.", 
         "start_time": 20.0, "end_time": 22.0, "sentiment": "neutral"},
        {"speaker": "상담사", "text": "그렇다면 데이터 사용량을 확인해보겠습니다. 실례지만 휴대폰 번호를 알려주시겠어요?", 
         "start_time": 23.0, "end_time": 27.0, "sentiment": "positive"},
        {"speaker": "고객", "text": "010-1234-5678입니다.", 
         "start_time": 28.0, "end_time": 30.0, "sentiment": "neutral"},
        {"speaker": "상담사", "text": "감사합니다. 확인해보니 이번 달에 데이터를 많이 사용하셨네요. 동영상 시청이나 게임을 하셨을 것 같습니다.", 
         "start_time": 31.5, "end_time": 36.0, "sentiment": "positive"},
        {"speaker": "고객", "text": "아 그런가요? 그럼 어떻게 해야 하나요?", 
         "start_time": 37.0, "end_time": 39.0, "sentiment": "neutral"},
        {"speaker": "상담사", "text": "다음 달부터는 데이터 사용량을 체크해주시면 좋을 것 같습니다. 도움이 되셨나요?", 
         "start_time": 40.0, "end_time": 44.0, "sentiment": "positive"}
    ]
    
    # 분석 수행
    analyzer = CommunicationQualityAnalyzer()
    result = analyzer.analyze_communication_quality(sample_utterances)
    
    # 결과 출력
    analyzer.print_analysis_report(result)
    
    # DataFrame 변환
    df = analyzer.export_results_to_dataframe(result)
    print("\n📊 DataFrame 결과:")
    print(df.to_string(index=False))
    
    return result


if __name__ == "__main__":
    # 테스트 실행
    test_communication_quality_analyzer() 