"""CookingWorkflow - 요리 AI 어시스턴트 워크플로우

LangGraph StateGraph를 구성하여 워크플로우를 정의합니다.
"""
from langgraph.graph import StateGraph, END
from app.domain.entities.cooking_state import CookingState
from app.application.workflow.nodes.intent_classifier_node import IntentClassifierNode
from app.application.workflow.nodes.recipe_generator_node import RecipeGeneratorNode
from app.application.workflow.nodes.image_generator_node import ImageGeneratorNode
from app.application.workflow.nodes.recommender_node import RecommenderNode
from app.application.workflow.nodes.question_answerer_node import QuestionAnswererNode
from app.application.workflow.edges.intent_router import route_by_intent, check_secondary_intents
import logging

logger = logging.getLogger(__name__)


class CookingWorkflow:
    """요리 AI 어시스턴트 워크플로우 (LangGraph)

    책임:
    - 노드 구성
    - 엣지 연결
    - 그래프 컴파일

    ❌ 비즈니스 로직은 여기 작성하지 말 것!
       → Domain Services에 위임

    Attributes:
        intent_classifier: 의도 분류 노드
        recipe_generator: 레시피 생성 노드
        image_generator: 이미지 생성 노드
        recommender: 추천 노드
        question_answerer: 질문 답변 노드
        graph: 컴파일된 LangGraph StateGraph
    """

    def __init__(
        self,
        intent_classifier: IntentClassifierNode,
        recipe_generator: RecipeGeneratorNode,
        image_generator: ImageGeneratorNode,
        recommender: RecommenderNode,
        question_answerer: QuestionAnswererNode
    ):
        """의존성 주입: 모든 노드

        Args:
            intent_classifier: 의도 분류 노드
            recipe_generator: 레시피 생성 노드
            image_generator: 이미지 생성 노드
            recommender: 추천 노드
            question_answerer: 질문 답변 노드
        """
        self.intent_classifier = intent_classifier
        self.recipe_generator = recipe_generator
        self.image_generator = image_generator
        self.recommender = recommender
        self.question_answerer = question_answerer

        # 그래프 빌드
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """워크플로우 구성 (오케스트레이션만 담당)

        Returns:
            StateGraph: 컴파일된 LangGraph StateGraph
        """
        workflow = StateGraph(CookingState)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1. 노드 추가
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        workflow.add_node("classify_intent", self.intent_classifier)
        workflow.add_node("recipe_generator", self.recipe_generator)
        workflow.add_node("image_generator", self.image_generator)
        workflow.add_node("recommender", self.recommender)
        workflow.add_node("question_answerer", self.question_answerer)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2. 시작점: 의도 분류
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        workflow.set_entry_point("classify_intent")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3. Primary Intent에 따라 분기
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        workflow.add_conditional_edges(
            "classify_intent",
            route_by_intent,  # 라우팅 함수
            {
                "recipe_generator": "recipe_generator",
                "recommender": "recommender",
                "question_answerer": "question_answerer"
            }
        )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 4. 레시피 생성 후 이미지 생성
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        workflow.add_edge("recipe_generator", "image_generator")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 5. 이미지 생성 후 Secondary Intents 확인
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        workflow.add_conditional_edges(
            "image_generator",
            check_secondary_intents,
            {
                "recipe_generator": "recipe_generator",
                "recommender": "recommender",
                "question_answerer": "question_answerer",
                "end": END
            }
        )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 6. 추천 후 Secondary Intents 확인
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        workflow.add_conditional_edges(
            "recommender",
            check_secondary_intents,
            {
                "recipe_generator": "recipe_generator",
                "recommender": "recommender",
                "question_answerer": "question_answerer",
                "end": END
            }
        )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 7. 질문 답변 후 Secondary Intents 확인
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        workflow.add_conditional_edges(
            "question_answerer",
            check_secondary_intents,
            {
                "recipe_generator": "recipe_generator",
                "recommender": "recommender",
                "question_answerer": "question_answerer",
                "end": END
            }
        )

        logger.info("[Workflow] 그래프 빌드 완료")

        return workflow.compile()

    async def run(self, initial_state: CookingState) -> CookingState:
        """워크플로우 실행

        Args:
            initial_state: 초기 상태

        Returns:
            CookingState: 최종 상태
        """
        logger.info(f"[Workflow] 시작: {initial_state['user_query'][:50]}...")
        result = await self.graph.ainvoke(initial_state)
        logger.info(f"[Workflow] 완료")
        return result
