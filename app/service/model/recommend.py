from pydantic import BaseModel
from typing import List, Optional
from .common import RecipeItem


class RecommendRequest(BaseModel):
    """요리 추천 요청"""
    categories: List[str]
    condition: Optional[str] = None


class RecommendResponse(BaseModel):
    """요리 추천 응답"""
    recipes: List[RecipeItem]
