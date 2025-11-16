# Domain vs Models - 폴더 구조 가이드

PyAi 프로젝트의 `app/domain/entities/`와 `app/models/schemas.py`의 차이를 설명합니다.

---

## 📋 목차

1. [개요](#개요)
2. [domain/entities - 비즈니스 엔티티](#domainentities---비즈니스-엔티티)
3. [models/schemas - API DTO](#modelsschemas---api-dto)
4. [비교표](#비교표)
5. [실제 사용 흐름](#실제-사용-흐름)
6. [예제 코드](#예제-코드)

---

## 개요

DDD (Domain-Driven Design)와 Hexagonal Architecture에서는 **도메인 모델**과 **DTO**를 명확히 구분합니다.

- **Domain Entity**: 비즈니스 규칙과 로직을 담는 핵심 객체
- **DTO (Data Transfer Object)**: HTTP API 요청/응답 직렬화용 객체

---

## domain/entities - 비즈니스 엔티티

### 목적
비즈니스 로직과 도메인 규칙을 담는 핵심 객체

### 특징
- `@dataclass` 사용 (데이터 + 행위)
- **비즈니스 메서드 포함**: `validate()`, `get_total_steps()` 등
- **도메인 규칙 검증**: 난이도는 "쉬움/중간/어려움"만 허용
- 외부 시스템과 무관 (순수한 비즈니스 로직)
- **불변성(Immutability) 지향**: 도메인 객체의 상태 변경은 명시적 메서드로만

### 코드 예시

```python
# app/domain/entities/recipe.py
from dataclasses import dataclass
from typing import List

@dataclass
class Recipe:
    """레시피 엔티티 (비즈니스 객체)

    레시피의 핵심 정보를 담는 도메인 모델입니다.
    """
    title: str
    ingredients: List[str]
    steps: List[str]
    cooking_time: str
    difficulty: str

    def validate(self) -> bool:
        """레시피 유효성 검증 (비즈니스 규칙)

        Returns:
            bool: 유효하면 True, 아니면 False
        """
        # 제목 검증
        if not self.title or len(self.title) < 2:
            return False

        # 재료 검증
        if not self.ingredients or len(self.ingredients) < 1:
            return False

        # 조리 단계 검증
        if not self.steps or len(self.steps) < 1:
            return False

        # 난이도 검증 (비즈니스 규칙!)
        valid_difficulties = ["쉬움", "중간", "어려움"]
        if self.difficulty not in valid_difficulties:
            return False

        return True

    def get_total_steps(self) -> int:
        """조리 단계 개수 반환

        Returns:
            int: 조리 단계 개수
        """
        return len(self.steps)

    def get_ingredient_count(self) -> int:
        """재료 개수 반환

        Returns:
            int: 재료 개수
        """
        return len(self.ingredients)
```

### 사용처
- Domain Services (`app/domain/services/`)
- Workflow Nodes (`app/application/workflow/nodes/`)
- UseCase (`app/application/use_cases/`)

---

## models/schemas - API DTO

### 목적
HTTP API 요청/응답 직렬화 (JSON ↔ Python 객체)

### 특징
- `BaseModel` (Pydantic) 사용
- **HTTP 통신 전용**: FastAPI가 자동으로 JSON 변환
- **비즈니스 로직 없음**: 데이터 구조만 정의
- **API 문서 자동 생성**: OpenAPI/Swagger 스펙
- **검증 로직**: Pydantic Field 제약 조건만 (비즈니스 규칙은 Domain에서)

### 코드 예시

```python
# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

# ============ Request DTOs ============

class CookingRequest(BaseModel):
    """요리 관련 요청 (레시피 생성, 추천, 질문 등)"""
    query: str = Field(
        ...,
        description="요리 관련 쿼리 (예: '파스타 카르보나라 만드는 법')"
    )


# ============ Response DTOs ============

class ResponseMetadata(BaseModel):
    """응답 메타데이터 (모든 응답에 공통)"""
    entities: Dict[str, Any] = Field(
        default_factory=dict,
        description="추출된 엔티티"
    )
    confidence: float = Field(
        default=0.0,
        description="의도 파악 확신도"
    )
    secondary_intents_processed: List[str] = Field(
        default_factory=list,
        description="처리된 부가 의도들"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="응답 생성 시각"
    )


class RecipeResponseData(BaseModel):
    """레시피 생성 응답 데이터"""
    recipe: Optional[Dict[str, Any]] = Field(
        None,
        description="단일 레시피"
    )
    recipes: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="복수 레시피"
    )
    image_url: Optional[str] = Field(
        None,
        description="생성된 음식 이미지 URL"
    )
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)


class RecipeResponse(BaseModel):
    """레시피 생성 응답"""
    status: Literal["success", "error"] = "success"
    code: str = Field(..., description="응답 코드 (예: RECIPE_CREATED)")
    intent: Literal["recipe_create"] = "recipe_create"
    data: RecipeResponseData
    message: Optional[str] = Field(
        None,
        description="추가 메시지 (예: 이미지 생성 실패)"
    )
```

### 사용처
- Routes (`app/api/routes.py`)
- UseCase의 반환 타입 (`app/application/use_cases/`)
- FastAPI의 `response_model`

---

## 비교표

| 항목 | domain/entities | models/schemas |
|------|----------------|----------------|
| **역할** | 비즈니스 로직 | HTTP 직렬화 |
| **타입** | `@dataclass` | Pydantic `BaseModel` |
| **메서드** | 비즈니스 로직 포함 | 거의 없음 (검증만) |
| **의존성** | 외부 시스템 무관 | FastAPI에 종속 |
| **검증** | 도메인 규칙 검증 | Pydantic Field 제약 |
| **예시** | `Recipe.validate()` | `RecipeResponse` (JSON 변환) |
| **사용처** | Domain Services, Workflow | Routes, UseCase → DTO 변환 |
| **불변성** | 명시적 메서드로만 변경 | 자유로운 생성/변경 |
| **테스트** | 비즈니스 로직 단위 테스트 | JSON 직렬화 테스트 |

---

## 실제 사용 흐름

```
1. API 요청 (JSON)
   ↓ (FastAPI 자동 변환)
2. CookingRequest (DTO) ← models/schemas.py
   ↓ (routes.py → UseCase)
3. UseCase
   ↓ (Workflow 실행)
4. Recipe (Entity) ← domain/entities/recipe.py
   ↓ (비즈니스 로직 실행)
5. Recipe.validate() → True/False
   ↓ (UseCase의 _to_dto() 메서드)
6. RecipeResponse (DTO) ← models/schemas.py
   ↓ (FastAPI 자동 변환)
7. API 응답 (JSON)
```

### 상세 흐름 예시

```python
# 1. API 요청 수신
POST /api/cooking
{
  "query": "김치찌개 만드는 법"
}

# 2. routes.py - DTO로 자동 변환
@router.post("/cooking", response_model=CookingResponse)
async def handle_cooking_query(
    request: CookingRequest,  # ← Pydantic 자동 변환
    use_case: CreateRecipeUseCase = Depends(...)
):
    return await use_case.execute(request.query)

# 3. UseCase - Workflow 실행
async def execute(self, query: str) -> CookingResponse:
    initial_state = create_initial_state(query)
    result: CookingState = await self.workflow.run(initial_state)
    return self._to_dto(result)  # ← Domain → DTO 변환

# 4. Workflow - Domain Entity 생성 및 검증
def recipe_generator_node(state: CookingState):
    # LLM으로부터 레시피 데이터 생성
    recipe = Recipe(
        title="김치찌개",
        ingredients=["김치 300g", "돼지고기 200g"],
        steps=["1. 김치를 썬다", "2. 고기를 볶는다"],
        cooking_time="30분",
        difficulty="쉬움"
    )

    # 비즈니스 규칙 검증
    if not recipe.validate():
        raise ValueError("유효하지 않은 레시피")

    # state 업데이트
    state["recipe"] = recipe
    return state

# 5. UseCase - DTO 변환
def _to_dto(self, result: CookingState) -> CookingResponse:
    if result["primary_intent"] == "recipe_create":
        return RecipeResponse(
            status="success",
            code="RECIPE_CREATED",
            intent="recipe_create",
            data=RecipeResponseData(
                recipe=asdict(result["recipe"]),  # Entity → Dict
                image_url=result.get("image_url"),
                metadata=ResponseMetadata(...)
            )
        )

# 6. API 응답 (FastAPI 자동 JSON 변환)
{
  "status": "success",
  "code": "RECIPE_CREATED",
  "intent": "recipe_create",
  "data": {
    "recipe": {
      "title": "김치찌개",
      "ingredients": ["김치 300g", "돼지고기 200g"],
      "steps": ["1. 김치를 썬다", "2. 고기를 볶는다"],
      "cooking_time": "30분",
      "difficulty": "쉬움"
    },
    "image_url": "https://...",
    "metadata": {...}
  }
}
```

---

## 예제 코드

### Domain Entity 예시

```python
# app/domain/entities/recipe.py
from dataclasses import dataclass
from typing import List

@dataclass
class Recipe:
    """레시피 엔티티 - 비즈니스 로직 포함"""
    title: str
    ingredients: List[str]
    steps: List[str]
    cooking_time: str
    difficulty: str

    def validate(self) -> bool:
        """도메인 규칙 검증"""
        valid_difficulties = ["쉬움", "중간", "어려움"]
        return (
            self.title and len(self.title) >= 2
            and self.ingredients and len(self.ingredients) >= 1
            and self.steps and len(self.steps) >= 1
            and self.difficulty in valid_difficulties
        )

    def is_quick_recipe(self) -> bool:
        """빠른 레시피 여부 (비즈니스 로직)"""
        # "30분" → 30 추출
        time_str = self.cooking_time.replace("분", "").strip()
        try:
            minutes = int(time_str)
            return minutes <= 30
        except ValueError:
            return False

    def get_total_steps(self) -> int:
        """조리 단계 개수"""
        return len(self.steps)
```

### DTO 예시

```python
# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class RecipeResponseData(BaseModel):
    """레시피 응답 데이터 - 직렬화만 담당"""
    recipe: Optional[Dict[str, Any]] = Field(
        None,
        description="단일 레시피"
    )
    image_url: Optional[str] = Field(
        None,
        description="생성된 음식 이미지 URL"
    )
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)

    # 비즈니스 로직 없음! 데이터 구조만 정의
```

### UseCase에서의 변환

```python
# app/application/use_cases/create_recipe_use_case.py
from dataclasses import asdict

class CreateRecipeUseCase:
    def _to_dto(self, result: CookingState) -> CookingResponse:
        """Domain Entity → DTO 변환"""

        if result["primary_intent"] == "recipe_create":
            # Entity를 Dict로 변환 (Pydantic이 이해할 수 있게)
            recipe_dict = asdict(result["recipe"]) if result.get("recipe") else None

            return RecipeResponse(
                status="success",
                code=ResponseCodes.RECIPE_CREATED,
                intent="recipe_create",
                data=RecipeResponseData(
                    recipe=recipe_dict,
                    image_url=result.get("image_url"),
                    metadata=ResponseMetadata(
                        entities=result.get("entities", {}),
                        confidence=result.get("confidence", 0.0),
                        secondary_intents_processed=result.get("secondary_intents_processed", [])
                    )
                )
            )
```

---

## 핵심 요약

### domain/entities
- **"비즈니스의 핵심 개념"**
- 도메인 규칙 검증 (`validate()`)
- 비즈니스 메서드 제공 (`is_quick_recipe()`)
- 외부 시스템과 무관

### models/schemas
- **"API 계약서"**
- HTTP 요청/응답 직렬화
- OpenAPI 문서 자동 생성
- FastAPI에 종속

### 설계 원칙
1. **Domain Entity는 순수하게 유지** (외부 의존성 최소화)
2. **DTO는 API 계층에만 사용** (Domain 계층에 침투하지 않음)
3. **UseCase가 변환 책임** (Domain → DTO)
4. **비즈니스 로직은 Domain에만** (DTO는 데이터 구조만)

---

## 참고 문서

- **프레임워크 가이드**: [docs/FRAMEWORK.md](FRAMEWORK.md)
- **아키텍처 설계**: [docs/TODO.md](TODO.md)
- **문서 요약**: [docs/SUMMARY.md](SUMMARY.md)

---

**작성일**: 2025-01-16
**버전**: 1.0.0
