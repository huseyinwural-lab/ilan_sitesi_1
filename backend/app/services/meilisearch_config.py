import os
import base64
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict
from urllib.parse import quote

import httpx
from cryptography.fernet import Fernet, InvalidToken


class MeiliConfigError(RuntimeError):
    def __init__(self, message: str, code: str = "meili_config_error") -> None:
        super().__init__(message)
        self.code = code


def _get_config_fernet() -> Fernet:
    key = os.environ.get("CONFIG_ENCRYPTION_KEY")
    if not key:
        raise MeiliConfigError("CONFIG_ENCRYPTION_KEY missing", code="config_key_missing")
    try:
        return Fernet(key)
    except Exception:
        try:
            derived = base64.urlsafe_b64encode(hashlib.sha256(key.encode("utf-8")).digest())
            return Fernet(derived)
        except Exception as exc:
            raise MeiliConfigError("CONFIG_ENCRYPTION_KEY invalid", code="config_key_invalid") from exc


def encrypt_meili_master_key(master_key: str) -> str:
    fernet = _get_config_fernet()
    return fernet.encrypt(master_key.encode("utf-8")).decode("utf-8")


def decrypt_meili_master_key(ciphertext: str) -> str:
    fernet = _get_config_fernet()
    try:
        return fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise MeiliConfigError("CONFIG_ENCRYPTION_KEY mismatch", code="config_key_mismatch") from exc


def normalize_meili_url(raw_url: str) -> str:
    url = (raw_url or "").strip()
    if not url:
        raise MeiliConfigError("meili_url required", code="validation_failed")
    if not (url.startswith("http://") or url.startswith("https://")):
        raise MeiliConfigError("meili_url must start with http:// or https://", code="validation_failed")
    return url.rstrip("/")


def _result_payload(ok: bool, reason_code: str, message: str, status_code: int | None = None) -> Dict[str, Any]:
    return {
        "status": "PASS" if ok else "FAIL",
        "ok": ok,
        "reason_code": reason_code,
        "message": message,
        "http_status": status_code,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


def _reason_from_status(status_code: int) -> str:
    if status_code in (401, 403):
        return "unauthorized"
    if status_code == 404:
        return "not_found"
    if 500 <= status_code <= 599:
        return "upstream_server_error"
    return "api_error"


async def test_and_prepare_meili_index(meili_url: str, master_key: str, index_name: str) -> Dict[str, Any]:
    url = normalize_meili_url(meili_url)
    idx = (index_name or "listings_index").strip() or "listings_index"
    headers = {
        "Authorization": f"Bearer {master_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(base_url=url, timeout=10.0) as client:
            health = await client.get("/health", headers=headers)
            if health.status_code != 200:
                reason = _reason_from_status(health.status_code)
                return _result_payload(False, reason, "Meilisearch health failed", health.status_code)

            index_path = f"/indexes/{quote(idx, safe='')}"
            index_check = await client.get(index_path, headers=headers)
            if index_check.status_code == 404:
                create_resp = await client.post(
                    "/indexes",
                    headers=headers,
                    json={"uid": idx, "primaryKey": "listing_id"},
                )
                if create_resp.status_code not in (200, 201, 202):
                    reason = _reason_from_status(create_resp.status_code)
                    return _result_payload(False, reason, "Index create failed", create_resp.status_code)
            elif index_check.status_code != 200:
                reason = _reason_from_status(index_check.status_code)
                return _result_payload(False, reason, "Index check failed", index_check.status_code)

            settings_payload = {
                "filterableAttributes": [
                    "category_path_ids",
                    "make_id",
                    "model_id",
                    "trim_id",
                    "city_id",
                    "attribute_*",
                    "price",
                    "premium_score",
                ],
                "sortableAttributes": ["published_at", "premium_score", "price"],
                "rankingRules": [
                    "words",
                    "typo",
                    "proximity",
                    "attribute",
                    "sort",
                    "exactness",
                    "desc(premium_score)",
                    "desc(published_at)",
                ],
            }
            settings_resp = await client.patch(f"{index_path}/settings", headers=headers, json=settings_payload)
            if settings_resp.status_code not in (200, 202):
                reason = _reason_from_status(settings_resp.status_code)
                return _result_payload(False, reason, "Index settings update failed", settings_resp.status_code)

            return _result_payload(True, "ok", "Meilisearch connection and index check passed", 200)
    except httpx.ConnectError:
        return _result_payload(False, "connection_error", "Unable to connect to Meilisearch", None)
    except httpx.TimeoutException:
        return _result_payload(False, "timeout", "Meilisearch request timed out", None)
    except Exception:
        return _result_payload(False, "runtime_error", "Unexpected Meilisearch runtime error", None)
