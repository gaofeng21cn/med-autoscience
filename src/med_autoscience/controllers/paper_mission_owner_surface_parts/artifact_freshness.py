from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


ACTION_TYPE = "current_package_freshness_required"
DISPLAY_MATERIALIZATION_ACTION_TYPE = "artifact_display_surface_materialization_required"
OWNER = "artifact_os"
REQUIRED_OUTPUT_SURFACE = "artifacts/controller/gate_clearing_batch/latest.json"
DISPLAY_REGISTRY_SURFACE = "paper/display_registry.json"
CURRENT_PACKAGE_FRESHNESS_SURFACE = "artifacts/controller/current_package_freshness/latest.json"
DEFAULT_EXECUTOR_EXECUTION_SURFACE = "artifacts/supervision/consumer/default_executor_execution/latest.json"
AI_REVIEWER_FRESHNESS_MISMATCH_ERROR = "current_package_freshness_source_eval_id_mismatch"


def action_payload(
    *,
    reason: str | None = None,
    controller_route: Mapping[str, Any] | None = None,
    source_blocked_reason: str | None = None,
) -> dict[str, Any]:
    payload = {
        "action_type": ACTION_TYPE,
        "authority": "observability_only",
        "owner": OWNER,
        "request_owner": OWNER,
        "recommended_owner": OWNER,
        "reason": reason or ACTION_TYPE,
        "summary": "Controller terminal requires current-package freshness proof through the gate-clearing batch.",
        "required_output_surface": REQUIRED_OUTPUT_SURFACE,
        "controller_action_type": "run_gate_clearing_batch",
        "paper_package_mutation_allowed": False,
    }
    if controller_route:
        payload["controller_route"] = dict(controller_route)
    if source_blocked_reason:
        payload["source_blocked_reason"] = source_blocked_reason
    return payload


def blocked_action_from_gate_clearing(*, study_root: Path, publication_eval_payload: Mapping[str, Any]) -> dict[str, Any] | None:
    record = _read_gate_clearing_record(study_root=study_root)
    if record is None:
        return None
    if not _same_publication_work_unit(record=record, publication_eval_payload=publication_eval_payload):
        return None
    failed_units = _failed_units(record)
    if not failed_units:
        return None
    blocking_refs = _blocking_artifact_refs(record=record, failed_units=failed_units)
    concrete = _display_materialization_blocker(failed_units=failed_units, blocking_refs=blocking_refs)
    if concrete is None:
        return None
    artifact_role = _text(concrete.get("artifact_role"))
    required_surface = DISPLAY_REGISTRY_SURFACE if artifact_role == "display_registry" else _text(concrete.get("artifact_path"))
    return {
        "action_type": DISPLAY_MATERIALIZATION_ACTION_TYPE,
        "authority": "observability_only",
        "owner": OWNER,
        "request_owner": OWNER,
        "recommended_owner": OWNER,
        "reason": "display_surface_materialization_failed",
        "summary": "Gate-clearing reached display surface materialization and failed on a concrete display artifact.",
        "required_output_surface": required_surface or DISPLAY_REGISTRY_SURFACE,
        "controller_action_type": "repair_display_surface_materialization",
        "paper_package_mutation_allowed": False,
        "failed_units": failed_units,
        "blocking_artifact_refs": blocking_refs,
        "gate_clearing_batch_path": str(_gate_clearing_path(study_root=study_root)),
    }


