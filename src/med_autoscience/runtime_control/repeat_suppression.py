from __future__ import annotations

from collections.abc import Mapping
from typing import Any


REPEAT_SUPPRESSED_REASON = "repeat_suppressed"
ANTI_LOOP_BUDGET_EXHAUSTED_REASON = "anti_loop_budget_exhausted"
LOOP_GUARD_STALE_REPLAY_REASON = "owner_route_loop_guard_stale_replay"
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
CURRENT_AI_REVIEWER_MATERIALIZATION_WORK_UNIT = "materialize_current_ai_reviewer_record_through_mas_owner_surface"


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
    materialization_guard = _materialization_loop_guard_or_none(
        previous_payload=previous_payload,
        study_id=study_id,
        owner_route=owner_route,
    )
    if materialization_guard is not None:
        return materialization_guard
    if _current_ai_reviewer_materialization_identity(study_id=study_id, owner_route=owner_route) is not None:
        return _not_suppressed(key)
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
    route_signature = _route_signature(owner_route)
    study_suppression = _previous_scan_study_suppression(
        previous_payload=previous_payload,
        study_id=study_id,
        key=key,
        route_signature=route_signature,
    )
    if study_suppression is not None:
        return study_suppression
    action_suppression = _previous_scan_action_suppression(
        previous_payload=previous_payload,
        study_id=study_id,
        key=key,
        route_signature=route_signature,
    )
    if action_suppression is not None:
        return action_suppression
    return _not_suppressed(key)


def _previous_scan_study_suppression(
    *,
    previous_payload: Mapping[str, Any] | None,
    study_id: str,
    key: str,
    route_signature: tuple[str | None, str | None, tuple[str, ...]],
) -> dict[str, Any] | None:
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
    return None


def _previous_scan_action_suppression(
    *,
    previous_payload: Mapping[str, Any] | None,
    study_id: str,
    key: str,
    route_signature: tuple[str | None, str | None, tuple[str, ...]],
) -> dict[str, Any] | None:
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
    return None


def _materialization_loop_guard_or_none(
    *,
    previous_payload: Mapping[str, Any] | None,
    study_id: str,
    owner_route: Mapping[str, Any],
) -> dict[str, Any] | None:
    guard = _current_ai_reviewer_materialization_loop_guard(
        previous_payload=previous_payload,
        study_id=study_id,
        owner_route=owner_route,
    )
    return guard


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
    anti_loop_guard = _anti_loop_budget_guard(
        dispatch=dispatch,
        previous_execution_latest=previous_execution_latest,
        key=key,
    )
    if anti_loop_guard is not None:
        return anti_loop_guard
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


def _anti_loop_budget_guard(
    *,
    dispatch: Mapping[str, Any],
    previous_execution_latest: Mapping[str, Any] | None,
    key: str,
) -> dict[str, Any] | None:
    identity = _dispatch_auto_failure_identity(dispatch=dispatch, key=key)
    if identity is None:
        return None
    failures = _matching_auto_failures(
        previous_execution_latest=previous_execution_latest,
        identity=identity,
    )
    if len(failures) < 2:
        return None
    blocker_reason = failures[-1]["blocker_reason"]
    return {
        "repeat_suppressed": True,
        "why_not_applied": ANTI_LOOP_BUDGET_EXHAUSTED_REASON,
        "work_unit_fingerprint": key,
        "repeat_suppression_key": key,
        "suppression_source": "previous_two_same_work_unit_blocker_failures",
        "anti_loop_budget": {
            "status": "exhausted",
            "max_automatic_failures": 2,
            "failure_count": len(failures),
            "study_id": identity["study_id"],
            "action_type": identity["action_type"],
            "work_unit_id": identity["work_unit_id"],
            "work_unit_fingerprint": key,
            "blocker_reason": blocker_reason,
            "escalation_route": "publishability_repair_sprint",
            "next_allowed_outcomes": [
                "publishability_repair_sprint",
                "single_typed_blocker",
                "human_or_operator_gate",
            ],
        },
    }


def _dispatch_auto_failure_identity(*, dispatch: Mapping[str, Any], key: str) -> dict[str, str] | None:
    study_id = _text(dispatch.get("study_id")) or _text(_mapping(dispatch.get("prompt_contract")).get("study_id"))
    action_type = _text(dispatch.get("action_type")) or _text(_mapping(dispatch.get("prompt_contract")).get("action_type"))
    work_unit_id = _work_unit_id_from_dispatch(dispatch)
    if study_id is None or action_type is None:
        return None
    return {
        "study_id": study_id,
        "action_type": action_type,
        "work_unit_id": work_unit_id or key,
        "work_unit_fingerprint": key,
    }


def _matching_auto_failures(
    *,
    previous_execution_latest: Mapping[str, Any] | None,
    identity: Mapping[str, str],
) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for execution in _previous_execution_records(previous_execution_latest):
        execution_payload = _mapping(execution)
        blocker_reason = _text(execution_payload.get("blocked_reason"))
        if blocker_reason is None:
            failures.clear()
            continue
        if not _execution_auto_failure_observed(execution_payload):
            failures.clear()
            continue
        if not _execution_matches_failure_identity(execution_payload, identity=identity):
            failures.clear()
            continue
        if failures and failures[-1]["blocker_reason"] != blocker_reason:
            failures = []
        failures.append({"blocker_reason": blocker_reason})
    return failures


