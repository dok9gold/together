"""Chef 채팅 서비스 - LangGraph 워크플로우 연동"""

from core.llm import LLMProvider
from app.service.chef.model.chat import ChatRequest, ChatResponse
from app.service.chef.model.common import RecipeItem, DiscountInfo
from app.workflow.chef.graph import ChefWorkflow


class ChatService:
    """채팅 서비스 - ChefWorkflow 연동"""

    def __init__(self, llm: LLMProvider):
        self.workflow = ChefWorkflow(llm)

    async def send_message(self, request: ChatRequest) -> ChatResponse:
        """채팅 메시지 처리

        Args:
            request: ChatRequest (message, session_id)

        Returns:
            ChatResponse (session_id, content, recipes)
        """
        # 워크플로우 실행
        state, session_id, message_id = await self.workflow.run(
            user_input=request.message,
            session_id=request.session_id
        )

        # State → ChatResponse 변환
        recipes = self._convert_recipes(state.get("recipes", []))

        return ChatResponse(
            session_id=session_id,
            content=state.get("response", ""),
            recipes=recipes if recipes else None
        )

    def _convert_recipes(self, state_recipes: list[dict]) -> list[RecipeItem]:
        """State의 recipes를 RecipeItem 리스트로 변환"""
        result = []
        for recipe in state_recipes:
            # 레시피에 포함된 discount_items에서 DiscountInfo 생성
            discount_items = recipe.get("discount_items", [])
            discount_info = [
                DiscountInfo(
                    item=d.get("name", ""),
                    rate=f"{d.get('discount_rate')}%" if d.get("discount_rate") else d.get("discount_type", "")
                )
                for d in discount_items
            ] if discount_items else None

            result.append(RecipeItem(
                id=recipe.get("id", ""),
                name=recipe.get("name", ""),
                cookTime=recipe.get("time", ""),
                difficulty=recipe.get("difficulty", "보통"),
                ingredients=recipe.get("ingredients", []),
                steps=recipe.get("steps", []),
                discountInfo=discount_info
            ))
        return result
