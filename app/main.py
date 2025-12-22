from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.front.route import mount_static

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

# API 라우터 등록 (나중에 추가)
# from app.api import router as api_router
# app.include_router(api_router, prefix="/api")

# Static 파일 서빙 (맨 마지막에 등록)
mount_static(app)
