# Phase 3: RAG (Vector Store) 통합

> **목표**: 유사 레시피 검색 기능 추가로 컨텍스트 기반 레시피 생성 강화

## 개요

RAG (Retrieval-Augmented Generation)를 통해:
- 과거 생성된 레시피를 Vector DB에 저장
- 사용자 쿼리와 유사한 레시피를 검색하여 컨텍스트 제공
- LLM이 더 정확하고 일관성 있는 레시피 생성

---

## 1. 아키텍처 설계

### 1.1 Port 인터페이스

```python
# app/core/ports/vector_store_port.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class Document:
    """Vector Store 문서"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

class IVectorStorePort(ABC):
    """Vector Store Port 인터페이스"""

    @abstractmethod
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """유사도 검색"""
        pass

    @abstractmethod
    async def add_documents(self, documents: List[Document]) -> None:
        """문서 추가"""
        pass

    @abstractmethod
    async def delete_by_metadata(self, filter: Dict[str, Any]) -> int:
        """메타데이터 기반 삭제"""
        pass

    @abstractmethod
    async def get_by_id(self, doc_id: str) -> Optional[Document]:
        """ID로 문서 조회"""
        pass
```

### 1.2 Adapter 구현 (ChromaDB)

```python
# app/core/adapters/vector_store/chroma_adapter.py
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from app.core.ports.vector_store_port import IVectorStorePort, Document

class ChromaVectorStoreAdapter(IVectorStorePort):
    """ChromaDB Vector Store Adapter"""

    def __init__(self, collection_name: str = "recipes"):
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="./data/chroma"
        ))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        # Embedding 모델 (한국어 지원)
        self.encoder = SentenceTransformer('jhgan/ko-sroberta-multitask')

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """유사도 검색"""
        # 쿼리 임베딩
        query_embedding = self.encoder.encode(query).tolist()

        # ChromaDB 검색
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter
        )

        # Document 객체로 변환
        documents = []
        for i in range(len(results['ids'][0])):
            doc = Document(
                id=results['ids'][0][i],
                content=results['documents'][0][i],
                metadata=results['metadatas'][0][i],
                embedding=results['embeddings'][0][i] if results.get('embeddings') else None
            )
            documents.append(doc)

        return documents

    async def add_documents(self, documents: List[Document]) -> None:
        """문서 추가"""
        # 임베딩 생성
        contents = [doc.content for doc in documents]
        embeddings = self.encoder.encode(contents).tolist()

        # ChromaDB에 저장
        self.collection.add(
            ids=[doc.id for doc in documents],
            documents=contents,
            embeddings=embeddings,
            metadatas=[doc.metadata for doc in documents]
        )

    async def delete_by_metadata(self, filter: Dict[str, Any]) -> int:
        """메타데이터 기반 삭제"""
        results = self.collection.get(where=filter)
        count = len(results['ids'])
        if count > 0:
            self.collection.delete(ids=results['ids'])
        return count

    async def get_by_id(self, doc_id: str) -> Optional[Document]:
        """ID로 문서 조회"""
        result = self.collection.get(ids=[doc_id])
        if not result['ids']:
            return None

        return Document(
            id=result['ids'][0],
            content=result['documents'][0],
            metadata=result['metadatas'][0]
        )
```

---

## 2. Workflow 통합

### 2.1 RAG Recipe Generator Node

