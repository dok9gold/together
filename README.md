# Recipe AI Service

Claude와 LangGraph를 활용한 레시피 생성 AI 서비스입니다.

## 기능

- Claude (Sonnet 4.5)를 사용한 레시피 텍스트 생성
- Replicate (Flux Schnell)를 사용한 완성 요리 이미지 생성
- LangGraph 기반 오케스트레이션
- FastAPI REST API

## 아키텍처

```
User Query → Recipe Generator (Claude) → Image Prompt Generator
          → Image Generator (Replicate) → Response
```

## 프로젝트 구조

```
PyAi/
├── app/
│   ├── main.py              # FastAPI 엔트리포인트
│   ├── api/
│   │   └── routes.py        # /api/recipe 엔드포인트
│   ├── services/
│   │   ├── recipe_graph.py  # LangGraph 워크플로우
│   │   └── image_service.py # Replicate 이미지 생성
│   └── models/
│       └── schemas.py       # Request/Response 모델
├── .env                     # 환경 변수 (생성 필요)
├── .env.example            # 환경 변수 예시
├── requirements.txt        # Python 패키지
└── README.md
```

## 설치

### 1. Python 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env.example`을 복사해서 `.env` 파일을 만들고, API 키를 입력하세요:

```bash
cp .env.example .env
```

`.env` 파일:
```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
REPLICATE_API_TOKEN=your_replicate_api_token_here
```

### API 키 발급

- **Anthropic**: https://console.anthropic.com/
- **Replicate**: https://replicate.com/account/api-tokens

## 실행

### 개발 서버 실행

```bash
python -m app.main
```

또는

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

서버가 실행되면 http://localhost:8000 에서 접근 가능합니다.

## API 사용법

### API 문서

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 레시피 생성 API

**Endpoint:** `POST /api/recipe`

**Request:**
```json
{
  "query": "파스타 카르보나라 만드는 법"
}
```

**Response (성공):**
```json
{
  "status": "success",
  "data": {
    "recipe": {
      "title": "파스타 카르보나라",
      "ingredients": [
        "파스타 200g",
        "베이컨 100g",
        "달걀 2개",
        "파마산 치즈 50g",
        "마늘 2쪽",
        "올리브유 2큰술"
      ],
      "steps": [
        "1. 큰 냄비에 물을 끓여 파스타를 삶습니다.",
        "2. 베이컨을 작게 썰어 팬에 볶습니다.",
        "3. 달걀과 파마산 치즈를 섞습니다.",
        "4. 삶은 파스타를 베이컨과 섞고 불을 끕니다.",
        "5. 달걀 혼합물을 넣고 빠르게 저어줍니다."
      ],
      "cooking_time": "30분",
      "difficulty": "중간"
    },
    "image_url": "https://replicate.delivery/pbxt/..."
  },
  "message": null
}
```

**Response (이미지 생성 실패 시):**
```json
{
  "status": "success",
  "data": {
    "recipe": { ... },
    "image_url": null
  },
  "message": "이미지 생성 실패"
}
```

### 헬스 체크

**Endpoint:** `GET /api/health`

```bash
curl http://localhost:8000/api/health
```

## 테스트

### cURL

```bash
curl -X POST http://localhost:8000/api/recipe \
  -H "Content-Type: application/json" \
  -d '{"query": "김치찌개 만드는 법"}'
```

### Python

```python
import requests

response = requests.post(
    "http://localhost:8000/api/recipe",
    json={"query": "김치찌개 만드는 법"}
)

print(response.json())
```

## 주요 특징

- **타임아웃**: 90초 (레시피 생성 + 이미지 생성)
- **에러 처리**: 이미지 생성 실패 시에도 레시피는 반환
- **재시도**: 이미지 생성 실패 시 최대 2회 재시도
- **Stateless**: DB 없이 동작

## 주의사항

- 이미지 생성에 10-20초가 소요됩니다
- 프론트엔드에서 로딩 UI를 구현하세요
- API 키는 절대 커밋하지 마세요 (`.env` 파일은 `.gitignore`에 추가)

## 향후 개선 사항

- [ ] Planner 추가 (동적 워크플로우)
- [ ] 영양 정보 조회
- [ ] 레시피 DB 저장 및 검색
- [ ] 단계별 이미지 생성
- [ ] 스트리밍 응답