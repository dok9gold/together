from fastapi import APIRouter
from app.service.model.fridge import FridgeRecommendRequest, FridgeRecommendResponse
from app.service.fridge import FridgeService

router = APIRouter(prefix="/fridge", tags=["fridge"])

# Service 인스턴스
fridge_service = FridgeService()


@router.post("/recommend", response_model=FridgeRecommendResponse)
async def get_fridge_recommendations(request: FridgeRecommendRequest):
    """
    냉장고 재료 기반 레시피 추천

    냉장고에 있는 재료로 만들 수 있는 요리를 추천합니다.
    """
    return await fridge_service.get_recommendations(request)
