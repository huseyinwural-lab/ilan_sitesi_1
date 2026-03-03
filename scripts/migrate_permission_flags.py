import json
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ENV = ROOT / "frontend" / ".env"
REPORT_PATH = ROOT / "test_reports" / "permission_flag_diff.json"


def _load_base_url() -> str:
    for raw_line in FRONTEND_ENV.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("REACT_APP_BACKEND_URL="):
            value = line.split("=", 1)[1].strip()
            if value:
                return value.rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL bulunamadı")


def _login(base_url: str, email: str, password: str) -> str:
    response = requests.post(
        f"{base_url}/api/auth/login",
        json={"email": email, "password": password},
        timeout=30,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Login failed: {response.status_code} {response.text}")
    token = response.json().get("access_token")
    if not token:
        raise RuntimeError("access_token missing")
    return token


def main() -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    base_url = _load_base_url()
    token = _login(base_url, "admin@platform.com", "Admin123!")
    headers = {"Authorization": f"Bearer {token}"}

    before = requests.get(f"{base_url}/api/admin/permissions/snapshot", headers=headers, timeout=60)
    before_payload = before.json() if before.status_code == 200 else {"status": before.status_code, "raw": before.text}

    migrate = requests.post(f"{base_url}/api/admin/permissions/migrate-from-roles", headers=headers, timeout=120)
    migrate_payload = migrate.json() if migrate.status_code == 200 else {"status": migrate.status_code, "raw": migrate.text}

    after = requests.get(f"{base_url}/api/admin/permissions/snapshot", headers=headers, timeout=60)
    after_payload = after.json() if after.status_code == 200 else {"status": after.status_code, "raw": after.text}

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "before_count": before_payload.get("count") if isinstance(before_payload, dict) else None,
        "after_count": after_payload.get("count") if isinstance(after_payload, dict) else None,
        "delta": (after_payload.get("count", 0) - before_payload.get("count", 0)) if isinstance(before_payload, dict) and isinstance(after_payload, dict) else None,
        "migration_response": migrate_payload,
    }

    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()