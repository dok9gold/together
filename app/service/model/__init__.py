# Service Models (Request/Response Schemas)
from .common import DiscountInfo, RecipeItem
from .chat import ChatRequest, ChatResponse, ChatAction
from .recommend import RecommendRequest, RecommendResponse
from .recipe import RecipeSearchResponse, RecipeDetail, IngredientDetail, StepDetail
from .discount import DiscountItem, DiscountRecommendRequest, DiscountRecommendResponse, DiscountRecipeItem
from .fridge import FridgeRecommendRequest, FridgeRecommendResponse, FridgeRecipeItem
from .cart import CartItem, CartAddRequest, CartAddResponse
