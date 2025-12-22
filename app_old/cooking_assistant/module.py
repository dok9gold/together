"""Cooking Assistant Dependency Injection Module

Port → Adapter 바인딩을 정의합니다.
Adapter를 교체하려면 이 파일만 수정하면 됩니다.
"""
from injector import Module, singleton, provider
from app.core.config import Settings, get_settings
from app.core.prompt_loader import PromptLoader

# Framework-level ports (reusable)
from app.core.ports.llm_port import ILLMPort
from app.core.ports.image_port import IImagePort

# Adapter implementations (replaceable)
from app.core.adapters.llm.anthropic_adapter import AnthropicLLMAdapter
from app.core.adapters.image.replicate_adapter import ReplicateImageAdapter


class CookingModule(Module):
    """Cooking Assistant DI Configuration

    Binds ports to concrete adapters for this template.
    To use different LLM/image providers, just change the bindings here.
    """

    @singleton
    @provider
    def provide_settings(self) -> Settings:
        """Settings 제공 (Singleton)"""
        return get_settings()

    @singleton
    @provider
    def provide_prompt_loader(self) -> PromptLoader:
        """PromptLoader 제공 (Singleton)

        Template-specific prompts location
        """
        return PromptLoader(prompts_dir="app/cooking_assistant/prompts")

    @singleton
    @provider
    def provide_llm_adapter(self, settings: Settings) -> ILLMPort:
        """LLM Adapter 제공 (Singleton)

        AnthropicLLMAdapter를 사용합니다.
        OpenAIAdapter, OllamaAdapter로 교체 가능합니다.

        Note: PromptLoader dependency removed from adapter (pure adapter pattern)
        """
        return AnthropicLLMAdapter(settings=settings)

    @singleton
    @provider
    def provide_image_adapter(self, settings: Settings) -> IImagePort:
        """Image Adapter 제공 (Singleton)

        ReplicateImageAdapter를 사용합니다.
        DALLEAdapter로 교체 가능합니다.
        """
        return ReplicateImageAdapter(settings=settings)
