# Standard library imports
import os
import json
import asyncio
import time
import threading
from typing import Dict, List, Any, Optional
from pathlib import Path

# Local imports
from src.audio.preprocessing import AudioPreprocessor
from src.audio.error import AdvancedDialogueDetecting
from src.audio.effect import AdvancedDemucsVocalSeparator
from src.audio.advanced_processing import AdvancedTranscriber
from src.audio.advanced_punctuation import AdvancedPunctuationRestorer
from src.text.advanced_analysis import AdvancedAnalysisManager, analyze_communication_quality_with_trend
from src.db.advanced_manager import AdvancedDatabaseManager


class AdvancedIntegratedAnalyzer:
    """
    고성능 통합 분석기
    모든 개선사항을 통합한 최종 파이프라인
    """
    
    def __init__(self, 
                 config_path: str = "config/config.yaml",
                 enable_cache: bool = True,
                 enable_parallel: bool = True,
                 enable_async: bool = True,
                 max_workers: int = 4):
        """
        AdvancedIntegratedAnalyzer 초기화
        
        Parameters
        ----------
        config_path : str
            설정 파일 경로
        enable_cache : bool
            캐시 활성화 여부
        enable_parallel : bool
            병렬 처리 활성화 여부
        enable_async : bool
            비동기 처리 활성화 여부
        max_workers : int
            최대 워커 수
        """
        self.config_path = config_path
        self.enable_cache = enable_cache
        self.enable_parallel = enable_parallel
        self.enable_async = enable_async
        self.max_workers = max_workers
        
        # 고성능 컴포넌트 초기화
        self.audio_preprocessor = AudioPreprocessor(
            max_workers=max_workers,
            cache_dir="/app/.cache/audio"
        )
        
        self.dialogue_detector = AdvancedDialogueDetecting(
            max_workers=max_workers,
            enable_parallel=enable_parallel
        )
        
        self.vocal_separator = AdvancedDemucsVocalSeparator(
            enable_cache=enable_cache,
            voice_detection_threshold=0.3
        )
        
        self.transcriber = AdvancedTranscriber(
            cache_dir="/app/.cache/stt",
            max_workers=max_workers,
            enable_cache=enable_cache,
            retry_attempts=3
        )
        
        self.punctuation_restorer = AdvancedPunctuationRestorer(
            cache_dir="/app/.cache/punctuation",
            enable_cache=enable_cache,
            max_batch_size=100
        )
        
        self.analysis_manager = AdvancedAnalysisManager(
            config_path=config_path,
            cache_dir="/app/.cache/analysis",
            max_workers=max_workers,
            enable_cache=enable_cache,
            enable_parallel=enable_parallel
        )
        
        self.db_manager = AdvancedDatabaseManager(
            config_path=config_path,
            max_workers=max_workers,
            batch_size=100,
            enable_async=enable_async,
            enable_recovery=True
        )
        
        # 성능 모니터링
        self.performance_stats = {
            "total_analyses": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "avg_processing_time": 0.0,
            "stage_times": {
                "preprocessing": 0.0,
                "dialogue_detection": 0.0,
                "vocal_separation": 0.0,
                "transcription": 0.0,
                "punctuation": 0.0,
                "analysis": 0.0,
                "database": 0.0
            }
        }
        
        print(f"✅ AdvancedIntegratedAnalyzer 초기화 완료")
    
    async def analyze_audio_comprehensive(self, audio_file: str) -> Dict[str, Any]:
        """
        종합 오디오 분석
        
        Parameters
        ----------
        audio_file : str
            분석할 오디오 파일 경로
            
        Returns
        -------
        Dict[str, Any]
            종합 분석 결과
        """
        try:
            print(f"🎯 종합 오디오 분석 시작: {audio_file}")
            overall_start_time = time.time()
            
            # 1. 오디오 전처리 (ffmpeg 병렬 처리, 임시파일 자동 정리)
            print("📊 1단계: 오디오 전처리")
            stage_start = time.time()
            
            preprocessed_files = await self.audio_preprocessor.normalize_audio_parallel(
                [audio_file], "/app/temp/preprocessed"
            )
            
            if not preprocessed_files or not preprocessed_files[0]:
                raise Exception("오디오 전처리 실패")
            
            preprocessed_file = preprocessed_files[0]
            self.performance_stats["stage_times"]["preprocessing"] = time.time() - stage_start
            
            # 2. 화자 분리 (긴 오디오 chunk 분할, 병렬 diarization, graceful degradation)
            print("🎤 2단계: 화자 분리")
            stage_start = time.time()
            
            dialogue_result = self.dialogue_detector.process(preprocessed_file)
            speakers = dialogue_result.get("speakers", set())
            segments = dialogue_result.get("segments", [])
            
            self.performance_stats["stage_times"]["dialogue_detection"] = time.time() - stage_start
            
            # 3. 보컬 분리 (분리 결과 캐싱, 불필요한 분리 생략)
            print("🎵 3단계: 보컬 분리")
            stage_start = time.time()
            
            vocal_file = self.vocal_separator.separate_vocals_advanced(
                preprocessed_file, "/app/temp/vocals"
            )
            
            self.performance_stats["stage_times"]["vocal_separation"] = time.time() - stage_start
            
            # 4. STT 처리 (STT 결과 캐싱, 실패 구간 재시도, 긴 오디오 분할 최적화)
            print("🎤 4단계: 음성 인식")
            stage_start = time.time()
            
            stt_result = self.transcriber.transcribe_advanced(vocal_file)
            transcription_segments = stt_result.get("segments", [])
            
            self.performance_stats["stage_times"]["transcription"] = time.time() - stage_start
            
            # 5. 문장 부호 복원 (batch 크기 자동 조정, fallback)
            print("🔤 5단계: 문장 부호 복원")
            stage_start = time.time()
            
            # 텍스트 추출
            texts = []
            for segment in transcription_segments:
                if segment.get("text"):
                    texts.append(segment["text"])
            
            if texts:
                restored_texts = self.punctuation_restorer.restore_punctuation_advanced(texts)
                
                # 복원된 텍스트를 세그먼트에 적용
                text_index = 0
                for segment in transcription_segments:
                    if segment.get("text") and text_index < len(restored_texts):
                        segment["text"] = restored_texts[text_index]
                        text_index += 1
            
            self.performance_stats["stage_times"]["punctuation"] = time.time() - stage_start
            
            # 6. 텍스트 분석 (분석 결과 캐싱, LLM 호출 병렬화, 품질지표 세분화)
            print("🔍 6단계: 텍스트 분석")
            stage_start = time.time()
            
            # 전체 텍스트 결합
            full_text = " ".join([segment.get("text", "") for segment in transcription_segments])
            
            # 발화 데이터 구성 (감정 추세 분석용)
            utterances_data = []
            for segment in transcription_segments:
                if segment.get("text"):
                    # 화자 식별 (간단한 규칙)
                    speaker = "고객"  # 기본값
                    if any(keyword in segment.get("text", "").lower() for keyword in ["죄송합니다", "감사합니다", "도와드리겠습니다", "확인해보겠습니다"]):
                        speaker = "상담사"
                    
                    utterances_data.append({
                        "speaker": speaker,
                        "text": segment.get("text", ""),
                        "start_time": segment.get("start", 0),
                        "end_time": segment.get("end", 0),
                        "sentiment": "중립"  # 기본값, 실제로는 감정 분석 결과 사용
                    })
            
            if full_text.strip():
                # 기존 텍스트 분석
                analysis_result = await self.analysis_manager.analyze_text_comprehensive(full_text)
                
                # 감정 추세 분석 추가
                trend_analysis = analyze_communication_quality_with_trend(utterances_data)
                
                # 결과 병합
                analysis_result.update(trend_analysis)
            else:
                analysis_result = {
                    "sentiment_analysis": {"sentiment": "중립", "confidence": 0.5},
                    "profanity_detection": {"has_profanity": False, "confidence": 0.5},
                    "speaker_classification": {"speaker_type": "고객", "confidence": 0.5},
                    "communication_quality": {
                        "overall_score": 0.5,
                        "category_scores": {
                            "politeness": 0.5,
                            "negative_expression": 0.5,
                            "empathy": 0.5,
                            "expertise": 0.5,
                            "specific_info": 0.5,
                            "punctuation": 0.5,
                            "sentiment": 0.5
                        },
                        "detailed_analysis": {
                            "politeness": {"score": 0.5, "details": {}, "examples": []},
                            "negative_expression": {"score": 0.5, "details": {}, "examples": []},
                            "empathy": {"score": 0.5, "details": {}, "examples": []},
                            "expertise": {"score": 0.5, "details": {}, "examples": []},
                            "specific_info": {"score": 0.5, "details": {}, "examples": []},
                            "punctuation": {"score": 0.5, "details": {}, "examples": []},
                            "sentiment": {
                                "score": 0.5, 
                                "details": {
                                    "positive_ratio": 0,
                                    "negative_ratio": 0,
                                    "positive_intensity": 0,
                                    "negative_intensity": 0
                                }, 
                                "examples": []
                            }
                        },
                        "recommendations": ["텍스트가 없어 분석할 수 없습니다."]
                    },
                    "customer_sentiment_early": None,
                    "customer_sentiment_late": None,
                    "customer_sentiment_trend": None
                }
            
            self.performance_stats["stage_times"]["analysis"] = time.time() - stage_start
            
            # 7. DB 저장 (bulk insert, 비동기 저장, 장애 복구 로직)
            print("💾 7단계: DB 저장")
            stage_start = time.time()
            
            # 오디오 분석 데이터 준비
            audio_analysis_data = {
                "file_path": audio_file,
                "duration": stt_result.get("end_time", 0),
                "sample_rate": 16000,
                "channels": 1,
                "transcription": full_text,
                "language": stt_result.get("language", "ko"),
                "confidence_score": stt_result.get("language_probability", 0.0)
            }
            
            # 품질 분석 데이터 준비 (통신사 상담사 수준)
            communication_quality = analysis_result.get("communication_quality", {})
            category_scores = communication_quality.get("category_scores", {})
            detailed_analysis = communication_quality.get("detailed_analysis", {})
            
            # KNU 감성 분석 결과 추출
            sentiment_analysis = detailed_analysis.get("sentiment", {})
            sentiment_details = sentiment_analysis.get("details", {})
            
            # 새로 추가한 컬럼들 추출
            honorific_ratio = analysis_result.get("honorific_ratio", 0.0)
            positive_word_ratio = analysis_result.get("positive_word_ratio", 0.0)
            negative_word_ratio = analysis_result.get("negative_word_ratio", 0.0)
            euphonious_word_ratio = analysis_result.get("euphonious_word_ratio", 0.0)
            empathy_ratio = analysis_result.get("empathy_ratio", 0.0)
            apology_ratio = analysis_result.get("apology_ratio", 0.0)
            avg_response_latency = analysis_result.get("avg_response_latency", 0.0)
            interruption_count = analysis_result.get("interruption_count", 0)
            silence_ratio = analysis_result.get("silence_ratio", 0.0)
            talk_ratio = analysis_result.get("talk_ratio", 0.0)
            
            quality_analysis_data = {
                "audio_analysis_id": 0,  # 실제로는 DB에서 가져온 ID
                "clarity_score": category_scores.get("expertise", 0.5) * 0.6 + category_scores.get("specific_info", 0.5) * 0.4,
                "politeness_score": category_scores.get("politeness", 0.5) * 0.7 + category_scores.get("negative_expression", 0.5) * 0.3,
                "empathy_score": category_scores.get("empathy", 0.5),
                "professionalism_score": category_scores.get("expertise", 0.5),
                "response_quality_score": communication_quality.get("overall_score", 0.5),
                "overall_score": communication_quality.get("overall_score", 0.5),
                "sentiment_analysis": analysis_result.get("sentiment_analysis", {}),
                "profanity_detected": analysis_result.get("profanity_detection", {}).get("has_profanity", False),
                "speaker_classification": analysis_result.get("speaker_classification", {}).get("speaker_type", "고객"),
                "detailed_quality_analysis": detailed_analysis,
                "recommendations": communication_quality.get("recommendations", []),
                # KNU 감성 분석 결과 추가
                "knu_sentiment_score": category_scores.get("sentiment", 0.5),
                "positive_word_ratio": sentiment_details.get("positive_ratio", 0),
                "negative_word_ratio": sentiment_details.get("negative_ratio", 0),
                "positive_intensity": sentiment_details.get("positive_intensity", 0),
                "negative_intensity": sentiment_details.get("negative_intensity", 0),
                "sentiment_examples": sentiment_analysis.get("examples", []),
                # 새로 추가한 컬럼들
                "honorific_ratio": honorific_ratio,
                "euphonious_word_ratio": euphonious_word_ratio,
                "empathy_ratio": empathy_ratio,
                "apology_ratio": apology_ratio,
                "avg_response_latency": avg_response_latency,
                "interruption_count": interruption_count,
                "silence_ratio": silence_ratio,
                "talk_ratio": talk_ratio
            }
            
            # LLM 분석 데이터 준비
            llm_analysis_data = {
                "audio_analysis_id": 0,  # 실제로는 DB에서 가져온 ID
                "analysis_type": "comprehensive",
                "analysis_result": analysis_result,
                "confidence_score": 0.8,
                "model_used": "advanced_analysis_manager",
                "processing_time": self.performance_stats["stage_times"]["analysis"]
            }
            
            # 비동기 저장
            if self.enable_async:
                await asyncio.gather(
                    self.db_manager.save_audio_analysis_async(audio_analysis_data),
                    self.db_manager.save_quality_analysis_async(quality_analysis_data),
                    self.db_manager.save_llm_analysis_async(llm_analysis_data)
                )
            else:
                # 즉시 저장
                self.db_manager.bulk_save_audio_analysis([audio_analysis_data])
                self.db_manager.bulk_save_quality_analysis([quality_analysis_data])
                self.db_manager.bulk_save_llm_analysis([llm_analysis_data])
            
            self.performance_stats["stage_times"]["database"] = time.time() - stage_start
            
            # 최종 결과 구성
            overall_processing_time = time.time() - overall_start_time
            
            final_result = {
                "audio_file": audio_file,
                "processing_status": "success",
                "processing_time": overall_processing_time,
                "speakers_detected": len(speakers),
                "speaker_segments": segments,
                "transcription": {
                    "full_text": full_text,
                    "segments": transcription_segments,
                    "language": stt_result.get("language", "ko"),
                    "confidence": stt_result.get("language_probability", 0.0)
                },
                "analysis": analysis_result,
                "quality_metrics": {
                    "clarity": category_scores.get("expertise", 0.5) * 0.6 + category_scores.get("specific_info", 0.5) * 0.4,
                    "politeness": category_scores.get("politeness", 0.5) * 0.7 + category_scores.get("negative_expression", 0.5) * 0.3,
                    "empathy": category_scores.get("empathy", 0.5),
                    "professionalism": category_scores.get("expertise", 0.5),
                    "response_quality": communication_quality.get("overall_score", 0.5),
                    "overall_score": communication_quality.get("overall_score", 0.5),
                    "detailed_analysis": detailed_analysis,
                    "recommendations": communication_quality.get("recommendations", []),
                    # KNU 감성 분석 결과
                    "knu_sentiment": {
                        "score": category_scores.get("sentiment", 0.5),
                        "positive_ratio": sentiment_details.get("positive_ratio", 0),
                        "negative_ratio": sentiment_details.get("negative_ratio", 0),
                        "positive_intensity": sentiment_details.get("positive_intensity", 0),
                        "negative_intensity": sentiment_details.get("negative_intensity", 0),
                        "examples": sentiment_analysis.get("examples", [])
                    },
                    # 고객 감정 추세 분석 결과 (50% 구분으로 안정성 향상)
                    "customer_sentiment_trend": {
                        "early_sentiment": analysis_result.get("customer_sentiment_early"),
                        "late_sentiment": analysis_result.get("customer_sentiment_late"),
                        "trend": analysis_result.get("customer_sentiment_trend"),
                        "trend_description": "개선됨" if analysis_result.get("customer_sentiment_trend", 0) > 0 else "악화됨" if analysis_result.get("customer_sentiment_trend", 0) < 0 else "변화없음",
                        "analysis_method": "50% 구분 (안정성 향상)"
                    }
                },
                "performance_stats": {
                    "stage_times": self.performance_stats["stage_times"].copy(),
                    "cache_hits": {
                        "audio_preprocessing": 0,  # 실제로는 각 컴포넌트에서 가져와야 함
                        "vocal_separation": 0,
                        "stt_processing": 0,
                        "punctuation_restoration": 0,
                        "text_analysis": 0
                    }
                }
            }
            
            # 성능 통계 업데이트
            self.performance_stats["total_analyses"] += 1
            self.performance_stats["successful_analyses"] += 1
            self.performance_stats["avg_processing_time"] = (
                (self.performance_stats["avg_processing_time"] * (self.performance_stats["total_analyses"] - 1) + overall_processing_time) 
                / self.performance_stats["total_analyses"]
            )
            
            print(f"✅ 종합 분석 완료: {overall_processing_time:.2f}초")
            print(f"📊 품질 점수: {final_result['quality_metrics']['overall_score']:.2f}")
            
            return final_result
            
        except Exception as e:
            print(f"⚠️ 종합 분석 실패: {e}")
            
            # 성능 통계 업데이트
            self.performance_stats["total_analyses"] += 1
            self.performance_stats["failed_analyses"] += 1
            
            return {
                "audio_file": audio_file,
                "processing_status": "failed",
                "error": str(e),
                "processing_time": time.time() - overall_start_time if 'overall_start_time' in locals() else 0
            }
    
    async def analyze_batch_parallel(self, audio_files: List[str]) -> List[Dict[str, Any]]:
        """
        배치 병렬 분석
        
        Parameters
        ----------
        audio_files : List[str]
            분석할 오디오 파일 리스트
            
        Returns
        -------
        List[Dict[str, Any]]
            분석 결과 리스트
        """
        try:
            print(f"🚀 배치 병렬 분석 시작: {len(audio_files)}개 파일")
            start_time = time.time()
            
            # 병렬 태스크 생성
            tasks = [self.analyze_audio_comprehensive(audio_file) for audio_file in audio_files]
            
            # 병렬 실행
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 정리
            final_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"⚠️ 파일 {i} 분석 실패: {result}")
                    final_results.append({
                        "audio_file": audio_files[i],
                        "processing_status": "failed",
                        "error": str(result),
                        "processing_time": 0
                    })
                else:
                    final_results.append(result)
            
            processing_time = time.time() - start_time
            print(f"✅ 배치 분석 완료: {processing_time:.2f}초")
            
            return final_results
            
        except Exception as e:
            print(f"⚠️ 배치 분석 실패: {e}")
            return [{"error": str(e)} for _ in audio_files]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        return self.performance_stats.copy()
    
    def get_component_stats(self) -> Dict[str, Any]:
        """각 컴포넌트별 성능 통계 반환"""
        return {
            "audio_preprocessor": self.audio_preprocessor.performance_stats if hasattr(self.audio_preprocessor, 'performance_stats') else {},
            "dialogue_detector": {},  # AdvancedDialogueDetecting에는 성능 통계가 없음
            "vocal_separator": {},    # AdvancedDemucsVocalSeparator에는 성능 통계가 없음
            "transcriber": self.transcriber.performance_stats if hasattr(self.transcriber, 'performance_stats') else {},
            "punctuation_restorer": self.punctuation_restorer.get_performance_stats(),
            "analysis_manager": self.analysis_manager.get_performance_stats(),
            "db_manager": self.db_manager.get_performance_stats()
        }
    
    def cleanup_all_caches(self, max_age_hours: int = 24):
        """모든 캐시 정리"""
        try:
            print("🧹 모든 캐시 정리 시작")
            
            # 각 컴포넌트의 캐시 정리
            if hasattr(self.audio_preprocessor, 'cleanup_cache'):
                self.audio_preprocessor.cleanup_cache(max_age_hours)
            
            if hasattr(self.vocal_separator, 'cleanup_cache'):
                self.vocal_separator.cleanup_cache(max_age_hours)
            
            if hasattr(self.transcriber, 'cleanup_cache'):
                self.transcriber.cleanup_cache(max_age_hours)
            
            self.punctuation_restorer.cleanup_cache(max_age_hours)
            self.analysis_manager.cleanup_cache(max_age_hours)
            
            print("✅ 모든 캐시 정리 완료")
            
        except Exception as e:
            print(f"⚠️ 캐시 정리 실패: {e}")
    
    def cleanup(self):
        """리소스 정리"""
        try:
            print("🧹 AdvancedIntegratedAnalyzer 정리 시작")
            
            # 각 컴포넌트 정리
            self.audio_preprocessor.cleanup()
            self.dialogue_detector.cleanup()
            self.transcriber.cleanup()
            self.analysis_manager.cleanup()
            self.db_manager.cleanup()
            
            print("✅ AdvancedIntegratedAnalyzer 정리 완료")
            
        except Exception as e:
            print(f"⚠️ 정리 실패: {e}")


# 사용 예시
async def main():
    """메인 실행 함수"""
    analyzer = AdvancedIntegratedAnalyzer(
        enable_cache=True,
        enable_parallel=True,
        enable_async=True,
        max_workers=4
    )
    
    try:
        # 단일 파일 분석
        result = await analyzer.analyze_audio_comprehensive("audio/sample.wav")
        print(f"분석 결과: {result['processing_status']}")
        
        # 배치 분석
        audio_files = ["audio/file1.wav", "audio/file2.wav", "audio/file3.wav"]
        results = await analyzer.analyze_batch_parallel(audio_files)
        
        # 성능 통계 출력
        stats = analyzer.get_performance_stats()
        print(f"성능 통계: {stats}")
        
    finally:
        analyzer.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 