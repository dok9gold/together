from typing import List
from app.service.chef.model.discount import (
    DiscountItem,
    DiscountRecommendRequest,
    DiscountRecommendResponse,
    DiscountRecipeItem
)
from app.service.chef.model.common import DiscountInfo


# 오늘의 할인상품 Mock
MOCK_DISCOUNT_ITEMS = [
    DiscountItem(name='들기름', discountRate='50%'),
    DiscountItem(name='삼겹살', discountRate='30%'),
    DiscountItem(name='고추장', discountRate='20%'),
    DiscountItem(name='두부', discountRate='1+1'),
]

# 할인상품 연관 레시피 Mock
MOCK_DISCOUNT_RECIPES = [
    DiscountRecipeItem(
        id='1',
        name='삼겹살 김치찌개',
        cookTime='30분',
        difficulty='쉬움',
        ingredients=['삼겹살', '김치', '두부', '대파', '고춧가루'],
        steps=['삼겹살을 먹기 좋게 썬다', '김치와 함께 볶는다', '물을 붓고 끓인다', '두부와 대파를 넣는다'],
        discountInfo=[DiscountInfo(item='삼겹살', rate='30%'), DiscountInfo(item='두부', rate='1+1')],
        relatedItems=['삼겹살', '두부']
    ),
    DiscountRecipeItem(
        id='2',
        name='비빔밥',
        cookTime='35분',
        difficulty='보통',
        ingredients=['밥', '고추장', '들기름', '나물', '계란'],
        steps=['나물을 준비한다', '밥 위에 올린다', '계란 프라이를 올린다', '고추장과 들기름을 넣고 비빈다'],
        discountInfo=[DiscountInfo(item='들기름', rate='50%'), DiscountInfo(item='고추장', rate='20%')],
        relatedItems=['들기름', '고추장']
    ),
    DiscountRecipeItem(
        id='3',
        name='제육볶음',
        cookTime='25분',
        difficulty='쉬움',
        ingredients=['삼겹살', '고추장', '양파', '대파', '마늘'],
        steps=['삼겹살에 양념을 버무린다', '양파와 대파를 썬다', '팬에 고기를 볶는다', '야채를 넣고 함께 볶는다'],
        discountInfo=[DiscountInfo(item='삼겹살', rate='30%'), DiscountInfo(item='고추장', rate='20%')],
        relatedItems=['삼겹살', '고추장']
    ),
    DiscountRecipeItem(
        id='4',
        name='두부조림',
        cookTime='20분',
        difficulty='쉬움',
        ingredients=['두부', '간장', '고춧가루', '대파', '마늘'],
        steps=['두부를 도톰하게 썬다', '팬에 노릇하게 굽는다', '양념장을 끼얹는다', '대파를 올려 마무리'],
        discountInfo=[DiscountInfo(item='두부', rate='1+1')],
        relatedItems=['두부']
    ),
]


class DiscountService:
    """할인상품 서비스"""

    async def get_today_discounts(self) -> List[DiscountItem]:
        """오늘의 할인상품 조회 (Mock)"""
        return MOCK_DISCOUNT_ITEMS

    async def get_recommendations(self, request: DiscountRecommendRequest) -> DiscountRecommendResponse:
        """할인상품 기반 레시피 추천 (Mock)"""
        selected_items = set(request.items)

        # 선택한 할인상품과 관련된 레시피 필터링
        recipes = [
            r for r in MOCK_DISCOUNT_RECIPES
            if any(item in selected_items for item in r.relatedItems)
        ]

        # 결과가 없으면 일부 반환
        if not recipes:
            recipes = MOCK_DISCOUNT_RECIPES[:2]

        return DiscountRecommendResponse(recipes=recipes)
