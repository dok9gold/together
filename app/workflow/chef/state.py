"""Chef 워크플로우 상태 정의"""

from typing import TypedDict


class State(TypedDict):
    user_input: str
    intents: list[str]
    entities: dict  # {"name": "value", ...} ex) {"cuisine": "한식", "ingredients": ["양파", "감자"]}
    discount_items: list[dict]  # [{"name": "참기름", "barcode": "..."}]
    dishes: list[str]
    recipes: list[dict]
    qa_answer: str | None
    response: str | None
