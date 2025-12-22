from fastapi import APIRouter, Depends
from typing import Optional
from app.cooking_assistant.models.schemas import CookingRequest, CookingResponse
from app.core.dependencies import get_optional_user
from app.cooking_assistant.services.cooking_service import CookingService
from app.core.decorators import get_dependency

router = APIRouter()


@router.post("/cooking", response_model=CookingResponse)
async def handle_cooking_query(
    request: CookingRequest,
    user_id: Optional[str] = Depends(get_optional_user),
    service: CookingService = Depends(get_dependency(CookingService))
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
        user_id: 사용자 ID (선택적 인증)
            - Authorization 헤더의 Bearer 토큰에서 추출
            - 토큰이 없으면 None (익명 사용자)
        service: CookingService (Service Layer)
            - 비즈니스 로직 조합 및 DTO 변환 담당
            - Workflow/Repository/API 호출 가능

    Returns:
        CookingResponse: 의도별 응답 DTO
            - RecipeResponse: 레시피 생성 응답
            - RecommendationResponse: 음식 추천 응답
            - QuestionResponse: 질문 답변 응답
            - ErrorResponse: 에러 응답

    Note:
        - 선택적 인증(get_optional_user): 토큰이 없어도 접근 가능
        - 토큰이 있으면 user_id를 Service에 전달하여 개인화 가능
        - Service가 모든 비즈니스 로직 및 DTO 변환을 처리
        - Service는 AI Workflow 외에도 DB 조회, 외부 API 호출 가능
    """
    # Service 실행 (Workflow → DTO 변환 포함, user_id 전달)
    return await service.process_cooking_query(request.query, user_id=user_id)


@router.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "service": "cooking-assistant"}