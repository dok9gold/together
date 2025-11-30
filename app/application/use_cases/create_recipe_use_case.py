"""CreateRecipeUseCase - 레시피 생성 유스케이스

워크플로우를 실행하여 레시피를 생성합니다.
"""
from app.core.decorators import inject
from app.application.workflow.cooking_workflow import CookingWorkflow
from app.domain.entities.cooking_state import CookingState, create_initial_state
from app.models.schemas import (
    CookingResponse,
    RecipeResponse,
    RecipeResponseData,
    RecommendationResponse,
    RecommendationResponseData,
    QuestionResponse,
    QuestionResponseData,
    ErrorResponse,
    ResponseMetadata,
    Recommendation
)
from app.domain.response_codes import ResponseCode
from app.domain.exceptions import (
    DomainException,
    LLMServiceError,
    ImageGenerationError,
    WorkflowError,
    ParsingError,
    ValidationError
)
import logging
import json
from typing import Union, Optional

logger = logging.getLogger(__name__)


class CreateRecipeUseCase:
    """레시피 생성 유스케이스

    책임:
    - 초기 상태 생성 (Factory 사용)
    - 워크플로우 실행
    - Domain Entity (CookingState) → DTO 변환
    - 응답 반환

    Attributes:
        workflow: LangGraph 워크플로우
    """

    @inject
    def __init__(self, workflow: CookingWorkflow):
        """의존성 주입: 워크플로우

        타입 힌트를 통해 자동으로 의존성이 주입됩니다.

        Args:
            workflow: 요리 AI 어시스턴트 워크플로우
        """
        self.workflow = workflow

    async def execute(
        self,
        query: str,
        user_id: Optional[str] = None
    ) -> CookingResponse:
        """레시피 생성 워크플로우 실행 및 DTO 변환

        전체 워크플로우:
        1. 의도 분류
        2. 의도에 따라 분기 (레시피/추천/질문)
        3. 레시피 생성 시 이미지 생성
        4. Secondary intents 처리 (복합 의도)
        5. Domain Entity → DTO 변환

        Args:
            query: 사용자 쿼리
                예: "파스타 카르보나라 만드는 법"
            user_id: 사용자 ID (선택적, 인증된 경우 전달됨)
                - 향후 개인화 기능에 활용 가능
                - 사용자 선호도, 히스토리 조회 등

        Returns:
            CookingResponse: 의도별 응답 DTO (RecipeResponse, RecommendationResponse, QuestionResponse, ErrorResponse)
        """
        logger.info(f"[UseCase] 실행 시작 - user_id: {user_id}, query: {query[:50]}...")

        try:
            # 1. 초기 상태 생성 (Factory 사용)
            initial_state = create_initial_state(query)

            # 2. user_id를 state에 추가 (향후 개인화 기능에서 활용)
            initial_state["user_id"] = user_id

            # 2. 워크플로우 실행
            result: CookingState = await self.workflow.run(initial_state)

            logger.info(f"[UseCase] 워크플로우 실행 완료")

            # 3. Domain → DTO 변환
            response = self._to_dto(result)

            logger.info(f"[UseCase] DTO 변환 완료 - intent: {result['primary_intent']}")

            return response

        except ImageGenerationError as e:
            # 이미지 생성 실패는 레시피는 반환 (우아한 성능 저하)
            logger.warning(f"[UseCase] 이미지 생성 실패: {e}")

            # 이미지 없이 레시피 응답 생성
            response = self._to_dto(result)

            # 에러 메시지 추가
            if isinstance(response, RecipeResponse):
                response.message = f"레시피는 생성되었으나 이미지 생성에 실패했습니다: {e.message}"

            return response

        except LLMServiceError as e:
            # LLM 서비스 오류 (치명적)
            logger.error(f"[UseCase] LLM 서비스 오류: {e}", exc_info=True)
            return ErrorResponse(
                code=e.code or ResponseCode.INTERNAL_ERROR,
                message=f"AI 서비스 오류: {e.message}",
                data=e.details if e.details else None
            )

        except (ParsingError, ValidationError) as e:
            # 데이터 파싱/검증 실패
            logger.error(f"[UseCase] 데이터 처리 오류: {e}", exc_info=True)
            return ErrorResponse(
                code=e.code or ResponseCode.INTERNAL_ERROR,
                message=f"데이터 처리 오류: {e.message}",
                data=e.details if e.details else None
            )

        except WorkflowError as e:
            # 워크플로우 실행 오류
            logger.error(f"[UseCase] 워크플로우 오류: {e}", exc_info=True)
            return ErrorResponse(
                code=e.code or ResponseCode.INTERNAL_ERROR,
                message=f"워크플로우 실행 오류: {e.message}",
                data=e.details if e.details else None
            )

        except DomainException as e:
            # 기타 도메인 예외
            logger.error(f"[UseCase] 도메인 오류: {e}", exc_info=True)
            return ErrorResponse(
                code=e.code or ResponseCode.INTERNAL_ERROR,
                message=e.message,
                data=e.details if e.details else None
            )

        except Exception as e:
            # 예상치 못한 오류
            logger.error(f"[UseCase] 예상치 못한 오류: {e}", exc_info=True)
            return ErrorResponse(
                code=ResponseCode.INTERNAL_ERROR,
                message=f"서버 오류: {str(e)}"
            )

    def _to_dto(self, state: CookingState) -> CookingResponse:
        """Domain Entity → DTO 변환

        기존 routes.py의 파싱/변환 로직을 여기로 이동.
        의도별로 적절한 Response DTO를 생성합니다.

        Args:
            state: 워크플로우 실행 결과 상태

        Returns:
            CookingResponse: 의도별 응답 DTO
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
            secondary_intents_processed=state.get("secondary_intents", [])
        )

        # 의도별 분기
        if intent == "recipe_create":
            return self._create_recipe_response(state, metadata)
        elif intent == "recommend":
            return self._create_recommendation_response(state, metadata)
        elif intent == "question":
            return self._create_question_response(state, metadata)
        else:
            return ErrorResponse(
                code=ResponseCode.INVALID_INTENT,
                intent=intent,
                message=f"알 수 없는 의도: {intent}"
            )

    def _create_recipe_response(self, state: CookingState, metadata: ResponseMetadata) -> Union[RecipeResponse, ErrorResponse]:
        """레시피 응답 DTO 생성"""
        try:
            if not state.get("recipe_text"):
                return ErrorResponse(
                    code=ResponseCode.RECIPE_PARSE_ERROR,
                    intent="recipe_create",
                    message="레시피 데이터가 없습니다"
                )

            # JSON 파싱
            recipe_data = json.loads(state["recipe_text"])

            # 단일 레시피 vs 복수 레시피 분기
            data = RecipeResponseData(metadata=metadata)
            if isinstance(recipe_data, list):
                data.recipes = recipe_data
            elif isinstance(recipe_data, dict):
                data.recipe = recipe_data
            else:
                return ErrorResponse(
                    code=ResponseCode.RECIPE_PARSE_ERROR,
                    intent="recipe_create",
                    message="레시피 데이터 형식이 잘못되었습니다"
                )

            # 이미지 URL 추가
            data.image_url = state.get("image_url")

            # 응답 생성
            return RecipeResponse(
                code=ResponseCode.RECIPE_CREATED,
                data=data,
                message="이미지 생성 실패" if not state.get("image_url") else None
            )

        except json.JSONDecodeError as e:
            logger.error(f"[UseCase] 레시피 파싱 실패: {e}")
            return ErrorResponse(
                code=ResponseCode.RECIPE_PARSE_ERROR,
                intent="recipe_create",
                message=f"레시피 파싱 실패: {str(e)}"
            )

    def _create_recommendation_response(self, state: CookingState, metadata: ResponseMetadata) -> Union[RecommendationResponse, ErrorResponse]:
        """추천 응답 DTO 생성"""
        try:
            if not state.get("recommendation"):
                return ErrorResponse(
                    code=ResponseCode.RECOMMENDATION_PARSE_ERROR,
                    intent="recommend",
                    message="추천 데이터가 없습니다"
                )

            # JSON 파싱
            recommendation_data = json.loads(state["recommendation"])
            recommendations_raw = recommendation_data.get("recommendations", [])

            # 클리닝 (name, description, reason만 유지)
            cleaned_recommendations = [
                Recommendation(
                    name=rec.get("name", ""),
                    description=rec.get("description", ""),
                    reason=rec.get("reason", "")
                )
                for rec in recommendations_raw
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

        except json.JSONDecodeError as e:
            logger.error(f"[UseCase] 추천 파싱 실패: {e}")
            return ErrorResponse(
                code=ResponseCode.RECOMMENDATION_PARSE_ERROR,
                intent="recommend",
                message=f"추천 파싱 실패: {str(e)}"
            )

    def _create_question_response(self, state: CookingState, metadata: ResponseMetadata) -> Union[QuestionResponse, ErrorResponse]:
        """질문 답변 응답 DTO 생성"""
        try:
            if not state.get("answer"):
                return ErrorResponse(
                    code=ResponseCode.QUESTION_PARSE_ERROR,
                    intent="question",
                    message="답변 데이터가 없습니다"
                )

            # JSON 파싱
            answer_data = json.loads(state["answer"])

            # 응답 생성
            data = QuestionResponseData(
                answer=answer_data.get("answer", ""),
                additional_tips=answer_data.get("additional_tips", []),
                metadata=metadata
            )

            return QuestionResponse(
                code=ResponseCode.QUESTION_ANSWERED,
                data=data
            )

        except json.JSONDecodeError as e:
            logger.error(f"[UseCase] 답변 파싱 실패: {e}")
            return ErrorResponse(
                code=ResponseCode.QUESTION_PARSE_ERROR,
                intent="question",
                message=f"답변 파싱 실패: {str(e)}"
            )
