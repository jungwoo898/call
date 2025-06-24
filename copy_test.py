import shutil
import time
import os

# 복사할 파일과 대상 경로
source = "audio/final_test.mp3"
destination = "C:/app/audio/test_dialogue_real.mp3"

print(f"파일 복사 시작: {source} -> {destination}")

try:
    shutil.copy2(source, destination)
    print("✅ 파일 복사 완료!")
    print(f"파일 크기: {os.path.getsize(destination) / 1024:.1f}KB")
    
    # 5초 대기 후 결과 확인
    time.sleep(5)
    
    # 파일이 처리되었는지 확인
    if os.path.exists(destination):
        print("⚠️ 파일이 아직 존재함 (처리 중 또는 처리되지 않음)")
    else:
        print("✅ 파일이 삭제됨 (처리 완료)")
        
except Exception as e:
    print(f"❌ 오류 발생: {e}") 