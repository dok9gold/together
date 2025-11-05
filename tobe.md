# PyAi 헥사고날 아키텍처 (Ports & Adapters) 리팩토링 계획

## 목표
**헥사고날 아키텍처(Ports & Adapters)** 와 **Dependency Injection(DI)** 을 적용하여 Spring Framework와 유사한 구조로 재설계합니다.

### 핵심 원칙
1. **의존성 역전 원칙(DIP)**: 도메인이 외부에 의존하지 않음
2. **관심사의 분리(SoC)**: 비즈니스 로직과 기술 세부사항 분리
3. **테스트 용이성**: 어댑터를 모킹하여 도메인 로직 단위 테스트
4. **확장성**: 새로운 어댑터 추가로 외부 시스템 교체 가능

---

## 현재 구조 문제점

### 1. 레이어 구분 모호
```python
# app/services/cooking_assistant.py (현재)
class CookingAssistant:
    def __init__(self):
        self.llm = ChatAnthropic(...)           # 외부 API 직접 의존
        self.image_service = ImageService()     # 외부 API 직접 의존
```

**문제:**
- 비즈니스 로직(CookingAssistant)과 외부 시스템(Anthropic API)이 같은 레이어
- LLM 제공자 변경(Anthropic → OpenAI) 시 도메인 로직 수정 필요
- **의존성 방향이 잘못됨**: 도메인 → 인프라 (역전 필요)

### 2. 강한 결합(Tight Coupling)
```python
# app/api/routes.py (현재)
cooking_assistant = CookingAssistant()  # 모듈 레벨 하드코딩

# 테스트 불가능
# - CookingAssistant가 내부에서 ChatAnthropic 직접 생성
# - 모킹 불가능 → 단위 테스트 작성 불가
```

### 3. 설정 관리 분산
```python
# 각 서비스에서 개별적으로 환경 변수 읽기
self.api_token = os.getenv("REPLICATE_API_TOKEN")
self.llm = ChatAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
```

**문제:**
- 환경 변수 이름 변경 시 여러 파일 수정 필요
- 검증 로직 분산
- 기본값 관리 일관성 부족

### 4. 책임 혼재
```python
class CookingAssistant:
    def _classify_intent(self, state):
        # LLM 프롬프트 작성 (비즈니스 로직)
        prompt = "..."

        # Anthropic API 호출 (인프라 로직)
        response = self.llm.invoke([HumanMessage(content=prompt)])

        # JSON 파싱 (기술 세부사항)
        result = json.loads(response.content)
```

**문제:**
- 비즈니스 로직 + 외부 통신 + 데이터 변환이 한 곳에 섞임
- 단일 책임 원칙(SRP) 위반
- 테스트 시 외부 API 호출 불가피

---

## TO-BE 아키텍처: 헥사고날 (Ports & Adapters)

### 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│                  (FastAPI Routes, DTO)                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│              (Use Cases, Workflow Orchestration)             │
│   - CreateRecipeUseCase                                      │
│   - RecommendDishesUseCase                                   │
│   - AnswerQuestionUseCase                                    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                            │
│            (Business Logic, Entities, Ports)                 │
│                                                              │
│   ┌────────────────────────────────────────────┐            │
│   │  Domain Services                           │            │
│   │  - CookingAssistantService                 │            │
│   │  - RecipeService                           │            │
│   └────────────────────────────────────────────┘            │
│                                                              │
│   ┌────────────────────────────────────────────┐            │
│   │  Ports (Interfaces)                        │            │
│   │  - ILLMPort                                │            │
│   │  - IImagePort                              │            │
│   │  - IRecipeRepositoryPort (미래)           │            │
│   └────────────────────────────────────────────┘            │
│                                                              │
│   ┌────────────────────────────────────────────┐            │
│   │  Entities                                  │            │
│   │  - Recipe, CookingState, Recommendation    │            │
│   └────────────────────────────────────────────┘            │
└──────────────────────────▲───────────────────────────────────┘
                           │ (의존성 역전)
                           │
┌──────────────────────────┴───────────────────────────────────┐
│                     Adapter Layer                            │
│               (External Systems Integration)                 │
│                                                              │
│   ┌────────────────┐  ┌────────────────┐  ┌──────────────┐ │
│   │  LLM Adapters  │  │ Image Adapters │  │ Persistence  │ │
│   │                │  │                │  │  (미래)      │ │
│   │ - Anthropic    │  │ - Replicate    │  │ - PostgreSQL │ │
│   │ - OpenAI       │  │ - DALL-E       │  │ - Redis      │ │
│   │ - Gemini       │  │ - Midjourney   │  │              │ │
│   └────────────────┘  └────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 핵심 개념

#### 1. Port (포트)
- **정의**: 도메인이 외부와 소통하기 위해 정의한 **인터페이스**
- **위치**: `domain/ports/`
- **역할**: "나는 LLM이 이렇게 동작했으면 좋겠어" (추상 메서드)
- **특징**: 구현 없음, 순수 인터페이스

#### 2. Adapter (어댑터)
- **정의**: 외부 시스템을 **Port에 맞게 변환**하는 구현체
- **위치**: `adapters/llm/`, `adapters/image/`
- **역할**: "Anthropic API를 Port에 맞게 감싸기"
- **특징**: 외부 API 호출, 데이터 변환

#### 3. Domain Service (도메인 서비스)
- **정의**: 핵심 비즈니스 로직
- **위치**: `domain/services/`
- **역할**: 레시피 생성 규칙, 추천 알고리즘
- **특징**: Port에만 의존, 외부 시스템 몰라도 됨

#### 4. Use Case (유스케이스)
- **정의**: 애플리케이션의 특정 작업 흐름
- **위치**: `application/use_cases/`
- **역할**: 도메인 서비스 조합, 트랜잭션 관리
- **특징**: LangGraph 워크플로우가 여기 위치

---

## 헥사고날 아키텍처 적용 범위 (중요!)

### ⚠️ 핵심: 헥사고날은 "외부 시스템 연동 부분만" 적용합니다

많은 개발자들이 헥사고날 아키텍처를 오해하는 부분:
- ❌ **잘못된 이해**: 모든 클래스마다 인터페이스를 만들어야 한다
- ✅ **올바른 이해**: 외부 시스템과의 경계에만 Port/Adapter를 적용한다

```
┌──────────────────────────────────────────────────────┐
│             Domain (비즈니스 로직)                      │
│                                                       │
│  ✅ 일반적인 객체지향 설계                              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                       │
│  class CookingAssistantService:                      │
│      def __init__(self, llm_port, image_port):      │
│          self.llm_port = llm_port                   │
│          self.image_port = image_port               │
│          # ✅ 내부 헬퍼는 그냥 직접 생성               │
│          self.validator = RecipeValidator()         │
│                                                       │
│      def classify_intent(self, state):              │
│          # ✅ 외부 시스템은 Port 사용                 │
│          result = self.llm_port.classify(...)       │
│          # ✅ 내부 검증은 일반 메서드 호출             │
│          if self.validator.is_valid(result):        │
│              return result                          │
│                                                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  ┌──────────────────────────────────────┐           │
│  │  Port (외부와의 경계만!)               │           │
│  │  ════════════════════════════════════ │           │
│  │  - ILLMPort (LLM API 호출)           │           │
│  │  - IImagePort (이미지 API 호출)       │           │
│  │  - IRepositoryPort (DB 접근)         │           │
│  └──────────────────────────────────────┘           │
└───────────────────┬───────────────────────────────────┘
                    │ (여기만 추상화!)
                    ▼
┌──────────────────────────────────────────────────────┐
│            Adapter (외부 시스템 연동)                  │
│  ════════════════════════════════════════════════════ │
│  - AnthropicLLMAdapter    → Anthropic API           │
│  - ReplicateImageAdapter  → Replicate API           │
│  - PostgreSQLAdapter      → PostgreSQL              │
└──────────────────────────────────────────────────────┘
```

---

### 판단 기준: 언제 Port/Adapter를 만들어야 하는가?

#### ✅ Port/Adapter를 만들어야 하는 경우 (외부 시스템)

| 대상 | 이유 | 예시 |
|------|------|------|
| **외부 API 호출** | 제공자 교체 가능성 | Anthropic → OpenAI |
| **데이터베이스** | DB 종류 변경 가능성 | PostgreSQL → MongoDB |
| **파일 시스템** | 저장소 교체 가능성 | Local → S3 |
| **외부 메시징** | 메시지 브로커 교체 | RabbitMQ → Kafka |
| **캐시 시스템** | 캐시 구현 교체 | Redis → Memcached |

**공통점:**
- 네트워크/IO 경계를 넘어감
- 외부 라이브러리/서비스에 의존
- 테스트 시 모킹 필요
- 교체 가능성 존재

#### ❌ Port/Adapter가 불필요한 경우 (내부 로직)

| 대상 | 이유 | 대신 사용 |
|------|------|----------|
| **검증 로직** | 순수 비즈니스 규칙 | 일반 클래스 |
| **계산 로직** | 알고리즘 | 일반 메서드 |
| **포매팅** | 단순 변환 | 유틸 함수 |
| **내부 헬퍼** | 도메인 내부 조합 | 일반 클래스 |

**공통점:**
- 외부 시스템 의존 없음
- 교체할 이유 없음
- 테스트 시 그냥 인스턴스 생성하면 됨

---

### 실전 예시: Good vs Bad

#### ❌ 과도한 추상화 (오버엔지니어링)

```python
# 나쁜 예: 내부 검증 로직까지 Port 만들기
class IRecipeValidatorPort(ABC):
    @abstractmethod
    def validate_title(self, title: str) -> bool:
        pass

    @abstractmethod
    def validate_ingredients(self, ingredients: List[str]) -> bool:
        pass

class RecipeValidatorAdapter(IRecipeValidatorPort):
    def validate_title(self, title: str) -> bool:
        return len(title) > 0 and len(title) < 100

    def validate_ingredients(self, ingredients: List[str]) -> bool:
        return len(ingredients) >= 1

# 문제:
# 1. 검증 로직은 교체할 일이 없다
# 2. 외부 시스템이 아니다
# 3. 테스트도 그냥 RecipeValidator() 생성하면 된다
# 4. 불필요한 추상화로 코드만 복잡해진다
```