def _previous_execution_records(previous_execution_latest: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    payload = _mapping(previous_execution_latest)
    records = _list(payload.get("execution_ledger")) or _list(payload.get("executions"))
    return [item for item in records if isinstance(item, Mapping)]


def _execution_matches_failure_identity(
    execution: Mapping[str, Any],
    *,
    identity: Mapping[str, str],
) -> bool:
    if _text(execution.get("study_id")) != identity["study_id"]:
        return False
    if _text(execution.get("action_type")) != identity["action_type"]:
        return False
    execution_key = repeat_key(execution)
    if execution_key != identity["work_unit_fingerprint"]:
        return False
    execution_work_unit_id = _work_unit_id_from_dispatch(execution)
    return execution_work_unit_id in {None, identity["work_unit_id"]}


def _execution_auto_failure_observed(execution: Mapping[str, Any]) -> bool:
    if _text(execution.get("execution_status")) != "blocked":
        return False
    if _text(execution.get("blocked_reason")) is None:
        return False
    if execution.get("repeat_suppressed") is True:
        return False
    if _text(execution.get("why_not_applied")) in {REPEAT_SUPPRESSED_REASON, ANTI_LOOP_BUDGET_EXHAUSTED_REASON}:
        return False
    return _execution_owner_receipt_observed(execution)


def _work_unit_id_from_dispatch(payload: Mapping[str, Any]) -> str | None:
    prompt_contract = _mapping(payload.get("prompt_contract"))
    source_action = _mapping(payload.get("source_action"))
    owner_route = _mapping(payload.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))
    route_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = _mapping(route_refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(owner_route.get("currentness_contract")).get("basis")
    )
    return (
        _work_unit_id(source_action.get("next_work_unit"))
        or _work_unit_id(payload.get("next_work_unit"))
        or _work_unit_id(prompt_contract.get("next_work_unit"))
        or _work_unit_id(route_refs.get("work_unit_id"))
        or _work_unit_id(currentness_basis.get("work_unit_id"))
    )


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id")) or _text(value.get("work_unit_id"))
    return _text(value)


def _current_ai_reviewer_materialization_loop_guard(
    *,
    previous_payload: Mapping[str, Any] | None,
    study_id: str,
    owner_route: Mapping[str, Any],
) -> dict[str, Any] | None:
    identity = _current_ai_reviewer_materialization_identity(
        study_id=study_id,
        owner_route=owner_route,
    )
    if identity is None:
        return None
    if _previous_materialization_identity_observed(previous_payload, identity):
        key = repeat_key(owner_route)
        return {
            "repeat_suppressed": True,
            "why_not_applied": LOOP_GUARD_STALE_REPLAY_REASON,
            "work_unit_fingerprint": key,
            "repeat_suppression_key": key,
            "suppression_source": "previous_scan_same_current_ai_reviewer_materialization_identity",
            "loop_guard": {
                "status": "stale_replay",
                "identity": identity,
                "stable_typed_blocker": {
                    "blocker_id": LOOP_GUARD_STALE_REPLAY_REASON,
                    "owner": "med-autoscience",
                    "write_permitted": False,
                },
            },
        }
    return _not_suppressed(repeat_key(owner_route))


def _current_ai_reviewer_materialization_identity(
    *,
    study_id: str,
    owner_route: Mapping[str, Any],
) -> dict[str, str] | None:
    route = _mapping(owner_route)
    refs = _mapping(route.get("source_refs"))
    work_unit_id = _text(refs.get("work_unit_id"))
    if work_unit_id != CURRENT_AI_REVIEWER_MATERIALIZATION_WORK_UNIT:
        return None
    source_fingerprint = _text(route.get("source_fingerprint"))
    source_eval_id = _text(refs.get("source_eval_id"))
    if not source_fingerprint or not source_eval_id:
        return None
    return {
        "study_id": study_id,
        "work_unit_id": work_unit_id,
        "source_fingerprint": source_fingerprint,
        "source_eval_id": source_eval_id,
    }


def _previous_materialization_identity_observed(
    previous_payload: Mapping[str, Any] | None,
    identity: Mapping[str, str],
) -> bool:
    payload = _mapping(previous_payload)
    for study in _list(payload.get("studies")):
        study_payload = _mapping(study)
        if _text(study_payload.get("study_id")) != identity["study_id"]:
            continue
        if _current_ai_reviewer_materialization_identity(
            study_id=identity["study_id"],
            owner_route=_mapping(study_payload.get("owner_route")),
        ) == dict(identity):
            return True
    for action in _list(payload.get("action_queue")):
        action_payload = _mapping(action)
        if _text(action_payload.get("study_id")) != identity["study_id"]:
            continue
        action_route = _mapping(action_payload.get("owner_route")) or _mapping(_mapping(action_payload.get("handoff_packet")).get("owner_route"))
        if _current_ai_reviewer_materialization_identity(
            study_id=identity["study_id"],
            owner_route=action_route,
        ) == dict(identity):
            return True
    return False


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


def _execution_owner_receipt_observed(execution: Mapping[str, Any]) -> bool:
    status = _text(execution.get("execution_status"))
    if status == "blocked" and (
        execution.get("dispatch_contract_valid") is False
        or _text(execution.get("dispatch_contract_blocked_reason")) is not None
        or (_text(execution.get("blocked_reason")) or "").endswith("_guard_missing")
    ):
        return False
    if status in {"executed", "handoff_ready", "repeat_suppressed"}:
        return True
    if _mapping(execution.get("owner_result")):
        return True
    if _mapping(execution.get("writer_worker_handoff")):
        return True
    if status == "blocked":
        return True
    return bool(_text(execution.get("owner_callable_surface")) and status is not None)


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
    "ANTI_LOOP_BUDGET_EXHAUSTED_REASON",
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
