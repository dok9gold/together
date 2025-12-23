# 화면 정의서

## 화면 구조

```
smart.html (메인 허브)
├── chat.html (AI 채팅)
├── recommend.html (요리 추천)
├── recipe.html (레시피 검색)
├── discount.html (할인상품 추천)
└── fridge.html (냉장고 털기)
```

---

## 1. smart.html - 스마트 AI 메인

### 화면 설명
기능 선택을 위한 메인 허브 페이지

### 기능 목록
| 기능 | 설명 |
|------|------|
| AI 채팅 이동 | chat.html로 이동 |
| 요리 추천 이동 | recommend.html로 이동 |
| 레시피 검색 이동 | recipe.html로 이동 |
| 할인상품 추천 이동 | discount.html로 이동 |
| 냉장고 털기 이동 | fridge.html로 이동 |

### API 요구사항
없음 (정적 페이지)

---

## 2. chat.html - AI 채팅

### 화면 설명
AI와 자유롭게 대화하며 요리 관련 질문을 할 수 있는 채팅 인터페이스

### 기능 목록
| 기능 | 설명 |
|------|------|
| 메시지 입력 | 텍스트 입력 (최대 500자) |
| 메시지 전송 | 엔터 또는 버튼 클릭으로 전송 |
| AI 응답 표시 | 타이핑 인디케이터 후 응답 표시 |
| 액션 버튼 | 레시피 보기, 장바구니 담기 등 |

### API 요구사항
| API | Method | Endpoint | Request | Response |
|-----|--------|----------|---------|----------|
| 채팅 메시지 전송 | POST | `/api/chat` | `{ message: string }` | `{ content: string, actions?: Action[] }` |

#### Response 타입
```typescript
interface ChatResponse {
  content: string;
  actions?: {
    label: string;
    type: 'recipe' | 'cart' | 'ingredients';
    data?: any;
  }[];
}
```

---

## 3. recommend.html - 요리 추천

### 화면 설명
카테고리와 조건을 선택하여 요리를 추천받는 페이지

### 기능 목록
| 기능 | 설명 |
|------|------|
| 카테고리 선택 | 한식, 중식, 일식, 양식 (다중 선택) |
| 조건 입력 | 추가 조건 텍스트 입력 |
| 추천 요청 | 선택/입력값 기반 추천 요청 |
| 결과 표시 | 추천 요리 목록 (요리별 재료 + 할인정보) |
| 레시피 보기 | 요리별 개별 버튼 → 모달로 레시피 상세 |
| 장바구니 담기 | 요리별 개별 버튼 → 해당 요리 재료 담기 |

### 화면 결과 예시
```
추천 결과:
┌─────────────────────────────────────┐
│ 김치찌개                [레시피] [담기] │
│ 재료: 김치, 돼지고기, 두부, 대파        │
│ 🏷️ 돼지고기 30% 할인                  │
├─────────────────────────────────────┤
│ 된장찌개                [레시피] [담기] │
│ 재료: 된장, 두부, 애호박, 감자          │
│ 🏷️ 두부 1+1                          │
└─────────────────────────────────────┘
```

### API 요구사항
| API | Method | Endpoint | Request | Response |
|-----|--------|----------|---------|----------|
| 요리 추천 | POST | `/api/recommend` | `{ categories: string[], condition?: string }` | `RecommendResponse` |

#### Response 타입
```typescript
interface RecommendResponse {
  recipes: {
    id: string;
    name: string;
    description: string;
    cookTime: string;
    difficulty: string;
    ingredients: string[];
    discountInfo?: {
      item: string;
      rate: string;
      price?: number;
    }[];
  }[];
  tip?: string;
}
```

---

## 4. recipe.html - 레시피 검색

### 화면 설명
요리명으로 레시피를 검색하는 페이지

### 기능 목록
| 기능 | 설명 |
|------|------|
| 검색어 입력 | 요리명 텍스트 입력 |
| 검색 실행 | 엔터 또는 버튼 클릭으로 검색 |
| 인기 검색어 | 빠른 검색을 위한 태그 버튼 |
| 결과 표시 | 레시피 정보 (조리시간, 난이도, 재료) |
| 레시피 상세 | 조리 단계 보기 |
| 장바구니 담기 | 필요 재료 장바구니에 추가 |

### API 요구사항
| API | Method | Endpoint | Request | Response |
|-----|--------|----------|---------|----------|
| 레시피 검색 | GET | `/api/recipe/search` | `?keyword={keyword}` | `RecipeResponse` |
| 인기 검색어 | GET | `/api/recipe/popular` | - | `string[]` |

