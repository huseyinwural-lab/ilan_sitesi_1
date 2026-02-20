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
MONGO_ENABLED_RAW = os.environ.get("MONGO_ENABLED")
if APP_ENV == "prod":
    MONGO_ENABLED = False
else:
    if MONGO_ENABLED_RAW is None:
        MONGO_ENABLED = True
    else:
        MONGO_ENABLED = MONGO_ENABLED_RAW.lower() in {"1", "true", "yes"}

AUTH_PROVIDER = (os.environ.get("AUTH_PROVIDER") or ("mongo" if MONGO_ENABLED else "sql")).lower()


def get_mongo_db(request: Request):
    db = getattr(request.app.state, "db", None)
    if not MONGO_ENABLED or db is None:
        raise HTTPException(status_code=503, detail="Mongo disabled")
    return db


async def _get_sql_user(user_id: str, session: AsyncSession) -> Optional[dict]:
    try:
        user_uuid = uuid.UUID(str(user_id))
    except ValueError:
        return None
    result = await session.execute(select(SqlUser).where(SqlUser.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user:
        return None
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "country_scope": user.country_scope or [],
        "country_code": user.country_code,
        "preferred_language": user.preferred_language,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    sql_session: AsyncSession = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = decode_token(token)

    if not payload or payload.get("type") != "access":
        raise credentials_exception

    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception

    db = getattr(request.app.state, "db", None) if request else None
    if AUTH_PROVIDER == "sql" or not MONGO_ENABLED or db is None:
        user = await _get_sql_user(user_id, sql_session)
    else:
        user = await db.users.find_one({"id": user_id}, {"_id": 0})

    if not user or not user.get("is_active", False):
        raise credentials_exception

    return user


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    sql_session: AsyncSession = Depends(get_db),
):
    if not credentials:
        return None

    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    db = getattr(request.app.state, "db", None) if request else None
    if AUTH_PROVIDER == "sql" or not MONGO_ENABLED or db is None:
        return await _get_sql_user(user_id, sql_session)

    return await db.users.find_one({"id": user_id}, {"_id": 0})


def check_permissions(required_roles: list[str]):
    async def permission_checker(current_user=Depends(get_current_user)):
        if current_user.get("role") not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return permission_checker
