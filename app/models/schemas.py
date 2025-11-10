from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union, Literal
from datetime import datetime


# ============ Request DTOs ============

class CookingRequest(BaseModel):
    """요리 관련 요청 (레시피 생성, 추천, 질문 등)"""
    query: str = Field(..., description="요리 관련 쿼리 (예: '파스타 카르보나라 만드는 법', '매운 음식 추천해줘', '김치찌개 칼로리는?')")


# ============ Response DTOs ============

class ResponseMetadata(BaseModel):
    """응답 메타데이터 (모든 응답에 공통)"""
    entities: Dict[str, Any] = Field(default_factory=dict, description="추출된 엔티티")
    confidence: float = Field(default=0.0, description="의도 파악 확신도")
    secondary_intents_processed: List[str] = Field(default_factory=list, description="처리된 부가 의도들")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 생성 시각")


class Recommendation(BaseModel):
    """음식 추천 항목"""
    name: str = Field(..., description="요리명")
    description: str = Field(..., description="요리 설명")
    reason: str = Field(..., description="추천 이유")


# ============ 의도별 Data DTOs ============

class RecipeResponseData(BaseModel):
    """레시피 생성 응답 데이터"""
    recipe: Optional[Dict[str, Any]] = Field(None, description="단일 레시피")
    recipes: Optional[List[Dict[str, Any]]] = Field(None, description="복수 레시피")
    image_url: Optional[str] = Field(None, description="생성된 음식 이미지 URL")
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)


class RecommendationResponseData(BaseModel):
    """음식 추천 응답 데이터"""
    recommendations: List[Recommendation] = Field(default_factory=list, description="추천 음식 목록")
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)


class QuestionResponseData(BaseModel):
    """질문 답변 응답 데이터"""
    answer: str = Field(..., description="질문에 대한 답변")
    additional_tips: List[str] = Field(default_factory=list, description="추가 팁")
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)


# ============ 최종 Response 모델 (의도별) ============

class RecipeResponse(BaseModel):
    """레시피 생성 응답"""
    status: Literal["success", "error"] = "success"
    code: str = Field(..., description="응답 코드 (예: RECIPE_CREATED)")
    intent: Literal["recipe_create"] = "recipe_create"
    data: RecipeResponseData
    message: Optional[str] = Field(None, description="추가 메시지 (예: 이미지 생성 실패)")


class RecommendationResponse(BaseModel):
    """음식 추천 응답"""
    status: Literal["success", "error"] = "success"
    code: str = Field(..., description="응답 코드 (예: RECOMMENDATION_SUCCESS)")
    intent: Literal["recommend"] = "recommend"
    data: RecommendationResponseData
    message: Optional[str] = None


class QuestionResponse(BaseModel):
    """질문 답변 응답"""
    status: Literal["success", "error"] = "success"
    code: str = Field(..., description="응답 코드 (예: QUESTION_ANSWERED)")
    intent: Literal["question"] = "question"
    data: QuestionResponseData
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """에러 응답"""
    status: Literal["error"] = "error"
    code: str = Field(..., description="에러 코드 (예: INTERNAL_ERROR)")
    intent: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    message: str = Field(..., description="에러 메시지")


# ============ Union Type (FastAPI response_model용) ============

CookingResponse = Union[RecipeResponse, RecommendationResponse, QuestionResponse, ErrorResponse]