from app.service.model.recommend import RecommendRequest, RecommendResponse
from app.service.model.common import RecipeItem, DiscountInfo


# Mock 레시피 데이터
MOCK_RECIPES = {
    '한식': [
        RecipeItem(
            id='1',
            name='김치찌개',
            cookTime='30분',
            difficulty='쉬움',
            ingredients=['돼지고기', '김치', '두부', '대파', '고춧가루'],
            steps=['돼지고기를 볶는다', '김치를 넣고 볶는다', '물을 붓고 끓인다', '두부와 대파를 넣는다'],
            discountInfo=[DiscountInfo(item='돼지고기', rate='30%')]
        ),
        RecipeItem(
            id='2',
            name='된장찌개',
            cookTime='25분',
            difficulty='쉬움',
            ingredients=['된장', '두부', '애호박', '감자', '대파'],
            steps=['감자와 애호박을 썬다', '된장을 풀어 끓인다', '야채를 넣고 끓인다', '두부를 넣고 마무리'],
            discountInfo=[DiscountInfo(item='두부', rate='1+1')]
        ),
        RecipeItem(
            id='3',
            name='제육볶음',
            cookTime='25분',
            difficulty='쉬움',
            ingredients=['삼겹살', '고추장', '양파', '대파', '마늘'],
            steps=['삼겹살을 양념에 버무린다', '팬을 달군다', '고기를 볶는다', '야채를 넣고 볶는다'],
            discountInfo=[DiscountInfo(item='삼겹살', rate='30%'), DiscountInfo(item='고추장', rate='20%')]
        ),
    ],
    '중식': [
        RecipeItem(
            id='4',
            name='짜장면',
            cookTime='40분',
            difficulty='보통',
            ingredients=['춘장', '돼지고기', '양파', '감자', '면'],
            steps=['야채를 썬다', '고기를 볶는다', '춘장을 넣고 볶는다', '면을 삶아 곁들인다'],
            discountInfo=None
        ),
    ],
    '일식': [
        RecipeItem(
            id='5',
            name='돈까스',
            cookTime='30분',
            difficulty='보통',
            ingredients=['돼지고기', '빵가루', '계란', '밀가루', '양배추'],
            steps=['고기를 두드린다', '밀가루-계란-빵가루 순으로 입힌다', '튀긴다', '양배추와 함께 담는다'],
            discountInfo=[DiscountInfo(item='돼지고기', rate='30%')]
        ),
    ],
    '양식': [
        RecipeItem(
            id='6',
            name='파스타',
            cookTime='25분',
            difficulty='쉬움',
            ingredients=['파스타면', '올리브오일', '마늘', '페퍼론치노', '파슬리'],
            steps=['면을 삶는다', '마늘을 볶는다', '면을 넣고 볶는다', '파슬리로 마무리'],
            discountInfo=None
        ),
    ],
}


class RecommendService:
    """요리 추천 서비스"""

    async def get_recommendations(self, request: RecommendRequest) -> RecommendResponse:
        """카테고리 기반 요리 추천 (Mock)"""
        recipes = []

        for category in request.categories:
            if category in MOCK_RECIPES:
                recipes.extend(MOCK_RECIPES[category])

        # 조건이 있으면 필터링 (간단한 키워드 매칭)
        if request.condition:
            condition = request.condition.lower()
            if '쉬운' in condition or '간단' in condition:
                recipes = [r for r in recipes if r.difficulty == '쉬움']
            if '빠른' in condition or '30분' in condition:
                recipes = [r for r in recipes if '30' in r.cookTime or '25' in r.cookTime or '20' in r.cookTime]

        return RecommendResponse(recipes=recipes)
