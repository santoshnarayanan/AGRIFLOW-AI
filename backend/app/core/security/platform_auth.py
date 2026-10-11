"""JWT + ops-key authentication for platform operator routes (Phase 15)."""

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status

from app.core.config import get_settings
from app.core.enums import PlatformRole
from app.core.security.jwt_tokens import decode_access_token


@dataclass(frozen=True, slots=True)
class PlatformPrincipal:
    """Authenticated caller for operator/intelligence APIs."""

    subject: str
    email: str | None
    role: PlatformRole
    auth_method: str  # jwt | ops_key | development_bypass


_OPERATOR_ROLES = {PlatformRole.OPERATOR, PlatformRole.ADMIN}


def _role_from_claim(value: str) -> PlatformRole:
    try:
        return PlatformRole(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token contains an invalid role.",
        ) from None


async def require_platform_operator(
    authorization: Annotated[str | None, Header()] = None,
    x_events_ops_key: Annotated[str | None, Header(alias="X-Events-Ops-Key")] = None,
) -> PlatformPrincipal:
    """
    Accept JWT (Bearer) or legacy ``X-Events-Ops-Key``.

    When ``AUTH_REQUIRED`` is false in development, unauthenticated access is allowed
    with a synthetic development principal.
    """
    settings = get_settings()

    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        try:
            claims = decode_access_token(token)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
            ) from exc
        role = _role_from_claim(str(claims.get("role", "")))
        if role not in _OPERATOR_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role for this operation.",
            )
        return PlatformPrincipal(
            subject=str(claims.get("sub", "")),
            email=claims.get("email"),
            role=role,
            auth_method="jwt",
        )

    expected_ops = settings.EVENTS_OPS_API_KEY
    if expected_ops and x_events_ops_key == expected_ops:
        return PlatformPrincipal(
            subject="ops-key",
            email=None,
            role=PlatformRole.ADMIN,
            auth_method="ops_key",
        )

    if not settings.AUTH_REQUIRED:
        if settings.APP_ENV == "development":
            return PlatformPrincipal(
                subject="development",
                email=None,
                role=PlatformRole.ADMIN,
                auth_method="development_bypass",
            )

    if not settings.AUTH_REQUIRED and settings.APP_ENV != "production":
        return PlatformPrincipal(
            subject="anonymous",
            email=None,
            role=PlatformRole.OPERATOR,
            auth_method="development_bypass",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Use Bearer JWT or X-Events-Ops-Key.",
    )


PlatformOperatorDep = Annotated[PlatformPrincipal, Depends(require_platform_operator)]
