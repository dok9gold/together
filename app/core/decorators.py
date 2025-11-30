"""Piri Framework DI Decorators

의존성 주입을 위한 데코레이터를 제공합니다.
injector 라이브러리를 기반으로 합니다.
"""
from injector import singleton, inject

__all__ = ['singleton', 'inject']
