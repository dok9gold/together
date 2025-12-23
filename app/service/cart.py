from typing import List
from app.service.model.cart import CartItem, CartAddRequest, CartAddResponse


# 메모리 기반 장바구니 (Mock)
# 실제 구현에서는 DB 또는 세션 기반으로 변경
_cart_items: List[CartItem] = []


class CartService:
    """장바구니 서비스"""

    async def get_items(self) -> List[CartItem]:
        """장바구니 조회 (Mock)"""
        return _cart_items

    async def add_items(self, request: CartAddRequest) -> CartAddResponse:
        """장바구니에 아이템 추가 (Mock)"""
        global _cart_items

        for item in request.items:
            # 이미 있는 아이템인지 확인
            existing = next((i for i in _cart_items if i.name == item.name), None)
            if existing:
                # 수량 업데이트
                existing.quantity = (existing.quantity or 1) + (item.quantity or 1)
            else:
                # 새 아이템 추가
                _cart_items.append(item)

        return CartAddResponse(success=True)

    async def clear(self) -> None:
        """장바구니 비우기 (Mock)"""
        global _cart_items
        _cart_items = []
