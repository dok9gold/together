"""AnthropicLLMAdapter - Anthropic Claude LLM 어댑터

ILLMPort 인터페이스를 Anthropic Claude API에 맞게 구현합니다.

Pure Adapter 원칙:
- 프롬프트를 받아 API 호출 후 결과 반환
- 비즈니스 로직 없음 (프롬프트 생성, 엔티티 추출 등은 호출자가 담당)
"""
from app.core.decorators import singleton, inject
from app.core.ports.llm_port import ILLMPort
from app.core.config import Settings
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from typing import Dict, Any
import json
import logging

logger = logging.getLogger(__name__)


@singleton
class AnthropicLLMAdapter(ILLMPort):
    """Anthropic Claude 어댑터 (ILLMPort 구현체)

    Port-Adapter Pattern 구현:
    - Port(ILLMPort)가 정의한 인터페이스를 Anthropic Claude API에 맞춰 구현
    - 다른 LLM 제공자(OpenAI, Google Gemini 등)로 교체 가능

    Pure Adapter 원칙:
    - 렌더링된 프롬프트를 받아서 API 호출
    - 비즈니스 로직 없음 (프롬프트 선택, 엔티티 추출 등은 호출자가 담당)
    - 단순히 API 호출 및 결과 반환만 담당

    Attributes:
        settings: 애플리케이션 설정
        llm: LangChain ChatAnthropic 인스턴스
    """

    @inject
    def __init__(self, settings: Settings):
        """의존성 주입: Settings

        Args:
            settings: 애플리케이션 설정 (LLM 모델명, API 키, 타임아웃 등)
        """
        self.settings = settings
        self.llm = ChatAnthropic(
            model=settings.llm_model,
            api_key=settings.anthropic_api_key,
            timeout=settings.llm_timeout,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )

    async def classify_intent(self, prompt: str) -> Dict[str, Any]:
        """의도 분류 (Pure adapter: prompt → API → result)

        Args:
            prompt: Pre-rendered prompt string

        Returns:
            Dict[str, Any]: 의도 분류 결과
        """
        logger.info("[Anthropic] 의도 분류 요청")

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result_json = self._extract_json(response.content)
            result = json.loads(result_json)

            logger.info(f"[Anthropic] 의도 분류 완료: {result.get('primary_intent')}")

            return result

        except Exception as e:
            logger.error(f"[Anthropic] 의도 분류 실패: {str(e)}")
            raise

    async def generate_recipe(self, prompt: str) -> Dict[str, Any]:
        """레시피 생성 (Pure adapter: prompt → API → result)

        Args:
            prompt: Pre-rendered prompt string

        Returns:
            Dict[str, Any] or List[Dict[str, Any]]: Recipe data
        """
        logger.info("[Anthropic] 레시피 생성 요청")

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result_json = self._extract_json(response.content)
            result = json.loads(result_json)

            logger.info("[Anthropic] 레시피 생성 완료")

            return result

        except Exception as e:
            logger.error(f"[Anthropic] 레시피 생성 실패: {str(e)}")
            raise

    async def recommend_dishes(self, prompt: str) -> Dict[str, Any]:
        """음식 추천 (Pure adapter: prompt → API → result)

        Args:
            prompt: Pre-rendered prompt string

        Returns:
            Dict[str, Any]: 추천 결과
        """
        logger.info("[Anthropic] 음식 추천 요청")

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result_json = self._extract_json(response.content)
            result = json.loads(result_json)

            logger.info("[Anthropic] 음식 추천 완료")

            return result

        except Exception as e:
            logger.error(f"[Anthropic] 음식 추천 실패: {str(e)}")
            raise

    async def answer_question(self, prompt: str) -> Dict[str, Any]:
        """질문 답변 (Pure adapter: prompt → API → result)

        Args:
            prompt: Pre-rendered prompt string

        Returns:
            Dict[str, Any]: 답변 결과
        """
        logger.info("[Anthropic] 질문 답변 요청")

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result_json = self._extract_json(response.content)
            result = json.loads(result_json)

            logger.info("[Anthropic] 질문 답변 완료")

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
