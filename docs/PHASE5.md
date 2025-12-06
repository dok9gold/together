# Phase 5: 프레임워크화 (Piri Framework)

> **목표**: `app/core/`를 독립 패키지로 추출하여 재사용 가능한 AI Agent 프레임워크 구축

## 개요

AI Assistant Framework를 **Piri Framework (피리 프레임워크)**로 범용화:
- 다양한 AI Agent 애플리케이션을 빠르게 구축
- Convention over Configuration 원칙 적용
- CLI 도구로 프로젝트 스캐폴딩 지원

**Piri (피리)**: 한국 전통 악기 피리처럼, 간결하고 조화로운 AI Agent 개발 경험 제공

---

## 1. Core 추출 및 범용화

### 1.1 현재 구조
```
app/
├── core/              # 프레임워크 컴포넌트
│   ├── config.py
│   ├── auth.py
│   ├── prompt_loader.py
│   ├── decorators.py
│   └── ...
└── cooking_assistant/ # 애플리케이션
```

### 1.2 목표 구조
```
piri/                      # 독립 프레임워크 패키지
├── __init__.py
├── core/
│   ├── base_port.py       # Port 추상 클래스
│   ├── base_adapter.py    # Adapter 추상 클래스
│   ├── base_node.py       # Node 추상 클래스
│   ├── config.py          # 설정 시스템
│   ├── auth.py            # 인증 시스템
│   ├── prompt_loader.py   # 프롬프트 관리
│   └── decorators.py      # DI 데코레이터
├── cli/
│   ├── create.py          # 프로젝트 생성
│   ├── generate.py        # 코드 생성
│   └── validate.py        # 검증 도구
└── templates/
    ├── chatbot/           # 템플릿: 일반 챗봇
    ├── cooking_assistant/ # 템플릿: 요리 어시스턴트
    └── rag_qa/            # 템플릿: RAG 기반 Q&A

# 사용자 프로젝트 구조
my-ai-app/
├── app/
│   ├── my_agent/          # 애플리케이션 코드만
│   └── main.py
├── config/
│   └── settings.yaml      # YAML 설정
└── requirements.txt       # piri-framework 의존성 포함
```

---

## 2. 추상 클래스 정의

### 2.1 BasePort

```python
# piri/core/base_port.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar('T')

class BasePort(ABC, Generic[T]):
    """Port 기본 추상 클래스"""

    @abstractmethod
    async def execute(self, *args, **kwargs) -> T:
        """포트 실행"""
        pass
```

### 2.2 BaseAdapter

```python
# piri/core/base_adapter.py
from abc import ABC
from typing import TypeVar

T = TypeVar('T')

class BaseAdapter(ABC):
    """Adapter 기본 추상 클래스"""

    def __init__(self, config: dict = None):
        self.config = config or {}

    async def _make_request(self, *args, **kwargs):
        """공통 요청 로직 (재사용 가능)"""
        pass

    async def _parse_response(self, response):
        """공통 응답 파싱 (재사용 가능)"""
        pass
```

### 2.3 BaseNode

```python
# piri/core/base_node.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseNode(ABC):
    """LangGraph Node 기본 추상 클래스"""

    def __init__(self, intent_name: str = None):
        self.intent_name = intent_name

    @abstractmethod
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """노드 실행"""
        pass

    def should_execute(self, state: Dict[str, Any]) -> bool:
        """실행 조건 (기본 구현)"""
        if not self.intent_name:
            return True
        return state.get("primary_intent") == self.intent_name
```

---

## 3. 설정 시스템 범용화

### 3.1 YAML 기반 설정

```yaml
# config/settings.yaml (사용자 프로젝트)
application:
  name: my-ai-app
  version: "1.0.0"
  template: chatbot  # 또는 cooking_assistant, rag_qa

server:
  host: 0.0.0.0
  port: 8000
  reload: true

llm:
  provider: anthropic  # anthropic | openai | gemini
  config:
    model: claude-sonnet-4-5-20250929
    temperature: 0.7
    max_tokens: 2000

vector_store:
  provider: chroma  # chroma | pinecone | weaviate
  enabled: true
  config:
    collection_name: documents
    persist_directory: ./data/chroma

memory:
  provider: postgres  # postgres | redis | in-memory
  enabled: true
  config:
    database_url: ${DATABASE_URL}

auth:
  enabled: true
  jwt_secret: ${JWT_SECRET_KEY}
  token_expire_minutes: 60

prompts:
  directory: ./prompts
  hot_reload: true
  localization:
    enabled: true
    default_locale: ko
```

### 3.2 설정 로더

