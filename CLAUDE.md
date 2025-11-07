# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

PyAi는 FastAPI, Claude (Anthropic), LangGraph로 구축된 한국어 요리 AI 어시스턴트 서비스입니다. **Hexagonal Architecture (Ports and Adapters)** 패턴을 적용하여 외부 시스템(LLM, 이미지 생성)과의 결합도를 낮추고 테스트 가능성을 높였습니다.

## 주요 명령어

### 개발 서버 실행
```bash
# 기본 방법 - 핫 리로드를 지원하는 FastAPI 서버 실행
python -m app.main

# uvicorn 직접 사용 (대안)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 설치
```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정 (.env.example을 .env로 복사하고 API 키 추가)
cp .env.example .env
```

### API 테스트
```bash
# 레시피 생성 테스트
curl -X POST http://localhost:8000/api/cooking \
  -H "Content-Type: application/json" \
  -d '{"query": "김치찌개 만드는 법"}'

# 헬스 체크
curl http://localhost:8000/api/health
```

## 아키텍처 개요

### Hexagonal Architecture (Ports and Adapters)

이 프로젝트는 **Hexagonal Architecture**를 따릅니다. 핵심 아이디어:
- **Domain Layer**: 순수 비즈니스 로직 (외부 시스템 몰라도 됨)
- **Ports**: Domain이 외부 시스템에게 요구하는 인터페이스
- **Adapters**: Port 인터페이스를 실제 구현 (Anthropic, Replicate 등)

```
┌─────────────────────────────────────────────────┐
│          API Layer (FastAPI)                     │
│  - routes.py: REST 엔드포인트                      │
│  - dependencies.py: DI Container 주입             │
└───────────────┬─────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────┐
│     Application Layer (Use Cases + Workflow)    │
│  - CreateRecipeUseCase: 요청 → 응답 변환          │
│  - CookingWorkflow: LangGraph 오케스트레이션       │
│  - Nodes: 워크플로우 단계 (의도분류, 레시피생성 등)    │
└───────────────┬─────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────┐
│      Domain Layer (순수 비즈니스 로직)             │
│  - CookingAssistantService: 핵심 도메인 서비스     │
│  - Entities: CookingState, Recipe 등             │
│  - Ports (인터페이스):                            │
│    · ILLMPort: LLM 서비스 요구사항                │
│    · IImagePort: 이미지 생성 서비스 요구사항         │
└───────────────┬─────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────┐
│      Adapters (외부 시스템 연동)                   │
│  - AnthropicLLMAdapter: ILLMPort 구현            │
│  - ReplicateImageAdapter: IImagePort 구현        │
└─────────────────────────────────────────────────┘
```

### 핵심 워크플로우 (LangGraph 기반)

`app/application/workflow/cooking_workflow.py`에 정의된 상태 기반 그래프:

1. **의도 분류** (`classify_intent`)
   - 사용자 쿼리 분석 → `recipe_create` / `recommend` / `question` 결정
   - 엔티티 추출 (요리명, 재료, 제약조건 등)

2. **Primary Intent 라우팅** (`route_by_intent`)
   - `recipe_create` → `recipe_generator` → `image_generator`
   - `recommend` → `recommender`
   - `question` → `question_answerer`

3. **Secondary Intents 처리** (`check_secondary_intents`)
   - 복합 쿼리 지원 (예: "매운 음식 추천하고 그 중 하나 레시피도 보여줘")
   - 각 단계 완료 후 다음 secondary intent로 분기

4. **이미지 생성** (레시피 생성 후 자동)
   - Replicate Flux Schnell 모델로 음식 이미지 생성
   - 실패해도 레시피는 정상 반환 (우아한 성능 저하)

### DI Container (Dependency Injection)

`app/core/container.py`에서 모든 의존성을 관리합니다 (Spring의 ApplicationContext와 유사):

```python
# Adapters (Singleton)
llm_adapter = AnthropicLLMAdapter(settings)
image_adapter = ReplicateImageAdapter(settings)

