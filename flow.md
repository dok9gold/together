# 📋 PyAi 프로그램 흐름 정리

## 🚀 1. 애플리케이션 시작 (main.py:1-59)

```
1. 환경 변수 로드 (.env)
2. FastAPI 앱 생성 (설정 기반)
3. CORS 미들웨어 추가
4. API 라우터 등록 (/api prefix)
5. uvicorn 서버 실행 (localhost:8000)
```

**핵심 코드:**
```python
app.include_router(router, prefix="/api", tags=["cooking"])
```

---

## 📡 2. 요청 수신 (routes.py:10-126)

**엔드포인트:** `POST /api/cooking`

```
사용자 요청 (JSON) → FastAPI 엔트포인트
    ↓
의존성 주입: CreateRecipeUseCase (Depends)
    ↓
use_case.execute(query)
```

**요청 흐름:**
1. `CookingRequest` 검증 (Pydantic)
2. DI Container에서 `CreateRecipeUseCase` 주입 (routes.py:13)
3. Use Case 실행 → 워크플로우 결과 반환
4. 결과 파싱 (recipe, recommendation, answer)
5. `CookingResponse` 반환 (통합 응답 형식)

---

## 🔧 3. 의존성 주입 (dependencies.py:25-32)

**DI Container 초기화 및 Use Case 주입**

```python
def get_create_recipe_use_case():
    container = get_container()  # 싱글톤
    yield container.create_recipe_use_case()
```

Container는 전역 싱글톤으로 관리되며, 모든 컴포넌트의 의존성을 관리합니다.

---

## 🏗️ 4. DI Container 구성 (container.py:31-123)

**의존성 그래프 (역순으로 구축):**

```
Settings (Singleton)
    ↓
PromptLoader (Singleton)
    ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Adapters (Singleton) - Port 구현
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ├─ AnthropicLLMAdapter (ILLMPort)
  └─ ReplicateImageAdapter (IImagePort)
    ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Domain Services (Singleton)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  └─ CookingAssistantService
         (llm_port, image_port 주입)
    ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Workflow Nodes (Factory)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ├─ IntentClassifierNode
  ├─ RecipeGeneratorNode
  ├─ ImageGeneratorNode
  ├─ RecommenderNode
  └─ QuestionAnswererNode
    ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Workflow (Singleton) - LangGraph
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  └─ CookingWorkflow (그래프 컴파일)
    ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Use Cases (Factory)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  └─ CreateRecipeUseCase
```

**생명주기:**
- **Singleton**: Settings, Adapters, Domain Services, Workflow
- **Factory**: Nodes, Use Cases (요청마다 새 인스턴스)

---

## 🎯 5. Use Case 실행 (create_recipe_use_case.py:32-73)

```python
async def execute(query: str) -> CookingState:
    # 1. 초기 상태 생성
    initial_state = {
        "user_query": query,
        "primary_intent": "",
        "secondary_intents": [],
        "entities": {},
        "recipe_text": "",
        "image_url": None,
        ...
    }

    # 2. 워크플로우 실행 (LangGraph)
    result = await self.workflow.run(initial_state)

    return result
```

**책임:**
- 초기 상태 생성
- 워크플로우 실행
- 결과 반환 (상태 변환 없음)

---

## 🔀 6. Workflow 오케스트레이션 (cooking_workflow.py:64-162)

### LangGraph StateGraph 구성:

```
┌─────────────────────┐
│  classify_intent    │ ← 시작점
└──────────┬──────────┘
           │
    ┌──────▼──────┐ route_by_intent()
    │ Primary?    │
    └─┬───┬───┬───┘
      │   │   │
  ┌───▼─┐ │ ┌─▼──────────────┐
  │recipe│ │ │recommender     │
  │gen.  │ │ │question_answer │
  └───┬──┘ │ └─┬─────────────┘
      │    │   │
  ┌───▼──┐ │   │
  │image │ │   │
  │gen.  │ │   │
  └───┬──┘ │   │
      │    │   │
    ┌─▼────▼───▼─┐ check_secondary_intents()
    │ Secondary?  │
    └─┬───────────┘
      │
   [순환 또는 END]
```

### 조건부 라우팅 (intent_router.py):

**1. `route_by_intent(state)` - Primary Intent 라우팅 (line 11-37)**
```python
routing_map = {
    "recipe_create": "recipe_generator",
    "recommend": "recommender",
    "question": "question_answerer"
}
```

