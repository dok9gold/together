
  📋 작업 계획 개요

  핵심 원칙

  - ✅ 점진적 마이그레이션: 각 단계마다 기존 기능 유지
  - ✅ 안쪽에서 바깥쪽으로: Domain → Adapter → Application → Presentation
  - ✅ 의존성 방향 준수: 항상 안쪽(Domain)을 향하도록

  ---
  🔍 Phase 0: 현재 상태 분석

  현재 코드베이스 구조 파악 및 이해
  - app/services/cooking_assistant.py 분석
  - app/services/image_service.py 분석
  - 기존 API 라우트 및 모델 확인

  ---
  🏗️ Phase 1: 기본 인프라 설정

  목표: 설정 관리 중앙화 및 디렉토리 구조 생성

  1. 디렉토리 구조 생성
  app/
  ├── domain/
  │   ├── entities/
  │   ├── ports/
  │   └── services/
  ├── adapters/
  │   ├── llm/
  │   └── image/
  ├── application/
  │   ├── use_cases/
  │   └── workflow/
  └── core/
  2. Config 클래스 구현 (app/core/config.py)
    - Pydantic Settings로 환경 변수 중앙 관리
    - API 키, LLM 설정, 이미지 설정 통합

  ---
  🎯 Phase 2: Domain Layer 구축

  목표: 순수 비즈니스 로직 레이어 구현 (외부 의존성 없음)

  1. Entities - 비즈니스 객체
    - Recipe, CookingState, Recommendation 등
  2. Ports - 인터페이스 정의 (외부 시스템과의 경계만!)
    - ILLMPort: LLM API 호출 인터페이스
    - IImagePort: 이미지 생성 API 인터페이스
  3. Domain Services - 핵심 비즈니스 로직
    - CookingAssistantService: Port에만 의존하는 순수 로직

  ---
  🔌 Phase 3: Adapter Layer 구축

  목표: Port 인터페이스 구현 (외부 시스템 연동)

  1. AnthropicLLMAdapter
    - ILLMPort 구현
    - 기존 cooking_assistant.py의 LLM 호출 로직 이전
    - 프롬프트 생성 메서드 포함
  2. ReplicateImageAdapter
    - IImagePort 구현
    - 기존 image_service.py 로직 이전

  ---
  🎬 Phase 4: Application Layer 구축

  목표: 워크플로우 오케스트레이션 (LangGraph 통합)

  1. Workflow Nodes - Domain Service 호출하는 얇은 래퍼
    - IntentClassifierNode
    - RecipeGeneratorNode
    - ImageGeneratorNode
    - RecommenderNode
  2. Workflow Edges - 조건부 라우팅
    - route_by_intent
    - check_secondary_intents
  3. CookingWorkflow - StateGraph 구성
  4. Use Cases - 워크플로우 실행
    - CreateRecipeUseCase
    - RecommendDishesUseCase
    - AnswerQuestionUseCase

  ---
  💉 Phase 5: DI Container 구축

  목표: 의존성 자동 주입 (Spring 스타일)

  - dependency-injector 라이브러리 사용
  - Container에 모든 컴포넌트 등록
    - Config (Singleton)
    - Adapters (Singleton)
    - Domain Services (Singleton)
    - Workflow (Singleton)
    - Use Cases (Factory)

  ---
  🌐 Phase 6: Presentation Layer 수정

  목표: API 계층을 DI 기반으로 전환

  1. DTO 구현
    - CookingRequest, CookingResponse
  2. Dependencies 헬퍼
    - FastAPI Depends용 팩토리 함수
  3. Routes 수정
    - DI Container에서 Use Case 주입받도록 수정
  4. main.py 업데이트
    - Container 초기화

  ---
  ✅ Phase 7: 통합 테스트

  목표: 새 아키텍처 검증

  - API 엔드포인트 테스트
  - 레시피 생성, 추천, 질문 답변 시나리오 테스트
  - 기존 기능과 동일하게 작동하는지 확인

  ---
  🧹 Phase 8: 기존 코드 정리

  목표: 레거시 코드 제거

  - app/services/ 디렉토리 제거
  - app/models/schemas.py 제거 (DTO로 대체)
  - 미사용 임포트 정리

  ---
  📚 Phase 9: 문서 업데이트

  목표: 새 아키텍처 문서화

  - README.md 업데이트
  - CLAUDE.md 업데이트
  - 코드 주석 보완

  ---
  🚀 시작할 준비 되셨나요?

  Phase 0부터 시작하여 현재 코드베이스를 분석할까요? 아니면 바로 Phase 1부터 디렉토리 구조를 생성하고 Config를 구현할까요?

  원하시는 방향으로 진행하겠습니다!

> 0부터 진행해보자 

● 좋습니다! Phase 0을 시작하겠습니다. 현재 코드베이스를 분석해보겠습니다.

● Bash(ls -la app/)
  ⎿  total 13                                      
     drwxr-xr-x 1 dok9 197121    0 10월 30 15:21 .
     drwxr-xr-x 1 dok9 197121    0 11월  6 19:30 ..
     … +6 lines (ctrl+o to expand)

● Bash(find app -type f -name "*.py" | head -20)
  ⎿  app/api/routes.py            
     app/api/__init__.py
     app/main.py
     … +6 lines (ctrl+o to expand)

● Read(app\main.py)
  ⎿  Read 48 lines

● Read(app\models\schemas.py)
  ⎿  Read 42 lines

● Read(app\api\routes.py)
  ⎿  Read 128 lines

● Read(app\services\image_service.py)
  ⎿  Read 60 lines

● Read(app\services\cooking_assistant.py)
  ⎿  Read 671 lines

● 완벽합니다! 현재 코드베이스의 모든 주요 파일을 분석했습니다. Phase 0 분석 결과를 정리해드리겠습니다.

