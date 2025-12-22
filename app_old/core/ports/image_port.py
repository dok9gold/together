"""IImagePort - 이미지 생성 포트 인터페이스

Application이 외부 이미지 생성 서비스에게 요구하는 기능을 정의합니다.

Port-Adapter Pattern:
    Port는 Application의 요구사항을 정의하고,
    Adapter는 외부 시스템(Replicate, DALL-E, Midjourney 등)에 맞춰 구현합니다.
"""
from abc import ABC, abstractmethod
from typing import Optional


class IImagePort(ABC):
    """이미지 생성 포트 (Application이 외부 이미지 서비스에게 원하는 기능)

    Pure port 원칙:
    - 렌더링된 프롬프트를 받아서 이미지 API 호출
    - 프롬프트 생성/템플릿은 호출자가 담당

    외부 이미지 생성 서비스(Replicate, DALL-E, Midjourney 등)와의 경계를 정의합니다.
    구체적인 구현은 Adapter Layer에서 담당합니다.

    이 인터페이스 덕분에:
    - 이미지 서비스 교체 가능 (Replicate ↔ DALL-E)
    - 테스트 시 모킹 가능
    - Application 로직이 외부 시스템에 의존하지 않음
    """

    @abstractmethod
    async def generate_image(self, prompt: str) -> Optional[str]:
        """이미지 생성

        Pure port: 프롬프트 → API → 이미지 URL

        Args:
            prompt: 렌더링된 이미지 생성 프롬프트

        Returns:
            Optional[str]: 이미지 URL (실패 시 None)

        Note:
            이미지 생성 실패는 치명적이지 않을 수 있습니다.
            Application의 요구사항에 따라 실패 처리 방식이 달라집니다.
        """
        pass
