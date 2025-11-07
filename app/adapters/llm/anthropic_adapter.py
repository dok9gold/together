"""AnthropicLLMAdapter - Anthropic Claude LLM 어댑터

ILLMPort 인터페이스를 Anthropic API에 맞게 구현합니다.
"""
from app.domain.ports.llm_port import ILLMPort
from app.core.config import Settings
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

    Attributes:
        settings: 애플리케이션 설정
        llm: LangChain ChatAnthropic 인스턴스
    """

    def __init__(self, settings: Settings):
        """의존성 주입: Settings

        Args:
            settings: 애플리케이션 설정 (Config)
        """
        self.settings = settings
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
        prompt = self._build_intent_classification_prompt(query)

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
        prompt = self._build_recipe_generation_prompt(query, entities)

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
        prompt = self._build_recommendation_prompt(query, entities)

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
        prompt = self._build_question_answering_prompt(query)

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
    # Private Methods (프롬프트 생성 및 유틸리티)
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

    def _build_intent_classification_prompt(self, query: str) -> str:
        """의도 분류 프롬프트 생성

        기존 로직을 그대로 유지합니다.

        Args:
            query: 사용자 쿼리

        Returns:
            str: 의도 분류 프롬프트
        """
        return f"""당신은 요리 AI 어시스턴트의 의도 분류 및 엔티티 추출 전문가입니다.

## 분류 기준
1. recipe_create: 특정 요리의 구체적인 조리법 요구
   - 키워드: "만드는 법", "레시피", "어떻게 만들어", "조리법", "요리법"

2. recommend: 여러 음식 중 선택지 요구
   - 키워드: "추천", "뭐 먹을까", "메뉴 제안", "어떤 음식", "소개"

3. question: 요리 관련 정보 질문
   - 키워드: "칼로리", "영양", "얼마나", "?", "뭐야", "차이"

## 엔티티 추출
- dishes: 구체적 요리명 (예: ["김치찌개", "된장찌개"])
- ingredients: 재료 (예: ["토마토", "달걀"])
- cuisine_type: 요리 유형 (예: "한식", "양식", "일식", "중식")
- taste: 맛 선호 (예: ["매운맛", "단맛", "짠맛"])
- constraints: 제약조건
  - time: 시간 (예: "30분", "1시간")
  - difficulty: 난이도 (예: "쉬움", "중간", "어려움")
  - servings: 인분 (예: 2, 4)
- dietary: 식이제한 (예: ["비건", "저염식", "글루텐프리"])
- count: 요청 개수 (예: 3)

## Few-Shot 예시

### 예시 1: 단일 레시피
입력: "김치찌개 만드는 법 알려줘"
출력:
{{
    "primary_intent": "recipe_create",
    "secondary_intents": [],
    "entities": {{
        "dishes": ["김치찌개"]
    }},
    "confidence": 0.95
}}

### 예시 2: 복수 레시피
입력: "김치찌개, 된장찌개, 순두부찌개 레시피 조회"
출력:
{{
    "primary_intent": "recipe_create",
    "secondary_intents": [],
    "entities": {{
        "dishes": ["김치찌개", "된장찌개", "순두부찌개"],
        "count": 3
    }},
    "confidence": 0.95
}}

### 예시 3: 제약 조건 포함
입력: "토마토와 달걀로 30분 안에 만들 수 있는 요리"
출력:
{{
    "primary_intent": "recipe_create",
    "secondary_intents": [],
    "entities": {{
        "ingredients": ["토마토", "달걀"],
        "constraints": {{"time": "30분"}}
    }},
    "confidence": 0.9
}}

### 예시 4: 추천
입력: "매운 한식 추천해줘"
출력:
{{
    "primary_intent": "recommend",
    "secondary_intents": [],
    "entities": {{
        "cuisine_type": "한식",
        "taste": ["매운맛"],
        "count": 3
    }},
    "confidence": 0.9
}}

### 예시 5: 복합 의도 (추천 + 레시피)
입력: "매운 음식 추천해서 그 중 하나 레시피도 보여줘"
출력:
{{
    "primary_intent": "recommend",
    "secondary_intents": ["recipe_create"],
    "entities": {{
        "taste": ["매운맛"],
        "count": 3
    }},
    "confidence": 0.85
}}

### 예시 6: 질문
입력: "김치찌개 칼로리 얼마야?"
출력:
{{
    "primary_intent": "question",
    "secondary_intents": [],
    "entities": {{
        "dishes": ["김치찌개"]
    }},
    "confidence": 0.95
}}

## 주의사항
- 복합 의도는 primary_intent + secondary_intents 사용
- confidence는 0.0~1.0 (0.7 이하면 애매함)
- 애매하면 가장 핵심적인 의도 선택
- entities는 추출 가능한 것만 포함 (없으면 빈 객체)

## 현재 사용자 입력
입력: "{query}"

위 기준과 예시에 따라 JSON으로 분류하세요:"""

    def _build_recipe_generation_prompt(
        self,
        query: str,
        entities: Dict[str, Any]
    ) -> str:
        """레시피 생성 프롬프트 생성

        Args:
            query: 사용자 쿼리
            entities: 추출된 엔티티

        Returns:
            str: 레시피 생성 프롬프트
        """
        # 엔티티 추출
        dishes = entities.get("dishes", [])
        ingredients = entities.get("ingredients", [])
        constraints = entities.get("constraints", {})
        dietary = entities.get("dietary", [])

        # 프롬프트 구성
        base_prompt = f"""사용자가 "{query}"를 요청했습니다.

