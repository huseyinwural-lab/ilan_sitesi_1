import argparse
import json
import os
import urllib.request
import urllib.error


def _request_json(url, payload, token=None):
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc


def _resolve_token(base_url):
    token = os.environ.get("ADMIN_TOKEN")
    if token:
        return token

    email = os.environ.get("ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD")
    if not email or not password:
        raise RuntimeError("ADMIN_TOKEN or ADMIN_EMAIL/ADMIN_PASSWORD must be set")

    resp = _request_json(
        f"{base_url}/api/auth/login",
        {"email": email, "password": password},
    )
    access_token = resp.get("access_token")
    if not access_token:
        raise RuntimeError("Login failed: access_token not found")
    return access_token


def main():
    parser = argparse.ArgumentParser(description="Vehicle import v1 (dry-run/apply)")
    parser.add_argument("--file", required=True, help="Path to JSON payload")
    parser.add_argument("--mode", choices=["dry-run", "apply"], default="dry-run")
    parser.add_argument("--base-url", default=os.environ.get("BACKEND_URL", "http://localhost:8001"))
    args = parser.parse_args()

    with open(args.file, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    token = _resolve_token(args.base_url)
    endpoint = "/api/admin/vehicle-import/dry-run" if args.mode == "dry-run" else "/api/admin/vehicle-import/apply"
    result = _request_json(f"{args.base_url}{endpoint}", payload, token=token)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
