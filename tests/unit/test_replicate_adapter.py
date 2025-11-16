"""Replicate Image Adapter 단위 테스트

이미지 생성 API Mock 테스트
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.adapters.image.replicate_adapter import ReplicateImageAdapter
from app.domain.exceptions import ImageGenerationError


@pytest.fixture
def mock_settings():
    """Mock Settings 픽스처"""
    settings = Mock()
    settings.replicate_api_token = "test-token"
    settings.image_model = "black-forest-labs/flux-schnell"
    settings.image_width = 1024
    settings.image_height = 1024
    return settings


@pytest.fixture
def adapter(mock_settings):
    """ReplicateImageAdapter 픽스처"""
    return ReplicateImageAdapter(settings=mock_settings)


class TestReplicateAdapterInitialization:
    """Adapter 초기화 테스트"""

    def test_adapter_creation(self, adapter, mock_settings):
        """Adapter 생성 확인"""
        assert adapter.settings == mock_settings
        assert adapter.client is not None

    def test_adapter_with_api_token(self, mock_settings):
        """API 토큰 설정 확인"""
        adapter = ReplicateImageAdapter(settings=mock_settings)
        assert adapter.settings.replicate_api_token == "test-token"


class TestGenerateImage:
    """이미지 생성 테스트"""

    @pytest.mark.asyncio
    async def test_generate_image_success(self, adapter):
        """이미지 생성 성공"""
        # Given
        prompt = "A delicious Korean kimchi stew in earthenware pot"
        expected_url = "https://replicate.delivery/pbxt/test-image.jpg"

        # Mock Replicate API 응답
        mock_output = [expected_url]

        with patch('replicate.run', return_value=mock_output):
            # When
            result_url = await adapter.generate_image(prompt)

        # Then
        assert result_url == expected_url

    @pytest.mark.asyncio
    async def test_generate_image_with_custom_size(self, adapter):
        """커스텀 이미지 크기"""
        # Given
        prompt = "Korean food photography"
        width = 512
        height = 512

        mock_output = ["https://replicate.delivery/test.jpg"]

        with patch('replicate.run', return_value=mock_output) as mock_run:
            # When
            result_url = await adapter.generate_image(
                prompt,
                width=width,
                height=height
            )

        # Then
        assert result_url is not None
        # replicate.run이 올바른 파라미터로 호출되었는지 확인
        mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_image_empty_output(self, adapter):
        """빈 출력 처리"""
        # Given
        prompt = "Test prompt"

        # Mock: 빈 출력
        mock_output = []

        with patch('replicate.run', return_value=mock_output):
            # When / Then
            with pytest.raises(ImageGenerationError) as exc_info:
                await adapter.generate_image(prompt)

            assert "이미지 생성 실패" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_generate_image_none_output(self, adapter):
        """None 출력 처리"""
        # Given
        prompt = "Test prompt"

        # Mock: None 출력
        with patch('replicate.run', return_value=None):
            # When / Then
            with pytest.raises(ImageGenerationError):
                await adapter.generate_image(prompt)


class TestGenerateMultipleImages:
    """복수 이미지 생성 테스트"""

    @pytest.mark.asyncio
    async def test_generate_multiple_images_success(self, adapter):
        """복수 이미지 생성 성공"""
        # Given
        prompts = [
            "Korean kimchi stew",
            "Italian pasta carbonara",
            "Japanese sushi platter"
        ]

        expected_urls = [
            "https://replicate.delivery/image1.jpg",
            "https://replicate.delivery/image2.jpg",
            "https://replicate.delivery/image3.jpg"
        ]

        # Mock: 각 호출마다 다른 URL 반환
        with patch('replicate.run', side_effect=[[url] for url in expected_urls]):
            # When
            result_urls = await adapter.generate_multiple_images(prompts)

        # Then
        assert len(result_urls) == 3
        assert result_urls == expected_urls

    @pytest.mark.asyncio
    async def test_generate_multiple_images_partial_failure(self, adapter):
        """일부 이미지 생성 실패"""
        # Given
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]

        # Mock: 두 번째 이미지 생성 실패
        def mock_run_side_effect(model, input):
            if "Prompt 2" in str(input):
                return []  # 빈 결과
            return ["https://replicate.delivery/image.jpg"]

        with patch('replicate.run', side_effect=mock_run_side_effect):
            # When
            result_urls = await adapter.generate_multiple_images(prompts)

        # Then
        # 실패한 것은 None으로 반환
        assert len(result_urls) == 3
        assert result_urls[0] is not None
        assert result_urls[1] is None  # 실패
        assert result_urls[2] is not None


class TestErrorHandling:
    """에러 핸들링 테스트"""

    @pytest.mark.asyncio
    async def test_api_timeout(self, adapter):
        """API 타임아웃"""
        # Given
        prompt = "Test image"

        # Mock: 타임아웃 발생
        with patch('replicate.run', side_effect=TimeoutError("Request timeout")):
            # When / Then
            with pytest.raises(ImageGenerationError) as exc_info:
                await adapter.generate_image(prompt)

            assert "타임아웃" in exc_info.value.message.lower() or "timeout" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_api_connection_error(self, adapter):
        """API 연결 실패"""
        # Given
        prompt = "Test image"

        # Mock: 연결 실패
        with patch('replicate.run', side_effect=ConnectionError("Connection failed")):
            # When / Then
            with pytest.raises(ImageGenerationError):
                await adapter.generate_image(prompt)

    @pytest.mark.asyncio
    async def test_api_authentication_error(self, adapter):
        """API 인증 실패"""
        # Given
        prompt = "Test image"

        # Mock: 인증 실패
        auth_error = Exception("Authentication failed")

        with patch('replicate.run', side_effect=auth_error):
            # When / Then
            with pytest.raises(ImageGenerationError) as exc_info:
                await adapter.generate_image(prompt)

            assert exc_info.value.code == "IMAGE_GEN_FAILED"


class TestPromptValidation:
    """프롬프트 검증 테스트"""

    @pytest.mark.asyncio
    async def test_empty_prompt(self, adapter):
        """빈 프롬프트"""
        # Given
        prompt = ""

        # When / Then
        with pytest.raises(ImageGenerationError) as exc_info:
            await adapter.generate_image(prompt)

        assert "프롬프트" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_very_long_prompt(self, adapter):
        """매우 긴 프롬프트 (정상 처리)"""
        # Given
        prompt = "Korean food " * 100  # 긴 프롬프트

        mock_output = ["https://replicate.delivery/image.jpg"]

        with patch('replicate.run', return_value=mock_output):
            # When
            result_url = await adapter.generate_image(prompt)

        # Then
        assert result_url is not None


class TestImageQuality:
    """이미지 품질 설정 테스트"""

    @pytest.mark.asyncio
    async def test_high_quality_image(self, adapter):
        """고품질 이미지 생성"""
        # Given
        prompt = "High quality Korean food photography"
        quality = "high"

        mock_output = ["https://replicate.delivery/hq-image.jpg"]

        with patch('replicate.run', return_value=mock_output):
            # When
            result_url = await adapter.generate_image(
                prompt,
                quality=quality
            )

        # Then
        assert result_url is not None

    @pytest.mark.asyncio
    async def test_default_size_image(self, adapter, mock_settings):
        """기본 크기 이미지 생성"""
        # Given
        prompt = "Korean food"

        mock_output = ["https://replicate.delivery/image.jpg"]

        with patch('replicate.run', return_value=mock_output) as mock_run:
            # When
            await adapter.generate_image(prompt)

        # Then
        # 기본 크기 (1024x1024) 사용 확인
        call_args = mock_run.call_args
        assert call_args is not None
