# Phase 4: Conversation Memory 통합

> **목표**: 대화 히스토리 관리 및 멀티턴 대화 지원

## 개요

Conversation Memory를 통해:
- 사용자별 대화 히스토리 저장/조회
- 컨텍스트를 유지한 멀티턴 대화 가능
- 세션 관리 및 대화 맥락 활용

---

## 1. 아키텍처 설계

### 1.1 Port 인터페이스

```python
# app/core/ports/memory_port.py
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Message:
    """대화 메시지"""
    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime
    metadata: dict = None

class IConversationMemory(ABC):
    """Conversation Memory Port 인터페이스"""

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
        """히스토리 초기화"""
        pass

    @abstractmethod
    async def get_session_count(self, session_id: str) -> int:
        """세션 내 메시지 수 조회"""
        pass
```

---

## 2. Adapter 구현

### 2.1 PostgreSQL Memory Adapter

```python
# app/core/adapters/memory/postgres_memory_adapter.py
from sqlalchemy import Column, String, DateTime, Integer, Text, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.ports.memory_port import IConversationMemory, Message

Base = declarative_base()

class ConversationHistory(Base):
    """대화 히스토리 테이블"""
    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(255), index=True, nullable=False)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    metadata = Column(JSON, nullable=True)

class PostgresMemoryAdapter(IConversationMemory):
    """PostgreSQL Conversation Memory Adapter"""

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    async def get_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Message]:
        """대화 히스토리 조회 (최근 N개)"""
        session = self.SessionLocal()
        try:
            records = session.query(ConversationHistory)\
                .filter(ConversationHistory.session_id == session_id)\
                .order_by(ConversationHistory.timestamp.desc())\
                .limit(limit)\
                .all()

            # 시간순 정렬 (오래된 것부터)
            records.reverse()

            return [
                Message(
                    role=record.role,
                    content=record.content,
                    timestamp=record.timestamp,
                    metadata=record.metadata
                )
                for record in records
            ]
        finally:
            session.close()

    async def save_message(
        self,
        session_id: str,
        message: Message
    ) -> None:
        """메시지 저장"""
        session = self.SessionLocal()
        try:
            record = ConversationHistory(
                session_id=session_id,
                role=message.role,
                content=message.content,
                timestamp=message.timestamp,
                metadata=message.metadata
            )
            session.add(record)
            session.commit()
        finally:
            session.close()

    async def clear_history(self, session_id: str) -> None:
        """히스토리 초기화"""
        session = self.SessionLocal()
        try:
            session.query(ConversationHistory)\
                .filter(ConversationHistory.session_id == session_id)\
                .delete()
            session.commit()
        finally:
            session.close()

    async def get_session_count(self, session_id: str) -> int:
        """세션 내 메시지 수"""
        session = self.SessionLocal()
        try:
            return session.query(ConversationHistory)\
                .filter(ConversationHistory.session_id == session_id)\
                .count()
        finally:
            session.close()
```

### 2.2 Redis Memory Adapter (캐시용)

```python
# app/core/adapters/memory/redis_memory_adapter.py
import redis.asyncio as redis
import json
from app.core.ports.memory_port import IConversationMemory, Message
from datetime import datetime

class RedisMemoryAdapter(IConversationMemory):
    """Redis Conversation Memory Adapter (캐시 전용)"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=True)

    def _get_key(self, session_id: str) -> str:
        """Redis 키 생성"""
        return f"conversation:{session_id}"

    async def get_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Message]:
        """대화 히스토리 조회"""
        key = self._get_key(session_id)
        messages = await self.redis.lrange(key, -limit, -1)

        return [
            Message(
                role=msg_dict["role"],
                content=msg_dict["content"],
                timestamp=datetime.fromisoformat(msg_dict["timestamp"]),
                metadata=msg_dict.get("metadata")
            )
            for msg in messages
            for msg_dict in [json.loads(msg)]
        ]

    async def save_message(
        self,
        session_id: str,
        message: Message
    ) -> None:
        """메시지 저장 (TTL 24시간)"""
        key = self._get_key(session_id)
        msg_json = json.dumps({
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "metadata": message.metadata
        })

        await self.redis.rpush(key, msg_json)
        await self.redis.expire(key, 86400)  # 24시간 TTL

    async def clear_history(self, session_id: str) -> None:
        """히스토리 초기화"""
        key = self._get_key(session_id)
        await self.redis.delete(key)

    async def get_session_count(self, session_id: str) -> int:
        """세션 내 메시지 수"""
        key = self._get_key(session_id)
        return await self.redis.llen(key)
```

---

## 3. Workflow 통합

### 3.1 Context-Aware Node