#### ✅ 적절한 추상화

```python
# 좋은 예 1: 외부 LLM API는 Port/Adapter
class ILLMPort(ABC):
    """외부 LLM 서비스 호출 (교체 가능)"""
    @abstractmethod
    async def classify_intent(self, query: str) -> Dict[str, Any]:
        pass

class AnthropicLLMAdapter(ILLMPort):
    """Anthropic Claude 구현"""
    # Anthropic API 호출

class OpenAILLMAdapter(ILLMPort):
    """OpenAI GPT 구현"""
    # OpenAI API 호출

# 장점:
# 1. LLM 제공자 교체 가능 (Anthropic ↔ OpenAI)
# 2. 테스트 시 모킹 가능 (실제 API 호출 불필요)
# 3. 실제 필요성 있음 (비용, 성능, 정책에 따라 교체)


# 좋은 예 2: 내부 검증 로직은 일반 클래스
class RecipeValidator:
    """내부 비즈니스 규칙 (인터페이스 불필요)"""

    def validate_title(self, title: str) -> bool:
        return len(title) > 0 and len(title) < 100

    def validate_ingredients(self, ingredients: List[str]) -> bool:
        return len(ingredients) >= 1

    def validate_recipe(self, recipe: Recipe) -> ValidationResult:
        errors = []
        if not self.validate_title(recipe.title):
            errors.append("제목이 유효하지 않습니다")
        if not self.validate_ingredients(recipe.ingredients):
            errors.append("재료가 필요합니다")
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

# 사용:
class CookingAssistantService:
    def __init__(self, llm_port: ILLMPort, image_port: IImagePort):
        self.llm_port = llm_port
        self.image_port = image_port
        # ✅ 내부 헬퍼는 그냥 직접 생성
        self.validator = RecipeValidator()

    async def generate_recipe(self, state: CookingState):
        # ✅ 외부 시스템은 Port 사용
        recipe_data = await self.llm_port.generate_recipe(...)

        # ✅ 내부 검증은 일반 메서드 호출
        validation = self.validator.validate_recipe(recipe_data)
        if not validation.is_valid:
            raise ValidationError(validation.errors)

        return recipe_data
```

---

### 실전 가이드라인: 4단계 체크리스트

Port/Adapter를 만들기 전에 다음 질문에 답하세요:

```
┌─────────────────────────────────────────────────────────┐
│  1. 외부 시스템 의존인가?                                 │
│     ├─ Yes → 2번으로                                    │
│     └─ No  → ❌ 일반 클래스 사용                         │
│                                                         │
│  2. 교체 가능성이 있는가?                                 │
│     ├─ Yes → 3번으로                                    │
│     └─ No  → ⚠️  재고민 (정말 필요한가?)                 │
│                                                         │
│  3. 테스트 시 모킹이 필요한가?                            │
│     ├─ Yes → 4번으로                                    │
│     └─ No  → ⚠️  재고민 (간단한 인터페이스면 OK)         │
│                                                         │
│  4. 네트워크/IO 경계를 넘는가?                            │
│     ├─ Yes → ✅ Port/Adapter 생성                       │
│     └─ No  → ❌ 일반 클래스 사용                         │
└─────────────────────────────────────────────────────────┘
```

#### 예시 적용

| 대상 | 외부? | 교체? | 모킹? | IO? | 결론 |
|------|-------|-------|-------|-----|------|
| **Anthropic API** | ✅ | ✅ | ✅ | ✅ | ✅ Port/Adapter |
| **Replicate API** | ✅ | ✅ | ✅ | ✅ | ✅ Port/Adapter |
| **PostgreSQL** | ✅ | ✅ | ✅ | ✅ | ✅ Port/Adapter |
| **RecipeValidator** | ❌ | ❌ | ❌ | ❌ | ❌ 일반 클래스 |
| **JSONParser** | ❌ | ❌ | ❌ | ❌ | ❌ 유틸 함수 |
| **PriceCalculator** | ❌ | ❌ | ❌ | ❌ | ❌ 일반 클래스 |

---

### 레이어별 적용 범위 요약

| 레이어 | Port/Adapter 적용 | 설계 방식 | 예시 |
|--------|------------------|----------|------|
| **Adapter** | ✅ **핵심** | Port 인터페이스 구현 | `AnthropicLLMAdapter` |
| **Domain (Ports)** | ✅ **핵심** | 인터페이스 정의 | `ILLMPort` |
| **Domain (Services)** | ❌ 일반 OOP | DI + 일반 클래스 | `CookingAssistantService` |
| **Domain (Entities)** | ❌ 일반 OOP | Dataclass/Pydantic | `Recipe`, `CookingState` |
| **Application (UseCase)** | ❌ 일반 OOP | Domain Service 조합 | `CreateRecipeUseCase` |
| **Presentation (API)** | ❌ 일반 OOP | UseCase 호출 | `routes.py` |

---

### 일반적인 함정 (Anti-Patterns)

#### 🚫 함정 1: "모든 것을 인터페이스로"

```python
# ❌ 나쁜 예
class IRecipeFormatter(ABC):
    @abstractmethod
    def format(self, recipe): pass

class IRecipeLogger(ABC):
    @abstractmethod
    def log(self, message): pass

class IRecipeCounter(ABC):
    @abstractmethod
    def count(self): pass

# 문제: 추상화할 이유가 없는 것까지 추상화
# 결과: 코드만 복잡해지고 유지보수 어려워짐
```

#### 🚫 함정 2: "일단 만들어두면 나중에 유용할 거야" (YAGNI 위반)

```python
# ❌ 나쁜 예
class INotificationPort(ABC):
    """미래에 이메일/SMS 보낼 수도 있으니까 만들어두자"""
    pass

class IPaymentPort(ABC):
    """나중에 결제 기능 추가할 수도 있으니까"""
    pass

# 문제: 현재 필요하지 않은 추상화
# 원칙: YAGNI (You Aren't Gonna Need It)
# 해법: 필요할 때 추가하기
```

#### 🚫 함정 3: "테스트를 위해 모든 것을 인터페이스로"

```python
# ❌ 나쁜 예
class IDateProvider(ABC):
    """현재 시간 모킹을 위해"""
    @abstractmethod
    def now(self): pass

class IRandomGenerator(ABC):
    """랜덤 값 모킹을 위해"""
    @abstractmethod
    def random(self): pass

# 문제: 테스트만을 위한 과도한 추상화
# 해법:
# - 시간은 파라미터로 전달
# - 랜덤 시드 설정
# - 정말 필요한 경우에만 추상화
```

#### ✅ 올바른 접근

```python
# ✅ 좋은 예: 외부 경계만 Port/Adapter
class CookingAssistantService:
    def __init__(
        self,
        llm_port: ILLMPort,              # ✅ 외부 LLM API
        image_port: IImagePort,          # ✅ 외부 이미지 API
        repository_port: IRepositoryPort # ✅ 외부 DB
    ):
        self.llm_port = llm_port
        self.image_port = image_port
        self.repository_port = repository_port

        # ✅ 내부 헬퍼는 직접 생성
        self.validator = RecipeValidator()
        self.formatter = RecipeFormatter()
        self.calculator = NutritionCalculator()

    async def create_recipe(self, query: str):
        # ✅ 외부 호출: Port 사용
        recipe_data = await self.llm_port.generate_recipe(query)

        # ✅ 내부 로직: 일반 메서드 호출
        if not self.validator.validate(recipe_data):
            raise ValidationError()

        formatted = self.formatter.format(recipe_data)
        nutrition = self.calculator.calculate(recipe_data)

        # ✅ 외부 저장: Port 사용
        await self.repository_port.save(formatted)

        # ✅ 외부 이미지 생성: Port 사용
        image_url = await self.image_port.generate(recipe_data.title)

        return formatted
```

---

### 핵심 원칙 요약

