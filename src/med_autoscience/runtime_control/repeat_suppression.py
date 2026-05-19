from __future__ import annotations

from collections.abc import Mapping
from typing import Any


REPEAT_SUPPRESSED_REASON = "repeat_suppressed"
OWNER_HANDOFF_REASON = "controller_work_unit_owner_handoff_required"
CLEAN_MIGRATION_OWNER_HANDOFF_REASON = "paper_authority_clean_migration_required"
OWNER_HANDOFF_REASONS = frozenset({OWNER_HANDOFF_REASON, CLEAN_MIGRATION_OWNER_HANDOFF_REASON})
PUBLICATION_GATE_SPECIFICITY_REASON = "publication_gate_specificity_required"
HARD_METHODOLOGY_REASON = "unit_harmonized_rerun_required"
HARD_METHODOLOGY_ACTION = "unit_harmonized_external_validation_rerun"
ANALYSIS_HARMONIZATION_OWNER = "analysis_harmonization_owner"
MODEL_PROVENANCE_REASON = "transport_model_provenance_recovery_required"
MODEL_PROVENANCE_ACTION = "recover_transport_model_provenance"
SOURCE_PROVENANCE_OWNER = "source_provenance_owner"
PROVENANCE_LIMITED_REASON = "provenance_limited_harmonization_audit_required"
PROVENANCE_LIMITED_ACTION = "provenance_limited_harmonization_audit"
PROVENANCE_LIMITED_OWNER = "provenance_limited_harmonization_owner"


def repeat_key(payload: Mapping[str, Any] | None) -> str | None:
    mapping = _mapping(payload)
    if not mapping:
        return None
    prompt_contract = _mapping(mapping.get("prompt_contract"))
    owner_route = _mapping(mapping.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))
    for value in (
        prompt_contract.get("repeat_suppression_key"),
        mapping.get("repeat_suppression_key"),
        owner_route.get("work_unit_fingerprint"),
        mapping.get("work_unit_fingerprint"),
    ):
        if text := _text(value):
            return text
    return None


def meaningful_artifact_delta_observed(payload: Mapping[str, Any] | None) -> bool:
    mapping = _mapping(payload)
    if not mapping:
        return False
    if mapping.get("meaningful_artifact_delta") is True:
        return True
    artifact_delta = _mapping(mapping.get("artifact_delta"))
    if _text(artifact_delta.get("latest_meaningful_delta_at")) is not None:
        return True
    progress_freshness = _mapping(mapping.get("progress_freshness"))
    artifact_delta_freshness = _mapping(progress_freshness.get("meaningful_artifact_delta_freshness"))
    return _text(artifact_delta_freshness.get("latest_progress_at")) is not None


def scan_repeat_suppression(
    *,
    previous_payload: Mapping[str, Any] | None,
    study_id: str,
    owner_route: Mapping[str, Any],
    current_meaningful_artifact_delta: bool,
    required_output_pending: bool = False,
) -> dict[str, Any]:
    key = repeat_key(owner_route)
    route_signature = _route_signature(owner_route)
    if (
        _owner_handoff_route(owner_route)
        or publication_gate_specificity_route(owner_route)
        or hard_methodology_harmonization_route(owner_route)
        or source_provenance_recovery_route(owner_route)
        or provenance_limited_harmonization_route(owner_route)
        or _external_supervisor_repair_route(owner_route)
    ):
        return _not_suppressed(key)
    if key is None or current_meaningful_artifact_delta or required_output_pending:
        return _not_suppressed(key)
    for study in _list(_mapping(previous_payload).get("studies")):
        study_payload = _mapping(study)
        if _text(study_payload.get("study_id")) != study_id:
            continue
        if meaningful_artifact_delta_observed(study_payload):
            return _not_suppressed(key)
        previous_route = _mapping(study_payload.get("owner_route"))
        if (
            repeat_key(previous_route) == key
            and _route_signature(previous_route) == route_signature
            and _study_owner_receipt_observed(study_payload)
        ):
            return _suppressed(key, "previous_scan_same_work_unit_without_artifact_delta")
    for action in _list(_mapping(previous_payload).get("action_queue")):
        action_payload = _mapping(action)
        if _text(action_payload.get("study_id")) != study_id:
            continue
        action_route = _mapping(action_payload.get("owner_route")) or _mapping(_mapping(action_payload.get("handoff_packet")).get("owner_route"))
        if (
            repeat_key(action_payload) == key
            and _route_signature(action_route) == route_signature
            and _action_owner_receipt_observed(action_payload)
        ):
            return _suppressed(key, "previous_scan_action_same_work_unit_without_artifact_delta")
    return _not_suppressed(key)


