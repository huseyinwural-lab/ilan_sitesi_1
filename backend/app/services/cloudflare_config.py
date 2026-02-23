import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Tuple

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cloudflare_config import CloudflareConfig


class CloudflareConfigError(RuntimeError):
    def __init__(self, message: str, code: str = "config_error") -> None:
        super().__init__(message)
        self.code = code


@dataclass
class CloudflareMaskedConfig:
    account_masked: Optional[str]
    zone_masked: Optional[str]
    account_last4: Optional[str]
    zone_last4: Optional[str]
    source: Optional[str]
    present: bool
    canary_status: Optional[str]
    canary_checked_at: Optional[str]


def _get_config_fernet() -> Fernet:
    key = os.environ.get("CONFIG_ENCRYPTION_KEY")
    if not key:
        raise CloudflareConfigError("CONFIG_ENCRYPTION_KEY missing", code="config_key_missing")
    try:
        return Fernet(key)
    except Exception as exc:
        raise CloudflareConfigError("CONFIG_ENCRYPTION_KEY invalid", code="config_key_invalid") from exc


def _mask_last4(last4: Optional[str]) -> Optional[str]:
    if not last4:
        return None
    return f"••••{last4}"


def encrypt_config_value(value: str) -> Tuple[str, str]:
    fernet = _get_config_fernet()
    token = fernet.encrypt(value.encode("utf-8")).decode("utf-8")
    last4 = value[-4:] if len(value) >= 4 else value
    return token, last4


