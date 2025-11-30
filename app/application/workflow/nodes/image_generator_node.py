"""ImageGeneratorNode - 이미지 생성 노드

Domain Service를 호출하는 얇은 래퍼입니다.
"""
from app.core.decorators import inject
from app.domain.services.cooking_assistant import CookingAssistantService
from app.domain.entities.cooking_state import CookingState
import logging

logger = logging.getLogger(__name__)


class ImageGeneratorNode:
    """이미지 생성 노드 (Domain Service 호출하는 얇은 래퍼)

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
        logger.info(f"[Node:ImageGenerator] 시작")

        # ✅ Domain Service 호출
        result = await self.cooking_assistant.generate_image(state)

        if result.get("image_url"):
            logger.info(f"[Node:ImageGenerator] 완료: {result['image_url']}")
        else:
            logger.info(f"[Node:ImageGenerator] 완료: 이미지 없음")

        return result
