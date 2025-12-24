"""ResponseGeneratorNode - 최종 응답 생성"""
import logging
from typing import Any

from .base import BaseNode, load_prompt, render_prompt

logger = logging.getLogger(__name__)


class ResponseGeneratorNode(BaseNode):
    """State를 조합하여 최종 사용자 응답 생성"""

    def __init__(self, llm):
        super().__init__(llm)
        self.templates = load_prompt("response_generator", "generate")

    async def execute(
        self,
        state: dict[str, Any],
        config: dict | None = None
    ) -> dict[str, Any]:
        """응답 생성 실행

        Args:
            state: 전체 State (user_input, intents, dishes, recipes, qa_answer 등)
            config: 설정

        Returns:
            {"response": str}
        """
        user_input = state.get("user_input", "")
        intents = state.get("intents", [])
        dishes = state.get("dishes", [])
        recipes = state.get("recipes", [])
        qa_answer = state.get("qa_answer")
        discount_items = state.get("discount_items", [])

        # 프롬프트 렌더링
        prompts = render_prompt(
            self.templates,
            user_input=user_input,
            intents=intents,
            dishes=dishes,
            recipes=recipes,
            qa_answer=qa_answer,
            discount_items=discount_items
        )

        logger.debug(f"[ResponseGenerator] intents: {intents}, dishes: {dishes}")

        # LLM 호출
        response = await self.llm.generate(
            prompt=prompts["user"],
            system=prompts["system"],
            option={"temperature": 0.7, "max_tokens": 2048}
        )

        logger.info(f"[ResponseGenerator] response generated, length: {len(response)}")

        return {"response": response.strip()}
