import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.database.postgres.connection import PostgresDatabase
from core.database.registry import DatabaseRegistry
from core.llm import LLMProvider, ClaudeLLM, GeminiLLM

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 리소스 관리"""

    # ========== 시작 시 초기화 ==========

    # 1. DB 커넥션풀 초기화
    # DATABASE_URL 우선, 없으면 개별 환경변수 사용
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        db_config = {
            'dsn': database_url,
            'pool': {'min_size': 2, 'max_size': 10}
        }
    else:
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'database': os.getenv('DB_NAME', 'together'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'pool': {'min_size': 2, 'max_size': 10}
        }
    db = await PostgresDatabase.create('main', db_config)
    DatabaseRegistry.register('main', db)
    app.state.db = db

    # 2. LLM Provider 초기화
    llm_provider = LLMProvider(default_provider="claude")

    # Claude 등록
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        llm_provider.register("claude", ClaudeLLM(api_key=anthropic_key))

    # Gemini 등록 (키가 있을 때만)
    google_key = os.getenv("GOOGLE_API_KEY")
    if google_key:
        llm_provider.register("gemini", GeminiLLM(api_key=google_key))

    app.state.llm = llm_provider

    logger.info("Application started")

    yield

    # ========== 종료 시 정리 ==========
    await DatabaseRegistry.close_all()
    logger.info("Application shutdown")


app = FastAPI(
    title="마트 AI 요리 도우미",
    description="할인상품 기반 레시피 추천 시스템",
    version="0.1.0",
    lifespan=lifespan
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
