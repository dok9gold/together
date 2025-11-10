from fastapi import APIRouter, Depends
from app.models.schemas import CookingRequest, CookingResponse
from app.api.dependencies import get_create_recipe_use_case
from app.application.use_cases.create_recipe_use_case import CreateRecipeUseCase

router = APIRouter()


@router.post("/cooking", response_model=CookingResponse)
async def handle_cooking_query(
    request: CookingRequest,
    use_case: CreateRecipeUseCase = Depends(get_create_recipe_use_case)
):
    """
    요리 AI 어시스턴트 API

    사용자 쿼리의 의도를 파악하여 적절한 응답을 생성합니다:
    - 레시피 생성: 상세한 조리법과 이미지
    - 음식 추천: 맞춤형 메뉴 제안
    - 질문 답변: 요리 관련 정보 제공

    Args:
        request: 요리 쿼리 요청
            - query: 요리 관련 쿼리
                - 예: "파스타 카르보나라 만드는 법" (레시피 생성)
                - 예: "매운 음식 추천해줘" (음식 추천)
                - 예: "김치찌개 칼로리는?" (질문 답변)

    Returns:
        CookingResponse: 의도별 응답 DTO
            - RecipeResponse: 레시피 생성 응답
            - RecommendationResponse: 음식 추천 응답
            - QuestionResponse: 질문 답변 응답
            - ErrorResponse: 에러 응답

    Note:
        UseCase가 모든 변환 로직을 처리하므로 routes는 단순히 호출 및 반환만 수행합니다.
    """
    # UseCase 실행 (Domain → DTO 변환 포함)
    return await use_case.execute(request.query)


@router.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "service": "cooking-assistant"}