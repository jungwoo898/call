# 📂 Callytics 볼륨 마운트 가이드

## 🚨 발견된 문제점

### 1. 임시 디렉토리 경로 불일치
**Docker 마운트**: `./temp:/app/temp`  
**코드에서 사용**: `/app/.temp/session_xxx`  
**결과**: 임시 파일이 컨테이너 내부에만 저장되어 **데이터 손실** 위험

### 2. 캐시 디렉토리 경로 불일치  
**AudioPreprocessor**: `/app/.cache/audio`  
**Docker 마운트**: 설정 없음  
**결과**: 캐시 효과 없음, **성능 저하**

### 3. 로그 디렉토리 일관성
**Docker 마운트**: `./logs:/app/logs` ✅  
**코드에서 사용**: `/app/logs` ✅  
**결과**: 정상 동작

## 🛠️ 표준 경로 정의

### 권장 컨테이너 경로 구조
```
/app/
├── audio/          # 입력 오디오 파일 (마운트)
├── temp/           # 임시 처리 파일 (마운트)
├── logs/           # 로그 파일 (마운트)
├── data/           # 영구 데이터 (마운트)
├── config/         # 설정 파일 (마운트)
├── .cache/         # 캐시 디렉토리 (마운트)
└── Callytics_new.sqlite  # DB 파일 (마운트)
```

## 🔧 수정된 Docker Compose 설정

### 통합 볼륨 마운트 (모든 서비스 공통)
```yaml
volumes:
  # 📁 데이터 디렉토리들
  - ./audio:/app/audio                    # 입력 오디오
  - ./temp:/app/temp                      # 임시 파일
  - ./logs:/app/logs                      # 로그 파일
  - ./data:/app/data                      # 영구 데이터
  - ./config:/app/config                  # 설정 파일
  - ./.cache:/app/.cache                  # 캐시 디렉토리
  
  # 🗄️ 데이터베이스
  - ./Callytics_new.sqlite:/app/Callytics_new.sqlite
```

## 📝 코드 수정 가이드

### 1. 임시 디렉토리 경로 표준화
```python
# ❌ 기존 (마운트되지 않는 경로)
temp_dir = f"/app/.temp/session_{unique_id}"

# ✅ 수정 (마운트된 경로 사용)
temp_dir = f"/app/temp/session_{unique_id}"
```

### 2. 캐시 디렉토리 표준화
```python
# AudioPreprocessor 초기화
def __init__(self, max_workers: int = 4, cache_dir: str = "/app/.cache/audio"):
    # ✅ 이미 올바른 경로 사용 중
```

### 3. 환경 변수 설정 표준화
```yaml
environment:
  # ✅ 올바른 SQLite URL
  - DATABASE_URL=sqlite:////app/Callytics_new.sqlite  # 절대 경로
  
  # 🗂️ 표준 디렉토리 환경 변수
  - TEMP_DIR=/app/temp
  - CACHE_DIR=/app/.cache
  - LOG_DIR=/app/logs
  - DATA_DIR=/app/data
```

## 🔍 검증 방법

### 1. 볼륨 마운트 확인
```bash
# 컨테이너 내부 확인
docker exec -it callytics-api-gateway ls -la /app/

# 호스트에서 파일 생성 테스트
echo "test" > ./temp/mount_test.txt
docker exec -it callytics-api-gateway cat /app/temp/mount_test.txt
```

### 2. 권한 확인
```bash
# 컨테이너 사용자 확인
docker exec -it callytics-api-gateway whoami

# 디렉토리 권한 확인
docker exec -it callytics-api-gateway ls -la /app/temp/
```

### 3. 디스크 사용량 모니터링
```bash
# 호스트에서 확인
du -sh ./temp ./logs ./.cache

# 컨테이너 내부에서 확인
docker exec -it callytics-api-gateway du -sh /app/temp /app/logs /app/.cache
```

## 🚨 주의사항

### Windows 경로 문제
```yaml
# ❌ Windows에서 문제 발생 가능
volumes:
  - C:\silent\Callytics\temp:/app/temp

# ✅ 상대 경로 사용 권장
volumes:
  - ./temp:/app/temp
```

### 권한 문제 해결  
```dockerfile
# Dockerfile에서 권한 설정
RUN chmod 755 /app/temp /app/logs /app/.cache
RUN chown -R app:app /app/temp /app/logs /app/.cache
```

### 디스크 공간 관리
```yaml
# 로그 로테이션 설정
logging:
  driver: "json-file"
  options:
    max-size: "100m"
    max-file: "3"
```

## 📊 마운트 상태 점검 스크립트

```python
#!/usr/bin/env python3
"""볼륨 마운트 상태 점검"""

import os
import json
from pathlib import Path

def check_mount_status():
    """마운트 상태 확인"""
    mount_points = {
        "audio": "/app/audio",
        "temp": "/app/temp", 
        "logs": "/app/logs",
        "data": "/app/data",
        "cache": "/app/.cache",
        "config": "/app/config",
        "database": "/app/Callytics_new.sqlite"
    }
    
    status = {}
    for name, path in mount_points.items():
        try:
            if os.path.exists(path):
                if os.path.isfile(path):
                    status[name] = {"exists": True, "type": "file", "size": os.path.getsize(path)}
                else:
                    status[name] = {"exists": True, "type": "directory", "writable": os.access(path, os.W_OK)}
            else:
                status[name] = {"exists": False, "error": "Path not found"}
        except Exception as e:
            status[name] = {"exists": False, "error": str(e)}
    
    return status

if __name__ == "__main__":
    result = check_mount_status()
    print(json.dumps(result, indent=2))
```

## 🔧 자동 수정 도구

### Docker Compose 업데이트
```bash
# 모든 서비스의 볼륨 마운트 표준화
python tools/fix_volume_mounts.py

# 설정 검증
python tools/validate_mounts.py
```

이 가이드를 따르면 **파일 손실 방지**, **캐시 효율성 향상**, **디버깅 용이성**을 확보할 수 있습니다. 