"""RecipeGeneratorNode - 레시피 생성 노드

Domain Service를 호출하는 얇은 래퍼입니다.
"""
from app.core.decorators import inject
from app.domain.services.cooking_assistant import CookingAssistantService
from app.domain.entities.cooking_state import CookingState
import logging

logger = logging.getLogger(__name__)


class RecipeGeneratorNode:
    """레시피 생성 노드 (Domain Service 호출하는 얇은 래퍼)

    Attributes:
        cooking_assistant: 도메인 서비스
    """

    @inject
    def __init__(self, cooking_assistant: CookingAssistantService):
        """의존성 주입: Domain Service

        Args:
            cooking_assistant: 요리 AI 어시스턴트 도메인 서비스
        """
        self.cooking_assistant = cooking_assistant

    async def __call__(self, state: CookingState) -> CookingState:
        """LangGraph 노드 실행

        Args:
            state: 현재 워크플로우 상태

        Returns:
            CookingState: 업데이트된 상태
        """
        logger.info(f"[Node:RecipeGenerator] 시작")

        # ✅ Domain Service 호출
        result = await self.cooking_assistant.generate_recipe(state)

        logger.info(f"[Node:RecipeGenerator] 완료: {result.get('dish_names', [])}")

        return result
