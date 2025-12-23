from fastapi import APIRouter, HTTPException
from typing import List
from app.service.model.recipe import RecipeSearchResponse, RecipeDetail
from app.service.recipe import RecipeService

router = APIRouter(prefix="/recipe", tags=["recipe"])

# Service 인스턴스
recipe_service = RecipeService()


@router.get("/search", response_model=RecipeSearchResponse)
async def search_recipes(keyword: str):
    """
    레시피 검색

    요리명 키워드로 레시피를 검색합니다.
    """
    return await recipe_service.search(keyword)


@router.get("/popular", response_model=List[str])
async def get_popular_keywords():
    """
    인기 검색어 조회

    빠른 검색을 위한 인기 검색어 목록을 반환합니다.
    """
    return await recipe_service.get_popular_keywords()


@router.get("/{recipe_id}", response_model=RecipeDetail)
async def get_recipe_detail(recipe_id: str):
    """
    레시피 상세 조회

    레시피의 상세 정보(재료 분량, 조리 단계 등)를 조회합니다.
    """
    result = await recipe_service.get_detail(recipe_id)
    if not result:
        raise HTTPException(status_code=404, detail="레시피를 찾을 수 없습니다")
    return result