```python
# app/cooking_assistant/workflow/nodes/rag_recipe_generator_node.py
from app.cooking_assistant.workflow.nodes.base_node import BaseNode
from app.core.ports.llm_port import ILLMPort
from app.core.ports.vector_store_port import IVectorStorePort, Document
from app.core.prompt_loader import PromptLoader

class RAGRecipeGeneratorNode(BaseNode):
    """RAG 기반 레시피 생성 노드"""

    def __init__(
        self,
        llm_port: ILLMPort,
        vector_store_port: IVectorStorePort,
        prompt_loader: PromptLoader
    ):
        super().__init__("recipe_create")
        self.llm_port = llm_port
        self.vector_store_port = vector_store_port
        self.prompt_loader = prompt_loader

    async def execute(self, state):
        """RAG 기반 레시피 생성"""
        user_query = state["user_query"]

        # 1. 유사 레시피 검색
        similar_recipes = await self._search_similar_recipes(user_query)

        # 2. 컨텍스트 구성
        context = self._build_context(similar_recipes)

        # 3. RAG 프롬프트 렌더링
        prompt = self.prompt_loader.render(
            "cooking.generate_recipe_with_rag",
            query=user_query,
            context=context
        )

        # 4. LLM 호출
        recipe_data = await self.llm_port.generate_recipe(prompt)

        # 5. 생성된 레시피 Vector DB에 저장
        await self._save_recipe_to_vector_store(recipe_data)

        return {"recipe": recipe_data}

    async def _search_similar_recipes(self, query: str) -> List[Document]:
        """유사 레시피 검색"""
        try:
            documents = await self.vector_store_port.search(
                query=query,
                top_k=3,
                filter={"type": "recipe"}  # 레시피만 필터링
            )
            return documents
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
            return []  # 검색 실패 시 빈 컨텍스트로 진행

    def _build_context(self, documents: List[Document]) -> str:
        """검색된 문서를 컨텍스트로 변환"""
        if not documents:
            return "참고할 유사 레시피가 없습니다."

        context_parts = []
        for i, doc in enumerate(documents, 1):
            metadata = doc.metadata
            context_parts.append(f"""
[참고 레시피 {i}]
제목: {metadata.get('title', 'N/A')}
재료: {', '.join(metadata.get('ingredients', []))}
조리법: {metadata.get('summary', 'N/A')}
""")
        return "\n".join(context_parts)

    async def _save_recipe_to_vector_store(self, recipe_data: dict):
        """생성된 레시피를 Vector Store에 저장"""
        try:
            # 레시피 텍스트 생성 (임베딩용)
            content = f"{recipe_data['title']} {' '.join(recipe_data['ingredients'])}"

            document = Document(
                id=f"recipe_{recipe_data.get('id', uuid.uuid4())}",
                content=content,
                metadata={
                    "type": "recipe",
                    "title": recipe_data["title"],
                    "ingredients": recipe_data["ingredients"],
                    "summary": recipe_data["steps"][:200],  # 요약만 저장
                    "created_at": datetime.now().isoformat()
                }
            )

            await self.vector_store_port.add_documents([document])
            logger.info("Recipe saved to vector store", recipe_id=document.id)
        except Exception as e:
            logger.error(f"Failed to save recipe to vector store: {e}")
            # 저장 실패해도 레시피 생성은 성공으로 처리
```

### 2.2 프롬프트 추가

```yaml
# app/cooking_assistant/prompts/cooking.yaml
generate_recipe_with_rag:
  system: |
    당신은 한국 요리 전문가입니다.
    사용자의 요청에 맞는 레시피를 생성하되, 아래 참고 레시피를 활용하세요.

  user: |
    ## 사용자 요청
    {{ query }}

    ## 참고 레시피
    {{ context }}

    ## 출력 형식
    위 참고 레시피를 고려하여 사용자 요청에 맞는 레시피를 JSON으로 생성하세요:
    {
      "title": "레시피 제목",
      "ingredients": ["재료1", "재료2", ...],
      "steps": ["1. ...", "2. ...", ...]
    }
```

---

## 3. 의존성 주입 설정

```python
# app/cooking_assistant/module.py
from app.core.adapters.vector_store.chroma_adapter import ChromaVectorStoreAdapter
from app.core.ports.vector_store_port import IVectorStorePort

class CookingModule(Module):
    @singleton
    @provider
    def provide_vector_store_adapter(self) -> IVectorStorePort:
        """Vector Store Adapter 제공"""
        return ChromaVectorStoreAdapter(collection_name="recipes")

    @singleton
    @provider
    def provide_rag_recipe_generator_node(
        self,
        llm_port: ILLMPort,
        vector_store_port: IVectorStorePort,
        prompt_loader: PromptLoader
    ) -> RAGRecipeGeneratorNode:
        """RAG Recipe Generator Node 제공"""
        return RAGRecipeGeneratorNode(llm_port, vector_store_port, prompt_loader)
```

---

## 4. 설치 및 설정

### 4.1 의존성 추가

```bash
# requirements.txt에 추가
chromadb==0.4.22
sentence-transformers==2.3.1
```

```bash
pip install chromadb sentence-transformers
```

### 4.2 데이터 디렉토리 생성