def dispatch_repeat_suppression(
    *,
    dispatch: Mapping[str, Any],
    current_study: Mapping[str, Any] | None,
    existing_dispatch: Mapping[str, Any] | None,
    required_output_pending: bool = False,
) -> dict[str, Any]:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    if prompt_contract.get("do_not_repeat") is not True:
        return _not_suppressed(repeat_key(dispatch))
    key = repeat_key(dispatch)
    if key is None:
        return _not_suppressed(None)
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))
    if (
        _owner_handoff_route(owner_route)
        or publication_gate_specificity_route(owner_route)
        or hard_methodology_harmonization_route(owner_route)
        or source_provenance_recovery_route(owner_route)
        or provenance_limited_harmonization_route(owner_route)
        or _external_supervisor_repair_route(owner_route)
    ):
        return _not_suppressed(key)
    if meaningful_artifact_delta_observed(current_study) or required_output_pending:
        return _not_suppressed(key)
    existing = _mapping(existing_dispatch)
    if existing and _text(existing.get("dispatch_status")) == "ready" and repeat_key(existing) == key:
        return _not_suppressed(key)
    if existing and _text(existing.get("dispatch_status")) == "repeat_suppressed" and repeat_key(existing) == key:
        return _suppressed(key, "existing_dispatch_same_work_unit_without_artifact_delta")
    return _not_suppressed(key)


def execution_repeat_suppression(
    *,
    dispatch: Mapping[str, Any],
    current_study: Mapping[str, Any] | None,
    previous_execution_latest: Mapping[str, Any] | None,
    required_output_pending: bool = False,
) -> dict[str, Any]:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    if prompt_contract.get("do_not_repeat") is not True:
        return _not_suppressed(repeat_key(dispatch))
    key = repeat_key(dispatch)
    if key is None:
        return _not_suppressed(None)
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))
    if (
        _owner_handoff_route(owner_route)
        or publication_gate_specificity_route(owner_route)
        or hard_methodology_harmonization_route(owner_route)
        or source_provenance_recovery_route(owner_route)
        or provenance_limited_harmonization_route(owner_route)
        or _external_supervisor_repair_route(owner_route)
    ):
        return _not_suppressed(key)
    if meaningful_artifact_delta_observed(current_study) or required_output_pending:
        return _not_suppressed(key)
    for execution in _list(_mapping(previous_execution_latest).get("executions")):
        execution_payload = _mapping(execution)
        if repeat_key(execution_payload) == key:
            return _suppressed(key, "previous_execution_same_work_unit_without_artifact_delta")
    return _not_suppressed(key)


def _suppressed(key: str, source: str) -> dict[str, Any]:
    return {
        "repeat_suppressed": True,
        "why_not_applied": REPEAT_SUPPRESSED_REASON,
        "work_unit_fingerprint": key,
        "repeat_suppression_key": key,
        "suppression_source": source,
    }


def _not_suppressed(key: str | None) -> dict[str, Any]:
    return {
        "repeat_suppressed": False,
        "why_not_applied": None,
        "work_unit_fingerprint": key,
        "repeat_suppression_key": key,
    }


def _owner_handoff_route(owner_route: Mapping[str, Any]) -> bool:
    route = _mapping(owner_route)
    owner_reason = _text(route.get("owner_reason"))
    failure_signature = _text(route.get("failure_signature"))
    if owner_reason in OWNER_HANDOFF_REASONS:
        return True
    return failure_signature in OWNER_HANDOFF_REASONS


def _external_supervisor_repair_route(owner_route: Mapping[str, Any]) -> bool:
    route = _mapping(owner_route)
    return (
        _text(route.get("next_owner")) == "external_supervisor"
        and _text(route.get("owner_reason")) == "runtime_recovery_not_authorized"
    )


