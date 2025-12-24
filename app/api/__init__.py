# API routes
from fastapi import APIRouter
from app.api import chat, recommend, recipe, discount, fridge, cart, chef

router = APIRouter(prefix="/api")

# 각 도메인별 라우터 등록
router.include_router(chat.router)
router.include_router(recommend.router)
router.include_router(recipe.router)
router.include_router(discount.router)
router.include_router(fridge.router)
router.include_router(cart.router)
router.include_router(chef.router)
