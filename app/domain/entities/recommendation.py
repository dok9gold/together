"""Recommendation - 음식 추천 엔티티

음식 추천 결과를 표현하는 비즈니스 객체입니다.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class DishRecommendation:
    """단일 음식 추천 항목

    Attributes:
        name: 음식 이름
        description: 음식 설명
        reason: 추천 이유

    Example:
        >>> rec = DishRecommendation(
        ...     name="김치찌개",
        ...     description="한국의 전통 찌개",
        ...     reason="매운맛을 좋아하시는 분께 추천"
        ... )
    """
    name: str
    description: str
    reason: str


@dataclass
class Recommendation:
    """음식 추천 결과 엔티티

    여러 개의 음식 추천 항목을 담는 도메인 모델입니다.

    Attributes:
        recommendations: 추천 항목 리스트

    Example:
        >>> rec1 = DishRecommendation("김치찌개", "한국 찌개", "매운맛")
        >>> rec2 = DishRecommendation("된장찌개", "구수한 찌개", "담백한 맛")
        >>> recommendation = Recommendation([rec1, rec2])
        >>> recommendation.get_count()
        2
    """
    recommendations: List[DishRecommendation]

    def get_count(self) -> int:
        """추천 개수 반환

        Returns:
            int: 추천 항목 개수
        """
        return len(self.recommendations)

    def get_dish_names(self) -> List[str]:
        """추천 음식 이름 목록 반환

        Returns:
            List[str]: 음식 이름 목록
        """
        return [rec.name for rec in self.recommendations]
