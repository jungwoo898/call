# Standard library imports
import os
from typing import Annotated, List, Dict

# Related third-party imports
import torch
from faster_whisper import decode_audio

# ctc-forced-aligner 안전 import
load_audio = None
load_alignment_model = None
generate_emissions = None
preprocess_text = None
get_alignments = None
get_spans = None
postprocess_results = None

try:
    import ctc_forced_aligner
    # 사용 가능한 함수들 확인
    if hasattr(ctc_forced_aligner, 'load_alignment_model'):
        load_alignment_model = ctc_forced_aligner.load_alignment_model
    if hasattr(ctc_forced_aligner, 'generate_emissions'):
        generate_emissions = ctc_forced_aligner.generate_emissions
    if hasattr(ctc_forced_aligner, 'preprocess_text'):
        preprocess_text = ctc_forced_aligner.preprocess_text
    if hasattr(ctc_forced_aligner, 'get_alignments'):
        get_alignments = ctc_forced_aligner.get_alignments
    if hasattr(ctc_forced_aligner, 'get_spans'):
        get_spans = ctc_forced_aligner.get_spans
    if hasattr(ctc_forced_aligner, 'postprocess_results'):
        postprocess_results = ctc_forced_aligner.postprocess_results
    if hasattr(ctc_forced_aligner, 'load_audio'):
        load_audio = ctc_forced_aligner.load_audio
    
    print("✅ ctc-forced-aligner imported successfully")
except ImportError as e:
    print(f"⚠️ ctc-forced-aligner import failed: {e}")
    print("🔄 ForcedAligner will run in fallback mode")
except Exception as e:
    print(f"⚠️ ctc-forced-aligner error: {e}")
    print("🔄 ForcedAligner will run in fallback mode")


class ForcedAligner:
    """
    ForcedAligner is a class for aligning audio to a provided transcript using a pre-trained alignment model.

    Attributes
    ----------
    device : str
        Device to run the model on ('cuda' for GPU or 'cpu').
    alignment_model : torch.nn.Module
        The pre-trained alignment model.
    alignment_tokenizer : Any
        Tokenizer for processing text in alignment.

    Methods
    -------
    align(audio_path, transcript, language, batch_size)
        Aligns audio with a transcript and returns word-level timing information.
    """

    def __init__(self, device: Annotated[str, "Device for model ('cuda' or 'cpu')"] = None):
        """
        Initialize the ForcedAligner with the specified device.

        Parameters
        ----------
        device : str, optional
            Device for running the model, by default 'cuda' if available, otherwise 'cpu'.
        """
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        
        # ctc-forced-aligner API 호환성 체크
        if load_alignment_model is None:
            print("Warning: ctc-forced-aligner not properly installed. ForcedAligner will be disabled.")
            self.alignment_model = None
            self.alignment_tokenizer = None
            return
            
        try:
            self.alignment_model, self.alignment_tokenizer = load_alignment_model(
                self.device,
                dtype=torch.float16 if self.device == 'cuda' else torch.float32,
            )
        except Exception as e:
            print(f"Warning: Failed to load alignment model: {e}")
            self.alignment_model = None
            self.alignment_tokenizer = None

    def align(
            self,
            audio_path: Annotated[str, "Path to the audio file"],
            transcript: Annotated[str, "Transcript of the audio content"],
            language: Annotated[str, "Language of the transcript"] = 'en',
            batch_size: Annotated[int, "Batch size for emission generation"] = 8,
            whisper_word_timestamps: Annotated[List[Dict], "Word timestamps from faster-whisper"] = None,
    ) -> Annotated[List[Dict[str, float]], "List of word alignment data with timestamps"]:
        """
        Aligns audio with a transcript and returns word-level timing information.

        Parameters
        ----------
        audio_path : str
            Path to the audio file.
        transcript : str
            Transcript text corresponding to the audio.
        language : str, optional
            Language code for the transcript, default is 'en' (English).
        batch_size : int, optional
            Batch size for generating emissions, by default 8.
        whisper_word_timestamps : List[Dict], optional
            Pre-computed word timestamps from faster-whisper, by default None.

        Returns
        -------
        List[Dict[str, float]]
            A list of dictionaries containing word timing information.

        Raises
        ------
        FileNotFoundError
            If the specified audio file does not exist.

        Examples
        --------
        >>> aligner = ForcedAligner()
        >>> aligner.align("path/to/audio.wav", "hello world")
        [{'word': 'hello', 'start': 0.0, 'end': 0.5}, {'word': 'world', 'start': 0.6, 'end': 1.0}]
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(
                f"The audio file at path '{audio_path}' was not found."
            )
        
        # ForcedAligner가 비활성화된 경우
        if self.alignment_model is None:
            print("Warning: ForcedAligner is disabled.")
            
            # faster-whisper word_timestamps가 제공된 경우 우선 사용
            if whisper_word_timestamps:
                print("Using faster-whisper word timestamps instead of ctc-forced-aligner.")
                return whisper_word_timestamps
            
            # fallback: 더미 데이터 생성
            print("Generating dummy alignment data.")
            words = transcript.split()
            dummy_alignments = []
            duration_per_word = 1.0  # 단어당 1초로 가정
            for i, word in enumerate(words):
                dummy_alignments.append({
                    'word': word,
                    'start': i * duration_per_word,
                    'end': (i + 1) * duration_per_word
                })
            return dummy_alignments

        try:
            if load_audio:
                audio_waveform = load_audio(audio_path, self.alignment_model.dtype, self.alignment_model.device)
            else:
                # Fallback to faster_whisper
                speech_array = torch.from_numpy(decode_audio(audio_path))
                audio_waveform = speech_array.to(self.alignment_model.dtype).to(self.alignment_model.device)

            emissions, stride = generate_emissions(
                self.alignment_model,
                audio_waveform,
                batch_size=batch_size,
            )

            tokens_starred, text_starred = preprocess_text(
                transcript,
                romanize=True,
                language=language,
            )

            segments, scores, blank_token = get_alignments(
                emissions,
                tokens_starred,
                self.alignment_tokenizer,
            )

            spans = get_spans(tokens_starred, segments, blank_token)

            word_timestamps = postprocess_results(text_starred, spans, stride, scores)

            if self.device == 'cuda':
                torch.cuda.empty_cache()

            print(f"Word_Timestamps: {word_timestamps}")

            return word_timestamps
            
        except Exception as e:
            print(f"Warning: Forced alignment failed: {e}")
            
            # faster-whisper word_timestamps가 제공된 경우 fallback으로 사용
            if whisper_word_timestamps:
                print("Using faster-whisper word timestamps as fallback.")
                return whisper_word_timestamps
            
            # 최종 fallback: 더미 데이터 반환
            print("Generating dummy alignment data as final fallback.")
            words = transcript.split()
            dummy_alignments = []
            duration_per_word = 1.0
            for i, word in enumerate(words):
                dummy_alignments.append({
                    'word': word,
                    'start': i * duration_per_word,
                    'end': (i + 1) * duration_per_word
                })
            return dummy_alignments


if __name__ == "__main__":

    forced_aligner = ForcedAligner()
    try:
        path = "example_audio.wav"
        audio_transcript = "This is a test transcript."
        word_timestamp = forced_aligner.align(path, audio_transcript)
        print(word_timestamp)
    except FileNotFoundError as e:
        print(e)