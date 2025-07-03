# Standard library imports
import os
import asyncio
from fastapi import FastAPI, HTTPException, File, Form, UploadFile
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager
# PyTorch 2.x + NeMo 1.17 호환성 임시 해결
import torch
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="torch")
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")

# NeMo 호환성 설정
if hasattr(torch, '_C') and hasattr(torch._C, '_set_print_stack_traces_on_fatal_signal'):
    torch._C._set_print_stack_traces_on_fatal_signal(False)

# CUDA 메모리 최적화
if torch.cuda.is_available():
    torch.backends.cudnn.benchmark = True
    torch.backends.cudnn.deterministic = False
    # 메모리 할당 최적화
    torch.cuda.empty_cache()



# Related third-party imports
from omegaconf import OmegaConf

# NeMo import (완전 지원 - Fallback 절대 불가)
from nemo.collections.asr.models.msdd_models import NeuralDiarizer
print("✅ NeMo NeuralDiarizer imported successfully")

# Local imports
from src.audio.utils import Formatter
from src.audio.metrics import SilenceStats
from src.audio.error import DialogueDetecting
from src.audio.alignment import ForcedAligner
from src.audio.effect import DemucsVocalSeparator
from src.audio.preprocessing import SpeechEnhancement
from src.audio.io import SpeakerTimestampReader, TranscriptWriter
from src.audio.analysis import WordSpeakerMapper, SentenceSpeakerMapper, Audio
from src.audio.advanced_processing import AdvancedTranscriber
from src.audio.advanced_punctuation import AdvancedPunctuationRestorer
from src.text.utils import Annotator
from src.text.llm import LLMOrchestrator, LLMResultHandler
from src.text.advanced_analysis import AdvancedAnalysisManager
from src.utils.utils import Cleaner, Watcher
from src.db.multi_database_manager import MultiDatabaseManager
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from src.text.korean_models import KoreanModels

from src.integrated_analyzer_advanced import AdvancedIntegratedAnalyzer

# FastAPI 앱 생성
app = FastAPI(title="Callytics API", version="1.0.0")

# 전역 변수로 처리 상태 관리
processing_status = {
    "is_processing": False,
    "current_file": None,
    "total_processed": 0,
    "errors": []
}

# PostgreSQL 우선 데이터베이스 매니저 전역 인스턴스
db_manager = MultiDatabaseManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 초기화
    print("🚀 Callytics API 서버 시작")
    print("🗄️ PostgreSQL 우선 데이터베이스 연결 시도...")
    
    # PostgreSQL 연결 상태 확인
    if db_manager.is_postgresql_available():
        print("✅ PostgreSQL 연결 성공")
    else:
        print("❌ PostgreSQL 연결 실패 - 애플리케이션을 종료합니다")
        raise RuntimeError("PostgreSQL 연결이 필수입니다")
    
    yield
    # 종료 시 정리
    print("🛑 Callytics API 서버 종료")
    await db_manager.close_async()

app = FastAPI(title="Callytics API", version="1.0.0", lifespan=lifespan)

# 공통 엔드포인트 사용
from src.utils.common_endpoints import get_common_endpoints

common_endpoints = get_common_endpoints("callytics-api", "1.0.0")

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    try:
        # 추가 체크 항목 구성
        additional_checks = {
            "api_keys_configured": {
                "openai": bool(os.getenv("OPENAI_API_KEY")),
                "azure": bool(os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT")),
                "huggingface": bool(os.getenv("HUGGINGFACE_TOKEN"))
            },
            "database_accessible": db_manager.is_postgresql_available(),
            "database_type": "postgresql",
            "audio_directory_accessible": os.path.exists("/app/audio"),
            "processing_status": processing_status
        }
        
        return await common_endpoints.health_check(additional_checks)
    except Exception as e:
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e)
        }, status_code=500)

@app.get("/metrics")
async def get_metrics():
    """메트릭 엔드포인트 (Prometheus용)"""
    try:
        # 추가 메트릭 구성
        additional_metrics = {
            "processing_status": processing_status
        }
        
        return await common_endpoints.get_metrics(additional_metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Callytics API 서버가 실행 중입니다",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/docs"
        }
    }

