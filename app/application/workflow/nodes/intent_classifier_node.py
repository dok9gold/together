"""IntentClassifierNode - 의도 분류 노드

Domain Service를 호출하는 얇은 래퍼입니다.
"""
from app.core.decorators import inject
from app.domain.services.cooking_assistant import CookingAssistantService
from app.domain.entities.cooking_state import CookingState
import logging

logger = logging.getLogger(__name__)


class IntentClassifierNode:
    """의도 분류 노드 (Domain Service 호출하는 얇은 래퍼)

    책임:
    - LangGraph 노드 시그니처에 맞게 변환
    - Domain Service에 위임
    - 워크플로우 전용 로직 (로깅, 모니터링 등)

    ❌ 비즈니스 로직은 여기 작성하지 말 것!
       → CookingAssistantService에 위임

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
        """LangGraph 노드 실행 (callable 객체)

        Args:
            state: 현재 워크플로우 상태

        Returns:
            CookingState: 업데이트된 상태
        """
        # 워크플로우 전용 로직 (선택)
        logger.info(f"[Node:IntentClassifier] 시작: {state['user_query'][:50]}...")

        # ✅ Domain Service 호출 (핵심 비즈니스 로직)
        result = await self.cooking_assistant.classify_intent(state)

        # 워크플로우 전용 로직 (선택)
        logger.info(
            f"[Node:IntentClassifier] 완료: "
            f"intent={result['primary_intent']}, "
            f"confidence={result['confidence']}"
        )

        return result
