# PyAi - 한국어 요리 AI 어시스턴트

FastAPI, Claude (Anthropic), LangGraph로 구축된 지능형 한국어 요리 AI 어시스턴트 서비스입니다.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.120+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 주요 기능

- **🍳 레시피 생성** - 상세한 조리법과 음식 이미지 자동 생성
- **🎨 음식 추천** - 선호도 기반 맞춤형 메뉴 제안
- **💬 요리 Q&A** - 요리 관련 질문에 대한 정확한 답변
- **🔐 JWT 인증** - 선택적 사용자 인증 (개인화 기능 확장 가능)
- **🌐 RESTful API** - 표준화된 API 엔드포인트 제공
- **🖼️ AI 이미지 생성** - Replicate Flux Schnell을 통한 고품질 음식 사진
- **🇰🇷 한국어 네이티브 지원** - 한국 요리에 최적화

---

## 🚀 빠른 시작

### 사전 요구사항

- Python 3.9 이상
- pip 패키지 매니저
- [Anthropic API Key](https://console.anthropic.com/)
- [Replicate API Token](https://replicate.com/account/api-tokens)

### 설치

1. **저장소 클론**
```bash
git clone https://github.com/your-username/born.git
cd born
```

2. **의존성 설치**
```bash
pip install -r requirements.txt
```

3. **환경 변수 설정**
```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env
```

`.env` 파일 내용:
```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
REPLICATE_API_TOKEN=r8_your-token-here
SECRET_KEY=your-secret-key-for-jwt
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

## 📖 API 사용법

### 기본 API 호출

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
  -d '{"query": "김치찌개 칼로리는?"}'
```

### 인증과 함께 사용

1. **JWT 토큰 생성**
```bash
python3 scripts/generate_token.py user123
```

2. **토큰과 함께 API 호출**
```bash
curl -X POST http://localhost:8000/api/cooking \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{"query": "파스타 만드는 법"}'
```

### API 문서

서버 실행 후 브라우저에서 확인:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🏗️ 아키텍처

### 기술 스택

- **Backend Framework**: FastAPI
- **AI/LLM**: Anthropic Claude Sonnet 4.5
- **Workflow Engine**: LangGraph
- **Image Generation**: Replicate (Flux Schnell)
- **Authentication**: JWT (python-jose)
- **Dependency Injection**: dependency-injector

### 계층 구조 (Hexagonal Architecture + DDD)

```
┌─────────────────────────────────────────────┐
│  Routes (Presentation Layer)               │
│  - 엔드포인트 정의                          │
│  - UseCase 호출 (1줄)                       │
└──────────────┬──────────────────────────────┘
               ↓
┌──────────────▼──────────────────────────────┐
│  UseCase (Application Layer)               │
│  - Workflow 실행                            │
│  - Domain → DTO 변환                        │
│  - 에러 핸들링                              │
└──────────────┬──────────────────────────────┘
               ↓
┌──────────────▼──────────────────────────────┐
│  Workflow (LangGraph Orchestration)        │
│  - 의도 분류 → 분기 → 응답 생성             │
│  - 노드 실행 순서 정의                       │
└──────────────┬──────────────────────────────┘
               ↓
┌──────────────▼──────────────────────────────┐
│  Domain Services (비즈니스 로직)            │
│  - 프롬프트 생성                            │
│  - LLM 호출 전/후 처리                      │
└──────────────┬──────────────────────────────┘
               ↓
┌──────────────▼──────────────────────────────┐
│  Adapters (Infrastructure)                 │
│  - Anthropic API 연동                       │
│  - Replicate API 연동                       │
└─────────────────────────────────────────────┘
```

### 워크플로우 실행 순서

```
사용자 쿼리
    ↓
1. classify_intent (의도 분류)
    ↓
2. route_by_intent (의도별 분기)
    ├─ recipe_create → recipe_generator → image_generator
    ├─ recommend → recommender
    └─ question → question_answerer
    ↓
3. check_secondary_intents (복합 의도 처리)
    ↓
4. Domain → DTO 변환
    ↓
응답 반환
```

---

## 📂 프로젝트 구조

```
born/
├── app/
│   ├── api/                    # API 엔드포인트
│   │   ├── routes.py          # 메인 라우트 (46줄)
│   │   └── dependencies.py    # DI 헬퍼 함수
│   ├── application/            # Application Layer
│   │   ├── use_cases/         # UseCase (비즈니스 로직)
│   │   └── workflow/          # LangGraph 워크플로우
│   ├── domain/                 # Domain Layer
│   │   ├── entities/          # 도메인 엔티티
│   │   ├── services/          # 도메인 서비스
│   │   └── ports/             # Port 인터페이스
│   ├── adapters/               # Infrastructure Layer
│   │   ├── llm/               # LLM Adapter (Anthropic)
│   │   └── image/             # 이미지 Adapter (Replicate)
│   ├── core/                   # 핵심 설정
│   │   ├── config.py          # 환경 변수 관리
│   │   ├── auth.py            # JWT 인증
│   │   ├── container.py       # DI 컨테이너
│   │   └── response_codes.py  # 응답 코드 관리
│   ├── models/                 # Pydantic 모델
│   │   └── schemas.py         # DTO 정의
│   ├── prompts/                # LLM 프롬프트
│   │   └── *.yaml
│   └── main.py                 # FastAPI 앱 진입점
├── scripts/
│   └── generate_token.py      # JWT 토큰 생성 스크립트
├── docs/                       # 프로젝트 문서
│   ├── TODO.md                # 아키텍처 설계 및 TODO
│   ├── FRAMEWORK.md           # 프레임워크 가이드
│   ├── SUMMARY.md             # 문서 요약
│   └── AUTH_TEST_GUIDE.md     # 인증 테스트 가이드
├── .env.example               # 환경 변수 예시
├── requirements.txt           # Python 의존성
├── CLAUDE.md                  # Claude Code 가이드
└── README.md                  # 프로젝트 README
```

---

## 🔐 인증 시스템

### JWT 토큰 생성

```bash
# 기본 사용 (24시간 유효)
python3 scripts/generate_token.py user123

# 만료 시간 지정 (48시간)
python3 scripts/generate_token.py user456 --hours 48
```

### 인증 방식

- **선택적 인증** (현재 구현): 토큰 없이도 API 접근 가능, 토큰 있으면 개인화
- **필수 인증**: `get_optional_user` → `get_current_user`로 변경 시 토큰 필수

자세한 내용은 [인증 테스트 가이드](docs/AUTH_TEST_GUIDE.md)를 참고하세요.

---

## 🌟 응답 예시

### 레시피 생성 응답

```json
{
  "status": "success",
  "code": "RECIPE_CREATED",
  "intent": "recipe_create",
  "data": {
    "recipe": {
      "name": "김치찌개",
      "description": "한국의 대표적인 찌개 요리",
      "ingredients": [
        {"name": "김치", "amount": "300g"},
        {"name": "돼지고기", "amount": "200g"}
      ],
      "steps": [
        "1. 김치를 먹기 좋은 크기로 썰어주세요.",
        "2. 돼지고기를 볶다가 김치를 넣고 함께 볶습니다."
      ],
      "servings": 2,
      "cooking_time": "30분",
      "difficulty": "쉬움"
    },
    "image_url": "https://replicate.delivery/pbxt/...",
    "metadata": {
      "entities": {"dishes": ["김치찌개"]},
      "confidence": 0.95,
      "secondary_intents_processed": []
    }
  }
}
```

---

## 🛠️ 개발

### 설계 원칙

1. **UseCase = Spring의 Service**
   - DTO 반환 담당
   - routes는 1줄로 단순 호출만

2. **Adapter = 연결자**
   - 비즈니스 로직 없음
   - HTTP 통신 및 파싱만 수행

3. **Workflow = 오케스트레이션**
   - 노드 실행 순서만 정의
   - 비즈니스 로직은 Domain Services로 위임

### 프롬프트 관리

프롬프트는 `app/prompts/*.yaml` 파일에서 관리됩니다:
- `intent_classifier.yaml` - 의도 분류
- `recipe_generator.yaml` - 레시피 생성
- `recommender.yaml` - 음식 추천
- `question_answerer.yaml` - 질문 답변
- `image_prompt_generator.yaml` - 이미지 프롬프트 생성

---

## 📚 문서

- **[CLAUDE.md](CLAUDE.md)** - Claude Code 가이드
- **[docs/TODO.md](docs/TODO.md)** - 아키텍처 설계 및 TODO
- **[docs/FRAMEWORK.md](docs/FRAMEWORK.md)** - 프레임워크 가이드
- **[docs/AUTH_TEST_GUIDE.md](docs/AUTH_TEST_GUIDE.md)** - 인증 테스트 가이드
- **[docs/SUMMARY.md](docs/SUMMARY.md)** - 문서 요약

---

## 🤝 기여

프로젝트에 기여하고 싶으시다면:

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 라이선스

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 감사의 말

- [Anthropic](https://www.anthropic.com/) - Claude API
- [Replicate](https://replicate.com/) - 이미지 생성 API
- [LangGraph](https://github.com/langchain-ai/langgraph) - Workflow Engine
- [FastAPI](https://fastapi.tiangolo.com/) - Web Framework

---

## 📧 문의

프로젝트에 대한 질문이나 제안이 있으시면 이슈를 생성해주세요.

**프로젝트 링크**: [https://github.com/your-username/born](https://github.com/your-username/born)
