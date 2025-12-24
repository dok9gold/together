from fastapi import APIRouter
from typing import List
from app.service.chef.model.cart import CartItem, CartAddRequest, CartAddResponse
from app.service.chef.cart import CartService

router = APIRouter(prefix="/cart", tags=["cart"])

# Service 인스턴스
cart_service = CartService()


@router.get("", response_model=List[CartItem])
async def get_cart():
    """
    장바구니 조회

    현재 장바구니에 담긴 아이템 목록을 반환합니다.
    """
    return await cart_service.get_items()


@router.post("/add", response_model=CartAddResponse)
async def add_to_cart(request: CartAddRequest):
    """
    장바구니에 아이템 추가

    선택한 재료들을 장바구니에 추가합니다.
    """
    return await cart_service.add_items(request)
