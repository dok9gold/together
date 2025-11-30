# Piri Framework

FastAPI + LangGraph 기반 AI Agent 애플리케이션을 빠르게 구축하는 통합 프레임워크입니다.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.120+-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-orange.svg)](https://github.com/langchain-ai/langgraph)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Hexagonal Architecture, DDD, 데코레이터 기반 의존성 주입, 프롬프트 관리를 기본 제공하는 AI Agent 프레임워크

---

## 핵심 특징

### 아키텍처
- **Hexagonal Architecture (Port-Adapter 패턴)** - 외부 시스템 의존성을 인터페이스로 분리하여 교체 가능
- **DDD (Domain-Driven Design)** - 도메인 중심 설계로 비즈니스 로직과 인프라 분리
- **데코레이터 기반 DI** - `@singleton`, `@inject` 데코레이터로 명시적 의존성 관리

### 핵심 컴포넌트
- **프롬프트 관리 시스템** - YAML 기반 프롬프트 버전 관리 및 템플릿
- **JWT 인증** - 선택적/필수 인증 전략 지원
- **LangGraph Workflow** - 복잡한 AI Agent 워크플로우 오케스트레이션
- **멀티 Adapter** - LLM, Image, VectorStore 등 다양한 어댑터 교체 가능

---

## 빠른 시작

### 사전 요구사항

- Python 3.9 이상
- pip 패키지 매니저

### 설치

```bash
# 저장소 클론
git clone https://github.com/your-username/born.git
cd born

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집하여 API 키 추가
```

### 실행

```bash
# 개발 서버 실행 (핫 리로드 지원)
python -m app.main

# 또는 uvicorn 직접 사용
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

서버가 실행되면 http://localhost:8000 에서 접속 가능합니다.

---

## 프레임워크 아키텍처

### 계층 구조 (Hexagonal Architecture + DDD)

```
Routes (Presentation Layer)
  ↓ CookingRequest (DTO)
UseCase (Application Layer)
  ↓ CookingState (Domain Entity)
Workflow (LangGraph Orchestration)
  ↓ 노드 실행
Domain Services (Business Logic)
  ↓ Port 인터페이스 호출
Adapters (Infrastructure)
  ↓ 외부 API 통신
External Systems (Anthropic, Replicate)
```

### 의존성 주입 (Decorator 기반)

Piri Framework는 데코레이터 기반 DI를 사용합니다:

```python
# Domain Service
from app.core.decorators import singleton, inject

@singleton  # Lifecycle 선언
class CookingAssistantService:
    @inject  # 타입 힌트 기반 자동 주입
    def __init__(self, llm_port: ILLMPort, image_port: IImagePort):
        self.llm_port = llm_port
        self.image_port = image_port
```

**Port → Adapter 바인딩 (중앙 관리)**:
```python
# app/core/module.py
class CookingModule(Module):
    @provider
    def provide_llm_adapter(self, settings: Settings, prompt_loader: PromptLoader) -> ILLMPort:
        return AnthropicLLMAdapter(settings, prompt_loader)  # 교체 가능!
```

**생명주기**:
- `@singleton` - 애플리케이션 전체에서 하나의 인스턴스 공유
- `@inject` - 타입 힌트를 통한 자동 의존성 주입
- 데코레이터 없음 - Factory 패턴 (요청마다 새 인스턴스)

---

## 프로젝트 구조

```
app/
├── core/                      # 프레임워크 인프라
│   ├── config.py             # 설정 관리
│   ├── auth.py               # JWT 인증
│   ├── prompt_loader.py      # 프롬프트 시스템
│   ├── decorators.py         # DI 데코레이터
│   └── module.py             # Port-Adapter 바인딩 (템플릿 특화)
│
├── domain/                    # 도메인 계층
│   ├── entities/             # 도메인 엔티티
│   ├── services/             # 도메인 서비스 (@singleton)
│   ├── ports/                # Port 인터페이스
│   ├── exceptions.py         # 도메인 예외
│   └── response_codes.py     # 응답 코드 (도메인 특화)
│
├── adapters/                  # 어댑터 계층 (@singleton)
│   ├── llm/                  # LLM Adapters (Anthropic, OpenAI 등)
│   └── image/                # Image Adapters (Replicate, DALLE 등)
│
├── application/               # 애플리케이션 계층
│   ├── use_cases/            # Use Cases (@inject, Factory)
│   └── workflow/             # LangGraph Workflows
│       ├── nodes/            # Workflow Nodes (@inject, Factory)
│       ├── edges/            # Routing Logic
│       └── cooking_workflow.py  # Workflow (@singleton)
│
├── api/                       # API 계층
│   ├── routes.py             # 엔드포인트
│   └── dependencies.py       # FastAPI Dependencies (Injector 연동)
│
├── models/                    # DTO 모델
│   └── schemas.py            # Pydantic DTO 정의
│
├── prompts/                   # 프롬프트 템플릿
│   └── *.yaml                # YAML 기반 프롬프트
│
└── main.py                    # FastAPI 앱 진입점
```

---

## 설계 원칙

### 1. Port-Adapter 패턴
외부 시스템 의존성을 Port 인터페이스로 추상화:
```python
# Port (인터페이스)
class ILLMPort(ABC):
    @abstractmethod
    async def classify_intent(self, query: str) -> Dict[str, Any]:
        pass

# Adapter (구현체 - 교체 가능)
@singleton
class AnthropicLLMAdapter(ILLMPort):
    async def classify_intent(self, query: str) -> Dict[str, Any]:
        # Anthropic API 호출
        ...
```

### 2. UseCase = Spring의 Service
- DTO 반환 담당
- Domain → DTO 변환 수행
- routes는 1줄로 단순 호출만

### 3. Adapter = 연결자
- 비즈니스 로직 없음
- HTTP 통신 및 파싱만 수행
- Port 인터페이스 구현

### 4. Workflow = 오케스트레이션
- 노드 실행 순서만 정의
- 비즈니스 로직은 Domain Services로 위임

---

## API 문서

서버 실행 후 브라우저에서 확인:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 기술 스택

- **Framework Core**: Piri Framework (FastAPI + LangGraph)
- **AI/LLM**: Anthropic Claude Sonnet 4.5 (Adapter 교체 가능)
- **Workflow Engine**: LangGraph
- **Image Generation**: Replicate Flux Schnell (Adapter 교체 가능)
- **Authentication**: JWT (python-jose)
- **Dependency Injection**: injector (decorator 기반)
- **Prompt Management**: YAML + Jinja2

---

## 테스트

### 테스트 구조
```
tests/
├── unit/                      # 단위 테스트 (Mock)
│   ├── test_cooking_assistant.py  # Domain Service Mock
│   ├── test_anthropic_adapter.py  # LLM Adapter Mock
│   └── test_replicate_adapter.py  # Image Adapter Mock
├── integration/               # 통합 테스트
│   └── test_workflow.py       # Workflow 통합
└── e2e/                       # E2E 테스트
    └── test_api.py            # API 엔드포인트
```

### 테스트 실행
```bash
# 전체 테스트
pytest

# 커버리지 포함
pytest --cov=app --cov-report=html
```

---

## 문서

- **[CLAUDE.md](CLAUDE.md)** - Claude Code 가이드
- **[docs/FRAMEWORK.md](docs/FRAMEWORK.md)** - Piri Framework 전체 가이드
- **[docs/TODO.md](docs/TODO.md)** - 아키텍처 설계 및 TODO
- **[docs/AUTH_TEST_GUIDE.md](docs/AUTH_TEST_GUIDE.md)** - 인증 테스트 가이드
- **[docs/SUMMARY.md](docs/SUMMARY.md)** - 문서 요약

---

## Cooking Assistant 템플릿

이 저장소는 Piri Framework의 **첫 번째 템플릿**인 한국어 요리 AI 어시스턴트입니다.

### 템플릿 기능
- **레시피 생성** - 상세한 조리법과 음식 이미지 자동 생성
- **음식 추천** - 선호도 기반 맞춤형 메뉴 제안
- **요리 Q&A** - 요리 관련 질문에 대한 정확한 답변
- **한국어 네이티브 지원** - 한국 요리에 최적화

### API 사용 예시

**레시피 생성**
```bash
curl -X POST http://localhost:8000/api/cooking \
  -H "Content-Type: application/json" \
  -d '{"query": "김치찌개 만드는 법"}'
```

**음식 추천**
```bash
curl -X POST http://localhost:8000/api/cooking \
  -H "Content-Type: application/json" \
  -d '{"query": "매운 음식 추천해줘"}'
```

**요리 질문**
```bash
curl -X POST http://localhost:8000/api/cooking \
  -H "Content-Type: application/json" \
  -d '{"query": "김치찌개 칼로리는 얼마나 돼?"}'
```

### 인증 사용 (선택적)
```bash
# 토큰 생성
python3 scripts/generate_token.py user123

# 인증과 함께 요청
curl -X POST http://localhost:8000/api/cooking \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"query": "김치찌개 만드는 법"}'
```

---

## 향후 템플릿 계획

- `chatbot` - 기본 대화형 챗봇
- `rag-qa` - RAG 기반 문서 Q&A
- `multimodal` - 멀티모달 AI 앱
- `conversational` - 대화 히스토리 관리

---

## 기여

Piri Framework와 이 템플릿에 기여하고 싶으시다면:

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일 참조

---

## 참고

- [Anthropic Claude](https://www.anthropic.com/) - LLM API
- [Replicate](https://replicate.com/) - 이미지 생성 API
- [LangGraph](https://github.com/langchain-ai/langgraph) - Workflow Engine
- [FastAPI](https://fastapi.tiangolo.com/) - Web Framework

---

## 문의

Piri Framework나 이 템플릿에 대한 질문이나 제안이 있으시면 이슈를 생성해주세요.

**프로젝트 링크**: [https://github.com/your-username/born](https://github.com/your-username/born)
