"""Framework-level ports - Reusable across all templates"""
from .llm_port import ILLMPort
from .image_port import IImagePort

__all__ = ["ILLMPort", "IImagePort"]
