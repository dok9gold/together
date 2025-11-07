# PyAi 아키텍처 프로젝트 요약

## 📋 문서 개요

이 프로젝트는 **PyAi (FastAPI + LangGraph 기반 한국어 요리 AI 어시스턴트)**를 헥사고날 아키텍처로 리팩토링하고, 이를 범용 프레임워크로 발전시키는 계획을 담고 있습니다.

- **tobe.md**: 리팩토링 상세 계획 (~2800줄)
- **framework.md**: 프레임워크화 전략

---

## 🎯 핵심 목표

### 1️⃣ 현재 문제점
- **강한 결합**: 비즈니스 로직과 외부 API(Anthropic, Replicate)가 직접 결합
- **설정 분산**: 환경 변수가 여러 파일에 분산
- **테스트 어려움**: 외부 API 모킹 불가능
- **레이어 혼재**: 도메인/인프라/프레젠테이션 경계 모호

### 2️⃣ 해결 방안
```
┌─────────────────────────┐
│   Presentation Layer    │  ← FastAPI (routes.py)
├─────────────────────────┤
│   Application Layer     │  ← Use Cases, LangGraph Workflow
├─────────────────────────┤
│      Domain Layer       │  ← Business Logic, Ports (인터페이스)
├─────────────────────────┤
│     Adapter Layer       │  ← Anthropic/Replicate/DB 구현체
└─────────────────────────┘
```

---

## 🔑 핵심 개념

### ⚠️ 헥사고날 아키텍처 적용 범위 (중요!)

**Port/Adapter는 외부 시스템 경계에만 적용합니다.**

#### ✅ Port/Adapter 사용
- **외부 API**: Anthropic, OpenAI, Replicate
- **데이터베이스**: PostgreSQL, MongoDB
- **파일 시스템**: S3, Local Storage
- **캐시**: Redis, Memcached

#### ❌ 일반 클래스 사용
- **검증 로직**: RecipeValidator
- **계산 로직**: NutritionCalculator
- **포매팅**: RecipeFormatter
- **내부 헬퍼**: 도메인 내부 유틸

#### 판단 기준 (4단계 체크리스트)
```
1. 외부 시스템 의존인가? → No면 일반 클래스
2. 교체 가능성이 있는가? → No면 재고민
3. 테스트 시 모킹 필요한가? → No면 재고민
4. 네트워크/IO 경계를 넘는가? → Yes면 Port/Adapter
```

---

## 🏗️ 아키텍처 구성 요소

### 1. Port (인터페이스)
```python
# domain/ports/llm_port.py
class ILLMPort(ABC):
    @abstractmethod
    async def classify_intent(self, query: str) -> Dict[str, Any]:
        pass
```
- 도메인이 외부에 원하는 기능을 **추상적으로 정의**
- 구현 없음, 순수 인터페이스

### 2. Adapter (구현체)
```python
# adapters/llm/anthropic_adapter.py
class AnthropicLLMAdapter(ILLMPort):
    async def classify_intent(self, query: str) -> Dict[str, Any]:
        # Anthropic API 호출 + 응답 변환
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return json.loads(response.content)
```
- Port 인터페이스를 외부 시스템에 맞게 구현
- **교체 가능**: Anthropic → OpenAI로 변경 시 Adapter만 교체

### 3. Domain Service (비즈니스 로직)
```python
# domain/services/cooking_assistant.py
class CookingAssistantService:
    def __init__(self, llm_port: ILLMPort, image_port: IImagePort):
        self.llm_port = llm_port  # 구체적 구현 몰라도 됨
        self.image_port = image_port
        self.validator = RecipeValidator()  # 내부는 직접 생성

    async def classify_intent(self, state: CookingState):
        result = await self.llm_port.classify_intent(state["user_query"])
        # 비즈니스 규칙 적용
        return state
```
- Port에만 의존, 외부 시스템 몰라도 됨
- 테스트 시 Port 모킹

### 4. DI Container
```python
# core/container.py
class Container(containers.DeclarativeContainer):
    config = providers.Singleton(get_settings)

    llm_adapter = providers.Singleton(
        AnthropicLLMAdapter,
        settings=config
    )

    cooking_assistant = providers.Singleton(
        CookingAssistantService,
        llm_port=llm_adapter,  # 자동 주입
        image_port=image_adapter
    )
```
- Spring의 ApplicationContext 역할
- 의존성 자동 주입

---

## 🔄 LangGraph 워크플로우 설계

### 원칙
```
┌─────────────────────────────────────────┐
│  1. 노드는 Domain Service 호출하는 얇은 래퍼  │
│  2. 엣지는 순수 라우팅 로직만                 │
│  3. 워크플로우는 Application Layer에 위치    │
│  4. 비즈니스 로직은 Domain에 위임            │
└─────────────────────────────────────────┘
```

