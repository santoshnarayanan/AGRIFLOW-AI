"""Platform authentication API (Phase 15 slice 5)."""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AuthServiceDep, SessionDep
from app.core.config import get_settings
from app.core.security.platform_auth import PlatformOperatorDep
from app.db.repositories.platform_user import PlatformUserRepository
from app.schemas.auth import LoginRequest, PlatformUserResponse, TokenResponse
from app.services.auth import InvalidCredentialsError

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    auth_service: AuthServiceDep,
) -> TokenResponse:
    """Issue a JWT for an active platform operator account."""
    try:
        _user, token = await auth_service.authenticate(body.email, body.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    settings = get_settings()
    return TokenResponse(
        access_token=token,
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


@router.get("/me", response_model=PlatformUserResponse)
async def get_current_platform_user(
    principal: PlatformOperatorDep,
    session: SessionDep,
) -> PlatformUserResponse:
    """Return the authenticated platform user (JWT or development bypass)."""
    if principal.auth_method in {"development_bypass", "ops_key"}:
        return PlatformUserResponse(
            id=uuid.UUID("00000000-0000-4000-8000-000000000099"),
            email=principal.email or "ops@agriflow.local",
            role=principal.role,
            is_active=True,
        )

    try:
        user_id = uuid.UUID(principal.subject)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid subject.") from exc

    user = await PlatformUserRepository(session).get_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    return PlatformUserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
    )
