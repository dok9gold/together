# PyAi 아키텍처 개선 및 확장 가이드 (tobe2)

> **목적**: UseCase DTO 반환 패턴 적용 + 사용자 인증 추가 + 향후 확장 방향 정리

---

## 📋 목차

1. [완료된 리팩토링 내용](#완료된-리팩토링-내용)
2. [아키텍처 설계 원칙](#아키텍처-설계-원칙)
3. [다음 단계: 사용자 인증](#다음-단계-사용자-인증)
4. [향후 확장 방향](#향후-확장-방향)
5. [파일 변경 요약](#파일-변경-요약)

---

## 완료된 리팩토링 내용

### 1. Response DTO 구조화

**변경 전 (app/models/schemas.py)**:
```python
class CookingResponse(BaseModel):
    status: str
    intent: Optional[str]
    data: Optional[dict] = None  # 😱 타입 안전성 없음
    message: Optional[str] = None
```

**변경 후**:
```python
# 의도별 명확한 DTO 정의
class RecipeResponse(BaseModel):
    status: Literal["success", "error"]
    code: str  # "RECIPE_CREATED" 등 시스템 코드
    intent: Literal["recipe_create"] = "recipe_create"
    data: RecipeResponseData  # 타입 안전
    message: Optional[str] = None

class RecommendationResponse(BaseModel):
    status: Literal["success", "error"]
    code: str
    intent: Literal["recommend"] = "recommend"
    data: RecommendationResponseData
    message: Optional[str] = None

class QuestionResponse(BaseModel):
    status: Literal["success", "error"]
    code: str
    intent: Literal["question"] = "question"
    data: QuestionResponseData
    message: Optional[str] = None

# Union Type
CookingResponse = Union[RecipeResponse, RecommendationResponse, QuestionResponse, ErrorResponse]
```

**장점**:
- ✅ 타입 안전성 (IDE 자동완성)
- ✅ 시스템 코드 중앙 관리 (`app/core/response_codes.py`)
- ✅ 의도별 명확한 데이터 구조

---

### 2. State 초기화 Factory 패턴

**변경 전 (app/application/use_cases/create_recipe_use_case.py:51-66)**:
```python
# UseCase에서 16줄의 초기화 코드
initial_state: CookingState = {
    "user_query": query,
    "primary_intent": "",
    "secondary_intents": [],
    "entities": {},
    "confidence": 0.0,
    "recipe_text": "",
    "recipes": [],
    "dish_names": [],
    "recommendation": "",
    "answer": "",
    "image_prompt": "",
    "image_url": None,
    "image_urls": [],
    "error": None
}
```

**변경 후 (app/domain/entities/cooking_state.py)**:
```python
def create_initial_state(query: str) -> CookingState:
    """초기 상태 생성 (Factory 함수)"""
    return {
        "user_query": query,
        "primary_intent": "",
        # ... (모든 필드 초기화)
    }

# UseCase에서는 1줄로!
initial_state = create_initial_state(query)
```

**장점**:
- ✅ 초기화 로직 재사용
- ✅ 테스트 코드에서도 동일하게 사용
- ✅ State 필드 추가 시 한 곳만 수정

---

### 3. UseCase가 DTO 반환 (핵심!)

**변경 전 (routes.py:33-121 - 58줄의 파싱 로직)**:
```python
@router.post("/cooking")
async def handle_cooking_query(request, use_case):
    result = await use_case.execute(request.query)  # Dict 반환

    # 😱 여기서 58줄 동안 JSON 파싱, 클리닝, 분기 처리
    response_data = {}
    if result.get("recommendation"):
        recommendation_data = json.loads(result["recommendation"])
        cleaned = [{"name": ..., "description": ..., "reason": ...}]
        response_data["recommendations"] = cleaned
    # ... 58줄 계속

    return CookingResponse(status="success", data=response_data)
```

**변경 후 (UseCase:48-88)**:
```python
# UseCase에서 DTO 변환까지 담당!
class CreateRecipeUseCase:
    async def execute(self, query: str) -> CookingResponse:
        # 1. 초기 상태 생성
        initial_state = create_initial_state(query)

        # 2. Workflow 실행
        result: CookingState = await self.workflow.run(initial_state)

        # 3. Domain → DTO 변환
        return self._to_dto(result)

    def _to_dto(self, state: CookingState) -> CookingResponse:
        """Domain Entity → DTO 변환 (58줄 로직 여기로 이동)"""
        intent = state["primary_intent"]

        if intent == "recipe_create":
            return self._create_recipe_response(state, metadata)
        elif intent == "recommend":
            return self._create_recommendation_response(state, metadata)
        # ...
```

**변경 후 (routes.py - 1줄!)**:
```python
@router.post("/cooking", response_model=CookingResponse)
async def handle_cooking_query(
    request: CookingRequest,
    use_case: CreateRecipeUseCase = Depends(get_create_recipe_use_case)
):
    """UseCase가 DTO 반환하므로 그냥 반환만"""
    return await use_case.execute(request.query)  # 끝!
```

**장점**:
- ✅ routes.py: 130줄 → 46줄 (84줄 감소!)
- ✅ 관심사 분리 (Presentation vs Application)
- ✅ Spring/NestJS 표준 패턴과 동일

---

## 아키텍처 설계 원칙

### 계층별 책임 정리

```
┌─────────────────────────────────────────────┐
│  Routes (Presentation Layer)                │
│  - 엔드포인트 정의                            │
│  - UseCase 호출 (1줄)                        │
│  - DTO 그대로 반환                            │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  UseCase (Application Layer)                │
│  책임:                                       │
│  - 워크플로우 실행 OR 직접 로직 구현          │
│  - Domain Entity → DTO 변환                 │
│  - 에러 핸들링 전략                          │
│  = Spring의 Service와 동일!                  │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  Workflow (복잡한 오케스트레이션)              │
│  책임:                                       │
│  - LangGraph 노드 실행 순서 정의              │
│  - 조건부 분기 (의도별 라우팅)                │
│  - 상태 관리                                 │
│  ※ 복잡한 AI 로직에만 사용                   │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  Workflow Nodes (단계별 비즈니스 로직)        │
│  책임:                                       │
│  - "언제" Adapter/Service 호출할지           │
│  - "어떤 데이터" 전달할지                     │
│  - 결과 검증 및 상태 업데이트                 │
│  ※ SQL, LLM, 외부 API 모두 호출 가능         │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  Domain Services (핵심 비즈니스 로직)         │
│  책임:                                       │
│  - Adapter 호출 전/후 처리                   │
│  - 비즈니스 규칙 검증                        │
│  - 도메인 지식 캡슐화                        │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  Adapters (외부 연결자)                      │
│  책임:                                       │
│  - HTTP 통신 (Anthropic, Replicate 등)      │
│  - API 포맷 맞추기 (프롬프트 생성)            │
│  - 응답 파싱 (JSON → Dict)                   │
│  ※ 비즈니스 로직 없음! 단순 연결자           │
└─────────────────────────────────────────────┘
```

### 복잡도별 패턴 선택

#### Level 1: UseCase에서 직접 처리 (간단)
```python
class GetRecipeUseCase:
    """간단한 조회 - Workflow 불필요"""
    def __init__(self, recipe_repository: IRecipeRepository):
        self.repository = recipe_repository

    async def execute(self, recipe_id: int) -> RecipeResponse:
        recipe = await self.repository.find_by_id(recipe_id)  # SQL 직접
        return RecipeResponse.from(recipe)
```

#### Level 2: UseCase + 여러 Service (중간)
```python
class CreateUserUseCase:
    """비즈니스 로직 있지만 Workflow는 과함"""
    def __init__(
        self,
        user_repository: IUserRepository,
        email_service: IEmailService,
        llm_adapter: ILLMPort
    ):
        self.repository = user_repository
        self.email = email_service
        self.llm = llm_adapter

    async def execute(self, request: CreateUserRequest) -> UserResponse:
        # 1. SQL 조회
        if await self.repository.exists_by_email(request.email):
            return ErrorResponse(code="USER_ALREADY_EXISTS", ...)

        # 2. LLM 직접 호출
        welcome_msg = await self.llm.generate_welcome_message(request.name)

        # 3. SQL 저장
        user = await self.repository.save(User(...))

        # 4. 외부 API 호출
        await self.email.send_welcome_email(user.email, welcome_msg)

        return UserResponse.from(user)
```

#### Level 3: UseCase + Workflow (복잡한 AI 오케스트레이션) ⭐ 현재
```python
class CreateRecipeUseCase:
    """복잡한 다단계 AI 워크플로우"""
    def __init__(self, workflow: CookingWorkflow):
        self.workflow = workflow

    async def execute(self, query: str) -> RecipeResponse:
        # Workflow에 위임 (의도 분류 → 레시피 생성 → 이미지 생성)
        state = await self.workflow.run(create_initial_state(query))
        return self._to_dto(state)
```

### Adapter vs UseCase/Workflow 책임 구분

| 항목 | Adapter (연결자) | UseCase/Workflow (실제 구현) |
|-----|-----------------|----------------------------|
| **역할** | "전화기" (통신 수단) | "전화 거는 사람" (의사결정) |
| **책임** | HTTP 통신, 포맷 변환, 파싱 | "언제, 누구에게, 무슨 내용" 결정 |
| **비즈니스 로직** | ❌ 없음 | ✅ 있음 |
| **예시** | `await self.client.messages.create(...)` | `if confidence < 0.5: use_default()` |

**잘못된 예** (Adapter에 비즈니스 로직):
```python
# ❌ 잘못됨
class AnthropicAdapter:
    async def classify_intent(self, query: str) -> Dict:
        result = await self.client.call(...)
        # 😱 비즈니스 로직이 Adapter에!
        if result["confidence"] < 0.5:
            result["primary_intent"] = "question"
        return result
```

**올바른 예** (비즈니스 로직은 Service/UseCase에):
```python
# ✅ 올바름
class AnthropicAdapter:
    async def classify_intent(self, query: str) -> Dict:
        # 단순 API 호출 및 파싱만
        response = await self.client.messages.create(...)
        return json.loads(response.content[0].text)

class CookingAssistantService:
    async def classify_intent(self, state: CookingState) -> Dict:
        result = await self.llm.classify_intent(state["user_query"])

        # ✅ 비즈니스 로직은 여기서!
        if result.get("confidence", 0) < 0.5:
            result["primary_intent"] = "question"

        return result
```

---

## 다음 단계: 사용자 인증

### 1. 인증 위치: Route 이전 (Dependency)

**실행 순서**:
```
HTTP Request
  ↓
FastAPI
  ↓
get_current_user() ← 인증 검증 (Route 이전!)
  ↓ (실패 → 401 에러)
  ↓ (성공 → user_id 추출)
handle_cooking_query() ← Route
  ↓
UseCase
```

### 2. 구현 가이드

#### 2.1. 인증 서비스 구현

```python
# ========== app/core/auth.py (새 파일) ==========
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

security = HTTPBearer()

class AuthService:
    """JWT 기반 인증 서비스"""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(
        self,
        user_id: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """액세스 토큰 생성

        Args:
            user_id: 사용자 ID
            expires_delta: 만료 시간 (기본 24시간)

        Returns:
            str: JWT 토큰
        """
        to_encode = {"sub": user_id}
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        to_encode.update({"exp": expire})

        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> str:
        """토큰 검증 및 user_id 추출

        Args:
            token: JWT 토큰

        Returns:
            str: user_id

        Raises:
            HTTPException: 토큰 검증 실패 시 401
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            user_id: str = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="유효하지 않은 토큰"
                )
            return user_id
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="토큰 검증 실패",
                headers={"WWW-Authenticate": "Bearer"}
            )
```

#### 2.2. Dependency 함수 추가

```python
# ========== app/api/dependencies.py (기존 파일 수정) ==========
from app.core.auth import AuthService, security
from fastapi.security import HTTPAuthorizationCredentials
from typing import Optional

# 인증 서비스 싱글톤
_auth_service: Optional[AuthService] = None

def get_auth_service() -> AuthService:
    """AuthService 싱글톤 반환"""
    global _auth_service
    if _auth_service is None:
        from app.core.config import settings
        _auth_service = AuthService(secret_key=settings.SECRET_KEY)
    return _auth_service


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> str:
    """현재 사용자 인증 (필수)

    Header: Authorization: Bearer <token>

    Returns:
        str: user_id

    Raises:
        HTTPException: 401 (토큰 없음 or 검증 실패)
    """
    token = credentials.credentials
    user_id = auth_service.verify_token(token)
    return user_id


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[str]:
    """옵셔널 인증 (토큰 없어도 통과)

    Returns:
        Optional[str]: user_id (토큰 없으면 None)
    """
    if credentials is None:
        return None

    try:
        return auth_service.verify_token(credentials.credentials)
    except HTTPException:
        return None  # 검증 실패해도 통과 (로그 남기는 게 좋음)
```

#### 2.3. Routes에 인증 적용

```python
# ========== app/api/routes.py (수정) ==========
from app.api.dependencies import get_current_user, get_optional_user

# 1. 공개 엔드포인트 (인증 불필요)
@router.get("/health")
async def health_check():
    """헬스 체크 (인증 불필요)"""
    return {"status": "healthy", "service": "cooking-assistant"}


# 2. 보호된 엔드포인트 (인증 필수) ⭐ 권장
@router.post("/cooking", response_model=CookingResponse)
async def handle_cooking_query(
    request: CookingRequest,
    user_id: str = Depends(get_current_user),  # ← 인증 추가!
    use_case: CreateRecipeUseCase = Depends(get_create_recipe_use_case)
):
    """
    인증된 사용자만 접근 가능

    Header:
        Authorization: Bearer <token>

    Args:
        request: 요리 쿼리
        user_id: 인증된 사용자 ID (자동 주입)
    """
    # user_id를 UseCase에 전달 가능
    return await use_case.execute(request.query, user_id=user_id)


# 3. 옵셔널 인증 (로그인 시 개인화)
@router.post("/cooking-public", response_model=CookingResponse)
async def handle_cooking_query_public(
    request: CookingRequest,
    user_id: Optional[str] = Depends(get_optional_user),  # ← 선택적 인증
    use_case: CreateRecipeUseCase = Depends(get_create_recipe_use_case)
):
    """
    토큰 없어도 접근 가능 (있으면 개인화)

    Args:
        user_id: 사용자 ID (없으면 None)
    """
    return await use_case.execute(request.query, user_id=user_id)
```

#### 2.4. UseCase에 user_id 전달

```python
# ========== app/application/use_cases/create_recipe_use_case.py (수정) ==========
class CreateRecipeUseCase:
    async def execute(
        self,
        query: str,
        user_id: Optional[str] = None  # ← user_id 파라미터 추가
    ) -> CookingResponse:
        """레시피 생성 워크플로우 실행

        Args:
            query: 사용자 쿼리
            user_id: 사용자 ID (인증된 경우)
        """
        logger.info(f"[UseCase] 실행 - user_id: {user_id}, query: {query[:50]}")

        try:
            initial_state = create_initial_state(query)
            # user_id를 state에 추가 (Workflow에서 사용 가능)
            initial_state["user_id"] = user_id

            result: CookingState = await self.workflow.run(initial_state)
            response = self._to_dto(result)

            return response
        except Exception as e:
            logger.error(f"[UseCase] 실행 오류: {e}", exc_info=True)
            return ErrorResponse(
                code=ResponseCode.INTERNAL_ERROR,
                message=f"서버 오류: {str(e)}"
            )
```

#### 2.5. 환경 변수 추가

```env
# .env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
REPLICATE_API_TOKEN=r8_xxxxx
SECRET_KEY=your-secret-key-here-change-in-production  # ← 추가 (필수!)
```

```python
# app/core/config.py (수정)
class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str
    REPLICATE_API_TOKEN: str
    SECRET_KEY: str  # ← 추가

    class Config:
        env_file = ".env"
```

#### 2.6. 의존성 설치

```bash
pip install python-jose[cryptography] passlib[bcrypt]
```

```txt
# requirements.txt에 추가
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

### 3. 인증 테스트 예시

```python
# 토큰 생성 (예시)
from app.core.auth import AuthService
from app.core.config import settings

auth_service = AuthService(secret_key=settings.SECRET_KEY)
token = auth_service.create_access_token(user_id="user123")
print(f"Token: {token}")

# cURL 테스트
curl -X POST http://localhost:8000/api/cooking \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"query": "김치찌개 만드는 법"}'
```

---

## 향후 확장 방향

### 1. RAG (Retrieval Augmented Generation) 추가

#### 1.1. Port 정의 (Domain Layer)

```python
# ========== app/domain/ports/vector_store_port.py (새 파일) ==========
from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass

@dataclass
class Document:
    """RAG 문서"""
    content: str
    metadata: dict
    score: float = 0.0

class IVectorStore(ABC):
    """벡터 DB Port (RAG용)"""

    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> List[Document]:
        """유사 문서 검색"""
        pass

    @abstractmethod
    async def add_documents(self, documents: List[Document]) -> None:
        """문서 추가 (임베딩 자동 생성)"""
        pass

    @abstractmethod
    async def delete_by_metadata(self, filter: dict) -> int:
        """메타데이터 기반 삭제"""
        pass
```

#### 1.2. Adapter 구현

```python
# ========== app/adapters/vector_store/chroma_adapter.py (새 파일) ==========
import chromadb
from app.domain.ports.vector_store_port import IVectorStore, Document

class ChromaVectorStoreAdapter(IVectorStore):
    """ChromaDB 기반 RAG 구현"""

    def __init__(self, client: chromadb.Client, collection_name: str = "recipes"):
        self.client = client
        self.collection = client.get_or_create_collection(collection_name)

    async def search(self, query: str, top_k: int = 5) -> List[Document]:
        """유사 레시피 검색"""
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )

        documents = []
        for i, doc in enumerate(results["documents"][0]):
            documents.append(Document(
                content=doc,
                metadata=results["metadatas"][0][i],
                score=results["distances"][0][i]
            ))
        return documents

    async def add_documents(self, documents: List[Document]) -> None:
        """레시피 임베딩 저장"""
        self.collection.add(
            documents=[d.content for d in documents],
            metadatas=[d.metadata for d in documents],
            ids=[f"doc_{i}" for i in range(len(documents))]
        )
```

#### 1.3. Workflow 노드에서 활용

```python
# ========== app/application/workflow/nodes/rag_recipe_generator_node.py (새 파일) ==========
class RAGRecipeGeneratorNode:
    """RAG 기반 레시피 생성"""

    def __init__(
        self,
        cooking_service: CookingAssistantService,
        vector_store: IVectorStore  # ← RAG 추가
    ):
        self.service = cooking_service
        self.vector_store = vector_store

    async def __call__(self, state: CookingState) -> CookingState:
        # 1. RAG: 유사 레시피 검색
        similar_recipes = await self.vector_store.search(
            query=state["user_query"],
            top_k=3
        )

        # 2. 컨텍스트 추가하여 레시피 생성
        state["rag_context"] = [r.content for r in similar_recipes]
        result_state = await self.service.generate_recipe(state)

        # 3. 생성된 레시피를 벡터 DB에 저장 (나중에 RAG로 활용)
        if result_state.get("recipe_text"):
            await self.vector_store.add_documents([
                Document(
                    content=result_state["recipe_text"],
                    metadata={"generated": True, "user_id": state.get("user_id")}
                )
            ])

        return result_state
```

#### 1.4. DI Container 확장

```python
# ========== app/core/container.py (수정) ==========
from app.adapters.vector_store.chroma_adapter import ChromaVectorStoreAdapter
import chromadb

class Container:
    def __init__(self):
        # 기존 Adapters
        self.llm_adapter = AnthropicLLMAdapter(settings)
        self.image_adapter = ReplicateImageAdapter(settings)

        # RAG Adapter 추가
        chroma_client = chromadb.Client()
        self.vector_store = ChromaVectorStoreAdapter(chroma_client)

        # Workflow Nodes (RAG 주입)
        self.rag_recipe_node = RAGRecipeGeneratorNode(
            cooking_service=self.cooking_service,
            vector_store=self.vector_store  # ← RAG 주입
        )

        # Workflow (RAG 노드로 교체)
        self.workflow = CookingWorkflow(
            recipe_generator=self.rag_recipe_node,  # ← RAG 노드 사용
            ...
        )
```

---

### 2. 대화 메모리 (Conversation Memory) 추가

#### 2.1. Port 정의

```python
# ========== app/domain/ports/memory_port.py (새 파일) ==========
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Message:
    """대화 메시지"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = None

class IConversationMemory(ABC):
    """대화 메모리 Port"""

    @abstractmethod
    async def get_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Message]:
        """대화 히스토리 조회"""
        pass

    @abstractmethod
    async def save_message(
        self,
        session_id: str,
        message: Message
    ) -> None:
        """메시지 저장"""
        pass

    @abstractmethod
    async def clear_history(self, session_id: str) -> None:
        """대화 히스토리 삭제"""
        pass
```

#### 2.2. Adapter 구현 (PostgreSQL 예시)

```python
# ========== app/adapters/memory/postgres_memory_adapter.py (새 파일) ==========
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.domain.ports.memory_port import IConversationMemory, Message

class PostgresConversationMemory(IConversationMemory):
    """PostgreSQL 기반 대화 메모리"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Message]:
        """대화 히스토리 조회 (최근순)"""
        result = await self.session.execute(
            select(ConversationMessage)
            .where(ConversationMessage.session_id == session_id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(limit)
        )
        rows = result.scalars().all()

        # Message 객체로 변환
        return [
            Message(
                role=row.role,
                content=row.content,
                timestamp=row.created_at
            )
            for row in reversed(rows)  # 시간순 정렬
        ]

    async def save_message(
        self,
        session_id: str,
        message: Message
    ) -> None:
        """메시지 저장"""
        msg = ConversationMessage(
            session_id=session_id,
            role=message.role,
            content=message.content
        )
        self.session.add(msg)
        await self.session.commit()
```

#### 2.3. Workflow 노드에서 활용

```python
# ========== app/application/workflow/nodes/context_aware_recipe_node.py (새 파일) ==========
class ContextAwareRecipeNode:
    """대화 메모리 기반 레시피 생성"""

    def __init__(
        self,
        cooking_service: CookingAssistantService,
        vector_store: IVectorStore,
        memory: IConversationMemory  # ← 메모리 추가
    ):
        self.service = cooking_service
        self.vector_store = vector_store
        self.memory = memory

    async def __call__(self, state: CookingState) -> CookingState:
        session_id = state.get("session_id", "default")

        # 1. RAG: 유사 레시피 검색
        similar_recipes = await self.vector_store.search(
            query=state["user_query"],
            top_k=5
        )

        # 2. 대화 히스토리 조회
        conversation_history = await self.memory.get_history(
            session_id,
            limit=10
        )

        # 3. 컨텍스트 포함하여 레시피 생성
        state["rag_context"] = [r.content for r in similar_recipes]
        state["conversation_history"] = [
            f"{m.role}: {m.content}" for m in conversation_history
        ]

        result_state = await self.service.generate_recipe(state)

        # 4. 대화 저장
        await self.memory.save_message(
            session_id,
            Message(role="user", content=state["user_query"])
        )
        await self.memory.save_message(
            session_id,
            Message(role="assistant", content=result_state["recipe_text"])
        )

        return result_state
```

---

### 3. 사용자 선호도 기반 개인화 (SQL)

```python
# ========== app/domain/repositories/user_repository.py (새 파일) ==========
from abc import ABC, abstractmethod
from typing import Optional

class IUserRepository(ABC):
    """사용자 Repository Port"""

    @abstractmethod
    async def get_preferences(self, user_id: str) -> Optional[dict]:
        """사용자 선호도 조회"""
        pass

    @abstractmethod
    async def save_preferences(self, user_id: str, preferences: dict) -> None:
        """사용자 선호도 저장"""
        pass


# ========== Workflow 노드에서 활용 ==========
class PersonalizedRecipeNode:
    def __init__(
        self,
        cooking_service: CookingAssistantService,
        user_repository: IUserRepository  # ← SQL Repository
    ):
        self.service = cooking_service
        self.user_repository = user_repository

    async def __call__(self, state: CookingState) -> CookingState:
        user_id = state.get("user_id")

        # SQL: 사용자 선호도 조회
        if user_id:
            preferences = await self.user_repository.get_preferences(user_id)
            state["user_preferences"] = preferences

        # 선호도 반영하여 레시피 생성
        result_state = await self.service.generate_recipe(state)

        return result_state
```

---

## 파일 변경 요약

### 신규 파일

```
app/
├── core/
│   ├── auth.py                    # ← 새로 추가: JWT 인증 서비스
│   └── response_codes.py          # ← 새로 추가: 시스템 코드 관리
├── domain/
│   └── ports/
│       ├── vector_store_port.py   # ← 향후 추가: RAG Port
│       └── memory_port.py         # ← 향후 추가: 메모리 Port
└── adapters/
    ├── vector_store/
    │   └── chroma_adapter.py      # ← 향후 추가: ChromaDB Adapter
    └── memory/
        └── postgres_memory_adapter.py  # ← 향후 추가: PostgreSQL 메모리
```

### 수정된 파일

| 파일 | 변경 내용 | 줄 수 변화 |
|-----|---------|----------|
| `app/models/schemas.py` | DTO 구조화 (RecipeResponse, RecommendationResponse 등) | +80줄 |
| `app/domain/entities/cooking_state.py` | `create_initial_state()` Factory 함수 추가 | +20줄 |
| `app/application/use_cases/create_recipe_use_case.py` | DTO 반환 + `_to_dto()` 메서드 구현 | 74줄 → 252줄 |
| `app/api/routes.py` | 파싱 로직 제거, UseCase 호출만 | 131줄 → 46줄 (85줄 감소!) |
| `app/api/dependencies.py` | `get_current_user()` 등 인증 Dependency 추가 | +30줄 |
| `app/core/config.py` | `SECRET_KEY` 환경 변수 추가 | +1줄 |
| `.env` | `SECRET_KEY` 추가 | +1줄 |
| `requirements.txt` | `python-jose`, `passlib` 추가 | +2줄 |

### 변경 전후 비교

```
변경 전: routes.py가 과도한 책임
routes.py (131줄)
  - 엔드포인트 정의
  - UseCase 호출
  - 😱 JSON 파싱 (58줄)
  - 😱 데이터 클리닝
  - 😱 타입 분기
  - 😱 DTO 생성

변경 후: 계층별 책임 명확
routes.py (46줄)
  - 엔드포인트 정의
  - 인증 (Dependency)
  - UseCase 호출 (1줄!)

use_case.py (252줄)
  - Workflow 실행
  - JSON 파싱
  - 데이터 클리닝
  - 타입 분기
  - DTO 생성
```

---

## 체크리스트

### 완료된 항목 ✅

- [x] Response DTO 구조화 (RecipeResponse, RecommendationResponse, QuestionResponse)
- [x] `create_initial_state()` Factory 함수 추가
- [x] UseCase에서 DTO 반환 (`_to_dto()` 메서드)
- [x] routes.py 간소화 (130줄 → 46줄)
- [x] 시스템 코드 중앙 관리 (`app/core/response_codes.py`)
- [x] 계층별 책임 명확화 문서

### 다음 단계 (인증) 🔜

- [ ] `app/core/auth.py` 파일 생성
- [ ] `SECRET_KEY` 환경 변수 추가
- [ ] `python-jose`, `passlib` 설치
- [ ] `get_current_user()` Dependency 구현
- [ ] routes.py에 `Depends(get_current_user)` 추가
- [ ] UseCase에 `user_id` 파라미터 추가
- [ ] 인증 테스트

### 향후 확장 (RAG + 메모리) 🚀

- [ ] `IVectorStore` Port 정의
- [ ] ChromaDB Adapter 구현
- [ ] `IConversationMemory` Port 정의
- [ ] PostgreSQL 메모리 Adapter 구현
- [ ] RAG/메모리 주입한 Workflow 노드 구현
- [ ] DI Container 확장

---

## 참고 자료

### 패턴 참고

- **Spring Boot Service 패턴**: UseCase = Service
- **Hexagonal Architecture**: Port/Adapter 패턴
- **Factory Pattern**: `create_initial_state()`
- **Dependency Injection**: FastAPI `Depends()`

### 라이브러리

- **JWT 인증**: `python-jose`, `passlib`
- **RAG**: `chromadb`, `langchain`
- **메모리**: `sqlalchemy` (PostgreSQL, MySQL 등)

---

## 마무리

이 문서는 **검토 후 코딩할 때 참고**할 수 있도록 작성되었습니다.

**핵심 원칙**:
1. ✅ **UseCase = Spring의 Service** (DTO 반환)
2. ✅ **Route = 1줄** (UseCase 호출만)
3. ✅ **Adapter = 연결자** (비즈니스 로직 없음)
4. ✅ **인증 = Dependency** (Route 이전 단계)
5. ✅ **확장 = Port 추가 → Adapter 구현 → 노드에 주입**

질문이나 수정 사항이 있으면 이 문서를 기반으로 논의해주세요! 🚀