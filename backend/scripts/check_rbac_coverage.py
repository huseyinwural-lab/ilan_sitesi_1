import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "server.py"
MAP_PATH = ROOT.parent / "docs" / "RBAC_ENDPOINT_MAP.md"

ROUTE_PATTERN = re.compile(r"@api_router\.(get|post|put|patch|delete)\(\"([^\"]+)\"")


def load_routes() -> set[tuple[str, str]]:
    content = SERVER_PATH.read_text(encoding="utf-8")
    routes = set()
    for method, path in ROUTE_PATTERN.findall(content):
        if path.startswith("/admin") or path.startswith("/v1/admin"):
            routes.add((method.upper(), f"/api{path}"))
    return routes


def load_map() -> set[tuple[str, str]]:
    rows = set()
    for raw in MAP_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        if "Method" in line or "---" in line:
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 2:
            continue
        method, path = parts[0], parts[1]
        if method and path:
            rows.add((method.upper(), path))
    return rows


def main() -> int:
    if not SERVER_PATH.exists():
        print(f"ERROR: server.py not found at {SERVER_PATH}")
        return 2
    if not MAP_PATH.exists():
        print(f"ERROR: RBAC_ENDPOINT_MAP.md not found at {MAP_PATH}")
        return 2

    routes = load_routes()
    mapped = load_map()

    missing = sorted(routes - mapped)
    extra = sorted(mapped - routes)

    if missing:
        print("RBAC COVERAGE FAIL: endpoints missing from RBAC_ENDPOINT_MAP")
        for method, path in missing:
            print(f"MISSING: {method} {path}")
        return 1

    print("RBAC COVERAGE PASS: all admin endpoints mapped")
    if extra:
        print("NOTE: entries in map without matching route (cleanup optional)")
        for method, path in extra[:10]:
            print(f"EXTRA: {method} {path}")
        if len(extra) > 10:
            print(f"... {len(extra) - 10} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