#### Response 타입
```typescript
interface RecipeResponse {
  name: string;
  cookTime: string;
  difficulty: string;
  ingredients: string[];
  steps: string[];
}
```

---

## 5. discount.html - 할인상품 추천

### 화면 설명
오늘의 할인상품을 기반으로 요리를 추천받는 페이지

### 기능 목록
| 기능 | 설명 |
|------|------|
| 할인상품 표시 | 오늘의 할인상품 목록 (할인율 포함) |
| 상품 선택 | 관심있는 할인상품 선택 (다중 선택) |
| 상품 추가 | 다른 할인상품 직접 입력 |
| 추천 요청 | 선택한 상품 기반 요리 추천 |
| 결과 표시 | 추천 요리 및 할인 정보 표시 |
| 레시피 보기 | 추천된 요리의 레시피 상세 보기 |
| 장바구니 담기 | 할인상품 장바구니에 추가 |

### API 요구사항
| API | Method | Endpoint | Request | Response |
|-----|--------|----------|---------|----------|
| 오늘의 할인상품 | GET | `/api/discount/today` | - | `DiscountItem[]` |
| 할인상품 기반 추천 | POST | `/api/discount/recommend` | `{ items: string[] }` | `DiscountRecommendResponse` |

#### Response 타입
```typescript
interface DiscountItem {
  name: string;
  discountRate: string;  // "50%", "30%", "1+1" 등
  originalPrice?: number;
  discountPrice?: number;
}

interface DiscountRecommendResponse {
  recipe: {
    name: string;
    description: string;
  };
  discountInfo: {
    item: string;
    rate: string;
    price: number;
  }[];
}
```

---

## 6. fridge.html - 냉장고 털기

### 화면 설명
냉장고에 있는 재료를 선택하여 만들 수 있는 요리를 추천받는 페이지

### 기능 목록
| 기능 | 설명 |
|------|------|
| 재료 선택 | 기본 재료 목록에서 선택 (다중 선택) |
| 재료 추가 | 재료 직접 입력하여 추가 |
| 재료 삭제 | 추가한 재료 삭제 |
| 선택 재료 표시 | 현재 선택된 모든 재료 표시 |
| 추천 요청 | 선택한 재료 기반 요리 추천 |
| 결과 표시 | 추천 요리 및 할인 정보 표시 |
| 레시피 보기 | 추천된 요리의 레시피 상세 보기 |
| 장바구니 담기 | 부족한 재료 장바구니에 추가 |

### API 요구사항
| API | Method | Endpoint | Request | Response |
|-----|--------|----------|---------|----------|
| 재료 기반 추천 | POST | `/api/fridge/recommend` | `{ ingredients: string[] }` | `FridgeRecommendResponse` |

#### Response 타입
```typescript
interface FridgeRecommendResponse {
  recipe: {
    name: string;
    description: string;
  };
  availableIngredients: string[];
  missingIngredients: string[];
  discountInfo?: {
    item: string;
    rate: string;
    price: number;
  };
}
```

---

## 공통 API

### 장바구니
| API | Method | Endpoint | Request | Response |
|-----|--------|----------|---------|----------|
| 장바구니 추가 | POST | `/api/cart/add` | `{ items: CartItem[] }` | `{ success: boolean }` |
| 장바구니 조회 | GET | `/api/cart` | - | `CartItem[]` |

```typescript
interface CartItem {
  name: string;
  quantity?: number;
  price?: number;
  discountRate?: string;
}
```

### 레시피 상세
| API | Method | Endpoint | Request | Response |
|-----|--------|----------|---------|----------|
| 레시피 상세 | GET | `/api/recipe/{id}` | - | `RecipeDetail` |

```typescript
interface RecipeDetail {
  id: string;
  name: string;
  cookTime: string;
  difficulty: string;
  servings: string;
  ingredients: {
    name: string;
    amount: string;
  }[];
  steps: {
    order: number;
    description: string;
    tip?: string;
  }[];
}
```

---

## API 요약

| 화면 | API 개수 | 엔드포인트 |
|------|----------|------------|
| smart.html | 0 | - |
| chat.html | 1 | POST /api/chat |
| recommend.html | 1 | POST /api/recommend |
| recipe.html | 2 | GET /api/recipe/search, GET /api/recipe/popular |
| discount.html | 2 | GET /api/discount/today, POST /api/discount/recommend |
| fridge.html | 1 | POST /api/fridge/recommend |
| 공통 | 3 | POST /api/cart/add, GET /api/cart, GET /api/recipe/{id} |

**총 API 개수: 10개**
