"""IntentClassifierNode - 의도 분류 노드"""
from app.core.decorators import inject
from app.core.ports.llm_port import ILLMPort
from app.core.prompt_loader import PromptLoader
from app.cooking_assistant.workflow.states.cooking_state import CookingState
from app.cooking_assistant.workflow.nodes.base_node import BaseNode
import logging

logger = logging.getLogger(__name__)


class IntentClassifierNode(BaseNode):
    @inject
    def __init__(self, llm_port: ILLMPort, prompt_loader: PromptLoader):
        super().__init__(intent_name=None)
        self.llm_port = llm_port
        self.prompt_loader = prompt_loader

    async def execute(self, state: CookingState) -> CookingState:
        try:
            query = state["user_query"]
            prompt = self.prompt_loader.render("cooking.classify_intent", query=query)
            result = await self.llm_port.classify_intent(prompt)
            
            state["primary_intent"] = result.get("primary_intent", "")
            state["secondary_intents"] = result.get("secondary_intents", [])
            state["entities"] = result.get("entities", {})
            state["confidence"] = result.get("confidence", 0.0)
            
            logger.info(f"[IntentClassifierNode] 의도 분류: {state['primary_intent']}")
        except Exception as e:
            logger.error(f"[IntentClassifierNode] 의도 분류 실패: {str(e)}")
            state["error"] = f"의도 분류 실패: {str(e)}"
        return state
