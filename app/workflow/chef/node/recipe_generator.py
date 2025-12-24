"""RecipeGeneratorNode - 레시피 생성"""
import json
import logging
import re
from typing import Any

from core.database.context import get_connection
from core.database.transaction import transactional, transactional_readonly

from .base import BaseNode, load_prompt, render_prompt

logger = logging.getLogger(__name__)


def normalize_dish_name(name: str) -> str:
    """요리명 정규화 (공백 제거, 영어 소문자)"""
    normalized = re.sub(r'\s+', '', name)  # 공백 제거
    normalized = normalized.lower()  # 소문자 변환
    return normalized


class RecipeGeneratorNode(BaseNode):
    """레시피 생성 (DB 캐싱 포함)"""

    def __init__(self, llm):
        super().__init__(llm)
        self.templates = load_prompt("recipe_generator", "generate")

    async def execute(
        self,
        state: dict[str, Any],
        config: dict | None = None
    ) -> dict[str, Any]:
        """레시피 생성 실행

        Args:
            state: State (dishes, entities 포함)
            config: 설정

        Returns:
            {"recipes": list[dict]}
        """
        dishes = state.get("dishes", [])  # [{"name": "...", "discount_items": [...]}]
        entities = state.get("entities", {})

        if not dishes:
            logger.warning("[RecipeGenerator] No dish to generate recipe for")
            return {"recipes": []}

        # 전체 dishes 순회
        recipes = []
        for dish in dishes:
            dish_name = dish.get("name", "") if isinstance(dish, dict) else dish
            discount_items = dish.get("discount_items", []) if isinstance(dish, dict) else []

            normalized_name = normalize_dish_name(dish_name)
            logger.debug(f"[RecipeGenerator] dish: {dish_name}, normalized: {normalized_name}")

            # 1. DB 캐시 확인
            cached = await self._fetch_recipe(normalized_name)
            if cached:
                logger.info(f"[RecipeGenerator] Cache hit: {dish_name}")
                # 캐시된 레시피에 discount_items 추가
                cached["discount_items"] = discount_items
                recipes.append(cached)
                continue

            # 2. LLM 생성 + DB 저장
            logger.info(f"[RecipeGenerator] Cache miss, generating: {dish_name}")
            recipe = await self._generate_recipe(dish_name, entities.get("servings"))
            if recipe:
                await self._save_recipe(normalized_name, dish_name, recipe)
                # 생성된 레시피에 discount_items 추가
                recipe["discount_items"] = discount_items
                recipes.append(recipe)

        return {"recipes": recipes}

    async def _fetch_recipe(self, normalized_name: str) -> dict | None:
        """DB에서 레시피 조회"""
        try:
            return await _fetch_recipe_from_db(normalized_name)
        except Exception as e:
            logger.warning(f"[RecipeGenerator] DB 조회 실패: {e}")
            return None

    async def _generate_recipe(self, dish_name: str, servings: str | None) -> dict | None:
        """LLM으로 레시피 생성"""
        prompts = render_prompt(
            self.templates,
            dish_name=dish_name,
            servings=servings
        )

        response = await self.llm.generate(
            prompt=prompts["user"],
            system=prompts["system"],
            option={"temperature": 0.7, "max_tokens": 2048}
        )

        return self._parse_response(response)

    async def _save_recipe(self, normalized_name: str, display_name: str, recipe: dict) -> None:
        """DB에 레시피 저장"""
        try:
            await _save_recipe_to_db(normalized_name, display_name, recipe)
            logger.info(f"[RecipeGenerator] Saved to DB: {display_name}")
        except Exception as e:
            logger.warning(f"[RecipeGenerator] DB 저장 실패: {e}")

    def _parse_response(self, response: str) -> dict | None:
        """LLM 응답에서 레시피 파싱"""
        try:
            text = response.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            return json.loads(text)
        except (json.JSONDecodeError, IndexError) as e:
            logger.warning(f"[RecipeGenerator] JSON 파싱 실패: {e}, response: {response[:200]}")
            return None


@transactional_readonly
async def _fetch_recipe_from_db(normalized_name: str) -> dict | None:
    """DB에서 레시피 조회 (읽기 전용)"""
    ctx = get_connection()
    row = await ctx.fetch_one(
        "SELECT content FROM recipe WHERE dish_name = $1",
        normalized_name
    )
    if not row:
        return None
    content = row["content"]
    # asyncpg가 str로 반환하면 파싱
    if isinstance(content, str):
        return json.loads(content)
    return content


@transactional
async def _save_recipe_to_db(normalized_name: str, display_name: str, recipe: dict) -> None:
    """DB에 레시피 저장"""
    ctx = get_connection()
    await ctx.execute(
        """
        INSERT INTO recipe (dish_name, display_name, content)
        VALUES ($1, $2, $3)
        ON CONFLICT (dish_name) DO UPDATE SET content = $3
        """,
        normalized_name,
        display_name,
        json.dumps(recipe, ensure_ascii=False)
    )
