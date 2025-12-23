from pydantic import BaseModel
from typing import List, Optional
from .common import RecipeItem


class RecipeSearchResponse(BaseModel):
    """레시피 검색 응답"""
    recipes: List[RecipeItem]


class IngredientDetail(BaseModel):
    """재료 상세 (분량 포함)"""
    name: str
    amount: str


class StepDetail(BaseModel):
    """조리 단계 상세"""
    order: int
    description: str
    tip: Optional[str] = None


class RecipeDetail(BaseModel):
    """레시피 상세 정보"""
    id: str
    name: str
    cookTime: str
    difficulty: str
    servings: str
    ingredients: List[IngredientDetail]
    steps: List[StepDetail]