```python
# app/cooking_assistant/workflow/nodes/context_aware_recipe_node.py
from app.cooking_assistant.workflow.nodes.base_node import BaseNode
from app.core.ports.llm_port import ILLMPort
from app.core.ports.memory_port import IConversationMemory, Message
from app.core.prompt_loader import PromptLoader
from datetime import datetime

class ContextAwareRecipeNode(BaseNode):
    """대화 컨텍스트를 활용한 레시피 생성 노드"""

    def __init__(
        self,
        llm_port: ILLMPort,
        memory_port: IConversationMemory,
        prompt_loader: PromptLoader
    ):
        super().__init__("recipe_create")
        self.llm_port = llm_port
        self.memory_port = memory_port
        self.prompt_loader = prompt_loader

    async def execute(self, state):
        """컨텍스트 기반 레시피 생성"""
        user_query = state["user_query"]
        session_id = state.get("session_id", "default")

        # 1. 대화 히스토리 조회
        history = await self.memory_port.get_history(session_id, limit=5)

        # 2. 컨텍스트 구성
        context = self._build_context(history)

        # 3. 프롬프트 렌더링
        prompt = self.prompt_loader.render(
            "cooking.generate_recipe_with_context",
            query=user_query,
            context=context
        )

        # 4. LLM 호출
        recipe_data = await self.llm_port.generate_recipe(prompt)

        # 5. 대화 저장
        await self._save_conversation(session_id, user_query, recipe_data)

        return {"recipe": recipe_data}

    def _build_context(self, history: List[Message]) -> str:
        """대화 히스토리를 컨텍스트로 변환"""
        if not history:
            return "이전 대화 없음"

        context_parts = []
        for msg in history:
            role_label = "사용자" if msg.role == "user" else "어시스턴트"
            context_parts.append(f"{role_label}: {msg.content[:100]}")  # 최대 100자

        return "\n".join(context_parts)

    async def _save_conversation(
        self,
        session_id: str,
        user_query: str,
        recipe_data: dict
    ):
        """대화 저장"""
        # 사용자 메시지
        await self.memory_port.save_message(
            session_id=session_id,
            message=Message(
                role="user",
                content=user_query,
                timestamp=datetime.now()
            )
        )

        # 어시스턴트 응답
        assistant_content = f"레시피: {recipe_data['title']}"
        await self.memory_port.save_message(
            session_id=session_id,
            message=Message(
                role="assistant",
                content=assistant_content,
                timestamp=datetime.now(),
                metadata={"recipe_id": recipe_data.get("id")}
            )
        )
```

### 3.2 프롬프트 추가

```yaml
# app/cooking_assistant/prompts/cooking.yaml
generate_recipe_with_context:
  system: |
    당신은 한국 요리 전문가입니다.
    이전 대화 맥락을 고려하여 레시피를 생성하세요.

  user: |
    ## 이전 대화
    {{ context }}

    ## 현재 요청
    {{ query }}

    ## 출력 형식
    JSON으로 레시피를 생성하세요:
    {
      "title": "레시피 제목",
      "ingredients": ["재료1", "재료2", ...],
      "steps": ["1. ...", "2. ...", ...]
    }
```

---

## 4. API 수정

### 4.1 Request DTO에 session_id 추가

```python
# app/cooking_assistant/models/schemas.py
class CookingRequest(BaseModel):
    query: str
    session_id: Optional[str] = None  # 세션 ID (없으면 자동 생성)
```

### 4.2 Routes 수정

```python
# app/cooking_assistant/api/routes.py
from uuid import uuid4

@router.post("/cooking")
async def create_cooking_response(
    request: CookingRequest,
    current_user: dict = Depends(get_current_user)
):
    """요리 어시스턴트 API (멀티턴 대화 지원)"""
    # session_id 없으면 생성
    session_id = request.session_id or str(uuid4())

    result = await cooking_service.process_request(
        query=request.query,
        user_id=current_user["user_id"],
        session_id=session_id
    )

    # 응답에 session_id 포함
    return {
        **result,
        "session_id": session_id
    }
```

---

## 5. 의존성 주입 설정

```python
# app/cooking_assistant/module.py
from app.core.adapters.memory.postgres_memory_adapter import PostgresMemoryAdapter
from app.core.adapters.memory.redis_memory_adapter import RedisMemoryAdapter
from app.core.ports.memory_port import IConversationMemory

class CookingModule(Module):
    @singleton
    @provider
    def provide_memory_adapter(self, settings: Settings) -> IConversationMemory:
        """Memory Adapter 제공 (환경별 분기)"""
        if settings.MEMORY_PROVIDER == "postgres":
            return PostgresMemoryAdapter(settings.DATABASE_URL)
        elif settings.MEMORY_PROVIDER == "redis":
            return RedisMemoryAdapter(settings.REDIS_URL)
        else:
            # 기본: In-Memory (개발용)
            return InMemoryAdapter()

    @singleton
    @provider
    def provide_context_aware_recipe_node(
        self,
        llm_port: ILLMPort,
        memory_port: IConversationMemory,
        prompt_loader: PromptLoader
    ) -> ContextAwareRecipeNode:
        """Context-Aware Recipe Node 제공"""
        return ContextAwareRecipeNode(llm_port, memory_port, prompt_loader)
```

