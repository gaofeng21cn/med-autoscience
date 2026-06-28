from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


STABLE_QUALITY_REPAIR_BATCH_RELATIVE_PATH = Path("artifacts/controller/quality_repair_batch/latest.json")
EVAL_HYGIENE_QUALITY_SUMMARY_RELATIVE_PATH = Path("artifacts/eval_hygiene/evaluation_summary/latest.json")
LEGACY_QUALITY_SUMMARY_RELATIVE_PATH = Path("artifacts/evaluation_summary/latest.json")


def stable_quality_repair_batch_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / STABLE_QUALITY_REPAIR_BATCH_RELATIVE_PATH


def read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return {}
    return payload


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def quality_summary_path(*, study_root: Path) -> Path:
    resolved_study_root = Path(study_root).expanduser().resolve()
    canonical_path = resolved_study_root / EVAL_HYGIENE_QUALITY_SUMMARY_RELATIVE_PATH
    if canonical_path.exists():
        return canonical_path
    return resolved_study_root / LEGACY_QUALITY_SUMMARY_RELATIVE_PATH


def read_quality_summary(*, study_root: Path) -> dict[str, Any]:
    return read_json_object(quality_summary_path(study_root=study_root))
