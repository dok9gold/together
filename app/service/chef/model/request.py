"""Chef 요청 모델"""

from pydantic import BaseModel


class DiscountItem(BaseModel):
    """할인 상품"""
    name: str      # 상품 대표명
    barcode: str   # 상품 판매코드


class ChefRequest(BaseModel):
    """Chef AI 요청"""
    user_input: str
    discount_items: list[DiscountItem] | None = None
