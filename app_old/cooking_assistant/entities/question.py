"""Question & Answer - 질문/답변 엔티티

요리 관련 질문과 답변을 표현하는 비즈니스 객체입니다.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class Answer:
    """질문 답변 엔티티

    Attributes:
        answer: 답변 내용
        additional_tips: 추가 팁 목록

    Example:
        >>> answer = Answer(
        ...     answer="김치찌개의 칼로리는 1인분 기준 약 250kcal입니다.",
        ...     additional_tips=["돼지고기 양을 줄이면 칼로리를 낮출 수 있습니다."]
        ... )
    """
    answer: str
    additional_tips: List[str]

    def has_tips(self) -> bool:
        """추가 팁 존재 여부 확인

        Returns:
            bool: 추가 팁이 있으면 True
        """
        return len(self.additional_tips) > 0

    def get_tip_count(self) -> int:
        """추가 팁 개수 반환

        Returns:
            int: 추가 팁 개수
        """
        return len(self.additional_tips)
