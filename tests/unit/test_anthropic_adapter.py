"""Anthropic LLM Adapter 단위 테스트

Port/Adapter 패턴의 핵심: Mock을 사용하여 외부 API 없이 테스트
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from app.adapters.llm.anthropic_adapter import AnthropicLLMAdapter
from app.core.config import get_settings
from app.core.prompt_loader import PromptLoader
from app.domain.exceptions import LLMServiceError, ParsingError
import json


@pytest.fixture
def mock_settings():
    """Mock Settings 픽스처"""
    settings = Mock()
    settings.anthropic_api_key = "test-api-key"
    settings.llm_model = "claude-sonnet-4-5-20250929"
    settings.llm_temperature = 0.7
    settings.llm_max_tokens = 4096
    settings.llm_timeout = 90
    return settings


@pytest.fixture
def mock_prompt_loader():
    """Mock PromptLoader 픽스처"""
    loader = Mock(spec=PromptLoader)
    loader.render = Mock(return_value="Mocked prompt template")
    return loader


@pytest.fixture
def adapter(mock_settings, mock_prompt_loader):
    """AnthropicLLMAdapter 픽스처"""
    return AnthropicLLMAdapter(
        settings=mock_settings,
        prompt_loader=mock_prompt_loader
    )


class TestAnthropicAdapterInitialization:
    """Adapter 초기화 테스트"""

    def test_adapter_creation(self, adapter, mock_settings):
        """Adapter 생성 확인"""
        assert adapter.settings == mock_settings
        assert adapter.client is not None

    def test_adapter_with_settings(self, mock_settings, mock_prompt_loader):
        """설정값 주입 확인"""
        adapter = AnthropicLLMAdapter(
            settings=mock_settings,
            prompt_loader=mock_prompt_loader
        )

        assert adapter.settings.llm_model == "claude-sonnet-4-5-20250929"
        assert adapter.settings.llm_temperature == 0.7


class TestClassifyIntent:
    """의도 분류 테스트"""

    @pytest.mark.asyncio
    async def test_classify_intent_success(self, adapter, mock_prompt_loader):
        """의도 분류 성공 (Mock)"""
        # Given
        query = "김치찌개 만드는 법"
        expected_response = {
            "primary_intent": "recipe_create",
            "secondary_intents": [],
            "entities": {
                "dishes": ["김치찌개"]
            },
            "confidence": 0.95
        }

        # Mock Anthropic API 응답
        mock_message = Mock()
        mock_message.content = [Mock(text=json.dumps(expected_response))]

        with patch.object(adapter.client.messages, 'create', return_value=mock_message):
            # When
            result = await adapter.classify_intent(query)

        # Then
        assert result["primary_intent"] == "recipe_create"
        assert result["confidence"] == 0.95
        assert "김치찌개" in result["entities"]["dishes"]

        # PromptLoader 호출 확인
        mock_prompt_loader.render.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_intent_with_secondary_intents(self, adapter):
        """복합 의도 분류"""
        # Given
        query = "매운 음식 추천하고 그 중 하나 레시피도 보여줘"
        mock_response = {
            "primary_intent": "recommend",
            "secondary_intents": ["recipe_create"],
            "entities": {
                "taste": ["매운"]
            },
            "confidence": 0.9
        }

        mock_message = Mock()
        mock_message.content = [Mock(text=json.dumps(mock_response))]

        with patch.object(adapter.client.messages, 'create', return_value=mock_message):
            # When
            result = await adapter.classify_intent(query)

        # Then
        assert result["primary_intent"] == "recommend"
        assert "recipe_create" in result["secondary_intents"]

    @pytest.mark.asyncio
    async def test_classify_intent_parsing_error(self, adapter):
        """잘못된 JSON 응답 파싱 실패"""
        # Given
        query = "김치찌개 만들기"

        # Mock: 유효하지 않은 JSON 응답
        mock_message = Mock()
        mock_message.content = [Mock(text="This is not JSON")]

        with patch.object(adapter.client.messages, 'create', return_value=mock_message):
            # When / Then
            with pytest.raises(ParsingError) as exc_info:
                await adapter.classify_intent(query)

            assert "JSON 파싱 실패" in exc_info.value.message


class TestGenerateRecipe:
    """레시피 생성 테스트"""

    @pytest.mark.asyncio
    async def test_generate_recipe_success(self, adapter):
        """레시피 생성 성공"""
        # Given
        query = "파스타 카르보나라 만드는 법"
        entities = {"dishes": ["파스타 카르보나라"]}

        mock_recipe = {
            "title": "파스타 카르보나라",
            "ingredients": ["파스타 면", "베이컨", "달걀", "파마산 치즈"],
            "steps": ["1. 면을 삶는다", "2. 베이컨을 볶는다"],
            "cooking_time": "20분",
            "difficulty": "중간",
            "servings": 2
        }

        mock_message = Mock()
        mock_message.content = [Mock(text=json.dumps(mock_recipe))]

        with patch.object(adapter.client.messages, 'create', return_value=mock_message):
            # When
            result = await adapter.generate_recipe(query, entities)

        # Then
        assert result["title"] == "파스타 카르보나라"
        assert len(result["ingredients"]) == 4
        assert len(result["steps"]) == 2
        assert result["difficulty"] == "중간"

    @pytest.mark.asyncio
    async def test_generate_recipe_with_constraints(self, adapter):
        """제약 조건 포함 레시피 생성"""
        # Given
        query = "빠른 아침 식사 만들기"
        entities = {
            "constraints": {
                "cooking_time": "10분",
                "difficulty": "쉬움"
            }
        }

        mock_recipe = {
            "title": "토스트",
            "ingredients": ["식빵", "버터"],
            "steps": ["1. 식빵을 굽는다"],
            "cooking_time": "5분",
            "difficulty": "쉬움",
            "servings": 1
        }

        mock_message = Mock()
        mock_message.content = [Mock(text=json.dumps(mock_recipe))]

        with patch.object(adapter.client.messages, 'create', return_value=mock_message):
            # When
            result = await adapter.generate_recipe(query, entities)

        # Then
        assert result["difficulty"] == "쉬움"
        assert "5분" in result["cooking_time"]


class TestRecommendFood:
    """음식 추천 테스트"""

    @pytest.mark.asyncio
    async def test_recommend_food_success(self, adapter):
        """음식 추천 성공"""
        # Given
        query = "매운 음식 추천해줘"
        entities = {"taste": ["매운"]}

        mock_recommendations = {
            "recommendations": [
                {
                    "name": "김치찌개",
                    "description": "한국의 대표적인 매운 찌개",
                    "reason": "얼큰하고 칼칼한 맛"
                },
                {
                    "name": "떡볶이",
                    "description": "매콤한 국물 떡볶이",
                    "reason": "고추장의 매콤함"
                }
            ]
        }

        mock_message = Mock()
        mock_message.content = [Mock(text=json.dumps(mock_recommendations))]

        with patch.object(adapter.client.messages, 'create', return_value=mock_message):
            # When
            result = await adapter.recommend_food(query, entities)

        # Then
        assert len(result["recommendations"]) == 2
        assert result["recommendations"][0]["name"] == "김치찌개"


class TestAnswerQuestion:
    """질문 답변 테스트"""

    @pytest.mark.asyncio
    async def test_answer_question_success(self, adapter):
        """질문 답변 성공"""
        # Given
        query = "김치찌개 칼로리는?"
        entities = {"dishes": ["김치찌개"]}

        mock_answer = {
            "answer": "김치찌개 1인분(300g)은 약 150-200kcal입니다.",
            "additional_tips": [
                "돼지고기를 넣으면 칼로리가 높아집니다",
                "두부를 추가하면 단백질 보충에 좋습니다"
            ]
        }

        mock_message = Mock()
        mock_message.content = [Mock(text=json.dumps(mock_answer))]

        with patch.object(adapter.client.messages, 'create', return_value=mock_message):
            # When
            result = await adapter.answer_question(query, entities)

        # Then
        assert "150-200kcal" in result["answer"]
        assert len(result["additional_tips"]) == 2


class TestGenerateImagePrompt:
    """이미지 프롬프트 생성 테스트"""

    @pytest.mark.asyncio
    async def test_generate_image_prompt_success(self, adapter):
        """이미지 프롬프트 생성 성공"""
        # Given
        recipe_text = "김치찌개: 김치, 돼지고기, 두부를 넣고 끓인 찌개"
        dish_names = ["김치찌개"]

        mock_prompt = {
            "image_prompt": "A steaming hot Korean kimchi stew in a traditional earthenware pot",
            "style": "food photography"
        }

        mock_message = Mock()
        mock_message.content = [Mock(text=json.dumps(mock_prompt))]

        with patch.object(adapter.client.messages, 'create', return_value=mock_message):
            # When
            result = await adapter.generate_image_prompt(recipe_text, dish_names)

        # Then
        assert "kimchi stew" in result["image_prompt"]
        assert result["style"] == "food photography"


class TestErrorHandling:
    """에러 핸들링 테스트"""

    @pytest.mark.asyncio
    async def test_api_timeout_error(self, adapter):
        """API 타임아웃 에러"""
        # Given
        query = "김치찌개 만들기"

        # Mock: 타임아웃 발생
        with patch.object(adapter.client.messages, 'create', side_effect=TimeoutError("Request timeout")):
            # When / Then
            with pytest.raises(LLMServiceError) as exc_info:
                await adapter.classify_intent(query)

            assert "타임아웃" in exc_info.value.message or "timeout" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_api_connection_error(self, adapter):
        """API 연결 에러"""
        # Given
        query = "김치찌개 만들기"

        # Mock: 연결 실패
        with patch.object(adapter.client.messages, 'create', side_effect=ConnectionError("Connection failed")):
            # When / Then
            with pytest.raises(LLMServiceError) as exc_info:
                await adapter.classify_intent(query)

            assert "LLM" in exc_info.value.message or "API" in exc_info.value.message


class TestPromptLoaderIntegration:
    """PromptLoader 통합 테스트"""

    def test_prompt_loader_called_with_correct_params(self, adapter, mock_prompt_loader):
        """PromptLoader가 올바른 파라미터로 호출되는지 확인"""
        # Given
        mock_prompt_loader.render.return_value = "Test prompt"

        # When
        adapter._render_prompt("test_template", query="test query")

        # Then
        mock_prompt_loader.render.assert_called_once_with(
            "test_template",
            query="test query"
        )
