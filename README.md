# Piri Framework

FastAPI + LangGraph 기반 AI Agent 애플리케이션을 빠르게 구축하는 통합 프레임워크

Hexagonal Architecture, DDD, 데코레이터 기반 의존성 주입, 프롬프트 관리를 기본 제공합니다.

**이 레포지토리는 Piri Framework의 첫 번째 템플릿인 `cooking-assistant` 예제를 포함합니다.**

---

## 핵심 특징

### 아키텍처
- Hexagonal Architecture - Port-Adapter 패턴으로 외부 시스템 교체 가능
- Domain-Driven Design - 비즈니스 로직과 인프라 분리
- 데코레이터 기반 DI - @singleton, @inject로 명시적 의존성 관리

### 핵심 컴포넌트
- 프롬프트 관리 - YAML 기반 버전 관리 및 템플릿
- JWT 인증 - 선택적/필수 인증 전략
- LangGraph Workflow - AI Agent 워크플로우 오케스트레이션
- 멀티 Adapter - LLM, Image, VectorDB 등 교체 가능

---

## 빠른 시작

### 설치

```bash
git clone https://github.com/your-username/born.git
cd born
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env 파일 편집하여 API 키 추가
```

### 실행

```bash
# 가상환경 활성화
source venv/bin/activate

# 서버 실행 (핫 리로드 포함)
uvicorn app.main:app --reload
```

http://localhost:8000 에서 접속 가능

종료: Ctrl+C

---

## 프레임워크 아키텍처

### 계층 구조

```
Routes → UseCase → Workflow → Domain Services → Adapters → External Systems
```

### 의존성 주입

데코레이터 기반 DI 사용:

```python
from app.core.decorators import singleton, inject

@singleton
class CookingAssistantService:
    @inject
    def __init__(self, llm_port: ILLMPort, image_port: IImagePort):
        self.llm_port = llm_port
        self.image_port = image_port
```

Port-Adapter 바인딩은 중앙에서 관리:

```python
# app/core/module.py
class CookingModule(Module):
    @provider
    def provide_llm_adapter(self, settings: Settings) -> ILLMPort:
        return AnthropicLLMAdapter(settings)  # 교체 가능
```

생명주기:
- @singleton: 전체 공유
- @inject: 자동 주입
- 데코레이터 없음: Factory 패턴

---

## 프로젝트 구조

```
app/
├── core/                      # 프레임워크 인프라
│   ├── config.py             # 설정 관리
│   ├── auth.py               # JWT 인증
│   ├── prompt_loader.py      # 프롬프트 시스템
│   ├── decorators.py         # DI 데코레이터
│   └── module.py             # Port-Adapter 바인딩
│
├── domain/                    # 도메인 계층
│   ├── entities/             # 도메인 엔티티
│   ├── services/             # 도메인 서비스
│   ├── ports/                # Port 인터페이스
│   └── exceptions.py         # 도메인 예외
│
├── adapters/                  # 어댑터 계층
│   ├── llm/                  # LLM Adapters
│   └── image/                # Image Adapters
│
├── application/               # 애플리케이션 계층
│   ├── use_cases/            # Use Cases
│   └── workflow/             # LangGraph Workflows
│
├── api/                       # API 계층
│   ├── routes.py             # 엔드포인트
│   └── dependencies.py       # FastAPI Dependencies
│
└── prompts/                   # 프롬프트 템플릿
```

---

## Core vs Adapters

### Core - 프레임워크 인프라
모든 템플릿에서 재사용 가능한 순수 인프라

- config.py - 설정 관리 (모든 템플릿 공통)
- auth.py - JWT 인증 (모든 템플릿 공통)
- prompt_loader.py - 프롬프트 로딩 (모든 템플릿 공통)
- decorators.py - DI 데코레이터 (모든 템플릿 공통)
- module.py - Port-Adapter 바인딩 (템플릿별로 다름)

특징: 도메인 무관, 기술적 인프라만 포함

### Adapters - 인프라 구현체
특정 외부 시스템 연결

- AnthropicLLMAdapter - Anthropic API 전용
- ReplicateImageAdapter - Replicate API 전용
- OpenAIAdapter - OpenAI API 전용

특징: 도메인 특화, 외부 시스템 의존적, 교체 가능

### 분리 이유

1. 프레임워크 vs 애플리케이션
```
Core (프레임워크)
  - 모든 템플릿이 공유
  - 변경 거의 없음

Adapters (애플리케이션)
  - 템플릿마다 다름
  - 자주 변경/추가
```

2. 의존성 방향
```
Core → 독립적 (순수 인프라)
Adapters → Core 사용
```

3. Hexagonal Architecture
```
core/       프레임워크 (중심)
domain/     비즈니스 로직 (중심)
adapters/   외부 세계 (바깥쪽)
```

---

## 설계 원칙

### Port-Adapter 패턴
외부 시스템을 Port 인터페이스로 추상화:

```python
# Port
class ILLMPort(ABC):
    @abstractmethod
    async def classify_intent(self, query: str) -> Dict[str, Any]:
        pass

# Adapter (교체 가능)
@singleton
class AnthropicLLMAdapter(ILLMPort):
    async def classify_intent(self, query: str) -> Dict[str, Any]:
        # Anthropic API 호출
        ...
```

### UseCase
- DTO 반환
- Domain to DTO 변환
- routes는 1줄로 호출만

### Adapter
- 비즈니스 로직 없음
- HTTP 통신 및 파싱만
- Port 인터페이스 구현

### Workflow
- 노드 실행 순서만 정의
- 비즈니스 로직은 Domain Services로 위임

---

## 기술 스택

- Framework Core: Piri Framework
- Web Framework: FastAPI
- Workflow Engine: LangGraph
- AI/LLM: Anthropic Claude Sonnet 4.5
- Image Generation: Replicate Flux Schnell
- Authentication: JWT
- Dependency Injection: injector
- Prompt Management: YAML + Jinja2

---

## 테스트

```bash
# 전체 테스트
pytest

# 커버리지 포함
pytest --cov=app --cov-report=html
```

---

## 예제: Cooking Assistant 템플릿

이 레포지토리는 Piri Framework의 첫 번째 템플릿인 **한국어 요리 AI 어시스턴트** 예제를 포함합니다.

### 기능
- 레시피 생성 - 조리법과 이미지 자동 생성
- 음식 추천 - 맞춤형 메뉴 제안
- 요리 Q&A - 요리 관련 질문 답변
- 한국어 네이티브 지원

### API 문서

서버 실행 후 브라우저에서 확인:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### API 사용 예제

레시피 생성:
```bash
curl -X POST http://localhost:8000/api/cooking \
  -H "Content-Type: application/json" \
  -d '{"query": "김치찌개 만드는 법"}'
```

음식 추천:
```bash
curl -X POST http://localhost:8000/api/cooking \
  -H "Content-Type: application/json" \
  -d '{"query": "매운 음식 추천해줘"}'
```

인증 사용:
```bash
python3 scripts/generate_token.py user123

curl -X POST http://localhost:8000/api/cooking \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"query": "김치찌개 만드는 법"}'
```

---

## 향후 템플릿 계획

- chatbot - 대화형 챗봇
- rag-qa - RAG 기반 문서 Q&A
- multimodal - 멀티모달 AI
- conversational - 대화 히스토리 관리

---

## 라이선스

MIT License
