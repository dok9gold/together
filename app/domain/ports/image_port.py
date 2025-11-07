"""IImagePort - 이미지 생성 포트 인터페이스

도메인이 외부 이미지 생성 서비스에게 요구하는 기능을 정의합니다.
"""
from abc import ABC, abstractmethod
from typing import Optional


class IImagePort(ABC):
    """이미지 생성 포트

    외부 시스템(Replicate, DALL-E 등)과의 경계를 정의합니다.
    구체적인 구현은 Adapter Layer에서 담당합니다.

    이 인터페이스 덕분에:
    - 이미지 서비스 교체 가능 (Replicate ↔ DALL-E)
    - 테스트 시 모킹 가능
    - 도메인 로직이 외부 시스템에 의존하지 않음
    """

    @abstractmethod
    def generate_prompt(self, dish_name: str) -> str:
        """요리명을 받아 이미지 생성 프롬프트 생성

        Args:
            dish_name: 요리 이름 (예: "김치찌개")

        Returns:
            str: 영어 이미지 생성 프롬프트

        Example:
            >>> image_port = ReplicateImageAdapter(settings)
            >>> prompt = image_port.generate_prompt("김치찌개")
            >>> prompt
            'professional food photography of 김치찌개, appetizing, high quality...'
        """
        pass

    @abstractmethod
    async def generate_image(self, prompt: str) -> Optional[str]:
        """이미지 생성

        Args:
            prompt: 이미지 생성 프롬프트

        Returns:
            Optional[str]: 이미지 URL 또는 None (실패 시)

        Note:
            이미지 생성 실패는 치명적이지 않습니다.
            실패 시 None을 반환하고, 레시피는 정상적으로 반환됩니다.

        Example:
            >>> prompt = "professional food photography of 김치찌개..."
            >>> url = await image_port.generate_image(prompt)
            >>> url
            'https://replicate.delivery/pbxt/...'
        """
        pass
