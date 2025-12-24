"""Chef 서비스 - AI 워크플로우 실행"""


class ChefService:
    """Chef AI 서비스"""

    async def process(self, user_input: str, discount_items: list[dict] | None = None):
        """
        사용자 입력 처리
        
        Args:
            user_input: 사용자 입력
            discount_items: 선택된 할인상품 [{"name": "...", "barcode": "..."}]
        """
        # TODO: LangGraph 워크플로우 연동
        pass
