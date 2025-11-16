# 인증 시스템 테스트 가이드

PyAi 프로젝트의 JWT 인증 기능을 테스트하는 방법을 안내합니다.

---

## 📋 사전 준비

### 1. 환경 변수 설정

`.env` 파일에 `SECRET_KEY`가 설정되어 있는지 확인하세요:

```bash
# .env 파일이 없으면 생성
cp .env.example .env

# .env 파일 편집
nano .env
```

`.env` 파일 내용:
```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
REPLICATE_API_TOKEN=r8_your-token-here
SECRET_KEY=my-super-secret-key-for-jwt  # 이 줄 추가!
```

⚠️ **중요**: 프로덕션에서는 강력한 랜덤 키를 사용하세요!

```bash
# 강력한 SECRET_KEY 생성 (Python 이용)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. 서버 실행

```bash
# 개발 서버 실행
python -m app.main
```

서버가 http://localhost:8000 에서 실행됩니다.

---

## 🔑 테스트 방법

### 방법 1: 토큰 생성 스크립트 사용 (권장)

#### Step 1: 토큰 생성

```bash
# 기본 사용 (24시간 유효)
python3 scripts/generate_token.py user123

# 만료 시간 지정 (48시간 유효)
python3 scripts/generate_token.py user456 --hours 48
```

**출력 예시:**
```
================================================================================
JWT Token Generated Successfully!
================================================================================

User ID: user123
Expires in: 24 hours

Token:
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIiwiZXhwIjoxNzM3MTEyMDAwfQ.abc123...

================================================================================
Test with curl:
================================================================================

curl -X POST http://localhost:8000/api/cooking \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{"query": "김치찌개 만드는 법"}'

================================================================================
```

#### Step 2: API 테스트

위에서 생성된 curl 명령어를 복사해서 실행하거나, 아래 방법을 사용하세요:

**1) 인증과 함께 요청 (로그인 사용자)**
```bash
# 토큰을 환경 변수에 저장
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# API 호출
curl -X POST http://localhost:8000/api/cooking \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "김치찌개 만드는 법"}'
```

**2) 인증 없이 요청 (익명 사용자)**
```bash
# 토큰 없이 호출 (선택적 인증이므로 동작함)
curl -X POST http://localhost:8000/api/cooking \
  -H "Content-Type: application/json" \
  -d '{"query": "김치찌개 만드는 법"}'
```

**3) 잘못된 토큰으로 요청**
```bash
# 잘못된 토큰 (선택적 인증이므로 401 에러 없이 익명으로 처리됨)
curl -X POST http://localhost:8000/api/cooking \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer invalid-token-here" \
  -d '{"query": "김치찌개 만드는 법"}'
```

---

### 방법 2: Python으로 직접 테스트

#### 토큰 생성 및 검증 테스트

```python
# test_auth.py
from app.core.auth import AuthService
from app.core.config import get_settings

# 1. 설정 로드
settings = get_settings()
auth_service = AuthService(secret_key=settings.secret_key)

# 2. 토큰 생성
token = auth_service.create_access_token(user_id="user123")
print(f"Generated Token: {token}")

# 3. 토큰 검증
try:
    user_id = auth_service.verify_token(token)
    print(f"✅ Token Valid! User ID: {user_id}")
except Exception as e:
    print(f"❌ Token Invalid: {e}")

# 4. 잘못된 토큰 검증
try:
    user_id = auth_service.verify_token("invalid-token")
    print(f"User ID: {user_id}")
except Exception as e:
    print(f"✅ Invalid token rejected: {e}")
```

실행:
```bash
python3 test_auth.py
```

---

### 방법 3: Postman / Insomnia 사용

#### 1. 토큰 생성
```bash
python3 scripts/generate_token.py user123
```

#### 2. Postman 설정

1. **Request 생성**
   - Method: `POST`
   - URL: `http://localhost:8000/api/cooking`

2. **Headers 설정**
   - `Content-Type`: `application/json`
   - `Authorization`: `Bearer <your-token-here>`

3. **Body 설정** (raw JSON)
   ```json
   {
     "query": "김치찌개 만드는 법"
   }
   ```

