# PyAI Framework - AI Agent 애플리케이션 통합 프레임워크

> **비전**: FastAPI + LangGraph 기반 AI Agent 애플리케이션을 5분 안에 구축할 수 있는 통합 프레임워크

---

## 📋 목차

1. [프레임워크 개요](#프레임워크-개요)
2. [핵심 아키텍처](#핵심-아키텍처)
3. [계층별 상세 설계](#계층별-상세-설계)
4. [설정 기반 개발](#설정-기반-개발)
5. [확장 포인트](#확장-포인트)
6. [프레임워크 사용 시나리오](#프레임워크-사용-시나리오)
7. [기존 프레임워크 비교](#기존-프레임워크-비교)

---

## 프레임워크 개요

### 왜 PyAI Framework인가?

**문제점**: AI Agent 애플리케이션 개발 시 반복적인 보일러플레이트 코드
- LLM API 연동 (Anthropic, OpenAI, Ollama 등)
- 프롬프트 관리 (버전, A/B 테스트, 다국어)
- 워크플로우 오케스트레이션 (LangGraph)
- 인증/권한 관리
- 응답 변환 및 에러 핸들링
- 테스트 및 모킹

**해결책**: 검증된 패턴을 프레임워크로 추상화
```
PyAI Framework = FastAPI + LangGraph + Hexagonal Architecture + DI Container + Prompt Management
```

### 핵심 가치 제안

| 항목 | PyAI Framework | 직접 구현 |
|-----|---------------|----------|
| **프로젝트 시작** | 5분 (CLI 스캐폴딩) | 1-2일 (보일러플레이트) |
| **LLM 교체** | 설정 변경만 | 코드 전체 수정 |
| **프롬프트 관리** | YAML + Jinja2 (즉시 반영) | 코드 하드코딩 (재배포) |
| **테스트** | Mock Adapter 자동 생성 | 매번 수동 작성 |
| **아키텍처** | Hexagonal 강제 | 자유 방임 (기술 부채) |

### 타겟 사용자

1. **AI 서비스 스타트업**: 빠른 MVP 구축
2. **Spring 백엔드 개발자**: 익숙한 DI/Port-Adapter 패턴
3. **LangChain 사용자**: 더 구조화된 대안 원하는 경우
4. **한국 시장**: 한국어 프롬프트 관리 최적화

---

## 핵심 아키텍처

### 전체 구조 (Layered + Hexagonal)

```
┌────────────────────────────────────────────────────────────┐
│                    Presentation Layer                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  FastAPI Routes (자동 생성)                           │  │
│  │  - REST API 엔드포인트                                 │  │
│  │  - WebSocket 지원                                     │  │
│  │  - 인증/권한 Middleware                               │  │
│  │  - Request/Response DTO 자동 변환                     │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────┐
│                   Application Layer                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Use Cases (비즈니스 시나리오)                          │  │
│  │  - 워크플로우 실행                                      │  │
│  │  - Domain → DTO 변환                                   │  │
│  │  - 트랜잭션 관리                                        │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  LangGraph Workflows (오케스트레이션)                  │  │
│  │  - 노드 실행 순서 정의                                  │  │
│  │  - 조건부 분기 (Edge Routing)                          │  │
│  │  - 상태 관리 (State)                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────┐
│                      Domain Layer                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Domain Services (핵심 비즈니스 로직)                   │  │
│  │  - 의도 분류, 레시피 생성 등                            │  │
│  │  - Port 인터페이스에만 의존                             │  │
│  │  - 외부 시스템 몰라도 됨                                │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Entities (도메인 모델)                                │  │
│  │  - CookingState, Recipe, User 등                      │  │
│  │  - 비즈니스 규칙 포함                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Ports (인터페이스 - 외부 시스템 경계)                  │  │
│  │  - ILLMPort, IVectorStorePort, IMemoryPort           │  │
│  │  - 도메인이 외부에 요구하는 기능 정의                    │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────┐
│                     Adapter Layer                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  LLM Adapters (Port 구현체)                            │  │
│  │  - AnthropicAdapter, OpenAIAdapter, OllamaAdapter    │  │
│  │  - 프롬프트 로딩 및 API 호출                            │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Vector Store Adapters                                │  │
│  │  - ChromaAdapter, PineconeAdapter, WeaviateAdapter   │  │
│  │  - 임베딩 생성 및 유사도 검색                           │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Memory Adapters                                      │  │
│  │  - PostgresMemory, RedisMemory, InMemoryAdapter      │  │
│  │  - 대화 히스토리 저장/조회                              │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Image Adapters                                       │  │
│  │  - ReplicateAdapter, DALLEAdapter, StabilityAdapter  │  │
│  │  - 이미지 생성 API 호출                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────┐
│                   Infrastructure                           │
│  - 외부 API (Anthropic, OpenAI, Replicate)                │
│  - 데이터베이스 (PostgreSQL, MongoDB)                      │
│  - 캐시 (Redis)                                            │
│  - 벡터 DB (Chroma, Pinecone)                             │
└────────────────────────────────────────────────────────────┘
```

### 횡단 관심사 (Cross-Cutting Concerns)

```
┌────────────────────────────────────────────────────────────┐
│                   Core Components                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  DI Container                                         │  │
│  │  - 모든 컴포넌트 의존성 자동 주입                       │  │
│  │  - Singleton, Transient, Scoped 라이프사이클          │  │
│  │  - Spring ApplicationContext 스타일                   │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Prompt Management System                            │  │
│  │  - Jinja2 템플릿 엔진                                  │  │
│  │  - YAML 설정 (버전, 모델, 변수)                        │  │
│  │  - A/B 테스트, 다국어 지원                             │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Configuration Management                            │  │
│  │  - YAML 중앙 설정                                      │  │
│  │  - 환경별 분리 (dev/staging/prod)                     │  │
│  │  - 시크릿 관리 (Vault 연동 가능)                       │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Authentication & Authorization                      │  │
│  │  - JWT 기반 인증 (Built-in)                           │  │
│  │  - Role-based Access Control                         │  │
│  │  - API Key 관리                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Observability                                       │  │
│  │  - 구조화된 로깅 (structlog)                          │  │
│  │  - 메트릭 (Prometheus 연동)                           │  │
│  │  - 트레이싱 (OpenTelemetry)                           │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

---

## 계층별 상세 설계

### 1. Presentation Layer (FastAPI 자동 생성)

#### 책임
- HTTP 요청/응답 처리
- 인증/권한 검증 (Dependency Injection)
- UseCase 호출만 (1줄)
- DTO 그대로 반환

#### 프레임워크 제공 기능
```yaml
# routes.yaml (선언적 라우팅)
routes:
  - path: /api/cooking
    method: POST
    use_case: CreateRecipeUseCase
    auth: required
    request_model: CookingRequest
    response_model: CookingResponse
    description: "요리 레시피 생성"

  - path: /api/health
    method: GET
    auth: public
    response:
      status: "healthy"
```

**자동 생성되는 코드**:
- FastAPI router 등록
- OpenAPI 스펙 생성
- Request 검증 (Pydantic)
- 인증 Dependency 주입
- 에러 핸들링 (표준 응답 포맷)

#### 인증 전략 (Built-in)
```yaml
# auth.yaml
authentication:
  type: jwt
  secret_key: ${SECRET_KEY}
  algorithm: HS256
  access_token_expire: 24h

  strategies:
    - name: required
      description: "토큰 필수"

    - name: optional
      description: "토큰 있으면 개인화, 없어도 통과"

    - name: public
      description: "인증 불필요"
```

---

### 2. Application Layer (UseCase + Workflow)

#### UseCase 패턴

**책임**:
- 워크플로우 실행 OR 직접 로직 구현
- Domain Entity → DTO 변환
- 트랜잭션 관리
- 에러 핸들링 전략

**복잡도별 패턴 선택**:

```
Level 1: 단순 CRUD (Workflow 불필요)
  UseCase → Repository 직접 호출

Level 2: 중간 비즈니스 로직 (Service 패턴)
  UseCase → 여러 Service 호출

Level 3: 복잡한 AI 오케스트레이션 (Workflow 필요)
  UseCase → Workflow 실행 → Domain Services
```

**프레임워크 제공 BaseUseCase**:
```python
# 개념적 구조 (실제 코드 없음)
BaseUseCase:
  - execute(request) → response
  - _to_dto(domain_entity) → DTO
  - 자동 트랜잭션 관리
  - 자동 로깅
  - 자동 메트릭 수집
```

#### Workflow 패턴 (LangGraph 기반)

**원칙**:
1. 노드는 Domain Service 호출하는 얇은 래퍼
2. 엣지는 순수 라우팅 로직만
3. 비즈니스 로직은 Domain에 위임
4. 선언적 워크플로우 정의 (YAML)

**선언적 워크플로우 정의**:
```yaml
# workflows/cooking_workflow.yaml
workflow:
  name: CookingWorkflow
  initial_node: classify_intent

  nodes:
    - name: classify_intent
      handler: IntentClassifierNode
      description: "사용자 의도 분류"

    - name: recipe_generator
      handler: RecipeGeneratorNode
      description: "레시피 생성"
      requires:
        - llm_port
        - vector_store_port

    - name: image_generator
      handler: ImageGeneratorNode
      description: "음식 이미지 생성"
      requires:
        - image_port

    - name: recommender
      handler: RecommenderNode
      description: "음식 추천"

  edges:
    - from: classify_intent
      to: route_by_intent  # 조건부 분기

    - from: recipe_generator
      to: image_generator
      condition: "state.primary_intent == 'recipe_create'"

    - from: image_generator
      to: END

  routing:
    - name: route_by_intent
      strategy: intent_based
      mapping:
        recipe_create: recipe_generator
        recommend: recommender
        question: question_answerer
```

**노드 구현 (개발자 작성)**:
```python
# 개념적 구조
class RecipeGeneratorNode(BaseNode):
    """BaseNode를 상속하여 핵심 로직만 구현"""

    def __init__(self, cooking_service: CookingAssistantService):
        self.service = cooking_service

    async def process(self, state: State) -> State:
        """Domain Service에 위임만"""
        return await self.service.generate_recipe(state)
```

**프레임워크 제공 BaseNode**:
```python
# 개념적 구조
BaseNode:
  - __call__(state) → state  # LangGraph 표준
  - process(state) → state  # 개발자 구현 필요
  - 자동 로깅 (노드 시작/종료)
  - 자동 메트릭 (실행 시간, 성공/실패)
  - 자동 에러 핸들링
```

---

### 3. Domain Layer (순수 비즈니스 로직)

#### Domain Services

**책임**:
- 핵심 비즈니스 로직
- Port 인터페이스에만 의존
- 외부 시스템 몰라도 됨
- 테스트 가능 (Port 모킹)

**프레임워크 가이드라인**:
```
✅ DO:
  - Port 인터페이스 사용
  - 비즈니스 규칙 검증
  - 도메인 지식 캡슐화

❌ DON'T:
  - Adapter 직접 참조
  - HTTP 통신
  - 데이터베이스 직접 접근
  - 프레임워크 의존성
```

#### Ports (인터페이스)

**Port 설계 원칙**:
```
외부 시스템 경계에만 적용:
  ✅ LLM API (ILLMPort)
  ✅ 벡터 DB (IVectorStorePort)
  ✅ 데이터베이스 (IRepository)
  ✅ 외부 API (IImagePort)

내부 로직은 일반 클래스:
  ❌ RecipeValidator
  ❌ NutritionCalculator
  ❌ RecipeFormatter
```

**프레임워크 제공 Base Ports**:
```python
# 개념적 구조
ILLMPort (추상 클래스):
  - generate(prompt, config) → response
  - stream(prompt, config) → async_iterator
  - embed(text) → vector

IVectorStorePort:
  - search(query, top_k) → documents
  - add_documents(docs) → None
  - delete(filter) → count

IMemoryPort:
  - get_history(session_id, limit) → messages
  - save_message(session_id, message) → None
  - clear(session_id) → None
```

#### Entities (도메인 모델)

**설계 원칙**:
- 비즈니스 규칙 포함 (메서드)
- Immutable 우선 (dataclass frozen=True)
- 검증 로직 포함

**프레임워크 제공 Base Entity**:
```python
# 개념적 구조
BaseEntity:
  - 자동 직렬화/역직렬화 (to_dict, from_dict)
  - 검증 (validate)
  - 이벤트 발행 (publish_event)
```

---

### 4. Adapter Layer (외부 시스템 연결)

#### Adapter 설계 원칙

**책임**:
- Port 인터페이스 구현
- 외부 API 호출
- 프롬프트 로딩 (Prompt Management 연동)
- 응답 파싱 및 변환
- 재시도 및 에러 핸들링

**비즈니스 로직 금지**:
```
❌ Adapter에서 하지 말아야 할 것:
  - if confidence < 0.5: use_default()
  - 비즈니스 규칙 검증
  - 상태 관리
  - 복잡한 로직

✅ Adapter에서 해야 할 것:
  - HTTP 통신
  - 프롬프트 템플릿 로딩
  - JSON 파싱
  - 에러 변환 (외부 에러 → 도메인 에러)
```

#### 프레임워크 제공 Base Adapters

**LLM Adapter**:
```python
# 개념적 구조
BaseLLMAdapter(ILLMPort):
  - prompt_loader: PromptLoader  # 자동 주입
  - client: Any  # Anthropic, OpenAI 등
  - config: LLMConfig  # 설정 자동 로딩

  def generate(self, prompt_name: str, **variables):
    # 1. 프롬프트 로딩 (YAML + Jinja2)
    prompt = self.prompt_loader.render(prompt_name, **variables)

    # 2. API 호출 (재시도 로직 내장)
    response = await self._call_api(prompt)

    # 3. 응답 파싱
    return self._parse_response(response)
```

**VectorStore Adapter**:
```python
# 개념적 구조
BaseVectorStoreAdapter(IVectorStorePort):
  - client: Any  # Chroma, Pinecone 등
  - config: VectorStoreConfig

  # 공통 기능:
  - 자동 임베딩 생성
  - 배치 처리
  - 캐싱
```

#### 플러그인 시스템

**내장 Adapters**:
```
LLM:
  - AnthropicAdapter (Claude 전용)
  - OpenAIAdapter (GPT 전용)
  - OllamaAdapter (로컬 LLM)

VectorStore:
  - ChromaAdapter
  - PineconeAdapter
  - WeaviateAdapter

Memory:
  - PostgresMemoryAdapter
  - RedisMemoryAdapter
  - InMemoryAdapter (테스트용)

Image:
  - ReplicateAdapter
  - DALLEAdapter
  - StabilityAdapter
```

**커스텀 Adapter 생성**:
```bash
# CLI로 Adapter 스캐폴딩
$ pyai generate adapter --type=llm --name=CustomLLM

# 생성되는 파일:
adapters/llm/custom_llm_adapter.py
tests/adapters/test_custom_llm_adapter.py
```

---

## 설정 기반 개발

### 철학: "코드 최소화, 설정 최대화"

```
전통적 방식: 코드로 모든 것 정의
  → 변경 시 재배포 필요
  → A/B 테스트 어려움
  → 환경별 분리 복잡

PyAI 방식: YAML로 설정 정의
  → 설정 변경만으로 동작 변경
  → A/B 테스트 즉시 가능
  → 환경별 설정 파일 분리
```

### 1. 프로젝트 구조

```
my-cooking-bot/
├── config/
│   ├── settings.yaml           # 메인 설정
│   ├── settings.dev.yaml       # 개발 환경
│   ├── settings.prod.yaml      # 프로덕션
│   ├── auth.yaml               # 인증 설정
│   └── workflows/
│       └── cooking_workflow.yaml
│
├── prompts/
│   ├── config.yaml             # 프롬프트 설정
│   ├── intent_classification.j2
│   ├── recipe_generation.j2
│   └── locales/
│       ├── ko/                 # 한국어
│       └── en/                 # 영어
│
├── app/
│   ├── domain/
│   │   ├── services/
│   │   ├── entities/
│   │   └── ports/
│   ├── adapters/
│   │   ├── llm/
│   │   ├── vector_store/
│   │   └── memory/
│   └── workflows/
│       └── nodes/
│
└── main.py                     # 프레임워크 초기화만
```

### 2. 메인 설정 (config/settings.yaml)

```yaml
# ========== 애플리케이션 정보 ==========
application:
  name: cooking-assistant
  version: "1.0.0"
  description: "한국어 요리 AI 어시스턴트"

# ========== 서버 설정 ==========
server:
  host: 0.0.0.0
  port: 8000
  reload: true
  workers: 4

# ========== LLM 설정 ==========
llm:
  provider: anthropic  # anthropic, openai, ollama
  config:
    model: claude-sonnet-4-5-20250929
    api_key: ${ANTHROPIC_API_KEY}
    temperature: 0.7
    max_tokens: 4096
    timeout: 90s
    retry:
      max_attempts: 3
      backoff_factor: 2

# ========== 벡터 DB 설정 (RAG) ==========
vector_store:
  provider: chroma  # chroma, pinecone, weaviate
  config:
    collection_name: recipes
    persist_directory: ./data/chroma
    embedding_model: all-MiniLM-L6-v2

# ========== 메모리 설정 ==========
memory:
  provider: postgres  # postgres, redis, in_memory
  config:
    database_url: ${DATABASE_URL}
    table_name: conversation_history
    ttl: 7d  # 대화 보관 기간

# ========== 이미지 생성 설정 ==========
image:
  provider: replicate  # replicate, dalle, stability
  config:
    api_token: ${REPLICATE_API_TOKEN}
    model: black-forest-labs/flux-schnell
    default_width: 1024
    default_height: 1024

# ========== 프롬프트 설정 ==========
prompts:
  base_path: ./prompts
  locale: ko  # 기본 언어
  cache: true
  reload_on_change: true  # 개발 시 자동 리로드

# ========== 워크플로우 설정 ==========
workflows:
  - name: cooking_workflow
    config_path: ./config/workflows/cooking_workflow.yaml
    enabled: true

# ========== 인증 설정 ==========
authentication:
  enabled: true
  config_path: ./config/auth.yaml

# ========== 로깅 설정 ==========
logging:
  level: INFO
  format: json
  handlers:
    - console
    - file:
        path: ./logs/app.log
        rotation: daily
        retention: 30d

# ========== 모니터링 설정 ==========
monitoring:
  metrics:
    enabled: true
    port: 9090
    provider: prometheus

  tracing:
    enabled: true
    provider: opentelemetry
    endpoint: http://localhost:4318

# ========== 캐싱 설정 ==========
cache:
  enabled: true
  provider: redis  # redis, in_memory
  config:
    url: ${REDIS_URL}
    ttl: 1h
```

### 3. 프롬프트 설정 (prompts/config.yaml)

```yaml
# ========== 프롬프트 버전 관리 ==========
prompts:
  intent_classification:
    template: intent_classification.j2
    version: "2.0"
    description: "사용자 의도 분류"
    model: claude-sonnet-4-5-20250929
    temperature: 0.3
    max_tokens: 512

    # A/B 테스트 설정
    ab_test:
      enabled: true
      variants:
        - name: control
          weight: 0.5
          template: intent_classification.j2
        - name: experimental
          weight: 0.5
          template: intent_classification_v2.j2

    # 변수 기본값
    variables:
      intent_types:
        recipe_create: "특정 요리의 구체적인 조리법 요구"
        recommend: "여러 음식 중 선택지 요구"
        question: "요리 관련 일반 질문"

      examples:
        - query: "김치찌개 만드는 법"
          intent: recipe_create
        - query: "매운 음식 추천해줘"
          intent: recommend

  recipe_generation:
    template: recipe_generation.j2
    version: "1.5"
    model: claude-sonnet-4-5-20250929
    temperature: 0.7
    max_tokens: 4096

    # 다국어 지원
    localization:
      enabled: true
      default_locale: ko
      fallback_locale: en

    variables:
      output_format:
        title: "레시피 제목"
        ingredients: "재료 목록 (배열)"
        steps: "조리 순서 (배열)"
        cooking_time: "조리 시간"
        difficulty: "난이도 (쉬움/보통/어려움)"
```

### 4. 프롬프트 템플릿 (prompts/intent_classification.j2)

```jinja2
당신은 한국어 요리 AI 어시스턴트의 의도 분류 전문가입니다.

## 분류 기준
{% for intent_type, description in intent_types.items() %}
{{ loop.index }}. **{{ intent_type }}**: {{ description }}
{% endfor %}

## 예시
{% for example in examples %}
- "{{ example.query }}" → {{ example.intent }}
{% endfor %}

## 현재 사용자 입력
입력: "{{ query }}"

## 응답 형식 (JSON)
{
  "primary_intent": "recipe_create|recommend|question",
  "secondary_intents": ["..."],
  "entities": {
    "dish_name": "...",
    "ingredients": [...],
    "constraints": [...]
  },
  "confidence": 0.95
}

분석을 시작하세요.
```

### 5. 환경별 설정 오버라이드

```yaml
# config/settings.dev.yaml (개발 환경)
llm:
  config:
    model: claude-3-haiku-20240307  # 빠른 모델 (비용 절감)

server:
  reload: true

logging:
  level: DEBUG

# config/settings.prod.yaml (프로덕션)
llm:
  config:
    model: claude-sonnet-4-5-20250929

server:
  reload: false
  workers: 8

logging:
  level: WARNING

monitoring:
  metrics:
    enabled: true
  tracing:
    enabled: true
```

### 6. 프레임워크 초기화 (main.py)

```python
# 개념적 코드 (실제 구현 시 더 간단)
from pyai import PyAIApp

# YAML 설정으로 앱 초기화 (환경 자동 감지)
app = PyAIApp.from_config("config/settings.yaml")

# 또는 환경 명시
app = PyAIApp.from_config("config/settings.yaml", env="prod")

# FastAPI 앱 자동 생성 (라우트, 인증, 미들웨어 포함)
fastapi_app = app.create_api()

if __name__ == "__main__":
    app.run()
```

**그게 전부입니다!** 설정만으로 전체 앱이 구동됩니다.

---

## 확장 포인트

### 1. 커스텀 Adapter 추가

```bash
# CLI로 Adapter 스캐폴딩
$ pyai generate adapter --type=llm --name=GeminiLLM

# 생성되는 파일:
app/adapters/llm/gemini_adapter.py
tests/adapters/test_gemini_adapter.py
prompts/gemini/  # Gemini 전용 프롬프트

# 설정에 추가
# config/settings.yaml
llm:
  provider: gemini
  config:
    api_key: ${GEMINI_API_KEY}
    model: gemini-pro
```

### 2. 커스텀 노드 추가

```bash
$ pyai generate node --name=NutritionAnalyzer

# 생성되는 파일:
app/workflows/nodes/nutrition_analyzer_node.py
tests/workflows/test_nutrition_analyzer_node.py

# 워크플로우에 추가
# config/workflows/cooking_workflow.yaml
nodes:
  - name: nutrition_analyzer
    handler: NutritionAnalyzerNode
    description: "영양 성분 분석"
```

### 3. 커스텀 Middleware 추가

```python
# app/middlewares/rate_limiter.py
from pyai.middleware import BaseMiddleware

class RateLimiterMiddleware(BaseMiddleware):
    async def __call__(self, request, call_next):
        # 속도 제한 로직
        return await call_next(request)

# config/settings.yaml
middlewares:
  - type: RateLimiterMiddleware
    config:
      limit: 100
      window: 1m
```

### 4. 이벤트 핸들러 추가

```python
# app/events/handlers.py
from pyai.events import on_event

@on_event("recipe.created")
async def save_to_vector_db(event):
    """레시피 생성 시 벡터 DB에 자동 저장"""
    await vector_store.add_documents([event.data])

@on_event("user.registered")
async def send_welcome_email(event):
    """사용자 등록 시 환영 이메일 발송"""
    await email_service.send(event.user_email, "welcome")
```

### 5. 커스텀 검증기 추가

```python
# app/domain/validators/recipe_validator.py
from pyai.validators import BaseValidator

class RecipeValidator(BaseValidator):
    def validate(self, recipe: Recipe) -> List[ValidationError]:
        errors = []

        if len(recipe.ingredients) < 1:
            errors.append(ValidationError("재료가 비어있습니다"))

        if recipe.cooking_time <= 0:
            errors.append(ValidationError("조리 시간이 유효하지 않습니다"))

        return errors
```

---

## 프레임워크 사용 시나리오

### Scenario 1: 간단한 챗봇 (5분)

```bash
# 1. 프로젝트 생성
$ pyai create simple-chatbot --template=chatbot
$ cd simple-chatbot

# 2. 환경 변수 설정
$ cp .env.example .env
$ nano .env  # ANTHROPIC_API_KEY 입력

# 3. 실행
$ pyai run --reload

# 완료! http://localhost:8000/docs
```

**자동 생성되는 것**:
- FastAPI 앱 (라우팅, 인증, 미들웨어)
- 기본 워크플로우 (의도 분류 → 응답 생성)
- 프롬프트 템플릿 (질문/답변)
- 테스트 코드
- Docker 설정

### Scenario 2: RAG 기반 문서 QA (10분)

```bash
# 1. RAG 템플릿으로 생성
$ pyai create doc-qa --template=rag
$ cd doc-qa

# 2. 문서 업로드
$ pyai ingest ./documents --collection=docs

# 3. 설정 조정
$ nano config/settings.yaml
vector_store:
  config:
    collection_name: docs
    top_k: 5

# 4. 실행
$ pyai run
```

**추가되는 기능**:
- 벡터 DB 연동 (Chroma)
- 문서 임베딩 자동화
- 유사도 검색 노드
- Context 주입 프롬프트

### Scenario 3: 멀티턴 대화 (15분)

```bash
# 1. 대화형 템플릿
$ pyai create conversation-bot --template=conversational
$ cd conversation-bot

# 2. 메모리 설정
$ nano config/settings.yaml
memory:
  provider: postgres
  config:
    database_url: postgresql://...

# 3. 실행
$ pyai run
```

**추가되는 기능**:
- 대화 히스토리 자동 저장/로드
- 세션 관리
- Context 윈도우 관리 (토큰 제한)
- 대화 요약 자동화

### Scenario 4: 멀티모달 앱 (20분)

```bash
# 1. 멀티모달 템플릿
$ pyai create multimodal-bot --template=multimodal
$ cd multimodal-bot

# 2. 이미지 생성 설정
$ nano config/settings.yaml
image:
  provider: replicate
  config:
    model: flux-schnell

# 3. 실행
$ pyai run
```

**추가되는 기능**:
- 이미지 생성 노드
- 이미지 분석 (Vision)
- 파일 업로드 엔드포인트
- 멀티모달 프롬프트

---

## 기존 프레임워크 비교

### PyAI vs LangChain

| 항목 | PyAI Framework | LangChain |
|-----|---------------|-----------|
| **학습 곡선** | 낮음 (FastAPI 경험자) | 높음 (방대한 API) |
| **아키텍처** | Hexagonal 강제 | 자유 (구조 없음) |
| **프롬프트 관리** | YAML + Jinja2 분리 | 코드 내 하드코딩 |
| **DI** | Built-in (Spring 스타일) | 없음 (수동 주입) |
| **워크플로우** | LangGraph (선언적) | LCEL (명령형) |
| **테스트** | Mock Adapter 자동 | 수동 모킹 |
| **타입 안전성** | 강함 (Pydantic 전역) | 약함 |
| **FastAPI 통합** | 네이티브 | 서드파티 필요 |
| **사용 사례** | FastAPI + AI 앱 특화 | 범용 LLM 앱 |

### PyAI vs CrewAI

| 항목 | PyAI Framework | CrewAI |
|-----|---------------|--------|
| **초점** | 단일 에이전트 → 워크플로우 | 멀티 에이전트 협업 |
| **복잡도** | 낮음 (단순 → 복잡) | 높음 (에이전트 관리) |
| **프롬프트 관리** | YAML + Jinja2 | 코드 내 정의 |
| **API 서버** | FastAPI Built-in | 별도 구축 필요 |
| **인증** | JWT Built-in | 없음 |
| **사용 사례** | REST API 서비스 | 복잡한 에이전트 협업 |

### PyAI vs Semantic Kernel

| 항목 | PyAI Framework | Semantic Kernel |
|-----|---------------|-----------------|
| **생태계** | Python/FastAPI | .NET/MS 생태계 |
| **아키텍처** | Hexagonal | Plugin 기반 |
| **프롬프트** | YAML + Jinja2 | Semantic Functions |
| **워크플로우** | LangGraph | Planner |
| **오픈소스** | 완전 오픈 | MS 주도 |
| **한국어** | 네이티브 지원 | 제한적 |

### 선택 가이드

```
PyAI Framework를 선택해야 하는 경우:
  ✅ FastAPI로 REST API 구축
  ✅ 한국어 AI 서비스
  ✅ Spring 경험자 (DI, Port-Adapter 익숙)
  ✅ 프롬프트 버전 관리 필요
  ✅ 빠른 MVP 구축

LangChain을 선택해야 하는 경우:
  ✅ 범용 LLM 앱 (다양한 유스케이스)
  ✅ 많은 서드파티 통합 필요
  ✅ 실험적 프로젝트

CrewAI를 선택해야 하는 경우:
  ✅ 복잡한 멀티 에이전트 협업
  ✅ Role-based 에이전트 시스템

Semantic Kernel을 선택해야 하는 경우:
  ✅ .NET 생태계
  ✅ MS Azure 통합
```

---

## 핵심 설계 원칙

### 1. Convention over Configuration

```
기본 설정으로 바로 동작:
  - 디렉토리 구조 (표준 레이아웃)
  - 라우팅 규칙 (자동 스캔)
  - 로깅 설정 (기본 포맷)

필요 시에만 커스터마이징
```

### 2. Progressive Disclosure

```
복잡도에 따라 점진적 노출:

Level 1: 설정만 작성 (80% 케이스)
  config/settings.yaml 수정

Level 2: 커스텀 노드 추가 (15% 케이스)
  app/workflows/nodes/ 구현

Level 3: 프레임워크 확장 (5% 케이스)
  Adapter, Middleware 추가
```

### 3. Fail-Fast with Clear Errors

```
설정 오류 시 즉시 실패:
  ❌ "LLM provider 'xxx' not found"
     → Available: anthropic, openai, ollama

  ❌ "Prompt template 'yyy' missing"
     → Check: prompts/yyy.j2

런타임 오류는 명확한 컨텍스트:
  ❌ "Node 'recipe_generator' failed"
     → State: {...}
     → Error: API timeout
     → Retry: 2/3
```

### 4. Zero-Lock-In

```
프레임워크 없이도 작동 가능:
  - Domain Layer: 완전 독립
  - Adapters: 표준 Port 인터페이스
  - Prompts: 일반 Jinja2 템플릿

언제든지 탈출 가능:
  - FastAPI 직접 사용
  - LangGraph 직접 구성
  - 프레임워크 → 라이브러리로 전환
```

### 5. Test-Driven by Default

```
자동 생성되는 테스트:
  - Adapter 테스트 (Mock 포함)
  - 노드 테스트
  - API 통합 테스트

설정 검증:
  $ pyai validate-config
  $ pyai validate-prompts
  $ pyai test --coverage
```

---

## 로드맵

### Phase 1: Core Framework (2-3개월)
- [ ] DI Container 구현
- [ ] Base Ports/Adapters 정의
- [ ] Prompt Management System
- [ ] 설정 시스템 (YAML)
- [ ] CLI 기본 기능

### Phase 2: Built-in Adapters (1-2개월)
- [ ] LLM Adapters (Anthropic, OpenAI, Ollama)
- [ ] VectorStore Adapters (Chroma, Pinecone)
- [ ] Memory Adapters (Postgres, Redis)
- [ ] Image Adapters (Replicate, DALLE)

### Phase 3: Developer Experience (1개월)
- [ ] CLI 고급 기능 (generate, scaffold)
- [ ] 템플릿 시스템
- [ ] 핫 리로드
- [ ] 개발 서버

### Phase 4: Observability (1개월)
- [ ] 구조화된 로깅
- [ ] 메트릭 (Prometheus)
- [ ] 트레이싱 (OpenTelemetry)
- [ ] 대시보드

### Phase 5: Production Ready (1개월)
- [ ] 성능 최적화
- [ ] 보안 강화
- [ ] 배포 가이드
- [ ] 문서화

### Phase 6: Ecosystem (지속)
- [ ] PyPI 배포
- [ ] 플러그인 마켓플레이스
- [ ] 튜토리얼 및 예제
- [ ] 커뮤니티 구축

---

## 결론

### PyAI Framework의 핵심 가치

```
1. 생산성: 5분 만에 AI Agent 앱 구축
2. 품질: Hexagonal Architecture 강제 (기술 부채 방지)
3. 유연성: 설정 기반 (코드 최소화)
4. 확장성: 플러그인 시스템 (커스터마이징 용이)
5. 학습 곡선: Spring 경험자 친화적
```

### 타겟 시장

```
1차 타겟: 국내 AI 스타트업
  - 한국어 프롬프트 관리 최적화
  - FastAPI 생태계
  - 빠른 MVP 구축

2차 타겟: Spring → Python 전환 개발자
  - 익숙한 DI, Port-Adapter 패턴
  - 명확한 레이어 분리

3차 타겟: LangChain 사용자
  - 더 구조화된 대안
  - 프로덕션 준비된 아키텍처
```

### 차별화 포인트

```
vs LangChain:
  → 구조화된 아키텍처 (Hexagonal)
  → FastAPI 네이티브 통합
  → 프롬프트 1급 객체 (YAML + Jinja2)

vs CrewAI:
  → 단일 에이전트 특화 (복잡도 낮음)
  → REST API 서버 Built-in

vs Semantic Kernel:
  → Python/FastAPI 생태계
  → 오픈소스 (Lock-in 없음)
  → 한국어 네이티브 지원
```

### 성공 지표

```
6개월 내:
  - GitHub Stars: 1,000+
  - PyPI Downloads: 10,000/month
  - 프로덕션 사용: 10+ 기업

1년 내:
  - GitHub Stars: 5,000+
  - PyPI Downloads: 50,000/month
  - 국내 AI 서비스 표준 프레임워크
```

---

**PyAI Framework: AI Agent 애플리케이션을 위한 FastAPI + LangGraph 통합 프레임워크**

*"설정만으로 AI 서비스 구축"*