"""ILLMPort - LLM 포트 인터페이스

도메인이 외부 LLM 서비스에게 요구하는 기능을 정의합니다.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class ILLMPort(ABC):
    """LLM 포트 (도메인이 외부 LLM에게 원하는 기능)

    외부 시스템(Anthropic, OpenAI 등)과의 경계를 정의합니다.
    구체적인 구현은 Adapter Layer에서 담당합니다.

    이 인터페이스 덕분에:
    - LLM 제공자 교체 가능 (Anthropic ↔ OpenAI)
    - 테스트 시 모킹 가능 (실제 API 호출 불필요)
    - 도메인 로직이 외부 시스템에 의존하지 않음
    """

    @abstractmethod
    async def classify_intent(self, query: str) -> Dict[str, Any]:
        """사용자 쿼리의 의도 분류 및 엔티티 추출

        Args:
            query: 사용자 쿼리
                예: "김치찌개 만드는 법 알려줘"

        Returns:
            Dict[str, Any]: 의도 분류 결과
                {
                    "primary_intent": "recipe_create" | "recommend" | "question",
                    "secondary_intents": [...],
                    "entities": {
                        "dishes": ["김치찌개"],
                        "ingredients": [...],
                        "constraints": {...},
                        ...
                    },
                    "confidence": 0.95
                }

        Example:
            >>> llm_port = AnthropicLLMAdapter(settings)
            >>> result = await llm_port.classify_intent("김치찌개 만드는 법")
            >>> result['primary_intent']
            'recipe_create'
        """
        pass

    @abstractmethod
    async def generate_recipe(
        self,
        query: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """레시피 생성

        Args:
            query: 사용자 쿼리
            entities: 추출된 엔티티 (요리명, 재료 등)

        Returns:
            Dict[str, Any]: 레시피 데이터 (단일 또는 복수)
                단일 레시피:
                {
                    "title": "김치찌개",
                    "ingredients": ["김치 200g", ...],
                    "steps": ["1. 김치를 썬다", ...],
                    "cooking_time": "30분",
                    "difficulty": "중간"
                }

                복수 레시피:
                [
                    {"title": "김치찌개", ...},
                    {"title": "된장찌개", ...}
                ]

        Example:
            >>> entities = {"dishes": ["김치찌개"]}
            >>> recipe = await llm_port.generate_recipe("김치찌개 만들기", entities)
            >>> recipe['title']
            '김치찌개'
        """
        pass

    @abstractmethod
    async def recommend_dishes(
        self,
        query: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """음식 추천

        Args:
            query: 사용자 쿼리
            entities: 추출된 엔티티 (맛 선호, 요리 유형 등)

        Returns:
            Dict[str, Any]: 추천 결과
                {
                    "recommendations": [
                        {
                            "name": "음식 이름",
                            "description": "간단한 설명",
                            "reason": "추천 이유"
                        },
                        ...
                    ]
                }

        Example:
            >>> entities = {"taste": ["매운맛"], "cuisine_type": "한식"}
            >>> result = await llm_port.recommend_dishes("매운 한식 추천", entities)
            >>> result['recommendations'][0]['name']
            '김치찌개'
        """
        pass

    @abstractmethod
    async def answer_question(self, query: str) -> Dict[str, Any]:
        """요리 관련 질문 답변

        Args:
            query: 사용자 질문
                예: "김치찌개 칼로리는?"

        Returns:
            Dict[str, Any]: 답변 결과
                {
                    "answer": "답변 내용",
                    "additional_tips": ["팁1", "팁2", ...]
                }

        Example:
            >>> result = await llm_port.answer_question("김치찌개 칼로리는?")
            >>> result['answer']
            '김치찌개는 1인분 기준 약 250kcal입니다.'
        """
        pass
