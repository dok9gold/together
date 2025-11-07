"""AnthropicLLMAdapter - Anthropic Claude LLM 어댑터

ILLMPort 인터페이스를 Anthropic API에 맞게 구현합니다.
"""
from app.domain.ports.llm_port import ILLMPort
from app.core.config import Settings
from app.core.prompt_loader import PromptLoader
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from typing import Dict, Any
import json
import logging

logger = logging.getLogger(__name__)


class AnthropicLLMAdapter(ILLMPort):
    """Anthropic Claude 어댑터 (ILLMPort 구현체)

    Port에 맞게 Anthropic API를 감싸기:
    - 도메인은 이 어댑터의 존재를 몰라도 됨
    - 어댑터 교체만으로 LLM 제공자 변경 가능 (Anthropic → OpenAI)
    - 프롬프트는 YAML 파일로 관리 (PromptLoader 사용)

    Attributes:
        settings: 애플리케이션 설정
        prompt_loader: 프롬프트 템플릿 로더 (MyBatis Mapper 역할)
        llm: LangChain ChatAnthropic 인스턴스
    """

    def __init__(self, settings: Settings, prompt_loader: PromptLoader):
        """의존성 주입: Settings, PromptLoader

        Args:
            settings: 애플리케이션 설정 (Config)
            prompt_loader: 프롬프트 템플릿 로더
        """
        self.settings = settings
        self.prompt_loader = prompt_loader
        self.llm = ChatAnthropic(
            model=settings.llm_model,
            api_key=settings.anthropic_api_key,
            timeout=settings.llm_timeout,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )

    async def classify_intent(self, query: str) -> Dict[str, Any]:
        """의도 분류 (Anthropic API 호출 + 응답 변환)

        Args:
            query: 사용자 쿼리

        Returns:
            Dict[str, Any]: 의도 분류 결과
        """
        # YAML 프롬프트 로드 (MyBatis 스타일)
        prompt = self.prompt_loader.render("cooking.classify_intent", query=query)

        logger.info(f"[Anthropic] 의도 분류 요청: {query[:50]}...")

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result_json = self._extract_json(response.content)
            result = json.loads(result_json)

            logger.info(f"[Anthropic] 의도 분류 완료: {result.get('primary_intent')}")

            return result

        except Exception as e:
            logger.error(f"[Anthropic] 의도 분류 실패: {str(e)}")
            raise

    async def generate_recipe(
        self,
        query: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """레시피 생성 (Anthropic API 호출 + 응답 변환)

        Args:
            query: 사용자 쿼리
            entities: 추출된 엔티티

        Returns:
            Dict[str, Any]: 레시피 데이터 (단일 또는 복수)
        """
        # 단일/복수 레시피 판단
        dishes = entities.get("dishes", [])
        if dishes and len(dishes) == 1:
            prompt_id = "cooking.generate_recipe_single"
        elif dishes and len(dishes) > 1:
            prompt_id = "cooking.generate_recipe_multiple"
        else:
            prompt_id = "cooking.generate_recipe_single"

        # YAML 프롬프트 로드 (MyBatis 스타일)
        prompt = self.prompt_loader.render(
            prompt_id,
            query=query,
            dishes=dishes,
            ingredients=entities.get("ingredients", []),
            constraints=entities.get("constraints", {}),
            dietary=entities.get("dietary", []),
            count=len(dishes) if dishes else 1
        )

        logger.info(f"[Anthropic] 레시피 생성 요청: {query[:50]}...")

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result_json = self._extract_json(response.content)
            result = json.loads(result_json)

            logger.info(f"[Anthropic] 레시피 생성 완료")

            return result

        except Exception as e:
            logger.error(f"[Anthropic] 레시피 생성 실패: {str(e)}")
            raise

    async def recommend_dishes(
        self,
        query: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """음식 추천 (Anthropic API 호출 + 응답 변환)

        Args:
            query: 사용자 쿼리
            entities: 추출된 엔티티

        Returns:
            Dict[str, Any]: 추천 결과
        """
        # YAML 프롬프트 로드 (MyBatis 스타일)
        prompt = self.prompt_loader.render(
            "cooking.recommend_dishes",
            query=query,
            cuisine_type=entities.get("cuisine_type"),
            taste=entities.get("taste", []),
            ingredients=entities.get("ingredients", []),
            dietary=entities.get("dietary", []),
            constraints=entities.get("constraints", {}),
            count=entities.get("count", 3)
        )

        logger.info(f"[Anthropic] 음식 추천 요청: {query[:50]}...")

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result_json = self._extract_json(response.content)
            result = json.loads(result_json)

            logger.info(f"[Anthropic] 음식 추천 완료")

            return result

        except Exception as e:
            logger.error(f"[Anthropic] 음식 추천 실패: {str(e)}")
            raise

    async def answer_question(self, query: str) -> Dict[str, Any]:
        """질문 답변 (Anthropic API 호출 + 응답 변환)

        Args:
            query: 사용자 질문

        Returns:
            Dict[str, Any]: 답변 결과
        """
        # YAML 프롬프트 로드 (MyBatis 스타일)
        prompt = self.prompt_loader.render("cooking.answer_question", query=query)

        logger.info(f"[Anthropic] 질문 답변 요청: {query[:50]}...")

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result_json = self._extract_json(response.content)
            result = json.loads(result_json)

            logger.info(f"[Anthropic] 질문 답변 완료")

            return result

        except Exception as e:
            logger.error(f"[Anthropic] 질문 답변 실패: {str(e)}")
            raise

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Private Methods (유틸리티)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _extract_json(self, content: str) -> str:
        """마크다운 코드 블록에서 JSON 추출

        Args:
            content: LLM 응답 (마크다운 포함 가능)

        Returns:
            str: 정제된 JSON 문자열
        """
        # 마크다운 코드 블록 제거 (```json ... ```)
        if content.startswith("```"):
            lines = content.split('\n')
            content = '\n'.join(lines[1:-1]) if len(lines) > 2 else content
            content = content.strip()

        # 마지막 } 이후 텍스트 제거
        last_brace = content.rfind('}')
        if last_brace != -1:
            content = content[:last_brace + 1]

        return content
