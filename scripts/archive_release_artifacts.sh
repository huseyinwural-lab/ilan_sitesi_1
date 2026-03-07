#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RELEASE_VERSION="${RELEASE_VERSION:-$(date +%F)_release}"
RELEASE_DATE="${RELEASE_DATE:-$(date +%F)}"
VALIDATED_LOCALES="${VALIDATED_LOCALES:-TR,DE,FR}"
PRESET_BATCH_SIZE="${PRESET_BATCH_SIZE:-100}"
VALIDATED_BY="${VALIDATED_BY:-${GITHUB_ACTOR:-system}}"

SOURCE_PUBLISH_REPORT="${SOURCE_PUBLISH_REPORT:-${ROOT_DIR}/publish_validation_report.md}"
SOURCE_PRESET_REPORT="${SOURCE_PRESET_REPORT:-${ROOT_DIR}/preset_stress_test_report.md}"

TARGET_DIR="${ROOT_DIR}/release-artifacts/${RELEASE_VERSION}"
mkdir -p "${TARGET_DIR}"

if [[ -f "${SOURCE_PUBLISH_REPORT}" ]]; then
  cp "${SOURCE_PUBLISH_REPORT}" "${TARGET_DIR}/publish_validation_report.md"
fi

if [[ -f "${SOURCE_PRESET_REPORT}" ]]; then
  cp "${SOURCE_PRESET_REPORT}" "${TARGET_DIR}/preset_stress_test_report.md"
fi

python3 - <<PY
import json
from pathlib import Path

target = Path(${TARGET_DIR@Q}) / "release_meta.json"
payload = {
    "release_version": ${RELEASE_VERSION@Q},
    "release_date": ${RELEASE_DATE@Q},
    "validated_locales": [item.strip() for item in ${VALIDATED_LOCALES@Q}.split(",") if item.strip()],
    "preset_batch_size": int(${PRESET_BATCH_SIZE@Q}),
    "validated_by": ${VALIDATED_BY@Q},
}
target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(str(target))
PY

echo "release artifact archive ready: ${TARGET_DIR}"
