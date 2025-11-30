"""FastAPI Dependencies - Injector 및 인증 관리

FastAPI의 Depends에서 사용할 의존성 주입 헬퍼 함수들입니다.

Note:
    UseCase 의존성은 app.core.decorators.get_dependency()를 사용하세요.
    이 파일은 Injector 싱글톤 및 인증 관련 의존성만 관리합니다.
"""
from typing import Optional
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from injector import Injector
from app.core.module import CookingModule
from app.core.auth import AuthService
from app.core.config import get_settings

# FastAPI HTTPBearer 스키마
security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)

# 글로벌 Injector (싱글톤)
_injector: Optional[Injector] = None

# 글로벌 AuthService (싱글톤)
_auth_service: Optional[AuthService] = None


def get_injector() -> Injector:
    """Injector 싱글톤 반환

    Returns:
        Injector: DI Injector 인스턴스
    """
    global _injector
    if _injector is None:
        _injector = Injector([CookingModule()])
    return _injector


def get_auth_service() -> AuthService:
    """AuthService 싱글톤 반환

    환경 변수에서 SECRET_KEY를 읽어 AuthService를 생성합니다.

    Returns:
        AuthService: JWT 인증 서비스 인스턴스
    """
    global _auth_service
    if _auth_service is None:
        settings = get_settings()
        _auth_service = AuthService(secret_key=settings.secret_key)
    return _auth_service


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> str:
    """현재 사용자 인증 (필수)

    Authorization 헤더의 Bearer 토큰을 검증하여 user_id를 반환합니다.
    토큰이 없거나 유효하지 않으면 401 에러를 발생시킵니다.

    Args:
        credentials: HTTP Bearer 토큰 (자동 주입)
        auth_service: 인증 서비스 (자동 주입)

    Returns:
        str: 인증된 사용자 ID

    Raises:
        HTTPException: 401 (토큰 없음 or 검증 실패)

    Example:
        @router.post("/cooking")
        async def handle_cooking_query(
            request: CookingRequest,
            user_id: str = Depends(get_current_user)
        ):
            # user_id를 사용하여 요청 처리
            ...
    """
    token = credentials.credentials
    user_id = auth_service.verify_token(token)
    return user_id


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[str]:
    """옵셔널 인증 (토큰 없어도 통과)

    토큰이 있으면 검증하여 user_id를 반환하고,
    없으면 None을 반환합니다. (401 에러 발생 안 함)

    Args:
        credentials: HTTP Bearer 토큰 (선택적)
        auth_service: 인증 서비스 (자동 주입)

    Returns:
        Optional[str]: 인증된 사용자 ID (토큰 없으면 None)

    Example:
        @router.post("/cooking-public")
        async def handle_cooking_query_public(
            request: CookingRequest,
            user_id: Optional[str] = Depends(get_optional_user)
        ):
            # user_id가 None이면 익명 사용자
            if user_id:
                # 로그인한 사용자용 개인화 처리
                ...
            else:
                # 익명 사용자용 일반 처리
                ...
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        return auth_service.verify_token(token)
    except Exception:
        # 검증 실패해도 통과 (로그는 AuthService에서 이미 남김)
        return None
