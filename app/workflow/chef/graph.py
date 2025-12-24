"""ChefWorkflow - 메인 LangGraph"""
import json
import logging
from typing import Any

from langgraph.graph import StateGraph, END

from core.database.context import get_connection
from core.database.transaction import transactional, transactional_readonly
from core.llm import LLMProvider

from .state import State
from .node import (
    RequestAnalyzerNode,
    RecommenderNode,
    RecipeGeneratorNode,
    QANode,
    ResponseGeneratorNode,
)

logger = logging.getLogger(__name__)

FEATURE = "chef"


# ============================================
# DB 함수
# ============================================

@transactional
async def create_session() -> int:
    """새 세션 생성"""
    ctx = get_connection()
    row = await ctx.fetch_one("SELECT nextval('chef_session_id_seq') as id")
    return row["id"]


@transactional_readonly
async def get_chat_history(session_id: int, limit: int = 10) -> list[dict]:
    """이전 대화 기록 조회

    Args:
        session_id: 세션 ID
        limit: 최대 조회 개수

    Returns:
        [{"role": "user", "content": "..."}, {"role": "ai", "content": "..."}]
    """
    ctx = get_connection()
    rows = await ctx.fetch_all(
        """
        SELECT role, content
        FROM message
        WHERE feature = $1 AND session_id = $2
        ORDER BY message_id DESC, role DESC
        LIMIT $3
        """,
        FEATURE,
        session_id,
        limit * 2  # user + ai 쌍
    )

    # 역순으로 정렬 (오래된 것부터)
    messages = [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]
    return messages


@transactional_readonly
async def get_last_state(session_id: int) -> State | None:
    """마지막 State 조회"""
    ctx = get_connection()
    row = await ctx.fetch_one(
        """
        SELECT state
        FROM state
        WHERE feature = $1 AND session_id = $2
        ORDER BY message_id DESC
        LIMIT 1
        """,
        FEATURE,
        session_id
    )
    return row["state"] if row else None


@transactional
async def save_state(session_id: int, message_id: int, state: State) -> None:
    """State 저장"""
    ctx = get_connection()
    await ctx.execute(
        """
        INSERT INTO state (feature, session_id, message_id, state)
        VALUES ($1, $2, $3, $4)
        """,
        FEATURE,
        session_id,
        message_id,
        json.dumps(state, ensure_ascii=False)
    )


@transactional
async def save_message(session_id: int, message_id: int, role: str, content: str) -> None:
    """메시지 저장"""
    ctx = get_connection()
    await ctx.execute(
        """
        INSERT INTO message (feature, session_id, message_id, role, content)
        VALUES ($1, $2, $3, $4, $5)
        """,
        FEATURE,
        session_id,
        message_id,
        role,
        content
    )


@transactional_readonly
async def get_next_message_id(session_id: int) -> int:
    """다음 message_id 조회"""
    ctx = get_connection()
    row = await ctx.fetch_one(
        """
        SELECT COALESCE(MAX(message_id), 0) + 1 as next_id
        FROM message
        WHERE feature = $1 AND session_id = $2
        """,
        FEATURE,
        session_id
    )
    return row["next_id"]


def create_router(state: State) -> list[str]:
    """intents에 따라 다음 실행할 노드 결정

    Args:
        state: 현재 State (intents 포함)

    Returns:
        다음 실행할 노드 이름 리스트
    """
    intents = state.get("intents", [])

    if not intents:
        # 요리와 무관한 질문 → 바로 응답 생성
        return ["response_generator"]

    next_nodes = []
    for intent in intents:
        if intent == "recommend":
            next_nodes.append("recommender")
        elif intent == "recipe":
            next_nodes.append("recipe_generator")
        elif intent == "qa":
            next_nodes.append("qa")

    # 마지막에 response_generator
    next_nodes.append("response_generator")

    return next_nodes


