"""Authentication service — JWT login for platform operators."""

from __future__ import annotations

from app.core.enums import PlatformRole
from app.core.security.jwt_tokens import create_access_token
from app.core.security.passwords import verify_password
from app.db.models.platform_user import PlatformUser
from app.db.repositories.platform_user import PlatformUserRepository


class InvalidCredentialsError(ValueError):
    """Raised when email/password do not match an active user."""


class AuthService:
    def __init__(self, user_repository: PlatformUserRepository) -> None:
        self._users = user_repository

    async def authenticate(self, email: str, password: str) -> tuple[PlatformUser, str]:
        user = await self._users.get_by_email(email.strip().lower())
        if user is None or not user.is_active:
            raise InvalidCredentialsError("Invalid email or password.")
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password.")
        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
        )
        return user, token

    @staticmethod
    def role_allows_operator_actions(role: PlatformRole) -> bool:
        return role in {PlatformRole.OPERATOR, PlatformRole.ADMIN}
