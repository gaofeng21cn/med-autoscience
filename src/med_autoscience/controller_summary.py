from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.study_charter import read_study_charter, resolve_study_charter_ref

__all__ = [
    "STABLE_CONTROLLER_SUMMARY_RELATIVE_PATH",
    "materialize_controller_summary",
    "read_controller_summary",
    "resolve_controller_summary_ref",
    "stable_controller_summary_path",
]


STABLE_CONTROLLER_SUMMARY_RELATIVE_PATH = Path("artifacts/controller/controller_summary.json")


def stable_controller_summary_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / STABLE_CONTROLLER_SUMMARY_RELATIVE_PATH).resolve()


def resolve_controller_summary_ref(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> Path:
    stable_path = stable_controller_summary_path(study_root=study_root)
    if ref is None:
        return stable_path
    candidate = Path(ref).expanduser()
    if candidate.is_absolute():
        candidate = candidate.resolve()
    else:
        candidate = (Path(study_root).expanduser().resolve() / candidate).resolve()
    if candidate != stable_path:
        raise ValueError("controller summary reader only accepts the stable controller artifact")
    return stable_path


def _required_text(label: str, field_name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} {field_name} must be non-empty")
    return value.strip()


def _required_mapping(label: str, field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} {field_name} must be a JSON object")
    return dict(value)


def _normalized_study_charter_ref(*, study_root: Path, value: object) -> dict[str, str]:
    payload = _required_mapping("controller summary", "study_charter_ref", value)
    charter_id = _required_text("controller summary study_charter_ref", "charter_id", payload.get("charter_id"))
    artifact_path = str(
        resolve_study_charter_ref(study_root=study_root, ref=payload.get("artifact_path"))
    )
    charter_payload = read_study_charter(study_root=study_root, ref=artifact_path)
    actual_charter_id = _required_text(
        "study charter",
        "charter_id",
        charter_payload.get("charter_id"),
    )
    if charter_id != actual_charter_id:
        raise ValueError(
            f"controller summary study_charter_ref charter_id mismatch: {charter_id} != {actual_charter_id}"
        )
    return {
        "charter_id": charter_id,
        "artifact_path": artifact_path,
    }


def _normalized_summary(*, study_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise TypeError("controller summary payload must be a mapping")
    schema_version = payload.get("schema_version", 1)
    if schema_version != 1:
        raise ValueError("controller summary schema_version must be 1")
    return {
        "schema_version": 1,
        "summary_id": _required_text("controller summary", "summary_id", payload.get("summary_id")),
        "study_id": _required_text("controller summary", "study_id", payload.get("study_id")),
        "study_charter_ref": _normalized_study_charter_ref(
            study_root=study_root,
            value=payload.get("study_charter_ref"),
        ),
        "controller_policy": _required_mapping(
            "controller summary",
            "controller_policy",
            payload.get("controller_policy"),
        ),
        "route_trigger_authority": _required_mapping(
            "controller summary",
            "route_trigger_authority",
            payload.get("route_trigger_authority"),
        ),
    }


def read_controller_summary(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> dict[str, Any]:
    summary_path = resolve_controller_summary_ref(study_root=study_root, ref=ref)
    payload = json.loads(summary_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"controller summary payload must be a JSON object: {summary_path}")
    return _normalized_summary(study_root=study_root, payload=payload)


def materialize_controller_summary(
    *,
    study_root: Path,
    study_id: str,
    study_charter_ref: dict[str, Any],
    controller_policy: dict[str, Any],
    route_trigger_authority: dict[str, Any],
) -> dict[str, str]:
    normalized_study_id = _required_text("controller summary", "study_id", study_id)
    normalized_charter_ref = _normalized_study_charter_ref(
        study_root=study_root,
        value=study_charter_ref,
    )
    normalized_payload = _normalized_summary(
        study_root=study_root,
        payload={
            "schema_version": 1,
            "summary_id": f"controller-summary::{normalized_study_id}::v1",
            "study_id": normalized_study_id,
            "study_charter_ref": normalized_charter_ref,
            "controller_policy": dict(controller_policy),
            "route_trigger_authority": dict(route_trigger_authority),
        },
    )
    summary_path = stable_controller_summary_path(study_root=study_root)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(normalized_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "summary_id": str(normalized_payload["summary_id"]),
        "artifact_path": str(summary_path),
    }
