from app.service.model.fridge import (
    FridgeRecommendRequest,
    FridgeRecommendResponse,
    FridgeRecipeItem
)
from app.service.model.common import DiscountInfo


# 냉장고 재료 기반 레시피 Mock
MOCK_FRIDGE_RECIPES = [
    FridgeRecipeItem(
        id='1',
        name='김치찌개',
        cookTime='30분',
        difficulty='쉬움',
        ingredients=['삼겹살', '김치', '두부', '대파', '고춧가루'],
        steps=['삼겹살을 먹기 좋게 썬다', '김치와 함께 볶는다', '물을 붓고 끓인다', '두부와 대파를 넣는다'],
        discountInfo=[DiscountInfo(item='삼겹살', rate='30%')],
        requiredIngredients=['김치', '삼겹살']
    ),
    FridgeRecipeItem(
        id='2',
        name='계란말이',
        cookTime='15분',
        difficulty='쉬움',
        ingredients=['계란', '대파', '당근', '소금'],
        steps=['계란을 풀어 소금 간을 한다', '대파와 당근을 잘게 썬다', '팬에 기름을 두르고 계란물을 붓는다', '돌돌 말아가며 익힌다'],
        discountInfo=None,
        requiredIngredients=['계란']
    ),
    FridgeRecipeItem(
        id='3',
        name='제육볶음',
        cookTime='25분',
        difficulty='쉬움',
        ingredients=['삼겹살', '고추장', '양파', '대파', '마늘'],
        steps=['삼겹살에 양념을 버무린다', '양파와 대파를 썬다', '팬에 고기를 볶는다', '야채를 넣고 함께 볶는다'],
        discountInfo=[DiscountInfo(item='고추장', rate='20%')],
        requiredIngredients=['삼겹살', '양파']
    ),
    FridgeRecipeItem(
        id='4',
        name='두부조림',
        cookTime='20분',
        difficulty='쉬움',
        ingredients=['두부', '간장', '고춧가루', '대파', '마늘'],
        steps=['두부를 도톰하게 썬다', '팬에 노릇하게 굽는다', '양념장을 끼얹는다', '대파를 올려 마무리'],
        discountInfo=[DiscountInfo(item='두부', rate='1+1')],
        requiredIngredients=['두부']
    ),
    FridgeRecipeItem(
        id='5',
        name='김치볶음밥',
        cookTime='15분',
        difficulty='쉬움',
        ingredients=['밥', '김치', '계란', '대파', '참기름'],
        steps=['김치를 잘게 썬다', '팬에 김치를 볶는다', '밥을 넣고 함께 볶는다', '계란 프라이를 올려 완성'],
        discountInfo=None,
        requiredIngredients=['김치', '계란']
    ),
]


class FridgeService:
    """냉장고 털기 서비스"""

    async def get_recommendations(self, request: FridgeRecommendRequest) -> FridgeRecommendResponse:
        """냉장고 재료 기반 레시피 추천 (Mock)"""
        user_ingredients = set(request.ingredients)

        # 선택한 재료로 만들 수 있는 레시피 필터링
        recipes = [
            r for r in MOCK_FRIDGE_RECIPES
            if any(req in user_ingredients for req in r.requiredIngredients)
        ]

        # 결과가 없으면 일부 반환
        if not recipes:
            recipes = MOCK_FRIDGE_RECIPES[:2]

        return FridgeRecommendResponse(recipes=recipes)
