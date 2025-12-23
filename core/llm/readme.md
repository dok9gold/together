# core/llm

LLM API 호출을 위한 모듈

## 구조

```
core/llm/
├── __init__.py
├── interface.py      # LLMInterface (ABC)
├── claude.py         # ClaudeLLM + ClaudeOption
├── gemini.py         # GeminiLLM + GeminiOption
└── provider.py       # LLMProvider (여러 LLM 관리)
```

## 사용법

### 1. 초기화 (main.py lifespan)

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.llm import LLMProvider, ClaudeLLM, GeminiLLM
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # LLM Provider 설정
    provider = LLMProvider(default_provider="claude")
    provider.register("claude", ClaudeLLM(api_key=os.getenv("ANTHROPIC_API_KEY")))
    provider.register("gemini", GeminiLLM(api_key=os.getenv("GOOGLE_API_KEY")))

    app.state.llm_provider = provider

    yield

app = FastAPI(lifespan=lifespan)
```

### 2. 노드에서 사용

```python
from core.llm import LLMProvider

class RecipeGeneratorNode:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def execute(self, state):
        # 기본 호출 (default provider 사용)
        result = await self.llm.generate(prompt="김치찌개 레시피")

        # provider 지정
        result = await self.llm.generate(
            prompt="김치찌개 레시피",
            provider="gemini"
        )

        # 시스템 프롬프트 + 옵션
        result = await self.llm.generate(
            prompt="김치찌개 레시피",
            provider="claude",
            system="당신은 요리 전문가입니다.",
            option={"temperature": 0.3, "max_tokens": 2048}
        )
```

### 3. 직접 LLM 인스턴스 사용

```python
from core.llm import ClaudeLLM, GeminiLLM

# Claude
claude = ClaudeLLM(api_key="...")
result = await claude.generate(
    prompt="안녕",
    system="친절하게 답변해주세요.",
    option={"temperature": 0.5}
)

# Gemini
gemini = GeminiLLM(api_key="...")
result = await gemini.generate(
    prompt="안녕",
    option={"max_output_tokens": 1024}
)
```

## 옵션

### ClaudeOption (기본값)

| 옵션 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| model | str | claude-sonnet-4-20250514 | 모델 ID |
| max_tokens | int | 4096 | 최대 토큰 수 |
| temperature | float | 0.7 | 샘플링 온도 (0.0~1.0) |
| top_p | float | None | Top-p 샘플링 |
| stop_sequences | list | None | 중단 시퀀스 |

### GeminiOption (기본값)

| 옵션 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| model | str | gemini-1.5-flash | 모델 ID |
| max_output_tokens | int | 4096 | 최대 출력 토큰 수 |
| temperature | float | 0.7 | 샘플링 온도 (0.0~2.0) |
| top_p | float | None | Top-p 샘플링 |
| top_k | int | None | Top-k 샘플링 |
| stop_sequences | list | None | 중단 시퀀스 |

## 환경변수

```env
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AI...
```

## 의존성

```
anthropic
google-generativeai
```
