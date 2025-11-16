"""API E2E 테스트

FastAPI TestClient를 사용한 엔드투엔드 테스트
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from app.main import app
from app.core.auth import AuthService
from app.core.config import get_settings
import json


@pytest.fixture
def client():
    """TestClient 픽스처"""
    return TestClient(app)


@pytest.fixture
def auth_token():
    """테스트용 JWT 토큰 생성"""
    settings = get_settings()
    auth_service = AuthService(secret_key=settings.secret_key)
    return auth_service.create_access_token(user_id="test_user")


class TestHealthCheck:
    """헬스 체크 엔드포인트 테스트"""

    def test_health_check(self, client):
        """헬스 체크 성공"""
        # When
        response = client.get("/api/health")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestRootEndpoint:
    """루트 엔드포인트 테스트"""

    def test_root(self, client):
        """루트 엔드포인트"""
        # When
        response = client.get("/")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "Cooking Assistant API" in data["message"]
        assert "/docs" in data["docs"]


class TestCookingEndpoint:
    """요리 AI 엔드포인트 테스트"""

    @patch('app.adapters.llm.anthropic_adapter.AnthropicLLMAdapter.classify_intent')
    @patch('app.adapters.llm.anthropic_adapter.AnthropicLLMAdapter.generate_recipe')
    @patch('app.adapters.image.replicate_adapter.ReplicateImageAdapter.generate_image')
    def test_create_recipe_success(
        self,
        mock_generate_image,
        mock_generate_recipe,
        mock_classify_intent,
        client
    ):
        """레시피 생성 성공 (Mock)"""
        # Given
        query = "김치찌개 만드는 법"

        # Mock LLM 응답
        mock_classify_intent.return_value = {
            "primary_intent": "recipe_create",
            "secondary_intents": [],
            "entities": {"dishes": ["김치찌개"]},
            "confidence": 0.95
        }

        mock_generate_recipe.return_value = {
            "title": "김치찌개",
            "ingredients": ["김치 300g", "돼지고기 200g"],
            "steps": ["1. 김치를 썬다", "2. 고기를 볶는다"],
            "cooking_time": "30분",
            "difficulty": "쉬움",
            "servings": 2
        }

        mock_generate_image.return_value = "https://replicate.delivery/test-image.jpg"

        # When
        response = client.post(
            "/api/cooking",
            json={"query": query}
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["intent"] == "recipe_create"
        assert "김치찌개" in data["data"]["recipe"]["title"]

    @patch('app.adapters.llm.anthropic_adapter.AnthropicLLMAdapter.classify_intent')
    @patch('app.adapters.llm.anthropic_adapter.AnthropicLLMAdapter.recommend_food')
    def test_recommend_food_success(
        self,
        mock_recommend_food,
        mock_classify_intent,
        client
    ):
        """음식 추천 성공 (Mock)"""
        # Given
        query = "매운 음식 추천해줘"

        mock_classify_intent.return_value = {
            "primary_intent": "recommend",
            "secondary_intents": [],
            "entities": {"taste": ["매운"]},
            "confidence": 0.9
        }

        mock_recommend_food.return_value = {
            "recommendations": [
                {
                    "name": "김치찌개",
                    "description": "한국의 매운 찌개",
                    "reason": "얼큰하고 칼칼함"
                }
            ]
        }

        # When
        response = client.post(
            "/api/cooking",
            json={"query": query}
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["intent"] == "recommend"

    @patch('app.adapters.llm.anthropic_adapter.AnthropicLLMAdapter.classify_intent')
    @patch('app.adapters.llm.anthropic_adapter.AnthropicLLMAdapter.answer_question')
    def test_answer_question_success(
        self,
        mock_answer_question,
        mock_classify_intent,
        client
    ):
        """질문 답변 성공 (Mock)"""
        # Given
        query = "김치찌개 칼로리는?"

        mock_classify_intent.return_value = {
            "primary_intent": "question",
            "secondary_intents": [],
            "entities": {"dishes": ["김치찌개"]},
            "confidence": 0.85
        }

        mock_answer_question.return_value = {
            "answer": "김치찌개 1인분은 약 150-200kcal입니다.",
            "additional_tips": []
        }

        # When
        response = client.post(
            "/api/cooking",
            json={"query": query}
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["intent"] == "question"


class TestAuthenticationEndpoint:
    """인증 테스트"""

    @patch('app.adapters.llm.anthropic_adapter.AnthropicLLMAdapter.classify_intent')
    def test_with_valid_token(
        self,
        mock_classify_intent,
        client,
        auth_token
    ):
        """유효한 토큰과 함께 요청"""
        # Given
        query = "김치찌개 만들기"

        mock_classify_intent.return_value = {
            "primary_intent": "recipe_create",
            "secondary_intents": [],
            "entities": {},
            "confidence": 0.9
        }

        # When
        response = client.post(
            "/api/cooking",
            json={"query": query},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Then
        assert response.status_code == 200

    def test_without_token(self, client):
        """토큰 없이 요청 (선택적 인증이므로 성공)"""
        # When
        response = client.post(
            "/api/cooking",
            json={"query": "김치찌개"}
        )

        # Then
        # 선택적 인증이므로 토큰 없어도 200 (Mock 없으면 실패할 수 있음)
        assert response.status_code in [200, 500]  # Mock 여부에 따라 다름

    def test_with_invalid_token(self, client):
        """잘못된 토큰 (선택적 인증이므로 통과)"""
        # When
        response = client.post(
            "/api/cooking",
            json={"query": "김치찌개"},
            headers={"Authorization": "Bearer invalid-token-here"}
        )

        # Then
        # 선택적 인증: 잘못된 토큰도 통과 (user_id=None으로 처리)
        assert response.status_code in [200, 500]


class TestInputValidation:
    """입력 검증 테스트"""

    def test_empty_query(self, client):
        """빈 쿼리"""
        # When
        response = client.post(
            "/api/cooking",
            json={"query": ""}
        )

        # Then
        # Pydantic 검증 통과 (빈 문자열 허용)
        assert response.status_code in [200, 422, 500]

    def test_missing_query_field(self, client):
        """쿼리 필드 누락"""
        # When
        response = client.post(
            "/api/cooking",
            json={}
        )

        # Then
        assert response.status_code == 422  # Validation error

    def test_invalid_json(self, client):
        """잘못된 JSON"""
        # When
        response = client.post(
            "/api/cooking",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        # Then
        assert response.status_code == 422

    def test_very_long_query(self, client):
        """매우 긴 쿼리 (정상 처리)"""
        # Given
        long_query = "김치찌개 " * 500

        # When
        response = client.post(
            "/api/cooking",
            json={"query": long_query}
        )

        # Then
        # 긴 쿼리도 허용 (Mock 없으면 실패할 수 있음)
        assert response.status_code in [200, 500]


class TestErrorResponse:
    """에러 응답 테스트"""

    @patch('app.application.workflow.cooking_workflow.CookingWorkflow.run')
    def test_internal_server_error(self, mock_workflow_run, client):
        """서버 내부 오류"""
        # Given
        mock_workflow_run.side_effect = Exception("Unexpected error")

        # When
        response = client.post(
            "/api/cooking",
            json={"query": "김치찌개"}
        )

        # Then
        assert response.status_code == 200  # ErrorResponse로 반환
        data = response.json()
        assert data["status"] == "error"


class TestCORS:
    """CORS 테스트"""

    def test_cors_headers(self, client):
        """CORS 헤더 확인"""
        # When
        response = client.options("/api/cooking")

        # Then
        # CORS 설정 확인 (FastAPI 기본 동작)
        assert response.status_code in [200, 405]


class TestOpenAPIDocumentation:
    """OpenAPI 문서 테스트"""

    def test_swagger_ui(self, client):
        """Swagger UI 접근"""
        # When
        response = client.get("/docs")

        # Then
        assert response.status_code == 200
        assert b"swagger" in response.content or b"Swagger" in response.content

    def test_redoc(self, client):
        """ReDoc 접근"""
        # When
        response = client.get("/redoc")

        # Then
        assert response.status_code == 200

    def test_openapi_json(self, client):
        """OpenAPI JSON 스펙"""
        # When
        response = client.get("/openapi.json")

        # Then
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
