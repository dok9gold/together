"""Intent Router - 의도 기반 라우팅 로직

조건부 엣지에서 사용하는 라우팅 함수들입니다.
"""
from app.domain.entities.cooking_state import CookingState
import logging

logger = logging.getLogger(__name__)


def route_by_intent(state: CookingState) -> str:
    """의도에 따라 다음 노드 결정 (조건부 라우팅)

    primary_intent를 기반으로 다음 노드를 선택합니다.

    Args:
        state: 현재 상태

    Returns:
        str: 다음 노드 이름
            - "recipe_generator": 레시피 생성 노드
            - "recommender": 음식 추천 노드
            - "question_answerer": 질문 답변 노드
    """
    intent = state.get("primary_intent", "recipe_create")

    routing_map = {
        "recipe_create": "recipe_generator",
        "recommend": "recommender",
        "question": "question_answerer"
    }

    next_node = routing_map.get(intent, "recipe_generator")  # 기본값: 레시피 생성

    logger.info(f"[Router] primary_intent={intent} → {next_node}")

    return next_node


def check_secondary_intents(state: CookingState) -> str:
    """Secondary intents 확인 및 라우팅

    secondary_intents 리스트를 확인하여 다음 노드를 결정합니다.
    리스트가 비어있으면 워크플로우를 종료합니다.

    Args:
        state: 현재 상태

    Returns:
        str: 다음 노드 이름 또는 "end"
    """
    secondary_intents = state.get("secondary_intents", [])

    if secondary_intents:
        # 다음 실행할 intent (리스트 첫 번째)
        next_intent = secondary_intents[0]
        logger.info(
            f"[Router] Secondary intent: {next_intent} "
            f"(남은 intents: {len(secondary_intents)})"
        )

        routing_map = {
            "recipe_create": "recipe_generator",
            "recommend": "recommender",
            "question": "question_answerer"
        }

        return routing_map.get(next_intent, "end")

    logger.info(f"[Router] 모든 intent 완료 → end")
    return "end"
