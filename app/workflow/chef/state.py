"""Chef 워크플로우 상태 정의"""

from typing import TypedDict


class State(TypedDict):
    user_input: str
    intents: list[str]
    entities: dict  # {"name": "value", ...} ex) {"cuisine": "한식", "ingredients": ["양파", "감자"]}
    dishes: list[dict]  # [{"name": "삼겹살구이", "discount_items": [{"name": "삼겹살", "discount_rate": 30}]}]
    recipes: list[dict]
    qa_answer: str | None
    response: str | None