def decrypt_config_value(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    fernet = _get_config_fernet()
    try:
        return fernet.decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise CloudflareConfigError("CONFIG_ENCRYPTION_KEY mismatch", code="config_key_mismatch") from exc


def resolve_env_fallback() -> Tuple[Optional[str], Optional[str]]:
    env_account = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    env_zone = os.environ.get("CLOUDFLARE_ZONE_ID")
    return env_account, env_zone


def resolve_env_source(env_account: Optional[str], env_zone: Optional[str]) -> Optional[str]:
    if not env_account or not env_zone:
        return None
    env_file_path = "/app/backend/.env"
    try:
        if os.path.exists(env_file_path):
            content = open(env_file_path, "r", encoding="utf-8").read()
            file_account = None
            file_zone = None
            for line in content.splitlines():
                if line.startswith("CLOUDFLARE_ACCOUNT_ID="):
                    file_account = line.split("=", 1)[1].strip().strip('"')
                if line.startswith("CLOUDFLARE_ZONE_ID="):
                    file_zone = line.split("=", 1)[1].strip().strip('"')
            if file_account and file_zone:
                if file_account == env_account and file_zone == env_zone:
                    return "env"
    except Exception:
        return "secret"
    return "secret"


async def fetch_cloudflare_config(session: AsyncSession) -> Optional[CloudflareConfig]:
    result = await session.execute(select(CloudflareConfig))
    return result.scalars().first()


async def upsert_cloudflare_config(
    session: AsyncSession,
    account_token: str,
    account_last4: str,
    zone_token: str,
    zone_last4: str,
    updated_by: Optional[str],
) -> CloudflareConfig:
    config = await fetch_cloudflare_config(session)
    now = datetime.now(timezone.utc)
    if config is None:
        config = CloudflareConfig(
            id=uuid.uuid4(),
            account_id_encrypted=account_token,
            account_id_last4=account_last4,
            zone_id_encrypted=zone_token,
            zone_id_last4=zone_last4,
            created_at=now,
            updated_at=now,
            updated_by=updated_by,
        )
    else:
        config.account_id_encrypted = account_token
        config.account_id_last4 = account_last4
        config.zone_id_encrypted = zone_token
        config.zone_id_last4 = zone_last4
        config.updated_at = now
        config.updated_by = updated_by
    session.add(config)
    await session.commit()
    await session.refresh(config)
    return config


async def update_canary_status(
    session: AsyncSession,
    status: str,
    updated_by: Optional[str],
) -> CloudflareConfig:
    config = await fetch_cloudflare_config(session)
    now = datetime.now(timezone.utc)
    if config is None:
        config = CloudflareConfig(
            id=uuid.uuid4(),
            canary_status=status,
            canary_checked_at=now,
            created_at=now,
            updated_at=now,
            updated_by=updated_by,
        )
    else:
        config.canary_status = status
        config.canary_checked_at = now
        config.updated_at = now
        config.updated_by = updated_by
    session.add(config)
    await session.commit()
    await session.refresh(config)
    return config


async def resolve_cloudflare_config(session: Optional[AsyncSession]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    env_account, env_zone = resolve_env_fallback()
    if env_account and env_zone:
        return env_account, env_zone, resolve_env_source(env_account, env_zone)

    if session is not None:
        config = await fetch_cloudflare_config(session)
        if config and config.account_id_encrypted and config.zone_id_encrypted:
            account_value = decrypt_config_value(config.account_id_encrypted)
            zone_value = decrypt_config_value(config.zone_id_encrypted)
            if account_value and zone_value:
                return account_value, zone_value, "db"

    # fallback to .env file if not in env
    try:
        if os.path.exists("/app/backend/.env"):
            content = open("/app/backend/.env", "r", encoding="utf-8").read()
            file_account = None
            file_zone = None
            for line in content.splitlines():
                if line.startswith("CLOUDFLARE_ACCOUNT_ID="):
                    file_account = line.split("=", 1)[1].strip().strip('"')
                if line.startswith("CLOUDFLARE_ZONE_ID="):
                    file_zone = line.split("=", 1)[1].strip().strip('"')
            if file_account and file_zone:
                return file_account, file_zone, "env"
    except Exception:
        pass

    return None, None, None


async def build_masked_config(session: Optional[AsyncSession]) -> CloudflareMaskedConfig:
    env_account, env_zone = resolve_env_fallback()
    if env_account and env_zone:
        source = resolve_env_source(env_account, env_zone)
        return CloudflareMaskedConfig(
            account_masked=_mask_last4(env_account[-4:]),
            zone_masked=_mask_last4(env_zone[-4:]),
            account_last4=env_account[-4:],
            zone_last4=env_zone[-4:],
            source=source,
            present=True,
            canary_status=None,
            canary_checked_at=None,
        )

    if session is not None:
        config = await fetch_cloudflare_config(session)
        if config:
            return CloudflareMaskedConfig(
                account_masked=_mask_last4(config.account_id_last4),
                zone_masked=_mask_last4(config.zone_id_last4),
                account_last4=config.account_id_last4,
                zone_last4=config.zone_id_last4,
                source="db" if config.account_id_last4 and config.zone_id_last4 else None,
                present=bool(config.account_id_last4 and config.zone_id_last4),
                canary_status=config.canary_status,
                canary_checked_at=config.canary_checked_at.isoformat() if config.canary_checked_at else None,
            )

    file_account = None
    file_zone = None
    try:
        if os.path.exists("/app/backend/.env"):
            content = open("/app/backend/.env", "r", encoding="utf-8").read()
            for line in content.splitlines():
                if line.startswith("CLOUDFLARE_ACCOUNT_ID="):
                    file_account = line.split("=", 1)[1].strip().strip('"')
                if line.startswith("CLOUDFLARE_ZONE_ID="):
                    file_zone = line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass

    if file_account and file_zone:
        return CloudflareMaskedConfig(
            account_masked=_mask_last4(file_account[-4:]),
            zone_masked=_mask_last4(file_zone[-4:]),
            account_last4=file_account[-4:],
            zone_last4=file_zone[-4:],
            source="env",
            present=True,
            canary_status=None,
            canary_checked_at=None,
        )

    return CloudflareMaskedConfig(
        account_masked=None,
        zone_masked=None,
        account_last4=None,
        zone_last4=None,
        source=None,
        present=False,
        canary_status=None,
        canary_checked_at=None,
    )
