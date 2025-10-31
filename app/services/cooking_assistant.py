import os
import json
import logging
from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from app.services.image_service import ImageService

# 로거 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 핸들러가 없으면 추가
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class CookingState(TypedDict):
    """요리 AI 어시스턴트 워크플로우 상태"""
    user_query: str
    primary_intent: str  # 주 의도 (recipe_create, recommend, question)
    secondary_intents: List[str]  # 부가 의도 (순차 실행)
    entities: Dict[str, Any]  # 추출된 엔티티 (요리명, 재료, 제약조건 등)
    confidence: float  # 의도 파악 확신도
    recipe_text: str  # 레시피 생성 결과 (단일)
    recipes: List[Dict[str, Any]]  # 레시피 목록 (복수)
    dish_names: List[str]  # 요리명 목록 (추천/레시피에서 추출)
    recommendation: str  # 음식 추천 결과
    answer: str  # 질문 답변 결과
    image_prompt: str  # 이미지 생성 프롬프트
    image_url: Optional[str]  # 생성된 이미지 URL
    image_urls: List[str]  # 이미지 URL 목록 (복수 레시피용)
    error: Optional[str]  # 오류 메시지


class CookingAssistant:
    """LangGraph 기반 요리 AI 어시스턴트

    사용자 의도를 파악하여:
    - 레시피 생성 (recipe_create)
    - 음식 추천 (recommend)
    - 요리 질문 답변 (question)
    """

    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-5-20250929",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            timeout=90
        )
        self.image_service = ImageService()
        self.graph = self._build_graph()

    def _classify_intent(self, state: CookingState) -> CookingState:
        """사용자 의도 및 엔티티 파악"""
        try:
            prompt = f"""당신은 요리 AI 어시스턴트의 의도 분류 및 엔티티 추출 전문가입니다.

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
입력: "{state['user_query']}"

위 기준과 예시에 따라 JSON으로 분류하세요:"""

            logger.info(f"[의도 분류] 사용자 쿼리: {state['user_query']}")
            logger.info(f"[의도 분류] LLM 요청 프롬프트:\n{prompt}")

            response = self.llm.invoke([HumanMessage(content=prompt)])
            result_json = response.content.strip()

            logger.info(f"[의도 분류] LLM 응답:\n{result_json}")

            # JSON 파싱 (마크다운 제거)
            if result_json.startswith("```"):
                lines = result_json.split('\n')
                result_json = '\n'.join(lines[1:-1]) if len(lines) > 2 else result_json
                result_json = result_json.strip()

            # JSON 이후의 추가 텍스트 제거 (마지막 } 찾기)
            last_brace = result_json.rfind('}')
            if last_brace != -1:
                result_json = result_json[:last_brace + 1]

            logger.info(f"[디버그] 정제된 JSON: {result_json}")

            result = json.loads(result_json)
            state["primary_intent"] = result.get("primary_intent", "recipe_create")
            state["secondary_intents"] = result.get("secondary_intents", [])
            state["entities"] = result.get("entities", {})
            state["confidence"] = result.get("confidence", 0.5)

            logger.info(f"[의도 분류 결과] primary={state['primary_intent']}, secondary={state['secondary_intents']}, confidence={state['confidence']}")
            logger.info(f"[엔티티 추출] {json.dumps(state['entities'], ensure_ascii=False)}")

        except Exception as e:
            logger.error(f"의도 분류 실패: {str(e)}")
            # 기본값으로 레시피 생성
            state["primary_intent"] = "recipe_create"
            state["secondary_intents"] = []
            state["entities"] = {}
            state["confidence"] = 0.5

        return state

    def _generate_recipe(self, state: CookingState) -> CookingState:
        """Claude를 사용해 레시피 생성 (Entity 기반)"""
        # Secondary intent로 실행되는 경우 제거
        if state.get("secondary_intents") and state["secondary_intents"][0] == "recipe_create":
            state["secondary_intents"].pop(0)
            logger.info(f"[Secondary 제거] recipe_create 실행 시작, 남은: {state['secondary_intents']}")

        try:
            # 엔티티 추출
            entities = state.get("entities", {})
            dishes = entities.get("dishes", [])
            ingredients = entities.get("ingredients", [])
            constraints = entities.get("constraints", {})
            dietary = entities.get("dietary", [])

            # 프롬프트 구성 - 엔티티 기반
            base_prompt = f"""사용자가 "{state['user_query']}"를 요청했습니다.

"""

            # 우선순위에 따라 요리명 결정
            # 1순위: entities.dishes (사용자 명시적 요청)
            # 2순위: state["dish_names"] (추천받은 요리)
            target_dishes = dishes if dishes else state.get("dish_names", [])

            # 엔티티 정보 추가
            if target_dishes:
                base_prompt += f"요리명: {', '.join(target_dishes)}\n"
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

            base_prompt += """
다음 JSON 형식으로 레시피를 작성하세요. 다른 텍스트 없이 오직 JSON만 반환하세요:

{
    "title": "요리 이름",
    "ingredients": ["재료1 (분량)", "재료2 (분량)", ...],
    "steps": ["1단계 설명", "2단계 설명", ...],
    "cooking_time": "예상 조리 시간 (예: 30분)",
    "difficulty": "난이도 (쉬움/중간/어려움 중 하나)"
}"""

            # 우선순위에 따른 프롬프트 생성
            if target_dishes:
                # entities.dishes 또는 추천받은 dish_names 사용
                if len(target_dishes) == 1:
                    prompt = base_prompt + f"\n\n위 정보를 바탕으로 '{target_dishes[0]}'의 레시피를 작성하세요."
                else:
                    prompt = base_prompt + f"\n\n위 정보를 바탕으로 {', '.join(target_dishes)} 각각의 레시피를 작성하세요."
            elif ingredients:
                # 재료 기반
                prompt = base_prompt + f"\n\n위 재료를 활용한 레시피를 작성하세요."
            else:
                # 엔티티가 없으면 기존 방식대로
                prompt = base_prompt

            logger.info(f"[요청] 사용자 쿼리: {state['user_query']}")
            logger.info(f"[요청] 추출된 엔티티: {json.dumps(entities, ensure_ascii=False)}")
            logger.info(f"[요청] 프롬프트:\n{prompt}")

            response = self.llm.invoke([HumanMessage(content=prompt)])
            recipe_json = response.content.strip()

            logger.info(f"[응답] 레시피:\n{recipe_json}")

            # JSON 파싱 검증 (마크다운 코드 블록 제거)
            # ```json과 ``` 제거
            if recipe_json.startswith("```"):
                # 첫 번째 줄 제거 (```json)
                lines = recipe_json.split('\n')
                recipe_json = '\n'.join(lines[1:-1]) if len(lines) > 2 else recipe_json
                recipe_json = recipe_json.strip()

            recipe_data = json.loads(recipe_json)

            # 타입 검증: 딕셔너리 또는 리스트 허용
            if isinstance(recipe_data, list):
                # 복수 레시피 (배열 형식)
                logger.info(f"[파싱 완료] 복수 레시피 타입: {type(recipe_data).__name__}, 개수: {len(recipe_data)}")
                state["recipes"] = recipe_data
                state["recipe_text"] = recipe_json
                # 요리명 목록을 dish_names에 저장
                state["dish_names"] = [r.get("title", "") for r in recipe_data if r.get("title")]
            elif isinstance(recipe_data, dict):
                # 단일 레시피 (딕셔너리 형식)
                logger.info(f"[파싱 완료] 단일 레시피 타입: {type(recipe_data).__name__}, 키: {list(recipe_data.keys())}")
                state["recipe_text"] = recipe_json
                # 단일 요리명을 리스트로 dish_names에 저장
                title = recipe_data.get("title", "")
                state["dish_names"] = [title] if title else []
            else:
                raise TypeError(f"레시피 데이터는 딕셔너리 또는 리스트여야 합니다. 현재 타입: {type(recipe_data).__name__}, 값: {recipe_data}")

        except Exception as e:
            logger.error(f"레시피 생성 실패: {str(e)}")
            state["error"] = f"레시피 생성 실패: {str(e)}"

        return state

    def _generate_image_prompt(self, state: CookingState) -> CookingState:
        """요리명을 기반으로 이미지 프롬프트 생성"""
        if state.get("error"):
            return state

        try:
            # 첫 번째 요리명으로 이미지 생성
            dish_names = state.get("dish_names", [])
            if dish_names:
                state["image_prompt"] = self.image_service.generate_image_prompt(
                    dish_names[0]
                )
        except Exception as e:
            state["error"] = f"이미지 프롬프트 생성 실패: {str(e)}"

        return state

    async def _generate_image(self, state: CookingState) -> CookingState:
        """Replicate를 사용해 이미지 생성"""
        # 레시피 생성에 실패했어도 진행 (이미지만 실패할 수도 있음)
        if not state.get("image_prompt"):
            return state

        try:
            image_url = await self.image_service.generate_image(
                state["image_prompt"]
            )
            state["image_url"] = image_url

            # 이미지 생성 실패는 에러로 처리하지 않음 (레시피는 반환)
            if not image_url:
                print("이미지 생성 실패, 레시피만 반환합니다.")

        except Exception as e:
            print(f"이미지 생성 중 예외 발생: {str(e)}")
            # 이미지 실패는 치명적이지 않음

        return state

    def _recommend_dish(self, state: CookingState) -> CookingState:
        """음식 추천 (Entity 기반)"""
        # Secondary intent로 실행되는 경우 제거
        if state.get("secondary_intents") and state["secondary_intents"][0] == "recommend":
            state["secondary_intents"].pop(0)
            logger.info(f"[Secondary 제거] recommend 실행 시작, 남은: {state['secondary_intents']}")

        try:
            # 엔티티 추출
            entities = state.get("entities", {})
            cuisine_type = entities.get("cuisine_type")
            taste = entities.get("taste", [])
            count = entities.get("count", 3)  # 기본 3개
            dietary = entities.get("dietary", [])
            ingredients = entities.get("ingredients", [])
            constraints = entities.get("constraints", {})

            # 프롬프트 구성 - 엔티티 기반
            base_prompt = f"""사용자가 "{state['user_query']}"를 요청했습니다.

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

            logger.info(f"[음식 추천] 사용자 쿼리: {state['user_query']}")
            logger.info(f"[음식 추천] 추출된 엔티티: {json.dumps(entities, ensure_ascii=False)}")

            prompt = base_prompt

            logger.info(f"[음식 추천] LLM 요청 프롬프트:\n{prompt}")

            response = self.llm.invoke([HumanMessage(content=prompt)])
            result_json = response.content.strip()

            logger.info(f"[음식 추천] LLM 응답:\n{result_json}")

            # JSON 파싱
            if result_json.startswith("```"):
                lines = result_json.split('\n')
                result_json = '\n'.join(lines[1:-1]) if len(lines) > 2 else result_json
                result_json = result_json.strip()

            # JSON 이후의 추가 텍스트 제거
            last_brace = result_json.rfind('}')
            if last_brace != -1:
                result_json = result_json[:last_brace + 1]

            # 타입 검증: 파싱 후 딕셔너리 확인
            recommendation_data = json.loads(result_json)
            if not isinstance(recommendation_data, dict):
                raise TypeError(f"추천 데이터는 딕셔너리여야 합니다. 현재 타입: {type(recommendation_data).__name__}, 값: {recommendation_data}")

            logger.info(f"[파싱 완료] 추천 타입: {type(recommendation_data).__name__}, 키: {list(recommendation_data.keys())}")

            state["recommendation"] = result_json

            # 추천받은 요리명을 dish_names에 저장
            recommendations = recommendation_data.get("recommendations", [])
            dish_names = [rec.get("name", "") for rec in recommendations if rec.get("name")]
            state["dish_names"] = dish_names

            logger.info(f"[음식 추천 완료] dish_names에 저장: {dish_names}")

        except Exception as e:
            logger.error(f"음식 추천 실패: {str(e)}")
            state["error"] = f"음식 추천 실패: {str(e)}"

        return state

    def _answer_question(self, state: CookingState) -> CookingState:
        """요리 관련 질문 답변"""
        # Secondary intent로 실행되는 경우 제거
        if state.get("secondary_intents") and state["secondary_intents"][0] == "question":
            state["secondary_intents"].pop(0)
            logger.info(f"[Secondary 제거] question 실행 시작, 남은: {state['secondary_intents']}")

        try:
            prompt = f"""사용자 질문: "{state['user_query']}"