def blocked_action_from_ai_reviewer_freshness_mismatch(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    eval_id = _text(publication_eval_payload.get("eval_id"))
    if eval_id is None:
        return None
    execution = _latest_ai_reviewer_freshness_mismatch_execution(study_root=study_root)
    if execution is None:
        return None
    freshness = _read_json_object(Path(study_root).expanduser().resolve() / CURRENT_PACKAGE_FRESHNESS_SURFACE)
    freshness_source_eval_id = _text(_mapping(freshness).get("source_eval_id"))
    if freshness_source_eval_id == eval_id:
        return None
    action = action_payload(
        reason=ACTION_TYPE,
        source_blocked_reason=_text(execution.get("blocked_reason")) or "ai_reviewer_workflow_failed",
    )
    action["summary"] = (
        "AI reviewer workflow is blocked because the human-facing current package freshness proof "
        "belongs to an older publication eval; refresh the package projection before retrying AI reviewer."
    )
    action["source_error"] = AI_REVIEWER_FRESHNESS_MISMATCH_ERROR
    action["source_execution_path"] = str(
        Path(study_root).expanduser().resolve() / DEFAULT_EXECUTOR_EXECUTION_SURFACE
    )
    action["current_package_freshness"] = {
        "status": _text(_mapping(freshness).get("status")),
        "source_eval_id": freshness_source_eval_id,
        "expected_source_eval_id": eval_id,
        "proof_path": str(Path(study_root).expanduser().resolve() / CURRENT_PACKAGE_FRESHNESS_SURFACE),
    }
    return action


def artifact_delta(progress: Mapping[str, Any]) -> dict[str, Any]:
    progress_freshness = _mapping(progress.get("progress_freshness"))
    delta_freshness = _mapping(progress_freshness.get("meaningful_artifact_delta_freshness"))
    if _text(delta_freshness.get("status")) in {"fresh", "stale"}:
        last_delta = _text(delta_freshness.get("latest_progress_at"))
        if last_delta is not None:
            return {
                "status": _text(delta_freshness.get("status")) or "observed",
                "latest_meaningful_delta_at": last_delta,
                "source": _text(delta_freshness.get("latest_progress_source")) or "mds_artifact_delta",
            }
    autonomy_slo = _mapping(progress.get("autonomy_slo"))
    markers = _mapping(autonomy_slo.get("mds_progress_markers"))
    last_delta = _text(markers.get("meaningful_artifact_delta_at"))
    if last_delta is not None:
        return {
            "status": "observed",
            "latest_meaningful_delta_at": last_delta,
            "source": "mds_artifact_delta",
        }
    return {"status": "not_observed", "summary": "No meaningful artifact delta observed by supervisor scan."}


def meaningful_artifact_delta_observed(progress: Mapping[str, Any]) -> bool:
    return _text(artifact_delta(progress).get("status")) == "fresh"


def _gate_clearing_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / REQUIRED_OUTPUT_SURFACE


def _read_gate_clearing_record(*, study_root: Path) -> dict[str, Any] | None:
    return _read_json_object(_gate_clearing_path(study_root=study_root))


def _latest_ai_reviewer_freshness_mismatch_execution(*, study_root: Path) -> dict[str, Any] | None:
    record = _read_json_object(Path(study_root).expanduser().resolve() / DEFAULT_EXECUTOR_EXECUTION_SURFACE)
    for execution in reversed(record.get("executions") or []):
        if not isinstance(execution, Mapping):
            continue
        if _text(execution.get("action_type")) != "return_to_ai_reviewer_workflow":
            continue
        if _text(execution.get("execution_status")) != "blocked":
            continue
        if _text(execution.get("blocked_reason")) != "ai_reviewer_workflow_failed":
            continue
        if _text(execution.get("error")) != AI_REVIEWER_FRESHNESS_MISMATCH_ERROR:
            continue
        return dict(execution)
    return None


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _same_publication_work_unit(*, record: Mapping[str, Any], publication_eval_payload: Mapping[str, Any]) -> bool:
    eval_id = _text(publication_eval_payload.get("eval_id"))
    source_eval_id = _text(record.get("source_eval_id"))
    if eval_id is not None and source_eval_id == eval_id:
        return True
    record_fingerprint = (
        _text(record.get("source_work_unit_fingerprint"))
        or _text(record.get("work_unit_fingerprint"))
        or _text(_mapping(record.get("work_unit_currentness")).get("current_work_unit_fingerprint"))
    )
    if record_fingerprint is None:
        return False
    return record_fingerprint in _publication_eval_work_unit_fingerprints(publication_eval_payload)


def _publication_eval_work_unit_fingerprints(publication_eval_payload: Mapping[str, Any]) -> set[str]:
    fingerprints: set[str] = set()
    for action in publication_eval_payload.get("recommended_actions") or []:
        if not isinstance(action, Mapping):
            continue
        if fingerprint := _text(action.get("work_unit_fingerprint")):
            fingerprints.add(fingerprint)
        next_work_unit = _mapping(action.get("next_work_unit"))
        if fingerprint := _text(next_work_unit.get("fingerprint")):
            fingerprints.add(fingerprint)
    return fingerprints


def _failed_units(record: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(item)
        for item in (record.get("unit_results") or [])
        if isinstance(item, Mapping)
        and _text(item.get("status"))
        in {
            "failed",
            "missing",
            "skipped_failed_dependency",
            "blocked_matching_failed_unit_fingerprint",
        }
    ]


def _blocking_artifact_refs(*, record: Mapping[str, Any], failed_units: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for source in (record.get("repair_blocking_artifact_refs"), *(item.get("blocking_artifact_refs") for item in failed_units)):
        if not isinstance(source, list):
            continue
        for item in source:
            if isinstance(item, Mapping):
                payload = dict(item)
                if payload not in refs:
                    refs.append(payload)
    return refs


def _display_materialization_blocker(
    *,
    failed_units: list[Mapping[str, Any]],
    blocking_refs: list[Mapping[str, Any]],
) -> dict[str, Any] | None:
    materialize_failed = any(
        _text(item.get("unit_id")) == "materialize_display_surface"
        and _text(item.get("status")) in {"failed", "blocked_matching_failed_unit_fingerprint"}
        for item in failed_units
    )
    if not materialize_failed:
        return None
    for ref in blocking_refs:
        if _text(ref.get("blocker")) == "display_surface_materialization_failed":
            return dict(ref)
    for item in failed_units:
        if _text(item.get("unit_id")) == "materialize_display_surface":
            return {
                "blocker": "display_surface_materialization_failed",
                "artifact_role": "display_registry",
                "failure_reason": _text(item.get("error")),
            }
    return None


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


__all__ = [
    "ACTION_TYPE",
    "AI_REVIEWER_FRESHNESS_MISMATCH_ERROR",
    "CURRENT_PACKAGE_FRESHNESS_SURFACE",
    "DEFAULT_EXECUTOR_EXECUTION_SURFACE",
    "DISPLAY_MATERIALIZATION_ACTION_TYPE",
    "OWNER",
    "REQUIRED_OUTPUT_SURFACE",
    "action_payload",
    "artifact_delta",
    "blocked_action_from_ai_reviewer_freshness_mismatch",
    "blocked_action_from_gate_clearing",
    "meaningful_artifact_delta_observed",
]
