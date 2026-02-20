import os
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User as SqlUser
from app.models.auth import UserCredential


def resolve_auth_provider(mongo_enabled: bool) -> str:
    provider = os.environ.get("AUTH_PROVIDER")
    if provider:
        return provider.lower()
    return "mongo" if mongo_enabled else "sql"


class AuthRepository:
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    async def update_last_login(self, user_id: str, iso_timestamp: str) -> None:
        raise NotImplementedError


class MongoAuthRepository(AuthRepository):
    def __init__(self, db):
        self.db = db

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        if not self.db:
            return None
        return await self.db.users.find_one({"email": email}, {"_id": 0})

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not self.db:
            return None
        return await self.db.users.find_one({"id": user_id}, {"_id": 0})

    async def update_last_login(self, user_id: str, iso_timestamp: str) -> None:
        if not self.db:
            return
        await self.db.users.update_one({"id": user_id}, {"$set": {"last_login": iso_timestamp}})


class SqlAuthRepository(AuthRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_password_hash(self, user_id: uuid.UUID) -> Optional[str]:
        result = await self.session.execute(
            select(UserCredential).where(
                UserCredential.user_id == user_id,
                UserCredential.provider == "password",
            )
        )
        cred = result.scalar_one_or_none()
        if cred and cred.password_hash:
            return cred.password_hash
        return None

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        result = await self.session.execute(select(SqlUser).where(SqlUser.email == email))
        user = result.scalar_one_or_none()
        if not user:
            return None
        password_hash = await self._get_password_hash(user.id) or user.hashed_password
        return _sql_user_to_dict(user, password_hash)

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            user_uuid = uuid.UUID(str(user_id))
        except ValueError:
            return None
        result = await self.session.execute(select(SqlUser).where(SqlUser.id == user_uuid))
        user = result.scalar_one_or_none()
        if not user:
            return None
        password_hash = await self._get_password_hash(user.id) or user.hashed_password
        return _sql_user_to_dict(user, password_hash)

    async def update_last_login(self, user_id: str, iso_timestamp: str) -> None:
        try:
            user_uuid = uuid.UUID(str(user_id))
        except ValueError:
            return
        result = await self.session.execute(select(SqlUser).where(SqlUser.id == user_uuid))
        user = result.scalar_one_or_none()
        if not user:
            return
        user.last_login = datetime.fromisoformat(iso_timestamp)
        await self.session.commit()


def _sql_user_to_dict(user: SqlUser, password_hash: Optional[str]) -> Dict[str, Any]:
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
        "hashed_password": password_hash,
        "deleted_at": None,
    }
