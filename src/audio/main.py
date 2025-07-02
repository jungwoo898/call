#!/usr/bin/env python3
"""
Callytics 오디오 처리 서비스
오디오 파일 전처리, 노이즈 제거, 음성 강화
"""

import os
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager

# 오디오 처리 모듈 import
from . import preprocessing, processing, io

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    logger.info("🎵 Callytics 오디오 처리 서비스 시작")
    yield
    logger.info("🛑 Callytics 오디오 처리 서비스 종료")

app = FastAPI(title="Callytics Audio Processor", version="1.0.0", lifespan=lifespan)

class AudioProcessor:
    """오디오 처리기"""
    
    def __init__(self):
        self.device = os.getenv('DEVICE', 'cpu')
        logger.info(f"오디오 처리기 초기화 (디바이스: {self.device})")
    
    async def preprocess_audio(self, audio_path: str) -> Dict[str, Any]:
        """오디오 전처리"""
        try:
            logger.info(f"오디오 전처리 시작: {audio_path}")
            
            # 1. 오디오 로드
            audio_data = io.load_audio(audio_path)
            
            # 2. 노이즈 제거
            denoised_audio = preprocessing.remove_noise(audio_data)
            
            # 3. 음성 강화
            enhanced_audio = preprocessing.enhance_speech(denoised_audio)
            
            # 4. 정규화
            normalized_audio = preprocessing.normalize_audio(enhanced_audio)
            
            # 5. 처리된 오디오 저장
            processed_path = audio_path.replace('.wav', '_processed.wav')
            io.save_audio(normalized_audio, processed_path)
            
            logger.info(f"오디오 전처리 완료: {processed_path}")
            
            return {
                "original_path": audio_path,
                "processed_path": processed_path,
                "status": "success",
                "processing_info": {
                    "noise_removed": True,
                    "speech_enhanced": True,
                    "normalized": True
                }
            }
            
        except Exception as e:
            error_msg = f"오디오 전처리 실패: {e}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

# 오디오 처리기 인스턴스
processor = AudioProcessor()

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    try:
        import psutil
        
        return JSONResponse({
            "status": "healthy",
            "service": "audio-processor",
            "device": processor.device,
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent
            }
        })
    except Exception as e:
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e)
        }, status_code=500)

@app.get("/metrics")
async def get_metrics():
    """메트릭 엔드포인트"""
    try:
        import psutil
        
        return JSONResponse({
            "service": "audio-processor",
            "device": processor.device,
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_gb": psutil.virtual_memory().available / 1024**3,
            "disk_usage_percent": psutil.disk_usage('/').percent
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/preprocess")
async def preprocess_audio(data: Dict[str, Any]):
    """오디오 전처리 엔드포인트"""
    try:
        audio_path = data.get('audio_path')
        if not audio_path:
            raise HTTPException(status_code=400, detail="audio_path가 필요합니다")
        
        if not os.path.exists(audio_path):
            raise HTTPException(status_code=404, detail=f"오디오 파일을 찾을 수 없습니다: {audio_path}")
        
        result = await processor.preprocess_audio(audio_path)
        return JSONResponse(result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Callytics 오디오 처리 서비스가 실행 중입니다",
        "version": "1.0.0",
        "device": processor.device,
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "preprocess": "/preprocess",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001) 