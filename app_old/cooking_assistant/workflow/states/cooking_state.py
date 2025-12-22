"""CookingState - LangGraph 워크플로우 상태

LangGraph 워크플로우에서 사용하는 상태 타입입니다.
"""
from typing import TypedDict, Optional, List, Dict, Any
from app.cooking_assistant.entities.recipe import Recipe
from app.cooking_assistant.entities.question import Answer
from app.cooking_assistant.entities.recommendation import Recommendation


class CookingState(TypedDict):
    """요리 AI 어시스턴트 워크플로우 상태

    LangGraph의 상태로 사용되며, 워크플로우 실행 중
    각 노드를 거치며 업데이트됩니다.

    Attributes:
        user_query: 사용자 입력 쿼리
        user_id: 사용자 ID (인증된 경우, 개인화 기능용)
        primary_intent: 주 의도 (recipe_create, recommend, question)
        secondary_intents: 부가 의도 리스트 (순차 실행)
        processed_secondary_intents: 처리 완료된 부가 의도 리스트 (NEW: 버그 수정용)
        entities: 추출된 엔티티 (요리명, 재료, 제약조건 등)
        confidence: 의도 파악 확신도 (0.0 ~ 1.0)
        recipe: 단일 레시피 엔티티 (NEW: Recipe 객체)
        recipes: 레시피 목록 (NEW: List[Recipe] 객체)
        dish_names: 요리명 목록 (추천/레시피에서 추출)
        recommendation: 음식 추천 결과 (NEW: Recommendation 객체)
        answer: 질문 답변 결과 (NEW: Answer 객체)
        image_prompt: 이미지 생성 프롬프트
        image_url: 생성된 이미지 URL
        image_urls: 이미지 URL 목록 (복수 레시피용)
        error: 오류 메시지
    """
    # Query info
    user_query: str
    user_id: Optional[str]

    # Intent classification
    primary_intent: str
    secondary_intents: List[str]              # Remaining intents to process
    processed_secondary_intents: List[str]    # NEW: Completed intents
    entities: Dict[str, Any]
    confidence: float

    # Domain entities (replacing raw dicts/JSON strings)
    recipe: Optional[Recipe]                  # Single recipe
    recipes: List[Recipe]                     # Multiple recipes
    recommendation: Optional[Recommendation]  # Dish recommendations
    answer: Optional[Answer]                  # Question answer

    # Supporting data
    dish_names: List[str]

    # Image generation
    image_prompt: str
    image_url: Optional[str]
    image_urls: List[str]

    # Error handling
    error: Optional[str]


def create_initial_state(query: str) -> CookingState:
    """초기 상태 생성 (Factory 함수)

    워크플로우 실행 전 초기 상태를 생성합니다.
    모든 필드를 기본값으로 초기화하고 user_query만 설정합니다.

    Args:
        query: 사용자 입력 쿼리

    Returns:
        CookingState: 초기화된 워크플로우 상태

    Example:
        >>> state = create_initial_state("김치찌개 만드는 법")
        >>> state["user_query"]
        '김치찌개 만드는 법'
        >>> state["primary_intent"]
        ''
    """
    return {
        "user_query": query,
        "user_id": None,
        "primary_intent": "",
        "secondary_intents": [],
        "processed_secondary_intents": [],  # NEW: Track processed intents
        "entities": {},
        "confidence": 0.0,

        # Initialize as None/empty (entities, not JSON strings)
        "recipe": None,
        "recipes": [],
        "recommendation": None,
        "answer": None,

        "dish_names": [],
        "image_prompt": "",
        "image_url": None,
        "image_urls": [],
        "error": None
    }
