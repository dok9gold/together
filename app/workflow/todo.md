# Workflow 구현 계획

## 개요
LangGraph 기반 요리 AI 워크플로우 구현
- **생성형 AI 채팅**: 메인 그래프 호출 → 전체 워크플로우 실행
- **웹 서비스**: 노드 단독 호출 → 개별 기능 사용

---

## 폴더 구조

```
app/workflow/
├── __init__.py
├── todo.md
│
└── cooking/
    ├── __init__.py
    ├── graph.py                      # 메인 LangGraph
    ├── state.py                      # CookingState 정의
    ├── router.py                     # 라우팅 함수
    │
    ├── node/
    │   ├── __init__.py
    │   ├── base.py                   # BaseNode (듀얼 호출 지원)
    │   ├── intent_extractor.py       # 의도 분석 + 개체 추출
    │   ├── recommender.py            # 요리 추천
    │   ├── recipe_generator.py       # 레시피 생성
    │   └── discount_recommender.py   # 할인상품 기반 추천
    │
    └── prompt/
        ├── intent_extractor/
        │   └── (프롬프트.yaml)
        ├── recommender/
        │   └── (프롬프트.yaml)
        ├── recipe_generator/
        │   └── (프롬프트.yaml)
        └── discount_recommender/
            └── (프롬프트.yaml)
```

---

## Phase 1: State 설계

### 1.1 CookingState
- [ ] state.py 작성

```python
class CookingState(TypedDict):
    # 입력
    user_query: str
    session_id: Optional[str]
    chat_history: List[dict]

    # 의도 분석 결과
    primary_intent: str                 # 'recipe_create' | 'recommend' | 'question'
    secondary_intents: List[str]
    entities: Dict[str, Any]            # 추출된 개체 (재료, 요리명 등)

    # 상품/할인 정보
    available_products: List[Product]
    active_discounts: List[Discount]

    # 생성 결과
    recipes: List[Recipe]
    recommendation: Optional[Recommendation]

    # 에러
    error: Optional[str]
```

---

## Phase 2: 노드 구현

### 2.1 BaseNode (듀얼 호출 지원)
- [ ] base.py 작성
- [ ] 워크플로우용 `execute(state)` + 단독 호출용 메서드

```python
class BaseNode(ABC):
    """듀얼 호출 지원 베이스 노드"""

    # 워크플로우용
    async def __call__(self, state: CookingState) -> CookingState:
        return await self.execute(state)

    @abstractmethod
    async def execute(self, state: CookingState) -> CookingState:
        """워크플로우 실행"""
        pass
```

### 2.2 IntentExtractorNode
- [ ] 의도 분석 (recipe_create, recommend, question)
- [ ] 개체 추출 (재료, 요리명, 조건 등)
- [ ] 프롬프트 작성 (Jinja2)

### 2.3 RecommenderNode
- [ ] 요리 추천 로직
- [ ] 카테고리/조건 기반 필터링
- [ ] 단독 호출: `recommend(category, condition) -> List[Recipe]`

### 2.4 RecipeGeneratorNode
- [ ] 레시피 생성 (LLM 기반)
- [ ] 상세 레시피 구조화
- [ ] 단독 호출: `generate(dish_name, constraints) -> Recipe`

### 2.5 DiscountRecommenderNode
- [ ] 할인 상품 조회
- [ ] 할인 상품 기반 요리 추천
- [ ] 단독 호출: `recommend_by_discount() -> List[Recipe]`

---

## Phase 3: 그래프 구성

### 3.1 graph.py
- [ ] StateGraph 구성
- [ ] 노드 연결
- [ ] 조건부 라우팅

```
[시작] → [IntentExtractor] → [조건 분기]
                               ├── recipe_create → [RecipeGenerator] → [끝]
                               ├── recommend → [Recommender] → [끝]
                               └── question → [QuestionAnswerer] → [끝]

* DiscountRecommender는 Recommender 노드 내에서 할인 정보 활용
```

### 3.2 router.py
- [ ] `route_by_intent()` - primary intent 라우팅
- [ ] `check_secondary_intents()` - secondary intent 처리

---

## Phase 4: 프롬프트 구현 (Jinja2)

### 4.1 프롬프트 구조
- [ ] intent_extractor/system.yaml
- [ ] intent_extractor/user.yaml
- [ ] recommender/system.yaml
- [ ] recipe_generator/system.yaml
- [ ] discount_recommender/system.yaml

---

## Phase 5: 서비스 연동

### 5.1 ChatService 수정
- [ ] 기존 Mock 제거
- [ ] CookingWorkflow 연동

### 5.2 웹 API 연동 (단독 호출)
- [ ] RecommendService → RecommenderNode 연동
- [ ] RecipeService → RecipeGeneratorNode 연동
- [ ] DiscountService → DiscountRecommenderNode 연동

---

## 우선순위 정리

| 순서 | 작업 | 파일 |
|------|------|------|
| 1 | CookingState 정의 | state.py |
| 2 | BaseNode 작성 | node/base.py |
| 3 | 각 노드 구현 | node/*.py |
| 4 | 프롬프트 작성 | prompt/**/*.yaml |
| 5 | 라우터 구현 | router.py |
| 6 | 그래프 구성 | graph.py |
| 7 | 서비스 연동 | service/*.py |

---

## 완료 체크리스트

- [ ] Phase 1: State
- [ ] Phase 2: Nodes
- [ ] Phase 3: Graph
- [ ] Phase 4: Prompts
- [ ] Phase 5: Service 연동
