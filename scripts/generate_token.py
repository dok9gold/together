"""JWT 토큰 생성 스크립트

인증 테스트를 위한 JWT 토큰을 생성합니다.

Usage:
    python scripts/generate_token.py user123
    python scripts/generate_token.py user456 --hours 48
"""
import sys
import os
from datetime import timedelta

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.auth import AuthService
from app.core.config import get_settings


def main():
    """토큰 생성 및 출력"""
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_token.py <user_id> [--hours <hours>]")
        print("Example: python scripts/generate_token.py user123")
        print("Example: python scripts/generate_token.py user456 --hours 48")
        sys.exit(1)

    user_id = sys.argv[1]

    # 만료 시간 설정 (기본 24시간)
    hours = 24
    if "--hours" in sys.argv:
        hours_index = sys.argv.index("--hours")
        if hours_index + 1 < len(sys.argv):
            hours = int(sys.argv[hours_index + 1])

    # 설정 로드
    settings = get_settings()
    auth_service = AuthService(secret_key=settings.secret_key)

    # 토큰 생성
    token = auth_service.create_access_token(
        user_id=user_id,
        expires_delta=timedelta(hours=hours)
    )

    print(f"\n{'=' * 80}")
    print(f"JWT Token Generated Successfully!")
    print(f"{'=' * 80}")
    print(f"\nUser ID: {user_id}")
    print(f"Expires in: {hours} hours")
    print(f"\nToken:")
    print(f"{token}")
    print(f"\n{'=' * 80}")
    print(f"\nTest with curl:")
    print(f"{'=' * 80}")
    print(f"""
curl -X POST http://localhost:8000/api/cooking \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer {token}" \\
  -d '{{"query": "김치찌개 만드는 법"}}'
""")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
