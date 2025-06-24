from pydub import AudioSegment
import os

# MP3 파일 로드
print("🔄 MP3 파일 로딩 중...")
audio = AudioSegment.from_mp3('40186.mp3')

# WAV로 내보내기
print("🔄 WAV로 변환 중...")
audio.export('40186.wav', format='wav')

print('✅ MP3 -> WAV 변환 완료')
print(f'파일 크기: {os.path.getsize("40186.wav")} bytes') 