● 📊 Phase 0: 현재 코드베이스 분석 완료

  현재 코드베이스를 분석한 결과, tobe.md에서 지적한 문제점들이 실제로 존재함을 확인했습니다.

  ---
  📁 현재 디렉토리 구조

  app/
  ├── __init__.py
  ├── main.py                      # FastAPI 앱 진입점
  ├── api/
  │   └── routes.py                # API 라우트
  ├── models/
  │   └── schemas.py               # Pydantic 모델
  └── services/
      ├── cooking_assistant.py     # 핵심 로직 (671줄)
      └── image_service.py         # 이미지 생성 (60줄)

  ---
  🔴 문제점 1: 레이어 구분 모호 (의존성 방향 위반)

  현재 코드: app/services/cooking_assistant.py:50-56

  def __init__(self):
      self.llm = ChatAnthropic(
          model="claude-sonnet-4-5-20250929",
          api_key=os.getenv("ANTHROPIC_API_KEY"),  # ❌ 환경 변수 직접 읽기
          timeout=90
      )
      self.image_service = ImageService()  # ❌ 외부 API 서비스 직접 생성
      self.graph = self._build_graph()

  문제:
  - 비즈니스 로직(CookingAssistant)이 외부 시스템(Anthropic API, Replicate API)에 직접 의존
  - 의존성 방향: 도메인 → 인프라 (잘못됨! 역전 필요)
  - LLM 제공자 변경(Anthropic → OpenAI) 시 도메인 로직 수정 필요

  ---
  🔴 문제점 2: 강한 결합 (Tight Coupling)

  현재 코드: app/api/routes.py:7

  router = APIRouter()
  cooking_assistant = CookingAssistant()  # ❌ 모듈 레벨 하드코딩

  문제:
  - CookingAssistant가 모듈 로드 시점에 생성됨
  - 내부에서 ChatAnthropic, ImageService를 직접 생성 → 모킹 불가능
  - 단위 테스트 작성 불가 (실제 API 호출 불가피)
  - DI(Dependency Injection) 없음

  ---
  🔴 문제점 3: 설정 관리 분산

  현재 코드: 여러 파일에서 개별적으로 환경 변수 읽기

  app/services/cooking_assistant.py:54
  api_key=os.getenv("ANTHROPIC_API_KEY")

  app/services/image_service.py:10
  self.api_token = os.getenv("REPLICATE_API_TOKEN")

  문제:
  - 환경 변수 이름 변경 시 여러 파일 수정 필요
  - 검증 로직 분산
  - 기본값 관리 일관성 부족
  - 중앙 설정 관리 없음

  ---
  🔴 문제점 4: 책임 혼재 (SRP 위반)

  현재 코드: app/services/cooking_assistant.py:59-214

  _classify_intent 메서드 예시:
  def _classify_intent(self, state: CookingState) -> CookingState:
      # 1. 프롬프트 작성 (비즈니스 로직)
      prompt = f"""당신은 요리 AI 어시스턴트의 의도 분류 전문가입니다...
      
      # 2. Anthropic API 호출 (인프라 로직)
      response = self.llm.invoke([HumanMessage(content=prompt)])
      
      # 3. JSON 파싱 (기술 세부사항)
      result_json = response.content.strip()
      if result_json.startswith("```"):
          lines = result_json.split('\n')
          result_json = '\n'.join(lines[1:-1])
      result = json.loads(result_json)

  문제:
  - 비즈니스 로직 (프롬프트 작성) + 외부 통신 (LLM 호출) + 데이터 변환 (JSON 파싱)이 한 메서드에 섞임
  - 단일 책임 원칙(SRP) 위반
  - 테스트 시 외부 API 호출 불가피
  - 프롬프트 수정 시 코드 재배포 필요

  ---
  🔴 문제점 5: LangGraph 워크플로우와 비즈니스 로직 혼재

  현재 코드: app/services/cooking_assistant.py:566-633

  def _build_graph(self) -> StateGraph:
      workflow = StateGraph(CookingState)

      # 노드 추가 - 메서드가 노드 함수 역할
      workflow.add_node("classify_intent", self._classify_intent)
      workflow.add_node("generate_recipe", self._generate_recipe)
      workflow.add_node("recommend_dish", self._recommend_dish)
      # ...

  문제:
  - 비즈니스 로직 메서드(_classify_intent, _generate_recipe 등)가 LangGraph 노드 함수 역할
  - 워크플로우 오케스트레이션과 도메인 로직이 한 클래스에 존재
  - 레이어 혼재 (Application Layer ↔ Domain Layer)

  ---
  ✅ 잘 구현된 부분

  1. LangGraph 워크플로우 구조
    - 의도 분류 → 분기 → 레시피/추천/질문 답변
    - Secondary intents 지원 (복합 의도 처리)
    - 상태 기반 그래프 설계
  2. API 응답 구조
    - routes.py의 응답 구성이 체계적
    - 메타데이터 포함 (entities, confidence)
    - 에러 처리 적절
  3. 엔티티 기반 프롬프트
    - 구조화된 엔티티 추출 (dishes, ingredients, constraints 등)
    - Few-shot 예시 포함

  ---
  📈 헥사고날 아키텍처 적용 시 개선 효과

  | 문제점     | 현재                        | TO-BE (헥사고날)                         |
  |---------|---------------------------|--------------------------------------|
  | LLM 교체  | CookingAssistant 코드 수정 필요 | AnthropicAdapter → OpenAIAdapter 교체만 |
  | 테스트     | 실제 API 호출 필요 (느림, 비용)     | Port 모킹 → 빠른 단위 테스트                  |
  | 설정 관리   | 여러 파일에 분산                 | 중앙 Config 클래스                        |
  | 프롬프트 수정 | 코드 재배포 필요                 | Jinja2 템플릿 수정만 (선택사항)                |
  | 의존성 주입  | 하드코딩                      | DI Container 자동 주입                   |

  ---
  🎯 다음 단계: Phase 1

  Phase 0 분석이 완료되었습니다!

  Phase 1에서는:
  1. ✅ 새로운 디렉토리 구조 생성 (domain, adapters, application, core)
  2. ✅ 중앙 설정 관리 클래스 구현 (Pydantic Settings)

  진행하시겠습니까?

> 진행시켜 

● 좋습니다! Phase 1을 시작하겠습니다.

  🏗️ Phase 1: 기본 인프라 설정

  1단계: 디렉토리 구조 생성

● Bash(mkdir -p app/domain/entities app/domain/ports app/domain/services app/adapters/llm app/adapters/image app/application/use_cases app/application/workflow/nodes a…)
  ⎿  (No content)

● Write(app\domain\__init__.py)
  ⎿  Wrote 1 lines to app\domain\__init__.py                                   
     """Domain Layer - 비즈니스 로직의 핵심
     이 레이어는 외부 시스템에 의존하지 않는 순수한 비즈니스 로직을 포함합니다.
     """

● Write(app\domain\entities\__init__.py)
  ⎿  Wrote 1 lines to app\domain\entities\__init__.py
     """Domain Entities - 비즈니스 객체"""

● Write(app\domain\ports\__init__.py)
  ⎿  Wrote 1 lines to app\domain\ports\__init__.py  
     """Domain Ports - 외부 시스템과의 인터페이스"""

● Write(app\domain\services\__init__.py)
  ⎿  Wrote 1 lines to app\domain\services\__init__.py
     """Domain Services - 핵심 비즈니스 로직"""

● Write(app\adapters\__init__.py)
  ⎿  Wrote 1 lines to app\adapters\__init__.py                        
     """Adapter Layer - 외부 시스템 연동
     Port 인터페이스를 실제 외부 시스템(API, DB 등)에 맞게 구현합니다.
     """

● Write(app\adapters\llm\__init__.py)
  ⎿  Wrote 1 lines to app\adapters\llm\__init__.py           
     """LLM Adapters - LLM API 연동 (Anthropic, OpenAI 등)"""

● Write(app\adapters\image\__init__.py)
  ⎿  Wrote 1 lines to app\adapters\image\__init__.py                   
     """Image Adapters - 이미지 생성 API 연동 (Replicate, DALL-E 등)"""

● Write(app\application\__init__.py)
  ⎿  Wrote 1 lines to app\application\__init__.py                        
     """Application Layer - 유스케이스 및 워크플로우 오케스트레이션
     도메인 서비스를 조합하여 애플리케이션의 특정 작업 흐름을 실행합니다.
     """

● Write(app\application\use_cases\__init__.py)
  ⎿  Wrote 1 lines to app\application\use_cases\__init__.py
     """Use Cases - 애플리케이션 작업 흐름"""

● Write(app\application\workflow\__init__.py)
  ⎿  Wrote 1 lines to app\application\workflow\__init__.py
     """Workflow - LangGraph 워크플로우"""

● Write(app\application\workflow\nodes\__init__.py)
  ⎿  Wrote 1 lines to app\application\workflow\nodes\__init__.py              
     """Workflow Nodes - LangGraph 노드 (Domain Service 호출하는 얇은 래퍼)"""

● Write(app\application\workflow\edges\__init__.py)
  ⎿  Wrote 1 lines to app\application\workflow\edges\__init__.py
     """Workflow Edges - LangGraph 조건부 라우팅 로직"""

● Write(app\core\__init__.py)
  ⎿  Wrote 1 lines to app\core\__init__.py
     """Core - 설정 및 DI Container"""

● 2단계: Config 클래스 구현

● Write(app\core\config.py)
  ⎿  Wrote 1 lines to app\core\config.py             
     """중앙 설정 관리
     환경 변수를 Pydantic Settings로 중앙 관리합니다.
     """
     from pydantic_settings import BaseSettings
     from functools import lru_cache
     from typing import List
     class Settings(BaseSettings):

● Bash(find app -type d | sort)
  ⎿  app                           
     app/__pycache__
     app/adapters
     … +18 lines (ctrl+o to expand)

● ✅ Phase 1 완료!

  생성된 디렉토리 구조

  app/
  ├── domain/                  # ✨ Domain Layer (가장 안쪽)
  │   ├── entities/           # 비즈니스 객체
  │   ├── ports/              # 외부 시스템 인터페이스
  │   └── services/           # 핵심 비즈니스 로직
  │
  ├── adapters/               # ✨ Adapter Layer (외부 시스템)
  │   ├── llm/               # LLM API 연동
  │   └── image/             # 이미지 API 연동
  │
  ├── application/            # ✨ Application Layer (유스케이스)
  │   ├── use_cases/         # 작업 흐름
  │   └── workflow/          # LangGraph 워크플로우
  │       ├── nodes/         # 워크플로우 노드
  │       └── edges/         # 조건부 라우팅
  │
  ├── core/                   # ✨ Core (설정, DI)
  │   ├── __init__.py
  │   └── config.py          # 중앙 설정 관리
  │
  ├── api/                    # (기존) Presentation Layer
  ├── models/                 # (기존, 추후 제거 예정)
  └── services/               # (기존, 추후 제거 예정)

  생성된 파일

  1. app/core/config.py - 중앙 설정 관리 클래스
    - Pydantic Settings 사용
    - 환경 변수 검증 및 기본값 관리
    - 싱글톤 패턴 (@lru_cache)

  주요 설정 항목:
    - API 키: anthropic_api_key, replicate_api_token
    - LLM 설정: llm_model, llm_timeout, llm_temperature 등
    - 이미지 설정: image_model, image_retries, image_aspect_ratio 등
    - 앱 설정: app_title, app_version, cors_origins 등

  ---
  🎯 다음 단계: Phase 2 - Domain Layer 구축

  Phase 2에서 구현할 항목:
  1. Entities - 비즈니스 객체 (Recipe, CookingState 등)
  2. Ports - 인터페이스 정의 (ILLMPort, IImagePort)
  3. Domain Services - 핵심 비즈니스 로직 (CookingAssistantService)

  Phase 2를 계속 진행할까요?

> 진행시켜 

● 좋습니다! Phase 2를 시작하겠습니다.

  🎯 Phase 2: Domain Layer 구축

  1단계: Entities 구현

● Write(app\domain\entities\cooking_state.py)
  ⎿  Wrote 1 lines to app\domain\entities\cooking_state.py  
     """CookingState - LangGraph 워크플로우 상태
     LangGraph 워크플로우에서 사용하는 상태 타입입니다.
     """
     from typing import TypedDict, Optional, List, Dict, Any
     class CookingState(TypedDict):
         """요리 AI 어시스턴트 워크플로우 상태

