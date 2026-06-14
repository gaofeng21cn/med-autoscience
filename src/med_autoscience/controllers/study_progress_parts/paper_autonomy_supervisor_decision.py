from __future__ import annotations

from collections.abc import Mapping
from typing import Any


EXECUTE_DECISION = "execute_current_owner_delta"
BLOCK_REASON = "paper_autonomy_supervisor_decision_blocks_provider_admission"

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
    "stage-run",
    "stage_run",
    "stage-attempt",
    "stage_attempt",
    "lease",
    "provider-attempt",
    "provider_attempt",
    "workflow",
)


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
    from med_autoscience.controllers.paper_autonomy_supervisor import build_supervisor_decision

    return build_supervisor_decision(
        payload,
        paper_recovery_state=recovery,
        diagnostic_report=_mapping(diagnostic_report),
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
    if _has_marker(evidence_refs, _PROVIDER_EVIDENCE_MARKERS):
        return True
    return _has_marker(evidence_refs, _STAGE_RUN_EVIDENCE_MARKERS)


def _supervisor_decision_allows_provider_admission_materialization(
    supervisor_decision: Mapping[str, Any],
    *,
    payload: Mapping[str, Any],
    paper_recovery_state: Mapping[str, Any] | None,
) -> bool:
    if _text(supervisor_decision.get("decision")) != "materialize_recovery_action":
        return False
    recovery = _mapping(paper_recovery_state) or _mapping(payload.get("paper_recovery_state"))
    next_safe_action = _mapping(recovery.get("next_safe_action"))
    if next_safe_action.get("provider_admission_allowed") is not True:
        return False
    phase = _text(recovery.get("phase"))
    if phase not in {"owner_action_ready", "admission_pending"}:
        return False
    action_kind = _text(next_safe_action.get("kind"))
    return action_kind in {
        "materialize_provider_admission_or_owner_callable",
        "materialize_successor_owner_action",
        "admit_provider_attempt",
        "admit_identity_bound_stage_packet",
    }


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


def _explicit_supervisor_decision(
    payload: Mapping[str, Any],
    *,
    paper_recovery_state: Mapping[str, Any] | None,
) -> dict[str, Any]:
    recovery = _mapping(paper_recovery_state) or _mapping(payload.get("paper_recovery_state"))
    for candidate in (
        payload.get("paper_autonomy_supervisor_decision"),
        payload.get("supervisor_decision"),
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


__all__ = [
    "BLOCK_REASON",
    "EXECUTE_DECISION",
    "execute_decision_identity_evidence_complete",
    "provider_admission_supervisor_gate",
    "supervisor_block_projection",
    "supervisor_decision_blocks_provider_admission",
    "supervisor_decision_for_projection",
]