### 구현 예시
```python
# application/workflow/nodes/recipe_generator_node.py
class RecipeGeneratorNode:
    def __init__(self, cooking_assistant: CookingAssistantService):
        self.cooking_assistant = cooking_assistant

    async def __call__(self, state: CookingState) -> CookingState:
        logger.info("[Node:RecipeGenerator] 시작")
        # ✅ Domain Service에 위임
        result = await self.cooking_assistant.generate_recipe(state)
        logger.info("[Node:RecipeGenerator] 완료")
        return result

# application/workflow/edges/intent_router.py
def route_by_intent(state: CookingState) -> str:
    intent = state.get("primary_intent", "recipe_create")
    routing_map = {
        "recipe_create": "recipe_generator",
        "recommend": "recommender",
        "question": "question_answerer"
    }
    return routing_map.get(intent, "recipe_generator")
```

---

## 📝 프롬프트 관리 (MyBatis 스타일)

### 문제점
```python
# ❌ 기존: 프롬프트가 코드에 하드코딩
prompt = f"""당신은 요리 AI 어시스턴트입니다.
사용자 입력: {query}
..."""
```
→ 수정 시 재배포 필요, 버전 관리 어려움, A/B 테스트 불가

### 해결책: Jinja2 + YAML
```jinja2
{# prompts/intent_classification.j2 #}
당신은 요리 AI 어시스턴트의 의도 분류 전문가입니다.

## 분류 기준
{% for intent_type, description in intent_types.items() %}
{{ loop.index }}. **{{ intent_type }}**: {{ description }}
{% endfor %}

## 현재 사용자 입력
입력: "{{ query }}"
```

```yaml
# prompts/config.yaml
intent_classification:
  template: intent_classification.j2
  version: "1.0"
  model: claude-sonnet-4-5-20250929
  temperature: 0.7

  variables:
    intent_types:
      recipe_create: "특정 요리의 구체적인 조리법 요구"
      recommend: "여러 음식 중 선택지 요구"
```

```python
# 사용
loader = PromptLoader("prompts/")
prompt = loader.render("intent_classification", query="김치찌개 만들기")
```

**장점**: 프롬프트 분리, 버전 관리, A/B 테스트, 다국어 지원

---

## 🚀 프레임워크화 가능성

### 왜 프레임워크로 만들 수 있나?

현재 tobe.md의 패턴들은 **AI Agent 애플리케이션 전용 프레임워크**로 발전 가능:

```
✅ Hexagonal Architecture (Port/Adapter) - AI 서비스 연동용
✅ DI Container 설계 - dependency-injector 기반
✅ LangGraph Workflow 추상화 - Node/Edge 패턴
✅ Prompt Management System - Jinja2 + YAML
✅ Settings Management - Pydantic 기반
```

### 프레임워크 사용 예시
```python
# main.py - 프레임워크 사용자가 작성
from pyai import PyAIApp, BaseNode, State

# 1. 앱 초기화
app = PyAIApp.from_settings("config/settings.yaml")

# 2. 도메인 로직만 작성
class RecipeGenerator(BaseNode):
    async def process(self, state: State) -> State:
        prompt = self.prompts.render("recipe", query=state["query"])
        result = await self.llm.generate(prompt)
        state["recipe"] = result
        return state

# 3. 워크플로우 구성 (선언적)
workflow = app.create_workflow()
workflow.add_node("classify", IntentClassifier)
workflow.add_node("recipe", RecipeGenerator)
workflow.add_edge("classify", "recipe", condition=lambda s: s["intent"] == "recipe")

# 4. FastAPI 통합 (자동)
api = app.create_api(workflow)
```

```bash
# CLI로 프로젝트 생성
$ pyai create my-cooking-bot --template=chatbot
$ cd my-cooking-bot
$ pyai generate adapter --type=llm --name=CustomLLM
$ pyai validate-prompts
$ pyai run --reload
```

### 핵심 가치 제안

| 특징 | 설명 | 기존 대안 |
|------|------|-----------|
| **AI Agent 특화** | LangGraph + LLM 통합 최적화 | LangChain (범용), CrewAI (에이전트만) |
| **Hexagonal by Default** | 외부 시스템 Port/Adapter 강제 | 직접 구현 필요 |
| **프롬프트 1급 객체** | MyBatis처럼 프롬프트 분리 관리 | 코드에 하드코딩 |
| **DI 기본 내장** | Spring 스타일 의존성 주입 | FastAPI Depends (수동) |
| **테스트 친화적** | Mock Adapter 자동 생성 | 매번 직접 작성 |
| **멀티 LLM 지원** | Anthropic/OpenAI/Ollama 즉시 교체 | 각각 다른 SDK |

### 기존 프레임워크와 차별화

```
LangChain: 범용 LLM 앱 (너무 방대함)
CrewAI: 멀티 에이전트 협업 특화
Haystack: 검색 증강 특화
Semantic Kernel: MS 생태계 종속

→ PyAI Framework: FastAPI + LangGraph 기반
   한국어 AI 서비스 빠른 구축에 최적화
```

