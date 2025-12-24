# Chef API routes
from fastapi import APIRouter
from app.api.chef import chat, recommend, recipe, discount, fridge, cart

router = APIRouter(prefix="/chef", tags=["chef"])

# 각 도메인별 라우터 등록
router.include_router(chat.router)
router.include_router(recommend.router)
router.include_router(recipe.router)
router.include_router(discount.router)
router.include_router(fridge.router)
router.include_router(cart.router)
