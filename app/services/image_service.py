import os
import replicate
from typing import Optional


class ImageService:
    """Replicate를 사용한 이미지 생성 서비스"""

    def __init__(self):
        self.api_token = os.getenv("REPLICATE_API_TOKEN")
        if not self.api_token:
            raise ValueError("REPLICATE_API_TOKEN not found in environment variables")

    def generate_image_prompt(self, dish_name: str) -> str:
        """
        요리명을 받아 이미지 생성 프롬프트를 생성 (템플릿 기반)

        Args:
            dish_name: 요리 이름 (예: "파스타 카르보나라")

        Returns:
            영어 이미지 프롬프트
        """
        # 간단한 템플릿 기반 프롬프트 생성
        return f"professional food photography of {dish_name}, appetizing, high quality, restaurant style, well plated, natural lighting"

    async def generate_image(self, prompt: str, retries: int = 2) -> Optional[str]:
        """
        Replicate Flux Schnell 모델을 사용해 이미지 생성

        Args:
            prompt: 이미지 생성 프롬프트
            retries: 실패 시 재시도 횟수

        Returns:
            이미지 URL 또는 실패 시 None
        """
        for attempt in range(retries):
            try:
                output = replicate.run(
                    "black-forest-labs/flux-schnell",
                    input={
                        "prompt": prompt,
                        "num_outputs": 1,
                        "aspect_ratio": "1:1",
                        "output_format": "jpg",
                        "output_quality": 80
                    }
                )

                # output은 리스트 형태로 반환됨
                if output and len(output) > 0:
                    return output[0]

            except Exception as e:
                print(f"Image generation attempt {attempt + 1} failed: {str(e)}")
                if attempt == retries - 1:
                    return None

        return None