"""CookingService - 요리 AI 비즈니스 로직 서비스

Service Layer 책임:
- 비즈니스 로직 조합 (Workflow/Repository/API 호출)
- Domain Entity → DTO 변환
- 예외 처리 및 응답 생성

Workflow뿐만 아니라 DB/외부 API도 호출 가능:
- AI 처리: Workflow 직접 호출
- DB 조회: IRecipeRepository 호출 (향후)
- 외부 API: INutritionAPI 호출 (향후)
"""
from app.core.decorators import singleton, inject
from app.cooking_assistant.workflow.cooking_workflow import CookingWorkflow
from app.cooking_assistant.workflow.states.cooking_state import CookingState, create_initial_state
from app.cooking_assistant.models.schemas import (
    CookingResponse,
    RecipeResponse,
    RecipeResponseData,
    RecommendationResponse,
    RecommendationResponseData,
    QuestionResponse,
    QuestionResponseData,
    ErrorResponse,
    ResponseMetadata,
    Recommendation,
    SecondaryIntentResult
)
from app.cooking_assistant.models.response_codes import ResponseCode
from app.cooking_assistant.exceptions import (
    DomainException,
    LLMServiceError,
    ImageGenerationError,
    WorkflowError,
    ParsingError,
    ValidationError
)
import logging
from dataclasses import asdict
from typing import Union, Optional, List

logger = logging.getLogger(__name__)