```
┌──────────────────────────────────────────────────────────┐
│  헥사고날 아키텍처의 황금률                                 │
│  ════════════════════════════════════════════════════════ │
│                                                           │
│  1. Port/Adapter는 외부 경계에만 적용한다                  │
│     → 네트워크, DB, 파일시스템, 외부 API                   │
│                                                           │
│  2. 도메인 내부는 일반적인 객체지향 설계를 따른다            │
│     → 일반 클래스, DI, 단순한 메서드 호출                   │
│                                                           │
│  3. "교체 가능성"과 "테스트 필요성"이 진짜 있는지 확인       │
│     → YAGNI 원칙 준수                                     │
│                                                           │
│  4. 과도한 추상화는 독이다                                 │
│     → 필요한 곳에만 적용                                   │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## 1. 디렉토리 구조

```
PyAi/
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI 앱 + DI 컨테이너 초기화
│   │
│   ├── domain/                          # 도메인 레이어 (가장 안쪽)
│   │   ├── __init__.py
│   │   │
│   │   ├── entities/                    # 엔티티 (비즈니스 객체)
│   │   │   ├── __init__.py
│   │   │   ├── recipe.py                # Recipe, RecipeStep, Ingredient
│   │   │   ├── recommendation.py        # Recommendation
│   │   │   ├── cooking_state.py         # CookingState (LangGraph 상태)
│   │   │   └── question.py              # Question, Answer
│   │   │
│   │   ├── ports/                       # 포트 (인터페이스)
│   │   │   ├── __init__.py
│   │   │   ├── llm_port.py              # ILLMPort (Inbound Port)
│   │   │   ├── image_port.py            # IImagePort (Inbound Port)
│   │   │   └── repository_port.py       # IRecipeRepositoryPort (미래)
│   │   │
│   │   └── services/                    # 도메인 서비스 (비즈니스 로직)
│   │       ├── __init__.py
│   │       ├── cooking_assistant.py     # 핵심 비즈니스 로직
│   │       └── recipe_validator.py      # 레시피 검증 로직
│   │
│   ├── application/                     # 애플리케이션 레이어 (유스케이스)
│   │   ├── __init__.py
│   │   │
│   │   ├── use_cases/                   # 유스케이스 (작업 흐름)
│   │   │   ├── __init__.py
│   │   │   ├── create_recipe_use_case.py       # 레시피 생성 워크플로우
│   │   │   ├── recommend_dishes_use_case.py    # 추천 워크플로우
│   │   │   └── answer_question_use_case.py     # 질문 답변 워크플로우
│   │   │
│   │   └── workflow/                    # LangGraph 워크플로우 (기존 유지)
│   │       ├── __init__.py
│   │       ├── intent_classifier.py     # 의도 분류 노드
│   │       ├── recipe_generator.py      # 레시피 생성 노드
│   │       └── dish_recommender.py      # 추천 노드
│   │
│   ├── adapters/                        # 어댑터 레이어 (외부 시스템)
│   │   ├── __init__.py
│   │   │
│   │   ├── llm/                         # LLM 어댑터
│   │   │   ├── __init__.py
│   │   │   ├── anthropic_adapter.py     # Anthropic Claude 구현
│   │   │   ├── openai_adapter.py        # (미래) OpenAI GPT 구현
│   │   │   └── gemini_adapter.py        # (미래) Google Gemini 구현
│   │   │
│   │   ├── image/                       # 이미지 생성 어댑터
│   │   │   ├── __init__.py
│   │   │   ├── replicate_adapter.py     # Replicate Flux Schnell 구현
│   │   │   ├── dalle_adapter.py         # (미래) DALL-E 구현
│   │   │   └── midjourney_adapter.py    # (미래) Midjourney 구현
│   │   │
│   │   └── persistence/                 # (미래) 영속성 어댑터
│   │       ├── __init__.py
│   │       └── recipe_repository.py     # PostgreSQL/MongoDB 구현
│   │
│   ├── api/                             # 프레젠테이션 레이어 (FastAPI)
│   │   ├── __init__.py
│   │   ├── routes.py                    # 라우트 (DI 사용)
│   │   ├── dependencies.py              # FastAPI Depends 헬퍼
│   │   └── dto/                         # DTO (Request/Response)
│   │       ├── __init__.py
│   │       ├── request.py               # CookingRequest
│   │       └── response.py              # CookingResponse
│   │
│   ├── core/                            # 인프라 레이어 (설정, DI)
│   │   ├── __init__.py
│   │   ├── config.py                    # 설정 클래스 (Pydantic BaseSettings)
│   │   └── container.py                 # DI 컨테이너 (dependency-injector)
│   │
│   └── models/                          # (점진적 마이그레이션용, 추후 제거)
│       ├── __init__.py
│       └── schemas.py
│
├── tests/                               # 테스트
│   ├── unit/
│   │   ├── domain/
│   │   │   └── test_cooking_assistant.py
│   │   ├── adapters/
│   │   │   ├── test_anthropic_adapter.py
│   │   │   └── test_replicate_adapter.py
│   │   └── use_cases/
│   │       └── test_create_recipe.py
│   │
│   └── integration/
│       └── test_api_routes.py
│
├── .env
├── .env.example
├── requirements.txt
└── tobe.md
```

---

## 2. 핵심 컴포넌트 설계

### 2.1 설정 관리 (중앙화)

```python
# app/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List

class Settings(BaseSettings):
    """애플리케이션 설정 (환경 변수 중앙 관리)"""

    # API 키
    anthropic_api_key: str
    replicate_api_token: str

    # LLM 설정
    llm_model: str = "claude-sonnet-4-5-20250929"
    llm_timeout: int = 90
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096

    # 이미지 생성 설정
    image_model: str = "black-forest-labs/flux-schnell"
    image_retries: int = 2
    image_aspect_ratio: str = "1:1"
    image_output_quality: int = 80

    # 애플리케이션 설정
    app_title: str = "Cooking Assistant API"
    app_version: str = "2.0.0"
    cors_origins: List[str] = ["*"]

    # 로깅
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """싱글톤 설정 인스턴스 반환"""
    return Settings()
```

---

### 2.2 Domain Layer (도메인 레이어)

#### 2.2.1 Entities (엔티티)

```python
# app/domain/entities/recipe.py
from dataclasses import dataclass
from typing import List

@dataclass
class Recipe:
    """레시피 엔티티 (비즈니스 객체)"""
    title: str
    ingredients: List[str]
    steps: List[str]
    cooking_time: str
    difficulty: str  # "쉬움", "중간", "어려움"

    def validate(self) -> bool:
        """레시피 유효성 검증 (비즈니스 규칙)"""
        if not self.title or len(self.title) < 2:
            return False
        if not self.ingredients or len(self.ingredients) < 1:
            return False
        if not self.steps or len(self.steps) < 1:
            return False
        return True

# app/domain/entities/cooking_state.py
from typing import TypedDict, Optional, List, Dict, Any

class CookingState(TypedDict):
    """LangGraph 워크플로우 상태"""
    user_query: str
    primary_intent: str
    secondary_intents: List[str]
    entities: Dict[str, Any]
    confidence: float
    recipe_text: str
    recipes: List[Dict[str, Any]]
    dish_names: List[str]
    recommendation: str
    answer: str
    image_prompt: str
    image_url: Optional[str]
    image_urls: List[str]
    error: Optional[str]