● Write(app\domain\entities\recipe.py)
  ⎿  Wrote 1 lines to app\domain\entities\recipe.py
     """Recipe - 레시피 엔티티
     레시피를 표현하는 비즈니스 객체입니다.
     """
     from dataclasses import dataclass
     from typing import List
     @dataclass
     class Recipe:

● Write(app\domain\entities\recommendation.py)
  ⎿  Wrote 1 lines to app\domain\entities\recommendation.py
     """Recommendation - 음식 추천 엔티티
     음식 추천 결과를 표현하는 비즈니스 객체입니다.
     """
     from dataclasses import dataclass
     from typing import List
     @dataclass
     class DishRecommendation:

● Write(app\domain\entities\question.py)
  ⎿  Wrote 1 lines to app\domain\entities\question.py     
     """Question & Answer - 질문/답변 엔티티
     요리 관련 질문과 답변을 표현하는 비즈니스 객체입니다.
     """
     from dataclasses import dataclass
     from typing import List
     @dataclass
     class Answer:

● 2단계: Ports 인터페이스 정의

● Write(app\domain\ports\llm_port.py)
  ⎿  Wrote 1 lines to app\domain\ports\llm_port.py           
     """ILLMPort - LLM 포트 인터페이스
     도메인이 외부 LLM 서비스에게 요구하는 기능을 정의합니다.
     """
     from abc import ABC, abstractmethod
     from typing import Dict, Any
     class ILLMPort(ABC):
         """LLM 포트 (도메인이 외부 LLM에게 원하는 기능)

● Write(app\domain\ports\image_port.py)
  ⎿  Wrote 1 lines to app\domain\ports\image_port.py                 
     """IImagePort - 이미지 생성 포트 인터페이스
     도메인이 외부 이미지 생성 서비스에게 요구하는 기능을 정의합니다.
     """
     from abc import ABC, abstractmethod
     from typing import Optional
     class IImagePort(ABC):
         """이미지 생성 포트

