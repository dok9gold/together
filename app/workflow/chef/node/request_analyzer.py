"""RequestAnalyzerNode - 요청 분석 (의도 + 개체 추출)"""
import json
import logging
from typing import Any

from .base import BaseNode, load_prompt, render_prompt

logger = logging.getLogger(__name__)


class RequestAnalyzerNode(BaseNode):
    """사용자 요청을 분석하여 intent와 entity 추출"""

    def __init__(self, llm):
        super().__init__(llm)
        self.templates = load_prompt("request_analyzer", "analyze")

    async def execute(
        self,
        state: dict[str, Any],
        config: dict | None = None
    ) -> dict[str, Any]:
        """쿼리 분석 실행

        Args:
            state: {"user_input": str, ...}
            config: {"configurable": {"chat_history": [...]}}

        Returns:
            {"intents": list[str], "entities": dict}
        """
        user_input = state.get("user_input", "")
        chat_history = []

        if config and "configurable" in config:
            chat_history = config["configurable"].get("chat_history", [])

        # 프롬프트 렌더링
        prompts = render_prompt(
            self.templates,
            user_input=user_input,
            chat_history=chat_history
        )

        logger.debug(f"[RequestAnalyzer] user_input: {user_input}")

        # LLM 호출
        response = await self.llm.generate(
            prompt=prompts["user"],
            system=prompts["system"],
            option={"temperature": 0.3, "max_tokens": 1024}
        )

        # JSON 파싱
        result = self._parse_response(response)

        logger.info(f"[RequestAnalyzer] intents: {result['intents']}, entities: {result['entities']}")

        return {
            "intents": result["intents"],
            "entities": result["entities"]
        }

    def _parse_response(self, response: str) -> dict[str, Any]:
        """LLM 응답을 JSON으로 파싱

        Args:
            response: LLM 응답 텍스트

        Returns:
            {"intents": list, "entities": dict}
        """
        try:
            # JSON 블록 추출 (```json ... ``` 형식 지원)
            text = response.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            data = json.loads(text)

            return {
                "intents": data.get("intents", ["general_chat"]),
                "entities": data.get("entities", {})
            }
        except (json.JSONDecodeError, IndexError) as e:
            logger.warning(f"[RequestAnalyzer] JSON 파싱 실패: {e}, response: {response[:200]}")
            return {
                "intents": ["general_chat"],
                "entities": {}
            }