```

#### 2.2.2 Ports (포트 = 인터페이스)

```python
# app/domain/ports/llm_port.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class ILLMPort(ABC):
    """LLM 포트 (도메인이 외부 LLM에게 원하는 기능)"""

    @abstractmethod
    async def classify_intent(self, query: str) -> Dict[str, Any]:
        """
        의도 분류

        Args:
            query: 사용자 쿼리

        Returns:
            {
                "primary_intent": "recipe_create" | "recommend" | "question",
                "secondary_intents": [...],
                "entities": {...},
                "confidence": 0.95
            }
        """
        pass

    @abstractmethod
    async def generate_recipe(
        self,
        query: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        레시피 생성

        Args:
            query: 사용자 쿼리
            entities: 추출된 엔티티 (요리명, 재료 등)

        Returns:
            {
                "title": "김치찌개",
                "ingredients": [...],
                "steps": [...],
                "cooking_time": "30분",
                "difficulty": "중간"
            }
        """
        pass

    @abstractmethod
    async def recommend_dishes(
        self,
        query: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        음식 추천

        Args:
            query: 사용자 쿼리
            entities: 추출된 엔티티 (맛 선호, 요리 유형 등)

        Returns:
            {
                "recommendations": [
                    {"name": "...", "description": "...", "reason": "..."},
                    ...
                ]
            }
        """
        pass

    @abstractmethod
    async def answer_question(self, query: str) -> Dict[str, Any]:
        """
        질문 답변

        Args:
            query: 사용자 질문

        Returns:
            {
                "answer": "...",
                "additional_tips": [...]
            }
        """
        pass


# app/domain/ports/image_port.py
from abc import ABC, abstractmethod
from typing import Optional

class IImagePort(ABC):
    """이미지 생성 포트"""

    @abstractmethod
    def generate_prompt(self, dish_name: str) -> str:
        """
        요리명을 받아 이미지 생성 프롬프트 생성

        Args:
            dish_name: 요리 이름 (예: "김치찌개")

        Returns:
            영어 이미지 프롬프트
        """
        pass

    @abstractmethod
    async def generate_image(self, prompt: str) -> Optional[str]:
        """
        이미지 생성

        Args:
            prompt: 이미지 생성 프롬프트

        Returns:
            이미지 URL 또는 None (실패 시)
        """
        pass
```

#### 2.2.3 Domain Services (도메인 서비스)

```python
# app/domain/services/cooking_assistant.py
from app.domain.ports.llm_port import ILLMPort
from app.domain.ports.image_port import IImagePort
from app.domain.entities.cooking_state import CookingState
import logging

logger = logging.getLogger(__name__)

class CookingAssistantService:
    """
    요리 AI 어시스턴트 도메인 서비스

    - 외부 시스템 몰라도 됨 (Port에만 의존)
    - 순수 비즈니스 로직만 포함
    - 테스트 시 Port를 모킹하면 됨
    """

    def __init__(self, llm_port: ILLMPort, image_port: IImagePort):
        """
        의존성 주입: Port 인터페이스를 받음

        Args:
            llm_port: LLM 포트 (Anthropic든 OpenAI든 상관없음)
            image_port: 이미지 포트 (Replicate든 DALL-E든 상관없음)
        """
        self.llm_port = llm_port
        self.image_port = image_port

    async def classify_intent(self, state: CookingState) -> CookingState:
        """의도 분류 (비즈니스 로직)"""
        try:
            # Port를 통해 LLM 호출 (구체적 구현 몰라도 됨)
            result = await self.llm_port.classify_intent(state["user_query"])

            state["primary_intent"] = result.get("primary_intent", "recipe_create")
            state["secondary_intents"] = result.get("secondary_intents", [])
            state["entities"] = result.get("entities", {})
            state["confidence"] = result.get("confidence", 0.5)

            logger.info(f"의도 분류 완료: {state['primary_intent']}")

        except Exception as e:
            logger.error(f"의도 분류 실패: {str(e)}")
            state["primary_intent"] = "recipe_create"
            state["confidence"] = 0.5

        return state

    async def generate_recipe(self, state: CookingState) -> CookingState:
        """레시피 생성 (비즈니스 로직)"""
        try:
            query = state["user_query"]
            entities = state.get("entities", {})

            # Port를 통해 레시피 생성
            recipe_data = await self.llm_port.generate_recipe(query, entities)

            # 비즈니스 규칙 적용
            if isinstance(recipe_data, list):
                state["recipes"] = recipe_data
                state["dish_names"] = [r.get("title", "") for r in recipe_data]
            elif isinstance(recipe_data, dict):
                state["recipe_text"] = str(recipe_data)
                state["dish_names"] = [recipe_data.get("title", "")]

            logger.info(f"레시피 생성 완료: {state['dish_names']}")

        except Exception as e:
            logger.error(f"레시피 생성 실패: {str(e)}")
            state["error"] = f"레시피 생성 실패: {str(e)}"

        return state

    async def generate_image(self, state: CookingState) -> CookingState:
        """이미지 생성 (비즈니스 로직)"""
        if not state.get("dish_names"):
            return state

        try:
            dish_name = state["dish_names"][0]

            # Port를 통해 이미지 프롬프트 생성
            prompt = self.image_port.generate_prompt(dish_name)
            state["image_prompt"] = prompt

            # Port를 통해 이미지 생성
            image_url = await self.image_port.generate_image(prompt)
            state["image_url"] = image_url

            logger.info(f"이미지 생성 완료: {image_url}")

        except Exception as e:
            logger.error(f"이미지 생성 실패: {str(e)}")
            # 이미지 실패는 치명적이지 않음 (레시피는 반환)

        return state
```

---

### 2.3 Adapter Layer (어댑터 레이어)

#### 2.3.1 LLM Adapter

```python
# app/adapters/llm/anthropic_adapter.py
from app.domain.ports.llm_port import ILLMPort
from app.core.config import Settings
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from typing import Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

class AnthropicLLMAdapter(ILLMPort):
    """
    Anthropic Claude 어댑터 (ILLMPort 구현체)

    - Port에 맞게 Anthropic API를 감싸기
    - 도메인은 이 어댑터의 존재를 몰라도 됨
    - 어댑터 교체만으로 LLM 제공자 변경 가능
    """

    def __init__(self, settings: Settings):
        """의존성 주입: Settings"""
        self.settings = settings
        self.llm = ChatAnthropic(
            model=settings.llm_model,
            api_key=settings.anthropic_api_key,
            timeout=settings.llm_timeout,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )

    async def classify_intent(self, query: str) -> Dict[str, Any]:
        """의도 분류 (Anthropic API 호출 + 응답 변환)"""
        prompt = self._build_intent_classification_prompt(query)

        logger.info(f"[Anthropic] 의도 분류 요청: {query}")

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result_json = self._extract_json(response.content)
            result = json.loads(result_json)

            logger.info(f"[Anthropic] 의도 분류 완료: {result.get('primary_intent')}")

            return result

        except Exception as e:
            logger.error(f"[Anthropic] 의도 분류 실패: {str(e)}")
            raise

    async def generate_recipe(self, query: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """레시피 생성 (Anthropic API 호출 + 응답 변환)"""
        prompt = self._build_recipe_generation_prompt(query, entities)

        logger.info(f"[Anthropic] 레시피 생성 요청: {query}")

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result_json = self._extract_json(response.content)
            result = json.loads(result_json)

            logger.info(f"[Anthropic] 레시피 생성 완료")

            return result

        except Exception as e:
            logger.error(f"[Anthropic] 레시피 생성 실패: {str(e)}")
            raise

    async def recommend_dishes(self, query: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """음식 추천 (Anthropic API 호출 + 응답 변환)"""
        prompt = self._build_recommendation_prompt(query, entities)

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result_json = self._extract_json(response.content)
            result = json.loads(result_json)

            return result

        except Exception as e:
            logger.error(f"[Anthropic] 추천 실패: {str(e)}")
            raise

    async def answer_question(self, query: str) -> Dict[str, Any]:
        """질문 답변 (Anthropic API 호출 + 응답 변환)"""
        prompt = f"""질문: {query}

위 질문에 대해 정확하고 도움이 되는 답변을 JSON 형식으로 제공하세요:
{{
    "answer": "답변 내용",
    "additional_tips": ["팁1", "팁2"]
}}"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result_json = self._extract_json(response.content)
            result = json.loads(result_json)

            return result

        except Exception as e:
            logger.error(f"[Anthropic] 질문 답변 실패: {str(e)}")
            raise

    def _extract_json(self, content: str) -> str:
        """마크다운 코드 블록에서 JSON 추출"""
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
        """의도 분류 프롬프트 생성 (기존 로직 유지)"""
        # 기존 cooking_assistant.py의 프롬프트 로직 그대로
        return f"""당신은 요리 AI 어시스턴트의 의도 분류 전문가입니다.

사용자 입력: "{query}"

다음 JSON 형식으로 분류하세요:
{{
    "primary_intent": "recipe_create|recommend|question",
    "secondary_intents": [],
    "entities": {{}},
    "confidence": 0.95
}}"""

    def _build_recipe_generation_prompt(self, query: str, entities: Dict[str, Any]) -> str:
        """레시피 생성 프롬프트 생성 (기존 로직 유지)"""
        # 기존 로직 그대로
        return f"""레시피를 JSON 형식으로 생성하세요.

Query: {query}
Entities: {entities}

JSON:
{{
    "title": "...",
    "ingredients": [...],
    "steps": [...],
    "cooking_time": "...",
    "difficulty": "..."
}}"""

    def _build_recommendation_prompt(self, query: str, entities: Dict[str, Any]) -> str:
        """추천 프롬프트 생성"""
        return f"""음식을 추천하고 JSON 형식으로 반환하세요.

Query: {query}
Entities: {entities}

JSON:
{{
    "recommendations": [
        {{"name": "...", "description": "...", "reason": "..."}},
        ...
    ]
}}"""
```

#### 2.3.2 Image Adapter

```python
# app/adapters/image/replicate_adapter.py
from app.domain.ports.image_port import IImagePort
from app.core.config import Settings
import replicate
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ReplicateImageAdapter(IImagePort):
    """
    Replicate 어댑터 (IImagePort 구현체)

    - Port에 맞게 Replicate API를 감싸기
    - 다른 이미지 서비스로 교체 가능 (DALL-E, Midjourney 등)
    """

    def __init__(self, settings: Settings):
        """의존성 주입: Settings"""
        self.settings = settings
        # Replicate API 토큰 설정
        self.api_token = settings.replicate_api_token

    def generate_prompt(self, dish_name: str) -> str:
        """요리명을 영어 프롬프트로 변환"""
        return f"professional food photography of {dish_name}, appetizing, high quality, restaurant style, well plated, natural lighting"

    async def generate_image(self, prompt: str) -> Optional[str]:
        """Replicate Flux Schnell 모델로 이미지 생성"""
        retries = self.settings.image_retries

        for attempt in range(retries):
            try:
                logger.info(f"[Replicate] 이미지 생성 시도 {attempt + 1}/{retries}")

                output = replicate.run(
                    self.settings.image_model,
                    input={
                        "prompt": prompt,
                        "num_outputs": 1,
                        "aspect_ratio": self.settings.image_aspect_ratio,
                        "output_format": "jpg",
                        "output_quality": self.settings.image_output_quality
                    }
                )

                if output and len(output) > 0:
                    logger.info(f"[Replicate] 이미지 생성 성공: {output[0]}")
                    return output[0]

            except Exception as e:
                logger.error(f"[Replicate] 시도 {attempt + 1} 실패: {str(e)}")
                if attempt == retries - 1:
                    return None

        return None
```

---

### 2.4 Application Layer (애플리케이션 레이어)

#### 2.4.1 Use Cases

```python
# app/application/use_cases/create_recipe_use_case.py
from app.domain.services.cooking_assistant import CookingAssistantService
from app.domain.entities.cooking_state import CookingState
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class CreateRecipeUseCase:
    """
    레시피 생성 유스케이스

    - 도메인 서비스를 조합하여 전체 워크플로우 실행
    - LangGraph 워크플로우가 여기 위치
    """

    def __init__(self, cooking_assistant: CookingAssistantService):
        """의존성 주입: 도메인 서비스"""
        self.cooking_assistant = cooking_assistant

    async def execute(self, query: str) -> CookingState:
        """
        레시피 생성 워크플로우 실행

        1. 의도 분류
        2. 레시피 생성
        3. 이미지 생성

        Args:
            query: 사용자 쿼리

        Returns:
            최종 상태 (CookingState)
        """
        logger.info(f"[UseCase] 레시피 생성 시작: {query}")

        # 초기 상태 생성
        state: CookingState = {
            "user_query": query,
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

        # 1. 의도 분류
        state = await self.cooking_assistant.classify_intent(state)

        # 2. 레시피 생성
        state = await self.cooking_assistant.generate_recipe(state)

        # 3. 이미지 생성
        state = await self.cooking_assistant.generate_image(state)

        logger.info(f"[UseCase] 레시피 생성 완료")

        return state
```

---

### 2.5 DI Container (컨테이너)

```python
# app/core/container.py
from dependency_injector import containers, providers
from app.core.config import get_settings

# Domain
from app.domain.services.cooking_assistant import CookingAssistantService

# Adapters
from app.adapters.llm.anthropic_adapter import AnthropicLLMAdapter
from app.adapters.image.replicate_adapter import ReplicateImageAdapter

# Application
from app.application.use_cases.create_recipe_use_case import CreateRecipeUseCase

class Container(containers.DeclarativeContainer):
    """
    의존성 컨테이너

    Spring의 ApplicationContext 역할
    """

    # 설정 (싱글톤)
    config = providers.Singleton(get_settings)

    # Adapters (싱글톤) - Port 구현체
    llm_adapter = providers.Singleton(
        AnthropicLLMAdapter,
        settings=config
    )

    image_adapter = providers.Singleton(
        ReplicateImageAdapter,
        settings=config
    )

    # Domain Services (싱글톤) - Adapter 주입
    cooking_assistant = providers.Singleton(
        CookingAssistantService,
        llm_port=llm_adapter,
        image_port=image_adapter
    )

    # Use Cases (팩토리) - 요청마다 새 인스턴스
    create_recipe_use_case = providers.Factory(
        CreateRecipeUseCase,
        cooking_assistant=cooking_assistant
    )
```

---

### 2.6 Presentation Layer (API)

```python
# app/api/routes.py
from fastapi import APIRouter, Depends, HTTPException
from app.api.dto.request import CookingRequest
from app.api.dto.response import CookingResponse
from app.api.dependencies import get_create_recipe_use_case
from app.application.use_cases.create_recipe_use_case import CreateRecipeUseCase
import json

router = APIRouter()

@router.post("/cooking", response_model=CookingResponse)
async def handle_cooking_query(
    request: CookingRequest,
    use_case: CreateRecipeUseCase = Depends(get_create_recipe_use_case)
):
    """
    요리 AI 어시스턴트 API (DI 적용)

    - use_case는 컨테이너에서 자동 주입
    - 도메인 로직은 전혀 몰라도 됨 (관심사 분리)
    """
    try:
        # 유스케이스 실행
        result = await use_case.execute(request.query)

        # 에러 처리
        if result.get("error"):
            return CookingResponse(
                status="error",
                intent=result.get("primary_intent", "recipe_create"),
                message=result["error"],
                data=None
            )

        # 응답 구성
        intent = result.get("primary_intent", "recipe_create")
        response_data = {
            "metadata": {
                "entities": result.get("entities", {}),
                "confidence": result.get("confidence", 0.0)
            }
        }

        # 레시피 데이터 추가
        if result.get("recipe_text"):
            recipe_data = json.loads(result["recipe_text"])
            if isinstance(recipe_data, list):
                response_data["recipes"] = recipe_data
            else:
                response_data["recipe"] = recipe_data
            response_data["image_url"] = result.get("image_url")

        return CookingResponse(
            status="success",
            intent=intent,
            data=response_data,
            message=None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")


# app/api/dependencies.py
from typing import Generator
from app.core.container import Container

_container = None

def get_container() -> Container:
    """컨테이너 싱글톤 반환"""
    global _container
    if _container is None:
        _container = Container()
    return _container

def get_create_recipe_use_case() -> Generator:
    """FastAPI Depends용 유스케이스 팩토리"""
    container = get_container()
    yield container.create_recipe_use_case()
```

---

## 2.7 LangGraph 워크플로우 설계

### 현재 문제점

```python
# app/services/cooking_assistant.py (현재)
class CookingAssistant:
    def __init__(self):
        self.graph = self._build_graph()  # LangGraph 워크플로우

    def _classify_intent(self, state):  # 노드 함수
        # 비즈니스 로직 + LLM 호출 + JSON 파싱
        pass

    def _generate_recipe(self, state):  # 노드 함수
        # 비즈니스 로직 + LLM 호출 + JSON 파싱
        pass
```

**문제:**
- 비즈니스 로직과 워크플로우 오케스트레이션이 한 클래스에 섞임
- 노드 함수가 Domain Service 메서드로 존재 (레이어 혼재)
- 테스트 시 LangGraph 의존성 불가피

---

### 해결책: Application Layer에 워크플로우 분리

```
app/
├── domain/
│   └── services/
│       └── cooking_assistant.py      # ✅ 순수 비즈니스 로직만
│
└── application/
    ├── use_cases/
    │   └── create_recipe_use_case.py  # ✅ 워크플로우 실행
    │
    └── workflow/                      # ✅ LangGraph 전용
        ├── __init__.py
        ├── cooking_workflow.py        # StateGraph 정의
        │
        ├── nodes/                     # 노드 (Domain을 호출하는 얇은 래퍼)
        │   ├── __init__.py
        │   ├── intent_classifier_node.py
        │   ├── recipe_generator_node.py
        │   ├── image_generator_node.py
        │   └── recommender_node.py
        │
        └── edges/                     # 조건부 라우팅 로직
            ├── __init__.py
            └── intent_router.py
```

---

### 구현 예시

#### 1. 노드 구현 (얇은 래퍼)

```python
# app/application/workflow/nodes/recipe_generator_node.py
from app.domain.services.cooking_assistant import CookingAssistantService
from app.domain.entities.cooking_state import CookingState
import logging

logger = logging.getLogger(__name__)

class RecipeGeneratorNode:
    """
    레시피 생성 노드 (Domain Service를 호출하는 얇은 래퍼)

    책임:
    - LangGraph 노드 시그니처에 맞게 변환
    - Domain Service에 위임
    - 워크플로우 전용 로직 (로깅, 모니터링 등)

    ❌ 비즈니스 로직은 여기 작성하지 말 것!
    """

    def __init__(self, cooking_assistant: CookingAssistantService):
        """의존성 주입: Domain Service"""
        self.cooking_assistant = cooking_assistant

    async def __call__(self, state: CookingState) -> CookingState:
        """LangGraph 노드 실행 (callable 객체)"""

        # 워크플로우 전용 로직 (선택)
        logger.info(f"[Node:RecipeGenerator] 시작: {state['user_query']}")

        # ✅ Domain Service 호출 (핵심 비즈니스 로직)
        result = await self.cooking_assistant.generate_recipe(state)

        # 워크플로우 전용 로직 (선택)
        logger.info(f"[Node:RecipeGenerator] 완료: {result.get('dish_names', [])}")

        return result


# app/application/workflow/nodes/intent_classifier_node.py
class IntentClassifierNode:
    """의도 분류 노드"""

    def __init__(self, cooking_assistant: CookingAssistantService):
        self.cooking_assistant = cooking_assistant

    async def __call__(self, state: CookingState) -> CookingState:
        logger.info(f"[Node:IntentClassifier] 시작")
        result = await self.cooking_assistant.classify_intent(state)
        logger.info(f"[Node:IntentClassifier] 의도={result['primary_intent']}")
        return result


# app/application/workflow/nodes/image_generator_node.py
class ImageGeneratorNode:
    """이미지 생성 노드"""

    def __init__(self, cooking_assistant: CookingAssistantService):
        self.cooking_assistant = cooking_assistant

    async def __call__(self, state: CookingState) -> CookingState:
        logger.info(f"[Node:ImageGenerator] 시작")
        result = await self.cooking_assistant.generate_image(state)
        logger.info(f"[Node:ImageGenerator] 완료: {result.get('image_url')}")
        return result
```

#### 2. 엣지 구현 (조건부 라우팅)

```python
# app/application/workflow/edges/intent_router.py
from app.domain.entities.cooking_state import CookingState
import logging

logger = logging.getLogger(__name__)

def route_by_intent(state: CookingState) -> str:
    """
    의도에 따라 다음 노드 결정 (조건부 라우팅)

    Args:
        state: 현재 상태

    Returns:
        다음 노드 이름
    """
    intent = state.get("primary_intent", "recipe_create")

    routing_map = {
        "recipe_create": "recipe_generator",
        "recommend": "recommender",
        "question": "question_answerer"
    }

    next_node = routing_map.get(intent, "recipe_generator")

    logger.info(f"[Router] {intent} → {next_node}")

    return next_node


def check_secondary_intents(state: CookingState) -> str:
    """
    Secondary intents 확인 및 라우팅

    Returns:
        다음 노드 이름 또는 "end"
    """
    secondary_intents = state.get("secondary_intents", [])

    if secondary_intents:
        next_intent = secondary_intents[0]
        logger.info(f"[Router] Secondary intent: {next_intent}")

        routing_map = {
            "recipe_create": "recipe_generator",
            "recommend": "recommender",
            "question": "question_answerer"
        }

        return routing_map.get(next_intent, "end")

    logger.info(f"[Router] 모든 intent 완료 → end")
    return "end"
```

#### 3. 워크플로우 구성

```python
# app/application/workflow/cooking_workflow.py
from langgraph.graph import StateGraph, END
from app.domain.entities.cooking_state import CookingState
from app.application.workflow.nodes.intent_classifier_node import IntentClassifierNode
from app.application.workflow.nodes.recipe_generator_node import RecipeGeneratorNode
from app.application.workflow.nodes.image_generator_node import ImageGeneratorNode
from app.application.workflow.nodes.recommender_node import RecommenderNode
from app.application.workflow.edges.intent_router import route_by_intent, check_secondary_intents
import logging

logger = logging.getLogger(__name__)

class CookingWorkflow:
    """
    요리 AI 어시스턴트 워크플로우 (LangGraph)

    책임:
    - 노드 구성
    - 엣지 연결
    - 그래프 컴파일

    ❌ 비즈니스 로직은 여기 작성하지 말 것!
    """

    def __init__(
        self,
        intent_classifier: IntentClassifierNode,
        recipe_generator: RecipeGeneratorNode,
        image_generator: ImageGeneratorNode,
        recommender: RecommenderNode
    ):
        """의존성 주입: 모든 노드"""
        self.intent_classifier = intent_classifier
        self.recipe_generator = recipe_generator
        self.image_generator = image_generator
        self.recommender = recommender

        # 그래프 빌드
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """워크플로우 구성 (오케스트레이션만 담당)"""
        workflow = StateGraph(CookingState)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1. 노드 추가
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        workflow.add_node("classify_intent", self.intent_classifier)
        workflow.add_node("recipe_generator", self.recipe_generator)
        workflow.add_node("image_generator", self.image_generator)
        workflow.add_node("recommender", self.recommender)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2. 시작점
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        workflow.set_entry_point("classify_intent")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3. Primary Intent에 따라 분기
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        workflow.add_conditional_edges(
            "classify_intent",
            route_by_intent,  # 라우팅 함수
            {
                "recipe_generator": "recipe_generator",
                "recommender": "recommender",
                "question_answerer": "question_answerer"
            }
        )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 4. 레시피 생성 후 이미지 생성
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        workflow.add_edge("recipe_generator", "image_generator")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 5. 이미지 생성 후 Secondary Intents 확인
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        workflow.add_conditional_edges(
            "image_generator",
            check_secondary_intents,
            {
                "recipe_generator": "recipe_generator",
                "recommender": "recommender",
                "question_answerer": "question_answerer",
                "end": END
            }
        )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 6. 추천 후 Secondary Intents 확인
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        workflow.add_conditional_edges(
            "recommender",
            check_secondary_intents,
            {
                "recipe_generator": "recipe_generator",
                "recommender": "recommender",
                "question_answerer": "question_answerer",
                "end": END
            }
        )

        logger.info("[Workflow] 그래프 빌드 완료")

        return workflow.compile()

    async def run(self, initial_state: CookingState) -> CookingState:
        """워크플로우 실행"""
        logger.info(f"[Workflow] 시작: {initial_state['user_query']}")
        result = await self.graph.ainvoke(initial_state)
        logger.info(f"[Workflow] 완료")
        return result
```

#### 4. Use Case에서 워크플로우 실행

```python
# app/application/use_cases/create_recipe_use_case.py
from app.application.workflow.cooking_workflow import CookingWorkflow
from app.domain.entities.cooking_state import CookingState
import logging

logger = logging.getLogger(__name__)

class CreateRecipeUseCase:
    """
    레시피 생성 유스케이스

    책임:
    - 초기 상태 생성
    - 워크플로우 실행
    - 결과 반환
    """

    def __init__(self, workflow: CookingWorkflow):
        """의존성 주입: 워크플로우"""
        self.workflow = workflow

    async def execute(self, query: str) -> CookingState:
        """
        레시피 생성 워크플로우 실행

        Args:
            query: 사용자 쿼리

        Returns:
            최종 상태 (CookingState)
        """
        logger.info(f"[UseCase] 실행 시작: {query}")

        # 초기 상태 생성
        initial_state: CookingState = {
            "user_query": query,
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

        # 워크플로우 실행
        result = await self.workflow.run(initial_state)

        logger.info(f"[UseCase] 실행 완료")

        return result
```

#### 5. DI Container 등록

```python
# app/core/container.py
from app.application.workflow.nodes.intent_classifier_node import IntentClassifierNode
from app.application.workflow.nodes.recipe_generator_node import RecipeGeneratorNode
from app.application.workflow.nodes.image_generator_node import ImageGeneratorNode
from app.application.workflow.nodes.recommender_node import RecommenderNode
from app.application.workflow.cooking_workflow import CookingWorkflow

class Container(containers.DeclarativeContainer):
    # ... 기존 코드 ...

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Workflow Nodes (Factory - 가볍고 상태 없음)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    intent_classifier_node = providers.Factory(
        IntentClassifierNode,
        cooking_assistant=cooking_assistant
    )

    recipe_generator_node = providers.Factory(
        RecipeGeneratorNode,
        cooking_assistant=cooking_assistant
    )

    image_generator_node = providers.Factory(
        ImageGeneratorNode,
        cooking_assistant=cooking_assistant
    )

    recommender_node = providers.Factory(
        RecommenderNode,
        cooking_assistant=cooking_assistant
    )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Workflow (Singleton - 그래프 컴파일 비용 절감)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    cooking_workflow = providers.Singleton(
        CookingWorkflow,
        intent_classifier=intent_classifier_node,
        recipe_generator=recipe_generator_node,
        image_generator=image_generator_node,
        recommender=recommender_node
    )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Use Case (Factory - 요청마다 새 인스턴스)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    create_recipe_use_case = providers.Factory(
        CreateRecipeUseCase,
        workflow=cooking_workflow
    )
```

---

### 핵심 원칙

```
┌──────────────────────────────────────────────────────┐
│  LangGraph 워크플로우 설계 원칙                       │
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

## 2.8 프롬프트 관리 (MyBatis 스타일)

### 현재 문제점

```python
# app/adapters/llm/anthropic_adapter.py (현재)
async def classify_intent(self, query: str):
    # 프롬프트가 코드에 하드코딩
    prompt = f"""당신은 요리 AI 어시스턴트입니다.

사용자 입력: {query}

다음 JSON 형식으로 분류하세요:
{{
    "primary_intent": "recipe_create|recommend|question",
    ...
}}"""

    response = self.llm.invoke([HumanMessage(content=prompt)])
    # ...
```

**문제:**
- 프롬프트가 코드에 하드코딩 → 수정 시 코드 재배포 필요
- 버전 관리 어려움
- 프롬프트 엔지니어와 개발자 협업 어려움
- A/B 테스트 불가능
- 다국어 지원 어려움

---

### 해결책: Jinja2 템플릿 + YAML 설정 (MyBatis Mapper 스타일)

```
app/
└── adapters/
    └── llm/
        ├── anthropic_adapter.py
        ├── prompt_loader.py          # 프롬프트 로더 (MyBatis SqlSessionFactory)
        │
        └── prompts/                  # 프롬프트 템플릿 디렉토리
            ├── __init__.py
            ├── config.yaml           # 메타데이터 (model, temperature 등)
            │
            ├── intent_classification.j2    # Jinja2 템플릿
            ├── recipe_generation.j2
            ├── recommendation.j2
            └── question_answering.j2
```

---

### 구현 예시

#### 1. 프롬프트 템플릿 (Jinja2)

```jinja2
{# app/adapters/llm/prompts/intent_classification.j2 #}
당신은 요리 AI 어시스턴트의 의도 분류 전문가입니다.

## 분류 기준
{% for intent_type, description in intent_types.items() %}
{{ loop.index }}. **{{ intent_type }}**: {{ description }}
   - 키워드: {{ intent_keywords[intent_type]|join(", ") }}
{% endfor %}

## 엔티티 추출
{% for entity_name, entity_desc in entities.items() %}
- **{{ entity_name }}**: {{ entity_desc }}
{% endfor %}

## Few-Shot 예시
{% for example in few_shots %}
### 예시 {{ loop.index }}: {{ example.description }}
입력: "{{ example.input }}"
출력:
```json
{{ example.output | tojson(indent=2) }}
```
{% endfor %}

## 현재 사용자 입력
입력: "{{ query }}"

위 기준과 예시에 따라 JSON으로 분류하세요:
```

```jinja2
{# app/adapters/llm/prompts/recipe_generation.j2 #}
사용자가 "{{ query }}"를 요청했습니다.

## 추출된 정보
{% if entities.dishes %}
요리명: {{ entities.dishes|join(", ") }}
{% endif %}
{% if entities.ingredients %}
사용 재료: {{ entities.ingredients|join(", ") }}
{% endif %}
{% if entities.constraints %}
제약 조건:
{% for key, value in entities.constraints.items() %}
- {{ key }}: {{ value }}
{% endfor %}
{% endif %}

## 출력 형식
{% if entities.dishes|length == 1 %}
단일 레시피 JSON:
{
    "title": "요리 이름",
    "ingredients": ["재료1 (분량)", ...],
    "steps": ["1단계 설명", ...],
    "cooking_time": "예상 시간",
    "difficulty": "쉬움|중간|어려움"
}
{% else %}
복수 레시피 JSON 배열:
[
    { "title": "...", "ingredients": [...], ... },
    ...
]
{% endif %}

위 형식에 맞춰 레시피를 생성하세요. 다른 텍스트 없이 JSON만 반환하세요.
```

#### 2. 설정 파일 (YAML)

```yaml
# app/adapters/llm/prompts/config.yaml

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 의도 분류 프롬프트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
intent_classification:
  template: intent_classification.j2
  version: "1.0"

  # LLM 설정
  model: claude-sonnet-4-5-20250929
  temperature: 0.7
  max_tokens: 1024

  # 템플릿 변수
  variables:
    intent_types:
      recipe_create: "특정 요리의 구체적인 조리법 요구"
      recommend: "여러 음식 중 선택지 요구"
      question: "요리 관련 정보 질문"

    intent_keywords:
      recipe_create: ["만드는 법", "레시피", "어떻게 만들어", "조리법", "요리법"]
      recommend: ["추천", "뭐 먹을까", "메뉴 제안", "어떤 음식", "소개"]
      question: ["칼로리", "영양", "얼마나", "?", "뭐야", "차이"]

    entities:
      dishes: "구체적 요리명 (예: [\"김치찌개\", \"된장찌개\"])"
      ingredients: "재료 (예: [\"토마토\", \"달걀\"])"
      cuisine_type: "요리 유형 (예: \"한식\", \"양식\", \"일식\")"
      taste: "맛 선호 (예: [\"매운맛\", \"단맛\"])"
      constraints: "제약조건 (time, difficulty, servings)"
      dietary: "식이제한 (예: [\"비건\", \"저염식\"])"

  # Few-Shot 예시
  few_shots:
    - description: "단일 레시피 요청"
      input: "김치찌개 만드는 법 알려줘"
      output:
        primary_intent: "recipe_create"
        secondary_intents: []
        entities:
          dishes: ["김치찌개"]
        confidence: 0.95

    - description: "복수 레시피 요청"
      input: "김치찌개, 된장찌개, 순두부찌개 레시피 조회"
      output:
        primary_intent: "recipe_create"
        secondary_intents: []
        entities:
          dishes: ["김치찌개", "된장찌개", "순두부찌개"]
          count: 3
        confidence: 0.95

    - description: "복합 의도 (추천 + 레시피)"
      input: "매운 음식 추천해서 그 중 하나 레시피도 보여줘"
      output:
        primary_intent: "recommend"
        secondary_intents: ["recipe_create"]
        entities:
          taste: ["매운맛"]
          count: 3
        confidence: 0.85

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 레시피 생성 프롬프트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
recipe_generation:
  template: recipe_generation.j2
  version: "1.0"

  # LLM 설정
  model: claude-sonnet-4-5-20250929
  temperature: 0.8
  max_tokens: 4096

  # 템플릿 변수 (동적으로 전달되는 것들은 제외)
  variables: {}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 음식 추천 프롬프트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
recommendation:
  template: recommendation.j2
  version: "1.0"

  model: claude-sonnet-4-5-20250929
  temperature: 0.9
  max_tokens: 2048

  variables:
    default_count: 3
```

#### 3. 프롬프트 로더 (MyBatis SqlSessionFactory 역할)

```python
# app/adapters/llm/prompt_loader.py
from jinja2 import Environment, FileSystemLoader, select_autoescape
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

class PromptLoader:
    """
    프롬프트 템플릿 로더 (MyBatis Mapper 역할)

    책임:
    - Jinja2 템플릿 로드 및 렌더링
    - YAML 설정 로드
    - 캐싱
    """

    def __init__(self, templates_dir: str = "app/adapters/llm/prompts"):
        self.templates_dir = Path(templates_dir)

        # Jinja2 환경 설정
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,      # {% %} 이후 공백 제거
            lstrip_blocks=True,    # 블록 앞 공백 제거
            keep_trailing_newline=True
        )

        # 커스텀 필터 추가 (선택)
        self.env.filters['tojson'] = self._custom_json_filter

        # 설정 로드
        self.config = self._load_config()

        logger.info(f"[PromptLoader] 초기화 완료: {self.templates_dir}")

    def _load_config(self) -> Dict[str, Any]:
        """config.yaml 로드"""
        config_path = self.templates_dir / "config.yaml"

        if not config_path.exists():
            logger.warning(f"[PromptLoader] 설정 파일 없음: {config_path}")
            return {}

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        logger.info(f"[PromptLoader] 설정 로드: {len(config)} 프롬프트")
        return config

    def _custom_json_filter(self, value: Any, indent: int = 2) -> str:
        """JSON 직렬화 커스텀 필터"""
        import json
        return json.dumps(value, ensure_ascii=False, indent=indent)

    def render(
        self,
        prompt_name: str,
        version: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        프롬프트 렌더링 (MyBatis select 역할)

        Args:
            prompt_name: 프롬프트 이름 (예: "intent_classification")
            version: 버전 (선택, 기본값: config.yaml의 version)
            **kwargs: 템플릿 변수 (동적으로 전달)

        Returns:
            렌더링된 프롬프트

        Example:
            prompt = loader.render(
                "intent_classification",
                query="김치찌개 만드는 법"
            )
        """
        # 설정에서 메타데이터 가져오기
        prompt_config = self.config.get(prompt_name, {})

        if not prompt_config:
            raise ValueError(f"프롬프트 '{prompt_name}' 설정 없음")

        template_file = prompt_config.get("template")
        if not template_file:
            raise ValueError(f"프롬프트 '{prompt_name}'의 template 필드 없음")

        # 버전 처리 (선택)
        config_version = prompt_config.get("version", "1.0")
        actual_version = version or config_version

        # 설정의 변수와 동적 변수 병합
        # 동적 변수가 우선순위 높음 (덮어쓰기)
        template_vars = {
            **prompt_config.get("variables", {}),
            **kwargs
        }

        # 템플릿 렌더링
        try:
            template = self.env.get_template(template_file)
            rendered = template.render(**template_vars)

            logger.debug(f"[PromptLoader] 렌더링 완료: {prompt_name} (v{actual_version})")

            return rendered

        except Exception as e:
            logger.error(f"[PromptLoader] 렌더링 실패: {prompt_name} - {e}")
            raise

    def get_config(self, prompt_name: str) -> Dict[str, Any]:
        """
        프롬프트 메타데이터 가져오기

        Args:
            prompt_name: 프롬프트 이름

        Returns:
            메타데이터 (model, temperature, max_tokens 등)
        """
        return self.config.get(prompt_name, {})

    def get_llm_params(self, prompt_name: str) -> Dict[str, Any]:
        """
        LLM 파라미터만 추출

        Returns:
            {"model": "...", "temperature": 0.7, "max_tokens": 1024}
        """
        config = self.get_config(prompt_name)

        return {
            "model": config.get("model"),
            "temperature": config.get("temperature", 0.7),
            "max_tokens": config.get("max_tokens", 1024)
        }


# Singleton 인스턴스 (전역 사용)
@lru_cache()
def get_prompt_loader() -> PromptLoader:
    """프롬프트 로더 싱글톤"""
    return PromptLoader()
```

#### 4. Adapter에서 사용

```python
# app/adapters/llm/anthropic_adapter.py
from app.domain.ports.llm_port import ILLMPort
from app.core.config import Settings
from app.adapters.llm.prompt_loader import get_prompt_loader
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from typing import Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

class AnthropicLLMAdapter(ILLMPort):
    """
    Anthropic Claude 어댑터 (프롬프트 로더 사용)
    """

    def __init__(self, settings: Settings):
        """의존성 주입: Settings"""
        self.settings = settings

        # ✅ 프롬프트 로더 (MyBatis SqlSession 역할)
        self.prompt_loader = get_prompt_loader()

        # LLM 클라이언트
        self.llm = ChatAnthropic(
            model=settings.llm_model,
            api_key=settings.anthropic_api_key,
            timeout=settings.llm_timeout
        )

    async def classify_intent(self, query: str) -> Dict[str, Any]:
        """의도 분류 (프롬프트 템플릿 사용)"""

        # ✅ 1. 프롬프트 렌더링 (MyBatis select 호출과 유사)
        prompt = self.prompt_loader.render(
            "intent_classification",
            query=query  # 동적 변수
        )

        # ✅ 2. LLM 파라미터 가져오기
        llm_params = self.prompt_loader.get_llm_params("intent_classification")

        logger.info(f"[Anthropic] 의도 분류 요청: {query}")
        logger.debug(f"[Prompt]\n{prompt[:200]}...")  # 일부만 로깅

        try:
            # ✅ 3. LLM 호출 (설정값 사용)
            response = self.llm.invoke(
                [HumanMessage(content=prompt)],
                temperature=llm_params.get("temperature", 0.7),
                max_tokens=llm_params.get("max_tokens", 1024)
            )

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
        """레시피 생성 (프롬프트 템플릿 사용)"""

        # ✅ 프롬프트 렌더링 (entities도 템플릿 변수로 전달)
        prompt = self.prompt_loader.render(
            "recipe_generation",
            query=query,
            entities=entities  # Jinja2 템플릿에서 사용
        )

        llm_params = self.prompt_loader.get_llm_params("recipe_generation")

        logger.info(f"[Anthropic] 레시피 생성 요청: {query}")

        try:
            response = self.llm.invoke(
                [HumanMessage(content=prompt)],
                temperature=llm_params.get("temperature", 0.8),
                max_tokens=llm_params.get("max_tokens", 4096)
            )

            result_json = self._extract_json(response.content)
            result = json.loads(result_json)

            logger.info(f"[Anthropic] 레시피 생성 완료")

            return result

        except Exception as e:
            logger.error(f"[Anthropic] 레시피 생성 실패: {str(e)}")
            raise

    # ... 나머지 메서드도 동일한 패턴
```

---

### 장점

#### 1. 관심사 분리
```
코드 (Python)           프롬프트 (Jinja2 + YAML)
   ↓                          ↓
비즈니스 로직            프롬프트 엔지니어링
```

#### 2. 수정 용이성
```python
# ❌ 기존: 프롬프트 수정 시 코드 재배포
prompt = f"당신은 요리 AI..."  # 코드 수정 → 재배포

# ✅ 개선: 템플릿 파일만 수정 (재배포 불필요 - 핫 리로드 가능)
# intent_classification.j2 수정 → 즉시 반영
```

#### 3. 버전 관리
```yaml
intent_classification:
  version: "1.0"  # Git으로 버전 관리

# 또는
prompts/
├── intent_classification/
│   ├── v1.0.j2
│   ├── v1.1.j2  # A/B 테스트
│   └── v2.0.j2
```

#### 4. 다국어 지원
```
prompts/
├── ko/
│   ├── config.yaml
│   └── intent_classification.j2
└── en/
    ├── config.yaml
    └── intent_classification.j2
```

#### 5. A/B 테스트
```python
# 실험 버전 렌더링
prompt_v1 = loader.render("intent_classification", version="1.0", query=query)
prompt_v2 = loader.render("intent_classification", version="2.0", query=query)

# 트래픽 50/50 분배
if random.random() < 0.5:
    result = await llm.invoke(prompt_v1)
else:
    result = await llm.invoke(prompt_v2)
```

---

### 추가 고려사항

#### 1. 프롬프트 캐싱 (성능 최적화)

```python
from functools import lru_cache

class PromptLoader:
    @lru_cache(maxsize=100)
    def _load_template(self, template_name: str):
        """템플릿 캐싱"""
        return self.env.get_template(template_name)
```

#### 2. 프롬프트 검증

```python
def validate_prompt(self, prompt_name: str) -> bool:
    """프롬프트 유효성 검증"""
    config = self.get_config(prompt_name)

    # 필수 필드 확인
    if not config.get("template"):
        return False

    # 템플릿 파일 존재 확인
    template_path = self.templates_dir / config["template"]
    if not template_path.exists():
        return False

    return True
```

#### 3. 프롬프트 모니터링

```python
import time

class PromptLoader:
    def render(self, prompt_name: str, **kwargs) -> str:
        start_time = time.time()

        rendered = template.render(**template_vars)

        # 메트릭 수집
        duration = time.time() - start_time
        logger.info(f"[Metrics] {prompt_name} 렌더링: {duration:.3f}초")

        return rendered
```

---

## 3. 테스트 개선

### 3.1 단위 테스트 (Port 모킹)

```python
# tests/unit/domain/test_cooking_assistant.py
import pytest
from unittest.mock import AsyncMock, Mock
from app.domain.services.cooking_assistant import CookingAssistantService
from app.domain.ports.llm_port import ILLMPort
from app.domain.ports.image_port import IImagePort
from app.domain.entities.cooking_state import CookingState

@pytest.fixture
def mock_llm_port():
    """LLM Port 모킹 (어댑터 구현체 몰라도 됨)"""
    mock = Mock(spec=ILLMPort)
    mock.classify_intent = AsyncMock(return_value={
        "primary_intent": "recipe_create",
        "secondary_intents": [],
        "entities": {"dishes": ["김치찌개"]},
        "confidence": 0.95
    })
    mock.generate_recipe = AsyncMock(return_value={
        "title": "김치찌개",
        "ingredients": ["김치 200g", "돼지고기 100g"],
        "steps": ["1단계", "2단계"],
        "cooking_time": "30분",
        "difficulty": "중간"
    })
    return mock

@pytest.fixture
def mock_image_port():
    """Image Port 모킹"""
    mock = Mock(spec=IImagePort)
    mock.generate_prompt = Mock(return_value="professional food photo...")
    mock.generate_image = AsyncMock(return_value="https://example.com/image.jpg")
    return mock

@pytest.mark.asyncio
async def test_cooking_assistant_classify_intent(mock_llm_port, mock_image_port):
    """의도 분류 테스트 (도메인 로직만 테스트)"""

    # Given: 도메인 서비스 생성 (모킹된 Port 주입)
    service = CookingAssistantService(
        llm_port=mock_llm_port,
        image_port=mock_image_port
    )

    state: CookingState = {
        "user_query": "김치찌개 만드는 법",
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

    # When: 의도 분류 실행
    result = await service.classify_intent(state)

    # Then: 결과 검증
    assert result["primary_intent"] == "recipe_create"
    assert result["confidence"] == 0.95
    assert "김치찌개" in result["entities"]["dishes"]

    # Port 호출 검증
    mock_llm_port.classify_intent.assert_called_once_with("김치찌개 만드는 법")

@pytest.mark.asyncio
async def test_cooking_assistant_generate_recipe(mock_llm_port, mock_image_port):
    """레시피 생성 테스트"""

    # Given
    service = CookingAssistantService(
        llm_port=mock_llm_port,
        image_port=mock_image_port
    )

    state: CookingState = {
        "user_query": "김치찌개 만드는 법",
        "primary_intent": "recipe_create",
        "secondary_intents": [],
        "entities": {"dishes": ["김치찌개"]},
        "confidence": 0.95,
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

    # When
    result = await service.generate_recipe(state)

    # Then
    assert result["dish_names"] == ["김치찌개"]
    assert result["error"] is None

    # Port 호출 검증
    mock_llm_port.generate_recipe.assert_called_once()
```

### 3.2 어댑터 테스트

```python
# tests/unit/adapters/test_anthropic_adapter.py
import pytest
from unittest.mock import patch, Mock
from app.adapters.llm.anthropic_adapter import AnthropicLLMAdapter
from app.core.config import Settings

@pytest.fixture
def settings():
    """테스트용 설정"""
    return Settings(
        anthropic_api_key="test_key",
        replicate_api_token="test_token",
        llm_model="claude-sonnet-4-5-20250929"
    )

@pytest.mark.asyncio
async def test_anthropic_adapter_classify_intent(settings):
    """Anthropic 어댑터 의도 분류 테스트"""

    # Given: 어댑터 생성
    adapter = AnthropicLLMAdapter(settings)

    # Mock LLM 응답
    with patch.object(adapter.llm, 'invoke') as mock_invoke:
        mock_response = Mock()
        mock_response.content = '''```json
        {
            "primary_intent": "recipe_create",
            "secondary_intents": [],
            "entities": {"dishes": ["김치찌개"]},
            "confidence": 0.95
        }
        ```'''
        mock_invoke.return_value = mock_response

        # When: 의도 분류 실행
        result = await adapter.classify_intent("김치찌개 만드는 법")

        # Then: 결과 검증
        assert result["primary_intent"] == "recipe_create"
        assert result["confidence"] == 0.95
        mock_invoke.assert_called_once()
```

---

## 4. 마이그레이션 전략 (점진적)

### Phase 1: 설정 중앙화 (1일)
- [ ] `app/core/config.py` 생성
- [ ] 환경 변수를 Settings로 이관
- [ ] 기존 서비스에서 Settings 사용

### Phase 2: Port 정의 (1일)
- [ ] `app/domain/ports/llm_port.py` 생성
- [ ] `app/domain/ports/image_port.py` 생성
- [ ] 인터페이스 메서드 정의

### Phase 3: Adapter 분리 (2일)
- [ ] `app/adapters/llm/anthropic_adapter.py` 생성
- [ ] `app/adapters/image/replicate_adapter.py` 생성
- [ ] 기존 서비스 코드를 어댑터로 이동
- [ ] Port 인터페이스 구현

### Phase 4: Domain Service 리팩토링 (2일)
- [ ] `app/domain/services/cooking_assistant.py` 생성
- [ ] 비즈니스 로직을 도메인 서비스로 이동
- [ ] Port에만 의존하도록 수정

### Phase 5: Use Case 분리 (1일)
- [ ] `app/application/use_cases/create_recipe_use_case.py` 생성
- [ ] LangGraph 워크플로우를 유스케이스로 이동

### Phase 6: DI Container 구축 (1일)
- [ ] `dependency-injector` 라이브러리 추가
- [ ] `app/core/container.py` 생성
- [ ] 모든 의존성 등록

### Phase 7: API Layer DI 적용 (1일)
- [ ] `app/api/dependencies.py` 생성
- [ ] `routes.py`에서 Depends 사용
- [ ] 모듈 레벨 인스턴스 제거

### Phase 8: 테스트 작성 (2일)
- [ ] 도메인 서비스 단위 테스트
- [ ] 어댑터 단위 테스트
- [ ] 통합 테스트

### Phase 9: 문서화 및 배포 (1일)
- [ ] CLAUDE.md 업데이트
- [ ] 아키텍처 다이어그램 작성
- [ ] 프로덕션 배포

---

## 5. 의존성 추가

```txt
# requirements.txt에 추가

# DI & 설정
dependency-injector[yaml]==4.41.0
pydantic-settings==2.0.3

# 프롬프트 관리
Jinja2==3.1.2
PyYAML==6.0.1

# 테스트
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-mock==3.12.0

# 워크플로우 (이미 사용 중)
langgraph==0.0.20
```

---

## 6. 기대 효과

### 6.1 명확한 레이어 분리
- Domain: 순수 비즈니스 로직 (외부 몰라도 됨)
- Adapter: 외부 시스템 통신 (교체 가능)
- Application: 워크플로우 조합
- Presentation: HTTP 요청/응답

### 6.2 의존성 역전
```
기존: Domain → Anthropic API (잘못된 방향)
개선: Domain → Port ← Adapter → Anthropic API (올바른 방향)
```

### 6.3 테스트 용이성
- Port 모킹만으로 도메인 로직 단위 테스트
- 실제 API 호출 없이 테스트 가능
- 테스트 속도 대폭 향상

### 6.4 확장성
- Anthropic → OpenAI: `OpenAILLMAdapter` 추가만으로 가능
- 멀티 LLM 전략: 여러 어댑터를 동시 사용
- 새로운 기능 추가 시 기존 코드 수정 최소화

### 6.5 유지보수성
- 레이어별 책임 명확
- 변경 영향 범위 최소화
- 코드 이해도 향상

---

## 7. 주의 사항

### 7.1 과도한 추상화 지양
- 현재 필요한 만큼만 Port 정의
- 미래를 위한 불필요한 추상화 금지
- YAGNI 원칙 준수

### 7.2 점진적 마이그레이션
- Big Bang 방식 지양
- 기존 코드와 병행 운영
- 단계별 검증 후 다음 단계 진행

### 7.3 성능 고려
- DI 컨테이너 오버헤드 모니터링
- 싱글톤 vs 팩토리 적절히 선택
- 불필요한 객체 생성 최소화

---

## 8. 참고 자료

### 아키텍처
- [Hexagonal Architecture (Ports & Adapters)](https://alistair.cockburn.us/hexagonal-architecture/)
- [Clean Architecture - Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design - Eric Evans](https://domainlanguage.com/ddd/)

### Python DI
- [dependency-injector 공식 문서](https://python-dependency-injector.ets-labs.org/)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

### 원칙
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Dependency Inversion Principle](https://en.wikipedia.org/wiki/Dependency_inversion_principle)
- [Separation of Concerns](https://en.wikipedia.org/wiki/Separation_of_concerns)

---

## 9. 체크리스트

### 설계
- [x] 헥사고날 아키텍처 설계 완료
- [x] Port 인터페이스 정의
- [x] Adapter 구조 정의
- [x] Domain Service 구조 정의
- [x] Use Case 구조 정의

### 구현
- [ ] Phase 1: 설정 중앙화
- [ ] Phase 2: Port 정의
- [ ] Phase 3: Adapter 분리
- [ ] Phase 4: Domain Service 리팩토링
- [ ] Phase 5: Use Case 분리
- [ ] Phase 6: DI Container 구축
- [ ] Phase 7: API Layer DI 적용
- [ ] Phase 8: 테스트 작성

### 검증
- [ ] 단위 테스트 통과
- [ ] 통합 테스트 통과
- [ ] 성능 테스트 (기존 대비 성능 저하 없음)
- [ ] 코드 리뷰 완료

### 문서화
- [ ] 아키텍처 다이어그램 작성
- [ ] CLAUDE.md 업데이트
- [ ] README.md 업데이트
- [ ] API 문서 업데이트

### 배포
- [ ] 스테이징 환경 배포
- [ ] 프로덕션 배포
- [ ] 모니터링 설정

---

**작성일:** 2025-11-05
**작성자:** Claude Code
**버전:** 2.0 (Hexagonal Architecture)
**변경 사항:** DI 기반 → 헥사고날 아키텍처 (Ports & Adapters) 전환