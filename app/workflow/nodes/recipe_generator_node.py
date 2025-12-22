"""RecipeGeneratorNode - 레시피 생성 노드

재사용 가능한 레시피 생성 노드입니다.
Port를 직접 주입받아 기능을 구현합니다.
"""
from app.core.decorators import inject
from app.core.ports.llm_port import ILLMPort
from app.core.prompt_loader import PromptLoader
from app.cooking_assistant.workflow.states.cooking_state import CookingState
from app.cooking_assistant.workflow.nodes.base_node import BaseNode
from app.cooking_assistant.entities.recipe import Recipe
import logging

logger = logging.getLogger(__name__)


class RecipeGeneratorNode(BaseNode):
    """레시피 생성 노드

    책임:
    - 프롬프트 선택 및 렌더링 (비즈니스 로직)
    - LLM Port를 통해 레시피 생성
    - Raw dict를 Recipe 엔티티로 변환 및 검증
    - Secondary intent "recipe_create" 처리 (BaseNode에서 자동)

    Attributes:
        llm_port: LLM 포트 (Anthropic, OpenAI 등)
        prompt_loader: 프롬프트 템플릿 로더
    """

    @inject
    def __init__(self, llm_port: ILLMPort, prompt_loader: PromptLoader):
        """의존성 주입: LLM Port, PromptLoader

        Args:
            llm_port: LLM 포트 (구체적 구현 몰라도 됨)
            prompt_loader: 프롬프트 템플릿 로더
        """
        super().__init__(intent_name="recipe_create")
        self.llm_port = llm_port
        self.prompt_loader = prompt_loader

    async def execute(self, state: CookingState) -> CookingState:
        """레시피 생성 비즈니스 로직

        Args:
            state: 현재 워크플로우 상태

        Returns:
            CookingState: 업데이트된 상태
        """
        try:
            query = state["user_query"]
            entities = state.get("entities", {})

            # BUSINESS LOGIC: 프롬프트 선택 (단일 vs 복수)
            dishes = entities.get("dishes", [])
            logger.info(f"[dishes: ]{dishes}")
            prompt_id = (
                "cooking.generate_recipe_multiple" if len(dishes) > 1
                else "cooking.generate_recipe_single"
            )

            # 프롬프트 렌더링
            prompt = self.prompt_loader.render(
                prompt_id,
                query=query,
                dishes=dishes,
                ingredients=entities.get("ingredients", []),
                constraints=entities.get("constraints", {}),
                dietary=entities.get("dietary", []),
                count=len(dishes) if dishes else 1
            )

            # Pure adapter 호출
            recipe_data = await self.llm_port.generate_recipe(prompt)
            logger.info(f"[recipe_data: ]{recipe_data}")
            # 엔티티 변환 및 검증
            if isinstance(recipe_data, list):
                # 복수 레시피
                recipes = [Recipe(**r) for r in recipe_data]
                for recipe in recipes:
                    recipe.validate()  # 비즈니스 규칙 검증
                state["recipes"] = recipes
                state["dish_names"] = [r.title for r in recipes]
                logger.info(f"[RecipeGeneratorNode] {len(recipes)}개 레시피 생성 완료")

            elif isinstance(recipe_data, dict):
                # 단일 레시피
                recipe = Recipe(**recipe_data)
                recipe.validate()
                state["recipe"] = recipe
                state["dish_names"] = [recipe.title] if recipe.title else []
                logger.info(f"[RecipeGeneratorNode] 레시피 생성 완료: {recipe.title}")

            else:
                raise TypeError(
                    f"레시피 데이터는 딕셔너리 또는 리스트여야 합니다. "
                    f"현재 타입: {type(recipe_data).__name__}"
                )

        except Exception as e:
            logger.error(f"[RecipeGeneratorNode] 레시피 생성 실패: {str(e)}")
            state["error"] = f"레시피 생성 실패: {str(e)}"

        return state
