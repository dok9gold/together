"""
데이터베이스 레지스트리

다중 DB 인스턴스를 이름 기반으로 관리합니다.
"""

import logging

from core.database.base import BaseDatabase

logger = logging.getLogger(__name__)


class DatabaseRegistry:
    """다중 DB 인스턴스 관리 (이름 기반)"""
    _databases: dict[str, BaseDatabase] = {}

    @classmethod
    def register(cls, name: str, db: BaseDatabase) -> None:
        """DB 등록"""
        cls._databases[name] = db
        logger.info(f"Database '{name}' registered")

    @classmethod
    def get(cls, name: str) -> BaseDatabase:
        """DB 조회"""
        if name not in cls._databases:
            raise KeyError(f"Database '{name}' not registered")
        return cls._databases[name]

    @classmethod
    def get_all(cls) -> dict[str, BaseDatabase]:
        """모든 DB 조회"""
        return cls._databases.copy()

    @classmethod
    async def close_all(cls) -> None:
        """모든 DB 연결 종료"""
        for name, db in cls._databases.items():
            await db.close()
        cls._databases.clear()
        logger.info("All databases closed")

    @classmethod
    def clear(cls) -> None:
        """레지스트리 초기화 (테스트용)"""
        cls._databases.clear()
