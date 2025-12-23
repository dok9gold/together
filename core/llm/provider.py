"""LLM Provider - 여러 LLM을 관리하고 선택"""
import logging
from typing import Any

from .interface import LLMInterface

logger = logging.getLogger(__name__)


class LLMProvider:
    """여러 LLM을 등록하고 선택적으로 호출

    사용 예시:
        provider = LLMProvider()
        provider.register("claude", ClaudeLLM(api_key="..."))
        provider.register("gemini", GeminiLLM(api_key="..."))

        # 호출
        result = await provider.generate(
            prompt="김치찌개 레시피",
            provider="claude",
            option={"temperature": 0.3}
        )
    """

    def __init__(self, default_provider: str = "claude"):
        """
        Args:
            default_provider: 기본 provider 이름
        """
        self._llms: dict[str, LLMInterface] = {}
        self._default_provider = default_provider

    def register(self, name: str, llm: LLMInterface) -> None:
        """LLM 등록

        Args:
            name: provider 이름 (예: "claude", "gemini")
            llm: LLMInterface 구현체
        """
        self._llms[name] = llm
        logger.info(f"[LLMProvider] '{name}' 등록 완료")

    def get(self, name: str | None = None) -> LLMInterface:
        """등록된 LLM 반환

        Args:
            name: provider 이름 (없으면 default)

        Returns:
            LLMInterface 구현체

        Raises:
            KeyError: 등록되지 않은 provider
        """
        provider = name or self._default_provider
        if provider not in self._llms:
            raise KeyError(f"Provider '{provider}' not registered")
        return self._llms[provider]

    @property
    def providers(self) -> list[str]:
        """등록된 provider 이름 목록"""
        return list(self._llms.keys())

    async def generate(
        self,
        prompt: str,
        provider: str | None = None,
        system: str | None = None,
        option: dict[str, Any] | None = None
    ) -> str:
        """LLM 호출

        Args:
            prompt: 사용자 프롬프트
            provider: provider 이름 (없으면 default)
            system: 시스템 프롬프트 (선택)
            option: API 옵션 오버라이드 (선택)

        Returns:
            LLM 응답 텍스트
        """
        llm = self.get(provider)
        provider_name = provider or self._default_provider

        logger.debug(f"[LLMProvider] '{provider_name}' 호출")

        return await llm.generate(prompt, system=system, option=option)
