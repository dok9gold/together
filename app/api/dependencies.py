"""FastAPI Dependencies - DI Container 연동

FastAPI의 Depends에서 사용할 의존성 주입 헬퍼 함수들입니다.
"""
from typing import Generator
from app.core.container import Container
from app.application.use_cases.create_recipe_use_case import CreateRecipeUseCase

# 글로벌 컨테이너 (싱글톤)
_container: Container = None


def get_container() -> Container:
    """컨테이너 싱글톤 반환

    Returns:
        Container: DI 컨테이너 인스턴스
    """
    global _container
    if _container is None:
        _container = Container()
    return _container


def get_create_recipe_use_case() -> Generator[CreateRecipeUseCase, None, None]:
    """레시피 생성 유스케이스 반환 (FastAPI Depends용)

    Yields:
        CreateRecipeUseCase: 레시피 생성 유스케이스 인스턴스
    """
    container = get_container()
    yield container.create_recipe_use_case()