● 3단계: Domain Services 구현

● Write(app\domain\services\cooking_assistant.py)
  ⎿  Wrote 1 lines to app\domain\services\cooking_assistant.py    
     """CookingAssistantService - 요리 AI 어시스턴트 도메인 서비스
     핵심 비즈니스 로직을 담당합니다.
     외부 시스템은 몰라도 되며, Port 인터페이스에만 의존합니다.
     """
     from app.domain.ports.llm_port import ILLMPort
     from app.domain.ports.image_port import IImagePort
     from app.domain.entities.cooking_state import CookingState
     import logging

● ✅ Phase 2 완료!

  생성된 파일

  Domain Layer:
  app/domain/
  ├── entities/
  │   ├── cooking_state.py      # LangGraph 워크플로우 상태
  │   ├── recipe.py              # 레시피 엔티티
  │   ├── recommendation.py      # 추천 엔티티
  │   └── question.py            # 질문/답변 엔티티
  │
  ├── ports/
  │   ├── llm_port.py            # ILLMPort 인터페이스
  │   └── image_port.py          # IImagePort 인터페이스
  │
  └── services/
      └── cooking_assistant.py   # CookingAssistantService (순수 비즈니스 로직)

  핵심 개선 사항:
  - ✅ 의존성 역전: Domain이 Port에만 의존 (Anthropic API 몰라도 됨)
  - ✅ 테스트 용이성: Port를 모킹하면 단위 테스트 가능
  - ✅ 확장성: LLM 교체 시 Adapter만 변경

  ---
  🎯 Phase 3 시작: Adapter Layer 구축

  이제 Port 인터페이스를 실제 외부 시스템(Anthropic, Replicate)에 맞게 구현하겠습니다.

  계속 진행하겠습니다...

> 진행시켜 

● 현재까지 Phase 0-2를 완료했습니다. 남은 Phase 3-9에 대한 상세 계획을 제시드리겠습니다.

  📊 현재까지 완료된 작업 (Phase 0-2)

  ✅ Phase 0: 현재 코드베이스 분석 완료
  ✅ Phase 1: 인프라 설정 완료
  - 디렉토리 구조 생성 (domain, adapters, application, core)
  - Config 클래스 구현

  ✅ Phase 2: Domain Layer 완료
  - Entities: CookingState, Recipe, Recommendation, Question
  - Ports: ILLMPort, IImagePort 인터페이스
  - Services: CookingAssistantService (순수 비즈니스 로직)

  ---
  📋 남은 작업 계획 (Phase 3-9)

∴ Thought for 18s (ctrl+o to show thinking)

✢ Brewing… (esc to interrupt · ctrl+t to show todos · 26s · ↓ 837 tokens)
  ⎿  Next: Phase 3: Adapter Layer - LLM Adapter 구현 (AnthropicLLMAdapter)

────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
>  
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  ⏸ plan mode on (alt+m to cycle)
╭─── Claude Code v2.0.35 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│                             │ Recent activity                                                                                                                                                            │
│      Welcome back 덕구!     │ No recent activity                                                                                                                                                         │
│                             │ ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│           ▐▛███▜▌           │ What's new                                                                                                                                                                 │
│          ▝▜█████▛▘          │ Improve fuzzy search results when searching commands                                                                                                                       │
│            ▘▘ ▝▝            │ Improved VS Code extension to respect `chat.fontSize` and `chat.fontFamily` settings throughout the entire UI, and apply font changes immediately without requiring reload │
│                             │ Added `CLAUDE_CODE_EXIT_AFTER_STOP_DELAY` environment variable to automatically exit SDK mode after a specified idle duration, useful for automated workflows and scripts  │
│   Sonnet 4.5 · Claude Pro   │ /release-notes for more                                                                                                                                                    │
│        D:\dok9\PyAi         │                                                                                                                                                                            │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

> @tobe.md를 참고해서 순차적으로 framework 작업을 진행할거야, 계획세워줘 
  ⎿  Read tobe.md (2000+ lines)

● tobe.md 문서를 확인했습니다. 헥사고날 아키텍처로 리팩토링하는 상세한 계획이네요. 순차적으로 진행할 수 있도록 단계별 작업 계획을 세워드리겠습니다.

