"""ReplicateImageAdapter - Replicate 이미지 생성 어댑터

IImagePort 인터페이스를 Replicate API에 맞게 구현합니다.
"""
from app.domain.ports.image_port import IImagePort
from app.core.config import Settings
import replicate
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ReplicateImageAdapter(IImagePort):
    """Replicate 어댑터 (IImagePort 구현체)

    Port에 맞게 Replicate API를 감싸기:
    - 다른 이미지 서비스로 교체 가능 (DALL-E, Midjourney 등)
    - 도메인은 이 어댑터의 존재를 몰라도 됨

    Attributes:
        settings: 애플리케이션 설정
        api_token: Replicate API 토큰
    """

    def __init__(self, settings: Settings):
        """의존성 주입: Settings

        Args:
            settings: 애플리케이션 설정 (Config)
        """
        self.settings = settings
        self.api_token = settings.replicate_api_token

    def generate_prompt(self, dish_name: str) -> str:
        """요리명을 영어 프롬프트로 변환

        Args:
            dish_name: 요리 이름 (예: "김치찌개")

        Returns:
            str: 영어 이미지 생성 프롬프트
        """
        return (
            f"professional food photography of {dish_name}, "
            f"appetizing, high quality, restaurant style, "
            f"well plated, natural lighting"
        )

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
