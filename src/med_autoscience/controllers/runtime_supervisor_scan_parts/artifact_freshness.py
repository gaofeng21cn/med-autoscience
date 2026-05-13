from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any


ACTION_TYPE = "current_package_freshness_required"
DISPLAY_MATERIALIZATION_ACTION_TYPE = "artifact_display_surface_materialization_required"
OWNER = "artifact_os"
REQUIRED_OUTPUT_SURFACE = "artifacts/controller/gate_clearing_batch/latest.json"
DISPLAY_REGISTRY_SURFACE = "paper/display_registry.json"


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


def route_required(runtime_platform_repair_apply: Mapping[str, Any] | None) -> bool:
    if runtime_platform_repair_apply is None:
        return False
    return (
        _text(runtime_platform_repair_apply.get("dispatch_status")) == "blocked"
        and _text(runtime_platform_repair_apply.get("reason")) == ACTION_TYPE
    )


def remove_runtime_platform_repair(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [action for action in actions if _text(action.get("action_type")) != "runtime_platform_repair"]


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
    try:
        import json

        payload = json.loads(_gate_clearing_path(study_root=study_root).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


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
    "DISPLAY_MATERIALIZATION_ACTION_TYPE",
    "OWNER",
    "REQUIRED_OUTPUT_SURFACE",
    "action_payload",
    "artifact_delta",
    "blocked_action_from_gate_clearing",
    "meaningful_artifact_delta_observed",
    "remove_runtime_platform_repair",
    "route_required",
]
