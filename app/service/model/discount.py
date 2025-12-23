from pydantic import BaseModel
from typing import List
from .common import RecipeItem


class DiscountItem(BaseModel):
    """오늘의 할인상품"""
    name: str
    discountRate: str  # "50%", "30%", "1+1" 등


class DiscountRecommendRequest(BaseModel):
    """할인상품 기반 추천 요청"""
    items: List[str]


class DiscountRecipeItem(RecipeItem):
    """할인상품 연관 레시피"""
    relatedItems: List[str]  # 선택한 할인상품과 매칭되는 재료


class DiscountRecommendResponse(BaseModel):
    """할인상품 기반 추천 응답"""
    recipes: List[DiscountRecipeItem]