def publication_gate_specificity_route(owner_route: Mapping[str, Any]) -> bool:
    route = _mapping(owner_route)
    if _text(route.get("next_owner")) != "publication_gate":
        return False
    route_reason = _text(route.get("owner_reason")) or _text(route.get("failure_signature"))
    if route_reason != PUBLICATION_GATE_SPECIFICITY_REASON:
        return False
    return PUBLICATION_GATE_SPECIFICITY_REASON in {
        item for value in route.get("allowed_actions") or [] if (item := _text(value)) is not None
    }


def hard_methodology_harmonization_route(owner_route: Mapping[str, Any]) -> bool:
    route = _mapping(owner_route)
    if _text(route.get("next_owner")) != ANALYSIS_HARMONIZATION_OWNER:
        return False
    route_reason = _text(route.get("owner_reason")) or _text(route.get("failure_signature"))
    if route_reason != HARD_METHODOLOGY_REASON:
        return False
    return HARD_METHODOLOGY_ACTION in {
        item for value in route.get("allowed_actions") or [] if (item := _text(value)) is not None
    }


def source_provenance_recovery_route(owner_route: Mapping[str, Any]) -> bool:
    route = _mapping(owner_route)
    if _text(route.get("next_owner")) != SOURCE_PROVENANCE_OWNER:
        return False
    route_reason = _text(route.get("owner_reason")) or _text(route.get("failure_signature"))
    if route_reason != MODEL_PROVENANCE_REASON:
        return False
    return MODEL_PROVENANCE_ACTION in {
        item for value in route.get("allowed_actions") or [] if (item := _text(value)) is not None
    }


def provenance_limited_harmonization_route(owner_route: Mapping[str, Any]) -> bool:
    route = _mapping(owner_route)
    if _text(route.get("next_owner")) != PROVENANCE_LIMITED_OWNER:
        return False
    route_reason = _text(route.get("owner_reason")) or _text(route.get("failure_signature"))
    if route_reason != PROVENANCE_LIMITED_REASON:
        return False
    return PROVENANCE_LIMITED_ACTION in {
        item for value in route.get("allowed_actions") or [] if (item := _text(value)) is not None
    }


def _route_signature(owner_route: Mapping[str, Any] | None) -> tuple[str | None, str | None, tuple[str, ...]]:
    route = _mapping(owner_route)
    return (
        _text(route.get("next_owner")),
        _text(route.get("owner_reason")) or _text(route.get("failure_signature")),
        tuple(item for value in route.get("allowed_actions") or [] if (item := _text(value)) is not None),
    )


def _study_owner_receipt_observed(study: Mapping[str, Any]) -> bool:
    repeat = _mapping(study.get("repeat_suppression"))
    if repeat.get("repeat_suppressed") is True:
        return True
    return _text(study.get("dispatch_status")) in {"ready", "applied", "executed", "repeat_suppressed"}


def _action_owner_receipt_observed(action: Mapping[str, Any]) -> bool:
    if _text(action.get("dispatch_status")) in {"ready", "applied", "executed", "repeat_suppressed"}:
        return True
    consumption_state = _text(_mapping(action.get("consumption")).get("state"))
    if consumption_state in {"consumed", "picked_up", "dispatched"}:
        return True
    owner_pickup_state = _text(_mapping(action.get("owner_pickup")).get("state"))
    return owner_pickup_state in {"picked_up", "consumed", "dispatched"}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "OWNER_HANDOFF_REASON",
    "OWNER_HANDOFF_REASONS",
    "HARD_METHODOLOGY_ACTION",
    "HARD_METHODOLOGY_REASON",
    "MODEL_PROVENANCE_ACTION",
    "MODEL_PROVENANCE_REASON",
    "PROVENANCE_LIMITED_ACTION",
    "PROVENANCE_LIMITED_REASON",
    "CLEAN_MIGRATION_OWNER_HANDOFF_REASON",
    "PUBLICATION_GATE_SPECIFICITY_REASON",
    "REPEAT_SUPPRESSED_REASON",
    "dispatch_repeat_suppression",
    "execution_repeat_suppression",
    "hard_methodology_harmonization_route",
    "meaningful_artifact_delta_observed",
    "publication_gate_specificity_route",
    "provenance_limited_harmonization_route",
    "repeat_key",
    "scan_repeat_suppression",
    "source_provenance_recovery_route",
]
