# AI Assistant Framework

FastAPI + LangGraph 기반 AI Agent 애플리케이션을 빠르게 구축하는 통합 프레임워크

Hexagonal Architecture, Port-Adapter Pattern, 데코레이터 기반 의존성 주입, 프롬프트 관리를 기본 제공합니다.

**이 레포지토리는 첫 번째 템플릿인 `cooking-assistant` 예제를 포함합니다.**

---

## 핵심 특징

### 아키텍처
- **Hexagonal Architecture** - Port-Adapter 패턴으로 외부 시스템 교체 가능
- **Pure Port 원칙** - Adapter는 API 호출만, 비즈니스 로직은 Application Layer가 담당
- **데코레이터 기반 DI** - @singleton, @inject로 명시적 의존성 관리

### 핵심 컴포넌트
- **프롬프트 관리** - YAML 기반 버전 관리 및 Jinja2 템플릿
- **JWT 인증** - 선택적/필수 인증 전략 지원
- **LangGraph Workflow** - AI Agent 워크플로우 오케스트레이션
- **멀티 Adapter** - LLM(Anthropic, OpenAI), Image(Replicate, DALL-E) 등 교체 가능

---

## 빠른 시작

### 설치

```bash
git clone https://github.com/your-username/ai-assistant-framework.git
cd ai-assistant-framework
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .env 파일 편집하여 API 키 추가
```

### 실행

```bash
# 가상환경 활성화
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 서버 실행 (핫 리로드 포함)
uvicorn app.main:app --reload
```

- 서버: http://localhost:8000
- API 문서: http://localhost:8000/docs
- 종료: Ctrl+C

---

## 프레임워크 아키텍처

### 계층 구조

```
API Routes → Services → Workflow → Nodes → Adapters → External APIs
             ↓
          Entities
```

### Port-Adapter Pattern

**Core의 역할:**
- Port 인터페이스 정의 (ILLMPort, IImagePort)
- Adapter 구현체 제공 (교체 가능)
- Application은 Port만 의존

**Pure Adapter 원칙:**
```python
# ❌ Bad: Adapter에 비즈니스 로직
class BadAdapter(ILLMPort):
    async def generate_recipe(self, query: str):
        # 프롬프트 선택 - 비즈니스 로직! (X)
        prompt = self.select_prompt(query)
        return self.llm.invoke(prompt)

# ✅ Good: Adapter는 API 호출만
class GoodAdapter(ILLMPort):
    async def generate_recipe(self, prompt: str):
        # 렌더링된 프롬프트를 받아 API만 호출
        return self.llm.invoke(prompt)
```

### 의존성 주입

데코레이터 기반 DI 사용:

```python
from app.core.decorators import singleton, inject

@singleton
class RecipeGeneratorNode(BaseNode):
    @inject
    def __init__(self, llm_port: ILLMPort, prompt_loader: PromptLoader):
        self.llm_port = llm_port
        self.prompt_loader = prompt_loader

    async def execute(self, state):
        # 비즈니스 로직: 프롬프트 선택
        prompt_id = "cooking.generate_recipe_single"

        # 비즈니스 로직: 프롬프트 렌더링
        prompt = self.prompt_loader.render(prompt_id, query=state["user_query"])

        # Adapter: 순수 API 호출만
        recipe = await self.llm_port.generate_recipe(prompt)
        return recipe
```

Port-Adapter 바인딩 (Application Module):

```python
# app/cooking_assistant/module.py
class CookingModule(Module):
    @provider
    def provide_llm_adapter(self, settings: Settings) -> ILLMPort:
        return AnthropicLLMAdapter(settings)  # 교체 가능
```

---

## 프로젝트 구조

```
app/
├── core/                            # 🔧 프레임워크 Core (재사용 가능)
│   ├── config.py                   # 설정 관리 (범용)
│   ├── auth.py                     # JWT 인증 (범용)
│   ├── prompt_loader.py            # 프롬프트 시스템 (범용)
│   ├── decorators.py               # DI 데코레이터 (범용)
│   ├── dependencies.py             # FastAPI Dependencies (범용)
│   ├── ports/                      # Port 인터페이스
│   │   ├── llm_port.py            # ILLMPort (범용 인터페이스)
│   │   └── image_port.py          # IImagePort (범용 인터페이스)
│   └── adapters/                   # Adapter 구현체
│       ├── llm/
│       │   └── anthropic_adapter.py
│       └── image/
│           └── replicate_adapter.py
│
├── cooking_assistant/               # 📦 Application Template (도메인 특화)
│   ├── module.py                   # DI 바인딩 (템플릿별)
│   ├── entities/                   # 도메인 엔티티
│   │   ├── recipe.py
│   │   ├── recommendation.py
│   │   └── question.py
│   ├── models/                     # DTO & Response 모델
│   │   ├── schemas.py
│   │   └── response_codes.py
│   ├── services/                   # 비즈니스 로직 서비스
│   │   └── cooking_service.py
│   ├── workflow/                   # LangGraph Workflow
│   │   ├── cooking_workflow.py
│   │   ├── states/
│   │   │   └── cooking_state.py
│   │   ├── nodes/                  # Workflow Nodes
│   │   │   ├── base_node.py
│   │   │   ├── intent_classifier_node.py
│   │   │   ├── recipe_generator_node.py
│   │   │   ├── recommender_node.py
│   │   │   ├── question_answerer_node.py
│   │   │   └── image_generator_node.py
│   │   └── edges/                  # Workflow Edges
│   │       └── intent_router.py
│   ├── api/                        # API Routes
│   │   └── routes.py
│   ├── prompts/                    # 프롬프트 템플릿
│   │   └── cooking.yaml
│   └── exceptions.py               # 도메인 예외
│
└── main.py                          # FastAPI 앱 진입점
```

