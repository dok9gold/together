"""Piri Framework DI Decorators

의존성 주입을 위한 데코레이터를 제공합니다.
injector 라이브러리를 기반으로 합니다.
"""
from injector import singleton, inject
from typing import Type, Generator, Callable

__all__ = ['singleton', 'inject', 'get_dependency']


def get_dependency(use_case_class: Type) -> Callable:
    """FastAPI Depends용 제네릭 의존성 주입 헬퍼

    UseCase 클래스를 받아서 FastAPI Depends에서 사용할 수 있는
    의존성 함수를 반환합니다.

    사용법:
        @router.post("/cooking")
        async def handle_cooking_query(
            use_case: CreateRecipeUseCase = Depends(get_dependency(CreateRecipeUseCase))
        ):
            return await use_case.execute(...)

    Args:
        use_case_class: UseCase 클래스 타입

    Returns:
        FastAPI Depends용 제네릭 함수
    """
    def dependency() -> Generator:
        # 순환 참조 방지를 위해 여기서 import
        from app.core.dependencies import get_injector
        injector = get_injector()
        yield injector.get(use_case_class)

    return dependency
