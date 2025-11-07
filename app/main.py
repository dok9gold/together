import os
import logging
from dotenv import load_dotenv

# 환경 변수 로드 (다른 import 전에 먼저 실행)
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import get_settings

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 설정 로드
settings = get_settings()

# FastAPI 앱 생성 (설정 기반)
app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
    version=settings.app_version
)

# CORS 설정 (설정 기반)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(router, prefix="/api", tags=["cooking"])


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Cooking Assistant API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )