from app.service.model.chat import ChatRequest, ChatResponse, ChatAction


class ChatService:
    """채팅 서비스"""

    async def send_message(self, request: ChatRequest) -> ChatResponse:
        """채팅 메시지 처리 (Mock)"""
        # TODO: AI 워크플로우 연동
        message = request.message.lower()

        # 간단한 Mock 응답
        if '레시피' in message or '만드는 법' in message:
            return ChatResponse(
                content="김치찌개 레시피를 알려드릴게요! 돼지고기, 김치, 두부, 대파가 필요해요.",
                actions=[
                    ChatAction(label="레시피 보기", type="recipe", data={"id": "1"}),
                    ChatAction(label="재료 담기", type="cart", data={"items": ["돼지고기", "김치", "두부", "대파"]})
                ]
            )
        elif '추천' in message:
            return ChatResponse(
                content="오늘은 제육볶음 어떠세요? 지금 삼겹살이 30% 할인 중이에요!",
                actions=[
                    ChatAction(label="레시피 보기", type="recipe", data={"id": "3"}),
                    ChatAction(label="재료 담기", type="cart", data={"items": ["삼겹살", "고추장", "양파"]})
                ]
            )
        else:
            return ChatResponse(
                content="안녕하세요! 요리에 대해 궁금한 점이 있으시면 물어보세요. 레시피 추천도 해드릴 수 있어요!",
                actions=None
            )