---

## 📅 마이그레이션 로드맵

### Phase 1: 설정 중앙화 (1주)
- `app/core/config.py` 생성 (Pydantic BaseSettings)
- 환경 변수 중앙 관리
- 기존 서비스에 Settings 주입

### Phase 2: Port/Adapter 분리 (2주)
- `domain/ports/llm_port.py`, `image_port.py` 생성
- `adapters/llm/anthropic_adapter.py` 구현
- `adapters/image/replicate_adapter.py` 구현

### Phase 3: DI Container 구축 (1주)
- `core/container.py` 생성
- 모든 의존성 컨테이너 등록
- FastAPI Depends 통합

### Phase 4: LangGraph 리팩토링 (2주)
- `application/workflow/` 디렉토리 생성
- 노드/엣지 분리
- Domain Service 호출 구조로 변경

### Phase 5: 프롬프트 분리 (1주)
- `adapters/llm/prompts/` 생성
- Jinja2 템플릿 작성
- PromptLoader 구현

### Phase 6-9: 테스트/문서화/최적화/프레임워크화 (4주)

---

## 📦 프레임워크 개발 로드맵

### Phase 1: Core 추출 (2-3주)
- PyAi에서 범용 부분 분리
- BasePort, BaseAdapter, BaseNode 추상화
- PromptLoader 독립 모듈화

### Phase 2: Adapter 라이브러리 (1-2주)
- Anthropic/OpenAI/Ollama LLM Adapter
- Replicate/DALLE Image Adapter
- Chroma/Pinecone VectorDB Adapter

### Phase 3: CLI 도구 (1주)
- 프로젝트 스캐폴딩
- Adapter 코드 생성기
- 프롬프트 검증 도구

### Phase 4: 문서화 & 배포 (1주)
- PyPI 배포 (pip install pyai)
- 튜토리얼 및 예제
- API 문서 (Sphinx)

---

## 🎓 핵심 원칙 요약

```
┌──────────────────────────────────────────────────────┐
│  헥사고날 아키텍처의 황금률                                 │
│  ════════════════════════════════════════════════════ │
│                                                       │
│  1. Port/Adapter는 외부 경계에만 적용한다                  │
│     → 네트워크, DB, 파일시스템, 외부 API                   │
│                                                       │
│  2. 도메인 내부는 일반적인 객체지향 설계를 따른다            │
│     → 일반 클래스, DI, 단순한 메서드 호출                   │
│                                                       │
│  3. "교체 가능성"과 "테스트 필요성"이 진짜 있는지 확인       │
│     → YAGNI 원칙 준수                                     │
│                                                       │
│  4. 과도한 추상화는 독이다                                 │
│     → 필요한 곳에만 적용                                   │
│                                                       │
└──────────────────────────────────────────────────────┘
```

```
┌──────────────────────────────────────────────────────┐
│  LangGraph 워크플로우 설계 원칙                           │
│  ════════════════════════════════════════════════════ │
│                                                       │
│  1. 노드는 Domain Service를 호출하는 얇은 래퍼         │
│     → 비즈니스 로직은 Domain에 위임                    │
│                                                       │
│  2. 엣지는 순수 라우팅 로직만 포함                     │
│     → 상태 기반 조건 분기                             │
│                                                       │
│  3. 워크플로우는 Application Layer에 위치             │
│     → Domain과 Presentation 중간에서 조율              │
│                                                       │
│  4. 노드/엣지는 테스트 불필요 (얇은 래퍼이므로)         │
│     → Domain Service만 단위 테스트                    │
│                                                       │
└──────────────────────────────────────────────────────┘
```

---

## 🎯 결론

**tobe.md**는 단순한 리팩토링 계획이 아니라, **실제 프로덕션에서 검증된 AI 애플리케이션 아키텍처 패턴**을 담고 있습니다.

### 즉시 적용 가능
- 지금 당장 다른 AI 프로젝트에 패턴 복사 사용 가능
- 2-3개 프로젝트에서 검증 후 프레임워크로 추출

### 타겟 시장
1. **국내 시장**: 한국어 AI 서비스 개발자용
2. **FastAPI + LangGraph** 황금 조합
3. **Spring 경험자 친화적** (DI, Port/Adapter)
4. **프롬프트 엔지니어링 생산성** (MyBatis 스타일)

### 다음 단계
- **현재**: PyAi 리팩토링 (Phase 1-9)
- **미래**: PyAI Framework 개발 (오픈소스)
- **최종**: pip install pyai로 AI Agent 앱 5분 만에 구축

---

## 📚 참고 문서
- **tobe.md**: 상세 리팩토링 계획 (~2800줄)
- **framework.md**: 프레임워크화 전략
- **CLAUDE.md**: 프로젝트 개요 및 명령어
