import os
import sys
import time
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.audio.processing import IntegratedAudioProcessor
from src.text.chatgpt_analyzer import ChatGPTAnalyzer
from src.text.communication_quality_analyzer import CommunicationQualityAnalyzer
from src.db.manager import DatabaseManager
from src.utils.performance_monitor import PerformanceMonitor

# Windows 환경에서 signal 모듈 패치
import signal
if not hasattr(signal, 'SIGKILL'):
    signal.SIGKILL = signal.SIGTERM
if not hasattr(signal, 'SIGUSR1'):
    signal.SIGUSR1 = signal.SIGTERM
if not hasattr(signal, 'SIGUSR2'):
    signal.SIGUSR2 = signal.SIGTERM

# Windows 환경에서 pyannote.audio 안정성을 위한 환경 변수 설정
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'
os.environ['CUDA_LAUNCH_BLOCKING'] = '1'

class IntegratedAnalyzer:
    """
    통합 분석기 - 오디오 처리부터 상담 분석까지 완전한 파이프라인
    """
    
    def __init__(
        self,
        config_path: str = "config/config_enhanced.yaml",
        diarization_token: Optional[str] = None
    ):
        """
        통합 분석기 초기화
        
        Parameters
        ----------
        config_path : str
            설정 파일 경로
        diarization_token : str, optional
            HuggingFace 인증 토큰 (화자 분리용)
        """
        self.config_path = config_path
        self.diarization_token = diarization_token
        
        # 로깅 설정
        self._setup_logging()
        
        # 컴포넌트 초기화
        self.audio_processor = IntegratedAudioProcessor(
            language="ko",
            device="auto",
            whisper_model="medium",
            diarization_auth_token=diarization_token
        )
        
        # 설정에서 OpenAI API 키 로드
        api_key = self._load_openai_api_key()
        self.consultation_analyzer = ChatGPTAnalyzer(
            api_key=api_key,
            model="gpt-4.1-nano",
            max_tokens=2000,
            temperature=0.1
        )
        
        self.db_manager = DatabaseManager(config_path)
        self.performance_monitor = PerformanceMonitor()
        
        # 커뮤니케이션 품질 분석기 초기화
        self.quality_analyzer = CommunicationQualityAnalyzer()
        
        self.logger.info("통합 분석기 초기화 완료")
    
    def _setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/integrated_analysis.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _load_openai_api_key(self) -> str:
        """설정에서 OpenAI API 키 로드"""
        try:
            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config.get('openai', {}).get('api_key') or os.getenv('OPENAI_API_KEY')
        except Exception as e:
            self.logger.warning(f"설정 파일 로드 실패, 환경 변수 사용: {e}")
            return os.getenv('OPENAI_API_KEY')
    
    def analyze_consultation(
        self,
        audio_path: str,
        consultation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        상담 오디오를 분석하여 결과를 반환하고 데이터베이스에 저장
        
        Parameters
        ----------
        audio_path : str
            분석할 오디오 파일 경로
        consultation_id : str, optional
            상담 ID (None이면 자동 생성)
        metadata : dict, optional
            추가 메타데이터
            
        Returns
        -------
        Dict[str, Any]
            분석 결과
        """
        try:
            self.logger.info(f"상담 분석 시작: {audio_path}")
            self.performance_monitor.start()
            
            # 1. 오디오 처리 (화자 분리 + 음성 인식)
            self.logger.info("1단계: 오디오 처리 시작")
            utterances = self.audio_processor.process_audio(audio_path)
            
            if not utterances:
                raise ValueError("오디오에서 발화를 추출할 수 없습니다.")
            
            # 2. 상담 내용 분석
            self.logger.info("2단계: 상담 내용 분석 시작")
            full_text = " ".join([u['text'] for u in utterances])
            analysis_result = self.consultation_analyzer.analyze_conversation(full_text)
            
            # 3. 커뮤니케이션 품질 분석
            self.logger.info("3단계: 커뮤니케이션 품질 분석 시작")
            quality_result = self.quality_analyzer.analyze_communication_quality(utterances)
            
            # 4. 결과 통합
            self.logger.info("4단계: 결과 통합")
            integrated_result = {
                'consultation_id': consultation_id or f"consultation_{int(time.time())}",
                'audio_path': audio_path,
                'metadata': metadata or {},
                'utterances': utterances,
                'analysis': {
                    'business_type': analysis_result.business_type,
                    'classification_type': analysis_result.classification_type,
                    'detailed_classification': analysis_result.detail_classification,
                    'consultation_result': analysis_result.consultation_result,
                    'summary': analysis_result.summary,
                    'customer_request': analysis_result.customer_request,
                    'solution': analysis_result.solution,
                    'additional_info': analysis_result.additional_info,
                    'confidence': analysis_result.confidence
                },
                'communication_quality': {
                    'honorific_ratio': quality_result.honorific_ratio,
                    'positive_word_ratio': quality_result.positive_word_ratio,
                    'negative_word_ratio': quality_result.negative_word_ratio,
                    'euphonious_word_ratio': quality_result.euphonious_word_ratio,
                    'empathy_ratio': quality_result.empathy_ratio,
                    'apology_ratio': quality_result.apology_ratio,
                    'total_sentences': quality_result.total_sentences,
                    'customer_sentiment_early': quality_result.customer_sentiment_early,
                    'customer_sentiment_late': quality_result.customer_sentiment_late,
                    'customer_sentiment_trend': quality_result.customer_sentiment_trend,
                    'avg_response_latency': quality_result.avg_response_latency,
                    'task_ratio': quality_result.task_ratio,
                    'suggestions': quality_result.suggestions,
                    'interruption_count': quality_result.interruption_count,
                    'analysis_details': quality_result.analysis_details
                },
                'processing_time': self.performance_monitor.get_elapsed_time(),
                'timestamp': time.time()
            }
            
            # 5. 데이터베이스 저장
            self.logger.info("5단계: 데이터베이스 저장")
            self._save_to_database(integrated_result)
            
            self.logger.info(f"상담 분석 완료: {len(utterances)}개 발화, {len(integrated_result['analysis'])}개 분석 항목")
            return integrated_result
            
        except Exception as e:
            self.logger.error(f"상담 분석 중 오류 발생: {e}")
            raise
    
    def _save_to_database(self, result: Dict[str, Any]):
        """결과를 데이터베이스에 저장"""
        try:
            # 1. 상담 분석 결과 저장
            consultation_data = {
                'consultation_id': result['consultation_id'],
                'audio_path': result['audio_path'],
                'business_type': result['analysis'].get('business_type', '그 외 업무유형'),
                'classification_type': result['analysis'].get('classification_type', '상담 주제'),
                'detail_classification': result['analysis'].get('detailed_classification', '기타'),
                'consultation_result': result['analysis'].get('consultation_result', '미흡'),
                'summary': result['analysis'].get('summary', ''),
                'customer_request': result['analysis'].get('customer_request', ''),
                'solution': result['analysis'].get('solution', ''),
                'additional_info': result['analysis'].get('additional_info', ''),
                'confidence': result['analysis'].get('confidence', 0.0),
                'processing_time': result['processing_time']
            }
            
            self.db_manager.insert_consultation_analysis(consultation_data)
            
            # 2. 커뮤니케이션 품질 분석 결과 저장
            quality_data = {
                'audio_path': result['audio_path'],
                'consultation_id': result['consultation_id'],
                'honorific_ratio': result['communication_quality']['honorific_ratio'],
                'positive_word_ratio': result['communication_quality']['positive_word_ratio'],
                'negative_word_ratio': result['communication_quality']['negative_word_ratio'],
                'euphonious_word_ratio': result['communication_quality']['euphonious_word_ratio'],
                'empathy_ratio': result['communication_quality']['empathy_ratio'],
                'apology_ratio': result['communication_quality']['apology_ratio'],
                'total_sentences': result['communication_quality']['total_sentences'],
                'customer_sentiment_early': result['communication_quality']['customer_sentiment_early'],
                'customer_sentiment_late': result['communication_quality']['customer_sentiment_late'],
                'customer_sentiment_trend': result['communication_quality']['customer_sentiment_trend'],
                'avg_response_latency': result['communication_quality']['avg_response_latency'],
                'task_ratio': result['communication_quality']['task_ratio'],
                'suggestions': result['communication_quality']['suggestions'],
                'interruption_count': result['communication_quality']['interruption_count'],
                'analysis_details': result['communication_quality']['analysis_details']
            }
            
            self.db_manager.insert_communication_quality(quality_data)
            
            # 3. 발화 내용 저장
            for i, utterance in enumerate(result['utterances']):
                utterance_data = {
                    'audio_path': result['audio_path'],
                    'speaker': utterance['speaker'],
                    'start_time': utterance['start'],
                    'end_time': utterance['end'],
                    'text': utterance['text'],
                    'confidence': utterance['confidence'],
                    'sequence': i + 1,
                    'sentiment': '중립',  # 기본값
                    'profane': 0  # 기본값
                }
                self.db_manager.insert_utterance(utterance_data)
            
            self.logger.info("데이터베이스 저장 완료")
            
        except Exception as e:
            self.logger.error(f"데이터베이스 저장 중 오류: {e}")
            raise
    
    def batch_analyze(self, audio_directory: str) -> List[Dict[str, Any]]:
        """
        디렉토리 내 모든 오디오 파일을 일괄 분석
        
        Parameters
        ----------
        audio_directory : str
            오디오 파일들이 있는 디렉토리 경로
            
        Returns
        -------
        List[Dict[str, Any]]
            분석 결과 리스트
        """
        audio_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.ogg'}
        audio_files = []
        
        for file_path in Path(audio_directory).rglob('*'):
            if file_path.suffix.lower() in audio_extensions:
                audio_files.append(str(file_path))
        
        self.logger.info(f"일괄 분석 시작: {len(audio_files)}개 파일")
        
        results = []
        for i, audio_path in enumerate(audio_files, 1):
            try:
                self.logger.info(f"처리 중 ({i}/{len(audio_files)}): {audio_path}")
                result = self.analyze_consultation(audio_path)
                results.append(result)
            except Exception as e:
                self.logger.error(f"파일 처리 실패 {audio_path}: {e}")
                continue
        
        self.logger.info(f"일괄 분석 완료: {len(results)}개 성공")
        return results
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """분석 통계 요약"""
        try:
            # 데이터베이스에서 통계 조회
            stats = self.db_manager.get_analysis_statistics()
            return stats
        except Exception as e:
            self.logger.error(f"통계 조회 중 오류: {e}")
            return {}

if __name__ == "__main__":
    import time
    
    # 사용 예제
    analyzer = IntegratedAnalyzer(
        config_path="config/config_enhanced.yaml",
        diarization_token=os.getenv("HUGGINGFACE_TOKEN")
    )
    
    # 단일 파일 분석
    result = analyzer.analyze_consultation("audio/40186.wav")
    print("분석 완료:", result['consultation_id'])
    
    # 일괄 분석
    # results = analyzer.batch_analyze("audio/")
    # print(f"일괄 분석 완료: {len(results)}개 파일") 