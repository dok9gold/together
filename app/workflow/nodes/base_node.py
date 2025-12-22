"""BaseNode - LangGraph 노드 베이스 클래스

워크플로우 공통 로직을 처리하는 추상 클래스입니다.
"""
from abc import ABC, abstractmethod
from app.cooking_assistant.workflow.states.cooking_state import CookingState
import logging

logger = logging.getLogger(__name__)


class BaseNode(ABC):
    """LangGraph 노드 베이스 클래스

    책임:
    - Secondary intent 공통 처리
    - 로깅 공통 처리
    - 하위 클래스는 execute()만 구현

    Attributes:
        intent_name: 이 노드가 처리하는 intent 이름
                     빈 문자열이면 secondary intent 처리 스킵
    """

    def __init__(self, intent_name: str = ""):
        """
        Args:
            intent_name: 이 노드가 처리하는 intent 이름
                         예: "recipe_create", "recommend", "question", "generate_image"
                         빈 문자열("")이면 secondary intent 처리 안함
        """
        self.intent_name = intent_name

    async def __call__(self, state: CookingState) -> CookingState:
        """LangGraph 노드 실행 (공통 로직)

        1. Secondary intent 처리 (자신의 intent 제거)
        2. 하위 클래스의 execute() 호출
        3. 공통 로깅

        Args:
            state: 현재 워크플로우 상태

        Returns:
            CookingState: 업데이트된 상태
        """
        # 1. Secondary intent 처리 (워크플로우 상태 관리)
        self._handle_secondary_intent(state)

        # 2. 노드 고유 기능 실행
        logger.info(f"[Node:{self.__class__.__name__}] 시작")
        result = await self.execute(state)
        logger.info(f"[Node:{self.__class__.__name__}] 완료")

        return result

    def _handle_secondary_intent(self, state: CookingState) -> None:
        """Secondary intent 처리 (공통 로직)

        자신의 intent_name과 일치하는 첫 번째 secondary intent를 제거하고,
        처리된 것으로 기록합니다.
        intent_name이 빈 문자열이면 아무것도 하지 않습니다.

        Args:
            state: 현재 워크플로우 상태
        """
        # intent_name이 비어있으면 스킵 (IntentClassifierNode용)
        if not self.intent_name:
            return

        secondary_intents = state.get("secondary_intents", [])

        if secondary_intents and secondary_intents[0] == self.intent_name:
            # 제거하기 전에 처리된 것으로 기록
            processed_intent = secondary_intents.pop(0)

            processed_list = state.get("processed_secondary_intents", [])
            processed_list.append(processed_intent)
            state["processed_secondary_intents"] = processed_list

            logger.info(
                f"[{self.__class__.__name__}] "
                f"Secondary intent '{self.intent_name}' 처리 완료 및 기록"
            )

    @abstractmethod
    async def execute(self, state: CookingState) -> CookingState:
        """노드 고유 비즈니스 로직

        하위 클래스에서 반드시 구현해야 함.
        Domain Service 호출 등의 로직 수행.

        Args:
            state: 현재 워크플로우 상태

        Returns:
            CookingState: 업데이트된 상태
        """
        pass