@singleton
class CookingService:
    """요리 AI 비즈니스 로직 서비스

    책임:
    - Workflow 실행 및 DTO 변환 (AI 처리)
    - DB 조회 (향후)
    - 외부 API 호출 (향후)
    - 예외 처리 및 에러 응답 생성

    Attributes:
        workflow: LangGraph 워크플로우
        # 향후 추가 가능:
        # recipe_repository: IRecipeRepository (DB 조회)
        # nutrition_api: INutritionAPI (외부 API)
    """

    @inject
    def __init__(
        self,
        workflow: CookingWorkflow
        # recipe_repository: IRecipeRepository = None,
        # nutrition_api: INutritionAPI = None
    ):
        """의존성 주입

        Args:
            workflow: LangGraph 워크플로우
        """
        self.workflow = workflow

    async def process_cooking_query(
        self,
        query: str,
        user_id: Optional[str] = None
    ) -> CookingResponse:
        """요리 관련 쿼리 처리 (AI Workflow)

        전체 흐름:
        1. Workflow 실행 (Domain Entity 반환)
        2. Domain → DTO 변환
        3. 에러 처리 및 응답 생성

        Args:
            query: 사용자 쿼리
                예: "파스타 카르보나라 만드는 법"
            user_id: 사용자 ID (선택적, 인증된 경우 전달됨)

        Returns:
            CookingResponse: 의도별 응답 DTO
        """
        logger.info(f"[Service] 쿼리 처리 시작 - user_id: {user_id}, query: {query[:50]}...")

        try:
            # 1. 초기 상태 생성
            initial_state = create_initial_state(query)
            initial_state["user_id"] = user_id

            # 2. Workflow 직접 실행
            result: CookingState = await self.workflow.run(initial_state)

            logger.info(f"[Service] Workflow 실행 완료")

            # 3. Domain → DTO 변환
            response = self._to_dto(result)

            logger.info(f"[Service] DTO 변환 완료 - intent: {result['primary_intent']}")

            return response

        except ImageGenerationError as e:
            # 이미지 생성 실패는 레시피는 반환 (우아한 성능 저하)
            logger.warning(f"[Service] 이미지 생성 실패: {e}")

            # 이미지 없이 레시피 응답 생성
            response = self._to_dto(result)

            # 에러 메시지 추가
            if isinstance(response, RecipeResponse):
                response.message = f"레시피는 생성되었으나 이미지 생성에 실패했습니다: {e.message}"

            return response

        except LLMServiceError as e:
            # LLM 서비스 오류 (치명적)
            logger.error(f"[Service] LLM 서비스 오류: {e}", exc_info=True)
            return ErrorResponse(
                code=e.code or ResponseCode.INTERNAL_ERROR,
                message=f"AI 서비스 오류: {e.message}",
                data=e.details if e.details else None
            )

        except (ParsingError, ValidationError) as e:
            # 데이터 파싱/검증 실패
            logger.error(f"[Service] 데이터 처리 오류: {e}", exc_info=True)
            return ErrorResponse(
                code=e.code or ResponseCode.INTERNAL_ERROR,
                message=f"데이터 처리 오류: {e.message}",
                data=e.details if e.details else None
            )

        except WorkflowError as e:
            # 워크플로우 실행 오류
            logger.error(f"[Service] 워크플로우 오류: {e}", exc_info=True)
            return ErrorResponse(
                code=e.code or ResponseCode.INTERNAL_ERROR,
                message=f"워크플로우 실행 오류: {e.message}",
                data=e.details if e.details else None
            )

        except DomainException as e:
            # 기타 도메인 예외
            logger.error(f"[Service] 도메인 오류: {e}", exc_info=True)
            return ErrorResponse(
                code=e.code or ResponseCode.INTERNAL_ERROR,
                message=e.message,
                data=e.details if e.details else None
            )

        except Exception as e:
            # 예상치 못한 오류
            logger.error(f"[Service] 예상치 못한 오류: {e}", exc_info=True)
            return ErrorResponse(
                code=ResponseCode.INTERNAL_ERROR,
                message=f"서버 오류: {str(e)}"
            )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 향후 DB 조회 예시 (레시피 저장 기능 추가 시)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # async def get_saved_recipe(self, recipe_id: str) -> RecipeResponse:
    #     """저장된 레시피 조회 (DB)
    #
    #     Workflow를 사용하지 않고 Repository에서 직접 조회
    #
    #     Args:
    #         recipe_id: 레시피 ID
    #
    #     Returns:
    #         RecipeResponse: 레시피 응답 DTO
    #     """
    #     recipe = await self.recipe_repository.find_by_id(recipe_id)
    #     return self._recipe_entity_to_dto(recipe)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 향후 외부 API 호출 예시 (영양 정보 추가 시)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # async def get_nutrition_info(self, dish_name: str) -> NutritionResponse:
    #     """영양 정보 조회 (외부 API)
    #
    #     Workflow를 사용하지 않고 외부 API 직접 호출
    #
    #     Args:
    #         dish_name: 요리 이름
    #
    #     Returns:
    #         NutritionResponse: 영양 정보 응답 DTO
    #     """
    #     nutrition = await self.nutrition_api.get_nutrition(dish_name)
    #     return self._nutrition_to_dto(nutrition)

    def _to_dto(self, state: CookingState) -> CookingResponse:
        """Domain Entity → DTO 변환

        의도별로 적절한 Response DTO를 생성합니다.
        Secondary intents 처리 결과도 함께 포함합니다.

        Args:
            state: 워크플로우 실행 결과 상태

        Returns:
            CookingResponse: 의도별 응답 DTO (secondary intents 결과 포함)
        """
        # 에러 처리
        if state.get("error"):
            return ErrorResponse(
                code=ResponseCode.WORKFLOW_ERROR,
                intent=state.get("primary_intent"),
                message=state["error"]
            )

        intent = state["primary_intent"]

        # 메타데이터 생성 (공통)
        metadata = ResponseMetadata(
            entities=state.get("entities", {}),
            confidence=state.get("confidence", 0.0),
            secondary_intents_processed=state.get("processed_secondary_intents", [])
        )

        # Secondary intents 결과 수집
        secondary_results = self._collect_secondary_results(state)

        # 의도별 분기 (Primary intent 응답 생성)
        if intent == "recipe_create":
            response = self._create_recipe_response(state, metadata)
        elif intent == "recommend":
            response = self._create_recommendation_response(state, metadata)
        elif intent == "question":
            response = self._create_question_response(state, metadata)
        else:
            return ErrorResponse(
                code=ResponseCode.INVALID_INTENT,
                intent=intent,
                message=f"알 수 없는 의도: {intent}"
            )

        # Secondary results 추가 (ErrorResponse가 아닌 경우만)
        if not isinstance(response, ErrorResponse) and secondary_results:
            response.data.secondary_results = secondary_results

        return response

    def _create_recipe_response(self, state: CookingState, metadata: ResponseMetadata) -> Union[RecipeResponse, ErrorResponse]:
        """레시피 응답 DTO 생성 (Entity → DTO 변환)"""
        try:
            # 단일 레시피 vs 복수 레시피 분기
            data = RecipeResponseData(metadata=metadata)

            if state.get("recipes"):
                # 복수 레시피: List[Recipe] → List[dict]
                recipes = state["recipes"]
                data.recipes = [asdict(recipe) for recipe in recipes]

            elif state.get("recipe"):
                # 단일 레시피: Recipe → dict
                recipe = state["recipe"]
                data.recipe = asdict(recipe)

            else:
                return ErrorResponse(
                    code=ResponseCode.RECIPE_PARSE_ERROR,
                    intent="recipe_create",
                    message="레시피 데이터가 없습니다"
                )

            # 이미지 URL 추가
            data.image_url = state.get("image_url")

            # 응답 생성
            return RecipeResponse(
                code=ResponseCode.RECIPE_CREATED,
                data=data,
                message="이미지 생성 실패" if not state.get("image_url") else None
            )

        except Exception as e:
            logger.error(f"[Service] 레시피 DTO 변환 실패: {e}")
            return ErrorResponse(
                code=ResponseCode.RECIPE_PARSE_ERROR,
                intent="recipe_create",
                message=f"레시피 DTO 변환 실패: {str(e)}"
            )

    def _create_recommendation_response(self, state: CookingState, metadata: ResponseMetadata) -> Union[RecommendationResponse, ErrorResponse]:
        """추천 응답 DTO 생성 (Entity → DTO 변환)"""
        try:
            if not state.get("recommendation"):
                return ErrorResponse(
                    code=ResponseCode.RECOMMENDATION_PARSE_ERROR,
                    intent="recommend",
                    message="추천 데이터가 없습니다"
                )

            # Entity → DTO: Recommendation → List[dict]
            recommendation_entity = state["recommendation"]

            # DishRecommendation 리스트를 dict 리스트로 변환
            cleaned_recommendations = [
                Recommendation(
                    name=dish_rec.name,
                    description=dish_rec.description,
                    reason=dish_rec.reason
                )
                for dish_rec in recommendation_entity.recommendations
            ]

            # 응답 생성
            data = RecommendationResponseData(
                recommendations=cleaned_recommendations,
                metadata=metadata
            )

            return RecommendationResponse(
                code=ResponseCode.RECOMMENDATION_SUCCESS,
                data=data
            )

        except Exception as e:
            logger.error(f"[Service] 추천 DTO 변환 실패: {e}")
            return ErrorResponse(
                code=ResponseCode.RECOMMENDATION_PARSE_ERROR,
                intent="recommend",
                message=f"추천 DTO 변환 실패: {str(e)}"
            )

    def _create_question_response(self, state: CookingState, metadata: ResponseMetadata) -> Union[QuestionResponse, ErrorResponse]:
        """질문 답변 응답 DTO 생성 (Entity → DTO 변환)"""
        try:
            if not state.get("answer"):
                return ErrorResponse(
                    code=ResponseCode.QUESTION_PARSE_ERROR,
                    intent="question",
                    message="답변 데이터가 없습니다"
                )

            # Entity → DTO: Answer → dict
            answer_entity = state["answer"]

            # 응답 생성
            data = QuestionResponseData(
                answer=answer_entity.answer,
                additional_tips=answer_entity.additional_tips,
                metadata=metadata
            )

            return QuestionResponse(
                code=ResponseCode.QUESTION_ANSWERED,
                data=data
            )

        except Exception as e:
            logger.error(f"[Service] 답변 DTO 변환 실패: {e}")
            return ErrorResponse(
                code=ResponseCode.QUESTION_PARSE_ERROR,
                intent="question",
                message=f"답변 DTO 변환 실패: {str(e)}"
            )

    def _collect_secondary_results(self, state: CookingState) -> List[SecondaryIntentResult]:
        """Secondary intents 처리 결과 수집

        processed_secondary_intents에 기록된 각 intent별로
        state에서 해당 결과를 추출하여 SecondaryIntentResult 리스트로 반환합니다.

        Args:
            state: 워크플로우 실행 결과 상태

        Returns:
            List[SecondaryIntentResult]: Secondary intent 처리 결과 리스트
        """
        results = []
        processed = state.get("processed_secondary_intents", [])

        for intent in processed:
            try:
                result = self._extract_result_by_intent(intent, state)
                if result:
                    results.append(result)
            except Exception as e:
                logger.warning(f"[Service] Secondary intent '{intent}' 결과 추출 실패: {e}")
                # 실패해도 계속 진행 (다른 intent 결과는 포함)
                continue

        return results

    def _extract_result_by_intent(self, intent: str, state: CookingState) -> Optional[SecondaryIntentResult]:
        """Intent에 해당하는 결과를 state에서 추출

        Args:
            intent: Intent 이름 (예: "recipe_create", "recommend", "question")
            state: 워크플로우 실행 결과 상태

        Returns:
            Optional[SecondaryIntentResult]: 추출된 결과 (없으면 None)
        """
        if intent == "recipe_create":
            # 레시피 결과 추출
            recipe = state.get("recipe")
            recipes = state.get("recipes")

            if recipe or recipes:
                return SecondaryIntentResult(
                    intent=intent,
                    recipe=asdict(recipe) if recipe else None,
                    recipes=[asdict(r) for r in recipes] if recipes else None,
                    image_url=state.get("image_url")
                )

        elif intent == "recommend":
            # 추천 결과 추출
            recommendation = state.get("recommendation")

            if recommendation:
                cleaned_recommendations = [
                    Recommendation(
                        name=dish_rec.name,
                        description=dish_rec.description,
                        reason=dish_rec.reason
                    )
                    for dish_rec in recommendation.recommendations
                ]

                return SecondaryIntentResult(
                    intent=intent,
                    recommendations=cleaned_recommendations
                )

        elif intent == "question":
            # 질문 답변 결과 추출
            answer = state.get("answer")

            if answer:
                return SecondaryIntentResult(
                    intent=intent,
                    answer=answer.answer,
                    additional_tips=answer.additional_tips
                )

        elif intent == "generate_image":
            # 이미지 생성 결과 추출
            image_url = state.get("image_url")

            if image_url:
                return SecondaryIntentResult(
                    intent=intent,
                    image_url=image_url
                )

        # 결과가 없는 경우
        logger.debug(f"[Service] Intent '{intent}'에 대한 결과가 state에 없습니다")
        return None
