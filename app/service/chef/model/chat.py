from pydantic import BaseModel
from typing import List, Optional, Literal, Any
from app.service.chef.model.common import RecipeItem


class ChatRequest(BaseModel):
    """채팅 요청"""
    message: str
    session_id: Optional[int] = None  # 첫 요청은 None, 이후 세션 유지


class ChatAction(BaseModel):
    """채팅 응답 액션 버튼"""
    label: str
    type: Literal['recipe', 'cart', 'ingredients']
    data: Optional[Any] = None


class ChatResponse(BaseModel):
    """채팅 응답"""
    session_id: int
    content: str
    recipes: Optional[List[RecipeItem]] = None
    actions: Optional[List[ChatAction]] = None