● 헥사고날 아키텍처 리팩토링을 위한 9단계 작업 계획을 수립했습니다.

  📋 작업 계획 개요

  핵심 원칙

  - ✅ 점진적 마이그레이션: 각 단계마다 기존 기능 유지
  - ✅ 안쪽에서 바깥쪽으로: Domain → Adapter → Application → Presentation
  - ✅ 의존성 방향 준수: 항상 안쪽(Domain)을 향하도록

  ---
  🔍 Phase 0: 현재 상태 분석

  현재 코드베이스 구조 파악 및 이해
  - app/services/cooking_assistant.py 분석
  - app/services/image_service.py 분석
  - 기존 API 라우트 및 모델 확인

  ---
  🏗️ Phase 1: 기본 인프라 설정

  목표: 설정 관리 중앙화 및 디렉토리 구조 생성

  1. 디렉토리 구조 생성
  app/
  ├── domain/
  │   ├── entities/
  │   ├── ports/
  │   └── services/
  ├── adapters/
  │   ├── llm/
  │   └── image/
  ├── application/
  │   ├── use_cases/
  │   └── workflow/
  └── core/
  2. Config 클래스 구현 (app/core/config.py)
    - Pydantic Settings로 환경 변수 중앙 관리
    - API 키, LLM 설정, 이미지 설정 통합

  ---
  🎯 Phase 2: Domain Layer 구축

  목표: 순수 비즈니스 로직 레이어 구현 (외부 의존성 없음)

  1. Entities - 비즈니스 객체
    - Recipe, CookingState, Recommendation 등
  2. Ports - 인터페이스 정의 (외부 시스템과의 경계만!)
    - ILLMPort: LLM API 호출 인터페이스
    - IImagePort: 이미지 생성 API 인터페이스
  3. Domain Services - 핵심 비즈니스 로직
    - CookingAssistantService: Port에만 의존하는 순수 로직

  ---
  🔌 Phase 3: Adapter Layer 구축

  목표: Port 인터페이스 구현 (외부 시스템 연동)

  1. AnthropicLLMAdapter
    - ILLMPort 구현
    - 기존 cooking_assistant.py의 LLM 호출 로직 이전
    - 프롬프트 생성 메서드 포함
  2. ReplicateImageAdapter
    - IImagePort 구현
    - 기존 image_service.py 로직 이전

  ---
  🎬 Phase 4: Application Layer 구축

  목표: 워크플로우 오케스트레이션 (LangGraph 통합)

  1. Workflow Nodes - Domain Service 호출하는 얇은 래퍼
    - IntentClassifierNode
    - RecipeGeneratorNode
    - ImageGeneratorNode
    - RecommenderNode
  2. Workflow Edges - 조건부 라우팅
    - route_by_intent
    - check_secondary_intents
  3. CookingWorkflow - StateGraph 구성
  4. Use Cases - 워크플로우 실행
    - CreateRecipeUseCase
    - RecommendDishesUseCase
    - AnswerQuestionUseCase

  ---
  💉 Phase 5: DI Container 구축

  목표: 의존성 자동 주입 (Spring 스타일)

  - dependency-injector 라이브러리 사용
  - Container에 모든 컴포넌트 등록
    - Config (Singleton)
    - Adapters (Singleton)
    - Domain Services (Singleton)
    - Workflow (Singleton)
    - Use Cases (Factory)

  ---
  🌐 Phase 6: Presentation Layer 수정

  목표: API 계층을 DI 기반으로 전환

  1. DTO 구현
    - CookingRequest, CookingResponse
  2. Dependencies 헬퍼
    - FastAPI Depends용 팩토리 함수
  3. Routes 수정
    - DI Container에서 Use Case 주입받도록 수정
  4. main.py 업데이트
    - Container 초기화

  ---
  ✅ Phase 7: 통합 테스트

  목표: 새 아키텍처 검증

  - API 엔드포인트 테스트
  - 레시피 생성, 추천, 질문 답변 시나리오 테스트
  - 기존 기능과 동일하게 작동하는지 확인

  ---
  🧹 Phase 8: 기존 코드 정리

  목표: 레거시 코드 제거

  - app/services/ 디렉토리 제거
  - app/models/schemas.py 제거 (DTO로 대체)
  - 미사용 임포트 정리

  ---
  📚 Phase 9: 문서 업데이트

  목표: 새 아키텍처 문서화

  - README.md 업데이트
  - CLAUDE.md 업데이트
  - 코드 주석 보완

  ---
  🚀 시작할 준비 되셨나요?

  Phase 0부터 시작하여 현재 코드베이스를 분석할까요? 아니면 바로 Phase 1부터 디렉토리 구조를 생성하고 Config를 구현할까요?

  원하시는 방향으로 진행하겠습니다!

> 0부터 진행해보자 

● 좋습니다! Phase 0을 시작하겠습니다. 현재 코드베이스를 분석해보겠습니다.

● Bash(ls -la app/)
  ⎿  total 13                                      
     drwxr-xr-x 1 dok9 197121    0 10월 30 15:21 .
     drwxr-xr-x 1 dok9 197121    0 11월  6 19:30 ..
     … +6 lines (ctrl+o to expand)

● Bash(find app -type f -name "*.py" | head -20)
  ⎿  app/api/routes.py            
     app/api/__init__.py
     app/main.py
     … +6 lines (ctrl+o to expand)

● Read(app\main.py)
  ⎿  Read 48 lines

● Read(app\models\schemas.py)
  ⎿  Read 42 lines

● Read(app\api\routes.py)
  ⎿  Read 128 lines

● Read(app\services\image_service.py)
  ⎿  Read 60 lines

● Read(app\services\cooking_assistant.py)
  ⎿  Read 671 lines

● 완벽합니다! 현재 코드베이스의 모든 주요 파일을 분석했습니다. Phase 0 분석 결과를 정리해드리겠습니다.