"""

        # 엔티티 정보 추가
        if dishes:
            base_prompt += f"요리명: {', '.join(dishes)}\n"
        if ingredients:
            base_prompt += f"사용 재료: {', '.join(ingredients)}\n"
        if constraints:
            constraint_details = []
            if constraints.get("time"):
                constraint_details.append(f"조리 시간: {constraints['time']}")
            if constraints.get("difficulty"):
                constraint_details.append(f"난이도: {constraints['difficulty']}")
            if constraints.get("servings"):
                constraint_details.append(f"인분: {constraints['servings']}인분")
            if constraint_details:
                base_prompt += f"제약 조건: {', '.join(constraint_details)}\n"
        if dietary:
            base_prompt += f"식이 제한: {', '.join(dietary)}\n"

        # 출력 형식 설명
        if dishes and len(dishes) == 1:
            # 단일 레시피
            base_prompt += """
다음 JSON 형식으로 레시피를 작성하세요. 다른 텍스트 없이 오직 JSON만 반환하세요:

{
    "title": "요리 이름",
    "ingredients": ["재료1 (분량)", "재료2 (분량)", ...],
    "steps": ["1단계 설명", "2단계 설명", ...],
    "cooking_time": "예상 조리 시간 (예: 30분)",
    "difficulty": "난이도 (쉬움/중간/어려움 중 하나)"
}"""
        elif dishes and len(dishes) > 1:
            # 복수 레시피
            base_prompt += f"""
다음 JSON 배열 형식으로 {len(dishes)}개의 레시피를 작성하세요. 다른 텍스트 없이 오직 JSON만 반환하세요:

[
    {{
        "title": "요리 이름1",
        "ingredients": ["재료1 (분량)", "재료2 (분량)", ...],
        "steps": ["1단계 설명", "2단계 설명", ...],
        "cooking_time": "예상 조리 시간",
        "difficulty": "난이도 (쉬움/중간/어려움 중 하나)"
    }},
    {{
        "title": "요리 이름2",
        ...
    }},
    ...
]"""
        else:
            # 재료 기반 또는 일반
            base_prompt += """
다음 JSON 형식으로 레시피를 작성하세요. 다른 텍스트 없이 오직 JSON만 반환하세요:

{
    "title": "요리 이름",
    "ingredients": ["재료1 (분량)", "재료2 (분량)", ...],
    "steps": ["1단계 설명", "2단계 설명", ...],
    "cooking_time": "예상 조리 시간 (예: 30분)",
    "difficulty": "난이도 (쉬움/중간/어려움 중 하나)"
}"""

        return base_prompt

    def _build_recommendation_prompt(
        self,
        query: str,
        entities: Dict[str, Any]
    ) -> str:
        """음식 추천 프롬프트 생성

        Args:
            query: 사용자 쿼리
            entities: 추출된 엔티티

        Returns:
            str: 추천 프롬프트
        """
        # 엔티티 추출
        cuisine_type = entities.get("cuisine_type")
        taste = entities.get("taste", [])
        count = entities.get("count", 3)  # 기본 3개
        dietary = entities.get("dietary", [])
        ingredients = entities.get("ingredients", [])
        constraints = entities.get("constraints", {})

        # 프롬프트 구성
        base_prompt = f"""사용자가 "{query}"를 요청했습니다.

"""

        # 엔티티 정보 추가
        requirements = []
        if cuisine_type:
            requirements.append(f"요리 유형: {cuisine_type}")
        if taste:
            requirements.append(f"맛 선호: {', '.join(taste)}")
        if ingredients:
            requirements.append(f"활용 재료: {', '.join(ingredients)}")
        if dietary:
            requirements.append(f"식이 제한: {', '.join(dietary)}")
        if constraints:
            constraint_details = []
            if constraints.get("time"):
                constraint_details.append(f"조리 시간: {constraints['time']}")
            if constraints.get("difficulty"):
                constraint_details.append(f"난이도: {constraints['difficulty']}")
            if constraint_details:
                requirements.append(', '.join(constraint_details))

        if requirements:
            base_prompt += "요구사항:\n"
            for req in requirements:
                base_prompt += f"- {req}\n"
            base_prompt += "\n"

        base_prompt += f"""위 요구사항에 맞는 음식 {count}가지를 추천하고, 각각에 대해 간단한 설명을 포함하세요.

JSON 형식으로 반환:
{{
    "recommendations": [
        {{"name": "음식 이름", "description": "간단한 설명", "reason": "추천 이유"}},
        ...
    ]
}}

⚠️ 중요: 오직 name, description, reason 필드만 포함하세요. recipe, ingredients, steps 등 다른 필드는 절대 추가하지 마세요."""

        return base_prompt

    def _build_question_answering_prompt(self, query: str) -> str:
        """질문 답변 프롬프트 생성

        Args:
            query: 사용자 질문

        Returns:
            str: 질문 답변 프롬프트
        """
        return f"""사용자 질문: "{query}"

위 질문에 대해 정확하고 도움이 되는 답변을 제공하세요.
요리, 재료, 영양, 조리법 등과 관련된 전문적인 답변을 작성하세요.

JSON 형식으로 반환:
{{
    "answer": "답변 내용",
    "additional_tips": ["추가 팁1", "추가 팁2"]
}}"""
