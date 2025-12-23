from fastapi import APIRouter
from typing import List
from app.service.model.discount import (
    DiscountItem,
    DiscountRecommendRequest,
    DiscountRecommendResponse
)
from app.service.discount import DiscountService

router = APIRouter(prefix="/discount", tags=["discount"])

# Service 인스턴스
discount_service = DiscountService()


@router.get("/today", response_model=List[DiscountItem])
async def get_today_discounts():
    """
    오늘의 할인상품 조회

    현재 할인 중인 상품 목록을 반환합니다.
    """
    return await discount_service.get_today_discounts()


@router.post("/recommend", response_model=DiscountRecommendResponse)
async def get_discount_recommendations(request: DiscountRecommendRequest):
    """
    할인상품 기반 레시피 추천

    선택한 할인상품으로 만들 수 있는 요리를 추천합니다.
    """
    return await discount_service.get_recommendations(request)
