"""LLM 인터페이스"""
from abc import ABC, abstractmethod
from typing import Any


class LLMInterface(ABC):
    """LLM API 호출 인터페이스"""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        option: dict[str, Any] | None = None
    ) -> str:
        """프롬프트를 받아 텍스트 응답 반환

        Args:
            prompt: 사용자 프롬프트
            system: 시스템 프롬프트 (선택)
            option: API 호출 옵션 오버라이드 (선택)

        Returns:
            LLM 응답 텍스트
        """
        pass
