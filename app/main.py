import os
from dotenv import load_dotenv

# 환경 변수 로드 (다른 import 전에 먼저 실행)
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

# FastAPI 앱 생성
app = FastAPI(
    title="Cooking Assistant API",
    description="Claude와 LangGraph를 활용한 요리 AI 어시스턴트 서비스 - 레시피 생성, 음식 추천, 요리 질문 답변",
    version="1.0.0"
)

# CORS 설정 (프론트엔드 연동)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용하도록 수정
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