# Domain Services (Adapter 주입)
cooking_assistant = CookingAssistantService(
    llm_port=llm_adapter,
    image_port=image_adapter
)

# Workflow (Nodes + Graph)
cooking_workflow = CookingWorkflow(
    intent_classifier=IntentClassifierNode(cooking_assistant),
    recipe_generator=RecipeGeneratorNode(cooking_assistant),
    ...
)
```

**장점**:
- LLM 제공자 교체 가능 (Anthropic → OpenAI): Adapter만 교체
- 테스트 시 Mock Adapter 주입 가능
- 의존성 명시적 관리

## 레이어별 책임

### 1. Domain Layer (`app/domain/`)
**순수 비즈니스 로직만 포함. 외부 시스템 몰라도 됨.**

- **Services** (`cooking_assistant.py`):
  - `classify_intent()`: 의도 분류 및 엔티티 추출
  - `generate_recipe()`: 레시피 생성
  - `recommend_dishes()`: 음식 추천
  - `answer_question()`: 질문 답변
  - `generate_image()`: 이미지 생성

- **Ports** (인터페이스):
  - `ILLMPort`: LLM 서비스 요구사항 (`classify_intent`, `generate_recipe` 등)
  - `IImagePort`: 이미지 생성 서비스 요구사항

- **Entities**:
  - `CookingState`: TypedDict로 워크플로우 상태 정의
  - `Recipe`, `Recommendation`, `Question`: 데이터 모델

**규칙**:
- ❌ Anthropic, Replicate 등 구체적 구현 의존 금지
- ✅ Port 인터페이스에만 의존
- ✅ 테스트 시 Port를 모킹

### 2. Adapters Layer (`app/adapters/`)
**Port 인터페이스를 실제 외부 시스템에 맞게 구현**

- **LLM Adapters**:
  - `AnthropicLLMAdapter`: ILLMPort 구현 (Claude API 호출)
  - 프롬프트 생성 및 응답 파싱 담당

- **Image Adapters**:
  - `ReplicateImageAdapter`: IImagePort 구현 (Replicate API 호출)

**규칙**:
- ✅ Port 인터페이스 구현 필수
- ✅ 외부 API 호출, 에러 핸들링, 재시도 로직 포함
- ✅ 프롬프트 생성 로직은 Adapter에 위치 (도메인 오염 방지)

### 3. Application Layer (`app/application/`)
**워크플로우 오케스트레이션 및 Use Case 구현**

- **Workflow** (`cooking_workflow.py`):
  - LangGraph StateGraph 구성
  - 노드 연결 및 조건부 분기 정의
  - ❌ 비즈니스 로직 작성 금지 (Domain Services에 위임)

- **Nodes** (`workflow/nodes/`):
  - `IntentClassifierNode`: 의도 분류 노드 (→ `cooking_assistant.classify_intent()`)
  - `RecipeGeneratorNode`: 레시피 생성 노드
  - `ImageGeneratorNode`: 이미지 생성 노드
  - 각 노드는 `CookingAssistantService`의 메서드를 호출만 함

- **Use Cases** (`use_cases/`):
  - `CreateRecipeUseCase`: 초기 상태 생성 → 워크플로우 실행 → 응답 변환

### 4. API Layer (`app/api/`)
**REST API 엔드포인트**

- **Routes** (`routes.py`):
  - `/api/cooking` (POST): 통합 쿼리 처리 엔드포인트
  - 의도별 응답 데이터 구성 (레시피, 추천, 질문 답변)
  - `/api/health` (GET): 헬스 체크

- **Dependencies** (`dependencies.py`):
  - DI Container에서 Use Case 주입

## 응답 형식

모든 `/api/cooking` 응답은 통합 구조를 따릅니다:

```json
{
  "status": "success|error",
  "intent": "recipe_create|recommend|question",
  "data": {
    // 레시피 생성 (recipe_create)
    "recipe": {...},              // 단일 레시피
    "recipes": [...],             // 복수 레시피
    "image_url": "https://...",

    // 음식 추천 (recommend)
    "recommendations": [
      {"name": "...", "description": "...", "reason": "..."}
    ],

    // 질문 답변 (question)
    "answer": "...",
    "additional_tips": [...],

    // 메타데이터 (항상 포함)
    "metadata": {
      "entities": {...},
      "confidence": 0.95,
      "secondary_intents_processed": [...]
    }
  },
  "message": null 또는 "이미지 생성 실패"
}
```

## 환경 변수

`.env`에 필수:
```env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
REPLICATE_API_TOKEN=r8_xxxxx
```

## 새로운 LLM 제공자 추가하는 방법

Hexagonal Architecture 덕분에 LLM 제공자 교체가 쉽습니다:

1. **새 Adapter 작성** (`app/adapters/llm/openai_adapter.py`):
```python
from app.domain.ports.llm_port import ILLMPort

