import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
REPORTS_DIR = ROOT / "test_reports"
PYTEST_DIR = REPORTS_DIR / "pytest"
RBAC_TEST_FILES = [
    BACKEND_DIR / "tests" / "test_p1_01_rbac_matrix.py",
    BACKEND_DIR / "tests" / "test_p1_1_permission_flags.py",
]
POLICY_DIFF_FILE = REPORTS_DIR / "rbac_policy_diff.json"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_dirs() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    PYTEST_DIR.mkdir(parents=True, exist_ok=True)


def run_pytest() -> dict[str, Any]:
    junit_file = PYTEST_DIR / "rbac_suite_results.xml"
    command = [
        sys.executable,
        "-m",
        "pytest",
        *[str(path) for path in RBAC_TEST_FILES],
        "-q",
        "--maxfail=1",
        f"--junitxml={junit_file}",
    ]
    result = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True)
    return {
        "command": " ".join(command),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "junit_xml": str(junit_file),
        "passed": result.returncode == 0,
    }


def build_policy_snapshot(demo_mode: bool) -> dict[str, Any]:
    sys.path.append(str(BACKEND_DIR))
    import server as backend_server  # type: ignore

    allowlist = backend_server.RBAC_ALLOWLIST or {}
    missing_routes = list(backend_server.RBAC_MISSING_POLICIES or [])

    routes = []
    for route in backend_server.app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None)
        if not path or not isinstance(path, str) or not path.startswith("/api"):
            continue
        route_methods = sorted([m for m in (methods or set()) if m not in {"HEAD", "OPTIONS"}])
        routes.append({"path": path, "methods": route_methods})

    routes.sort(key=lambda item: (item["path"], ",".join(item["methods"])))

    if demo_mode:
        missing_routes.append("/api/demo/synthetic-unprotected-route")

    return {
        "generated_at": utc_now().isoformat(),
        "rbac_allowlist": allowlist,
        "rbac_missing_policies": sorted(set(missing_routes)),
        "route_inventory": routes,
        "demo_mode": demo_mode,
    }


def snapshot_path(date_key: str) -> Path:
    return REPORTS_DIR / f"rbac_policy_snapshot_{date_key}.json"


def load_previous_snapshot(current_path: Path) -> dict[str, Any] | None:
    candidates = sorted(REPORTS_DIR.glob("rbac_policy_snapshot_*.json"))
    previous = [item for item in candidates if item.resolve() != current_path.resolve()]
    if not previous:
        return None
    return json.loads(previous[-1].read_text(encoding="utf-8"))


def build_policy_diff(current: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    current_allow = current.get("rbac_allowlist", {}) or {}
    current_missing = set(current.get("rbac_missing_policies", []) or [])

    if not previous:
        return {
            "generated_at": utc_now().isoformat(),
            "baseline_created": True,
            "added_allowlist_routes": sorted(current_allow.keys()),
            "removed_allowlist_routes": [],
            "changed_roles": [],
            "added_missing_routes": sorted(current_missing),
            "removed_missing_routes": [],
        }

    prev_allow = previous.get("rbac_allowlist", {}) or {}
    prev_missing = set(previous.get("rbac_missing_policies", []) or [])

    added_routes = sorted(set(current_allow.keys()) - set(prev_allow.keys()))
    removed_routes = sorted(set(prev_allow.keys()) - set(current_allow.keys()))

    changed_roles = []
    for key in sorted(set(current_allow.keys()) & set(prev_allow.keys())):
        cur_roles = sorted(current_allow.get(key) or [])
        old_roles = sorted(prev_allow.get(key) or [])
        if cur_roles != old_roles:
            changed_roles.append({
                "route": key,
                "before": old_roles,
                "after": cur_roles,
            })

    return {
        "generated_at": utc_now().isoformat(),
        "baseline_created": False,
        "added_allowlist_routes": added_routes,
        "removed_allowlist_routes": removed_routes,
        "changed_roles": changed_roles,
        "added_missing_routes": sorted(current_missing - prev_missing),
        "removed_missing_routes": sorted(prev_missing - current_missing),
    }


def report_path_for_mode(mode: str, date_key: str) -> Path:
    if mode == "nightly":
        return REPORTS_DIR / f"rbac_nightly_{date_key}.json"
    if mode == "demo":
        return REPORTS_DIR / f"rbac_nightly_{date_key}_demo_fail.json"
    return REPORTS_DIR / "rbac_check_latest.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="RBAC suite runner (check/nightly/demo)")
    parser.add_argument("--mode", choices=["check", "nightly", "demo"], default="check")
    args = parser.parse_args()

    ensure_dirs()

    date_key = utc_now().strftime("%Y%m%d")
    demo_mode = args.mode == "demo" or os.environ.get("RBAC_DRIFT_DEMO") == "1"

    pytest_result = run_pytest()
    current_snapshot = build_policy_snapshot(demo_mode=demo_mode)

    current_snapshot_path = snapshot_path(date_key)
    current_snapshot_path.write_text(json.dumps(current_snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

    previous_snapshot = load_previous_snapshot(current_snapshot_path)
    policy_diff = build_policy_diff(current_snapshot, previous_snapshot)
    POLICY_DIFF_FILE.write_text(json.dumps(policy_diff, ensure_ascii=False, indent=2), encoding="utf-8")

    fail_reasons: list[str] = []
    if not pytest_result["passed"]:
        fail_reasons.append("rbac_pytest_failed")

    missing_routes = current_snapshot.get("rbac_missing_policies", []) or []
    if missing_routes:
        fail_reasons.append("unbound_rbac_policy_routes_detected")

    if policy_diff.get("added_missing_routes"):
        fail_reasons.append("new_unbound_routes_detected_in_diff")

    status = "PASS" if not fail_reasons else "FAIL"

    report = {
        "generated_at": utc_now().isoformat(),
        "mode": args.mode,
        "status": status,
        "alarm_triggered": status == "FAIL",
        "demo_mode": demo_mode,
        "fail_reasons": fail_reasons,
        "pytest": {
            "passed": pytest_result["passed"],
            "returncode": pytest_result["returncode"],
            "command": pytest_result["command"],
            "junit_xml": pytest_result["junit_xml"],
        },
        "artifacts": {
            "policy_snapshot": str(current_snapshot_path),
            "policy_diff": str(POLICY_DIFF_FILE),
            "nightly_report": str(report_path_for_mode(args.mode, date_key)),
        },
        "rbac_summary": {
            "allowlist_route_count": len((current_snapshot.get("rbac_allowlist") or {}).keys()),
            "missing_policy_route_count": len(missing_routes),
            "added_missing_routes": policy_diff.get("added_missing_routes", []),
        },
        "ci_gate": {
            "merge_blocked": status == "FAIL",
            "policy_diff_gate_active": True,
            "nightly_gate_active": args.mode in {"nightly", "demo"},
        },
    }

    report_path = report_path_for_mode(args.mode, date_key)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "status": status,
        "mode": args.mode,
        "report_path": str(report_path),
        "policy_diff": str(POLICY_DIFF_FILE),
        "fail_reasons": fail_reasons,
    }, ensure_ascii=False, indent=2))

    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())