### 구조 설명

**Core (프레임워크):**
- 모든 Application에서 재사용 가능
- 도메인 무관, 순수 기술 인프라
- Port 인터페이스 정의
- Adapter 구현체 제공

**Application Template (cooking_assistant):**
- 특정 도메인 비즈니스 로직
- Core의 Port를 활용
- 템플릿별로 독립적

---

## 설계 원칙

### 1. Port-Adapter Pattern

**Port (인터페이스):**
```python
# app/core/ports/llm_port.py
class ILLMPort(ABC):
    @abstractmethod
    async def classify_intent(self, prompt: str) -> Dict[str, Any]:
        """렌더링된 프롬프트를 받아 LLM API 호출"""
        pass
```

**Adapter (구현체):**
```python
# app/core/adapters/llm/anthropic_adapter.py
@singleton
class AnthropicLLMAdapter(ILLMPort):
    async def classify_intent(self, prompt: str) -> Dict[str, Any]:
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return json.loads(self._extract_json(response.content))
```

**교체 가능:**
```python
# OpenAI로 교체
class OpenAIAdapter(ILLMPort):
    async def classify_intent(self, prompt: str) -> Dict[str, Any]:
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return json.loads(response.choices[0].message.content)
```

### 2. Pure Adapter 원칙

**Adapter의 책임:**
- ✅ API 호출
- ✅ 결과 파싱 (JSON → Dict)
- ❌ 프롬프트 선택 (비즈니스 로직)
- ❌ 프롬프트 렌더링 (비즈니스 로직)
- ❌ 엔티티 변환 (비즈니스 로직)

**호출자(Node, Service)의 책임:**
- ✅ 프롬프트 선택
- ✅ 프롬프트 렌더링
- ✅ 엔티티 변환 및 검증

### 3. 레이어별 책임

**API Layer (Routes):**
- HTTP 요청/응답 처리
- 인증 확인
- Service 호출

**Service Layer:**
- 비즈니스 로직 조합
- Workflow 실행
- Entity → DTO 변환

**Workflow Layer:**
- 노드 실행 순서 정의
- State 관리

**Node Layer:**
- 프롬프트 선택 및 렌더링
- Port를 통한 외부 API 호출
- 결과를 Entity로 변환

**Adapter Layer:**
- 순수 API 호출 및 파싱만

---

## Secondary Intent 처리

이 프레임워크는 **복합 의도 처리**를 지원합니다.

### 예시
```
사용자 쿼리: "매운 음식 추천해주고, 김치찌개 레시피도 알려줘"

분류 결과:
- primary_intent: "recommend"
- secondary_intents: ["recipe_create"]

워크플로우 실행 순서:
1. Recommender Node (primary) → 추천 목록 생성
2. Recipe Generator Node (secondary) → 레시피 생성

최종 응답:
{
  "code": "RECOMMENDATION_SUCCESS",
  "data": {
    "recommendations": [...],
    "secondary_results": [
      {
        "intent": "recipe_create",
        "recipe": {...}
      }
    ]
  }
}
```

### 구현 방식

**1. BaseNode에서 자동 처리:**
```python
# app/cooking_assistant/workflow/nodes/base_node.py
class BaseNode(ABC):
    def _handle_secondary_intent(self, state: CookingState):
        if secondary_intents and secondary_intents[0] == self.intent_name:
            processed_intent = secondary_intents.pop(0)
            state["processed_secondary_intents"].append(processed_intent)
```

**2. Service에서 결과 수집:**
```python
# app/cooking_assistant/services/cooking_service.py
def _to_dto(self, state: CookingState):
    # Primary intent 응답 생성
    response = self._create_response_by_intent(state["primary_intent"], state)

    # Secondary intents 결과 수집
    secondary_results = self._collect_secondary_results(state)

    # 응답에 추가
    response.data.secondary_results = secondary_results
    return response
```