위 질문에 대해 정확하고 도움이 되는 답변을 제공하세요.
요리, 재료, 영양, 조리법 등과 관련된 전문적인 답변을 작성하세요.

JSON 형식으로 반환:
{{
    "answer": "답변 내용",
    "additional_tips": ["추가 팁1", "추가 팁2"]
}}"""

            logger.info(f"[질문 답변] 사용자 쿼리: {state['user_query']}")
            logger.info(f"[질문 답변] LLM 요청 프롬프트:\n{prompt}")

            response = self.llm.invoke([HumanMessage(content=prompt)])
            result_json = response.content.strip()

            logger.info(f"[질문 답변] LLM 응답:\n{result_json}")

            # JSON 파싱
            if result_json.startswith("```"):
                lines = result_json.split('\n')
                result_json = '\n'.join(lines[1:-1]) if len(lines) > 2 else result_json
                result_json = result_json.strip()

            # JSON 이후의 추가 텍스트 제거
            last_brace = result_json.rfind('}')
            if last_brace != -1:
                result_json = result_json[:last_brace + 1]

            # 타입 검증: 파싱 후 딕셔너리 확인
            answer_data = json.loads(result_json)
            if not isinstance(answer_data, dict):
                raise TypeError(f"답변 데이터는 딕셔너리여야 합니다. 현재 타입: {type(answer_data).__name__}, 값: {answer_data}")

            logger.info(f"[파싱 완료] 답변 타입: {type(answer_data).__name__}, 키: {list(answer_data.keys())}")

            state["answer"] = result_json
            logger.info(f"[질문 답변 완료]")

        except Exception as e:
            logger.error(f"질문 답변 실패: {str(e)}")
            state["error"] = f"질문 답변 실패: {str(e)}"

        return state

    def _route_by_intent(self, state: CookingState) -> str:
        """의도에 따라 다음 노드 결정"""
        intent = state.get("primary_intent", "recipe_create")

        logger.info(f"[라우팅] primary_intent={intent}로 라우팅")

        if intent == "recipe_create":
            return "generate_recipe"
        elif intent == "recommend":
            return "recommend_dish"
        elif intent == "question":
            return "answer_question"
        else:
            # 기본값: 레시피 생성
            return "generate_recipe"

    def _check_secondary_intents(self, state: CookingState) -> str:
        """secondary_intents 확인하고 다음 노드 결정 (state 수정 없이 읽기만)"""
        secondary_intents = state.get("secondary_intents", [])

        if secondary_intents:
            next_intent = secondary_intents[0]
            logger.info(f"[Secondary 실행] {next_intent} 실행 예정 (남은 intents: {len(secondary_intents)})")

            # 다음 실행할 노드 결정 (state는 수정하지 않음)
            if next_intent == "recipe_create":
                return "generate_recipe"
            elif next_intent == "recommend":
                return "recommend_dish"
            elif next_intent == "question":
                return "answer_question"

        logger.info("[Secondary 완료] 모든 secondary_intents 실행 완료")
        return "end"

    def _pop_secondary_intent(self, state: CookingState) -> None:
        """현재 secondary_intent 제거 (노드 시작 시 호출)"""
        secondary_intents = state.get("secondary_intents", [])
        if secondary_intents:
            removed = secondary_intents.pop(0)
            logger.info(f"[Secondary 제거] {removed} 실행 시작, 남은: {secondary_intents}")

    def _build_graph(self) -> StateGraph:
        """LangGraph 워크플로우 구성 (Secondary Intents 지원)"""
        workflow = StateGraph(CookingState)

        # 1. 모든 노드 추가
        workflow.add_node("classify_intent", self._classify_intent)
        workflow.add_node("generate_recipe", self._generate_recipe)
        workflow.add_node("recommend_dish", self._recommend_dish)
        workflow.add_node("answer_question", self._answer_question)
        workflow.add_node("generate_image_prompt", self._generate_image_prompt)
        workflow.add_node("generate_image", self._generate_image)

        # 2. 시작점: 의도 분류
        workflow.set_entry_point("classify_intent")

        # 3. Primary Intent에 따라 분기
        workflow.add_conditional_edges(
            "classify_intent",
            self._route_by_intent,
            {
                "generate_recipe": "generate_recipe",
                "recommend_dish": "recommend_dish",
                "answer_question": "answer_question"
            }
        )

        # 4. 레시피 생성 후 이미지 생성, 그 후 Secondary Intents 확인
        workflow.add_edge("generate_recipe", "generate_image_prompt")
        workflow.add_edge("generate_image_prompt", "generate_image")

        # 5. 모든 작업 완료 후 Secondary Intents 확인
        #    - generate_image 후
        #    - recommend_dish 후
        #    - answer_question 후
        workflow.add_conditional_edges(
            "generate_image",
            self._check_secondary_intents,
            {
                "generate_recipe": "generate_recipe",
                "recommend_dish": "recommend_dish",
                "answer_question": "answer_question",
                "end": END
            }
        )

        workflow.add_conditional_edges(
            "recommend_dish",
            self._check_secondary_intents,
            {
                "generate_recipe": "generate_recipe",
                "recommend_dish": "recommend_dish",
                "answer_question": "answer_question",
                "end": END
            }
        )

        workflow.add_conditional_edges(
            "answer_question",
            self._check_secondary_intents,
            {
                "generate_recipe": "generate_recipe",
                "recommend_dish": "recommend_dish",
                "answer_question": "answer_question",
                "end": END
            }
        )

        return workflow.compile()

    async def run(self, user_query: str) -> CookingState:
        """
        요리 AI 어시스턴트 워크플로우 실행

        사용자 쿼리의 의도를 파악하여 적절한 응답 생성:
        - 레시피 생성: 상세한 조리법과 이미지
        - 음식 추천: 맞춤형 메뉴 제안
        - 질문 답변: 요리 관련 정보 제공

        Args:
            user_query: 사용자 쿼리
                예: "파스타 카르보나라 만드는 법" (레시피)
                예: "매운 음식 추천해줘" (추천)
                예: "김치찌개 칼로리는?" (질문)

        Returns:
            최종 상태 (의도, 레시피/추천/답변, 이미지 URL 등 포함)
        """
        initial_state: CookingState = {
            "user_query": user_query,
            "primary_intent": "",
            "secondary_intents": [],
            "entities": {},
            "confidence": 0.0,
            "recipe_text": "",
            "recipes": [],
            "dish_names": [],
            "recommendation": "",
            "answer": "",
            "image_prompt": "",
            "image_url": None,
            "image_urls": [],
            "error": None
        }

        final_state = await self.graph.ainvoke(initial_state)
        return final_state