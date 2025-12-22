"""Domain entities with business logic and validation"""
from .recipe import Recipe
from .question import Answer
from .recommendation import Recommendation, DishRecommendation

__all__ = ["Recipe", "Answer", "Recommendation", "DishRecommendation"]
