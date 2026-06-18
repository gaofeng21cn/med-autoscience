from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback import (
    has_opl_transition_readback as _has_opl_transition_readback,
)


EXECUTE_DECISION = "execute_current_owner_delta"
BLOCK_REASON = "paper_autonomy_supervisor_decision_blocks_provider_admission"
READBACK_REQUIRED_DECISION = "opl_supervisor_decision_readback_required"

_REQUIRED_OBLIGATION_FIELDS = (
    "study_id",
    "quest_id",
    "stage_id",
    "action_type",
    "work_unit_id",
    "work_unit_fingerprint",
    "route_identity_key",
    "attempt_idempotency_key",
)
_PROVIDER_EVIDENCE_MARKERS = (
    "provider-admission",
    "provider_admission",
    "stage-packet",
    "stage_packet",
    "selected-dispatch",
    "selected_dispatch",
)
_STAGE_RUN_EVIDENCE_MARKERS = (
    "default_executor_dispatches",
    "default-executor-dispatch",
    "stage-run",
    "stage_run",
    "stage-attempt",
    "stage_attempt",
    "lease",
    "provider-attempt",
    "provider_attempt",
    "workflow",
)
_OPL_TRANSITION_READBACK_SOURCE = "opl_domain_progress_transition_runtime_live_readback"


