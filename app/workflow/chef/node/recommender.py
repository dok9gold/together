"""RecommenderNode - 요리 추천"""
import json
import logging
from typing import Any

from core.database.context import get_connection
from core.database.transaction import transactional_readonly

from .base import BaseNode, load_prompt, render_prompt

logger = logging.getLogger(__name__)


class RecommenderNode(BaseNode):
    """사용자 조건에 맞는 요리 추천"""

    def __init__(self, llm):
        super().__init__(llm)
        self.templates = load_prompt("recommender", "recommend")

    async def execute(
        self,
        state: dict[str, Any],
        config: dict | None = None
    ) -> dict[str, Any]:
        """요리 추천 실행

        Args:
            state: State (entities 포함)
            config: 설정

        Returns:
            {"dishes": [{"name": "요리명", "discount_items": [...]}]}
        """
        entities = state.get("entities", {})

        # 할인 상품 조회 (use_discount=true일 때) - 프롬프트용
        discount_items = []
        if entities.get("use_discount"):
            discount_items = await self._fetch_discount_items()

        # 프롬프트 렌더링 (entities 통째로 전달)
        prompts = render_prompt(
            self.templates,
            entities=entities,
            discount_items=discount_items
        )

        logger.debug(f"[Recommender] entities: {entities}, discount_items: {len(discount_items)}")

        # LLM 호출
        response = await self.llm.generate(
            prompt=prompts["user"],
            system=prompts["system"],
            option={"temperature": 0.7, "max_tokens": 1024}
        )

        # dishes 파싱 (새 구조: [{name, discount_items}, ...])
        dishes = self._parse_response(response)

        logger.info(f"[Recommender] recommended dishes: {[d.get('name') for d in dishes]}")

        return {"dishes": dishes}

    async def _fetch_discount_items(self) -> list[dict]:
        """할인 상품 조회"""
        try:
            return await _fetch_discount_items_from_db()
        except Exception as e:
            logger.warning(f"[Recommender] 할인 상품 조회 실패: {e}")
            return []

    def _parse_response(self, response: str) -> list[dict]:
        """LLM 응답에서 dishes 파싱 (새 구조)"""
        try:
            text = response.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            data = json.loads(text)
            dishes = data.get("dishes", [])

            # 각 dish가 올바른 구조인지 확인
            result = []
            for dish in dishes:
                if isinstance(dish, str):
                    # 이전 형식 호환: 문자열이면 dict로 변환
                    result.append({"name": dish, "discount_items": []})
                elif isinstance(dish, dict):
                    result.append({
                        "name": dish.get("name", ""),
                        "discount_items": dish.get("discount_items", [])
                    })
            return result
        except (json.JSONDecodeError, IndexError) as e:
            logger.warning(f"[Recommender] JSON 파싱 실패: {e}, response: {response[:200]}")
            return []


@transactional_readonly
async def _fetch_discount_items_from_db() -> list[dict]:
    """DB에서 할인 상품 조회 (읽기 전용 트랜잭션)"""
    ctx = get_connection()
    rows = await ctx.fetch_all("""
        SELECT p.name, p.barcode, dp.discount_type, dp.discount_rate
        FROM discount_product dp
        JOIN product p ON dp.barcode = p.barcode
        WHERE dp.end_date >= CURRENT_DATE OR dp.end_date IS NULL
    """)

    return [
        {
            "name": row["name"],
            "barcode": row["barcode"],
            "discount_type": row["discount_type"],
            "discount_rate": row["discount_rate"]
        }
        for row in rows
    ]
