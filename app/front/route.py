from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter()

STATIC_DIR = "app/front/static/chef"


@router.get("/")
async def index():
    """메인 페이지 → smart.html"""
    return FileResponse(os.path.join(STATIC_DIR, "pages/smart.html"))


@router.get("/smart")
async def smart():
    """스마트 AI 메인"""
    return FileResponse(os.path.join(STATIC_DIR, "pages/smart.html"))


@router.get("/chat")
async def chat():
    """AI 채팅"""
    return FileResponse(os.path.join(STATIC_DIR, "pages/chat.html"))


@router.get("/recommend")
async def recommend():
    """요리 추천"""
    return FileResponse(os.path.join(STATIC_DIR, "pages/recommend.html"))


@router.get("/recipe")
async def recipe():
    """레시피 검색"""
    return FileResponse(os.path.join(STATIC_DIR, "pages/recipe.html"))


@router.get("/discount")
async def discount():
    """할인상품 추천"""
    return FileResponse(os.path.join(STATIC_DIR, "pages/discount.html"))


@router.get("/fridge")
async def fridge():
    """냉장고 털기"""
    return FileResponse(os.path.join(STATIC_DIR, "pages/fridge.html"))
