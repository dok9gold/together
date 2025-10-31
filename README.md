# 🍳 PyAi - 지능형 한국어 요리 AI 어시스턴트

[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.120.2-009688.svg)](https://fastapi.tiangolo.com)
[![Claude](https://img.shields.io/badge/Claude-Sonnet%204.5-orange.svg)](https://anthropic.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

자연어 이해를 통해 레시피 생성, 음식 추천, 요리 질문 답변을 제공하는 차세대 한국어 요리 AI 서비스입니다.

## ✨ 핵심 가치

- **🎯 의도 기반 응답**: 사용자가 무엇을 원하는지 정확히 파악하여 맞춤형 응답 제공
- **🔄 다중 작업 처리**: 하나의 쿼리로 추천 → 레시피 생성 → 이미지 생성까지 연속 처리
- **🎨 비주얼 레시피**: 텍스트 레시피와 함께 고품질 음식 이미지 자동 생성
- **⚡ 실시간 API**: RESTful API를 통한 즉각적인 응답 (평균 응답시간: 15-30초)

## 🚀 주요 기능

### 1. 레시피 생성 (`recipe_create`)
```
"김치찌개 만드는 법 알려줘"
→ 재료, 단계별 조리법, 난이도, 시간, 완성 이미지
```

### 2. 음식 추천 (`recommend`)
```
"매운 한식 3가지 추천해줘"
→ 추천 음식 리스트, 각 음식 설명, 추천 이유
```

### 3. 요리 Q&A (`question`)
```
"김치찌개 칼로리가 얼마야?"
→ 정확한 답변, 추가 팁 제공
```

### 4. 복합 쿼리 처리
```
"매운 음식 추천하고 그 중 하나 레시피도 보여줘"
→ 추천 리스트 → 자동 레시피 선택 → 이미지 생성
```

## 🛠 기술 스택

| 영역 | 기술 | 용도 |
|------|------|------|
| **Backend** | FastAPI 0.120.2 | 고성능 비동기 웹 프레임워크 |
| **AI Engine** | Claude Sonnet 4.5 | 자연어 이해 및 텍스트 생성 |
| **Orchestration** | LangGraph 1.0.2 | 상태 기반 워크플로우 관리 |
| **Image Gen** | Replicate (Flux Schnell) | 음식 이미지 실시간 생성 |
| **Language** | Python 3.13+ | 메인 개발 언어 |

## 📦 빠른 시작

### 사전 요구사항

- Python 3.13 이상
- [Anthropic API Key](https://console.anthropic.com/)
- [Replicate API Token](https://replicate.com/account/api-tokens)

### 1. 저장소 클론
```bash
git clone https://github.com/yourusername/PyAi.git
cd PyAi
```

### 2. 가상환경 설정 (권장)
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
```bash
cp .env.example .env
```

`.env` 파일 편집:
```env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
REPLICATE_API_TOKEN=r8_xxxxx
```

### 5. 서버 실행
```bash
python -m app.main
```

서버가 http://localhost:8000 에서 실행됩니다.

## 📖 API 사용 예시

### 기본 레시피 생성
```python
import requests

response = requests.post(
    "http://localhost:8000/api/cooking",
    json={"query": "된장찌개 만드는 법"}
)

result = response.json()
print(f"레시피: {result['data']['recipe']}")
print(f"이미지: {result['data']['image_url']}")
```

### 복수 레시피 조회
```python
response = requests.post(
    "http://localhost:8000/api/cooking",
    json={"query": "김치찌개, 된장찌개, 순두부찌개 레시피"}
)

result = response.json()
for recipe in result['data']['recipes']:
    print(f"- {recipe['title']}: {recipe['cooking_time']}")
```

### 조건부 추천
```python
response = requests.post(
    "http://localhost:8000/api/cooking",
    json={"query": "30분 안에 만들 수 있는 쉬운 한식 추천해줘"}
)

recommendations = result['data']['recommendations']
for rec in recommendations:
    print(f"- {rec['name']}: {rec['reason']}")
```

## 📂 프로젝트 구조

```
PyAi/
├── app/
│   ├── main.py                 # FastAPI 앱 진입점
│   ├── api/
│   │   └── routes.py           # API 엔드포인트 정의
│   ├── services/
│   │   ├── cooking_assistant.py # LangGraph 워크플로우 엔진
│   │   └── image_service.py    # 이미지 생성 서비스
│   └── models/
│       └── schemas.py          # Pydantic 데이터 모델
├── .env.example                # 환경변수 템플릿
├── requirements.txt            # Python 패키지 목록
├── CLAUDE.md                   # Claude Code 전용 가이드
└── README.md                   # 프로젝트 문서 (현재 파일)
```

## 🔍 API 문서

서버 실행 후 접속:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## ⚙️ 고급 설정

### 타임아웃 조정
`app/services/cooking_assistant.py`:
```python
self.llm = ChatAnthropic(
    model="claude-sonnet-4-5-20250929",
    timeout=90  # 기본 90초, 필요시 조정
)
```

### 이미지 생성 재시도
`app/services/image_service.py`:
```python
async def generate_image(self, prompt: str, retries: int = 2):
    # retries 값 조정으로 재시도 횟수 변경
```

### CORS 설정
`app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 프로덕션 도메인으로 변경
)
```

## 📊 성능 및 제한사항

### 성능
- **평균 응답 시간**: 15-30초 (레시피 + 이미지)
- **동시 처리**: FastAPI 비동기로 다중 요청 처리
- **캐싱**: 없음 (Stateless 설계)

### 제한사항
- 최대 타임아웃: 90초
- 이미지 생성 실패 시 텍스트만 반환
- API 키 Rate Limit 적용
- 한국어 특화 (다국어 미지원)

## 🐛 트러블슈팅

### API 키 오류
```
ValueError: ANTHROPIC_API_KEY not found
```
**해결**: `.env` 파일에 API 키가 올바르게 설정되어 있는지 확인

### 이미지 생성 실패
```json
{
  "status": "success",
  "data": {"recipe": {...}, "image_url": null},
  "message": "이미지 생성 실패"
}
```
**해결**: Replicate API 토큰 확인, 네트워크 연결 확인

### 타임아웃 오류
```
TimeoutError: Request timed out after 90 seconds
```
**해결**: 복잡한 쿼리를 단순화하거나 타임아웃 값 증가

## 🔄 업데이트 로그

### v1.0.0 (2024-10-30)
- 초기 릴리스
- 레시피 생성, 음식 추천, Q&A 기능
- LangGraph 워크플로우 구현
- Replicate 이미지 생성 통합

## 🚧 로드맵

- [ ] **v1.1.0** - 영양 정보 자동 계산
- [ ] **v1.2.0** - 레시피 저장 및 검색 (DB 통합)
- [ ] **v1.3.0** - 단계별 조리 이미지 생성
- [ ] **v2.0.0** - 실시간 스트리밍 응답
- [ ] **v2.1.0** - 다국어 지원 (영어, 일본어, 중국어)

## 🤝 기여하기

1. 이 저장소를 Fork 합니다
2. 기능 브랜치를 생성합니다 (`git checkout -b feature/AmazingFeature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 Push 합니다 (`git push origin feature/AmazingFeature`)
5. Pull Request를 생성합니다

## 📜 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 💬 문의 및 지원

- **이슈 트래커**: [GitHub Issues](https://github.com/yourusername/PyAi/issues)
- **이메일**: your.email@example.com
- **문서**: [프로젝트 Wiki](https://github.com/yourusername/PyAi/wiki)

---

**Made with ❤️ using Claude Sonnet 4.5 and LangGraph**