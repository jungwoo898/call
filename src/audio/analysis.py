# Standard library imports
import os
import wave
from typing import List, Dict, Annotated, Union, Tuple, Any, Optional

# Related third-party imports
import nltk
import numpy as np
import soundfile as sf
from librosa.feature import mfcc
from scipy.fft import fft, fftfreq


class WordSpeakerMapper:
    """
    Maps words to speakers based on timestamps and aligns speaker tags after punctuation restoration.

    This class processes word timing information and assigns each word to a speaker
    based on the provided speaker timestamps. Missing timestamps are handled, and each
    word can be aligned to a speaker based on different reference points ('start', 'mid', or 'end').
    After punctuation restoration, word-speaker mapping can be realigned to ensure consistency
    within a sentence.

    Attributes
    ----------
    word_timestamps : List[Dict]
        List of word timing information with 'start', 'end', and 'text' keys.
    speaker_timestamps : List[List[int]]
        List of speaker segments, where each segment contains [start_time, end_time, speaker_id].
    word_speaker_mapping : List[Dict] or None
        Processed word-to-speaker mappings.

    Methods
    -------
    audio_filter_missing_timestamps(word_timestamps, initial_timestamp=0, final_timestamp=None)
        Fills in missing start and end timestamps in word timing data.
    audio_get_words_speaker_mapping(word_anchor_option='start')
        Maps words to speakers based on word and speaker timestamps.
    """

    def __init__(
            self,
            word_timestamps: Annotated[List[Dict], "List of word timing information"],
            speaker_timestamps: Annotated[List[List[Union[int, float]]], "List of speaker segments"],
    ):
        """
        Initializes the WordSpeakerMapper with word and speaker timestamps.

        Parameters
        ----------
        word_timestamps : List[Dict]
            List of word timing information.
        speaker_timestamps : List[List[int]]
            List of speaker segments.
        """
        self.word_timestamps = self.audio_filter_missing_timestamps(word_timestamps)
        self.speaker_timestamps = speaker_timestamps
        self.word_speaker_mapping = None

    def audio_filter_missing_timestamps(
            self,
            word_timestamps: Annotated[List[Dict], "List of word timing information"],
            initial_timestamp: Annotated[int, "Start time of the first word"] = 0,
            final_timestamp: Annotated[int, "End time of the last word"] = None
    ) -> Annotated[List[Dict], "List of word timestamps with missing values filled"]:
        """
        Fills in missing start and end timestamps.

        Parameters
        ----------
        word_timestamps : List[Dict]
            List of word timing information that may contain missing timestamps.
        initial_timestamp : int, optional
            Start time of the first word, default is 0.
        final_timestamp : int, optional
            End time of the last word, if available.

        Returns
        -------
        List[Dict]
            List of word timestamps with missing values filled.

        Examples
        --------
        >>> word_timestamp = [{'text': 'Hello', 'end': 1.2}]
        >>> mapper = WordSpeakerMapper([], [])
        >>> mapper.audio_filter_missing_timestamps(word_timestamps)
        [{'text': 'Hello', 'start': 0, 'end': 1.2}]
        """
        if not word_timestamps:
            return []
        
        if word_timestamps[0].get("start") is None:
            word_timestamps[0]["start"] = initial_timestamp
            word_timestamps[0]["end"] = self._get_next_start_timestamp(
                word_timestamps,
                0,
                final_timestamp,
            )
    

        result = [word_timestamps[0]]

        for i, ws in enumerate(word_timestamps[1:], start=1):
            if "text" not in ws:
                continue

            if ws.get("start") is None:
                ws["start"] = word_timestamps[i - 1]["end"]
                ws["end"] = self._get_next_start_timestamp(word_timestamps, i, final_timestamp)

            if ws["text"] is not None:
                result.append(ws)
        return result

    @staticmethod
    def _get_next_start_timestamp(
            word_timestamps: Annotated[List[Dict], "List of word timing information"],
            current_word_index: Annotated[int, "Index of the current word"],
            final_timestamp: Annotated[int, "Final timestamp if needed"]
    ) -> Annotated[int, "Next start timestamp for filling missing values"]:
        """
        Finds the next start timestamp to fill in missing values.

        Parameters
        ----------
        word_timestamps : List[Dict]
            List of word timing information.
        current_word_index : int
            Index of the current word.
        final_timestamp : int, optional
            Final timestamp to use if no next timestamp is found.

        Returns
        -------
        int
            Next start timestamp for filling missing values.

        Examples
        --------
        >>> word_timestamp = [{'start': 0.5, 'text': 'Hello'}, {'end': 2.0}]
        >>> mapper = WordSpeakerMapper([], [])
        >>> mapper._get_next_start_timestamp(word_timestamps, 0, 2)
        """
        if current_word_index == len(word_timestamps) - 1:
            return word_timestamps[current_word_index]["start"]

        next_word_index = current_word_index + 1
        while next_word_index < len(word_timestamps):
            if word_timestamps[next_word_index].get("start") is None:
                word_timestamps[current_word_index]["text"] += (
                        " " + word_timestamps[next_word_index]["text"]
                )
                word_timestamps[next_word_index]["text"] = None
                next_word_index += 1
                if next_word_index == len(word_timestamps):
                    return final_timestamp
            else:
                return word_timestamps[next_word_index]["start"]
        return final_timestamp

    def audio_get_words_speaker_mapping(self, word_anchor_option='start') -> List[Dict]:
        """
        Maps words to speakers based on their timestamps.

        Parameters
        ----------
        word_anchor_option : str, optional
            Anchor point for word mapping ('start', 'mid', or 'end'), default is 'start'.

        Returns
        -------
        List[Dict]
            List of word-to-speaker mappings with timestamps and speaker IDs.

        Examples
        --------
        >>> word_timestamps = [{'start': 0.5, 'end': 1.2, 'text': 'Hello'}]
        >>> speaker_timestamps = [[0, 1000, 1]]
        >>> mapper = WordSpeakerMapper(word_timestamps, speaker_timestamps)
        >>> mapper.audio_get_words_speaker_mapping()
        [{'text': 'Hello', 'start_time': 500, 'end_time': 1200, 'speaker': 1}]
        """

        def audio_get_word_ts_anchor(start: int, end: int, option: str) -> int:
            """
            Determines the anchor timestamp for a word.

            Parameters
            ----------
            start : int
                Start time of the word in milliseconds.
            end : int
                End time of the word in milliseconds.
            option : str
                Anchor point for timestamp calculation ('start', 'mid', or 'end').

            Returns
            -------
            int
                Anchor timestamp for the word.

            Examples
            --------
            >>> audio_get_word_ts_anchor(500, 1200, 'mid')
            850
            """
            if option == "end":
                return end
            elif option == "mid":
                return (start + end) // 2
            return start

        wrd_spk_mapping = []
        turn_idx = 0
        num_speaker_ts = len(self.speaker_timestamps)

        for wrd_dict in self.word_timestamps:
            ws, we, wrd = (
                int(wrd_dict["start"] * 1000),
                int(wrd_dict["end"] * 1000),
                wrd_dict["text"],
            )
            wrd_pos = audio_get_word_ts_anchor(ws, we, word_anchor_option)

            sp = -1

            while turn_idx < num_speaker_ts and wrd_pos > self.speaker_timestamps[turn_idx][1]:
                turn_idx += 1

            if turn_idx < num_speaker_ts and self.speaker_timestamps[turn_idx][0] <= wrd_pos <= \
                    self.speaker_timestamps[turn_idx][1]:
                sp = self.speaker_timestamps[turn_idx][2]
            elif turn_idx > 0:
                sp = self.speaker_timestamps[turn_idx - 1][2]

            wrd_spk_mapping.append(
                {"text": wrd, "start_time": ws, "end_time": we, "speaker": sp}
            )

        self.word_speaker_mapping = wrd_spk_mapping
        return self.word_speaker_mapping

    def audio_realign_with_punctuation(self, max_words_in_sentence: int = 50) -> None:
        """
        Realigns word-speaker mapping after punctuation restoration.

        This method ensures consistent speaker mapping within sentences by analyzing
        punctuation and adjusting speaker labels for words that are part of the same sentence.

        Parameters
        ----------
        max_words_in_sentence : int, optional
            Maximum number of words to consider for realignment in a sentence,
            default is 50.

        Examples
        --------
        >>> word_speaker_mapping = [
        ...     {"text": "Hello", "speaker": "Speaker 1"},
        ...     {"text": "world", "speaker": "Speaker 2"},
        ...     {"text": ".", "speaker": "Speaker 2"},
        ...     {"text": "How", "speaker": "Speaker 1"},
        ...     {"text": "are", "speaker": "Speaker 1"},
        ...     {"text": "you", "speaker": "Speaker 2"},
        ...     {"text": "?", "speaker": "Speaker 2"}
        ... ]
        >>> mapper = WordSpeakerMapper([], [])
        >>> mapper.word_speaker_mapping = word_speaker_mapping
        >>> mapper.audio_realign_with_punctuation()
        >>> print(mapper.word_speaker_mapping)
        [{'text': 'Hello', 'speaker': 'Speaker 1'},
         {'text': 'world', 'speaker': 'Speaker 1'},
         {'text': '.', 'speaker': 'Speaker 1'},
         {'text': 'How', 'speaker': 'Speaker 1'},
         {'text': 'are', 'speaker': 'Speaker 1'},
         {'text': 'you', 'speaker': 'Speaker 1'},
         {'text': '?', 'speaker': 'Speaker 1'}]
        """
        sentence_ending_punctuations = ".?!"

        def audio_is_word_sentence_end(word_index: Annotated[int, "Index of the word to check"]) -> Annotated[
            bool, "True if the word is a sentence end, False otherwise"]:
            """
            Checks if a word is the end of a sentence based on punctuation.

            This method determines whether a word at the given index marks
            the end of a sentence by checking if the last character of the
            word is a sentence-ending punctuation (e.g., '.', '!', or '?').

            Parameters
            ----------
            word_index : int
                Index of the word to check in the `word_speaker_mapping`.

            Returns
            -------
            bool
                True if the word at the given index is the end of a sentence,
                False otherwise.

            """
            return (
                    word_index >= 0
                    and self.word_speaker_mapping[word_index]["text"][-1] in sentence_ending_punctuations
            )

        wsp_len = len(self.word_speaker_mapping)
        words_list = [wd['text'] for wd in self.word_speaker_mapping]
        speaker_list = [wd['speaker'] for wd in self.word_speaker_mapping]

        k = 0
        while k < len(self.word_speaker_mapping):
            if (
                    k < wsp_len - 1
                    and speaker_list[k] != speaker_list[k + 1]
                    and not audio_is_word_sentence_end(k)
            ):
                left_idx = self._get_first_word_idx_of_sentence(
                    k, words_list, speaker_list, max_words_in_sentence
                )
                right_idx = (
                    self._get_last_word_idx_of_sentence(
                        k, words_list, max_words_in_sentence - (k - left_idx) - 1
                    )
                    if left_idx > -1
                    else -1
                )
                if min(left_idx, right_idx) == -1:
                    k += 1
                    continue

                spk_labels = speaker_list[left_idx:right_idx + 1]
                mod_speaker = max(set(spk_labels), key=spk_labels.count)
                if spk_labels.count(mod_speaker) < len(spk_labels) // 2:
                    k += 1
                    continue

                speaker_list[left_idx:right_idx + 1] = [mod_speaker] * (
                        right_idx - left_idx + 1
                )
                k = right_idx

            k += 1

        for idx in range(len(self.word_speaker_mapping)):
            self.word_speaker_mapping[idx]["speaker"] = speaker_list[idx]

    @staticmethod
    def _get_first_word_idx_of_sentence(
            word_idx: int, word_list: List[str], speaker_list: List[str], max_words: int
    ) -> int:
        """
        Finds the first word index of a sentence for realignment.

        Parameters
        ----------
        word_idx : int
            Current word index.
        word_list : List[str]
            List of words in the sentence.
        speaker_list : List[str]
            List of speakers for the words.
        max_words : int
            Maximum words to consider in the sentence.

        Returns
        -------
        int
            The index of the first word of the sentence.

        Examples
        --------
        >>> words_list = ["Hello", "world", ".", "How", "are", "you", "?"]
        >>> speakers_list = ["Speaker 1", "Speaker 1", "Speaker 1", "Speaker 2", "Speaker 2", "Speaker 2", "Speaker 2"]
        >>> WordSpeakerMapper._get_first_word_idx_of_sentence(4, word_list, speaker_list, 50)
        3
        """
        sentence_ending_punctuations = ".?!"
        is_word_sentence_end = (
            lambda x: x >= 0 and word_list[x][-1] in sentence_ending_punctuations
        )
        left_idx = word_idx
        while (
                left_idx > 0
                and word_idx - left_idx < max_words
                and speaker_list[left_idx - 1] == speaker_list[left_idx]
                and not audio_is_word_sentence_end(left_idx - 1)
        ):
            left_idx -= 1

        return left_idx if left_idx == 0 or audio_is_word_sentence_end(left_idx - 1) else -1

    @staticmethod
    def _get_last_word_idx_of_sentence(
            word_idx: int, word_list: List[str], max_words: int
    ) -> int:
        """
        Finds the last word index of a sentence for realignment.

        Parameters
        ----------
        word_idx : int
            Current word index.
        word_list : List[str]
            List of words in the sentence.
        max_words : int
            Maximum words to consider in the sentence.

        Returns
        -------
        int
            The index of the last word of the sentence.

        Examples
        --------
        >>> words_list = ["Hello", "world", ".", "How", "are", "you", "?"]
        >>> WordSpeakerMapper._get_last_word_idx_of_sentence(3, word_list, 50)
        6
        """
        sentence_ending_punctuations = ".?!"
        is_word_sentence_end = (
            lambda x: x >= 0 and word_list[x][-1] in sentence_ending_punctuations
        )
        right_idx = word_idx
        while (
                right_idx < len(word_list) - 1
                and right_idx - word_idx < max_words
                and not audio_is_word_sentence_end(right_idx)
        ):
            right_idx += 1

        return (
            right_idx
            if right_idx == len(word_list) - 1 or audio_is_word_sentence_end(right_idx)
            else -1
        )


