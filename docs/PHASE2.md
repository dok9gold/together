# Phase 2: 인증 및 테스트 인프라 구축

> **목표**: JWT 인증 시스템 안정화 및 테스트 자동화 구축

## 현재 상태

- **진행률**: 95% 완료
- **구현 완료**: JWT 토큰 생성, 검증, FastAPI Dependency 통합
- **남은 작업**: 테스트 코드 작성, 에러 핸들링 개선

---

## 1. JWT 인증 테스트 (P0 - 즉시)

### 1.1 테스트 파일 구조
```
tests/
├── conftest.py              # pytest 설정, fixtures
├── core/
│   ├── test_auth.py         # JWT 생성/검증 단위 테스트
│   └── test_dependencies.py # FastAPI Dependency 테스트
└── api/
    └── test_auth_routes.py  # 인증 API 통합 테스트
```

### 1.2 테스트 항목

#### JWT 생성/검증 테스트
```python
# tests/core/test_auth.py
import pytest
from app.core.auth import create_access_token, verify_token

def test_create_access_token():
    """토큰 생성 테스트"""
    token = create_access_token(user_id="user123")
    assert token is not None
    assert isinstance(token, str)

def test_verify_valid_token():
    """유효한 토큰 검증 테스트"""
    token = create_access_token(user_id="user123")
    payload = verify_token(token)
    assert payload["user_id"] == "user123"

def test_verify_expired_token():
    """만료된 토큰 검증 테스트"""
    # 만료 시간 0초로 설정
    token = create_access_token(user_id="user123", expires_delta=timedelta(seconds=0))
    time.sleep(1)
    with pytest.raises(HTTPException) as exc:
        verify_token(token)
    assert exc.value.status_code == 401

def test_verify_invalid_token():
    """잘못된 토큰 검증 테스트"""
    with pytest.raises(HTTPException) as exc:
        verify_token("invalid.token.here")
    assert exc.value.status_code == 401
```

#### Dependency 테스트
```python
# tests/core/test_dependencies.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_protected_endpoint_without_token():
    """토큰 없이 보호된 엔드포인트 접근 테스트"""
    response = client.post("/api/cooking", json={"query": "김치찌개"})
    assert response.status_code == 401

def test_protected_endpoint_with_valid_token():
    """유효한 토큰으로 보호된 엔드포인트 접근 테스트"""
    token = create_access_token(user_id="test_user")
    response = client.post(
        "/api/cooking",
        json={"query": "김치찌개"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

def test_protected_endpoint_with_invalid_token():
    """잘못된 토큰으로 보호된 엔드포인트 접근 테스트"""
    response = client.post(
        "/api/cooking",
        json={"query": "김치찌개"},
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
```

### 1.3 실행 방법
```bash
# 전체 테스트 실행
pytest

# 특정 파일만 실행
pytest tests/core/test_auth.py

# 상세 출력 (-v), 커버리지 포함
pytest -v --cov=app/core/auth
```

---

## 2. 에러 핸들링 개선 (P0 - 즉시)

### 2.1 현재 문제점
- 일부 예외가 처리되지 않아 500 에러 발생
- 사용자에게 불친절한 에러 메시지
- 로그 부재로 디버깅 어려움

### 2.2 개선 사항

#### 전역 예외 핸들러 추가
```python
# app/core/error_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse

async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 핸들러"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_SERVER_ERROR",
            "message": "서버 내부 오류가 발생했습니다.",
            "detail": str(exc) if settings.DEBUG else None
        }
    )

# app/main.py에 등록
app.add_exception_handler(Exception, global_exception_handler)
```

#### 도메인 예외 체계화
```python
# app/cooking_assistant/exceptions.py
class CookingException(Exception):
    """요리 도메인 기본 예외"""
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(message)

class RecipeGenerationError(CookingException):
    """레시피 생성 실패"""
    def __init__(self, reason: str):
        super().__init__(
            message=f"레시피 생성 실패: {reason}",
            code="RECIPE_GENERATION_FAILED"
        )

class InvalidIntentError(CookingException):
    """잘못된 Intent"""
    def __init__(self, intent: str):
        super().__init__(
            message=f"지원하지 않는 Intent: {intent}",
            code="INVALID_INTENT"
        )
```

