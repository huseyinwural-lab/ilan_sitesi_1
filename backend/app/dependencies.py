import os
import uuid
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.core.database import get_db
from app.models.user import User as SqlUser

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)

APP_ENV = (os.environ.get("APP_ENV") or "dev").lower()
TOKEN_VERSION = os.environ.get("TOKEN_VERSION", "v2")

ADMIN_ROLES = {
    "super_admin",
    "country_admin",
    "moderator",
    "support",
    "finance",
    "campaigns_admin",
    "campaigns_supervisor",
    "ROLE_AUDIT_VIEWER",
    "audit_viewer",
}

DEALER_ROLES = {"dealer"}


async def _get_sql_user(user_id: str, session: AsyncSession) -> Optional[SqlUser]:
    try:
        user_uuid = uuid.UUID(str(user_id))
    except ValueError:
        return None
    result = await session.execute(select(SqlUser).where(SqlUser.id == user_uuid))
    return result.scalar_one_or_none()


def _resolve_portal_scope(role: Optional[str]) -> str:
    if not role:
        return "account"
    if role in DEALER_ROLES:
        return "dealer"
    if role in ADMIN_ROLES:
        return "admin"
    return "account"


def _infer_required_portal_scope(required_roles: Optional[list]) -> Optional[str]:
    if not required_roles:
        return None
    if any(role in DEALER_ROLES for role in required_roles):
        return "dealer"
    if any(role in ADMIN_ROLES for role in required_roles):
        return "admin"
    return "account"


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    sql_session: AsyncSession = Depends(get_db),
):
    cached_user = getattr(request.state, "current_user", None)
    if cached_user:
        return cached_user

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = decode_token(token)

    if not payload or payload.get("type") != "access":
        raise credentials_exception

    if payload.get("token_version") != TOKEN_VERSION:
        raise credentials_exception

    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception

    user = await _get_sql_user(user_id, sql_session)

    if not user or not user.is_active:
        raise credentials_exception

    token_scope = payload.get("portal_scope")
    if not token_scope:
        raise credentials_exception
    expected_scope = _resolve_portal_scope(user.role)
    if token_scope != expected_scope:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Portal scope mismatch")
    user.portal_scope = token_scope
    if user.country_scope is None:
        user.country_scope = []
    request.state.current_user = user

    return user


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    sql_session: AsyncSession = Depends(get_db),
):
    cached_user = getattr(request.state, "current_user", None)
    if cached_user:
        return cached_user

    if not credentials:
        return None

    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        return None
    if payload.get("token_version") != TOKEN_VERSION:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = await _get_sql_user(user_id, sql_session)

    if not user:
        return None

    token_scope = payload.get("portal_scope")
    if not token_scope:
        return None
    expected_scope = _resolve_portal_scope(user.role)
    if token_scope != expected_scope:
        return None
    user.portal_scope = token_scope
    if user.country_scope is None:
        user.country_scope = []
    request.state.current_user = user

    return user


def check_permissions(required_roles: list[str]):
    required_scope = _infer_required_portal_scope(required_roles)

    async def permission_checker(current_user=Depends(get_current_user)):
        if current_user.get("role") not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        if required_scope and current_user.get("portal_scope") != required_scope:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Portal scope mismatch",
            )
        return current_user

    permission_checker.required_roles = required_roles
    permission_checker.required_scope = required_scope

    return permission_checker


def require_portal_scope(scope: str):
    async def portal_checker(current_user=Depends(get_current_user)):
        if current_user.get("portal_scope") != scope:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Portal scope mismatch",
            )
        return current_user

    return portal_checker
