"""Claude LLM 구현체"""
import logging
from dataclasses import dataclass, field, asdict
from typing import Any

import anthropic

from .interface import LLMInterface

logger = logging.getLogger(__name__)


@dataclass
class ClaudeOption:
    """Claude API 호출 옵션

    Attributes:
        model: 모델 ID
        max_tokens: 최대 토큰 수
        temperature: 샘플링 온도 (0.0 ~ 1.0)
        top_p: Top-p 샘플링 (선택)
        stop_sequences: 중단 시퀀스 (선택)
    """
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float | None = None
    stop_sequences: list[str] | None = None

    def merge(self, overrides: dict[str, Any] | None) -> "ClaudeOption":
        """전달된 값만 덮어쓰기하여 새 옵션 반환

        Args:
            overrides: 덮어쓸 옵션 딕셔너리

        Returns:
            머지된 새 ClaudeOption
        """
        if not overrides:
            return self

        current = asdict(self)
        # None이 아닌 값만 머지
        for key, value in overrides.items():
            if key in current and value is not None:
                current[key] = value

        return ClaudeOption(**current)


class ClaudeLLM(LLMInterface):
    """Anthropic Claude API 구현체"""

    def __init__(
        self,
        api_key: str,
        default_option: ClaudeOption | None = None
    ):
        """
        Args:
            api_key: Anthropic API 키
            default_option: 기본 옵션 (없으면 ClaudeOption 기본값 사용)
        """
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.default_option = default_option or ClaudeOption()

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        option: dict[str, Any] | None = None
    ) -> str:
        """프롬프트를 받아 Claude 응답 반환

        Args:
            prompt: 사용자 프롬프트
            system: 시스템 프롬프트 (선택)
            option: 옵션 오버라이드 (선택)

        Returns:
            Claude 응답 텍스트
        """
        # 옵션 머지
        final_option = self.default_option.merge(option)

        logger.debug(
            f"[ClaudeLLM] model={final_option.model}, "
            f"max_tokens={final_option.max_tokens}, "
            f"temperature={final_option.temperature}"
        )

        # API 호출 파라미터 구성
        params: dict[str, Any] = {
            "model": final_option.model,
            "max_tokens": final_option.max_tokens,
            "temperature": final_option.temperature,
            "messages": [{"role": "user", "content": prompt}]
        }

        if system:
            params["system"] = system

        if final_option.top_p is not None:
            params["top_p"] = final_option.top_p

        if final_option.stop_sequences:
            params["stop_sequences"] = final_option.stop_sequences

        # API 호출
        response = await self.client.messages.create(**params)

        # 텍스트 추출
        result = response.content[0].text

        logger.debug(f"[ClaudeLLM] 응답 길이: {len(result)}자")

        return result