class OpenAILLMAdapter(ILLMPort):
    async def classify_intent(self, query: str) -> Dict[str, Any]:
        # OpenAI API 호출
        pass
```

2. **DI Container 수정** (`app/core/container.py`):
```python
llm_adapter = providers.Singleton(
    OpenAILLMAdapter,  # Anthropic → OpenAI
    settings=config
)
```

3. **도메인 로직 변경 불필요!** Domain Services는 `ILLMPort`에만 의존하므로 그대로 작동합니다.

## 새로운 의도(Intent) 추가하는 방법

1. **의도 분류 프롬프트 업데이트** (`anthropic_adapter.py:_build_intent_classification_prompt`):
   - 새 의도 추가 (예: `nutrition_info`)

2. **Domain Service에 메서드 추가** (`cooking_assistant.py`):
```python
async def get_nutrition_info(self, state: CookingState) -> CookingState:
    result = await self.llm_port.get_nutrition_info(query)
    state["nutrition"] = json.dumps(result, ensure_ascii=False)
    return state
```

3. **LLM Port 인터페이스 확장** (`llm_port.py`):
```python
@abstractmethod
async def get_nutrition_info(self, query: str) -> Dict[str, Any]:
    pass
```

4. **Adapter 구현** (`anthropic_adapter.py`):
```python
async def get_nutrition_info(self, query: str) -> Dict[str, Any]:
    # 프롬프트 생성 및 API 호출
    pass
```

5. **Workflow에 노드 추가** (`cooking_workflow.py`):
```python
workflow.add_node("nutrition_info", NutritionInfoNode(cooking_assistant))
workflow.add_conditional_edges("classify_intent", ..., {
    "nutrition_info": "nutrition_info"
})
```

## 주요 기능

- **한국어 네이티브 지원**: 프롬프트 및 응답 한국어 최적화
- **우아한 성능 저하**: 이미지 생성 실패 시에도 레시피는 정상 반환
- **무상태 설계**: 데이터베이스 불필요 (Stateless)
- **90초 타임아웃**: LLM 및 이미지 생성 지연 시간 수용
- **구조화된 로깅**: 의도 분류, 워크플로우 실행 디버깅 용이

## API 문서

서버 실행 시 자동 생성:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 주의사항

### 코드 수정 시 유의점

1. **비즈니스 로직은 Domain Layer에만 작성**
   - ❌ Adapter에 비즈니스 로직 포함 금지
   - ❌ Workflow에 비즈니스 로직 포함 금지
   - ✅ `CookingAssistantService`에 작성

2. **Port 인터페이스 우선**
   - 새 기능 추가 시 Port 인터페이스부터 정의
   - 도메인이 "무엇을 원하는지" 먼저 정의 → Adapter에서 "어떻게 구현할지" 결정

3. **프롬프트 관리**
   - 프롬프트 생성 로직은 Adapter에 위치
   - 향후 프롬프트 관리 시스템(Jinja2 + YAML) 도입 예정 (framework.md 참조)

4. **Secondary Intents 처리**
   - `secondary_intents` 리스트는 각 노드에서 `pop(0)` 방식으로 소비
   - 빈 리스트가 되면 `check_secondary_intents()`가 `"end"` 반환하여 종료