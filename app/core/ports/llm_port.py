"""ILLMPort - LLM 포트 인터페이스

Application이 외부 LLM 서비스에게 요구하는 기능을 정의합니다.

Port-Adapter Pattern:
    Port는 Application의 요구사항을 정의하고,
    Adapter는 외부 시스템(Anthropic, OpenAI 등)에 맞춰 구현합니다.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class ILLMPort(ABC):
    """LLM 포트 (Application이 외부 LLM에게 원하는 기능)

    외부 LLM 서비스(Anthropic, OpenAI 등)와의 경계를 정의합니다.
    구체적인 구현은 Adapter Layer에서 담당합니다.

    이 인터페이스 덕분에:
    - LLM 제공자 교체 가능 (Anthropic ↔ OpenAI)
    - 테스트 시 모킹 가능 (실제 API 호출 불필요)
    - Application 로직이 외부 시스템에 의존하지 않음

    Note:
        메서드명은 Application 도메인에 맞춰 정의되어 있습니다.
        새로운 Application을 만들 경우, 해당 도메인에 맞는 메서드로 변경하세요.
    """

    @abstractmethod
    async def classify_intent(self, prompt: str) -> Dict[str, Any]:
        """사용자 쿼리의 의도 분류 및 엔티티 추출

        Pure port 원칙:
        - 렌더링된 프롬프트를 받아서 LLM API 호출
        - 비즈니스 로직 없음 (프롬프트 생성은 호출자가 담당)

        Args:
            prompt: 렌더링된 프롬프트 문자열

        Returns:
            Dict[str, Any]: LLM이 반환한 의도 분류 결과 (JSON)
        """
        pass

    @abstractmethod
    async def generate_recipe(self, prompt: str) -> Dict[str, Any]:
        """구조화된 데이터 생성 (예: 레시피, 계획서 등)

        Pure port 원칙:
        - 렌더링된 프롬프트를 받아서 LLM API 호출
        - 비즈니스 로직 없음

        Args:
            prompt: 렌더링된 프롬프트 문자열

        Returns:
            Dict[str, Any] or List[Dict[str, Any]]: LLM이 반환한 구조화 데이터
        """
        pass

    @abstractmethod
    async def recommend_dishes(self, prompt: str) -> Dict[str, Any]:
        """추천 목록 생성 (예: 음식, 상품, 콘텐츠 등)

        Pure port 원칙:
        - 렌더링된 프롬프트를 받아서 LLM API 호출

        Args:
            prompt: 렌더링된 프롬프트 문자열

        Returns:
            Dict[str, Any]: LLM이 반환한 추천 결과
        """
        pass

    @abstractmethod
    async def answer_question(self, prompt: str) -> Dict[str, Any]:
        """질문 답변 생성

        Pure port 원칙:
        - 렌더링된 프롬프트를 받아서 LLM API 호출

        Args:
            prompt: 렌더링된 프롬프트 문자열

        Returns:
            Dict[str, Any]: LLM이 반환한 답변 결과
        """
        pass
