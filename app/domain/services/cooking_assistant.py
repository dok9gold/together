"""CookingAssistantService - 요리 AI 어시스턴트 도메인 서비스

핵심 비즈니스 로직을 담당합니다.
외부 시스템은 몰라도 되며, Port 인터페이스에만 의존합니다.
"""
from app.core.decorators import singleton, inject
from app.domain.ports.llm_port import ILLMPort
from app.domain.ports.image_port import IImagePort
from app.domain.entities.cooking_state import CookingState
import logging

logger = logging.getLogger(__name__)


@singleton
class CookingAssistantService:
    """요리 AI 어시스턴트 도메인 서비스

    순수 비즈니스 로직만 포함:
    - 외부 시스템 몰라도 됨 (Port에만 의존)
    - 의도 분류, 레시피 생성, 추천, 질문 답변 로직
    - 테스트 시 Port를 모킹하면 됨

    Attributes:
        llm_port: LLM 포트 (Anthropic든 OpenAI든 상관없음)
        image_port: 이미지 포트 (Replicate든 DALL-E든 상관없음)

    Example:
        >>> llm_port = AnthropicLLMAdapter(settings)
        >>> image_port = ReplicateImageAdapter(settings)
        >>> service = CookingAssistantService(llm_port, image_port)
        >>> state = await service.classify_intent(initial_state)
    """

    @inject
    def __init__(self, llm_port: ILLMPort, image_port: IImagePort):
        """의존성 주입: Port 인터페이스를 받음

        타입 힌트를 통해 자동으로 의존성이 주입됩니다.

        Args:
            llm_port: LLM 포트 (Anthropic든 OpenAI든 상관없음)
            image_port: 이미지 포트 (Replicate든 DALL-E든 상관없음)
        """
        self.llm_port = llm_port
        self.image_port = image_port

    async def classify_intent(self, state: CookingState) -> CookingState:
        """사용자 의도 분류 및 엔티티 추출

        Port를 통해 LLM 호출하여 의도를 분류합니다.

        Args:
            state: 현재 워크플로우 상태

        Returns:
            CookingState: 업데이트된 상태 (intent, entities 등)
        """
        try:
            # Port를 통해 LLM 호출 (구체적 구현 몰라도 됨)
            result = await self.llm_port.classify_intent(state["user_query"])

            # 비즈니스 규칙 적용
            state["primary_intent"] = result.get("primary_intent", "recipe_create")
            state["secondary_intents"] = result.get("secondary_intents", [])
            state["entities"] = result.get("entities", {})
            state["confidence"] = result.get("confidence", 0.5)

            logger.info(
                f"[CookingAssistant] 의도 분류 완료: "
                f"primary={state['primary_intent']}, "
                f"confidence={state['confidence']}"
            )

        except Exception as e:
            logger.error(f"[CookingAssistant] 의도 분류 실패: {str(e)}")
            # 기본값으로 폴백 (비즈니스 규칙)
            state["primary_intent"] = "recipe_create"
            state["secondary_intents"] = []
            state["entities"] = {}
            state["confidence"] = 0.5

        return state

    async def generate_recipe(self, state: CookingState) -> CookingState:
        """레시피 생성

        Port를 통해 LLM 호출하여 레시피를 생성합니다.

        Args:
            state: 현재 워크플로우 상태

        Returns:
            CookingState: 업데이트된 상태 (recipe_text, dish_names 등)
        """
        # Secondary intent 처리 (비즈니스 규칙)
        if state.get("secondary_intents") and state["secondary_intents"][0] == "recipe_create":
            state["secondary_intents"].pop(0)
            logger.info(f"[CookingAssistant] Secondary intent 'recipe_create' 제거")

        try:
            query = state["user_query"]
            entities = state.get("entities", {})

            # Port를 통해 레시피 생성
            recipe_data = await self.llm_port.generate_recipe(query, entities)

            # 비즈니스 규칙: 단일 vs 복수 레시피 처리
            if isinstance(recipe_data, list):
                # 복수 레시피
                state["recipes"] = recipe_data
                state["dish_names"] = [r.get("title", "") for r in recipe_data if r.get("title")]
                # recipe_text는 JSON 문자열로 저장 (API 응답용)
                import json
                state["recipe_text"] = json.dumps(recipe_data, ensure_ascii=False)
                logger.info(f"[CookingAssistant] 복수 레시피 생성 완료: {len(recipe_data)}개")

            elif isinstance(recipe_data, dict):
                # 단일 레시피
                import json
                state["recipe_text"] = json.dumps(recipe_data, ensure_ascii=False)
                title = recipe_data.get("title", "")
                state["dish_names"] = [title] if title else []
                logger.info(f"[CookingAssistant] 단일 레시피 생성 완료: {title}")

            else:
                raise TypeError(
                    f"레시피 데이터는 딕셔너리 또는 리스트여야 합니다. "
                    f"현재 타입: {type(recipe_data).__name__}"
                )

        except Exception as e:
            logger.error(f"[CookingAssistant] 레시피 생성 실패: {str(e)}")
            state["error"] = f"레시피 생성 실패: {str(e)}"

        return state

    async def recommend_dishes(self, state: CookingState) -> CookingState:
        """음식 추천

        Port를 통해 LLM 호출하여 음식을 추천합니다.

        Args:
            state: 현재 워크플로우 상태

        Returns:
            CookingState: 업데이트된 상태 (recommendation, dish_names 등)
        """
        # Secondary intent 처리
        if state.get("secondary_intents") and state["secondary_intents"][0] == "recommend":
            state["secondary_intents"].pop(0)
            logger.info(f"[CookingAssistant] Secondary intent 'recommend' 제거")

        try:
            query = state["user_query"]
            entities = state.get("entities", {})

            # Port를 통해 추천
            recommendation_data = await self.llm_port.recommend_dishes(query, entities)

            # 비즈니스 규칙: 추천 결과 처리
            if not isinstance(recommendation_data, dict):
                raise TypeError(
                    f"추천 데이터는 딕셔너리여야 합니다. "
                    f"현재 타입: {type(recommendation_data).__name__}"
                )

            # recommendation은 JSON 문자열로 저장 (API 응답용)
            import json
            state["recommendation"] = json.dumps(recommendation_data, ensure_ascii=False)

            # 추천받은 요리명을 dish_names에 저장 (이후 레시피 생성에 활용)
            recommendations = recommendation_data.get("recommendations", [])
            dish_names = [rec.get("name", "") for rec in recommendations if rec.get("name")]
            state["dish_names"] = dish_names

            logger.info(f"[CookingAssistant] 음식 추천 완료: {len(dish_names)}개")

        except Exception as e:
            logger.error(f"[CookingAssistant] 음식 추천 실패: {str(e)}")
            state["error"] = f"음식 추천 실패: {str(e)}"

        return state

    async def answer_question(self, state: CookingState) -> CookingState:
        """요리 관련 질문 답변

        Port를 통해 LLM 호출하여 질문에 답변합니다.

        Args:
            state: 현재 워크플로우 상태

        Returns:
            CookingState: 업데이트된 상태 (answer 등)
        """
        # Secondary intent 처리
        if state.get("secondary_intents") and state["secondary_intents"][0] == "question":
            state["secondary_intents"].pop(0)
            logger.info(f"[CookingAssistant] Secondary intent 'question' 제거")

        try:
            query = state["user_query"]

            # Port를 통해 질문 답변
            answer_data = await self.llm_port.answer_question(query)

            # 비즈니스 규칙: 답변 결과 처리
            if not isinstance(answer_data, dict):
                raise TypeError(
                    f"답변 데이터는 딕셔너리여야 합니다. "
                    f"현재 타입: {type(answer_data).__name__}"
                )

            # answer는 JSON 문자열로 저장 (API 응답용)
            import json
            state["answer"] = json.dumps(answer_data, ensure_ascii=False)

            logger.info(f"[CookingAssistant] 질문 답변 완료")

        except Exception as e:
            logger.error(f"[CookingAssistant] 질문 답변 실패: {str(e)}")
            state["error"] = f"질문 답변 실패: {str(e)}"

        return state

    async def generate_image(self, state: CookingState) -> CookingState:
        """이미지 생성

        Port를 통해 이미지를 생성합니다.
        이미지 생성 실패는 치명적이지 않으며, 레시피는 정상적으로 반환됩니다.

        Args:
            state: 현재 워크플로우 상태

        Returns:
            CookingState: 업데이트된 상태 (image_url 등)
        """
        # 비즈니스 규칙: dish_names가 없으면 이미지 생성 불가
        if not state.get("dish_names"):
            logger.info("[CookingAssistant] dish_names 없음, 이미지 생성 건너뜀")
            return state

        try:
            # 첫 번째 요리명으로 이미지 생성
            dish_name = state["dish_names"][0]

            # Port를 통해 프롬프트 생성
            prompt = self.image_port.generate_prompt(dish_name)
            state["image_prompt"] = prompt

            # Port를 통해 이미지 생성
            image_url = await self.image_port.generate_image(prompt)
            state["image_url"] = image_url

            if image_url:
                logger.info(f"[CookingAssistant] 이미지 생성 완료: {image_url}")
            else:
                logger.warning("[CookingAssistant] 이미지 생성 실패 (URL 없음)")

        except Exception as e:
            logger.warning(f"[CookingAssistant] 이미지 생성 중 예외 발생: {str(e)}")
            # 이미지 실패는 치명적이지 않음 (레시피는 반환)

        return state
