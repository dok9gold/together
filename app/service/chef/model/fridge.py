from pydantic import BaseModel
from typing import List, Optional
from .common import RecipeItem, DiscountInfo


class FridgeRecommendRequest(BaseModel):
    """냉장고 재료 기반 추천 요청"""
    ingredients: List[str]


class FridgeRecipeItem(RecipeItem):
    """냉장고 재료 연관 레시피"""
    requiredIngredients: List[str]  # 필수 재료 (매칭에 사용)


class FridgeRecommendResponse(BaseModel):
    """냉장고 재료 기반 추천 응답"""
    recipes: List[FridgeRecipeItem]