● 📊 Phase 0: 현재 코드베이스 분석 완료

  현재 코드베이스를 분석한 결과, tobe.md에서 지적한 문제점들이 실제로 존재함을 확인했습니다.

  ---
  📁 현재 디렉토리 구조

  app/
  ├── __init__.py
  ├── main.py                      # FastAPI 앱 진입점
  ├── api/
  │   └── routes.py                # API 라우트
  ├── models/
  │   └── schemas.py               # Pydantic 모델
  └── services/
      ├── cooking_assistant.py     # 핵심 로직 (671줄)
      └── image_service.py         # 이미지 생성 (60줄)

  ---
  🔴 문제점 1: 레이어 구분 모호 (의존성 방향 위반)

  현재 코드: app/services/cooking_assistant.py:50-56

  def __init__(self):
      self.llm = ChatAnthropic(
          model="claude-sonnet-4-5-20250929",
          api_key=os.getenv("ANTHROPIC_API_KEY"),  # ❌ 환경 변수 직접 읽기
          timeout=90
      )
      self.image_service = ImageService()  # ❌ 외부 API 서비스 직접 생성
      self.graph = self._build_graph()

  문제:
  - 비즈니스 로직(CookingAssistant)이 외부 시스템(Anthropic API, Replicate API)에 직접 의존
  - 의존성 방향: 도메인 → 인프라 (잘못됨! 역전 필요)
  - LLM 제공자 변경(Anthropic → OpenAI) 시 도메인 로직 수정 필요

  ---
  🔴 문제점 2: 강한 결합 (Tight Coupling)

  현재 코드: app/api/routes.py:7

  router = APIRouter()
  cooking_assistant = CookingAssistant()  # ❌ 모듈 레벨 하드코딩

  문제:
  - CookingAssistant가 모듈 로드 시점에 생성됨
  - 내부에서 ChatAnthropic, ImageService를 직접 생성 → 모킹 불가능
  - 단위 테스트 작성 불가 (실제 API 호출 불가피)
  - DI(Dependency Injection) 없음

  ---
  🔴 문제점 3: 설정 관리 분산

  현재 코드: 여러 파일에서 개별적으로 환경 변수 읽기

  app/services/cooking_assistant.py:54
  api_key=os.getenv("ANTHROPIC_API_KEY")

  app/services/image_service.py:10
  self.api_token = os.getenv("REPLICATE_API_TOKEN")

  문제:
  - 환경 변수 이름 변경 시 여러 파일 수정 필요
  - 검증 로직 분산
  - 기본값 관리 일관성 부족
  - 중앙 설정 관리 없음

  ---
  🔴 문제점 4: 책임 혼재 (SRP 위반)

  현재 코드: app/services/cooking_assistant.py:59-214

  _classify_intent 메서드 예시:
  def _classify_intent(self, state: CookingState) -> CookingState:
      # 1. 프롬프트 작성 (비즈니스 로직)
      prompt = f"""당신은 요리 AI 어시스턴트의 의도 분류 전문가입니다...
      
      # 2. Anthropic API 호출 (인프라 로직)
      response = self.llm.invoke([HumanMessage(content=prompt)])
      
      # 3. JSON 파싱 (기술 세부사항)
      result_json = response.content.strip()
      if result_json.startswith("```"):
          lines = result_json.split('\n')
          result_json = '\n'.join(lines[1:-1])
      result = json.loads(result_json)

  문제:
  - 비즈니스 로직 (프롬프트 작성) + 외부 통신 (LLM 호출) + 데이터 변환 (JSON 파싱)이 한 메서드에 섞임
  - 단일 책임 원칙(SRP) 위반
  - 테스트 시 외부 API 호출 불가피
  - 프롬프트 수정 시 코드 재배포 필요

  ---
  🔴 문제점 5: LangGraph 워크플로우와 비즈니스 로직 혼재

  현재 코드: app/services/cooking_assistant.py:566-633

  def _build_graph(self) -> StateGraph:
      workflow = StateGraph(CookingState)

      # 노드 추가 - 메서드가 노드 함수 역할
      workflow.add_node("classify_intent", self._classify_intent)
      workflow.add_node("generate_recipe", self._generate_recipe)
      workflow.add_node("recommend_dish", self._recommend_dish)
      # ...

  문제:
  - 비즈니스 로직 메서드(_classify_intent, _generate_recipe 등)가 LangGraph 노드 함수 역할
  - 워크플로우 오케스트레이션과 도메인 로직이 한 클래스에 존재
  - 레이어 혼재 (Application Layer ↔ Domain Layer)

  ---
  ✅ 잘 구현된 부분

  1. LangGraph 워크플로우 구조
    - 의도 분류 → 분기 → 레시피/추천/질문 답변
    - Secondary intents 지원 (복합 의도 처리)
    - 상태 기반 그래프 설계
  2. API 응답 구조
    - routes.py의 응답 구성이 체계적
    - 메타데이터 포함 (entities, confidence)
    - 에러 처리 적절
  3. 엔티티 기반 프롬프트
    - 구조화된 엔티티 추출 (dishes, ingredients, constraints 등)
    - Few-shot 예시 포함

  ---
  📈 헥사고날 아키텍처 적용 시 개선 효과

  | 문제점     | 현재                        | TO-BE (헥사고날)                         |
  |---------|---------------------------|--------------------------------------|
  | LLM 교체  | CookingAssistant 코드 수정 필요 | AnthropicAdapter → OpenAIAdapter 교체만 |
  | 테스트     | 실제 API 호출 필요 (느림, 비용)     | Port 모킹 → 빠른 단위 테스트                  |
  | 설정 관리   | 여러 파일에 분산                 | 중앙 Config 클래스                        |
  | 프롬프트 수정 | 코드 재배포 필요                 | Jinja2 템플릿 수정만 (선택사항)                |
  | 의존성 주입  | 하드코딩                      | DI Container 자동 주입                   |

  ---
  🎯 다음 단계: Phase 1

  Phase 0 분석이 완료되었습니다!

  Phase 1에서는:
  1. ✅ 새로운 디렉토리 구조 생성 (domain, adapters, application, core)
  2. ✅ 중앙 설정 관리 클래스 구현 (Pydantic Settings)

  진행하시겠습니까?

> 진행시켜 

● 좋습니다! Phase 1을 시작하겠습니다.

  🏗️ Phase 1: 기본 인프라 설정

  1단계: 디렉토리 구조 생성

● Bash(mkdir -p app/domain/entities app/domain/ports app/domain/services app/adapters/llm app/adapters/image app/application/use_cases app/application/workflow/nodes a…)
  ⎿  (No content)

● Write(app\domain\__init__.py)
  ⎿  Wrote 1 lines to app\domain\__init__.py                                   
     """Domain Layer - 비즈니스 로직의 핵심
     이 레이어는 외부 시스템에 의존하지 않는 순수한 비즈니스 로직을 포함합니다.
     """

● Write(app\domain\entities\__init__.py)
  ⎿  Wrote 1 lines to app\domain\entities\__init__.py
     """Domain Entities - 비즈니스 객체"""

● Write(app\domain\ports\__init__.py)
  ⎿  Wrote 1 lines to app\domain\ports\__init__.py  
     """Domain Ports - 외부 시스템과의 인터페이스"""

● Write(app\domain\services\__init__.py)
  ⎿  Wrote 1 lines to app\domain\services\__init__.py
     """Domain Services - 핵심 비즈니스 로직"""

● Write(app\adapters\__init__.py)
  ⎿  Wrote 1 lines to app\adapters\__init__.py                        
     """Adapter Layer - 외부 시스템 연동
     Port 인터페이스를 실제 외부 시스템(API, DB 등)에 맞게 구현합니다.
     """

● Write(app\adapters\llm\__init__.py)
  ⎿  Wrote 1 lines to app\adapters\llm\__init__.py           
     """LLM Adapters - LLM API 연동 (Anthropic, OpenAI 등)"""

● Write(app\adapters\image\__init__.py)
  ⎿  Wrote 1 lines to app\adapters\image\__init__.py                   
     """Image Adapters - 이미지 생성 API 연동 (Replicate, DALL-E 등)"""

● Write(app\application\__init__.py)
  ⎿  Wrote 1 lines to app\application\__init__.py                        
     """Application Layer - 유스케이스 및 워크플로우 오케스트레이션
     도메인 서비스를 조합하여 애플리케이션의 특정 작업 흐름을 실행합니다.
     """

● Write(app\application\use_cases\__init__.py)
  ⎿  Wrote 1 lines to app\application\use_cases\__init__.py
     """Use Cases - 애플리케이션 작업 흐름"""

● Write(app\application\workflow\__init__.py)
  ⎿  Wrote 1 lines to app\application\workflow\__init__.py
     """Workflow - LangGraph 워크플로우"""

● Write(app\application\workflow\nodes\__init__.py)
  ⎿  Wrote 1 lines to app\application\workflow\nodes\__init__.py              
     """Workflow Nodes - LangGraph 노드 (Domain Service 호출하는 얇은 래퍼)"""

● Write(app\application\workflow\edges\__init__.py)
  ⎿  Wrote 1 lines to app\application\workflow\edges\__init__.py
     """Workflow Edges - LangGraph 조건부 라우팅 로직"""

● Write(app\core\__init__.py)
  ⎿  Wrote 1 lines to app\core\__init__.py
     """Core - 설정 및 DI Container"""

● 2단계: Config 클래스 구현

● Write(app\core\config.py)
  ⎿  Wrote 1 lines to app\core\config.py             
     """중앙 설정 관리
     환경 변수를 Pydantic Settings로 중앙 관리합니다.
     """
     from pydantic_settings import BaseSettings
     from functools import lru_cache
     from typing import List
     class Settings(BaseSettings):

● Bash(find app -type d | sort)
  ⎿  app                           
     app/__pycache__
     app/adapters
     … +18 lines (ctrl+o to expand)

● ✅ Phase 1 완료!

  생성된 디렉토리 구조

  app/
  ├── domain/                  # ✨ Domain Layer (가장 안쪽)
  │   ├── entities/           # 비즈니스 객체
  │   ├── ports/              # 외부 시스템 인터페이스
  │   └── services/           # 핵심 비즈니스 로직
  │
  ├── adapters/               # ✨ Adapter Layer (외부 시스템)
  │   ├── llm/               # LLM API 연동
  │   └── image/             # 이미지 API 연동
  │
  ├── application/            # ✨ Application Layer (유스케이스)
  │   ├── use_cases/         # 작업 흐름
  │   └── workflow/          # LangGraph 워크플로우
  │       ├── nodes/         # 워크플로우 노드
  │       └── edges/         # 조건부 라우팅
  │
  ├── core/                   # ✨ Core (설정, DI)
  │   ├── __init__.py
  │   └── config.py          # 중앙 설정 관리
  │
  ├── api/                    # (기존) Presentation Layer
  ├── models/                 # (기존, 추후 제거 예정)
  └── services/               # (기존, 추후 제거 예정)

  생성된 파일

  1. app/core/config.py - 중앙 설정 관리 클래스
    - Pydantic Settings 사용
    - 환경 변수 검증 및 기본값 관리
    - 싱글톤 패턴 (@lru_cache)

  주요 설정 항목:
    - API 키: anthropic_api_key, replicate_api_token
    - LLM 설정: llm_model, llm_timeout, llm_temperature 등
    - 이미지 설정: image_model, image_retries, image_aspect_ratio 등
    - 앱 설정: app_title, app_version, cors_origins 등

  ---
  🎯 다음 단계: Phase 2 - Domain Layer 구축

  Phase 2에서 구현할 항목:
  1. Entities - 비즈니스 객체 (Recipe, CookingState 등)
  2. Ports - 인터페이스 정의 (ILLMPort, IImagePort)
  3. Domain Services - 핵심 비즈니스 로직 (CookingAssistantService)

  Phase 2를 계속 진행할까요?

> 진행시켜 

● 좋습니다! Phase 2를 시작하겠습니다.

  🎯 Phase 2: Domain Layer 구축

  1단계: Entities 구현

● Write(app\domain\entities\cooking_state.py)
  ⎿  Wrote 1 lines to app\domain\entities\cooking_state.py  
     """CookingState - LangGraph 워크플로우 상태
     LangGraph 워크플로우에서 사용하는 상태 타입입니다.
     """
     from typing import TypedDict, Optional, List, Dict, Any
     class CookingState(TypedDict):
         """요리 AI 어시스턴트 워크플로우 상태

