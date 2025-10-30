from pydantic import BaseModel, Field
from typing import Optional, List


class CookingRequest(BaseModel):
    """요리 관련 요청 (레시피 생성, 추천, 질문 등)"""
    query: str = Field(..., description="요리 관련 쿼리 (예: '파스타 카르보나라 만드는 법', '매운 음식 추천해줘', '김치찌개 칼로리는?')")


class RecipeData(BaseModel):
    """레시피 데이터"""
    title: str
    ingredients: List[str]
    steps: List[str]
    cooking_time: str
    difficulty: str


class CookingResponse(BaseModel):
    """요리 관련 응답 (의도에 따라 다른 데이터 반환)"""
    status: str = Field(..., description="success 또는 error")
    intent: Optional[str] = Field(None, description="사용자 의도 (recipe_create, recommend, question)")
    data: Optional[dict] = None
    message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "intent": "recipe_create",
                "data": {
                    "recipe": {
                        "title": "파스타 카르보나라",
                        "ingredients": ["파스타 200g", "베이컨 100g", "달걀 2개"],
                        "steps": ["1. 파스타를 삶는다", "2. 베이컨을 볶는다"],
                        "cooking_time": "30분",
                        "difficulty": "중"
                    },
                    "image_url": "https://replicate.delivery/..."
                }
            }
        }