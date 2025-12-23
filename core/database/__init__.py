"""
데이터베이스 패키지

다중 DB 지원을 위한 공통 인터페이스와 유틸리티를 제공합니다.
"""

from core.database.base import BaseDatabase
from core.database.registry import DatabaseRegistry
from core.database.context import get_connection, set_connection, clear_connection
from core.database.transaction import transactional, transactional_readonly
from core.database.exception import (
    DatabaseError,
    ConnectionPoolExhaustedError,
    TransactionError,
    ReadOnlyTransactionError,
    QueryExecutionError,
)


def get_db(name: str = 'default'):
    """DatabaseRegistry에서 DB 인스턴스 반환 (편의 함수)"""
    return DatabaseRegistry.get(name)


__all__ = [
    'BaseDatabase',
    'DatabaseRegistry',
    'get_connection',
    'set_connection',
    'clear_connection',
    'get_db',
    'transactional',
    'transactional_readonly',
    'DatabaseError',
    'ConnectionPoolExhaustedError',
    'TransactionError',
    'ReadOnlyTransactionError',
    'QueryExecutionError',
]
