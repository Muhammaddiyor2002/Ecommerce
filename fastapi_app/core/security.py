"""JWT validation that matches Django SimpleJWT-issued tokens."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import jwt
from fastapi import Header, HTTPException, status

from .config import get_settings

_settings = get_settings()


@dataclass(slots=True)
class TokenUser:
    id: str
    email: str
    roles: list[str]
    is_staff: bool
    raw: dict[str, Any]


def _decode(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            _settings.jwt_signing_key,
            algorithms=[_settings.jwt_algorithm],
            options={"verify_aud": False},
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token") from exc


def _extract_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    return authorization.split(" ", 1)[1].strip()


async def get_current_user(authorization: str | None = Header(default=None)) -> TokenUser:
    payload = _decode(_extract_token(authorization))
    return TokenUser(
        id=str(payload.get("user_id") or payload.get("sub") or ""),
        email=payload.get("email", ""),
        roles=list(payload.get("roles") or []),
        is_staff=bool(payload.get("is_staff", False)),
        raw=payload,
    )


async def get_optional_user(
    authorization: str | None = Header(default=None),
) -> TokenUser | None:
    if not authorization:
        return None
    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None


def require_staff(user: TokenUser) -> None:
    if not user.is_staff and "staff" not in user.roles and "admin" not in user.roles:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "staff only")
