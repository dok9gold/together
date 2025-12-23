# core/database

PostgreSQL 비동기 커넥션풀 및 트랜잭션 관리 모듈

## 구조

```
core/database/
├── __init__.py
├── base.py              # BaseDatabase (ABC)
├── context.py           # ContextVar로 트랜잭션 컨텍스트 관리
├── transaction.py       # @transactional 데코레이터
├── registry.py          # DatabaseRegistry (다중 DB 관리)
├── exception.py         # 예외 클래스
└── postgres/
    └── connection.py    # PostgresDatabase, TransactionContext
```

## 사용법

### 1. 초기화 (main.py lifespan)

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.database.postgres.connection import PostgresDatabase
from core.database.registry import DatabaseRegistry
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # DB 초기화
    db = await PostgresDatabase.create('main', {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'together'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'pool': {
            'min_size': 2,
            'max_size': 10,
        }
    })

    # 레지스트리에 등록
    DatabaseRegistry.register('main', db)

    # app.state에도 저장 (선택)
    app.state.db = db

    yield

    # 종료 시 정리
    await DatabaseRegistry.close_all()

app = FastAPI(lifespan=lifespan)
```

### 2. 서비스/Repository에서 사용

#### 방법 1: @transactional 데코레이터

```python
from core.database.transaction import transactional
from core.database.context import get_connection
from core.database.registry import DatabaseRegistry

db = DatabaseRegistry.get('main')

@transactional(db)
async def create_user(name: str, email: str) -> dict:
    ctx = get_connection('main')
    await ctx.execute(
        "INSERT INTO users (name, email) VALUES ($1, $2)",
        name, email
    )
    row = await ctx.fetch_one(
        "SELECT * FROM users WHERE email = $1",
        email
    )
    return dict(row)
```

#### 방법 2: async with 직접 사용

```python
async def get_user(user_id: str) -> dict | None:
    db = DatabaseRegistry.get('main')

    async with db.transaction() as ctx:
        row = await ctx.fetch_one(
            "SELECT * FROM users WHERE id = $1",
            user_id
        )
        return dict(row) if row else None
```

#### 방법 3: 읽기 전용 트랜잭션

```python
from core.database.transaction import transactional_readonly

@transactional_readonly(db)
async def list_users() -> list[dict]:
    ctx = get_connection('main')
    rows = await ctx.fetch_all("SELECT * FROM users")
    return [dict(row) for row in rows]
```

### 3. 워크플로우 노드에서 사용

```python
from core.database.registry import DatabaseRegistry
from core.database.context import get_connection

class RecipeGeneratorNode:
    async def execute(self, state):
        db = DatabaseRegistry.get('main')

        async with db.transaction() as ctx:
            # 할인 상품 조회
            discounts = await ctx.fetch_all(
                "SELECT * FROM discounts WHERE is_active = true"
            )

            # 레시피 저장
            await ctx.execute(
                "INSERT INTO recipes (name, content) VALUES ($1, $2)",
                state['recipe_name'],
                state['recipe_content']
            )

        return state
```

## TransactionContext 메서드

| 메서드 | 설명 | 반환 |
|--------|------|------|
| `execute(sql, *args)` | INSERT, UPDATE, DELETE 실행 | str (상태) |
| `executemany(sql, args)` | 다중 행 실행 | None |
| `fetch_one(sql, *args)` | 단일 행 조회 | Record \| None |
| `fetch_all(sql, *args)` | 모든 행 조회 | list[Record] |
| `fetch_val(sql, *args)` | 단일 값 조회 | Any |

## 예외

| 예외 | 설명 |
|------|------|
| `ConnectionPoolExhaustedError` | 커넥션풀 고갈 |
| `ReadOnlyTransactionError` | 읽기 전용에서 쓰기 시도 |
| `TransactionError` | 트랜잭션 관련 에러 |

## 환경변수

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=together
DB_USER=postgres
DB_PASSWORD=yourpassword
```

## 의존성

```
asyncpg
```
