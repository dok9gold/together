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
    async def classify_intent(self, prompt: str) -> Dict[str, Any]:
        """사용자 쿼리의 의도 분류 및 엔티티 추출

        Pure port: accepts pre-rendered prompt, returns raw LLM response.
        No business logic - prompt rendering done by caller.

        Args:
            prompt: Pre-rendered prompt string

        Returns:
            Dict[str, Any]: 의도 분류 결과
                {
                    "primary_intent": "recipe_create" | "recommend" | "question",
                    "secondary_intents": [...],
                    "entities": {...},
                    "confidence": 0.95
                }
        """
        pass

    @abstractmethod
    async def generate_recipe(self, prompt: str) -> Dict[str, Any]:
        """레시피 생성

        Pure port: accepts pre-rendered prompt, returns raw LLM response.
        No business logic - prompt selection/rendering done by caller.

        Args:
            prompt: Pre-rendered prompt string

        Returns:
            Dict[str, Any] or List[Dict[str, Any]]: Recipe data
                Single recipe dict or list of recipe dicts
        """
        pass

    @abstractmethod
    async def recommend_dishes(self, prompt: str) -> Dict[str, Any]:
        """음식 추천

        Pure port: accepts pre-rendered prompt, returns raw LLM response.

        Args:
            prompt: Pre-rendered prompt string

        Returns:
            Dict[str, Any]: 추천 결과
                {
                    "recommendations": [
                        {"name": "...", "description": "...", "reason": "..."},
                        ...
                    ]
                }
        """
        pass

    @abstractmethod
    async def answer_question(self, prompt: str) -> Dict[str, Any]:
        """요리 관련 질문 답변

        Pure port: accepts pre-rendered prompt, returns raw LLM response.

        Args:
            prompt: Pre-rendered prompt string

        Returns:
            Dict[str, Any]: 답변 결과
                {
                    "answer": "답변 내용",
                    "additional_tips": ["팁1", "팁2", ...]
                }
        """
        pass
