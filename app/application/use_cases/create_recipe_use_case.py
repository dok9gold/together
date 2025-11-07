"""CreateRecipeUseCase - 레시피 생성 유스케이스

워크플로우를 실행하여 레시피를 생성합니다.
"""
from app.application.workflow.cooking_workflow import CookingWorkflow
from app.domain.entities.cooking_state import CookingState
import logging

logger = logging.getLogger(__name__)


class CreateRecipeUseCase:
    """레시피 생성 유스케이스

    책임:
    - 초기 상태 생성
    - 워크플로우 실행
    - 결과 반환

    Attributes:
        workflow: LangGraph 워크플로우
    """

    def __init__(self, workflow: CookingWorkflow):
        """의존성 주입: 워크플로우

        Args:
            workflow: 요리 AI 어시스턴트 워크플로우
        """
        self.workflow = workflow

    async def execute(self, query: str) -> CookingState:
        """레시피 생성 워크플로우 실행

        전체 워크플로우:
        1. 의도 분류
        2. 의도에 따라 분기 (레시피/추천/질문)
        3. 레시피 생성 시 이미지 생성
        4. Secondary intents 처리 (복합 의도)

        Args:
            query: 사용자 쿼리
                예: "파스타 카르보나라 만드는 법"

        Returns:
            CookingState: 최종 상태 (레시피, 이미지 URL 등 포함)
        """
        logger.info(f"[UseCase] 실행 시작: {query[:50]}...")

        # 초기 상태 생성
        initial_state: CookingState = {
            "user_query": query,
            "primary_intent": "",
            "secondary_intents": [],
            "entities": {},
            "confidence": 0.0,
            "recipe_text": "",
            "recipes": [],
            "dish_names": [],
            "recommendation": "",
            "answer": "",
            "image_prompt": "",
            "image_url": None,
            "image_urls": [],
            "error": None
        }

        # 워크플로우 실행
        result = await self.workflow.run(initial_state)

        logger.info(f"[UseCase] 실행 완료")

        return result
