# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

이 프로젝트는 **Piri Framework**의 `cooking-assistant` 템플릿입니다.

**Piri Framework**는 FastAPI + LangGraph 기반 AI Agent 애플리케이션을 빠르게 구축할 수 있는 통합 프레임워크입니다.
- Hexagonal Architecture (Port-Adapter 패턴)
- DDD (Domain-Driven Design)
- 데코레이터 기반 의존성 주입 (`@singleton`, `@inject`)
- 프롬프트 관리 시스템 (YAML + Jinja2)

**Cooking Assistant**는 한국어 요리 AI 어시스턴트로, RESTful API를 통해 지능형 레시피 생성, 음식 추천, 요리 관련 Q&A를 제공합니다.

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
    @singleton
    @provider
    def provide_llm_adapter(
        self,
        settings: Settings,
        prompt_loader: PromptLoader
    ) -> ILLMPort:
        return AnthropicLLMAdapter(settings, prompt_loader)
```

**생명주기**:
- **@singleton**: 애플리케이션 전체에서 하나의 인스턴스 공유
- **@inject + 데코레이터 없음**: Factory (요청마다 새 인스턴스)

---

## Piri Framework 설계 원칙

### 1. Core = 프레임워크 인프라
- **프레임워크 컴포넌트**: 모든 템플릿에서 재사용 가능 (config, auth, prompt_loader, decorators)
- **템플릿 조립**: Port-Adapter 바인딩 (module.py)

### 2. UseCase = Spring의 Service
- DTO 반환 담당
- Domain → DTO 변환 수행
- routes는 1줄로 단순 호출만

### 3. Adapter = 연결자
- 비즈니스 로직 없음
- HTTP 통신 및 파싱만 수행

### 4. Workflow = 오케스트레이션
- 노드 실행 순서만 정의
- 비즈니스 로직은 Domain Services로 위임

---

## 참고 문서

- **Piri Framework 전체 가이드**: `docs/FRAMEWORK.md`
- **프롬프트**: `app/prompts/*.yaml`