---

## 기술 스택

- **Web Framework:** FastAPI
- **Workflow Engine:** LangGraph
- **AI/LLM:** Anthropic Claude Sonnet 4.5
- **Image Generation:** Replicate Flux Schnell
- **Authentication:** JWT (python-jose)
- **Dependency Injection:** injector
- **Prompt Management:** YAML + Jinja2
- **Configuration:** pydantic-settings

---

## 예제: Cooking Assistant 템플릿

이 레포지토리는 첫 번째 템플릿인 **한국어 요리 AI 어시스턴트** 예제를 포함합니다.

### 기능
- **레시피 생성** - 조리법과 이미지 자동 생성
- **음식 추천** - 맞춤형 메뉴 제안
- **요리 Q&A** - 요리 관련 질문 답변
- **복합 의도 처리** - 하나의 쿼리로 여러 작업 수행
- **한국어 네이티브 지원**

### API 사용 예제

**레시피 생성:**
```bash
curl -X POST http://localhost:8000/api/cooking \
  -H "Content-Type: application/json" \
  -d '{"query": "김치찌개 만드는 법"}'
```

**음식 추천:**
```bash
curl -X POST http://localhost:8000/api/cooking \
  -H "Content-Type: application/json" \
  -d '{"query": "매운 음식 추천해줘"}'
```

**복합 의도:**
```bash
curl -X POST http://localhost:8000/api/cooking \
  -H "Content-Type: application/json" \
  -d '{"query": "매운 음식 추천해주고, 김치찌개 레시피도 알려줘"}'
```

**인증 사용:**
```bash
# 토큰 생성
python3 scripts/generate_token.py user123

# 인증된 요청
curl -X POST http://localhost:8000/api/cooking \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"query": "김치찌개 만드는 법"}'
```

---

## 새로운 Application 만들기

### 1. Application 패키지 생성

```bash
mkdir -p app/my_app/{entities,models,services,workflow/{nodes,edges,states},api,prompts}
```

### 2. Module 정의

```python
# app/my_app/module.py
from injector import Module, singleton, provider
from app.core.ports.llm_port import ILLMPort
from app.core.adapters.llm.anthropic_adapter import AnthropicLLMAdapter

class MyAppModule(Module):
    @singleton
    @provider
    def provide_llm_adapter(self, settings: Settings) -> ILLMPort:
        return AnthropicLLMAdapter(settings)
```

### 3. Dependencies 수정

```python
# app/core/dependencies.py
from app.my_app.module import MyAppModule

def get_injector() -> Injector:
    if _injector is None:
        _injector = Injector([MyAppModule()])  # 변경
    return _injector
```

### 4. Entity, Service, Workflow 구현

기존 `cooking_assistant` 패키지를 참고하여 구현

---

## Adapter 교체하기

### LLM Adapter 교체 (Anthropic → OpenAI)

**1. OpenAI Adapter 구현:**
```python
# app/core/adapters/llm/openai_adapter.py
@singleton
class OpenAIAdapter(ILLMPort):
    @inject
    def __init__(self, settings: Settings):
        self.client = OpenAI(api_key=settings.openai_api_key)

    async def classify_intent(self, prompt: str) -> Dict[str, Any]:
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
```

**2. Module에서 바인딩 변경:**
```python
# app/cooking_assistant/module.py
from app.core.adapters.llm.openai_adapter import OpenAIAdapter

class CookingModule(Module):
    @provider
    def provide_llm_adapter(self, settings: Settings) -> ILLMPort:
        return OpenAIAdapter(settings)  # 변경!
```

**3. Config 수정:**
```python
# app/core/config.py
class Settings(BaseSettings):
    openai_api_key: str  # 추가
```

완료! Application 코드는 전혀 수정할 필요 없음.

---

## 환경 변수

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
REPLICATE_API_TOKEN=r8_...
SECRET_KEY=your-secret-key-here

# LLM 설정
LLM_MODEL=claude-sonnet-4-5-20250929
LLM_TIMEOUT=90
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096

# 이미지 생성 설정
IMAGE_MODEL=black-forest-labs/flux-schnell
IMAGE_RETRIES=2

# 앱 설정
APP_TITLE=AI Assistant API
APP_VERSION=2.0.0
LOG_LEVEL=INFO
```

---

## 향후 계획

### Application Templates
- **chatbot** - 대화형 챗봇 (대화 히스토리 관리)
- **rag-qa** - RAG 기반 문서 Q&A (Vector DB 연동)
- **multimodal** - 멀티모달 AI (이미지 + 텍스트)

### Framework 개선
- CLI 도구 (프로젝트 스캐폴딩)
- 테스트 유틸리티
- 추가 Adapter (OpenAI, Google Gemini, DALL-E 등)

---

## 라이선스

MIT License
