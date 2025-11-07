"""Recipe - 레시피 엔티티

레시피를 표현하는 비즈니스 객체입니다.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class Recipe:
    """레시피 엔티티 (비즈니스 객체)

    레시피의 핵심 정보를 담는 도메인 모델입니다.

    Attributes:
        title: 요리 이름
        ingredients: 재료 목록 (분량 포함)
        steps: 조리 단계 목록
        cooking_time: 예상 조리 시간 (예: "30분")
        difficulty: 난이도 ("쉬움", "중간", "어려움")

    Example:
        >>> recipe = Recipe(
        ...     title="김치찌개",
        ...     ingredients=["김치 200g", "돼지고기 100g"],
        ...     steps=["1. 김치를 썬다", "2. 고기를 볶는다"],
        ...     cooking_time="30분",
        ...     difficulty="중간"
        ... )
        >>> recipe.validate()
        True
    """
    title: str
    ingredients: List[str]
    steps: List[str]
    cooking_time: str
    difficulty: str

    def validate(self) -> bool:
        """레시피 유효성 검증 (비즈니스 규칙)

        Returns:
            bool: 유효하면 True, 아니면 False
        """
        # 제목 검증
        if not self.title or len(self.title) < 2:
            return False

        # 재료 검증
        if not self.ingredients or len(self.ingredients) < 1:
            return False

        # 조리 단계 검증
        if not self.steps or len(self.steps) < 1:
            return False

        # 난이도 검증
        valid_difficulties = ["쉬움", "중간", "어려움"]
        if self.difficulty not in valid_difficulties:
            return False

        return True

    def get_total_steps(self) -> int:
        """조리 단계 개수 반환

        Returns:
            int: 조리 단계 개수
        """
        return len(self.steps)

    def get_ingredient_count(self) -> int:
        """재료 개수 반환

        Returns:
            int: 재료 개수
        """
        return len(self.ingredients)
