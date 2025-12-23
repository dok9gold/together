"""Gemini LLM 구현체"""
import logging
from dataclasses import dataclass, asdict
from typing import Any

import google.generativeai as genai

from .interface import LLMInterface

logger = logging.getLogger(__name__)


@dataclass
class GeminiOption:
    """Gemini API 호출 옵션

    Attributes:
        model: 모델 ID
        max_output_tokens: 최대 출력 토큰 수
        temperature: 샘플링 온도 (0.0 ~ 2.0)
        top_p: Top-p 샘플링 (선택)
        top_k: Top-k 샘플링 (선택)
        stop_sequences: 중단 시퀀스 (선택)
    """
    model: str = "gemini-1.5-flash"
    max_output_tokens: int = 4096
    temperature: float = 0.7
    top_p: float | None = None
    top_k: int | None = None
    stop_sequences: list[str] | None = None

    def merge(self, overrides: dict[str, Any] | None) -> "GeminiOption":
        """전달된 값만 덮어쓰기하여 새 옵션 반환"""
        if not overrides:
            return self

        current = asdict(self)
        for key, value in overrides.items():
            if key in current and value is not None:
                current[key] = value

        return GeminiOption(**current)


class GeminiLLM(LLMInterface):
    """Google Gemini API 구현체"""

    def __init__(
        self,
        api_key: str,
        default_option: GeminiOption | None = None
    ):
        """
        Args:
            api_key: Google API 키
            default_option: 기본 옵션 (없으면 GeminiOption 기본값 사용)
        """
        genai.configure(api_key=api_key)
        self.default_option = default_option or GeminiOption()

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        option: dict[str, Any] | None = None
    ) -> str:
        """프롬프트를 받아 Gemini 응답 반환

        Args:
            prompt: 사용자 프롬프트
            system: 시스템 프롬프트 (선택)
            option: 옵션 오버라이드 (선택)

        Returns:
            Gemini 응답 텍스트
        """
        final_option = self.default_option.merge(option)

        logger.debug(
            f"[GeminiLLM] model={final_option.model}, "
            f"max_output_tokens={final_option.max_output_tokens}, "
            f"temperature={final_option.temperature}"
        )

        # 모델 생성
        generation_config = {
            "max_output_tokens": final_option.max_output_tokens,
            "temperature": final_option.temperature,
        }

        if final_option.top_p is not None:
            generation_config["top_p"] = final_option.top_p

        if final_option.top_k is not None:
            generation_config["top_k"] = final_option.top_k

        if final_option.stop_sequences:
            generation_config["stop_sequences"] = final_option.stop_sequences

        model = genai.GenerativeModel(
            model_name=final_option.model,
            generation_config=generation_config,
            system_instruction=system
        )

        # API 호출 (async)
        response = await model.generate_content_async(prompt)

        result = response.text

        logger.debug(f"[GeminiLLM] 응답 길이: {len(result)}자")

        return result
