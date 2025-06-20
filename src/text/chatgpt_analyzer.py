import os
import json
import time
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import openai
import yaml

class BusinessType(Enum):
    """수집기관별 업무 유형"""
    FEE_INFO = "요금 안내"
    FEE_PAYMENT = "요금 납부"
    PLAN_CHANGE = "요금제 변경"
    SELECTIVE_DISCOUNT = "선택약정 할인"
    PAYMENT_METHOD_CHANGE = "납부 방법 변경"
    ADDITIONAL_SERVICE = "부가서비스 안내"
    MICRO_PAYMENT = "소액 결제"
    PHONE_SUSPENSION_LOSS_DAMAGE = "휴대폰 정지 분실 파손"
    DEVICE_CHANGE = "기기변경"
    NAME_NUMBER_USIM_CANCEL = "명의 번호 유심 해지"
    OTHER = "그 외 업무유형"

class ClassificationType(Enum):
    """분류 유형"""
    CONSULTATION_TOPIC = "상담 주제"
    CONSULTATION_REQUIREMENT = "상담 요건"
    CONSULTATION_CONTENT = "상담 내용"
    CONSULTATION_REASON = "상담 사유"
    CONSULTATION_RESULT = "상담 결과"

class DetailClassificationType(Enum):
    """세부 분류 유형"""
    # 상담 주제
    PRODUCT_SERVICE_GENERAL = "상품 및 서비스 일반"
    ORDER_PAYMENT_DEPOSIT_CONFIRM = "주문 결제 입금 확인"
    CANCEL_RETURN_EXCHANGE_REFUND_AS = "취소 반품 교환 환불 AS"
    MEMBER_MANAGEMENT = "회원 관리"
    DELIVERY_INQUIRY = "배송 문의"
    EVENT_DISCOUNT = "이벤트 할인"
    CONTENT = "콘텐츠"
    PARTNERSHIP = "제휴"
    ETC = "기타"
    
    # 상담 요건
    SINGLE_REQUIREMENT = "단일 요건 민원"
    MULTIPLE_REQUIREMENT = "다수 요건 민원"
    
    # 상담 내용
    GENERAL_INQUIRY = "일반 문의 상담"
    BUSINESS_PROCESSING = "업무 처리 상담"
    COMPLAINT = "고충 상담"
    
    # 상담 사유
    COMPANY = "업체"
    COMPLAINANT = "민원인"
    
    # 상담 결과
    SATISFACTION = "만족"
    INSUFFICIENT = "미흡"
    UNSOLVABLE = "해결 불가"
    ADDITIONAL_CONSULTATION = "추가 상담 필요"

@dataclass
class ConsultationAnalysisResult:
    """상담 분석 결과"""
    business_type: str
    classification_type: str
    detail_classification: str
    consultation_result: str
    summary: str
    customer_request: str
    solution: str
    additional_info: str
    confidence: float = 0.0
    processing_time: float = 0.0

class ChatGPTAnalyzer:
    """ChatGPT API를 사용한 상담 분석기"""
    
    def __init__(self, api_key: str, model: str = "gpt-4", max_tokens: int = 2000, temperature: float = 0.1):
        """
        ChatGPT 분석기 초기화
        
        Parameters
        ----------
        api_key : str
            OpenAI API 키
        model : str
            사용할 모델명 (기본값: gpt-4)
        max_tokens : int
            최대 토큰 수 (기본값: 2000)
        temperature : float
            생성 다양성 (기본값: 0.1)
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.client = openai.OpenAI(api_key=api_key)
        
        # 분석 프롬프트 템플릿
        self.analysis_prompt = self._create_analysis_prompt()
    
    def _create_analysis_prompt(self) -> str:
        """분석용 프롬프트 생성"""
        return """당신은 고객 상담 분석 전문가입니다. 
다음 상담 내용을 분석하여 JSON 형태로 결과를 반환해주세요.

## 분석 항목

