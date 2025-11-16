# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

PyAi는 FastAPI, Claude (Anthropic), LangGraph로 구축된 한국어 요리 AI 어시스턴트 서비스입니다. RESTful API를 통해 지능형 레시피 생성, 음식 추천, 요리 관련 Q&A를 제공합니다.

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

# 인증과 함께 요청 (JWT 토큰 생성 후)
python3 scripts/generate_token.py user123
curl -X POST http://localhost:8000/api/cooking \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"query": "김치찌개 만드는 법"}'

# 헬스 체크
curl http://localhost:8000/api/health
```

---

## 아키텍처 개요

### 계층별 책임 (Hexagonal Architecture + DDD)

```
Routes (Presentation)
  ↓ CookingRequest (DTO)
UseCase (Application)
  ↓ CookingState (Domain Entity)
Workflow (LangGraph Orchestration)
  ↓ 노드 실행
Domain Services (비즈니스 로직)
  ↓ Port 인터페이스 호출
Adapters (Infrastructure)
  ↓ 외부 API 통신
External Systems (Anthropic, Replicate)
```

#### 1. **Routes** (`app/api/routes.py`)
- 엔드포인트 정의만 수행 (비즈니스 로직 없음)
- UseCase 호출 후 DTO 반환
- 인증은 `Depends(get_optional_user)` Dependency로 처리

**중요**: routes.py는 **46줄**로 매우 간결함. JSON 파싱/변환 로직은 모두 UseCase로 이동됨.

#### 2. **UseCase** (`app/application/use_cases/`)
- **Spring의 Service와 동일한 역할**
- Workflow 실행 OR 직접 비즈니스 로직 구현
- **Domain Entity → DTO 변환** (`_to_dto()` 메서드)
- 에러 핸들링 및 응답 생성

**중요**: UseCase가 DTO를 반환하므로 routes는 1줄로 단순 호출만 수행.

#### 3. **Workflow** (`app/application/workflow/cooking_workflow.py`)
- LangGraph StateGraph 기반 오케스트레이션
- 노드 구성 및 조건부 분기 정의
- **비즈니스 로직은 여기 작성 금지** → Domain Services에 위임

**워크플로우 실행 순서**:
```
1. classify_intent (의도 분류)
   ↓
2. route_by_intent (의도별 분기)
   ├─ recipe_create → recipe_generator → image_generator
   ├─ recommend → recommender
   └─ question → question_answerer
   ↓
3. check_secondary_intents (부가 의도 처리)
   ↓
4. END
```

#### 4. **Workflow Nodes** (`app/application/workflow/nodes/`)
- **"언제" 서비스 호출할지** 결정
- **"어떤 데이터" 전달할지** 결정
- 결과 검증 및 상태 업데이트
- SQL, LLM, 외부 API 모두 호출 가능

#### 5. **Domain Services** (`app/domain/services/`)
- Adapter 호출 전/후 처리
- 비즈니스 규칙 검증
- 도메인 지식 캡슐화

**중요**: 프롬프트 생성, LLM 호출, 응답 파싱 등 실제 비즈니스 로직이 위치.

#### 6. **Adapters** (`app/adapters/`)
- **Port 인터페이스 구현체**
- HTTP 통신, API 포맷 맞추기, 응답 파싱
- **비즈니스 로직 없음** (단순 연결자 역할)

예시:
- `AnthropicLLMAdapter`: Claude API 호출
- `ReplicateImageAdapter`: Replicate API 호출

---

### 핵심 워크플로우 (LangGraph 기반)

애플리케이션은 `app/services/cooking_assistant.py`에 구현된 상태 기반 그래프 워크플로우를 사용합니다:

1. **의도 분류** - 사용자 쿼리를 분석하여 다음을 결정:
   - `recipe_create`: 상세한 요리 레시피 생성
   - `recommend`: 선호도에 따른 요리 추천
   - `question`: 요리 관련 질문 답변

2. **엔티티 추출** - 구조화된 데이터 추출:
   - dishes (구체적인 요리명)
   - ingredients, cuisine_type, taste (재료, 요리 유형, 맛 선호)
   - constraints (시간, 난이도, 인분)
   - dietary (식이 제한사항)

3. **다중 의도 지원** - 주 의도와 부가 의도가 있는 복잡한 쿼리 처리 (예: "매운 음식 추천하고 그 중 하나 레시피도 보여줘")

4. **응답 생성** - Claude Sonnet이 의도와 엔티티를 기반으로 상황별 응답 생성

5. **이미지 생성** - Replicate의 Flux Schnell 모델을 통한 음식 사진 생성 (선택사항)

---

### 상태 관리

`CookingState` TypedDict가 추적하는 항목:
- 사용자 쿼리 및 추출된 의도/엔티티
- 생성된 레시피, 추천, 또는 답변
- 이미지 생성 프롬프트 및 URL
- **user_id** (인증된 경우, 개인화 기능용)
- 우아한 성능 저하를 위한 오류 상태

**Factory 패턴**: `create_initial_state(query: str)` 함수로 초기 상태 생성.

---

### 의존성 주입 (DI Container)

`app/core/container.py`에서 모든 컴포넌트 등록:

```python
# Spring의 ApplicationContext와 동일한 역할
class Container:
    # Singleton: 애플리케이션 전체 공유
    config = Singleton(get_settings)
    llm_adapter = Singleton(AnthropicLLMAdapter)
    cooking_workflow = Singleton(CookingWorkflow)

    # Factory: 요청마다 새 인스턴스
    create_recipe_use_case = Factory(CreateRecipeUseCase)