---

## 3. 로깅 시스템 구축 (P0 - 즉시)

### 3.1 구조화된 로깅 (`structlog`)

#### 설치
```bash
pip install structlog
```

#### 설정
```python
# app/core/logging_config.py
import structlog
import logging

def configure_logging():
    """로깅 설정"""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

# app/main.py에서 호출
configure_logging()
logger = structlog.get_logger()
```

#### 사용 예시
```python
# Node에서 로깅
logger.info("recipe_generation_started", user_query=query, user_id=user_id)

try:
    recipe = await self.llm_port.generate_recipe(prompt)
    logger.info("recipe_generation_success", recipe_id=recipe.id, duration_ms=elapsed)
except Exception as e:
    logger.error("recipe_generation_failed", error=str(e), user_query=query)
    raise
```

### 3.2 로그 포맷
```json
{
  "event": "recipe_generation_started",
  "timestamp": "2025-12-06T10:30:00.123Z",
  "level": "info",
  "user_query": "김치찌개 만드는 법",
  "user_id": "user123"
}
```

---

## 4. 테스트 인프라 구축 (P1 - 1-2주)

### 4.1 Mock Adapter 생성

#### Base Mock Adapter
```python
# tests/mocks/base_mock_adapter.py
class MockLLMAdapter(ILLMPort):
    """LLM Adapter Mock"""
    def __init__(self):
        self.call_count = 0
        self.last_prompt = None

    async def generate_recipe(self, prompt: str) -> dict:
        self.call_count += 1
        self.last_prompt = prompt
        return {
            "title": "Mock 레시피",
            "ingredients": ["재료1", "재료2"],
            "steps": ["단계1", "단계2"]
        }
```

#### Fixture 등록
```python
# tests/conftest.py
@pytest.fixture
def mock_llm_adapter():
    return MockLLMAdapter()

@pytest.fixture
def test_service(mock_llm_adapter):
    return CookingAssistantService(llm_port=mock_llm_adapter)
```

### 4.2 Workflow 통합 테스트

```python
# tests/workflows/test_cooking_workflow.py
@pytest.mark.asyncio
async def test_recipe_creation_workflow(mock_llm_adapter):
    """레시피 생성 워크플로우 통합 테스트"""
    state = {
        "user_query": "김치찌개 만드는 법",
        "primary_intent": "recipe_create",
        "secondary_intents": [],
        "processed_secondary_intents": []
    }

    result = await cooking_workflow.run(state)

    assert result["recipe"] is not None
    assert mock_llm_adapter.call_count == 2  # Intent + Recipe
```

### 4.3 CI/CD 파이프라인 (GitHub Actions)

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 5. 보안 강화

### 5.1 환경 변수 검증
```python
# app/core/config.py
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    JWT_SECRET_KEY: str
    ANTHROPIC_API_KEY: str

    @validator("JWT_SECRET_KEY")
    def validate_jwt_secret(cls, v):
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return v

    class Config:
        env_file = ".env"
```

### 5.2 Rate Limiting
```python
# app/core/rate_limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# app/main.py
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# routes에서 사용
@router.post("/cooking")
@limiter.limit("10/minute")
async def create_cooking_response(request: Request, ...):
    ...
```

---

## 체크리스트

### P0 (즉시 완료)
- [ ] JWT 생성/검증 단위 테스트 작성
- [ ] FastAPI Dependency 통합 테스트 작성
- [ ] 전역 예외 핸들러 추가
- [ ] 도메인 예외 체계화
- [ ] structlog 로깅 시스템 구축
- [ ] 주요 Node에 로깅 추가

### P1 (1-2주)
- [ ] Mock Adapter 자동 생성 도구
- [ ] Workflow 통합 테스트 작성
- [ ] GitHub Actions CI/CD 구축
- [ ] 환경 변수 검증 강화
- [ ] Rate Limiting 추가
- [ ] 테스트 커버리지 80% 이상 달성

---

## 다음 단계

Phase 2 완료 후 → [Phase 3: RAG 통합](PHASE3.md)
