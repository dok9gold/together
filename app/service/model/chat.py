from pydantic import BaseModel
from typing import List, Optional, Literal, Any
from app.service.model.common import RecipeItem


class ChatRequest(BaseModel):
    """채팅 요청"""
    message: str


class ChatAction(BaseModel):
    """채팅 응답 액션 버튼"""
    label: str
    type: Literal['recipe', 'cart', 'ingredients']
    data: Optional[Any] = None


class ChatResponse(BaseModel):
    """채팅 응답"""
    content: str
    recipes: Optional[List[RecipeItem]] = None
    actions: Optional[List[ChatAction]] = None
