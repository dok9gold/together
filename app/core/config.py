"""중앙 설정 관리

환경 변수를 Pydantic Settings로 중앙 관리합니다.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """애플리케이션 설정 (환경 변수 중앙 관리)

    모든 환경 변수를 한 곳에서 관리하여:
    - 검증 로직 통합
    - 기본값 일관성 유지
    - 환경 변수 이름 변경 시 한 곳만 수정
    """

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # API 키
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    anthropic_api_key: str
    replicate_api_token: str

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # LLM 설정 (Anthropic Claude)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    llm_model: str = "claude-sonnet-4-5-20250929"
    llm_timeout: int = 90  # 초
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 이미지 생성 설정 (Replicate Flux Schnell)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    image_model: str = "black-forest-labs/flux-schnell"
    image_retries: int = 2  # 실패 시 재시도 횟수
    image_aspect_ratio: str = "1:1"
    image_output_format: str = "jpg"
    image_output_quality: int = 80
    image_num_outputs: int = 1

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 애플리케이션 설정
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    app_title: str = "Cooking Assistant API"
    app_description: str = "Claude와 LangGraph를 활용한 요리 AI 어시스턴트 서비스"
    app_version: str = "2.0.0"
    cors_origins: List[str] = ["*"]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 로깅
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    log_level: str = "INFO"

    class Config:
        """Pydantic Settings 설정"""
        env_file = ".env"
        case_sensitive = False  # 환경 변수 대소문자 무시

        # 예시 설정 (문서화용)
        json_schema_extra = {
            "example": {
                "anthropic_api_key": "sk-ant-...",
                "replicate_api_token": "r8_...",
                "llm_model": "claude-sonnet-4-5-20250929",
                "llm_timeout": 90,
                "image_model": "black-forest-labs/flux-schnell"
            }
        }


@lru_cache()
def get_settings() -> Settings:
    """싱글톤 설정 인스턴스 반환

    lru_cache로 캐싱하여 애플리케이션 전체에서 하나의 인스턴스만 사용합니다.

    Returns:
        Settings: 싱글톤 설정 객체

    Example:
        >>> settings = get_settings()
        >>> print(settings.llm_model)
        'claude-sonnet-4-5-20250929'
    """
    return Settings()