**2. `check_secondary_intents(state)` - Secondary Intent 처리 (line 40-72)**
```python
if secondary_intents:
    next_intent = secondary_intents[0]  # 첫 번째 intent
    return routing_map.get(next_intent, "end")
else:
    return "end"  # 모든 intent 완료
```

---

## 🧠 7. Domain Service - 비즈니스 로직 (cooking_assistant.py:14-259)

**각 노드가 호출하는 도메인 메서드:**

### 7.1 의도 분류 (`classify_intent`, line 43-78)
```python
result = await self.llm_port.classify_intent(query)
state["primary_intent"] = result["primary_intent"]
state["secondary_intents"] = result["secondary_intents"]
state["entities"] = result["entities"]
state["confidence"] = result["confidence"]
```

### 7.2 레시피 생성 (`generate_recipe`, line 80-131)
```python
# Secondary intent 제거
if state["secondary_intents"][0] == "recipe_create":
    state["secondary_intents"].pop(0)

# LLM 호출
recipe_data = await self.llm_port.generate_recipe(query, entities)

# 단일 vs 복수 레시피 처리
if isinstance(recipe_data, list):
    state["recipes"] = recipe_data
    state["dish_names"] = [r["title"] for r in recipe_data]
elif isinstance(recipe_data, dict):
    state["recipe_text"] = json.dumps(recipe_data)
    state["dish_names"] = [recipe_data["title"]]
```

### 7.3 음식 추천 (`recommend_dishes`, line 133-178)
```python
recommendation_data = await self.llm_port.recommend_dishes(query, entities)
state["recommendation"] = json.dumps(recommendation_data)
state["dish_names"] = [rec["name"] for rec in recommendation_data["recommendations"]]
```

### 7.4 질문 답변 (`answer_question`, line 180-219)
```python
answer_data = await self.llm_port.answer_question(query)
state["answer"] = json.dumps(answer_data)
```

### 7.5 이미지 생성 (`generate_image`, line 221-259)
```python
if not state["dish_names"]:
    return state  # 건너뜀

dish_name = state["dish_names"][0]
prompt = self.image_port.generate_prompt(dish_name)
image_url = await self.image_port.generate_image(prompt)
state["image_url"] = image_url

# 실패해도 레시피는 반환 (우아한 성능 저하)
```

---

## 🔌 8. Adapters - 외부 시스템 연동

### LLM Adapter (AnthropicLLMAdapter)
**Port 인터페이스 구현:**
- `classify_intent()` → Claude API 호출 + 응답 파싱
- `generate_recipe()` → 프롬프트 생성 (Jinja2) + Claude API
- `recommend_dishes()` → 프롬프트 생성 + Claude API
- `answer_question()` → 프롬프트 생성 + Claude API

**프롬프트 관리:**
```
app/prompts/
├── intent_classification.yaml
├── recipe_generation.yaml
├── dish_recommendation.yaml
└── question_answering.yaml
```

### Image Adapter (ReplicateImageAdapter)
**Port 인터페이스 구현:**
- `generate_prompt()` → 한국 음식 이미지 프롬프트 생성
- `generate_image()` → Replicate Flux Schnell API 호출

---

## 📊 9. 응답 구성 (routes.py:42-122)

**통합 응답 형식:**
```json
{
  "status": "success",
  "intent": "recipe_create",
  "data": {
    "recipe": {...},           // 단일 레시피
    "recipes": [...],          // 복수 레시피
    "image_url": "https://...",
    "recommendations": [...],  // 음식 추천
    "answer": "...",           // 질문 답변
    "metadata": {
      "entities": {...},
      "confidence": 0.95,
      "secondary_intents_processed": [...]
    }
  },
  "message": null
}
```

**복합 의도 처리:**
- Primary intent 결과 + Secondary intents 결과 모두 포함
- 순차적 처리 (추천 → 레시피 → 질문 순서)

---

## 🔄 복합 쿼리 예시

**쿼리:** "매운 음식 추천하고 그 중 첫 번째 레시피도 보여줘"

