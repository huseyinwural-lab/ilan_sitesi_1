import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from cryptography.fernet import Fernet, InvalidToken


CLOUDFLARE_ACCOUNT_KEY = "cloudflare.account_id"
CLOUDFLARE_ZONE_KEY = "cloudflare.zone_id"
CLOUDFLARE_CANARY_KEY = "cloudflare.canary_status"


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


def _get_config_fernet() -> Fernet:
    key = os.environ.get("CONFIG_ENCRYPTION_KEY")
    if not key:
        raise CloudflareConfigError("CONFIG_ENCRYPTION_KEY missing", code="config_key_missing")
    try:
        return Fernet(key)
    except Exception as exc:  # pragma: no cover
        raise CloudflareConfigError("CONFIG_ENCRYPTION_KEY invalid", code="config_key_invalid") from exc


def _mask_last4(last4: Optional[str]) -> Optional[str]:
    if not last4:
        return None
    return f"••••{last4}"


def encrypt_config_value(value: str) -> Dict[str, str]:
    fernet = _get_config_fernet()
    token = fernet.encrypt(value.encode("utf-8")).decode("utf-8")
    last4 = value[-4:] if len(value) >= 4 else value
    return {"ciphertext": token, "last4": last4}


def decrypt_config_value(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and value.get("ciphertext"):
        fernet = _get_config_fernet()
        try:
            return fernet.decrypt(value.get("ciphertext").encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:  # pragma: no cover
            raise CloudflareConfigError("CONFIG_ENCRYPTION_KEY mismatch", code="config_key_mismatch") from exc
    return None


async def load_db_cloudflare_config(db) -> Optional[Dict[str, Any]]:
    account_doc = await db.system_settings.find_one({"key": CLOUDFLARE_ACCOUNT_KEY}, {"_id": 0})
    zone_doc = await db.system_settings.find_one({"key": CLOUDFLARE_ZONE_KEY}, {"_id": 0})
    if not account_doc or not zone_doc:
        return None
    return {"account": account_doc, "zone": zone_doc}


async def load_canary_status(db) -> Optional[Dict[str, Any]]:
    doc = await db.system_settings.find_one({"key": CLOUDFLARE_CANARY_KEY}, {"_id": 0})
    return doc


async def upsert_cloudflare_setting(db, key: str, value: Any, admin_user: dict) -> Dict[str, Any]:
    existing = await db.system_settings.find_one({"key": key}, {"_id": 0})
    now_iso = datetime.now(timezone.utc).isoformat()
    if existing:
        updates = {"value": value, "updated_at": now_iso}
        await db.system_settings.update_one({"id": existing.get("id")}, {"$set": updates})
        updated = await db.system_settings.find_one({"id": existing.get("id")}, {"_id": 0})
        return updated

    setting_id = str(uuid.uuid4())
    doc = {
        "id": setting_id,
        "key": key,
        "value": value,
        "country_code": None,
        "is_readonly": False,
        "description": "Cloudflare config",
        "created_at": now_iso,
        "updated_at": now_iso,
    }
    await db.system_settings.insert_one(doc)
    return doc


async def write_cloudflare_audit(db, admin_user: dict, action: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    now_iso = datetime.now(timezone.utc).isoformat()
    audit_doc = {
        "id": str(uuid.uuid4()),
        "created_at": now_iso,
        "event_type": "CLOUDFLARE_CONFIG",
        "action": action,
        "admin_user_id": admin_user.get("id"),
        "user_id": admin_user.get("id"),
        "user_email": admin_user.get("email"),
        "role": admin_user.get("role"),
        "resource_type": "cloudflare_config",
        "resource_id": admin_user.get("id"),
        "metadata": metadata or {},
        "applied": True,
    }
    await db.audit_logs.insert_one(audit_doc)


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


async def resolve_cloudflare_config(db) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    env_account, env_zone = resolve_env_fallback()
    if env_account and env_zone:
        return env_account, env_zone, resolve_env_source(env_account, env_zone)

    db_docs = await load_db_cloudflare_config(db)
    if db_docs:
        account_value = decrypt_config_value(db_docs["account"].get("value"))
        zone_value = decrypt_config_value(db_docs["zone"].get("value"))
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


async def build_masked_config(db) -> CloudflareMaskedConfig:
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
        )

    db_docs = await load_db_cloudflare_config(db)
    if db_docs:
        account_last4 = None
        zone_last4 = None
        account_value = db_docs["account"].get("value") or {}
        zone_value = db_docs["zone"].get("value") or {}
        if isinstance(account_value, dict):
            account_last4 = account_value.get("last4")
        if isinstance(zone_value, dict):
            zone_last4 = zone_value.get("last4")
        return CloudflareMaskedConfig(
            account_masked=_mask_last4(account_last4),
            zone_masked=_mask_last4(zone_last4),
            account_last4=account_last4,
            zone_last4=zone_last4,
            source="db",
            present=bool(account_last4 and zone_last4),
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
        )

    return CloudflareMaskedConfig(
        account_masked=None,
        zone_masked=None,
        account_last4=None,
        zone_last4=None,
        source=None,
        present=False,
    )
