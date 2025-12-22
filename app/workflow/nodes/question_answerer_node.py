"""QuestionAnswererNode - 질문 답변 노드

재사용 가능한 질문 답변 노드입니다.
Port를 직접 주입받아 기능을 구현합니다.
"""
from app.core.decorators import inject
from app.core.ports.llm_port import ILLMPort
from app.core.prompt_loader import PromptLoader
from app.cooking_assistant.workflow.states.cooking_state import CookingState
from app.cooking_assistant.workflow.nodes.base_node import BaseNode
from app.cooking_assistant.entities.question import Answer
import logging

logger = logging.getLogger(__name__)


class QuestionAnswererNode(BaseNode):
    @inject
    def __init__(self, llm_port: ILLMPort, prompt_loader: PromptLoader):
        super().__init__(intent_name="question")
        self.llm_port = llm_port
        self.prompt_loader = prompt_loader

    async def execute(self, state: CookingState) -> CookingState:
        try:
            query = state["user_query"]
            prompt = self.prompt_loader.render("cooking.answer_question", query=query)
            answer_data = await self.llm_port.answer_question(prompt)
            
            answer = Answer(
                answer=answer_data.get("answer", ""),
                additional_tips=answer_data.get("additional_tips", [])
            )
            state["answer"] = answer
            logger.info(f"[QuestionAnswererNode] 답변 완료")
        except Exception as e:
            logger.error(f"[QuestionAnswererNode] 질문 답변 실패: {str(e)}")
            state["error"] = f"질문 답변 실패: {str(e)}"
        return state
