from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="마트 AI 요리 도우미",
    description="할인상품 기반 레시피 추천 시스템",
    version="0.1.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
from app.api import router as api_router
app.include_router(api_router)

# 프론트 라우터 등록 (clean URL)
from app.front.route import router as front_router
app.include_router(front_router)

# Static 파일 서빙 (JS, CSS, 이미지 등 - 맨 마지막에 등록)
app.mount("/static", StaticFiles(directory="app/front/static"), name="static")
