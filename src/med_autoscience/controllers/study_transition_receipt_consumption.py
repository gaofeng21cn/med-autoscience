from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def execution_receipt_consumption(status: Mapping[str, Any]) -> dict[str, Any]:
    supersession = _mapping(status.get("blocked_turn_closeout_supersession"))
    if not supersession:
        return {}
    source_ref = relative_study_artifact_ref(_text(supersession.get("source_path")))
    return {
        "status": "superseded_stale_closeout",
        "receipt_kind": "default_executor_execution",
        "superseded_run_id": _text(supersession.get("superseded_run_id")),
        "execution_id": _text(supersession.get("execution_id")),
        "action_type": _text(supersession.get("action_type")),
        "source_ref": source_ref or _text(supersession.get("source_surface")),
        "next_action": "honor_newer_owner_execution_receipt",
    }


def bundle_stage_completion_receipt_consumption(
    *,
    study_root: Path,
    publication_eval: Mapping[str, Any],
    work_unit: Mapping[str, Any],
    controller_decision: Mapping[str, Any],
) -> dict[str, Any]:
    work_unit_id = _text(work_unit.get("unit_id"))
    if not work_unit_id:
        return {}
    work_unit_fingerprint = _text(controller_decision.get("work_unit_fingerprint")) or _text(
        work_unit.get("fingerprint")
    )
    quest_root = _publication_eval_quest_root(publication_eval)
    if quest_root is None:
        return {}
    closeout_root = quest_root / "artifacts" / "runtime" / "turn_closeouts"
    if not closeout_root.exists():
        return {}
    for closeout_path in sorted(closeout_root.glob("*.json")):
        closeout = _read_json_object(closeout_path)
        if closeout is None or closeout.get("status") != "completed":
            continue
        if closeout.get("meaningful_artifact_delta") is not True:
            continue
        for artifact_ref in closeout.get("artifact_refs") or []:
            artifact_ref_text = _text(artifact_ref)
            artifact_path = _resolve_runtime_artifact_ref(quest_root, artifact_ref_text)
            package_closure = _read_json_object(artifact_path) if artifact_path is not None else None
            if not _package_closure_matches_work_unit(
                package_closure,
                study_root=study_root,
                work_unit_id=work_unit_id,
                work_unit_fingerprint=work_unit_fingerprint,
            ):
                continue
            return {
                "status": "consumed",
                "receipt_kind": "runtime_turn_closeout_package_closure",
                "consumed_work_unit_id": work_unit_id,
                "consumed_work_unit_fingerprint": work_unit_fingerprint,
                "completion_ref": _quest_relative_ref(quest_root=quest_root, path=closeout_path),
                "artifact_ref": artifact_ref_text,
                "next_action": "do_not_redrive_completed_work_unit",
            }
    return {}


def relative_study_artifact_ref(path_text: str) -> str:
    if not path_text:
        return ""
    path = Path(path_text).expanduser()
    parts = path.parts
    if "artifacts" not in parts:
        return path.name
    return str(Path(*parts[parts.index("artifacts") :]))


def _publication_eval_quest_root(publication_eval: Mapping[str, Any]) -> Path | None:
    runtime_context_refs = _mapping(publication_eval.get("runtime_context_refs"))
    runtime_escalation_ref = _text(runtime_context_refs.get("runtime_escalation_ref"))
    if not runtime_escalation_ref:
        return None
    path = Path(runtime_escalation_ref).expanduser()
    parts = path.parts
    if "artifacts" not in parts:
        return None
    artifacts_index = parts.index("artifacts")
    if artifacts_index <= 0:
        return None
    return Path(*parts[:artifacts_index]).resolve()


def _resolve_runtime_artifact_ref(quest_root: Path, artifact_ref: str) -> Path | None:
    if not artifact_ref:
        return None
    path = Path(artifact_ref).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (quest_root / path).resolve()


def _package_closure_matches_work_unit(
    payload: Mapping[str, Any] | None,
    *,
    study_root: Path,
    work_unit_id: str,
    work_unit_fingerprint: str,
) -> bool:
    if payload is None:
        return False
    if _text(payload.get("artifact_kind")) != work_unit_id:
        return False
    work_unit = _mapping(payload.get("work_unit"))
    if _text(work_unit.get("unit_id")) != work_unit_id:
        return False
    if work_unit_fingerprint and _text(work_unit.get("fingerprint")) != work_unit_fingerprint:
        return False
    authority_closure = _mapping(payload.get("authority_closure"))
    if _text(authority_closure.get("status")) != "closed_for_bundle_stage":
        return False
    if _text(authority_closure.get("publication_gate_status")) != "clear":
        return False
    if authority_closure.get("publication_gate_allow_write") is not True:
        return False
    if list(authority_closure.get("publication_gate_blockers") or []):
        return False
    submission_authority = _mapping(payload.get("submission_minimal_authority"))
    if _text(submission_authority.get("status")) != "current":
        return False
    human_facing_delivery = _mapping(payload.get("human_facing_delivery"))
    current_package_zip = _text(human_facing_delivery.get("current_package_zip"))
    if not current_package_zip:
        return False
    package_path = Path(current_package_zip).expanduser()
    if not package_path.is_absolute():
        package_path = study_root / package_path
    try:
        package_path.resolve().relative_to(study_root.resolve())
    except ValueError:
        return False
    return _text(human_facing_delivery.get("status")) == "current"


def _quest_relative_ref(*, quest_root: Path, path: Path) -> str:
    resolved_path = path.expanduser().resolve()
    try:
        return str(resolved_path.relative_to(quest_root.expanduser().resolve()))
    except ValueError:
        return str(resolved_path)


def _read_json_object(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    return dict(payload)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "bundle_stage_completion_receipt_consumption",
    "execution_receipt_consumption",
    "relative_study_artifact_ref",
]
