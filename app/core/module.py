"""Cooking Assistant DI Module

Port 인터페이스를 구체적인 Adapter로 바인딩합니다.
이 파일은 템플릿 특화 설정입니다 (다른 템플릿은 다른 바인딩).
"""
from injector import Module, singleton, provider
from app.core.config import Settings, get_settings
from app.core.prompt_loader import PromptLoader

# Port Interfaces
from app.domain.ports.llm_port import ILLMPort
from app.domain.ports.image_port import IImagePort

# Adapter Implementations
from app.adapters.llm.anthropic_adapter import AnthropicLLMAdapter
from app.adapters.image.replicate_adapter import ReplicateImageAdapter


class CookingModule(Module):
    """Cooking Assistant Template DI Module

    Port → Adapter 바인딩을 정의합니다.
    Adapter를 교체하려면 이 파일만 수정하면 됩니다.

    Example:
        # OpenAI로 교체
        binder.bind(ILLMPort, to=OpenAIAdapter, scope=singleton)
    """

    @singleton
    @provider
    def provide_settings(self) -> Settings:
        """Settings 제공 (Singleton)"""
        return get_settings()

    @singleton
    @provider
    def provide_prompt_loader(self) -> PromptLoader:
        """PromptLoader 제공 (Singleton)"""
        return PromptLoader(prompts_dir="app/prompts")

    @singleton
    @provider
    def provide_llm_adapter(
        self,
        settings: Settings,
        prompt_loader: PromptLoader
    ) -> ILLMPort:
        """LLM Adapter 제공 (Singleton)

        AnthropicLLMAdapter를 사용합니다.
        OpenAIAdapter, OllamaAdapter로 교체 가능합니다.
        """
        return AnthropicLLMAdapter(settings=settings, prompt_loader=prompt_loader)

    @singleton
    @provider
    def provide_image_adapter(self, settings: Settings) -> IImagePort:
        """Image Adapter 제공 (Singleton)

        ReplicateImageAdapter를 사용합니다.
        DALLEAdapter로 교체 가능합니다.
        """
        return ReplicateImageAdapter(settings=settings)
