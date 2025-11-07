"""PromptLoader - 프롬프트 템플릿 로더 (MyBatis Mapper 역할)

YAML 파일에서 프롬프트를 로드하고 Jinja2로 렌더링합니다.
"""
from jinja2 import Environment, BaseLoader, TemplateNotFound
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PromptLoader:
    """프롬프트 템플릿 로더 (MyBatis SqlSessionFactory와 유사)

    YAML 파일에서 프롬프트를 로드하고 Jinja2 템플릿 엔진으로 렌더링합니다.

    Features:
    - YAML 파일 자동 로드 (app/prompts/*.yaml)
    - Jinja2 템플릿 엔진 통합 (동적 파라미터 바인딩)
    - 네임스페이스 기반 프롬프트 관리 (예: "cooking.classify_intent")
    - 핫 리로드 지원 (개발 모드)

    Example:
        >>> loader = PromptLoader()
        >>> prompt = loader.render("cooking.classify_intent", query="김치찌개")
        >>> print(prompt)
        당신은 요리 AI 어시스턴트의 의도 분류 전문가입니다...
    """

    def __init__(self, prompts_dir: str = "app/prompts"):
        """초기화 및 YAML 파일 로드

        Args:
            prompts_dir: 프롬프트 YAML 파일이 위치한 디렉토리
        """
        self.prompts_dir = Path(prompts_dir)
        self.prompts: Dict[str, Dict[str, Any]] = {}

        # Jinja2 환경 설정 (autoescape=False: 프롬프트는 HTML이 아님)
        self.jinja_env = Environment(
            loader=BaseLoader(),  # 문자열 직접 로드
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )

        self._load_prompts()

    def _load_prompts(self):
        """YAML 파일들을 로드하여 메모리에 캐싱

        디렉토리 구조:
            app/prompts/
                cooking.yaml       # namespace: "cooking"
                common.yaml        # namespace: "common"
        """
        if not self.prompts_dir.exists():
            logger.warning(f"[PromptLoader] 프롬프트 디렉토리가 없습니다: {self.prompts_dir}")
            return

        for yaml_file in self.prompts_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    namespace = yaml_file.stem  # cooking.yaml -> "cooking"
                    self.prompts[namespace] = data
                    logger.info(f"[PromptLoader] 로드 완료: {namespace} ({len(data)} prompts)")
            except Exception as e:
                logger.error(f"[PromptLoader] YAML 로드 실패: {yaml_file} - {e}")

    def render(self, prompt_id: str, **kwargs) -> str:
        """프롬프트 렌더링 (MyBatis의 selectOne과 유사)

        Args:
            prompt_id: "namespace.prompt_name" 형식
                예: "cooking.classify_intent"
            **kwargs: Jinja2 템플릿 변수
                예: query="김치찌개", dishes=["김치찌개"]

        Returns:
            렌더링된 프롬프트 문자열

        Raises:
            ValueError: prompt_id 형식이 잘못되었거나 프롬프트가 없는 경우

        Example:
            >>> loader.render(
            ...     "cooking.generate_recipe_single",
            ...     query="김치찌개 만들기",
            ...     dishes=["김치찌개"],
            ...     ingredients=["김치", "돼지고기"],
            ...     constraints={"time": "30분"}
            ... )
        """
        # prompt_id 파싱 (namespace.name)
        if '.' not in prompt_id:
            raise ValueError(
                f"[PromptLoader] prompt_id는 'namespace.name' 형식이어야 합니다: {prompt_id}"
            )

        namespace, name = prompt_id.split('.', 1)

        # 네임스페이스 확인
        if namespace not in self.prompts:
            raise ValueError(
                f"[PromptLoader] 네임스페이스를 찾을 수 없습니다: {namespace} "
                f"(가능한 값: {list(self.prompts.keys())})"
            )

        # 프롬프트 확인
        if name not in self.prompts[namespace]:
            raise ValueError(
                f"[PromptLoader] 프롬프트를 찾을 수 없습니다: {name} "
                f"(가능한 값: {list(self.prompts[namespace].keys())})"
            )

        # 템플릿 문자열 추출
        prompt_data = self.prompts[namespace][name]
        template_str = prompt_data.get('template')

        if not template_str:
            raise ValueError(
                f"[PromptLoader] 프롬프트에 'template' 필드가 없습니다: {prompt_id}"
            )

        # Jinja2 렌더링
        try:
            template = self.jinja_env.from_string(template_str)
            rendered = template.render(**kwargs)

            logger.debug(
                f"[PromptLoader] 렌더링 완료: {prompt_id} "
                f"(params: {list(kwargs.keys())})"
            )

            return rendered

        except Exception as e:
            logger.error(f"[PromptLoader] 렌더링 실패: {prompt_id} - {e}")
            raise ValueError(f"[PromptLoader] 템플릿 렌더링 오류: {e}")

    def get_description(self, prompt_id: str) -> Optional[str]:
        """프롬프트 설명 조회 (디버깅용)

        Args:
            prompt_id: "namespace.prompt_name" 형식

        Returns:
            프롬프트 설명 (없으면 None)
        """
        try:
            namespace, name = prompt_id.split('.', 1)
            return self.prompts[namespace][name].get('description')
        except (KeyError, ValueError):
            return None

    def list_prompts(self, namespace: Optional[str] = None) -> Dict[str, list]:
        """로드된 프롬프트 목록 조회 (디버깅용)

        Args:
            namespace: 특정 네임스페이스만 조회 (None이면 전체)

        Returns:
            네임스페이스별 프롬프트 이름 목록

        Example:
            >>> loader.list_prompts()
            {
                'cooking': ['classify_intent', 'generate_recipe_single', ...],
                'common': [...]
            }
        """
        if namespace:
            return {namespace: list(self.prompts.get(namespace, {}).keys())}

        return {
            ns: list(prompts.keys())
            for ns, prompts in self.prompts.items()
        }

    def reload(self):
        """프롬프트 재로드 (핫 리로드, 개발 모드용)

        프로덕션 환경에서는 사용하지 않는 것을 권장합니다.
        """
        logger.info("[PromptLoader] 프롬프트 재로드 시작...")
        self.prompts.clear()
        self._load_prompts()
        logger.info("[PromptLoader] 프롬프트 재로드 완료")