● Write(app\domain\entities\recipe.py)
  ⎿  Wrote 1 lines to app\domain\entities\recipe.py
     """Recipe - 레시피 엔티티
     레시피를 표현하는 비즈니스 객체입니다.
     """
     from dataclasses import dataclass
     from typing import List
     @dataclass
     class Recipe:

● Write(app\domain\entities\recommendation.py)
  ⎿  Wrote 1 lines to app\domain\entities\recommendation.py
     """Recommendation - 음식 추천 엔티티
     음식 추천 결과를 표현하는 비즈니스 객체입니다.
     """
     from dataclasses import dataclass
     from typing import List
     @dataclass
     class DishRecommendation:

● Write(app\domain\entities\question.py)
  ⎿  Wrote 1 lines to app\domain\entities\question.py     
     """Question & Answer - 질문/답변 엔티티
     요리 관련 질문과 답변을 표현하는 비즈니스 객체입니다.
     """
     from dataclasses import dataclass
     from typing import List
     @dataclass
     class Answer:

● 2단계: Ports 인터페이스 정의

● Write(app\domain\ports\llm_port.py)
  ⎿  Wrote 1 lines to app\domain\ports\llm_port.py           
     """ILLMPort - LLM 포트 인터페이스
     도메인이 외부 LLM 서비스에게 요구하는 기능을 정의합니다.
     """
     from abc import ABC, abstractmethod
     from typing import Dict, Any
     class ILLMPort(ABC):
         """LLM 포트 (도메인이 외부 LLM에게 원하는 기능)

● Write(app\domain\ports\image_port.py)
  ⎿  Wrote 1 lines to app\domain\ports\image_port.py                 
     """IImagePort - 이미지 생성 포트 인터페이스
     도메인이 외부 이미지 생성 서비스에게 요구하는 기능을 정의합니다.
     """
     from abc import ABC, abstractmethod
     from typing import Optional
     class IImagePort(ABC):
         """이미지 생성 포트

● 3단계: Domain Services 구현

● Write(app\domain\services\cooking_assistant.py)
  ⎿  Wrote 1 lines to app\domain\services\cooking_assistant.py    
     """CookingAssistantService - 요리 AI 어시스턴트 도메인 서비스
     핵심 비즈니스 로직을 담당합니다.
     외부 시스템은 몰라도 되며, Port 인터페이스에만 의존합니다.
     """
     from app.domain.ports.llm_port import ILLMPort
     from app.domain.ports.image_port import IImagePort
     from app.domain.entities.cooking_state import CookingState
     import logging

● ✅ Phase 2 완료!

  생성된 파일

  Domain Layer:
  app/domain/
  ├── entities/
  │   ├── cooking_state.py      # LangGraph 워크플로우 상태
  │   ├── recipe.py              # 레시피 엔티티
  │   ├── recommendation.py      # 추천 엔티티
  │   └── question.py            # 질문/답변 엔티티
  │
  ├── ports/
  │   ├── llm_port.py            # ILLMPort 인터페이스
  │   └── image_port.py          # IImagePort 인터페이스
  │
  └── services/
      └── cooking_assistant.py   # CookingAssistantService (순수 비즈니스 로직)

  핵심 개선 사항:
  - ✅ 의존성 역전: Domain이 Port에만 의존 (Anthropic API 몰라도 됨)
  - ✅ 테스트 용이성: Port를 모킹하면 단위 테스트 가능
  - ✅ 확장성: LLM 교체 시 Adapter만 변경

  ---
  🎯 Phase 3 시작: Adapter Layer 구축

  이제 Port 인터페이스를 실제 외부 시스템(Anthropic, Replicate)에 맞게 구현하겠습니다.

  계속 진행하겠습니다...

> 진행시켜 

