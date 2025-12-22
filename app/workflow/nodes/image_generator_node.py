"""ImageGeneratorNode - 이미지 생성 노드"""
from app.core.decorators import inject
from app.core.ports.image_port import IImagePort
from app.core.prompt_loader import PromptLoader
from app.cooking_assistant.workflow.states.cooking_state import CookingState
from app.cooking_assistant.workflow.nodes.base_node import BaseNode
import logging

logger = logging.getLogger(__name__)


class ImageGeneratorNode(BaseNode):
    @inject
    def __init__(self, image_port: IImagePort, prompt_loader: PromptLoader):
        super().__init__(intent_name="generate_image")
        self.image_port = image_port
        self.prompt_loader = prompt_loader

    async def execute(self, state: CookingState) -> CookingState:
        try:
            if not state.get("dish_names"):
                return state

            dish_name = state["dish_names"][0]
            prompt = self.prompt_loader.render("cooking.image_prompt", dish_name=dish_name)
            state["image_prompt"] = prompt
            
            image_url = await self.image_port.generate_image(prompt)
            state["image_url"] = image_url
            
            if image_url:
                logger.info(f"[ImageGeneratorNode] 이미지 생성 성공")
        except Exception as e:
            logger.error(f"[ImageGeneratorNode] 이미지 생성 실패: {str(e)}")
            state["image_url"] = None
        return state
