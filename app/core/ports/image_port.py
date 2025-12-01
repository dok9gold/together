"""IImagePort - 이미지 생성 포트 인터페이스

도메인이 외부 이미지 생성 서비스에게 요구하는 기능을 정의합니다.
"""
from abc import ABC, abstractmethod
from typing import Optional


class IImagePort(ABC):
    """이미지 생성 포트

    Pure port: accepts pre-rendered prompt, calls image API, returns image URL.
    Prompt generation/templates are handled by caller (workflow nodes).

    외부 시스템(Replicate, DALL-E 등)과의 경계를 정의합니다.
    구체적인 구현은 Adapter Layer에서 담당합니다.

    이 인터페이스 덕분에:
    - 이미지 서비스 교체 가능 (Replicate ↔ DALL-E)
    - 테스트 시 모킹 가능
    - 도메인 로직이 외부 시스템에 의존하지 않음
    """

    @abstractmethod
    async def generate_image(self, prompt: str) -> Optional[str]:
        """이미지 생성

        Pure adapter: prompt → API → image URL

        Args:
            prompt: Pre-rendered image generation prompt

        Returns:
            Optional[str]: Image URL or None (on failure)

        Note:
            이미지 생성 실패는 치명적이지 않습니다.
            실패 시 None을 반환하고, 레시피는 정상적으로 반환됩니다.
        """
        pass