```python
# piri/core/config_loader.py
import yaml
import os
from typing import Any, Dict

class ConfigLoader:
    """YAML 설정 로더"""

    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config_path = config_path
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """YAML 로드 및 환경 변수 치환"""
        with open(self.config_path) as f:
            config = yaml.safe_load(f)

        # 환경 변수 치환 (${VAR_NAME})
        return self._resolve_env_vars(config)

    def _resolve_env_vars(self, config: Any) -> Any:
        """재귀적으로 ${VAR} 치환"""
        if isinstance(config, dict):
            return {k: self._resolve_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._resolve_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            var_name = config[2:-1]
            return os.getenv(var_name, config)
        return config

    def get(self, path: str, default=None):
        """점(.) 구분 경로로 값 조회"""
        keys = path.split(".")
        value = self._config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        return value if value is not None else default
```

---

## 4. CLI 도구

### 4.1 설치 및 사용

```bash
# Piri Framework 설치
pip install piri-framework

# 프로젝트 생성
piri create my-chatbot --template=chatbot

# Adapter 생성
cd my-chatbot
piri generate adapter --type=llm --name=GeminiLLM

# Node 생성
piri generate node --name=SummaryNode

# 프롬프트 검증
piri validate-prompts

# 실행
piri run --reload
```

### 4.2 프로젝트 생성

```python
# piri/cli/create.py
import click
import shutil
from pathlib import Path

@click.command()
@click.argument('project_name')
@click.option('--template', default='chatbot', help='템플릿 선택')
def create(project_name: str, template: str):
    """새 Piri 프로젝트 생성"""
    template_path = Path(__file__).parent.parent / "templates" / template
    target_path = Path.cwd() / project_name

    if target_path.exists():
        click.echo(f"Error: {project_name} already exists")
        return

    # 템플릿 복사
    shutil.copytree(template_path, target_path)

    # 변수 치환 (프로젝트 이름 등)
    _replace_placeholders(target_path, project_name)

    click.echo(f"✅ Created project: {project_name}")
    click.echo(f"cd {project_name} && pip install -r requirements.txt")

def _replace_placeholders(path: Path, project_name: str):
    """템플릿의 {{PROJECT_NAME}} 치환"""
    for file in path.rglob("*.py"):
        content = file.read_text()
        content = content.replace("{{PROJECT_NAME}}", project_name)
        file.write_text(content)
```

### 4.3 Adapter 생성

```python
# piri/cli/generate.py
import click
from jinja2 import Template
from pathlib import Path

ADAPTER_TEMPLATE = '''
# app/core/adapters/{{ adapter_type }}/{{ adapter_name | lower }}_adapter.py
from piri.core.base_adapter import BaseAdapter
from app.core.ports.{{ adapter_type }}_port import I{{ adapter_type | capitalize }}Port

class {{ adapter_name }}Adapter(BaseAdapter, I{{ adapter_type | capitalize }}Port):
    """{{ adapter_name }} Adapter"""

    def __init__(self, config: dict):
        super().__init__(config)
        # TODO: 클라이언트 초기화

    async def execute(self, *args, **kwargs):
        """포트 실행"""
        # TODO: API 호출 로직
        pass
'''

@click.command()
@click.option('--type', 'adapter_type', required=True, help='llm | image | vector_store')
@click.option('--name', required=True, help='Adapter 이름 (예: GeminiLLM)')
def generate_adapter(adapter_type: str, name: str):
    """Adapter 코드 생성"""
    template = Template(ADAPTER_TEMPLATE)
    code = template.render(adapter_type=adapter_type, adapter_name=name)

    # 파일 저장
    output_path = Path(f"app/core/adapters/{adapter_type}/{name.lower()}_adapter.py")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(code)

    click.echo(f"✅ Generated: {output_path}")
```

### 4.4 프롬프트 검증

```python
# piri/cli/validate.py
import click
from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError

@click.command()
def validate_prompts():
    """프롬프트 YAML 파일 검증"""
    prompts_dir = Path("prompts")
    errors = []

    for yaml_file in prompts_dir.rglob("*.yaml"):
        try:
            # YAML 파싱
            with open(yaml_file) as f:
                prompts = yaml.safe_load(f)

            # Jinja2 템플릿 검증
            for prompt_id, prompt_data in prompts.items():
                if isinstance(prompt_data, dict):
                    for key in ["system", "user"]:
                        if key in prompt_data:
                            env = Environment()
                            env.parse(prompt_data[key])

        except yaml.YAMLError as e:
            errors.append(f"{yaml_file}: YAML 파싱 오류 - {e}")
        except TemplateSyntaxError as e:
            errors.append(f"{yaml_file}: Jinja2 문법 오류 - {e}")

    if errors:
        click.echo("❌ 검증 실패:")
        for error in errors:
            click.echo(f"  - {error}")
    else:
        click.echo("✅ 모든 프롬프트 검증 완료")
```

---

## 5. 템플릿 구조

### 5.1 Chatbot 템플릿

