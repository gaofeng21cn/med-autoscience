from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
SURFACE = "real_workspace_soak_monitor"
READ_MODEL = "real_workspace_soak_monitor_read_model"
MONITOR_MODE = "continuous_read_only"
MONITOR_ROOT = Path("artifacts/medical_paper")

MATRIX_REF = MONITOR_ROOT / "real_study_soak_matrix_evidence.json"
READINESS_REF = MONITOR_ROOT / "medical_paper_readiness.json"
CANONICAL_READINESS_REF = MONITOR_ROOT / "readiness.json"
MONITOR_REF = MONITOR_ROOT / "real_workspace_soak_monitor.json"

SURFACE_KEY_TO_CONTRACT = {
    "literature_scout": "literature_contract",
    "archetype_analysis_contract": "statistical_contract",
    "real_study_soak_matrix_evidence": "external_validation_fixture",
}
SURFACE_KEY_TO_STAGE = {
    "literature_scout": "literature_scout",
    "literature_provider_runtime": "literature_scout",
    "study_line_selection": "line_selection",
    "route_decision_orchestrator": "route_back",
    "archetype_analysis_contract": "baseline",
    "statistical_discipline_operations": "primary_analysis",
    "bounded_analysis_candidate_board": "bounded_analysis",
    "stop_loss_memo": "stop_loss",
    "revision_rebuttal_loop": "revision_reopen",
    "authoring_runtime_authorization": "final_pre_submission_audit",
    "real_study_soak_matrix_evidence": "runtime_recovery",
    "real_workspace_soak_monitor": "finalize_rebuild",
}


def _authority_contract() -> dict[str, Any]:
    return {
        "authority": "observability_read_model_only",
        "can_mutate_runtime": False,
        "can_authorize_quality": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
    }


def _read_only_monitor_contract() -> dict[str, Any]:
    return {
        "mode": "read_only_monitor",
        "writes_runtime_owned_surfaces": False,
        "writable_surfaces": [SURFACE],
        "prohibited_runtime_owned_surfaces": [
            "study_runtime_status",
            "runtime_watch",
            "publication_eval/latest.json",
            "runtime_escalation_record.json",
            "controller_decisions/latest.json",
            "quality_authorization",
            "submission_authorization",
        ],
    }


def _read_json(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


def _text(value: object, default: str = "unknown") -> str:
    text = str(value or "").strip()
    return text or default


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> Sequence[object]:
    if isinstance(value, list | tuple):
        return value
    return ()


def _optional_bool(value: object) -> bool | None:
    if value is True:
        return True
    if value is False:
        return False
    return None


def _truthy_bool(value: object) -> bool:
    return value is True


def _catalog_entries(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    for key in ("studies", "study_catalog", "items"):
        entries = payload.get(key)
        if isinstance(entries, Mapping):
            return [
                {**entry, "study_id": entry.get("study_id") or str(study_id)}
                for study_id, entry in entries.items()
                if isinstance(entry, Mapping)
            ]
        if isinstance(entries, list | tuple):
            return [entry for entry in entries if isinstance(entry, Mapping)]
    if payload.get("study_id") or payload.get("study_root"):
        return [payload]
    return []


def _route_mapping(entry: Mapping[str, Any]) -> Mapping[str, Any]:
    route_decision = _mapping(entry.get("route_decision"))
    if route_decision:
        return route_decision
    return _mapping(entry.get("route"))


def _catalog_route_action(entry: Mapping[str, Any]) -> str:
    route = _route_mapping(entry)
    return _text(entry.get("route_action") or route.get("action"), "")


def _catalog_route_reason(entry: Mapping[str, Any]) -> str:
    route = _route_mapping(entry)
    return _text(
        entry.get("route_reason")
        or entry.get("route_decision_reason")
        or route.get("reason")
        or route.get("decision_reason"),
        "",
    )


def _catalog_readiness_status(entry: Mapping[str, Any]) -> str:
    readiness = _mapping(entry.get("readiness"))
    return _text(
        entry.get("readiness_status")
        or entry.get("current_readiness_status")
        or readiness.get("overall_status"),
        "",
    )


def _catalog_previous_readiness_status(entry: Mapping[str, Any]) -> str:
    readiness = _mapping(entry.get("readiness"))
    return _text(
        entry.get("previous_readiness_status")
        or entry.get("last_readiness_status")
        or readiness.get("previous_overall_status"),
        "",
    )


def _catalog_blocked_reason(entry: Mapping[str, Any]) -> str:
    readiness = _mapping(entry.get("readiness"))
    reasons = entry.get("blocked_reasons") or readiness.get("blocked_reasons")
    if isinstance(reasons, list | tuple) and reasons:
        return "; ".join(_text(reason, "") for reason in reasons if _text(reason, ""))
    return _text(
        entry.get("blocked_reason")
        or entry.get("blocked_reason_summary")
        or readiness.get("blocked_reason")
        or readiness.get("missing_reason"),
        "",
    )


def _catalog_bool(entry: Mapping[str, Any], key: str) -> bool | None:
    readiness = _mapping(entry.get("readiness"))
    return _optional_bool(entry.get(key)) if key in entry else _optional_bool(readiness.get(key))


def _catalog_durable_refs(entry: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("durable_refs", "evidence_refs", "proof_refs"):
        refs.extend(str(ref) for ref in _sequence(entry.get(key)) if _text(ref, ""))
    readiness = _mapping(entry.get("readiness"))
    refs.extend(str(ref) for ref in _sequence(readiness.get("durable_refs")) if _text(ref, ""))
    for surface in _sequence(readiness.get("capability_surfaces")):
        if not isinstance(surface, Mapping):
            continue
        refs.extend(str(ref) for ref in _sequence(surface.get("evidence_refs")) if _text(ref, ""))
    return refs


def _catalog_study_root(
    entry: Mapping[str, Any],
    *,
    catalog_payload: Mapping[str, Any],
) -> Path | None:
    root = _text(
        entry.get("study_root")
        or entry.get("root")
        or entry.get("path")
        or entry.get("study_path"),
        "",
    )
    if root:
        return Path(root).expanduser().resolve()
    study_id = _text(entry.get("study_id"), "")
    studies_root = _text(entry.get("studies_root") or catalog_payload.get("studies_root"), "")
    if study_id and studies_root:
        return (Path(studies_root).expanduser() / study_id).resolve()
    return None