class ChefWorkflow:
    """요리 도우미 AI 워크플로우

    LangGraph 기반 동적 라우팅 워크플로우
    """

    def __init__(self, llm: LLMProvider):
        self.llm = llm
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """그래프 구성"""
        # 노드 인스턴스 생성
        request_analyzer = RequestAnalyzerNode(self.llm)
        recommender = RecommenderNode(self.llm)
        recipe_generator = RecipeGeneratorNode(self.llm)
        qa = QANode(self.llm)
        response_generator = ResponseGeneratorNode(self.llm)

        # StateGraph 생성
        graph = StateGraph(State)

        # 노드 등록
        graph.add_node("request_analyzer", request_analyzer.execute)
        graph.add_node("recommender", recommender.execute)
        graph.add_node("recipe_generator", recipe_generator.execute)
        graph.add_node("qa", qa.execute)
        graph.add_node("response_generator", response_generator.execute)

        # 시작점 설정
        graph.set_entry_point("request_analyzer")

        # 조건부 엣지: request_analyzer → 동적 라우팅
        graph.add_conditional_edges(
            "request_analyzer",
            self._route_after_analyzer,
            {
                "recommender": "recommender",
                "recipe_generator": "recipe_generator",
                "qa": "qa",
                "response_generator": "response_generator",
            }
        )

        # 각 노드에서 다음 노드로 이동
        graph.add_conditional_edges(
            "recommender",
            self._route_after_recommender,
            {
                "recipe_generator": "recipe_generator",
                "response_generator": "response_generator",
            }
        )

        graph.add_edge("recipe_generator", "response_generator")
        graph.add_edge("qa", "response_generator")
        graph.add_edge("response_generator", END)

        return graph.compile()

    def _route_after_analyzer(self, state: State) -> str:
        """request_analyzer 후 다음 노드 결정"""
        intents = state.get("intents", [])

        if not intents:
            return "response_generator"

        first_intent = intents[0]
        if first_intent == "recommend":
            return "recommender"
        elif first_intent == "recipe":
            return "recipe_generator"
        elif first_intent == "qa":
            return "qa"

        return "response_generator"

    def _route_after_recommender(self, state: State) -> str:
        """recommender 후 다음 노드 결정"""
        intents = state.get("intents", [])
        if "recipe" in intents:
            return "recipe_generator"
        return "response_generator"

    async def run(
        self,
        user_input: str,
        session_id: int | None = None,
        save_history: bool = True
    ) -> tuple[State, int, int]:
        """워크플로우 실행

        Args:
            user_input: 사용자 입력
            session_id: 세션 ID (None이면 새 세션 생성)
            save_history: State/Message 저장 여부

        Returns:
            (최종 State, session_id, message_id)
        """
        # 세션 생성 또는 기존 세션 사용
        if session_id is None:
            session_id = await create_session()
            chat_history = []
            logger.info(f"[ChefWorkflow] New session created: {session_id}")
        else:
            chat_history = await get_chat_history(session_id)
            logger.info(f"[ChefWorkflow] Existing session: {session_id}, history: {len(chat_history)} messages")

        # message_id 조회
        message_id = await get_next_message_id(session_id)

        initial_state: State = {
            "user_input": user_input,
            "intents": [],
            "entities": {},
            "dishes": [],
            "recipes": [],
            "qa_answer": None,
            "response": None,
        }

        config = {"configurable": {"chat_history": chat_history}}

        logger.info(f"[ChefWorkflow] Starting with input: {user_input[:50]}...")

        result = await self.graph.ainvoke(initial_state, config)

        logger.info(f"[ChefWorkflow] Completed. Response length: {len(result.get('response', ''))}")

        # State/Message 저장
        if save_history:
            await save_message(session_id, message_id, "user", user_input)
            await save_message(session_id, message_id, "ai", result.get("response", ""))
            await save_state(session_id, message_id, result)
            logger.debug(f"[ChefWorkflow] Saved to DB: session={session_id}, message={message_id}")

        return result, session_id, message_id