```
templates/chatbot/
├── app/
│   ├── chatbot/
│   │   ├── module.py
│   │   ├── entities/
│   │   ├── services/
│   │   ├── workflow/
│   │   ├── api/
│   │   └── prompts/
│   └── main.py
├── config/
│   └── settings.yaml
├── prompts/
│   └── chatbot.yaml
├── .env.example
└── requirements.txt
```

### 5.2 RAG Q&A 템플릿

```
templates/rag_qa/
├── app/
│   ├── rag_qa/
│   │   ├── module.py
│   │   ├── workflow/
│   │   │   └── nodes/
│   │   │       ├── retriever_node.py
│   │   │       └── answer_node.py
│   │   └── prompts/
│   └── main.py
├── config/
│   └── settings.yaml  # vector_store 활성화
└── requirements.txt
```

---

## 6. DI Container 범용화

### 6.1 자동 Provider 스캔

```python
# piri/core/auto_module.py
from piri.core.decorators import provider, singleton
import inspect

class AutoModule:
    """Provider 자동 스캔"""

    def __init__(self, config_loader: ConfigLoader):
        self.config = config_loader
        self._scan_providers()

    def _scan_providers(self):
        """설정 기반 Provider 자동 등록"""
        # LLM Provider
        llm_provider = self.config.get("llm.provider")
        if llm_provider == "anthropic":
            self._register_anthropic_llm()
        elif llm_provider == "openai":
            self._register_openai_llm()

        # Vector Store Provider
        if self.config.get("vector_store.enabled"):
            vs_provider = self.config.get("vector_store.provider")
            if vs_provider == "chroma":
                self._register_chroma_vector_store()

    @singleton
    @provider
    def _register_anthropic_llm(self) -> ILLMPort:
        """Anthropic LLM Adapter 등록"""
        from app.core.adapters.llm.anthropic_adapter import AnthropicLLMAdapter
        return AnthropicLLMAdapter(self.config.get("llm.config"))
```

---

## 7. 배포 및 패키징

### 7.1 PyPI 배포

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "piri-framework"
version = "1.0.0"
description = "FastAPI + LangGraph AI Agent Framework - 피리 프레임워크"
authors = [{name = "Your Name", email = "you@example.com"}]
dependencies = [
    "fastapi>=0.104.0",
    "langgraph>=0.0.20",
    "pydantic>=2.0.0",
    "jinja2>=3.1.0",
    "pyyaml>=6.0",
    "click>=8.0.0"
]

[project.scripts]
piri = "piri.cli:main"
```

### 7.2 설치

```bash
# 개발자 모드
pip install -e .

# PyPI 배포
python -m build
twine upload dist/*

# 사용자 설치
pip install piri-framework
```

---

## 8. 문서화

### 8.1 Quick Start 가이드

```markdown
# Piri Framework (피리 프레임워크) Quick Start

## 설치
```bash
pip install piri-framework
```

## 프로젝트 생성
```bash
piri create my-chatbot --template=chatbot
cd my-chatbot
pip install -r requirements.txt
```

## 설정
```yaml
# config/settings.yaml
llm:
  provider: anthropic
  config:
    model: claude-sonnet-4-5-20250929
```

## 실행
```bash
piri run --reload
```
```

### 8.2 API Reference

- [BasePort 사용법](docs/api/base_port.md)
- [BaseAdapter 사용법](docs/api/base_adapter.md)
- [PromptLoader 사용법](docs/api/prompt_loader.md)
- [CLI 커맨드](docs/cli/commands.md)

---

## 체크리스트

### Core 추출
- [ ] BasePort, BaseAdapter, BaseNode 추상 클래스 정의
- [ ] PromptLoader 독립 모듈화
- [ ] DI Container 범용화
- [ ] ConfigLoader 구현 (YAML + 환경 변수)

### CLI 도구
- [ ] `piri create` 명령어 구현
- [ ] `piri generate adapter` 구현
- [ ] `piri generate node` 구현
- [ ] `piri validate-prompts` 구현
- [ ] `piri run` 구현

### 템플릿
- [ ] chatbot 템플릿 작성
- [ ] rag_qa 템플릿 작성
- [ ] cooking_assistant 템플릿 정리

### 배포
- [ ] pyproject.toml 작성
- [ ] PyPI 배포 설정
- [ ] 문서화 (Quick Start, API Reference)
- [ ] 예제 프로젝트 작성

---

## 예상 효과

- **개발 속도 향상**: 템플릿 기반 5분 내 프로젝트 생성
- **코드 재사용성**: 공통 컴포넌트 중복 제거
- **학습 곡선 완화**: Convention over Configuration

---

## 참고 자료

- [FastAPI 프레임워크](https://fastapi.tiangolo.com/)
- [LangGraph 문서](https://langchain-ai.github.io/langgraph/)
- [Click CLI 프레임워크](https://click.palletsprojects.com/)
