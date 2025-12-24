"""Chef 응답 모델"""

from pydantic import BaseModel


class ChefResponse(BaseModel):
    """Chef AI 응답"""
    intents: list[str]
    entities: dict
    dishes: list[str]
    response: str | None