---

## 6. 설정 파일 업데이트

### 6.1 환경 변수

```bash
# .env
MEMORY_PROVIDER=postgres
DATABASE_URL=postgresql://user:password@localhost:5432/cooking_db

# 또는 Redis
MEMORY_PROVIDER=redis
REDIS_URL=redis://localhost:6379
```

### 6.2 Settings

```python
# app/core/config.py
class Settings(BaseSettings):
    MEMORY_PROVIDER: str = "postgres"
    DATABASE_URL: Optional[str] = None
    REDIS_URL: Optional[str] = None
```

---

## 7. 데이터베이스 마이그레이션

### 7.1 Alembic 설정

```bash
# 설치
pip install alembic psycopg2-binary

# 초기화
alembic init alembic

# 마이그레이션 생성
alembic revision --autogenerate -m "Create conversation_history table"

# 적용
alembic upgrade head
```

### 7.2 마이그레이션 파일 예시

```python
# alembic/versions/xxx_create_conversation_history.py
def upgrade():
    op.create_table(
        'conversation_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_session_id', 'conversation_history', ['session_id'])
```

---

## 8. 테스트

### 8.1 Memory Adapter 단위 테스트

```python
# tests/adapters/test_postgres_memory.py
@pytest.mark.asyncio
async def test_save_and_get_history():
    """메시지 저장 및 조회 테스트"""
    adapter = PostgresMemoryAdapter("sqlite:///:memory:")  # 테스트용 in-memory DB

    session_id = "test_session"
    message = Message(
        role="user",
        content="김치찌개 레시피 알려줘",
        timestamp=datetime.now()
    )

    await adapter.save_message(session_id, message)
    history = await adapter.get_history(session_id)

    assert len(history) == 1
    assert history[0].content == "김치찌개 레시피 알려줘"
```

### 8.2 멀티턴 대화 통합 테스트

```python
# tests/workflows/test_multiturn_conversation.py
@pytest.mark.asyncio
async def test_multiturn_conversation():
    """멀티턴 대화 테스트"""
    session_id = "test_multiturn"

    # Turn 1
    response1 = await cooking_service.process_request(
        query="김치찌개 레시피 알려줘",
        session_id=session_id
    )

    # Turn 2 (컨텍스트 활용)
    response2 = await cooking_service.process_request(
        query="여기에 버섯 추가할 수 있어?",
        session_id=session_id
    )

    # 히스토리 검증
    history = await memory_port.get_history(session_id)
    assert len(history) == 4  # 2턴 * 2메시지(user + assistant)
```

---

## 9. 성능 최적화

### 9.1 Composite Adapter (Postgres + Redis)

```python
# app/core/adapters/memory/composite_memory_adapter.py
class CompositeMemoryAdapter(IConversationMemory):
    """PostgreSQL (영구 저장) + Redis (캐시) 조합"""

    def __init__(
        self,
        postgres_adapter: PostgresMemoryAdapter,
        redis_adapter: RedisMemoryAdapter
    ):
        self.postgres = postgres_adapter
        self.redis = redis_adapter

    async def save_message(self, session_id: str, message: Message):
        """양쪽 모두 저장"""
        await self.postgres.save_message(session_id, message)
        await self.redis.save_message(session_id, message)

    async def get_history(self, session_id: str, limit: int = 10):
        """Redis 먼저 조회, 없으면 Postgres"""
        history = await self.redis.get_history(session_id, limit)
        if not history:
            history = await self.postgres.get_history(session_id, limit)
            # Redis에 캐싱
            for msg in history:
                await self.redis.save_message(session_id, msg)
        return history
```

---

## 체크리스트

### 구현
- [ ] IConversationMemory 인터페이스 정의
- [ ] PostgresMemoryAdapter 구현
- [ ] RedisMemoryAdapter 구현 (선택)
- [ ] ContextAwareRecipeNode 구현
- [ ] 프롬프트 추가 (generate_recipe_with_context)
- [ ] API에 session_id 추가
- [ ] Module.py에 DI 설정 추가
- [ ] Alembic 마이그레이션 설정

### 테스트
- [ ] Memory Adapter 단위 테스트
- [ ] 멀티턴 대화 통합 테스트
- [ ] 세션 격리 테스트

### 문서화
- [ ] README.md에 멀티턴 대화 예시 추가
- [ ] API 문서에 session_id 파라미터 설명

---

## 예상 효과

- **자연스러운 대화**: "이거" "그거" 같은 대명사 활용 가능
- **컨텍스트 유지**: 이전 대화 내용을 기억하여 정확한 응답
- **사용자 경험 향상**: 반복 설명 불필요

---

## 다음 단계

Phase 4 완료 후 → [Phase 5: 프레임워크화](PHASE5.md)