```bash
mkdir -p data/chroma
```

### 4.3 .gitignore 업데이트

```
# .gitignore
data/chroma/
```

---

## 5. 테스트

### 5.1 Vector Store 단위 테스트

```python
# tests/adapters/test_chroma_adapter.py
import pytest
from app.core.adapters.vector_store.chroma_adapter import ChromaVectorStoreAdapter
from app.core.ports.vector_store_port import Document

@pytest.mark.asyncio
async def test_add_and_search_documents():
    """문서 추가 및 검색 테스트"""
    adapter = ChromaVectorStoreAdapter(collection_name="test_recipes")

    # 문서 추가
    documents = [
        Document(
            id="recipe_1",
            content="김치찌개 돼지고기 김치 두부",
            metadata={"title": "김치찌개", "type": "recipe"}
        ),
        Document(
            id="recipe_2",
            content="된장찌개 두부 애호박 감자",
            metadata={"title": "된장찌개", "type": "recipe"}
        )
    ]
    await adapter.add_documents(documents)

    # 검색
    results = await adapter.search("김치를 이용한 요리", top_k=1)

    assert len(results) == 1
    assert results[0].metadata["title"] == "김치찌개"
```

### 5.2 RAG Node 통합 테스트

```python
# tests/workflows/test_rag_node.py
@pytest.mark.asyncio
async def test_rag_recipe_generation(mock_llm_adapter, mock_vector_store_adapter):
    """RAG 레시피 생성 통합 테스트"""
    node = RAGRecipeGeneratorNode(
        llm_port=mock_llm_adapter,
        vector_store_port=mock_vector_store_adapter,
        prompt_loader=PromptLoader()
    )

    state = {"user_query": "매운 김치찌개"}
    result = await node.execute(state)

    assert result["recipe"] is not None
    assert mock_vector_store_adapter.search_called
    assert mock_vector_store_adapter.add_documents_called
```

---

## 6. 성능 최적화

### 6.1 배치 처리

```python
# 레시피 대량 저장
async def batch_save_recipes(recipes: List[dict], vector_store: IVectorStorePort):
    """레시피 배치 저장"""
    documents = [
        Document(
            id=f"recipe_{recipe['id']}",
            content=f"{recipe['title']} {' '.join(recipe['ingredients'])}",
            metadata={...}
        )
        for recipe in recipes
    ]

    # 한 번에 저장 (100개씩 분할)
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        await vector_store.add_documents(batch)
```

### 6.2 캐싱

```python
# Redis 캐싱 (향후 Phase 4에서 통합)
from functools import lru_cache

@lru_cache(maxsize=100)
def get_similar_recipes_cached(query: str) -> List[Document]:
    """검색 결과 캐싱"""
    return await vector_store.search(query)
```

---

## 7. 모니터링

### 7.1 메트릭 수집

```python
# Vector Store 성능 추적
logger.info(
    "vector_search_completed",
    query=query,
    results_count=len(results),
    search_time_ms=elapsed_ms
)
```

### 7.2 품질 평가

```python
# 검색 품질 평가 (수동)
# - 사용자 쿼리 vs 검색된 레시피 관련성
# - 생성된 레시피 vs 검색된 컨텍스트 활용도
```

---

## 체크리스트

### 구현
- [ ] IVectorStorePort 인터페이스 정의
- [ ] ChromaVectorStoreAdapter 구현
- [ ] RAGRecipeGeneratorNode 구현
- [ ] 프롬프트 추가 (generate_recipe_with_rag)
- [ ] Module.py에 DI 설정 추가
- [ ] 의존성 설치 (chromadb, sentence-transformers)

### 테스트
- [ ] Vector Store 단위 테스트
- [ ] RAG Node 통합 테스트
- [ ] 검색 품질 평가

### 문서화
- [ ] README.md에 RAG 사용 예시 추가
- [ ] API 문서에 RAG 동작 설명 추가

---

## 예상 효과

- **컨텍스트 활용**: 과거 레시피 참고로 더 정확한 생성
- **일관성 향상**: 유사 요청에 대해 일관된 스타일 유지
- **재사용성**: 생성된 레시피 자동 축적 및 재활용

---

## 다음 단계

Phase 3 완료 후 → [Phase 4: Conversation Memory 통합](PHASE4.md)
