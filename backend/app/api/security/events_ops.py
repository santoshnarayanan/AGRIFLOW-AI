"""Backward-compatible alias for platform operator authentication."""

from app.core.security.platform_auth import PlatformOperatorDep, require_platform_operator

__all__ = ["PlatformOperatorDep", "require_platform_operator"]
