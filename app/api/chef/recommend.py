from fastapi import APIRouter
from app.service.chef.model.recommend import RecommendRequest, RecommendResponse
from app.service.chef.recommend import RecommendService

router = APIRouter(prefix="/recommend", tags=["recommend"])

# Service 인스턴스
recommend_service = RecommendService()


@router.post("", response_model=RecommendResponse)
async def get_recommendations(request: RecommendRequest):
    """
    요리 추천

    카테고리(한식, 중식, 일식, 양식)와 조건을 기반으로 요리를 추천합니다.
    """
    return await recommend_service.get_recommendations(request)
