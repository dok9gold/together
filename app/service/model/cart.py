from pydantic import BaseModel
from typing import List, Optional


class CartItem(BaseModel):
    """장바구니 아이템"""
    name: str
    quantity: Optional[int] = None
    price: Optional[int] = None
    discountRate: Optional[str] = None


class CartAddRequest(BaseModel):
    """장바구니 추가 요청"""
    items: List[CartItem]


class CartAddResponse(BaseModel):
    """장바구니 추가 응답"""
    success: bool