def supervisor_decision_for_projection(
    payload: Mapping[str, Any],
    *,
    paper_recovery_state: Mapping[str, Any] | None = None,
    diagnostic_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    explicit = _explicit_supervisor_decision(
        payload,
        paper_recovery_state=paper_recovery_state,
    )
    if explicit:
        return explicit
    recovery = _mapping(paper_recovery_state) or _mapping(payload.get("paper_recovery_state"))
    if not recovery:
        return {}
    return _supervisor_decision_readback_required_projection(
        payload,
        paper_recovery_state=recovery,
        diagnostic_report=diagnostic_report,
    )


def provider_admission_supervisor_gate(
    payload: Mapping[str, Any],
    *,
    paper_recovery_state: Mapping[str, Any] | None = None,
    diagnostic_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    decision = supervisor_decision_for_projection(
        payload,
        paper_recovery_state=paper_recovery_state,
        diagnostic_report=diagnostic_report,
    )
    if not decision:
        return {
            "blocked": False,
            "admission_allowed": None,
            "supervisor_decision": {},
        }
    decision_kind = _text(decision.get("decision"))
    if decision_kind == READBACK_REQUIRED_DECISION:
        if _readback_required_projection_satisfied_by_opl_runtime_readback(
            decision,
            payload=payload,
            paper_recovery_state=paper_recovery_state,
        ):
            return {
                "blocked": False,
                "admission_allowed": True,
                "supervisor_decision": dict(decision),
            }
        return _blocked_gate(decision, reason=READBACK_REQUIRED_DECISION)
    if decision_kind != EXECUTE_DECISION:
        if _supervisor_decision_allows_provider_admission_materialization(
            decision,
            payload=payload,
            paper_recovery_state=paper_recovery_state,
        ):
            return {
                "blocked": False,
                "admission_allowed": True,
                "supervisor_decision": dict(decision),
            }
        return _blocked_gate(decision, reason=BLOCK_REASON)
    if not execute_decision_identity_evidence_complete(decision):
        return _blocked_gate(
            decision,
            reason="execute_current_owner_delta_missing_identity_or_evidence",
        )
    return {
        "blocked": False,
        "admission_allowed": True,
        "supervisor_decision": dict(decision),
    }


def supervisor_decision_blocks_provider_admission(
    supervisor_decision: Mapping[str, Any],
) -> bool:
    return provider_admission_supervisor_gate(
        {"paper_autonomy_supervisor_decision": supervisor_decision}
    ).get("blocked") is True


def execute_decision_identity_evidence_complete(
    supervisor_decision: Mapping[str, Any],
) -> bool:
    decision = _mapping(supervisor_decision)
    if _text(decision.get("decision")) != EXECUTE_DECISION:
        return False
    if decision.get("identity_match") is not True:
        return False
    if _text_items(decision.get("missing_evidence_refs")):
        return False
    obligation = _mapping(decision.get("paper_autonomy_obligation"))
    if not all(_text(obligation.get(key)) is not None for key in _REQUIRED_OBLIGATION_FIELDS):
        return False
    evidence_refs = _text_items(decision.get("evidence_refs"))
    return _has_marker(evidence_refs, _PROVIDER_EVIDENCE_MARKERS) and _has_marker(
        evidence_refs,
        _STAGE_RUN_EVIDENCE_MARKERS,
    )


def _supervisor_decision_allows_provider_admission_materialization(
    supervisor_decision: Mapping[str, Any],
    *,
    payload: Mapping[str, Any],
    paper_recovery_state: Mapping[str, Any] | None,
) -> bool:
    if _text(supervisor_decision.get("decision")) != "materialize_recovery_action":
        return False
    recovery = _mapping(paper_recovery_state) or _mapping(payload.get("paper_recovery_state"))
    if _payload_has_bound_opl_transition_readback(
        payload,
        supervisor_decision=supervisor_decision,
    ):
        return True
    if _payload_has_opl_transition_readback(payload):
        return _text(recovery.get("phase")) == "admission_pending"
    next_safe_action = _mapping(recovery.get("next_safe_action"))
    if next_safe_action.get("provider_admission_requires_opl_runtime_result") is not False:
        return False
    phase = _text(recovery.get("phase"))
    if phase != "admission_pending":
        return False
    action_kind = _text(next_safe_action.get("kind"))
    return action_kind in {
        "materialize_mas_transition_request_or_owner_callable",
        "materialize_successor_owner_action",
        "admit_provider_attempt",
        "admit_identity_bound_stage_packet",
    }


def _payload_has_bound_opl_transition_readback(
    payload: Mapping[str, Any],
    *,
    supervisor_decision: Mapping[str, Any],
) -> bool:
    obligation = _mapping(supervisor_decision.get("paper_autonomy_obligation"))
    return any(
        _candidate_has_matching_opl_readback(
            item,
            obligation=obligation,
        )
        for field in ("provider_admission_candidates", "transition_request_candidates")
        for item in payload.get(field) or []
        if isinstance(item, Mapping)
    )


def _readback_required_projection_satisfied_by_opl_runtime_readback(
    supervisor_decision: Mapping[str, Any],
    *,
    payload: Mapping[str, Any],
    paper_recovery_state: Mapping[str, Any] | None,
) -> bool:
    recovery = _mapping(paper_recovery_state) or _mapping(payload.get("paper_recovery_state"))
    if _text(recovery.get("phase")) != "admission_pending":
        return False
    projection_identity = _mapping(supervisor_decision.get("paper_autonomy_obligation_identity"))
    recovery_obligation = _mapping(_mapping(recovery.get("current_authority")).get("obligation"))
    obligation = projection_identity or recovery_obligation
    if not obligation:
        return False
    return _payload_has_bound_opl_transition_readback(
        payload,
        supervisor_decision={"paper_autonomy_obligation": obligation},
    )


def _candidate_has_matching_opl_readback(
    candidate: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> bool:
    if _text(candidate.get("opl_transition_readback_source")) != _OPL_TRANSITION_READBACK_SOURCE:
        return False
    if not _has_opl_transition_readback(candidate):
        return False
    result = _mapping(candidate.get("opl_domain_progress_transition_result"))
    identity = _mapping(result.get("identity"))
    aggregate_identity = _mapping(identity.get("aggregate_identity"))
    if not identity and not aggregate_identity:
        return False
    if not _candidate_identity_fields_do_not_conflict(candidate, obligation=obligation):
        return False
    return (
        _same_text(
            _first_text(
                identity.get("study_id"),
                aggregate_identity.get("study_id"),
                candidate.get("study_id"),
                candidate.get("quest_id"),
            ),
            obligation.get("study_id"),
        )
        and _same_text(candidate.get("action_type"), obligation.get("action_type"))
        and _same_text(
            _first_text(identity.get("work_unit_id"), aggregate_identity.get("work_unit_id")),
            obligation.get("work_unit_id"),
        )
        and _same_text(
            _first_text(
                identity.get("work_unit_fingerprint"),
                aggregate_identity.get("work_unit_fingerprint"),
            ),
            obligation.get("work_unit_fingerprint"),
        )
    )


def _candidate_identity_fields_do_not_conflict(
    candidate: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> bool:
    study_id = _text(obligation.get("study_id"))
    if study_id is not None:
        for key in ("study_id", "quest_id"):
            value = _text(candidate.get(key))
            if value is not None and value != study_id:
                return False
    for key in ("action_type", "work_unit_id"):
        expected = _text(obligation.get(key))
        value = _text(candidate.get(key))
        if expected is not None and value is not None and value != expected:
            return False
    expected_fingerprint = _text(obligation.get("work_unit_fingerprint"))
    if expected_fingerprint is not None:
        for key in ("work_unit_fingerprint", "action_fingerprint"):
            value = _text(candidate.get(key))
            if value is not None and value != expected_fingerprint:
                return False
    return True


def _payload_has_opl_transition_readback(payload: Mapping[str, Any]) -> bool:
    return any(
        _has_opl_transition_readback(item)
        for field in ("provider_admission_candidates", "transition_request_candidates")
        for item in payload.get(field) or []
        if isinstance(item, Mapping)
    )


def supervisor_block_projection(gate: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(gate.get("supervisor_decision"))
    decision_kind = _text(decision.get("decision"))
    reason = _text(gate.get("reason")) or BLOCK_REASON
    return {
        "decision": decision_kind,
        "reason": reason,
    }


def _blocked_gate(supervisor_decision: Mapping[str, Any], *, reason: str) -> dict[str, Any]:
    return {
        "blocked": True,
        "admission_allowed": False,
        "reason": reason,
        "supervisor_decision": dict(supervisor_decision),
    }


def _supervisor_decision_readback_required_projection(
    payload: Mapping[str, Any],
    *,
    paper_recovery_state: Mapping[str, Any],
    diagnostic_report: Mapping[str, Any] | None,
) -> dict[str, Any]:
    recovery = _mapping(paper_recovery_state)
    current_work_unit = _mapping(payload.get("current_work_unit"))
    current_action = _mapping(payload.get("current_executable_owner_action"))
    obligation = _mapping(_mapping(recovery.get("current_authority")).get("obligation"))
    diagnostic = _mapping(diagnostic_report)
    return _clean_mapping(
        {
            "surface_kind": "paper_progress_policy_result_projection",
            "projection_role": "mas_paper_progress_policy_result_projection",
            "policy_result_role": "mas_paper_progress_policy_result_projection",
            "decision": READBACK_REQUIRED_DECISION,
            "decision_authority": False,
            "legacy_decision_surface_kind": "paper_autonomy_supervisor_decision",
            "legacy_decision_field_role": "policy_recommendation_label",
            "legacy_decision_field_is_authority": False,
            "decision_field_deprecated": True,
            "read_model_can_build_supervisor_decision": False,
            "requires_explicit_supervisor_decision_projection": True,
            "requires_opl_supervisor_decision_engine_readback": True,
            "supervisor_decision_engine_owner": "one-person-lab",
            "recovery_obligation_store_owner": "one-person-lab",
            "mas_can_run_supervisor_decision_engine": False,
            "mas_can_store_recovery_obligation": False,
            "mas_can_create_opl_command_event_or_outbox": False,
            "mas_can_authorize_provider_admission": False,
            "provider_admission_pending": False,
            "request_projection_only": True,
            "paper_progress_classification": "none_until_opl_supervisor_decision_readback",
            "platform_repair_classification": "readback_required",
            "next_owner": "one-person-lab",
            "next_safe_action": {
                "kind": READBACK_REQUIRED_DECISION,
                "required_readback_shape": "RecoveryObligationStore/SupervisorDecisionEngine",
            },
            "missing_evidence_refs": [
                "explicit_paper_autonomy_supervisor_decision_projection",
                "opl_supervisor_decision_engine_readback",
            ],
            "evidence_refs": _text_items(recovery.get("evidence_refs"))
            + _text_items(diagnostic.get("evidence_refs")),
            "paper_autonomy_obligation_identity": _clean_mapping(
                {
                    "study_id": _first_text(
                        obligation.get("study_id"),
                        recovery.get("study_id"),
                        payload.get("study_id"),
                        current_work_unit.get("study_id"),
                    ),
                    "quest_id": _first_text(
                        obligation.get("quest_id"),
                        recovery.get("quest_id"),
                        payload.get("quest_id"),
                        current_work_unit.get("quest_id"),
                    ),
                    "stage_id": _first_text(
                        obligation.get("stage_id"),
                        current_work_unit.get("stage_id"),
                    ),
                    "action_type": _first_text(
                        obligation.get("action_type"),
                        current_work_unit.get("action_type"),
                        current_action.get("action_type"),
                    ),
                    "work_unit_id": _first_text(
                        obligation.get("work_unit_id"),
                        current_work_unit.get("work_unit_id"),
                        current_action.get("work_unit_id"),
                    ),
                    "work_unit_fingerprint": _first_text(
                        obligation.get("work_unit_fingerprint"),
                        current_work_unit.get("work_unit_fingerprint"),
                        current_action.get("work_unit_fingerprint"),
                    ),
                    "route_identity_key": _first_text(
                        obligation.get("route_identity_key"),
                        current_work_unit.get("route_identity_key"),
                    ),
                    "attempt_idempotency_key": _first_text(
                        obligation.get("attempt_idempotency_key"),
                        current_work_unit.get("attempt_idempotency_key"),
                        current_work_unit.get("idempotency_key"),
                    ),
                }
            ),
            "authority_boundary": {
                "adapter_kind": "mas_policy_adapter",
                "decision_authority": False,
                "read_model_can_create_decision": False,
                "supervisor_decision_engine_owner": "one-person-lab",
                "recovery_obligation_store_owner": "one-person-lab",
                "can_run_supervisor_decision_engine": False,
                "can_store_recovery_obligation": False,
                "can_create_opl_command_event_or_outbox": False,
                "can_authorize_provider_admission": False,
            },
        },
        keep_empty_keys={"evidence_refs", "missing_evidence_refs"},
    )


def _explicit_supervisor_decision(
    payload: Mapping[str, Any],
    *,
    paper_recovery_state: Mapping[str, Any] | None,
) -> dict[str, Any]:
    recovery = _mapping(paper_recovery_state) or _mapping(payload.get("paper_recovery_state"))
    for candidate in (
        payload.get("paper_progress_policy_result_projection"),
        payload.get("paper_autonomy_supervisor_decision"),
        payload.get("supervisor_decision"),
        recovery.get("paper_progress_policy_result_projection"),
        recovery.get("supervisor_decision"),
        recovery.get("paper_autonomy_supervisor_decision"),
    ):
        decision = _mapping(candidate)
        if decision:
            return decision
    return {}


def _has_marker(values: list[str], markers: tuple[str, ...]) -> bool:
    return any(any(marker in value for marker in markers) for value in values)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _text(value)
        return [text] if text is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _same_text(left: object, right: object) -> bool:
    left_text = _text(left)
    right_text = _text(right)
    return left_text is not None and right_text is not None and left_text == right_text


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _text(value)
        if text is not None:
            return text
    return None


def _clean_mapping(
    value: Mapping[str, Any],
    *,
    keep_empty_keys: set[str] | None = None,
) -> dict[str, Any]:
    keep = keep_empty_keys or set()
    return {
        key: item
        for key, item in dict(value).items()
        if key in keep or item not in (None, "", [], {})
    }


__all__ = [
    "BLOCK_REASON",
    "EXECUTE_DECISION",
    "READBACK_REQUIRED_DECISION",
    "execute_decision_identity_evidence_complete",
    "provider_admission_supervisor_gate",
    "supervisor_block_projection",
    "supervisor_decision_blocks_provider_admission",
    "supervisor_decision_for_projection",
]
