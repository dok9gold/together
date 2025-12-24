"""BaseNode - 듀얼 호출 지원 베이스 노드"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Template

from core.llm import LLMProvider

# 프롬프트 디렉토리 경로
PROMPT_DIR = Path(__file__).parent.parent / "prompt"


def load_prompt(node_name: str, prompt_name: str = "default") -> dict[str, Template]:
    """YAML 프롬프트 파일을 로드하고 Jinja2 Template으로 변환

    Args:
        node_name: 노드 이름 (폴더명, ex: query_analyzer)
        prompt_name: 프롬프트 파일명 (확장자 제외, ex: analyze)

    Returns:
        {"system": Template, "user": Template} 형태의 딕셔너리

    Raises:
        FileNotFoundError: 프롬프트 파일이 없을 때
    """
    prompt_path = PROMPT_DIR / node_name / f"{prompt_name}.yaml"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    with open(prompt_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return {
        "system": Template(data.get("system", "")),
        "user": Template(data.get("user", "")),
    }


def render_prompt(templates: dict[str, Template], **kwargs) -> dict[str, str]:
    """Jinja2 템플릿을 렌더링

    Args:
        templates: load_prompt()의 반환값
        **kwargs: 템플릿 변수

    Returns:
        {"system": str, "user": str}
    """
    return {
        "system": templates["system"].render(**kwargs),
        "user": templates["user"].render(**kwargs),
    }


class BaseNode(ABC):
    """모든 노드의 베이스 클래스

    LLMProvider를 주입받아 사용
    """

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    @abstractmethod
    async def execute(self, state: dict[str, Any], config: dict | None = None) -> dict[str, Any]:
        """노드 실행

        Args:
            state: 현재 상태
            config: 설정 (chat_history 등)

        Returns:
            업데이트할 상태 필드
        """
        pass