```
1. classify_intent
   ↓ primary="recommend", secondary=["recipe_create"]

2. recommender (추천)
   ↓ dish_names=["떡볶이", "김치찌개", "매운갈비찜"]

3. check_secondary_intents
   ↓ secondary_intents[0]="recipe_create" → recipe_generator

4. recipe_generator (떡볶이 레시피 생성)
   ↓ recipe_text={...}

5. image_generator (떡볶이 이미지)
   ↓ image_url="https://..."

6. check_secondary_intents
   ↓ secondary_intents=[] → END
```

---

## 📌 핵심 설계 원칙

### 1. Hexagonal Architecture
- Domain은 Port에만 의존 (외부 시스템 몰라도 됨)
- Adapter는 Port 구현 (교체 가능)

### 2. 의존성 주입 (DI)
- Container가 모든 의존성 관리
- 테스트 시 Mock 주입 가능

### 3. LangGraph 워크플로우
- 상태 기반 그래프 (StateGraph)
- 조건부 분기 (primary/secondary intents)
- 순환 가능 (복합 의도 처리)

### 4. 우아한 성능 저하
- 이미지 생성 실패 시에도 레시피 반환
- 각 단계별 에러 핸들링

### 5. 프롬프트 관리
- YAML + Jinja2로 프롬프트 외부화
- Adapter에서 프롬프트 생성 (도메인 오염 방지)

---

## 🔗 전체 요청 흐름 요약

```
[클라이언트]
    ↓ POST /api/cooking {"query": "..."}
[routes.py]
    ↓ Depends(get_create_recipe_use_case)
[dependencies.py]
    ↓ Container.create_recipe_use_case()
[container.py]
    ↓ DI: CookingWorkflow + Nodes + Services + Adapters
[create_recipe_use_case.py]
    ↓ workflow.run(initial_state)
[cooking_workflow.py]
    ↓ LangGraph StateGraph 실행
    ├─ classify_intent → IntentClassifierNode
    │   └─ cooking_assistant.classify_intent()
    │       └─ llm_adapter.classify_intent() → Claude API
    │
    ├─ route_by_intent() → 의도별 분기
    │
    ├─ recipe_generator → RecipeGeneratorNode
    │   └─ cooking_assistant.generate_recipe()
    │       └─ llm_adapter.generate_recipe() → Claude API
    │
    ├─ image_generator → ImageGeneratorNode
    │   └─ cooking_assistant.generate_image()
    │       └─ image_adapter.generate_image() → Replicate API
    │
    ├─ recommender → RecommenderNode
    │   └─ cooking_assistant.recommend_dishes()
    │       └─ llm_adapter.recommend_dishes() → Claude API
    │
    ├─ question_answerer → QuestionAnswererNode
    │   └─ cooking_assistant.answer_question()
    │       └─ llm_adapter.answer_question() → Claude API
    │
    └─ check_secondary_intents() → 순환 또는 END
[routes.py]
    ↓ 결과 파싱 및 응답 구성
[클라이언트]
    ← CookingResponse JSON
```

---

## 📂 주요 파일 위치

```
app/
├── main.py                                # 1. 앱 시작점
├── api/
│   ├── routes.py                          # 2. REST API 엔드포인트
│   └── dependencies.py                    # 3. DI 헬퍼
├── core/
│   ├── container.py                       # 4. DI Container
│   ├── config.py                          # 설정 관리
│   └── prompt_loader.py                   # 프롬프트 로더
├── application/
│   ├── use_cases/
│   │   └── create_recipe_use_case.py      # 5. Use Case
│   └── workflow/
│       ├── cooking_workflow.py            # 6. LangGraph 워크플로우
│       ├── nodes/                         # 워크플로우 노드
│       │   ├── intent_classifier_node.py
│       │   ├── recipe_generator_node.py
│       │   ├── image_generator_node.py
│       │   ├── recommender_node.py
│       │   └── question_answerer_node.py
│       └── edges/
│           └── intent_router.py           # 라우팅 로직
├── domain/
│   ├── services/
│   │   └── cooking_assistant.py           # 7. 도메인 서비스
│   ├── ports/
│   │   ├── llm_port.py                    # ILLMPort 인터페이스
│   │   └── image_port.py                  # IImagePort 인터페이스
│   └── entities/
│       └── cooking_state.py               # CookingState TypedDict
└── adapters/
    ├── llm/
    │   └── anthropic_adapter.py           # 8. Anthropic LLM 구현
    └── image/
        └── replicate_adapter.py           # 8. Replicate 이미지 구현
```