### 1. 업무 유형 (다음 중 하나 선택):
- 요금 안내: 요금제, 청구서, 요금 관련 문의
- 요금 납부: 납부 방법, 연체, 결제 관련
- 요금제 변경: 플랜 변경, 업그레이드/다운그레이드
- 선택약정 할인: 약정 관련 혜택, 할인
- 납부 방법 변경: 결제 수단 변경
- 부가서비스 안내: 추가 서비스, 옵션
- 소액 결제: 콘텐츠 결제, 앱 결제
- 휴대폰 정지 분실 파손: 단말기 관련 문제
- 기기변경: 폰 교체, 기종 변경
- 명의 번호 유심 해지: 계약 해지, 명의 변경
- 그 외 업무유형: 위에 해당하지 않는 경우

### 2. 상담 분류:
- 상담 주제: 고객이 문의한 핵심 주제

### 3. 세부 분류:
- 상품 및 서비스 일반: 일반적인 상품/서비스 문의
- 주문 결제 입금 확인: 결제 및 주문 확인
- 취소 반품 교환 환불 AS: 취소/환불 관련
- 회원 관리: 계정, 개인정보 관리
- 배송 문의: 배송 상태, 주소 변경
- 이벤트 할인: 프로모션, 이벤트 관련
- 콘텐츠: 디지털 콘텐츠 관련
- 제휴: 파트너사 서비스
- 기타: 위에 해당하지 않는 경우

### 4. 상담 결과:
- 만족: 문제가 완전히 해결됨
- 미흡: 부분적으로 해결되었거나 고객이 아쉬워함
- 해결 불가: 기술적/정책적으로 해결 불가
- 추가 상담 필요: 추가 절차나 상담이 필요

## 분석 지침:
1. 상담 내용에서 고객의 핵심 요청사항을 파악하세요
2. 가장 적합한 업무 유형을 선택하세요
3. 고객의 만족도와 문제 해결 여부를 판단하세요
4. 구체적이고 명확한 요약을 작성하세요

## 응답 형식:
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요.

```json
{
    "business_type": "선택된 업무 유형",
    "classification_type": "상담 주제", 
    "detail_classification": "선택된 세부 분류",
    "consultation_result": "선택된 상담 결과",
    "summary": "상담 내용 요약 (50자 이내)",
    "customer_request": "고객의 구체적 요청사항",
    "solution": "제공된 해결방안",
    "additional_info": "추가 안내사항이나 특이사항",
    "confidence": 0.9
}
```

