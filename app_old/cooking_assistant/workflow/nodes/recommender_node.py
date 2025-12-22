"""RecommenderNode - 음식 추천 노드

재사용 가능한 음식 추천 노드입니다.
Port를 직접 주입받아 기능을 구현합니다.
"""
from app.core.decorators import inject
from app.core.ports.llm_port import ILLMPort
from app.core.prompt_loader import PromptLoader
from app.cooking_assistant.workflow.states.cooking_state import CookingState
from app.cooking_assistant.workflow.nodes.base_node import BaseNode
from app.cooking_assistant.entities.recommendation import Recommendation, DishRecommendation
import logging

logger = logging.getLogger(__name__)


class RecommenderNode(BaseNode):
    """음식 추천 노드

    책임:
    - 프롬프트 렌더링 (비즈니스 로직)
    - LLM Port를 통해 음식 추천
    - Raw dict를 Recommendation 엔티티로 변환
    - Secondary intent "recommend" 처리 (BaseNode에서 자동)

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
        super().__init__(intent_name="recommend")
        self.llm_port = llm_port
        self.prompt_loader = prompt_loader

    async def execute(self, state: CookingState) -> CookingState:
        """음식 추천 비즈니스 로직

        Args:
            state: 현재 워크플로우 상태

        Returns:
            CookingState: 업데이트된 상태
        """
        try:
            query = state["user_query"]
            entities = state.get("entities", {})

            # 프롬프트 렌더링
            prompt = self.prompt_loader.render(
                "cooking.recommend_dishes",
                query=query,
                cuisine_type=entities.get("cuisine_type"),
                taste=entities.get("taste", []),
                ingredients=entities.get("ingredients", []),
                dietary=entities.get("dietary", []),
                constraints=entities.get("constraints", {}),
                count=entities.get("count", 3)
            )

            # Pure adapter 호출
            rec_data = await self.llm_port.recommend_dishes(prompt)

            if not isinstance(rec_data, dict):
                raise TypeError(
                    f"추천 데이터는 딕셔너리여야 합니다. "
                    f"현재 타입: {type(rec_data).__name__}"
                )

            # 엔티티 변환
            raw_recs = rec_data.get("recommendations", [])
            dish_recs = [
                DishRecommendation(
                    name=r.get("name", ""),
                    description=r.get("description", ""),
                    reason=r.get("reason", "")
                )
                for r in raw_recs
            ]

            recommendation = Recommendation(recommendations=dish_recs)
            state["recommendation"] = recommendation
            state["dish_names"] = recommendation.get_dish_names()

            logger.info(f"[RecommenderNode] {recommendation.get_count()}개 음식 추천 완료")

        except Exception as e:
            logger.error(f"[RecommenderNode] 음식 추천 실패: {str(e)}")
            state["error"] = f"음식 추천 실패: {str(e)}"

        return state
