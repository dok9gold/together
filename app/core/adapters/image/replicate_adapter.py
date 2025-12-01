"""ReplicateImageAdapter - Replicate 이미지 생성 어댑터

IImagePort 인터페이스를 Replicate API에 맞게 구현합니다.
Pure adapter: prompt → API → image URL (no template logic)
"""
from app.core.decorators import singleton, inject
from app.core.ports.image_port import IImagePort
from app.core.config import Settings
import replicate
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@singleton
class ReplicateImageAdapter(IImagePort):
    """Replicate 어댑터 (IImagePort 구현체)

    Pure adapter pattern:
    - Receives pre-rendered prompts from workflow nodes
    - Calls Replicate API
    - Returns image URL
    - NO business logic (no prompt templates)

    Attributes:
        settings: 애플리케이션 설정
        api_token: Replicate API 토큰
    """

    @inject
    def __init__(self, settings: Settings):
        """의존성 주입: Settings

        타입 힌트를 통해 자동으로 의존성이 주입됩니다.

        Args:
            settings: 애플리케이션 설정 (Config)
        """
        self.settings = settings
        self.api_token = settings.replicate_api_token

    async def generate_image(self, prompt: str) -> Optional[str]:
        """Replicate Flux Schnell 모델로 이미지 생성

        Args:
            prompt: 이미지 생성 프롬프트

        Returns:
            Optional[str]: 이미지 URL 또는 None (실패 시)
        """
        retries = self.settings.image_retries

        for attempt in range(retries):
            try:
                logger.info(f"[Replicate] 이미지 생성 시도 {attempt + 1}/{retries}")

                output = replicate.run(
                    self.settings.image_model,
                    input={
                        "prompt": prompt,
                        "num_outputs": self.settings.image_num_outputs,
                        "aspect_ratio": self.settings.image_aspect_ratio,
                        "output_format": self.settings.image_output_format,
                        "output_quality": self.settings.image_output_quality
                    }
                )

                # output은 리스트 형태로 반환됨
                if output and len(output) > 0:
                    logger.info(f"[Replicate] 이미지 생성 성공: {output[0]}")
                    return output[0]

            except Exception as e:
                logger.error(f"[Replicate] 시도 {attempt + 1} 실패: {str(e)}")
                if attempt == retries - 1:
                    return None

        return None
