"""JWT 기반 인증 서비스

사용자 인증을 위한 JWT 토큰 생성 및 검증 기능을 제공합니다.
"""
from fastapi import HTTPException, status
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """JWT 기반 인증 서비스

    책임:
    - JWT 액세스 토큰 생성
    - JWT 토큰 검증 및 user_id 추출
    - 인증 실패 시 HTTPException 발생

    Attributes:
        secret_key: JWT 서명에 사용할 비밀키
        algorithm: JWT 알고리즘 (기본: HS256)
    """

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """AuthService 초기화

        Args:
            secret_key: JWT 서명 비밀키 (환경 변수에서 주입)
            algorithm: JWT 알고리즘 (기본값: HS256)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(
        self,
        user_id: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """액세스 토큰 생성

        Args:
            user_id: 사용자 ID
            expires_delta: 만료 시간 (기본값: 24시간)

        Returns:
            str: JWT 토큰

        Example:
            >>> auth = AuthService(secret_key="my-secret")
            >>> token = auth.create_access_token(user_id="user123")
            >>> print(token)
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
        """
        to_encode = {"sub": user_id}

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)

        to_encode.update({"exp": expire})

        logger.debug(f"[Auth] 토큰 생성 - user_id: {user_id}, expire: {expire}")

        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> str:
        """토큰 검증 및 user_id 추출

        Args:
            token: JWT 토큰

        Returns:
            str: user_id

        Raises:
            HTTPException: 토큰 검증 실패 시 401 에러
                - 토큰이 유효하지 않음
                - 토큰이 만료됨
                - user_id(sub)가 없음

        Example:
            >>> auth = AuthService(secret_key="my-secret")
            >>> user_id = auth.verify_token(token)
            >>> print(user_id)
            'user123'
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            user_id: str = payload.get("sub")

            if user_id is None:
                logger.warning("[Auth] 토큰에 user_id(sub)가 없음")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="유효하지 않은 토큰",
                    headers={"WWW-Authenticate": "Bearer"}
                )

            logger.debug(f"[Auth] 토큰 검증 성공 - user_id: {user_id}")
            return user_id

        except JWTError as e:
            logger.warning(f"[Auth] 토큰 검증 실패: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="토큰 검증 실패",
                headers={"WWW-Authenticate": "Bearer"}
            )
