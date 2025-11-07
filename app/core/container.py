"""DI Container - 의존성 주입 컨테이너

Spring의 ApplicationContext와 유사한 역할을 합니다.
모든 컴포넌트를 등록하고 의존성을 자동으로 주입합니다.
"""
from dependency_injector import containers, providers
from app.core.config import get_settings

# Domain
from app.domain.services.cooking_assistant import CookingAssistantService

# Adapters
from app.adapters.llm.anthropic_adapter import AnthropicLLMAdapter
from app.adapters.image.replicate_adapter import ReplicateImageAdapter

# Application - Workflow Nodes
from app.application.workflow.nodes.intent_classifier_node import IntentClassifierNode
from app.application.workflow.nodes.recipe_generator_node import RecipeGeneratorNode
from app.application.workflow.nodes.image_generator_node import ImageGeneratorNode
from app.application.workflow.nodes.recommender_node import RecommenderNode
from app.application.workflow.nodes.question_answerer_node import QuestionAnswererNode

# Application - Workflow
from app.application.workflow.cooking_workflow import CookingWorkflow

# Application - Use Cases
from app.application.use_cases.create_recipe_use_case import CreateRecipeUseCase


class Container(containers.DeclarativeContainer):
    """의존성 컨테이너 (Spring ApplicationContext 역할)

    모든 컴포넌트를 등록하고 의존성을 자동으로 주입합니다.

    생명주기:
    - Singleton: 애플리케이션 전체에서 하나의 인스턴스만 사용
    - Factory: 요청마다 새로운 인스턴스 생성
    """

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 설정 (Singleton)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    config = providers.Singleton(get_settings)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Adapters (Singleton) - Port 구현체
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    llm_adapter = providers.Singleton(
        AnthropicLLMAdapter,
        settings=config
    )

    image_adapter = providers.Singleton(
        ReplicateImageAdapter,
        settings=config
    )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Domain Services (Singleton) - Adapter 주입
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    cooking_assistant = providers.Singleton(
        CookingAssistantService,
        llm_port=llm_adapter,
        image_port=image_adapter
    )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Workflow Nodes (Factory - 가볍고 상태 없음)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    intent_classifier_node = providers.Factory(
        IntentClassifierNode,
        cooking_assistant=cooking_assistant
    )

    recipe_generator_node = providers.Factory(
        RecipeGeneratorNode,
        cooking_assistant=cooking_assistant
    )

    image_generator_node = providers.Factory(
        ImageGeneratorNode,
        cooking_assistant=cooking_assistant
    )

    recommender_node = providers.Factory(
        RecommenderNode,
        cooking_assistant=cooking_assistant
    )

    question_answerer_node = providers.Factory(
        QuestionAnswererNode,
        cooking_assistant=cooking_assistant
    )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Workflow (Singleton - 그래프 컴파일 비용 절감)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    cooking_workflow = providers.Singleton(
        CookingWorkflow,
        intent_classifier=intent_classifier_node,
        recipe_generator=recipe_generator_node,
        image_generator=image_generator_node,
        recommender=recommender_node,
        question_answerer=question_answerer_node
    )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Use Cases (Factory - 요청마다 새 인스턴스)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    create_recipe_use_case = providers.Factory(
        CreateRecipeUseCase,
        workflow=cooking_workflow
    )
