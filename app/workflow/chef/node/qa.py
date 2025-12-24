"""QANode - 요리 관련 질문 답변"""
import logging
from typing import Any

from .base import BaseNode, load_prompt, render_prompt

logger = logging.getLogger(__name__)


class QANode(BaseNode):
    """요리 관련 질문에 답변"""

    def __init__(self, llm):
        super().__init__(llm)
        self.templates = load_prompt("qa", "answer")

    async def execute(
        self,
        state: dict[str, Any],
        config: dict | None = None
    ) -> dict[str, Any]:
        """QA 실행

        Args:
            state: State (user_input, entities 포함)
            config: 설정

        Returns:
            {"qa_answer": str | None}
        """
        user_input = state.get("user_input", "")
        entities = state.get("entities", {})

        # 프롬프트 렌더링
        prompts = render_prompt(
            self.templates,
            user_input=user_input,
            entities=entities
        )

        logger.debug(f"[QA] user_input: {user_input}")

        # LLM 호출
        response = await self.llm.generate(
            prompt=prompts["user"],
            system=prompts["system"],
            option={"temperature": 0.7, "max_tokens": 1024}
        )

        logger.info(f"[QA] answer generated: {len(response)} chars")

        return {"qa_answer": response.strip()}
