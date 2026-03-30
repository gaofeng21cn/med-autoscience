from __future__ import annotations

from pathlib import Path
from typing import Any


def _normalized_string(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _normalized_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    for item in value:
        text = _normalized_string(item)
        if text:
            normalized.append(text)
    return normalized


def _resolve_relative_path(*, study_root: Path, raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = (study_root / candidate).resolve()
    return candidate


def evaluate_runtime_reentry(
    *,
    study_root: Path,
    study_payload: dict[str, Any],
    execution: dict[str, Any],
) -> dict[str, Any]:
    raw_gate = execution.get("runtime_reentry_gate")
    gate = dict(raw_gate) if isinstance(raw_gate, dict) else {}
    enabled = gate.get("enabled") is True
    required_paths = _normalized_string_list(gate.get("required_paths"))
    execution_root = _normalized_string(gate.get("execution_root"))
    first_runtime_unit = _normalized_string(gate.get("first_runtime_unit"))
    blockers: list[str] = []
    advisories: list[str] = []

    if not enabled:
        return {
            "status": "not_configured",
            "study_id": str(study_payload.get("study_id") or study_root.name).strip() or study_root.name,
            "study_root": str(study_root),
            "allow_runtime_entry": True,
            "blockers": [],
            "advisories": [],
            "required_paths": required_paths,
            "execution_root": execution_root,
            "first_runtime_unit": first_runtime_unit,
        }

    execution_root_path: Path | None = None
    if not execution_root:
        blockers.append("execution_root_missing")
    else:
        execution_root_path = _resolve_relative_path(study_root=study_root, raw_path=execution_root)
        if not execution_root_path.exists():
            blockers.append(f"missing_execution_root:{execution_root}")

    if not first_runtime_unit:
        blockers.append("first_runtime_unit_missing")
    elif execution_root_path is not None:
        first_unit_path = execution_root_path / first_runtime_unit
        if not first_unit_path.exists():
            blockers.append(f"missing_first_runtime_unit:{first_runtime_unit}")

    for relative_path in required_paths:
        resolved = _resolve_relative_path(study_root=study_root, raw_path=relative_path)
        if not resolved.exists():
            blockers.append(f"missing_required_path:{relative_path}")

    advisories.extend(
        [
            f"execution_root:{execution_root or 'unset'}",
            f"first_runtime_unit:{first_runtime_unit or 'unset'}",
        ]
    )

    return {
        "status": "ready" if not blockers else "blocked",
        "study_id": str(study_payload.get("study_id") or study_root.name).strip() or study_root.name,
        "study_root": str(study_root),
        "allow_runtime_entry": not blockers,
        "blockers": blockers,
        "advisories": advisories,
        "required_paths": required_paths,
        "execution_root": execution_root,
        "first_runtime_unit": first_runtime_unit,
    }
