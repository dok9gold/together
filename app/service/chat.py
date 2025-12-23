from app.service.model.chat import ChatRequest, ChatResponse
from app.service.model.common import RecipeItem, DiscountInfo


class ChatService:
    """채팅 서비스"""

    async def send_message(self, request: ChatRequest) -> ChatResponse:
        """채팅 메시지 처리 (Mock)"""
        # TODO: AI 워크플로우 연동
        message = request.message.lower()

        # 간단한 Mock 응답
        if '레시피' in message or '만드는 법' in message:
            return ChatResponse(
                content="김치찌개 레시피를 알려드릴게요!",
                recipes=[
                    RecipeItem(
                        id="1",
                        name="김치찌개",
                        cookTime="30분",
                        difficulty="쉬움",
                        ingredients=["돼지고기", "김치", "두부", "대파", "고춧가루"],
                        steps=["돼지고기를 볶는다", "김치를 넣고 같이 볶는다", "물을 붓고 끓인다", "두부와 대파를 넣는다"],
                        discountInfo=[DiscountInfo(item="돼지고기", rate="30%")]
                    )
                ]
            )
        elif '추천' in message:
            return ChatResponse(
                content="오늘의 할인상품으로 만들 수 있는 요리를 추천해드릴게요! 삼겹살이 30% 할인 중이에요.",
                recipes=[
                    RecipeItem(
                        id="3",
                        name="제육볶음",
                        cookTime="25분",
                        difficulty="쉬움",
                        ingredients=["삼겹살", "고추장", "양파", "대파", "마늘"],
                        steps=["삼겹살을 먹기 좋게 썬다", "양념장을 만든다", "팬에 고기와 양념을 볶는다", "채소를 넣고 마무리"],
                        discountInfo=[DiscountInfo(item="삼겹살", rate="30%")]
                    ),
                    RecipeItem(
                        id="4",
                        name="삼겹살 김치찌개",
                        cookTime="35분",
                        difficulty="쉬움",
                        ingredients=["삼겹살", "김치", "두부", "대파", "고춧가루"],
                        steps=["삼겹살을 볶는다", "김치를 넣고 볶는다", "물을 붓고 끓인다", "두부와 대파를 넣는다"],
                        discountInfo=[DiscountInfo(item="삼겹살", rate="30%")]
                    )
                ]
            )
        else:
            return ChatResponse(
                content="안녕하세요! 요리에 대해 궁금한 점이 있으시면 물어보세요. '추천해줘'라고 하시면 오늘의 할인상품으로 만들 수 있는 요리를 추천해드릴게요!",
                recipes=None
            )
