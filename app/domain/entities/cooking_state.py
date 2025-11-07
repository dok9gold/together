"""CookingState - LangGraph 워크플로우 상태

LangGraph 워크플로우에서 사용하는 상태 타입입니다.
"""
from typing import TypedDict, Optional, List, Dict, Any


class CookingState(TypedDict):
    """요리 AI 어시스턴트 워크플로우 상태

    LangGraph의 상태로 사용되며, 워크플로우 실행 중
    각 노드를 거치며 업데이트됩니다.

    Attributes:
        user_query: 사용자 입력 쿼리
        primary_intent: 주 의도 (recipe_create, recommend, question)
        secondary_intents: 부가 의도 리스트 (순차 실행)
        entities: 추출된 엔티티 (요리명, 재료, 제약조건 등)
        confidence: 의도 파악 확신도 (0.0 ~ 1.0)
        recipe_text: 레시피 생성 결과 (JSON 문자열)
        recipes: 레시피 목록 (복수 레시피)
        dish_names: 요리명 목록 (추천/레시피에서 추출)
        recommendation: 음식 추천 결과 (JSON 문자열)
        answer: 질문 답변 결과 (JSON 문자열)
        image_prompt: 이미지 생성 프롬프트
        image_url: 생성된 이미지 URL
        image_urls: 이미지 URL 목록 (복수 레시피용)
        error: 오류 메시지
    """
    user_query: str
    primary_intent: str
    secondary_intents: List[str]
    entities: Dict[str, Any]
    confidence: float
    recipe_text: str
    recipes: List[Dict[str, Any]]
    dish_names: List[str]
    recommendation: str
    answer: str
    image_prompt: str
    image_url: Optional[str]
    image_urls: List[str]
    error: Optional[str]
