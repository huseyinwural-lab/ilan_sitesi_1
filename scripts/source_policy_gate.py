#!/usr/bin/env python3
import os
from pathlib import Path
import subprocess
import sys


TESTS = [
    "/app/backend/tests/test_iteration_169_home_source_policy.py",
    "/app/backend/tests/test_iteration_170_source_policy_gate.py",
]


def main() -> int:
    command = ["pytest", "-q", *TESTS]

    env = dict(os.environ)
    if not env.get("REACT_APP_BACKEND_URL"):
        frontend_env = Path("/app/frontend/.env")
        if frontend_env.exists():
            for line in frontend_env.read_text(encoding="utf-8").splitlines():
                if line.startswith("REACT_APP_BACKEND_URL="):
                    env["REACT_APP_BACKEND_URL"] = line.split("=", 1)[1].strip()
                    break

    result = subprocess.run(command, check=False, env=env)
    return int(result.returncode)


if __name__ == "__main__":
    sys.exit(main())
