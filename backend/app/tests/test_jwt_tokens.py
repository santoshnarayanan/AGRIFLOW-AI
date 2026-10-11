"""JWT helper tests (Phase 15 slice 5)."""

from uuid import uuid4

from app.core.enums import PlatformRole
from app.core.security.jwt_tokens import create_access_token, decode_access_token


def test_access_token_roundtrip() -> None:
    user_id = uuid4()
    token = create_access_token(
        user_id=user_id,
        email="operator@agriflow.local",
        role=PlatformRole.OPERATOR,
        expires_minutes=30,
    )
    claims = decode_access_token(token)
    assert claims["sub"] == str(user_id)
    assert claims["email"] == "operator@agriflow.local"
    assert claims["role"] == PlatformRole.OPERATOR.value
