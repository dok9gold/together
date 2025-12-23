from pydantic import BaseModel
from typing import List, Optional


class DiscountInfo(BaseModel):
    """할인 정보"""
    item: str
    rate: str


class RecipeItem(BaseModel):
    """레시피 기본 정보"""
    id: str
    name: str
    cookTime: str
    difficulty: str
    ingredients: List[str]
    steps: List[str]
    discountInfo: Optional[List[DiscountInfo]] = None
