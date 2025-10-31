# CLAUDE.md

이 파일은 이 저장소의 코드 작업 시 Claude Code (claude.ai/code)에 대한 가이드를 제공합니다.

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

# 헬스 체크
curl http://localhost:8000/api/health
```

## 아키텍처 개요

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

### API 구조

- **진입점**: `app/main.py` - CORS를 포함한 FastAPI 애플리케이션 설정
- **라우트**: `app/api/routes.py` - 모든 쿼리 유형을 처리하는 단일 `/api/cooking` 엔드포인트
- **모델**: `app/models/schemas.py` - 요청/응답 검증을 위한 Pydantic 모델
- **서비스**:
  - `cooking_assistant.py`: 메인 LangGraph 워크플로우 오케스트레이터
  - `image_service.py`: 이미지 생성을 위한 Replicate API 통합

### 상태 관리

`CookingState` TypedDict가 추적하는 항목:
- 사용자 쿼리 및 추출된 의도/엔티티
- 생성된 레시피, 추천, 또는 답변
- 이미지 생성 프롬프트 및 URL
- 우아한 성능 저하를 위한 오류 상태

## 응답 형식

모든 응답은 의도별 데이터를 포함한 통합 구조를 따릅니다:

```json
{
  "status": "success|error",
  "intent": "recipe_create|recommend|question",
  "data": {
    // recipe_create의 경우:
    "recipe": {...} 또는 "recipes": [...],
    "image_url": "...",

    // recommend의 경우:
    "recommendations": [...],

    // question의 경우:
    "answer": "...",
    "additional_tips": [...],

    // 메타데이터 (항상 포함):
    "metadata": {
      "entities": {...},
      "confidence": 0.95,
      "secondary_intents_processed": [...]
    }
  },
  "message": null 또는 오류_메시지
}
```

## 환경 변수

`.env`에 필수:
- `ANTHROPIC_API_KEY` - Claude API 액세스
- `REPLICATE_API_TOKEN` - 이미지 생성 서비스

## 주요 기능

- **한국어 지원** - 한국어 레시피 생성 및 이해 네이티브 지원
- **우아한 성능 저하** - 이미지 생성이 실패해도 레시피 반환
- **무상태 설계** - 데이터베이스 불필요
- **90초 타임아웃** - LLM 및 이미지 생성 지연 시간 수용
- **구조화된 로깅** - 의도 분류 및 워크플로우 실행 디버깅을 위한 상세 로깅

## API 문서

서버 실행 시:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc