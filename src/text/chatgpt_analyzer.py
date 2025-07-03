# import openai  # 필요시 주석 해제
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

@dataclass
class AnalysisResult:
    """분석 결과를 담는 데이터 클래스"""
    business_type: str
    classification_type: str
    detail_classification: str
    consultation_result: str
    summary: str
    customer_request: str
    solution: str
    additional_info: str
    confidence: float

class ChatGPTAnalyzer:
    """
    ChatGPT를 사용한 상담 내용 분석기
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        max_tokens: int = 2000,
        temperature: float = 0.1
    ):
        """
        ChatGPT 분석기 초기화
        
        Parameters
        ----------
        api_key : str
            OpenAI API 키
        model : str
            사용할 GPT 모델
        max_tokens : int
            최대 토큰 수
        temperature : float
            생성 다양성
        """
        # self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        self.logger = logging.getLogger(__name__)
        
        # 상담 분석 프롬프트
        self.analysis_prompt = None"
다음 상담 내용을 분석하여 JSON 형태로 결과를 제공해주세요.

분석 항목:
1. business_type: 업무 유형 (요금 안내, 요금 납부, 요금제 변경, 선택약정 할인, 납부 방법 변경, 부가서비스 안내, 소액 결제, 휴대폰 정지 분실 파손, 기기변경, 명의 번호 유심 해지, 그 외 업무유형)
2. classification_type: 분류 유형 (상담 주제, 상담 요건, 상담 내용, 상담 사유, 상담 결과)
3. detail_classification: 세부 분류
4. consultation_result: 상담 결과 (만족, 미흡, 해결 불가, 추가 상담 필요)
5. summary: 상담 요약 (100자 이내)
6. customer_request: 고객 요청사항
7. solution: 제공된 해결방안
8. additional_info: 추가 정보
9. confidence: 분석 신뢰도 (0.0-1.0)

상담 내용:
{conversation_text}

응답 형식:
{{
    "business_type": "...",
    "classification_type": "...",
    "detail_classification": "...",
    "consultation_result": "...",
    "summary": "...",
    "customer_request": "...",
    "solution": "...",
    "additional_info": "...",
    "confidence": 0.0
}}
"""
    
    def text_analyze_conversation(self, conversation_text: str) -> AnalysisResult:
        """
        상담 내용을 분석합니다.
        
        Parameters
        ----------
        conversation_text : str
            분석할 상담 내용
            
        Returns
        -------
        AnalysisResult
            분석 결과
        """
        try:
            # ChatGPT API 호출
            # response = self.client.chat.completions.create(
            #     model=self.model,
            #     messages=[
            #         {
            #             "role": "system",
            #             "content": "당신은 고객 상담 내용을 분석하는 전문가입니다. 정확하고 객관적인 분석을 제공해주세요."
            #         },
            #         {
            #             "role": "user",
            #             "content": self.analysis_prompt.format(conversation_text=conversation_text)
            #         }
            #     ],
            #     max_tokens=self.max_tokens,
            #     temperature=self.temperature
            # )
            
            # 응답 파싱
            # result_text = response.choices[0].message.content
            
            # JSON 파싱 시도
            # import json
            # try:
            #     result_dict = json.loads(result_text)
            # except json.JSONDecodeError:
            #     # JSON 파싱 실패 시 기본값 반환
            #     self.logger.warning("ChatGPT 응답을 JSON으로 파싱할 수 없습니다. 기본값을 사용합니다.")
            #     result_dict = {
            #         "business_type": "그 외 업무유형",
            #         "classification_type": "상담 주제",
            #         "detail_classification": "기타",
            #         "consultation_result": "추가 상담 필요",
            #         "summary": "분석 실패",
            #         "customer_request": "파악 불가",
            #         "solution": "추가 분석 필요",
            #         "additional_info": "ChatGPT 응답 파싱 실패",
            #         "confidence": 0.1
            #     }
            
            # AnalysisResult 객체 생성
            return AnalysisResult(
                business_type="그 외 업무유형",
                classification_type="상담 주제",
                detail_classification="기타",
                consultation_result="추가 상담 필요",
                summary="요약 없음",
                customer_request="요청사항 파악 불가",
                solution="해결방안 없음",
                additional_info="추가 정보 없음",
                confidence=0.5
            )
            
        except Exception as e:
            self.logger.error(f"ChatGPT 분석 중 오류 발생: {e}")
            
            # 오류 발생 시 기본값 반환
            return AnalysisResult(
                business_type="그 외 업무유형",
                classification_type="상담 주제",
                detail_classification="기타",
                consultation_result="해결 불가",
                summary="분석 오류 발생",
                customer_request="파악 불가",
                solution="추가 분석 필요",
                additional_info=f"오류: {str(e)}",
                confidence=0.0
            )
    
    def text_batch_analyze(self, conversations: list) -> list:
        """
        여러 상담 내용을 일괄 분석합니다.
        
        Parameters
        ----------
        conversations : list
            분석할 상담 내용 리스트
            
        Returns
        -------
        list
            분석 결과 리스트
        """
        results = []
        for i, conversation in enumerate(conversations):
            self.logger.info(f"상담 분석 진행: {i+1}/{len(conversations)}")
            result = self.text_analyze_conversation(conversation)
            results.append(result)
        
        return results 