class SentenceSpeakerMapper:
    """
    Groups words into sentences and assigns each sentence to a speaker.

    This class uses word-speaker mapping to group words into sentences based on punctuation
    and speaker changes. It uses the NLTK library to detect sentence boundaries.

    Attributes
    ----------
    sentence_checker : Callable
        Function to check for sentence breaks.
    sentence_ending_punctuations : str
        String of punctuation characters that indicate sentence endings.

    Methods
    -------
    audio_get_sentences_speaker_mapping(word_speaker_mapping)
        Groups words into sentences and assigns each sentence to a speaker.
    """

    def __init__(self):
        """
        Initializes the SentenceSpeakerMapper and downloads required NLTK resources.
        """
        nltk.download('punkt', quiet=True)
        self.sentence_checker = nltk.tokenize.PunktSentenceTokenizer().text_contains_sentbreak
        # 한국어 문장 부호 확장
        self.sentence_ending_punctuations = ".?!。？！～"
        
        # 한국어 문장 경계 패턴 추가
        self.korean_sentence_patterns = [
            r'[.?!。？！][\s]*$',  # 문장 부호로 끝나는 경우
            r'[다가요니까요지만습니다][\s]*$',  # 한국어 종결어미
            r'[해요해주세요해봐요합니다][\s]*$',  # 존댓말 종결
            r'[네예아니오맞습니다그렇습니다][\s]*$',  # 답변 표현
        ]
        
    def audio_korean_sentence_check(self, text: str) -> bool:
        """
        한국어 특성을 고려한 문장 경계 검사
        
        Parameters
        ----------
        text : str
            검사할 텍스트
            
        Returns
        -------
        bool
            문장 경계 여부
        """
        import re
        
        # 기본 NLTK 검사
        if self.sentence_checker(text):
            return True
            
        # 한국어 패턴 검사
        for pattern in self.korean_sentence_patterns:
            if re.search(pattern, text.strip()):
                return True
                
        # 문장 길이 기반 검사 (너무 긴 문장 분할)
        if len(text.split()) > 30:  # 30단어 이상 시 분할 고려
            return True
            
        return False

    def audio_get_sentences_speaker_mapping(
            self,
            word_speaker_mapping: Annotated[List[Dict], "List of words with speaker labels"]
    ) -> Annotated[List[Dict], "List of sentences with speaker labels and timing information"]:
        """
        Groups words into sentences and assigns each sentence to a speaker.

        Parameters
        ----------
        word_speaker_mapping : List[Dict]
            List of words with speaker labels.

        Returns
        -------
        List[Dict]
            List of sentences with speaker labels and timing information.

        Examples
        --------
        >>> sentence_mapper = SentenceSpeakerMapper()
        >>> word_speaker_map = [
        ...     {'text': 'Hello', 'start_time': 0, 'end_time': 500, 'speaker': 1},
        ...     {'text': 'world.', 'start_time': 600, 'end_time': 1000, 'speaker': 1},
        ...     {'text': 'How', 'start_time': 1100, 'end_time': 1300, 'speaker': 2},
        ...     {'text': 'are', 'start_time': 1400, 'end_time': 1500, 'speaker': 2},
        ...     {'text': 'you?', 'start_time': 1600, 'end_time': 2000, 'speaker': 2},
        ... ]
        >>> sentence_mapper.audio_get_sentences_speaker_mapping(word_speaker_mapping)
        [{'speaker': 'Speaker 1', 'start_time': 0, 'end_time': 1000, 'text': 'Hello world. '},
         {'speaker': 'Speaker 2', 'start_time': 1100, 'end_time': 2000, 'text': 'How are you?'}]
        """
        snts = []
        prev_spk = word_speaker_mapping[0]['speaker']
        snt = {
            "speaker": f"Speaker {prev_spk}",
            "start_time": word_speaker_mapping[0]['start_time'],
            "end_time": word_speaker_mapping[0]['end_time'],
            "text": word_speaker_mapping[0]['text'] + " ",
        }

        for word_dict in word_speaker_mapping[1:]:
            word, spk = word_dict["text"], word_dict["speaker"]
            s, e = word_dict["start_time"], word_dict["end_time"]
            if spk != prev_spk or self.audio_korean_sentence_check(snt["text"] + word):
                snts.append(snt)
                snt = {
                    "speaker": f"Speaker {spk}",
                    "start_time": s,
                    "end_time": e,
                    "text": word + " ",
                }
            else:
                snt["end_time"] = e
                snt["text"] += word + " "
            prev_spk = spk

        snts.append(snt)
        return snts