```

**의존성 흐름**:
```
Container
  ↓
Adapters (Singleton)
  ↓
Domain Services (Singleton)
  ↓
Workflow Nodes (Factory)
  ↓
Workflow (Singleton)
  ↓
UseCase (Factory)
  ↓
Routes (Depends)
```

---

### Response DTO 구조

**타입 안전성 확보**:
```python
# 의도별 명확한 DTO
RecipeResponse         # recipe_create
RecommendationResponse # recommend
QuestionResponse       # question
ErrorResponse          # 에러

# Union Type
CookingResponse = Union[RecipeResponse, RecommendationResponse, QuestionResponse, ErrorResponse]
```

**응답 코드 중앙 관리**: `app/core/response_codes.py`

---

## 응답 형식

모든 응답은 의도별 데이터를 포함한 통합 구조를 따릅니다:

```json
{
  "status": "success|error",
  "code": "RECIPE_CREATED|RECOMMENDATION_SUCCESS|...",
  "intent": "recipe_create|recommend|question",
  "data": {
    // 의도별 데이터 (타입 안전)
    "metadata": {
      "entities": {...},
      "confidence": 0.95,
      "secondary_intents_processed": [...]
    }
  },
  "message": null 또는 오류_메시지
}
```

---

## 인증 시스템 (JWT)

### 구조
- **AuthService** (`app/core/auth.py`): JWT 토큰 생성 및 검증
- **Dependency 함수** (`app/api/dependencies.py`):
  - `get_current_user()`: 필수 인증 (토큰 없으면 401)
  - `get_optional_user()`: 선택적 인증 (토큰 없어도 통과)

### 현재 구현
```python
# routes.py - 선택적 인증
user_id: Optional[str] = Depends(get_optional_user)

# UseCase에서 user_id 활용
initial_state["user_id"] = user_id  # 향후 개인화 기능용
```

### 토큰 생성
```bash
# 스크립트 사용
python3 scripts/generate_token.py user123

# Python 직접
from app.core.auth import AuthService
auth = AuthService(secret_key=settings.secret_key)
token = auth.create_access_token(user_id="user123")
```

---

## 환경 변수

`.env`에 필수:
```env
ANTHROPIC_API_KEY=sk-ant-...
REPLICATE_API_TOKEN=r8_...
SECRET_KEY=your-secret-key-here  # JWT 인증용
```

---

## 주요 기능

- **한국어 지원** - 한국어 레시피 생성 및 이해 네이티브 지원
- **우아한 성능 저하** - 이미지 생성이 실패해도 레시피 반환
- **무상태 설계** - 데이터베이스 불필요
- **90초 타임아웃** - LLM 및 이미지 생성 지연 시간 수용
- **구조화된 로깅** - 의도 분류 및 워크플로우 실행 디버깅을 위한 상세 로깅
- **JWT 인증** - 선택적 사용자 인증 (개인화 기능 확장 가능)

---

## 설계 원칙

### 1. UseCase = Spring의 Service
- DTO 반환 담당
- Domain → DTO 변환 수행
- routes는 1줄로 단순 호출만

### 2. Adapter = 연결자
- 비즈니스 로직 없음
- HTTP 통신 및 파싱만 수행

### 3. Workflow = 오케스트레이션
- 노드 실행 순서만 정의
- 비즈니스 로직은 Domain Services로 위임

### 4. 복잡도별 패턴 선택
- **Level 1**: UseCase에서 직접 처리 (간단한 조회)
- **Level 2**: UseCase + 여러 Service (중간 복잡도)
- **Level 3**: UseCase + Workflow (복잡한 AI 오케스트레이션) ← 현재

---

## API 문서

서버 실행 시:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 참고 문서

- **인증 테스트**: `docs/AUTH_TEST_GUIDE.md`
- **TODO 및 아키텍처 설계**: `docs/TODO.md`
- **프레임워크 가이드**: `docs/FRAMEWORK.md`
- **문서 요약**: `docs/SUMMARY.md`
- **프롬프트**: `app/prompts/*.yaml`
