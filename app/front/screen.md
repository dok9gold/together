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

## 공통 UI 컴포넌트

### 레시피 카드
모든 추천 결과 페이지에서 동일한 구조 사용

```
┌─────────────────────────────────────┐
│ 요리명                  [레시피] [담기] │
│ 재료: 재료1, 재료2, 재료3...           │
│ 🏷️ 할인정보 (있을 경우)               │
└─────────────────────────────────────┘
```

- **[레시피]** 버튼: 모달 팝업으로 레시피 상세 표시
- **[담기]** 버튼: 해당 요리 재료를 장바구니에 추가

### 레시피 모달
[레시피] 버튼 클릭 시 표시되는 팝업

```
┌─────────────────────────────────────┐
│ 요리명                           ✕  │
├─────────────────────────────────────┤
│ 조리시간: 30분    난이도: 쉬움         │
│                                     │
│ ■ 재료                              │
│ • 재료1                             │
│ • 재료2                             │
│                                     │
│ ■ 조리 순서                          │
│ ① 첫 번째 단계                       │
│ ② 두 번째 단계                       │
│ ③ 세 번째 단계                       │
└─────────────────────────────────────┘
```

- ESC 키 또는 모달 바깥 클릭으로 닫기

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
| 채팅 메시지 전송 | POST | `/api/chat` | `{ message: string }` | `ChatResponse` |

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
| 결과 표시 | 레시피 카드 목록 (재료 + 할인정보) |
| 레시피 보기 | 카드별 [레시피] 버튼 → 모달 표시 |
| 장바구니 담기 | 카드별 [담기] 버튼 → 재료 담기 |

### 화면 결과 예시
```
추천 결과:
┌─────────────────────────────────────┐
│ 김치찌개                [레시피] [담기] │
│ 재료: 돼지고기, 김치, 두부, 대파        │
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
    cookTime: string;
    difficulty: string;
    ingredients: string[];
    steps: string[];
    discountInfo?: {
      item: string;
      rate: string;
    }[];
  }[];
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
| 결과 표시 | 레시피 카드 목록 |
| 레시피 보기 | 카드별 [레시피] 버튼 → 모달 표시 |
| 장바구니 담기 | 카드별 [담기] 버튼 → 재료 담기 |

### 화면 결과 예시
```
검색 결과:
┌─────────────────────────────────────┐
│ 김치찌개                [레시피] [담기] │
│ 재료: 돼지고기, 김치, 두부, 대파        │
├─────────────────────────────────────┤
│ 참치김치찌개            [레시피] [담기] │
│ 재료: 참치캔, 김치, 두부, 대파          │
└─────────────────────────────────────┘
```

### API 요구사항
| API | Method | Endpoint | Request | Response |
|-----|--------|----------|---------|----------|
| 레시피 검색 | GET | `/api/recipe/search` | `?keyword={keyword}` | `RecipeSearchResponse` |
| 인기 검색어 | GET | `/api/recipe/popular` | - | `string[]` |

#### Response 타입
```typescript
interface RecipeSearchResponse {
  recipes: {
    id: string;
    name: string;
    cookTime: string;
    difficulty: string;
    ingredients: string[];
    steps: string[];
  }[];
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
| 결과 표시 | 레시피 카드 목록 (할인정보 포함) |
| 레시피 보기 | 카드별 [레시피] 버튼 → 모달 표시 |
| 장바구니 담기 | 카드별 [담기] 버튼 → 재료 담기 |

### 화면 결과 예시
```
추천 결과:
┌─────────────────────────────────────┐
│ 삼겹살 김치찌개          [레시피] [담기] │
│ 재료: 삼겹살, 김치, 두부, 대파, 고춧가루  │
│ 🏷️ 삼겹살 30% 할인, 두부 1+1 할인     │
├─────────────────────────────────────┤
│ 제육볶음                [레시피] [담기] │
│ 재료: 삼겹살, 고추장, 양파, 대파, 마늘   │
│ 🏷️ 삼겹살 30% 할인, 고추장 20% 할인   │
└─────────────────────────────────────┘
```

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
}

interface DiscountRecommendResponse {
  recipes: {
    id: string;
    name: string;
    cookTime: string;
    difficulty: string;
    ingredients: string[];
    steps: string[];
    discountInfo: {
      item: string;
      rate: string;
    }[];
    relatedItems: string[];  // 선택한 할인상품과 매칭되는 재료
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
| 결과 표시 | 레시피 카드 목록 (부족한 재료 표시) |
| 레시피 보기 | 카드별 [레시피] 버튼 → 모달 표시 |
| 장바구니 담기 | 카드별 [담기] 버튼 → 재료 담기 |

### 화면 결과 예시
```
추천 결과:
┌─────────────────────────────────────┐
│ 김치찌개                [레시피] [담기] │
│ 재료: 삼겹살, 김치, 두부, 대파, 고춧가루  │
│ ⚠️ 부족한 재료: 고춧가루               │
│ 🏷️ 삼겹살 30% 할인                   │
├─────────────────────────────────────┤
│ 계란말이                [레시피] [담기] │
│ 재료: 계란, 대파, 당근, 소금           │
│ ✅ 모든 재료가 있어요!                 │
└─────────────────────────────────────┘
```

### API 요구사항
| API | Method | Endpoint | Request | Response |
|-----|--------|----------|---------|----------|
| 재료 기반 추천 | POST | `/api/fridge/recommend` | `{ ingredients: string[] }` | `FridgeRecommendResponse` |

#### Response 타입
```typescript
interface FridgeRecommendResponse {
  recipes: {
    id: string;
    name: string;
    cookTime: string;
    difficulty: string;
    ingredients: string[];
    steps: string[];
    requiredIngredients: string[];  // 필수 재료 (매칭에 사용)
    discountInfo?: {
      item: string;
      rate: string;
    }[];
  }[];
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

---

## 향후 확장 기능 (메모)

- 레시피 생성시 계량(스푼, 컵, ml 등등)을 사용자 지정 가능하게
- 간단버전 레시피, 풀버전 레시피를 사용자 지정 가능하게 (시간, 분 설정)
- 건강식을 가미한 레시피 (올리고당 등등...)