4. **Send 클릭**

---

## ✅ 테스트 체크리스트

### 기본 테스트
- [ ] 서버가 정상적으로 실행됨 (`python -m app.main`)
- [ ] `.env`에 `SECRET_KEY`가 설정됨
- [ ] 토큰 생성 스크립트가 정상 동작함 (`python3 scripts/generate_token.py user123`)

### 인증 테스트
- [ ] **토큰 없이 요청** → 200 응답 (익명 사용자로 처리)
- [ ] **유효한 토큰과 함께 요청** → 200 응답 (user_id가 로그에 출력됨)
- [ ] **잘못된 토큰과 함께 요청** → 200 응답 (익명 사용자로 처리, 에러 로그 출력)

### 로그 확인
서버 로그에서 다음 메시지를 확인하세요:

```
[UseCase] 실행 시작 - user_id: user123, query: 김치찌개 만드는 법...
```

- 토큰이 있으면: `user_id: user123`
- 토큰이 없으면: `user_id: None`

---

## 🔍 트러블슈팅

### 1. `SECRET_KEY` 누락 에러
```
ValidationError: field required (type=value_error.missing)
```

**해결**: `.env` 파일에 `SECRET_KEY` 추가

```bash
echo "SECRET_KEY=my-secret-key-here" >> .env
```

---

### 2. 토큰 검증 실패
```
HTTPException: 401 Unauthorized - 토큰 검증 실패
```

**원인**:
- 토큰이 만료됨
- SECRET_KEY가 변경됨
- 토큰 형식이 잘못됨

**해결**:
```bash
# 새 토큰 생성
python3 scripts/generate_token.py user123
```

---

### 3. 모듈 import 에러
```
ModuleNotFoundError: No module named 'jose'
```

**해결**:
```bash
pip3 install 'python-jose[cryptography]==3.3.0' 'passlib[bcrypt]==1.7.4'
```

---

## 📊 예상 응답 예시

### 성공 응답 (레시피 생성)
```json
{
  "status": "success",
  "code": "RECIPE_CREATED",
  "intent": "recipe_create",
  "data": {
    "recipe": {
      "name": "김치찌개",
      "ingredients": [...],
      "steps": [...]
    },
    "image_url": "https://replicate.delivery/...",
    "metadata": {
      "entities": {...},
      "confidence": 0.95,
      "secondary_intents_processed": [],
      "timestamp": "2025-01-16T12:00:00"
    }
  },
  "message": null
}
```

### 에러 응답
```json
{
  "status": "error",
  "code": "INTERNAL_ERROR",
  "intent": null,
  "data": null,
  "message": "서버 오류: ..."
}
```

---

## 🎯 필수 vs 선택적 인증 비교

### 현재 구현 (선택적 인증)
```python
# app/api/routes.py
user_id: Optional[str] = Depends(get_optional_user)
```

- ✅ 토큰 없어도 접근 가능 (익명 사용자)
- ✅ 토큰 있으면 user_id 활용 (개인화 가능)
- ⚠️ 잘못된 토큰도 무시하고 통과 (user_id=None)

### 필수 인증으로 변경하려면
```python
# app/api/routes.py
from app.api.dependencies import get_current_user

user_id: str = Depends(get_current_user)  # ← Optional 제거
```

- ❌ 토큰 없으면 **401 에러**
- ❌ 잘못된 토큰도 **401 에러**
- ✅ 유효한 토큰만 통과

---

## 🚀 다음 단계

인증 기능이 정상 동작하면:

1. **사용자 DB 연동** (향후 확장)
   - 회원가입/로그인 엔드포인트 추가
   - user_id로 사용자 정보 조회

2. **사용자 선호도 기반 개인화**
   - user_id로 과거 레시피 히스토리 조회
   - 맞춤형 추천 제공

3. **RAG + 대화 메모리 추가**
   - user_id별 대화 히스토리 저장
   - 컨텍스트 기반 응답 생성

---

## 📚 참고 자료

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io](https://jwt.io/) - JWT 토큰 디버깅
- [tobe2.md](../tobe2.md) - 아키텍처 설계 문서