class Audio:
    """
    A class to handle audio file analysis and property extraction.

    This class provides methods to load an audio file, process it, and
    extract various audio properties including spectral, temporal, and
    perceptual features.

    Parameters
    ----------
    audio_path : str
        Path to the audio file to be analyzed.

    Attributes
    ----------
    audio_path : str
        Path to the audio file.
    extension : str
        File extension of the audio file.
    samples : int
        Total number of audio samples.
    duration : float
        Duration of the audio in seconds.
    data : np.ndarray
        Audio data loaded from the file.
    rate : int
        Sampling rate of the audio file.
    """

    def __init__(self, audio_path: str):
        """
        Initialize the Audio class with a given audio file path.

        Parameters
        ----------
        audio_path : str
            Path to the audio file.

        Raises
        ------
        TypeError
            If `audio_path` is not a non-empty string.
        FileNotFoundError
            If the file specified by `audio_path` does not exist.
        ValueError
            If the file has an unsupported extension or is empty.
        RuntimeError
            If there is an error reading the audio file.
        """
        if not isinstance(audio_path, str) or not audio_path:
            raise TypeError("audio_path must be a non-empty string")

        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"The specified audio file does not exist: {audio_path}")

        valid_extensions = [".wav", ".flac", ".mp3", ".ogg", ".m4a", ".aac"]
        extension = os.path.splitext(audio_path)[1].lower()
        if extension not in valid_extensions:
            raise ValueError(f"File extension {extension} is not recognized as a supported audio format.")

        try:
            # soundfile로 먼저 시도
            self.data, self.rate = sf.read(audio_path, dtype='float32')
            print("✅ soundfile로 오디오 파일 읽기 성공")
        except Exception as e:
            print(f"⚠️ soundfile 읽기 실패: {e}")
            try:
                # librosa로 fallback 시도
                import librosa
                print("🔄 librosa로 fallback 시도...")
                self.data, self.rate = librosa.load(audio_path, sr=None, dtype=np.float32)
                print("✅ librosa로 오디오 파일 읽기 성공")
            except Exception as e2:
                print(f"⚠️ librosa 읽기 실패: {e2}")
                try:
                    # FFmpeg를 사용한 최종 fallback
                    import subprocess
                    import tempfile
                    print("🔄 FFmpeg를 사용한 최종 fallback 시도...")
                    
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                        temp_path = temp_file.name
                    
                    # FFmpeg로 WAV 형식으로 변환
                    cmd = [
                        'ffmpeg', '-i', audio_path, 
                        '-acodec', 'pcm_s16le', 
                        '-ar', '16000', 
                        '-ac', '1', 
                        '-y', temp_path
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        raise RuntimeError(f"FFmpeg 변환 실패: {result.stderr}")
                    
                    # 변환된 파일 읽기
                    self.data, self.rate = sf.read(temp_path, dtype='float32')
                    
                    # 임시 파일 삭제
                    os.unlink(temp_path)
                    print("✅ FFmpeg 변환 후 오디오 파일 읽기 성공")
                    
                except Exception as e3:
                    raise RuntimeError(f"Error reading audio file: {audio_path} (soundfile: {e}, librosa: {e2}, ffmpeg: {e3})") from e3

        if len(self.data) == 0:
            raise ValueError(f"Audio file is empty: {audio_path}")

        # Convert stereo or multichannel audio to mono
        if len(self.data.shape) > 1 and self.data.shape[1] > 1:
            self.data = np.mean(self.data, axis=1)

        self.audio_path = audio_path
        self.extension = extension
        self.samples = len(self.data)
        self.duration = self.samples / self.rate

    def audio_properties(self) -> Tuple[
        str, str, str, int, float, float, Optional[int], int, float, float, Dict[str, float]]:
        """
        Extract various properties and features from the audio file.

        Returns
        -------
        Tuple[str, str, str, int, float, float, int | None, int, float, float, Dict[str, float]]
            A tuple containing:
            - File name (str)
            - File extension (str)
            - File path (str)
            - Sample rate (int)
            - Minimum frequency (float)
            - Maximum frequency (float)
            - Bit depth (int | None)
            - Number of channels (int)
            - Duration (float)
            - Root mean square loudness (float)
            - A dictionary of extracted audio_properties(Dict[str, float])

        Notes
        -----
        Properties extracted include:
        - Spectral bands energy
        - Zero Crossing Rate (ZCR)
        - Spectral Centroid
        - MFCCs (Mel Frequency Cepstral Coefficients)

        Examples
        --------
        >>> audio = Audio("sample.wav")
        >>> audio.audio_properties()
        ('sample.wav', '.wav', '/path/to/sample.wav', 44100, 20.0, 20000.0, 16, 2, 5.2, 0.25, {...})
        """
        bands = [(20, 250), (250, 2000), (2000, 6000), (6000, 20000)]

        x = fft(self.data)
        xf = fftfreq(self.samples, 1 / self.rate)

        nonzero_indices = np.where(xf != 0)[0]
        min_freq = np.min(np.abs(xf[nonzero_indices]))
        max_freq = np.max(np.abs(xf))

        bit_depth = None
        if self.extension == ".wav":
            with wave.open(file_path, "r", encoding="utf-8") as wav_file:
                bit_depth = wav_file.getsampwidth() * 8
                channels = wav_file.getnchannels()
        else:
            info = sf.info(self.audio_path)
            channels = info.channels

        duration = float(self.duration)
        loudness = np.sqrt(np.mean(self.data ** 2))

        s = np.abs(x)
        freqs = xf
        eq_properties = {}
        for band in bands:
            band_mask = (freqs >= band[0]) & (freqs <= band[1])
            band_data = s[band_mask]
            band_energy = np.mean(band_data ** 2, axis=0) if band_data.size > 0 else 0
            eq_properties[f"EQ_{band[0]}_{band[1]}_Hz"] = band_energy

        zcr = np.sum(np.abs(np.diff(np.sign(self.data)))) / len(self.data)

        magnitude_spectrum = np.abs(np.fft.rfft(self.data))
        freqs_centroid = np.fft.rfftfreq(len(self.data), 1.0 / self.rate)
        spectral_centroid = (np.sum(freqs_centroid * magnitude_spectrum) /
                             np.sum(magnitude_spectrum)) if np.sum(magnitude_spectrum) != 0 else 0.0

        mfccs = mfcc(y=self.data, sr=self.rate, n_mfcc=13)

        mfcc_mean = np.mean(mfccs, axis=1)

        eq_properties["RMSLoudness"] = float(loudness)
        eq_properties["ZeroCrossingRate"] = float(zcr)
        eq_properties["SpectralCentroid"] = float(spectral_centroid)
        for i, val in enumerate(mfcc_mean):
            eq_properties[f"MFCC_{i + 1}"] = float(val)

        eq_properties_converted = {key: float(value) for key, value in eq_properties.items()}

        file_name = os.path.basename(self.audio_path)
        path = os.path.abspath(self.audio_path)

        bit_depth = int(bit_depth) if bit_depth is not None else None
        channels = int(channels) if channels is not None else 1

        return (
            file_name,
            self.extension,
            path,
            int(self.rate),
            float(min_freq),
            float(max_freq),
            bit_depth,
            channels,
            float(duration),
            float(loudness),
            eq_properties_converted
        )

    def audio_extract_properties(self) -> Dict[str, Any]:
        """
        Extract audio properties in a dictionary format for database storage.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing audio properties for database insertion.
        """
        try:
            # Get file size
            file_size = os.path.getsize(self.audio_path)
            
            # Get basic properties
            file_name = os.path.basename(self.audio_path)
            file_path = os.path.abspath(self.audio_path)
            
            # Get bit depth and channels
            bit_depth = None
            if self.extension == ".wav":
                with wave.open(file_path, "r", encoding="utf-8") as wav_file:
                    bit_depth = wav_file.getsampwidth() * 8
                    channels = wav_file.getnchannels()
            else:
                info = sf.info(self.audio_path)
                channels = info.channels
            
            return {
                "file_name": file_name,
                "file_path": file_path,
                "duration": float(self.duration),
                "sample_rate": int(self.rate),
                "channels": int(channels) if channels is not None else 1,
                "bit_depth": int(bit_depth) if bit_depth is not None else None,
                "format": self.extension,
                "file_size": file_size
            }
        except Exception as e:
            print(f"오디오 속성 추출 오류: {e}")
            # 기본값 반환
            return {
                "file_name": os.path.basename(self.audio_path),
                "file_path": os.path.abspath(self.audio_path),
                "duration": 0.0,
                "sample_rate": 0,
                "channels": 1,
                "bit_depth": None,
                "format": self.extension,
                "file_size": 0
            }


if __name__ == "__main__":
    words_timestamp = [
        {'text': 'Hello', 'start': 0.0, 'end': 1.2},
        {'text': 'world', 'start': 1.3, 'end': 2.0}
    ]
    speaker_timestamp = [
        [0.0, 1.5, 1],
        [1.6, 3.0, 2]
    ]

    word_sentence_mapper = WordSpeakerMapper(words_timestamp, speaker_timestamp)
    word_speaker_maps = word_sentence_mapper.audio_get_words_speaker_mapping()
    print("Word-Speaker Mapping:")
    print(word_speaker_maps)