상담 내용:
{conversation_text}
"""
    
    def analyze_conversation(self, conversation_text: str) -> ConsultationAnalysisResult:
        """
        대화 내용 분석
        
        Parameters
        ----------
        conversation_text : str
            분석할 대화 내용
            
        Returns
        -------
        ConsultationAnalysisResult
            분석 결과
        """
        start_time = time.time()
        
        try:
            # ChatGPT API 호출
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 통신사 고객 상담 전문가입니다."},
                    {"role": "user", "content": self.analysis_prompt.format(conversation_text=conversation_text)}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # 응답 파싱
            content = response.choices[0].message.content
            result_dict = self._parse_json_response(content)
            
            processing_time = time.time() - start_time
            
            return ConsultationAnalysisResult(
                business_type=result_dict.get("business_type", "그 외 업무유형"),
                classification_type=result_dict.get("classification_type", "상담 주제"),
                detail_classification=result_dict.get("detail_classification", "기타"),
                consultation_result=result_dict.get("consultation_result", "미흡"),
                summary=result_dict.get("summary", ""),
                customer_request=result_dict.get("customer_request", ""),
                solution=result_dict.get("solution", ""),
                additional_info=result_dict.get("additional_info", ""),
                confidence=result_dict.get("confidence", 0.0),
                processing_time=processing_time
            )
            
        except Exception as e:
            print(f"ChatGPT 분석 중 오류 발생: {e}")
            # 기본값 반환
            return ConsultationAnalysisResult(
                business_type="그 외 업무유형",
                classification_type="상담 주제",
                detail_classification="기타",
                consultation_result="미흡",
                summary="분석 실패",
                customer_request="",
                solution="",
                additional_info="",
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """JSON 응답 파싱"""
        try:
            print(f"ChatGPT 응답 (처음 500자): {content[:500]}...")
            
            json_str = None
            
            # 방법 1: ```json 블록 찾기
            json_start = content.find('```json')
            if json_start != -1:
                json_start = content.find('\n', json_start) + 1
                json_end = content.find('```', json_start)
                if json_end != -1:
                    json_str = content[json_start:json_end].strip()
            
            # 방법 2: ``` 블록 찾기
            if not json_str:
                json_start = content.find('```')
                if json_start != -1:
                    json_start = content.find('\n', json_start) + 1
                    json_end = content.find('```', json_start)
                    if json_end != -1:
                        json_str = content[json_start:json_end].strip()
            
            # 방법 3: 중괄호로 감싸진 JSON 찾기
            if not json_str:
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                
                if start_idx != -1 and end_idx != 0:
                    json_str = content[start_idx:end_idx]
            
            if json_str:
                print(f"추출된 JSON 문자열: {json_str}")
                
                # JSON 문자열 정리
                json_str = json_str.strip()
                
                # 불필요한 주석이나 설명 제거
                lines = json_str.split('\n')
                clean_lines = []
                in_json = False
                brace_count = 0
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('{'):
                        in_json = True
                    
                    if in_json:
                        clean_lines.append(line)
                        brace_count += line.count('{') - line.count('}')
                        
                        if brace_count == 0 and '}' in line:
                            break
                
                json_str = '\n'.join(clean_lines)
                print(f"정리된 JSON: {json_str}")
                
                return json.loads(json_str)
            else:
                print(f"JSON 블록을 찾을 수 없습니다.")
                return {}
                
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
            print(f"파싱 시도한 문자열: {json_str}")
            
            # 간단한 정규식으로 재시도
            try:
                import re
                # 기본 패턴 매칭으로 값 추출
                patterns = {
                    'business_type': r'"business_type"\s*:\s*"([^"]*)"',
                    'classification_type': r'"classification_type"\s*:\s*"([^"]*)"',
                    'detail_classification': r'"detail_classification"\s*:\s*"([^"]*)"',
                    'consultation_result': r'"consultation_result"\s*:\s*"([^"]*)"',
                    'summary': r'"summary"\s*:\s*"([^"]*)"',
                    'customer_request': r'"customer_request"\s*:\s*"([^"]*)"',
                    'solution': r'"solution"\s*:\s*"([^"]*)"',
                    'additional_info': r'"additional_info"\s*:\s*"([^"]*)"',
                    'confidence': r'"confidence"\s*:\s*([0-9.]+)'
                }
                
                result = {}
                for key, pattern in patterns.items():
                    match = re.search(pattern, content)
                    if match:
                        if key == 'confidence':
                            result[key] = float(match.group(1))
                        else:
                            result[key] = match.group(1)
                
                if result:
                    print(f"정규식으로 추출한 결과: {result}")
                    return result
                
            except Exception as regex_e:
                print(f"정규식 파싱도 실패: {regex_e}")
            
            return {}
        except Exception as e:
            print(f"JSON 파싱 중 예상치 못한 오류: {e}")
            return {}
    
    def batch_analyze(self, conversations: List[str]) -> List[ConsultationAnalysisResult]:
        """
        여러 대화 내용 일괄 분석
        
        Parameters
        ----------
        conversations : List[str]
            분석할 대화 내용 리스트
            
        Returns
        -------
        List[ConsultationAnalysisResult]
            분석 결과 리스트
        """
        results = []
        for conversation in conversations:
            result = self.analyze_conversation(conversation)
            results.append(result)
            # API 호출 간격 조절
            time.sleep(0.5)
        return results 