● 현재까지 Phase 0-2를 완료했습니다. 남은 Phase 3-9에 대한 상세 계획을 제시드리겠습니다.

  📊 현재까지 완료된 작업 (Phase 0-2)

  ✅ Phase 0: 현재 코드베이스 분석 완료
  ✅ Phase 1: 인프라 설정 완료
  - 디렉토리 구조 생성 (domain, adapters, application, core)
  - Config 클래스 구현

  ✅ Phase 2: Domain Layer 완료
  - Entities: CookingState, Recipe, Recommendation, Question
  - Ports: ILLMPort, IImagePort 인터페이스
  - Services: CookingAssistantService (순수 비즈니스 로직)

  ---
  📋 남은 작업 계획 (Phase 3-9)

∴ Thought for 18s (ctrl+o to show thinking)

✢ Brewing… (esc to interrupt · ctrl+t to show todos)
  ⎿  Next: Phase 3: Adapter Layer - LLM Adapter 구현 (AnthropicLLMAdapter)

────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
>  
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  ⏸ plan mode on (alt+m to cycle)
╭─── Claude Code v2.0.35 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│                             │ Recent activity                                                                                                                                                            │
│      Welcome back 덕구!     │ No recent activity                                                                                                                                                         │
│                             │ ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│           ▐▛███▜▌           │ What's new                                                                                                                                                                 │
│          ▝▜█████▛▘          │ Improve fuzzy search results when searching commands                                                                                                                       │
│            ▘▘ ▝▝            │ Improved VS Code extension to respect `chat.fontSize` and `chat.fontFamily` settings throughout the entire UI, and apply font changes immediately without requiring reload │
│                             │ Added `CLAUDE_CODE_EXIT_AFTER_STOP_DELAY` environment variable to automatically exit SDK mode after a specified idle duration, useful for automated workflows and scripts  │
│   Sonnet 4.5 · Claude Pro   │ /release-notes for more                                                                                                                                                    │
│        D:\dok9\PyAi         │                                                                                                                                                                            │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

> @tobe.md를 참고해서 순차적으로 framework 작업을 진행할거야, 계획세워줘 
  ⎿  Read tobe.md (2000+ lines)

● tobe.md 문서를 확인했습니다. 헥사고날 아키텍처로 리팩토링하는 상세한 계획이네요. 순차적으로 진행할 수 있도록 단계별 작업 계획을 세워드리겠습니다.

● 헥사고날 아키텍처 리팩토링을 위한 9단계 작업 계획을 수립했습니다.

  📋 작업 계획 개요

  핵심 원칙

  - ✅ 점진적 마이그레이션: 각 단계마다 기존 기능 유지
  - ✅ 안쪽에서 바깥쪽으로: Domain → Adapter → Application → Presentation
  - ✅ 의존성 방향 준수: 항상 안쪽(Domain)을 향하도록

  ---
  🔍 Phase 0: 현재 상태 분석

  현재 코드베이스 구조 파악 및 이해
  - app/services/cooking_assistant.py 분석
  - app/services/image_service.py 분석
  - 기존 API 라우트 및 모델 확인

  ---
  🏗️ Phase 1: 기본 인프라 설정

  목표: 설정 관리 중앙화 및 디렉토리 구조 생성

  1. 디렉토리 구조 생성
  app/
  ├── domain/
  │   ├── entities/
  │   ├── ports/
  │   └── services/
  ├── adapters/
  │   ├── llm/
  │   └── image/
  ├── application/
  │   ├── use_cases/
  │   └── workflow/
  └── core/
  2. Config 클래스 구현 (app/core/config.py)
    - Pydantic Settings로 환경 변수 중앙 관리
    - API 키, LLM 설정, 이미지 설정 통합

  ---
  🎯 Phase 2: Domain Layer 구축

  목표: 순수 비즈니스 로직 레이어 구현 (외부 의존성 없음)

  1. Entities - 비즈니스 객체
    - Recipe, CookingState, Recommendation 등
  2. Ports - 인터페이스 정의 (외부 시스템과의 경계만!)
    - ILLMPort: LLM API 호출 인터페이스
    - IImagePort: 이미지 생성 API 인터페이스
  3. Domain Services - 핵심 비즈니스 로직
    - CookingAssistantService: Port에만 의존하는 순수 로직

  ---
  🔌 Phase 3: Adapter Layer 구축

  목표: Port 인터페이스 구현 (외부 시스템 연동)

  1. AnthropicLLMAdapter
    - ILLMPort 구현
    - 기존 cooking_assistant.py의 LLM 호출 로직 이전
    - 프롬프트 생성 메서드 포함
  2. ReplicateImageAdapter
    - IImagePort 구현
    - 기존 image_service.py 로직 이전

  ---
  🎬 Phase 4: Application Layer 구축

  목표: 워크플로우 오케스트레이션 (LangGraph 통합)

  1. Workflow Nodes - Domain Service 호출하는 얇은 래퍼
    - IntentClassifierNode
    - RecipeGeneratorNode
    - ImageGeneratorNode
    - RecommenderNode
  2. Workflow Edges - 조건부 라우팅
    - route_by_intent
    - check_secondary_intents
  3. CookingWorkflow - StateGraph 구성
  4. Use Cases - 워크플로우 실행
    - CreateRecipeUseCase
    - RecommendDishesUseCase
    - AnswerQuestionUseCase

  ---
  💉 Phase 5: DI Container 구축

  목표: 의존성 자동 주입 (Spring 스타일)

  - dependency-injector 라이브러리 사용
  - Container에 모든 컴포넌트 등록
    - Config (Singleton)
    - Adapters (Singleton)
    - Domain Services (Singleton)
    - Workflow (Singleton)
    - Use Cases (Factory)

  ---
  🌐 Phase 6: Presentation Layer 수정

  목표: API 계층을 DI 기반으로 전환

  1. DTO 구현
    - CookingRequest, CookingResponse
  2. Dependencies 헬퍼
    - FastAPI Depends용 팩토리 함수
  3. Routes 수정
    - DI Container에서 Use Case 주입받도록 수정
  4. main.py 업데이트
    - Container 초기화

  ---
  ✅ Phase 7: 통합 테스트

  목표: 새 아키텍처 검증

  - API 엔드포인트 테스트
  - 레시피 생성, 추천, 질문 답변 시나리오 테스트
  - 기존 기능과 동일하게 작동하는지 확인

  ---
  🧹 Phase 8: 기존 코드 정리

  목표: 레거시 코드 제거

  - app/services/ 디렉토리 제거
  - app/models/schemas.py 제거 (DTO로 대체)
  - 미사용 임포트 정리

  ---
  📚 Phase 9: 문서 업데이트

  목표: 새 아키텍처 문서화

  - README.md 업데이트
  - CLAUDE.md 업데이트
  - 코드 주석 보완

  ---