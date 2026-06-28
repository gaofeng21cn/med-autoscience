from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any


def quality_repair_handoff_payload(source_ref: Path) -> dict[str, Any] | None:
    payload = _read_json_object(source_ref)
    if not payload:
        return None
    if _text(payload.get("status")) != "blocked":
        return None
    if _text(payload.get("blocked_reason")) != "unit_harmonized_rerun_required":
        return None
    if _text(payload.get("next_owner")) != "analysis_harmonization_owner":
        return None
    if _text(payload.get("next_work_unit")) != "unit_harmonized_external_validation_rerun":
        return None
    if payload.get("quality_gate_relaxation_allowed") is not False:
        return None
    if payload.get("current_package_write_allowed") is not False:
        return None
    return payload


def quality_repair_handoff_path(study_root: Path) -> Path:
    return (
        Path(study_root).expanduser().resolve()
        / "artifacts"
        / "controller"
        / "quality_repair_batch"
        / "latest.json"
    )


def handoff_supersedes_paths(*, source_ref: Path, consumer_paths: tuple[Path, ...]) -> bool:
    if quality_repair_handoff_payload(source_ref) is None:
        return False
    source_mtime = _path_mtime(source_ref)
    if source_mtime is None:
        return False
    consumer_mtimes = [mtime for path in consumer_paths if (mtime := _path_mtime(path)) is not None]
    return bool(consumer_mtimes) and source_mtime > max(consumer_mtimes)


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    try:
        import json

        decoded = json.loads(payload)
    except json.JSONDecodeError:
        return {}
    return dict(decoded) if isinstance(decoded, Mapping) else {}


def _path_mtime(path: Path) -> float | None:
    try:
        return Path(path).expanduser().resolve().stat().st_mtime
    except OSError:
        return None


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "handoff_supersedes_paths",
    "quality_repair_handoff_path",
    "quality_repair_handoff_payload",
]