@app.post("/analyze")
async def analyze_audio(
    file: UploadFile = File(...),
    consultation_id: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None)
):
    """오디오 파일 분석 API"""
    try:
        # 파일 저장
        file_path = f"temp/{file.filename}"
        os.makedirs("temp", exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 메타데이터 파싱
        parsed_metadata = None
        if metadata:
            try:
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                logger.warning("메타데이터 JSON 파싱 실패")
        
        # 고성능 통합 분석기 사용
        analyzer = AdvancedIntegratedAnalyzer(
            config_path="config/config.yaml",
            enable_cache=True,
            enable_parallel=True,
            enable_async=True,
            max_workers=4
        )
        
        # 분석 실행
        result = await analyzer.analyze_audio_comprehensive(file_path)
        
        # 임시 파일 정리
        try:
            os.remove(file_path)
        except:
            pass
        
        return result
        
    except Exception as e:
        logger.error(f"분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def main(audio_file_path: str):
    """
    Process an audio file to perform diarization, transcription, punctuation restoration,
    and speaker role classification.

    Parameters
    ----------
    audio_file_path : str
        The path to the input audio file to be processed.

    Returns
    -------
    None
    """
    # Paths - 고유한 임시 디렉토리 생성
    import uuid
    import time
    unique_id = f"{int(time.time())}_{str(uuid.uuid4())[:8]}"
    temp_dir = f"/app/temp/session_{unique_id}"
    os.makedirs(temp_dir, exist_ok=True)
    
    config_nemo = "config/nemo/diar_infer_telephonic.yaml"
    manifest_path = os.path.join(temp_dir, "manifest.json")
    rttm_file_path = os.path.join(temp_dir, "pred_rttms", "mono_file.rttm")
    transcript_output_path = os.path.join(temp_dir, "output.txt")
    srt_output_path = os.path.join(temp_dir, "output.srt")
    config_path = "config/config.yaml"
    prompt_path = "config/prompt.yaml"
    # PostgreSQL 전용 설정 - SQLite 관련 변수 제거
    db_topic_fetch_path = "src/db/sql/TopicFetch.sql"
    db_topic_insert_path = "src/db/sql/TopicInsert.sql"
    db_audio_properties_insert_path = "src/db/sql/AudioPropertiesInsert.sql"
    db_utterance_insert_path = "src/db/sql/UtteranceInsert.sql"

    # Configuration
    config = OmegaConf.load(config_path)
    device = config.runtime.device
    compute_type = config.runtime.compute_type
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = config.runtime.cuda_alloc_conf

    # Step 0: Audio Normalization (FFmpeg 기반)
    normalized_audio_path = os.path.join(temp_dir, "normalized.wav")
    try:
        import subprocess
        print(f"🔄 오디오 파일 정규화 시작: {audio_file_path}")
        
        # FFmpeg로 오디오를 표준 WAV 형식으로 변환
        cmd = [
            'ffmpeg', '-i', audio_file_path,
            '-acodec', 'pcm_s16le',  # 16비트 PCM
            '-ar', '16000',          # 16kHz 샘플링
            '-ac', '1',              # 모노 채널
            '-y', normalized_audio_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ 오디오 정규화 완료: {normalized_audio_path}")
            # 정규화된 파일을 사용
            audio_file_path = normalized_audio_path
        else:
            print(f"⚠️ 오디오 정규화 실패, 원본 사용: {result.stderr}")
            
    except Exception as e:
        print(f"⚠️ 오디오 정규화 오류, 원본 사용: {e}")

    # Initialize Classes
    dialogue_detector = DialogueDetecting(delete_original=True)
    enhancer = SpeechEnhancement(config_path=config_path, output_dir=temp_dir)
    separator = DemucsVocalSeparator()
    processor = AudioProcessor(audio_path=audio_file_path, temp_dir=temp_dir)
    transcriber = Transcriber(device=device, compute_type=compute_type)
    aligner = ForcedAligner(device=device)
    llm_handler = LLMOrchestrator(config_path=config_path, prompt_config_path=prompt_path, model_id="openai")
    llm_result_handler = LLMResultHandler()
    cleaner = Cleaner()
    formatter = Formatter()
    db = MultiDatabaseManager()
    audio_feature_extractor = Audio(audio_file_path)

    # Step 1: Detect Dialogue
    try:
        print("🔍 대화 감지 시작...")
        has_dialogue = dialogue_detector.process(audio_file_path)
        print(f"🔍 대화 감지 결과: {has_dialogue}")
        if not has_dialogue:
            print("⚠️ 대화가 감지되지 않아 처리를 중단합니다.")
            return
    except Exception as e:
        print(f"❌ 대화 감지 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 2: Speech Enhancement
    audio_path = enhancer.enhance_audio(
        input_path=audio_file_path,
        output_path=os.path.join(temp_dir, "enhanced.wav"),
        noise_threshold=0.0001,
        verbose=True
    )

    # Step 3: Vocal Separation
    vocal_path = separator.separate_vocals(audio_file=audio_path, output_dir=temp_dir)

    # Step 4: Transcription
    transcript, info = transcriber.transcribe(audio_path=vocal_path)
    detected_language = info["language"]
    whisper_word_timestamps = info.get("word_timestamps", [])  # faster-whisper word timestamps 추출

    # Step 5: Forced Alignment (faster-whisper word_timestamps 우선 활용)
    word_timestamps = aligner.align(
        audio_path=vocal_path,
        transcript=transcript,
        language=detected_language,
        whisper_word_timestamps=whisper_word_timestamps  # faster-whisper 결과 전달
    )

    # Step 6: Diarization
    processor.audio_path = vocal_path
    mono_audio_path = processor.convert_to_mono()
    processor.audio_path = mono_audio_path
    processor.create_manifest(manifest_path)
    
    # NeuralDiarizer를 사용한 화자 분리 (fallback 모드 지원)
    if NeuralDiarizer is None:
        print("Warning: NeuralDiarizer is not available. Using fallback diarization.")
        # NeuralDiarizer를 사용한 화자 분리 (완전 지원)
        cfg = OmegaConf.load(config_nemo)
        cfg.diarizer.manifest_filepath = manifest_path
        cfg.diarizer.out_dir = temp_dir
        msdd_model = NeuralDiarizer(cfg=cfg)
        msdd_model.diarize()

    # Step 7: Processing Transcript
    # Step 7.1: Speaker Timestamps
    speaker_reader = SpeakerTimestampReader(rttm_path=rttm_file_path)
    speaker_ts = speaker_reader.read_speaker_timestamps()

    # Step 7.2: Mapping Words
    word_speaker_mapper = WordSpeakerMapper(word_timestamps, speaker_ts)
    wsm = word_speaker_mapper.get_words_speaker_mapping()

    # Step 7.3: Punctuation Restoration
    punct_restorer = PunctuationRestorer(language=detected_language)
    wsm = punct_restorer.restore_punctuation(wsm)
    word_speaker_mapper.word_speaker_mapping = wsm
    word_speaker_mapper.realign_with_punctuation()
    wsm = word_speaker_mapper.word_speaker_mapping

    # Step 7.4: Mapping Sentences
    sentence_mapper = SentenceSpeakerMapper()
    ssm = sentence_mapper.get_sentences_speaker_mapping(wsm)

    # Step 7.5: 언어 감지 및 검증
    # API 기반 한국어 모델 초기화
    korean_models = KoreanModels(device=device)
    
    # 전체 텍스트를 합쳐서 언어 감지
    full_text = " ".join([utterance["text"] for utterance in ssm])
    
    if not korean_models.is_korean_content(full_text):
        print("⚠️ 경고: 한국어가 아닌 오디오가 감지되었습니다.")
        print("📝 감지된 언어로 처리하거나 한국어 오디오를 사용해주세요.")
        # 한국어가 아닌 경우에도 계속 진행하되 경고 표시
        language_warning = True
    else:
        print("✅ 한국어 오디오가 확인되었습니다.")
        language_warning = False

    # Step 8 (Optional): Write Transcript and SRT Files
    writer = TranscriptWriter()
    writer.write_transcript(ssm, transcript_output_path)
    writer.write_srt(ssm, srt_output_path)
    
    # JSON 대본 출력 경로 설정
    json_output_path = os.path.join(temp_dir, "transcript.json")
    comprehensive_json_path = os.path.join(temp_dir, "analysis_complete.json")

    # Step 9: Classify Speaker Roles
    speaker_roles = await llm_handler.generate("Classification", ssm)

    # Step 9.1: LLM results validation
    ssm = llm_result_handler.validate_and_fallback(speaker_roles, ssm)
    llm_result_handler.log_result(ssm, speaker_roles)

    # Step 10: Sentiment Analysis (API 기반 배치 처리)
    ssm_with_indices = formatter.add_indices_to_ssm(ssm)
    annotator = Annotator(ssm_with_indices)
    
    # API를 통해 배치로 감정 분석 수행
    texts_for_sentiment = [utterance["text"] for utterance in ssm]
    sentiment_results = await korean_models.analyze_sentiment_batch(texts_for_sentiment)
    
    # 결과를 SSM에 적용
    for i, utterance in enumerate(ssm):
        utterance["sentiment"] = sentiment_results[i]
    
    # Step 11: Profanity Word Detection (API 기반 배치 처리)
    profanity_results = await korean_models.detect_profanity_batch(texts_for_sentiment)
    
    # 결과를 SSM에 적용
    for i, utterance in enumerate(ssm):
        utterance["profane"] = profanity_results[i]

    # Step 12: Summary
    summary_result = await llm_handler.generate("Summary", user_input=ssm)
    annotator.add_summary(summary_result)

    # Step 13: Conflict Detection
    conflict_result = await llm_handler.generate("ConflictDetection", user_input=ssm)
    annotator.add_conflict(conflict_result)

    # Step 14: Topic Detection
    topics = db.fetch(db_topic_fetch_path)
    topic_result = await llm_handler.generate(
        "TopicDetection",
        user_input=ssm,
        system_input=topics
    )
    annotator.add_topic(topic_result)

    # Step 15: Complaint Analysis
    complaint_result = await llm_handler.generate("ComplaintAnalysis", user_input=ssm)
    annotator.add_complaint(complaint_result)

    # Step 16: Action Items
    action_result = await llm_handler.generate("ActionItems", user_input=ssm)
    annotator.add_action_items(action_result)

    # Step 17: Quality Assessment
    quality_result = await llm_handler.generate("QualityAssessment", user_input=ssm)
    annotator.add_quality_assessment(quality_result)

    # Step 17.5: Communication Quality Analysis (새로운 LLM 정성 지표)
    try:
        print("📊 커뮤니케이션 품질 분석 시작...")
        quality_analyzer = CommunicationQualityAnalyzer()
        quality_analysis_result = await quality_analyzer.analyze_communication_quality(ssm)
        
        print(f"📊 커뮤니케이션 품질 분석 완료:")
        print(f"   - 문제 해결 제안 점수: {quality_analysis_result.suggestions}")
        print(f"   - 대화 가로채기 횟수: {quality_analysis_result.interruption_count}회")
        print(f"   - 존댓말 비율: {quality_analysis_result.honorific_ratio:.2f}")
        print(f"   - 긍정어 비율: {quality_analysis_result.positive_word_ratio:.2f}")
        
    except Exception as e:
        print(f"❌ 커뮤니케이션 품질 분석 실패: {e}")
        quality_analysis_result = None

    # Step 18: Generate JSON Outputs
    # Step 18.1: Basic JSON transcript with analysis
    writer.write_json(ssm, json_output_path, include_analysis=True)
    
    # Step 18.2: Export complete analysis results
    analysis_json_path = os.path.join(temp_dir, "analysis_results.json")
    annotator.export_to_json(analysis_json_path)
    
    # Step 18.3: Extract Audio Properties
    audio_properties = audio_feature_extractor.extract_properties()
    
    # Step 18.4: Generate comprehensive JSON report
    analysis_summary = annotator.get_analysis_summary()
    writer.write_comprehensive_json(
        ssm, 
        comprehensive_json_path,
        analysis_results=analysis_summary,
        audio_properties=audio_properties
    )

    # Step 19: Database Operations
    # Step 19.1: Insert Audio Properties (기존 SQL 파일 사용)
    try:
        # Audio 클래스의 extract_properties() 메소드 사용
        audio_properties = audio_feature_extractor.extract_properties()
        
        # properties() 메소드로 상세 정보 추출
        (
            name,
            extension,
            path,
            sample_rate,
            min_freq,
            max_freq,
            bit_depth,
            channels,
            duration,
            rms_loudness,
            final_features
        ) = audio_feature_extractor.properties()
        
        # 기본값 설정
        summary = "오디오 분석 완료"
        conflict_flag = 0
        silence_value = 0.0
        detected_topic = "일반"
        
        # Topic ID 가져오기 (기본값 1 사용)
        topic_id = 1
        
        # AudioPropertiesInsert.sql에 맞는 파라미터 구성 (33개 파라미터 필요)
        params = (
            path,           # 1. file_path
            name,           # 2. file_name
            duration,       # 3. duration
            sample_rate,    # 4. sample_rate
            channels,       # 5. channels
            topic_id,       # 6. topic_id
            extension,      # 7. extension
            min_freq,       # 8. min_frequency
            max_freq,       # 9. max_frequency
            bit_depth if bit_depth is not None else 16,  # 10. bit_depth
            rms_loudness,   # 11. rms_loudness
            final_features.get("ZeroCrossingRate", 0.0),  # 12. zero_crossing_rate
            final_features.get("SpectralCentroid", 0.0),  # 13. spectral_centroid
            final_features.get("EQ_20_250_Hz", 0.0),      # 14. eq_20_250_hz
            final_features.get("EQ_250_2000_Hz", 0.0),    # 15. eq_250_2000_hz
            final_features.get("EQ_2000_6000_Hz", 0.0),   # 16. eq_2000_6000_hz
            final_features.get("EQ_6000_20000_Hz", 0.0),  # 17. eq_6000_20000_hz
            final_features.get("MFCC_1", 0.0),            # 18. mfcc_1
            final_features.get("MFCC_2", 0.0),            # 19. mfcc_2
            final_features.get("MFCC_3", 0.0),            # 20. mfcc_3
            final_features.get("MFCC_4", 0.0),            # 21. mfcc_4
            final_features.get("MFCC_5", 0.0),            # 22. mfcc_5
            final_features.get("MFCC_6", 0.0),            # 23. mfcc_6
            final_features.get("MFCC_7", 0.0),            # 24. mfcc_7
            final_features.get("MFCC_8", 0.0),            # 25. mfcc_8
            final_features.get("MFCC_9", 0.0),            # 26. mfcc_9
            final_features.get("MFCC_10", 0.0),           # 27. mfcc_10
            final_features.get("MFCC_11", 0.0),           # 28. mfcc_11
            final_features.get("MFCC_12", 0.0),           # 29. mfcc_12
            final_features.get("MFCC_13", 0.0),           # 30. mfcc_13
            summary,        # 31. summary
            conflict_flag,  # 32. conflict_flag
            silence_value   # 33. silence_value
            # 34. created_at은 SQL에서 datetime('now')로 자동 생성됨
        )
        
        last_id = db.insert(db_audio_properties_insert_path, params)
        print(f"✅ 오디오 속성 DB 저장 완료: ID {last_id}")
        
    except Exception as e:
        print(f"❌ 오디오 속성 DB 저장 실패: {e}")
        last_id = None

    # Step 19.2: Insert Utterances (기존 SQL 파일 사용)
    if last_id is not None:
        try:
            for i, utterance in enumerate(ssm):
                # UtteranceInsert.sql에 맞는 파라미터 구성
                utterance_params = (
                    last_id,  # audio_properties_id
                    utterance["speaker"],  # speaker
                    utterance["start_time"] / 1000.0,  # start_time (초 단위) - 필드명 수정
                    utterance["end_time"] / 1000.0,  # end_time (초 단위) - 필드명 수정
                    utterance["text"],  # text
                    1.0,  # confidence (기본값)
                    i + 1,  # sequence
                    utterance.get("sentiment", "중립"),  # sentiment
                    1 if utterance.get("profane", False) else 0  # profane (0/1)
                )
                db.insert(db_utterance_insert_path, utterance_params)
            
            print(f"✅ 발화 데이터 DB 저장 완료: {len(ssm)}개 발화")
            
        except Exception as e:
            print(f"❌ 발화 데이터 DB 저장 실패: {e}")
    else:
        print("⚠️ File ID가 없어 발화 데이터 저장을 건너뜁니다.")

    # Step 19.3: Insert Consultation Analysis (LLM 분석 결과 저장)
    if last_id is not None:
        try:
            # 분석 결과에서 필요한 정보 추출
            analysis_summary = annotator.get_analysis_summary()
            global_analysis = analysis_summary.get("global_analysis", {})
            
            # 구조화된 분석 결과 처리
            summary_data = global_analysis.get("summary", {})
            conflict_data = global_analysis.get("conflict", {})
            topic_data = global_analysis.get("topic", {})
            complaint_data = global_analysis.get("complaint", {})
            quality_data = global_analysis.get("quality_assessment", {})
            
            # 주제 분류 결과 처리 (개선된 구조)
            if isinstance(topic_data, dict):
                primary_topic = topic_data.get("primary_topic", "기타")
                topic_confidence = topic_data.get("confidence", 0.7)
            else:
                primary_topic = str(topic_data) if topic_data else "기타"
                topic_confidence = 0.7
            
            # 주제에 따른 업무 유형 매핑 (확장된 매핑)
            business_type = "OTHER"  # 기본값
            topic_mapping = {
                "요금": "FEE_INFO", "요금제": "PLAN_CHANGE", "납부": "FEE_PAYMENT",
                "할인": "SELECTIVE_DISCOUNT", "결제": "PAYMENT_METHOD_CHANGE",
                "부가서비스": "ADDITIONAL_SERVICE", "소액결제": "MICRO_PAYMENT",
                "정지": "PHONE_SUSPENSION_LOSS_DAMAGE", "분실": "PHONE_SUSPENSION_LOSS_DAMAGE",
                "기기": "DEVICE_CHANGE", "명의": "NAME_NUMBER_USIM_CANCEL",
                "번호": "NAME_NUMBER_USIM_CANCEL", "해지": "NAME_NUMBER_USIM_CANCEL"
            }
            
            for keyword, biz_type in topic_mapping.items():
                if keyword in primary_topic:
                    business_type = biz_type
                    break
            
            # 갈등 분석 결과 처리 (개선된 구조)
            if isinstance(conflict_data, dict):
                conflict_detected = conflict_data.get("conflict_detected", False)
                conflict_level = conflict_data.get("conflict_level", "낮음")
            else:
                conflict_detected = bool(conflict_data)
                conflict_level = "보통" if conflict_detected else "낮음"
            
            consultation_content = "COMPLAINT" if conflict_detected else "GENERAL_INQUIRY"
            
            # 품질 평가 결과 처리 (개선된 구조)
            if isinstance(quality_data, dict):
                satisfaction_score = quality_data.get("customer_satisfaction_predicted", 3)
                overall_score = quality_data.get("overall_score", 3)
            else:
                satisfaction_score = 3
                overall_score = 3
            
            # 상담 결과 결정 로직 개선
            if overall_score >= 4:
                consultation_result = "SATISFACTION"
            elif overall_score >= 3:
                consultation_result = "INSUFFICIENT" 
            else:
                consultation_result = "UNSOLVABLE"
            
            # 요약 데이터 처리 (개선된 구조)
            if isinstance(summary_data, dict):
                summary_text = summary_data.get("summary", "")
                customer_inquiry = summary_data.get("customer_inquiry", "")
                agent_response = summary_data.get("agent_response", "")
            else:
                summary_text = str(summary_data) if summary_data else ""
                customer_inquiry = ""
                agent_response = ""
            
            # 액션 아이템 처리
            action_items = global_analysis.get("action_items", {})
            if isinstance(action_items, dict):
                immediate_actions = action_items.get("immediate_actions", [])
                follow_up_actions = action_items.get("follow_up_actions", [])
                customer_request = "; ".join(immediate_actions[:3]) if immediate_actions else customer_inquiry
                solution = "; ".join(follow_up_actions[:3]) if follow_up_actions else agent_response
            else:
                customer_request = customer_inquiry
                solution = agent_response
            
            # 불만 분석 추가 정보
            if isinstance(complaint_data, dict):
                additional_info = complaint_data.get("department_recommendation", "")
                if not additional_info:
                    additional_info = f"갈등수준: {conflict_level}, 신뢰도: {topic_confidence:.2f}"
            else:
                additional_info = f"갈등수준: {conflict_level}, 신뢰도: {topic_confidence:.2f}"
            
            # ConsultationAnalysisInsert.sql 파라미터 구성
            consultation_params = (
                last_id,  # audio_properties_id
                business_type,  # business_type
                "CONSULTATION_CONTENT",  # classification_type
                consultation_content,  # detail_classification
                consultation_result,  # consultation_result
                summary_text or "상담 분석 완료",  # summary
                customer_request or "고객 요청사항 없음",  # customer_request
                solution or "해결방안 제시됨",  # solution
                additional_info,  # additional_info
                max(topic_confidence, 0.5),  # confidence
                0.0   # processing_time
            )
            
            # ConsultationAnalysisInsert.sql 파일 경로
            db_consultation_insert_path = os.path.join("src", "db", "sql", "ConsultationAnalysisInsert.sql")
            
            db.insert(db_consultation_insert_path, consultation_params)
            print(f"✅ 상담 분석 결과 DB 저장 완료 (업무유형: {business_type}, 갈등: {conflict_detected})")
            
        except Exception as e:
            print(f"❌ 상담 분석 결과 DB 저장 실패: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("⚠️ File ID가 없어 상담 분석 결과 저장을 건너뜁니다.")

    # Step 19.4: Insert Communication Quality (새로운 LLM 지표 저장)
    if last_id is not None and quality_analysis_result:
        try:
            print("💾 커뮤니케이션 품질 분석 결과 DB 저장 시작...")
            
            # PostgreSQL 전용 저장
            await db_manager.save_communication_quality_async(
                audio_file_id=last_id,
                consultation_id=f"CONSULT_{last_id}",
                quality_metrics={
                    'honorific_ratio': quality_analysis_result.honorific_ratio or 0.0,
                    'positive_word_ratio': quality_analysis_result.positive_word_ratio or 0.0,
                    'negative_word_ratio': quality_analysis_result.negative_word_ratio or 0.0,
                    'euphonious_word_ratio': quality_analysis_result.euphonious_word_ratio or 0.0,
                    'empathy_ratio': quality_analysis_result.empathy_ratio or 0.0,
                    'apology_ratio': quality_analysis_result.apology_ratio or 0.0,
                    'total_sentences': quality_analysis_result.total_sentences or 0,
                    'customer_sentiment_early': quality_analysis_result.customer_sentiment_early or 0.0,
                    'customer_sentiment_late': quality_analysis_result.customer_sentiment_late or 0.0,
                    'customer_sentiment_trend': quality_analysis_result.customer_sentiment_trend or 0.0,
                    'avg_response_latency': quality_analysis_result.avg_response_latency or 0.0,
                    'task_ratio': quality_analysis_result.task_ratio or 0.0,
                    'suggestions': quality_analysis_result.suggestions or 0.0,
                    'interruption_count': quality_analysis_result.interruption_count or 0,
                    'silence_ratio': quality_analysis_result.silence_ratio or 0.0,
                    'talk_ratio': quality_analysis_result.talk_ratio or 0.0,
                    'analysis_details': quality_analysis_result.analysis_details or {}
                }
            )
            print("✅ PostgreSQL에 커뮤니케이션 품질 분석 결과 저장 완료")
            print(f"   - 새로운 LLM 지표: suggestions={quality_analysis_result.suggestions}, interruption_count={quality_analysis_result.interruption_count}")
            
        except Exception as e:
            print(f"❌ 커뮤니케이션 품질 분석 결과 DB 저장 실패: {e}")
            import traceback
            traceback.print_exc()
    else:
        if last_id is None:
            print("⚠️ File ID가 없어 커뮤니케이션 품질 분석 결과 저장을 건너뜁니다.")
        if not quality_analysis_result:
            print("⚠️ 품질 분석 결과가 없어 저장을 건너뜁니다.")

    # Step 20: Cleanup
    cleaner.cleanup_temp_files(temp_dir)

    print(f"✅ 오디오 처리 완료: {audio_file_path}")
    print(f"📊 처리된 발화 수: {len(ssm)}")
    print(f"🗣️ 감지된 화자 수: {len(set(utterance['speaker'] for utterance in ssm))}")
    print(f"📝 감지된 언어: {detected_language}")
    
    # 새로운 LLM 지표 결과 출력
    if quality_analysis_result:
        print(f"🎯 커뮤니케이션 품질 분석 결과:")
        print(f"   - 문제 해결 제안 점수: {quality_analysis_result.suggestions:.2f}")
        print(f"   - 대화 가로채기 횟수: {quality_analysis_result.interruption_count}회")
        print(f"   - 존댓말 비율: {quality_analysis_result.honorific_ratio:.2f}")
        print(f"   - 긍정어 비율: {quality_analysis_result.positive_word_ratio:.2f}")
        print(f"   - 완곡 표현 비율: {quality_analysis_result.euphonious_word_ratio:.2f}")
        print(f"   - 사과 표현 비율: {quality_analysis_result.apology_ratio:.2f}")
        print(f"   - 평균 응답 지연 시간: {quality_analysis_result.avg_response_latency:.2f}초")
        print(f"   - 침묵 비율: {quality_analysis_result.silence_ratio:.2f}")
        print(f"   - 발화 시간 비율: {quality_analysis_result.talk_ratio:.2f}")
        print(f"   - 전체 분석 지표: 15개 (기존 11개 + 새로운 지표 4개)")
    
    print(f"📄 생성된 출력 파일:")
    print(f"   - 텍스트 대본: {transcript_output_path}")
    print(f"   - SRT 자막: {srt_output_path}")
    print(f"   - JSON 대본: {json_output_path}")
    print(f"   - 분석 결과: {analysis_json_path}")
    print(f"   - 종합 보고서: {comprehensive_json_path}")
    if language_warning:
        print("⚠️ 언어 경고: 한국어가 아닌 콘텐츠가 포함되어 있습니다.")


async def process(path: str):
    """
    Process a single audio file asynchronously.

    Parameters
    ----------
    path : str
        Path to the audio file to process.

    Returns
    -------
    None
    """
    success = False
    try:
        # 처리 상태 업데이트
        processing_status["is_processing"] = True
        processing_status["current_file"] = path
        processing_status["errors"] = []
        
        print(f"🎵 오디오 파일 처리 시작: {path}")
        await main(path)
        print(f"✅ 오디오 파일 처리 완료: {path}")
        
        # 처리 성공 표시
        success = True
        
        # 처리 완료 상태 업데이트
        processing_status["total_processed"] += 1
        processing_status["current_file"] = None
        
    except Exception as e:
        print(f"❌ 오디오 파일 처리 실패: {path}")
        print(f"오류: {e}")
        print(f"📁 실패한 파일 보존: {path}")
        
        # 오류 상태 업데이트
        processing_status["errors"].append({
            "file": path,
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time()
        })
        
    finally:
        # 성공한 경우에만 파일 삭제
        if success:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"🗑️ 처리 완료된 오디오 파일 삭제: {path}")
                else:
                    print(f"⚠️ 삭제할 파일이 없습니다: {path}")
            except Exception as e:
                print(f"❌ 파일 삭제 실패: {path} - {e}")
        
        # 처리 완료
        processing_status["is_processing"] = False


def watch_and_process():
    """
    Watch for new audio files and process them automatically.
    """
    print("🔍 오디오 파일 감시 시작...")
    
    # 감시할 디렉토리 설정
    watch_directories = [
        "/app/audio",
        "/app/.temp"
    ]
    
    # 파일 핸들러 클래스 정의
    class FileHandler(FileSystemEventHandler):
        def __init__(self, callback):
            self.callback = callback
            self.processing_files = set()
        
        def on_created(self, event):
            if not event.is_directory:
                self._handle_file(event.src_path)
        
        def on_moved(self, event):
            if not event.is_directory:
                self._handle_file(event.dest_path)
        
        def _handle_file(self, file_path):
            # 이미 처리 중인 파일인지 확인
            if file_path in self.processing_files:
                return
            
            # 오디오 파일 확장자 확인
            audio_extensions = {'.wav', '.mp3', '.flac', '.m4a', '.aac', '.ogg'}
            if any(file_path.lower().endswith(ext) for ext in audio_extensions):
                print(f"🎵 새로운 오디오 파일 감지: {file_path}")
                self.processing_files.add(file_path)
                
                # 별도 스레드에서 동기 처리
                import threading
                thread = threading.Thread(target=self._process_file, args=(file_path,))
                thread.daemon = True
                thread.start()
        
        def _process_file(self, file_path):
            try:
                # 동기 방식으로 처리
                asyncio.run(self.callback(file_path))
            finally:
                # 처리 완료 후 파일 목록에서 제거
                self.processing_files.discard(file_path)
    
    # 파일 핸들러 생성
    handler = FileHandler(process)
    
    # Observer 설정 및 시작
    observer = Observer()
    for directory in watch_directories:
        if os.path.exists(directory):
            observer.schedule(handler, directory, recursive=False)
            print(f"📁 디렉토리 감시 시작: {directory}")
        else:
            print(f"⚠️ 디렉토리가 존재하지 않습니다: {directory}")
    
    observer.start()
    
    try:
        print("🔄 파일 감시 중... (Ctrl+C로 종료)")
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 파일 감시 중지...")
        observer.stop()
    
    observer.join()
    print("✅ 파일 감시 종료")


if __name__ == "__main__":
    import sys
    import threading
    
    if len(sys.argv) > 1:
        # 파일 경로가 제공된 경우 해당 파일만 처리
        file_path = sys.argv[1]
        asyncio.run(process(file_path))
    else:
        # FastAPI 서버와 파일 감시를 동시에 실행
        def run_file_watcher():
            """별도 스레드에서 파일 감시 실행"""
            watch_and_process()
        
        # 파일 감시 스레드 시작
        watcher_thread = threading.Thread(target=run_file_watcher, daemon=True)
        watcher_thread.start()
        
        # FastAPI 서버 시작
        print("🚀 Callytics API 서버 시작...")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=True
        )