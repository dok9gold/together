from typing import List, Optional
from app.service.model.recipe import RecipeSearchResponse, RecipeDetail, IngredientDetail, StepDetail
from app.service.model.common import RecipeItem


# Mock 레시피 데이터
MOCK_RECIPES = [
    RecipeItem(
        id='1',
        name='김치찌개',
        cookTime='30분',
        difficulty='쉬움',
        ingredients=['돼지고기', '김치', '두부', '대파', '고춧가루'],
        steps=['돼지고기를 볶는다', '김치를 넣고 볶는다', '물을 붓고 끓인다', '두부와 대파를 넣는다']
    ),
    RecipeItem(
        id='2',
        name='된장찌개',
        cookTime='25분',
        difficulty='쉬움',
        ingredients=['된장', '두부', '애호박', '감자', '대파'],
        steps=['감자와 애호박을 썬다', '된장을 풀어 끓인다', '야채를 넣고 끓인다', '두부를 넣고 마무리']
    ),
    RecipeItem(
        id='3',
        name='제육볶음',
        cookTime='25분',
        difficulty='쉬움',
        ingredients=['삼겹살', '고추장', '양파', '대파', '마늘'],
        steps=['삼겹살을 양념에 버무린다', '팬을 달군다', '고기를 볶는다', '야채를 넣고 볶는다']
    ),
    RecipeItem(
        id='4',
        name='참치김치찌개',
        cookTime='20분',
        difficulty='쉬움',
        ingredients=['참치캔', '김치', '두부', '대파', '고춧가루'],
        steps=['참치와 김치를 볶는다', '물을 붓고 끓인다', '두부를 넣는다', '대파를 넣고 마무리']
    ),
    RecipeItem(
        id='5',
        name='순두부찌개',
        cookTime='20분',
        difficulty='쉬움',
        ingredients=['순두부', '돼지고기', '계란', '대파', '고춧가루'],
        steps=['돼지고기를 볶는다', '물과 순두부를 넣는다', '끓이면서 간을 맞춘다', '계란을 넣고 마무리']
    ),
]

MOCK_RECIPE_DETAILS = {
    '1': RecipeDetail(
        id='1',
        name='김치찌개',
        cookTime='30분',
        difficulty='쉬움',
        servings='2인분',
        ingredients=[
            IngredientDetail(name='돼지고기', amount='200g'),
            IngredientDetail(name='김치', amount='1컵'),
            IngredientDetail(name='두부', amount='1/2모'),
            IngredientDetail(name='대파', amount='1대'),
            IngredientDetail(name='고춧가루', amount='1스푼'),
        ],
        steps=[
            StepDetail(order=1, description='돼지고기를 먹기 좋은 크기로 썬다', tip='기름기 있는 부위가 더 맛있어요'),
            StepDetail(order=2, description='냄비에 돼지고기와 김치를 넣고 볶는다'),
            StepDetail(order=3, description='물 2컵을 붓고 센 불에서 끓인다'),
            StepDetail(order=4, description='두부와 대파를 넣고 5분 더 끓인다', tip='두부는 손으로 으깨 넣으면 더 맛있어요'),
        ]
    ),
    '2': RecipeDetail(
        id='2',
        name='된장찌개',
        cookTime='25분',
        difficulty='쉬움',
        servings='2인분',
        ingredients=[
            IngredientDetail(name='된장', amount='2스푼'),
            IngredientDetail(name='두부', amount='1/2모'),
            IngredientDetail(name='애호박', amount='1/4개'),
            IngredientDetail(name='감자', amount='1개'),
            IngredientDetail(name='대파', amount='1대'),
        ],
        steps=[
            StepDetail(order=1, description='감자와 애호박을 깍둑썰기한다'),
            StepDetail(order=2, description='물에 된장을 풀어 끓인다', tip='멸치육수를 쓰면 더 깊은 맛이 나요'),
            StepDetail(order=3, description='감자를 먼저 넣고 5분 끓인다'),
            StepDetail(order=4, description='애호박과 두부를 넣고 5분 더 끓인다'),
            StepDetail(order=5, description='대파를 넣고 마무리한다'),
        ]
    ),
    '3': RecipeDetail(
        id='3',
        name='제육볶음',
        cookTime='25분',
        difficulty='쉬움',
        servings='2인분',
        ingredients=[
            IngredientDetail(name='삼겹살', amount='300g'),
            IngredientDetail(name='고추장', amount='2스푼'),
            IngredientDetail(name='양파', amount='1개'),
            IngredientDetail(name='대파', amount='1대'),
            IngredientDetail(name='마늘', amount='3쪽'),
        ],
        steps=[
            StepDetail(order=1, description='삼겹살을 얇게 썰어 양념에 버무린다', tip='30분 재워두면 더 맛있어요'),
            StepDetail(order=2, description='양파와 대파를 썬다'),
            StepDetail(order=3, description='달군 팬에 고기를 볶는다'),
            StepDetail(order=4, description='고기가 익으면 야채를 넣고 함께 볶는다'),
        ]
    ),
}

# 인기 검색어 Mock
POPULAR_KEYWORDS = ['김치찌개', '된장찌개', '제육볶음', '파스타', '볶음밥']


class RecipeService:
    """레시피 서비스"""

    async def search(self, keyword: str) -> RecipeSearchResponse:
        """레시피 검색 (Mock)"""
        keyword_lower = keyword.lower()
        results = [r for r in MOCK_RECIPES if keyword_lower in r.name.lower()]
        return RecipeSearchResponse(recipes=results)

    async def get_popular_keywords(self) -> List[str]:
        """인기 검색어 조회 (Mock)"""
        return POPULAR_KEYWORDS

    async def get_detail(self, recipe_id: str) -> Optional[RecipeDetail]:
        """레시피 상세 조회 (Mock)"""
        return MOCK_RECIPE_DETAILS.get(recipe_id)
