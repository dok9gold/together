"""Pytest 설정 파일

전역 픽스처 및 설정을 정의합니다.
"""
import pytest
import sys
from pathlib import Path

# 프로젝트 루트를 Python Path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def event_loop_policy():
    """asyncio 이벤트 루프 정책 설정"""
    import asyncio
    return asyncio.get_event_loop_policy()
