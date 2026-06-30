from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import control_identity
from med_autoscience.controllers.current_work_unit_parts.stage_packet_blockers import (
    is_selected_dispatch_stage_packet_blocker as _is_selected_dispatch_stage_packet_blocker,
)
from med_autoscience.controllers.domain_action_request_materializer_parts import (
    currentness_identity,
)
from med_autoscience.controllers.provider_admission_parts.current_ai_reviewer_gate_replay import (
    current_ai_reviewer_gate_replay_fingerprint,
    current_ai_reviewer_gate_replay_source_eval_id,
    is_current_ai_reviewer_gate_replay_fingerprint,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_handoffs import (
    handoff_dispatch_path,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_helpers import (
    first_text as _first_text,
    mapping as _mapping,
    non_empty_text as _non_empty_text,
    text_items as _text_items,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_identity import (
    current_action_currentness_basis as _current_action_currentness_basis,
    current_work_unit_opl_authorization_required as _current_work_unit_opl_authorization_required,
    owner_route_currentness_basis_complete as _owner_route_currentness_basis_complete,
)
from med_autoscience.controllers.gate_clearing_batch_work_units import (
    PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS,
)
OWNER_CALLABLE_ADAPTERS = Path("artifacts/supervision/consumer/owner_callable_adapters")
PAPER_PROGRESS_TRANSITION_REQUESTS = Path(
    "artifacts/runtime/paper_progress_transition_refs/transition_requests"
)
CURRENT_CONTROL_PROVIDER_ADMISSION_ACTION_OWNERS = {
    "complete_medical_paper_readiness_surface": {"MedAutoScience"},
    "request_opl_stage_attempt": {"write"},
    "return_to_ai_reviewer_workflow": {"ai_reviewer"},
    "run_quality_repair_batch": {"analysis-campaign", "write"},
    "run_gate_clearing_batch": {"finalize", "gate_clearing_batch", "write"},
}
CURRENT_CONTROL_PROVIDER_ADMISSION_DEFAULT_EXECUTABLE_OWNERS = {
    "complete_medical_paper_readiness_surface": "MedAutoScience",
    "request_opl_stage_attempt": "write",
    "return_to_ai_reviewer_workflow": "ai_reviewer",
    "run_quality_repair_batch": "write",
    "run_gate_clearing_batch": "gate_clearing_batch",
}
OPL_RUNTIME_ROUTE_OWNERS = {"one-person-lab"}
ACCEPTED_OWNER_GATE_DECISION_SOURCE = "paper_recovery_state.accepted_owner_gate_decision"
CURRENT_CONTROL_PROVIDER_ADMISSION_DISPATCH_AUTHORITIES = {
    "complete_medical_paper_readiness_surface": {"consumer_owner_callable_dispatch"},
    "return_to_ai_reviewer_workflow": {"ai_reviewer_record_production_handoff"},
    "run_quality_repair_batch": {None, "quality_repair_batch_writer_handoff", "consumer_owner_callable_dispatch"},
    "run_gate_clearing_batch": {None, "consumer_owner_callable_dispatch"},
}


def _current_action_from_paper_recovery_successor(
    study: Mapping[str, Any],
) -> dict[str, Any]:
    recovery = _mapping(study.get("paper_recovery_state"))
    next_safe_action = _mapping(recovery.get("next_safe_action"))
    if _non_empty_text(next_safe_action.get("kind")) not in {
        "materialize_successor_owner_action",
        "materialize_successor_owner_gate",
    }:
        return {}
    successor = _mapping(next_safe_action.get("successor_owner_action"))
    action_type = _non_empty_text(successor.get("action_type"))
    owner = _non_empty_text(successor.get("next_owner")) or _non_empty_text(successor.get("owner"))
    work_unit_id = _non_empty_text(successor.get("work_unit_id")) or _non_empty_text(
        successor.get("next_work_unit")
    )
    if action_type is None or owner is None or work_unit_id is None:
        return {}
    executable_owner = _current_control_executable_owner(action_type=action_type, owner=owner)
    if executable_owner is None:
        return {}
    obligation = _mapping(_mapping(recovery.get("current_authority")).get("obligation"))
    current_work_unit = _mapping(study.get("current_work_unit"))
    currentness_basis = (
        _mapping(successor.get("currentness_basis"))
        or _mapping(obligation.get("currentness_basis"))
        or _mapping(current_work_unit.get("currentness_basis"))
    )
    fingerprint = _first_currentness_fingerprint(
        successor.get("work_unit_fingerprint"),
        successor.get("action_fingerprint"),
        obligation.get("work_unit_fingerprint"),
        obligation.get("action_fingerprint"),
        current_work_unit.get("work_unit_fingerprint"),
        current_work_unit.get("action_fingerprint"),
        currentness_basis.get("work_unit_fingerprint"),
        currentness_basis.get("source_fingerprint"),
        study_id=_non_empty_text(study.get("study_id")),
        action_type=action_type,
        work_unit_id=work_unit_id,
    )
    if fingerprint is None and _currentness_basis_can_bind_stable_ticket(currentness_basis):
        fingerprint = _stable_provider_admission_ticket(
            study_id=_non_empty_text(study.get("study_id")),
            action_type=action_type,
            work_unit_id=work_unit_id,
        )
    if fingerprint is None:
        return {}
    successor_source = _non_empty_text(successor.get("source_surface")) or _non_empty_text(
        currentness_basis.get("source")
    )
    basis = {
        **dict(currentness_basis),
        **({"current_action_source": successor_source} if successor_source is not None else {}),
        **({"current_work_unit_source": successor_source} if successor_source is not None else {}),
        "source_eval_id": (
            _non_empty_text(successor.get("source_eval_id"))
            or _non_empty_text(currentness_basis.get("source_eval_id"))
        ),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
    }
    basis = {key: value for key, value in basis.items() if value is not None}
    return {
        "surface_kind": "current_executable_owner_action",
        "status": "ready",
        "source": "paper_recovery_state.next_safe_action.successor_owner_action",
        "next_owner": executable_owner,
        "owner": executable_owner,
        "action_type": action_type,
        "allowed_actions": [action_type],
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "source_ref": _non_empty_text(successor.get("source_ref")),
        "source_surface": _non_empty_text(successor.get("source_surface")),
        "required_output_surface": _required_output_surface(successor),
        "owner_route_currentness_basis": basis,
        "currentness_basis": basis,
    }


def _current_action_from_accepted_owner_gate_admission(
    study: Mapping[str, Any],
) -> dict[str, Any]:
    recovery = _mapping(study.get("paper_recovery_state"))
    if not accepted_owner_gate_admission_matches_selected_dispatch_blocker(
        study=study,
        recovery=recovery,
    ):
        return {}
    next_safe_action = _mapping(recovery.get("next_safe_action"))
    current_work_unit = _mapping(study.get("current_work_unit"))
    action_type = _non_empty_text(current_work_unit.get("action_type"))
    work_unit_id = _non_empty_text(current_work_unit.get("work_unit_id"))
    fingerprint = _non_empty_text(current_work_unit.get("work_unit_fingerprint")) or _non_empty_text(
        current_work_unit.get("action_fingerprint")
    )
    if action_type is None or work_unit_id is None or fingerprint is None:
        return {}
    owner = _non_empty_text(next_safe_action.get("owner")) or _non_empty_text(current_work_unit.get("owner"))
    executable_owner = _current_control_executable_owner(action_type=action_type, owner=owner)
    if executable_owner is None:
        return {}
    currentness_basis = _mapping(current_work_unit.get("currentness_basis"))
    owner_gate_event = _accepted_owner_gate_admission_event(study, recovery=recovery)
    stage_packet_ref = _accepted_owner_gate_stage_packet_ref(
        recovery=recovery,
        owner_gate_event=owner_gate_event,
        study=study,
    )
    stage_packet_refs = _accepted_owner_gate_stage_packet_refs(
        recovery=recovery,
        owner_gate_event=owner_gate_event,
        study=study,
    )
    basis = {
        **dict(currentness_basis),
        "source": "paper_recovery_state.accepted_owner_gate_decision",
        "mas_owner_action_source": "paper_recovery_state.accepted_owner_gate_decision",
        "truth_epoch": _non_empty_text(currentness_basis.get("truth_epoch")) or fingerprint,
        "runtime_health_epoch": _non_empty_text(currentness_basis.get("runtime_health_epoch")) or fingerprint,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "stage_packet_ref": stage_packet_ref,
    }
    basis = {key: value for key, value in basis.items() if value is not None}
    action = {
        "surface_kind": "current_executable_owner_action",
        "status": "ready",
        "source": "paper_recovery_state.accepted_owner_gate_decision",
        "authority": "paper_recovery_state.accepted_owner_gate_decision",
        "next_owner": executable_owner,
        "owner": executable_owner,
        "action_type": action_type,
        "allowed_actions": [action_type],
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "source_ref": stage_packet_ref or _first_text(recovery.get("evidence_refs")),
        "dispatch_path": _current_control_action_dispatch_path_for_action_type(
            action_type=action_type,
            study=study,
        ),
        "stage_packet_ref": stage_packet_ref,
        "stage_packet_refs": stage_packet_refs,
        "required_output_surface": _required_output_surface(current_work_unit),
        "owner_route_currentness_basis": basis,
        "currentness_basis": basis,
    }
    return {key: value for key, value in action.items() if value not in (None, "", [], {})}


def _current_control_action_dispatch_path_for_action_type(
    *,
    action_type: str,
    study: Mapping[str, Any],
) -> str | None:
    study_root_text = _non_empty_text(study.get("study_root"))
    study_id = _non_empty_text(study.get("study_id"))
    if study_root_text is not None:
        return str(
            (
                Path(study_root_text).expanduser().resolve()
                / OWNER_CALLABLE_ADAPTERS
                / f"{action_type}.json"
            )
        )
    if study_id is None:
        return None
    return str(
        Path("studies")
        / study_id
        / OWNER_CALLABLE_ADAPTERS
        / f"{action_type}.json"
    )


def accepted_owner_gate_admission_matches_selected_dispatch_blocker(
    *,
    study: Mapping[str, Any],
    recovery: Mapping[str, Any] | None = None,
) -> bool:
    recovery_payload = _mapping(recovery) or _mapping(study.get("paper_recovery_state"))
    if _non_empty_text(recovery_payload.get("phase")) != "admission_pending":
        return False
    next_safe_action = _mapping(recovery_payload.get("next_safe_action"))
    if _non_empty_text(next_safe_action.get("kind")) != "admit_identity_bound_stage_packet":
        return False
    if next_safe_action.get("provider_admission_allowed") is not True:
        return False
    if not _recovery_records_accepted_identity_bound_stage_packet(recovery_payload):
        return False
    if not _recovery_has_owner_gate_stage_packet_ref(recovery_payload):
        return False
    if _accepted_owner_gate_admission_event_matches_recovery_obligation(
        study,
        recovery=recovery_payload,
    ):
        return True
    current_work_unit = _mapping(study.get("current_work_unit"))
    if _non_empty_text(current_work_unit.get("status")) != "typed_blocker":
        return False
    return any(
        _is_selected_dispatch_stage_packet_blocker(reason)
        for reason in _selected_dispatch_typed_blocker_reasons(
            study,
            recovery=recovery_payload,
        )
    )


def _accepted_owner_gate_admission_event_matches_recovery_obligation(
    study: Mapping[str, Any],
    *,
    recovery: Mapping[str, Any],
) -> bool:
    event = _accepted_owner_gate_admission_event(study, recovery=recovery)
    if not event:
        return False
    payload = _mapping(event.get("payload"))
    owner_identity = _mapping(payload.get("current_owner_identity"))
    if not _is_selected_dispatch_stage_packet_blocker(
        _non_empty_text(owner_identity.get("blocker_type"))
        or _non_empty_text(owner_identity.get("blocker_id"))
        or _non_empty_text(owner_identity.get("blocked_reason"))
        or _non_empty_text(payload.get("blocker_type"))
    ):
        return False
    return _owner_gate_identity_matches_recovery_obligation(
        owner_identity,
        study=study,
        recovery=recovery,
    )


def _accepted_owner_gate_admission_event(
    study: Mapping[str, Any],
    *,
    recovery: Mapping[str, Any],
) -> dict[str, Any]:
    owner_gate_refs = {
        ref
        for ref in _text_items(recovery.get("evidence_refs"))
        if ref.startswith("owner-gate-decision:")
    }
    for item in study.get("study_intervention_events") or []:
        event = _mapping(item)
        if _non_empty_text(event.get("intent")) != "owner_gate_decision":
            continue
        payload = _mapping(event.get("payload"))
        if _non_empty_text(payload.get("decision")) != "admit_identity_bound_stage_packet":
            continue
        if payload.get("provider_admission_allowed") is not True:
            continue
        decision_ref = _non_empty_text(payload.get("owner_gate_decision_ref"))
        if owner_gate_refs and decision_ref not in owner_gate_refs:
            continue
        if _accepted_owner_gate_stage_packet_refs(recovery=recovery, owner_gate_event=event):
            return event
    return {}


def _owner_gate_identity_matches_recovery_obligation(
    identity: Mapping[str, Any],
    *,
    study: Mapping[str, Any],
    recovery: Mapping[str, Any],
) -> bool:
    obligation = _mapping(_mapping(recovery.get("current_authority")).get("obligation"))
    current_work_unit = _mapping(study.get("current_work_unit"))
    expected = {
        "study_id": _coalesce_text(
            obligation.get("study_id"),
            recovery.get("study_id"),
            study.get("study_id"),
            current_work_unit.get("study_id"),
        ),
        "action_type": _coalesce_text(
            obligation.get("action_type"),
            current_work_unit.get("action_type"),
        ),
        "work_unit_id": _coalesce_text(
            obligation.get("work_unit_id"),
            current_work_unit.get("work_unit_id"),
        ),
        "work_unit_fingerprint": _coalesce_text(
            obligation.get("work_unit_fingerprint"),
            current_work_unit.get("work_unit_fingerprint"),
            current_work_unit.get("action_fingerprint"),
        ),
    }
    for key, expected_value in expected.items():
        value = _non_empty_text(identity.get(key))
        if expected_value is not None and value != expected_value:
            return False
    return all(_non_empty_text(identity.get(key)) is not None for key in expected)


def _coalesce_text(*values: object) -> str | None:
    for value in values:
        text = _non_empty_text(value)
        if text is not None:
            return text
    return None


def _accepted_owner_gate_stage_packet_ref(
    *,
    recovery: Mapping[str, Any],
    owner_gate_event: Mapping[str, Any],
    study: Mapping[str, Any] | None = None,
) -> str | None:
    refs = _accepted_owner_gate_stage_packet_refs(
        recovery=recovery,
        owner_gate_event=owner_gate_event,
        study=study,
    )
    return refs[0] if refs else None


def _accepted_owner_gate_stage_packet_refs(
    *,
    recovery: Mapping[str, Any],
    owner_gate_event: Mapping[str, Any],
    study: Mapping[str, Any] | None = None,
) -> list[str]:
    payload = _mapping(owner_gate_event.get("payload"))
    refs = [
        _non_empty_text(payload.get("stage_packet_ref")),
        *_text_items(payload.get("stage_packet_refs")),
        *[
            ref
            for ref in _text_items(recovery.get("evidence_refs"))
            if ref.startswith("stage-packet:")
            or "stage_packet" in ref
            or "owner_callable_adapters" in ref
        ],
    ]
    result: list[str] = []
    for ref in refs:
        normalized = _stage_packet_ref_for_dispatch_path(ref, study=study)
        if normalized is not None and normalized not in result:
            result.append(normalized)
    return result


def _stage_packet_ref_for_dispatch_path(
    ref: str | None,
    *,
    study: Mapping[str, Any] | None,
) -> str | None:
    text = _non_empty_text(ref)
    if text is None:
        return None
    path = Path(text).expanduser()
    if path.is_absolute():
        return str(path)
    study_root_text = _non_empty_text(_mapping(study).get("study_root"))
    study_root = Path(study_root_text).expanduser() if study_root_text is not None else None
    study_id = _non_empty_text(_mapping(study).get("study_id"))
    if study_id is not None and study_root is not None and len(path.parts) >= 2 and path.parts[:2] == ("studies", study_id):
        workspace_root = study_root.parent.parent
        return str((workspace_root / path).resolve())
    return text


def _recovery_records_accepted_identity_bound_stage_packet(
    recovery: Mapping[str, Any],
) -> bool:
    for item in recovery.get("conditions") or []:
        condition = _mapping(item)
        if (
            _non_empty_text(condition.get("condition")) == "accepted_owner_gate_decision"
            and _non_empty_text(condition.get("decision")) == "admit_identity_bound_stage_packet"
        ):
            return True
    return False


def _recovery_has_owner_gate_stage_packet_ref(recovery: Mapping[str, Any]) -> bool:
    refs = _text_items(recovery.get("evidence_refs"))
    has_owner_gate = any(ref.startswith("owner-gate-decision:") for ref in refs)
    has_stage_packet = any(
        ref.startswith("stage-packet:")
        or "stage_packet" in ref
        or "owner_callable_adapters" in ref
        for ref in refs
    )
    return has_owner_gate and has_stage_packet


def _selected_dispatch_typed_blocker_reasons(
    study: Mapping[str, Any],
    *,
    recovery: Mapping[str, Any],
) -> list[str]:
    reasons: list[str] = []
    current_work_unit = _mapping(study.get("current_work_unit"))
    current_execution = _mapping(study.get("current_execution_envelope"))
    recovery_obligation = _mapping(_mapping(recovery.get("current_authority")).get("obligation"))
    for blocker in (
        _mapping(_mapping(current_work_unit.get("state")).get("typed_blocker")),
        _mapping(current_work_unit.get("typed_blocker")),
        _mapping(current_execution.get("typed_blocker")),
        recovery_obligation,
        _mapping(current_work_unit.get("state")),
        current_execution,
    ):
        reason = (
            _non_empty_text(blocker.get("blocker_id"))
            or _non_empty_text(blocker.get("blocker_type"))
            or _non_empty_text(blocker.get("reason"))
            or _non_empty_text(blocker.get("blocked_reason"))
        )
        if reason is not None:
            reasons.append(reason)
    return reasons


def _provider_admission_action_key(action: Mapping[str, Any]) -> tuple[str | None, str | None, str | None]:
    fingerprint = _non_empty_text(action.get("work_unit_fingerprint")) or _non_empty_text(
        action.get("action_fingerprint")
    )
    if is_current_ai_reviewer_gate_replay_fingerprint(fingerprint):
        return (
            _non_empty_text(action.get("study_id")),
            _current_action_action_type(action),
            fingerprint,
        )
    return (
        _non_empty_text(action.get("study_id")),
        _current_action_action_type(action),
        _canonical_provider_admission_work_unit_id(
            action_type=_current_action_action_type(action),
            work_unit_id=_non_empty_text(action.get("work_unit_id"))
            or _non_empty_text(action.get("next_work_unit")),
        ),
    )


def _current_action_action_type(action: Mapping[str, Any]) -> str | None:
    action_type = _non_empty_text(action.get("action_type"))
    if action_type is not None:
        return action_type
    for item in _text_items(action.get("allowed_actions")):
        if item in CURRENT_CONTROL_PROVIDER_ADMISSION_ACTION_OWNERS:
            return item
    return None


def _stable_provider_admission_ticket(
    *,
    study_id: str | None,
    action_type: str | None,
    work_unit_id: str | None,
) -> str | None:
    return control_identity.stable_current_owner_ticket_fingerprint(
        study_id=study_id,
        work_unit_id=work_unit_id,
        action_type=action_type,
    )


def _first_non_synthetic_fingerprint(*values: object) -> str | None:
    for value in values:
        text = _non_empty_text(value)
        if text is not None and not control_identity.is_synthetic_current_owner_ticket(text):
            return text
    return None


def _first_currentness_fingerprint(
    *values: object,
    study_id: str | None,
    action_type: str | None,
    work_unit_id: str | None,
) -> str | None:
    fingerprint = _first_non_synthetic_fingerprint(*values)
    if fingerprint is not None:
        return fingerprint
    stable_ticket = _stable_provider_admission_ticket(
        study_id=study_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
    )
    if stable_ticket is None:
        return None
    for value in values:
        if _non_empty_text(value) == stable_ticket:
            return stable_ticket
    return None


def _currentness_basis_can_bind_stable_ticket(basis: Mapping[str, Any]) -> bool:
    if _non_empty_text(basis.get("work_unit_id")) is None:
        return False
    if _non_empty_text(basis.get("truth_epoch")) is None:
        return False
    return (
        _non_empty_text(basis.get("runtime_health_epoch")) is not None
        or _non_empty_text(basis.get("source_eval_id")) is not None
    )


def _required_output_surface(current: Mapping[str, Any]) -> str | None:
    return (
        _non_empty_text(current.get("required_output_surface"))
        or _non_empty_text(_mapping(current.get("target_surface")).get("surface_ref"))
    )


def _current_action_can_bind_stable_ticket(
    *,
    status_payload: Mapping[str, Any],
    current: Mapping[str, Any],
    currentness_basis: Mapping[str, Any],
) -> bool:
    if _currentness_basis_can_bind_stable_ticket(currentness_basis):
        return True
    if _non_empty_text(current.get("source_ref")) is not None:
        return True
    if _non_empty_text(current.get("source_eval_id")) is not None:
        return True
    return _non_empty_text(status_payload.get("generated_at")) is not None or _non_empty_text(
        status_payload.get("study_progress_generated_at")
    ) is not None


def _status_with_current_control_study_currentness(
    *,
    status: Mapping[str, Any],
    study: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(status)
    for key in (
        "current_work_unit",
        "current_execution_envelope",
        "current_executable_owner_action",
        "current_owner_ticket",
    ):
        if _mapping(payload.get(key)):
            continue
        value = _mapping(study.get(key))
        if value:
            payload[key] = value
    if not _mapping(payload.get("current_executable_owner_action")):
        successor_action = _current_action_from_paper_recovery_successor(study)
        if successor_action:
            payload["current_executable_owner_action"] = successor_action
    if not _mapping(payload.get("current_executable_owner_action")):
        owner_gate_action = _current_action_from_accepted_owner_gate_admission(study)
        if owner_gate_action:
            payload["current_executable_owner_action"] = owner_gate_action
    return payload


def _current_action_identity(status_payload: Mapping[str, Any]) -> dict[str, Any]:
    current_work_unit = _mapping(status_payload.get("current_work_unit"))
    if _non_empty_text(current_work_unit.get("status")) == "owner_receipt_recorded":
        recovery_identity = _paper_recovery_successor_identity(status_payload)
        if recovery_identity:
            return recovery_identity
    accepted_owner_gate_identity = _accepted_owner_gate_current_action_identity(status_payload)
    if accepted_owner_gate_identity:
        return accepted_owner_gate_identity
    if current_work_unit:
        identity = _current_work_unit_identity(current_work_unit)
        if identity:
            return identity
    current = _mapping(status_payload.get("current_executable_owner_action"))
    if not current:
        return {}
    study_id = _non_empty_text(status_payload.get("study_id"))
    target_surface = _mapping(current.get("target_surface"))
    next_action = _mapping(current.get("next_action"))
    action_ids = _text_items(current.get("allowed_actions"))
    action_ids.extend(
        _text_items(
            [
                current.get("action_type"),
                current.get("work_unit_id"),
                next_action.get("action_id"),
            ]
        )
    )
    action_ids = list(dict.fromkeys(action_ids))
    work_unit_id = _non_empty_text(current.get("work_unit_id")) or _non_empty_text(
        next_action.get("action_id")
    )
    surface_key = _non_empty_text(current.get("surface_key")) or _non_empty_text(
        target_surface.get("surface_key")
    )
    source_ref = _non_empty_text(current.get("source_ref")) or _non_empty_text(
        current.get("latest_owner_answer_ref")
    )
    action_type = _current_action_action_type(current)
    current_action_basis = _mapping(current.get("owner_route_currentness_basis")) or _mapping(
        current.get("currentness_basis")
    )
    fingerprint = _first_currentness_fingerprint(
        current.get("work_unit_fingerprint"),
        current.get("action_fingerprint"),
        current.get("source_fingerprint"),
        _mapping(current.get("repair_progress_precedence")).get("source_fingerprint"),
        current_action_basis.get("work_unit_fingerprint"),
        current_action_basis.get("source_fingerprint"),
        study_id=study_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
    )
    if fingerprint is None and _current_action_can_bind_stable_ticket(
        status_payload=status_payload,
        current=current,
        currentness_basis=current_action_basis,
    ):
        fingerprint = _stable_provider_admission_ticket(
            study_id=study_id,
            action_type=action_type,
            work_unit_id=work_unit_id,
        )
    fingerprints: list[str] = []
    if fingerprint is not None:
        fingerprints.append(fingerprint)
    if work_unit_id is not None and source_ref is not None:
        fingerprints.append(
            "stage-current-owner-delta::"
            f"{work_unit_id}::{surface_key or 'unspecified_surface'}::{source_ref}"
        )
    repair_precedence = _mapping(current.get("repair_progress_precedence"))
    repair_fingerprint = _non_empty_text(repair_precedence.get("source_fingerprint"))
    if repair_fingerprint is not None:
        fingerprints.append(repair_fingerprint)
    ticket = _mapping(status_payload.get("current_owner_ticket"))
    for item in ticket.get("required_input_refs") or []:
        text = _non_empty_text(item)
        if text is not None and text.startswith("sha256:"):
            fingerprints.append(text)
    fingerprints = list(dict.fromkeys(fingerprints))
    if fingerprint is None and fingerprints:
        fingerprint = fingerprints[0]
    basis = _current_action_currentness_basis(
        status_payload=status_payload,
        current=current,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=fingerprint,
    )
    return {
        "action_ids": action_ids,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "work_unit_fingerprints": fingerprints,
        "source_ref": source_ref,
        "source": _non_empty_text(current.get("source")),
        "next_owner": _non_empty_text(current.get("next_owner")),
        "currentness_basis": basis if basis else None,
    }


def _accepted_owner_gate_current_action_identity(status_payload: Mapping[str, Any]) -> dict[str, Any]:
    current = _mapping(status_payload.get("current_executable_owner_action"))
    if _non_empty_text(current.get("source")) != ACCEPTED_OWNER_GATE_DECISION_SOURCE:
        return {}
    action_type = _current_action_action_type(current)
    work_unit_id = _non_empty_text(current.get("work_unit_id")) or _non_empty_text(
        current.get("next_work_unit")
    )
    current_action_basis = _mapping(current.get("owner_route_currentness_basis")) or _mapping(
        current.get("currentness_basis")
    )
    fingerprint = _first_currentness_fingerprint(
        current.get("work_unit_fingerprint"),
        current.get("action_fingerprint"),
        current.get("source_fingerprint"),
        current_action_basis.get("work_unit_fingerprint"),
        current_action_basis.get("source_fingerprint"),
        study_id=_non_empty_text(status_payload.get("study_id")),
        action_type=action_type,
        work_unit_id=work_unit_id,
    )
    if action_type is None or work_unit_id is None or fingerprint is None:
        return {}
    basis = _current_action_currentness_basis(
        status_payload=status_payload,
        current=current,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=fingerprint,
    )
    return {
        "action_ids": [action_type, work_unit_id],
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "work_unit_fingerprints": [fingerprint],
        "source_ref": _non_empty_text(current.get("source_ref")),
        "source": ACCEPTED_OWNER_GATE_DECISION_SOURCE,
        "next_owner": _non_empty_text(current.get("next_owner")),
        "currentness_basis": basis if basis else None,
    }


def _paper_recovery_successor_identity(status_payload: Mapping[str, Any]) -> dict[str, Any]:
    recovery_action = _current_action_from_paper_recovery_successor(status_payload)
    if not recovery_action:
        return {}
    return _current_control_action_identity(
        {
            **recovery_action,
            "study_id": _non_empty_text(status_payload.get("study_id")),
            "quest_id": _non_empty_text(status_payload.get("quest_id")),
            "source_surface": "opl_current_control_state.study_current_executable_owner_action",
            "next_executable_owner": _non_empty_text(recovery_action.get("next_owner")),
            "owner_route": {
                "next_owner": _non_empty_text(recovery_action.get("next_owner")),
                "allowed_actions": [
                    action
                    for action in (_current_action_action_type(recovery_action),)
                    if action is not None
                ],
                "work_unit_fingerprint": _non_empty_text(
                    recovery_action.get("work_unit_fingerprint")
                )
                or _non_empty_text(recovery_action.get("action_fingerprint")),
                "source_refs": {
                    "work_unit_id": _non_empty_text(recovery_action.get("work_unit_id"))
                    or _non_empty_text(recovery_action.get("next_work_unit")),
                    "work_unit_fingerprint": _non_empty_text(
                        recovery_action.get("work_unit_fingerprint")
                    )
                    or _non_empty_text(recovery_action.get("action_fingerprint")),
                    "owner_route_currentness_basis": _mapping(
                        recovery_action.get("owner_route_currentness_basis")
                    )
                    or _mapping(recovery_action.get("currentness_basis")),
                },
            },
        }
    )


def _current_control_action_identity(action: Mapping[str, Any]) -> dict[str, Any]:
    if _non_empty_text(action.get("source_surface")) not in {
        None,
        "opl_current_control_state.action_queue",
        "opl_current_control_state.study_current_executable_owner_action",
        "opl_current_control_state.study_current_work_unit",
    }:
        return {}
    action_type = _current_action_action_type(action)
    work_unit_id = (
        _non_empty_text(action.get("work_unit_id"))
        or _non_empty_text(action.get("next_work_unit"))
        or _non_empty_text(action.get("controller_work_unit_id"))
    )
    fingerprint = (
        _non_empty_text(action.get("work_unit_fingerprint"))
        or _non_empty_text(action.get("action_fingerprint"))
        or _non_empty_text(action.get("source_fingerprint"))
    )
    owner_route = _mapping(action.get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    if not _owner_route_currentness_basis_complete(currentness_basis):
        return {}
    work_unit_id = (
        work_unit_id
        or _non_empty_text(source_refs.get("work_unit_id"))
        or _non_empty_text(currentness_basis.get("work_unit_id"))
    )
    fingerprint = (
        fingerprint
        or _non_empty_text(source_refs.get("work_unit_fingerprint"))
        or _non_empty_text(currentness_basis.get("work_unit_fingerprint"))
    )
    if action_type is None or work_unit_id is None or fingerprint is None:
        return {}
    if not _current_control_action_requests_provider_admission(action):
        return {}
    fingerprints = [
        item
        for item in (
            _non_empty_text(action.get("work_unit_fingerprint")),
            _non_empty_text(action.get("action_fingerprint")),
            _non_empty_text(action.get("source_fingerprint")),
            _non_empty_text(source_refs.get("work_unit_fingerprint")),
            _non_empty_text(currentness_basis.get("work_unit_fingerprint")),
        )
        if item is not None
    ]
    return {
        "action_ids": [action_type, work_unit_id],
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "work_unit_fingerprints": list(dict.fromkeys(fingerprints)),
        "source": _non_empty_text(action.get("source_surface"))
        or "opl_current_control_state.action_queue",
        "next_owner": _non_empty_text(action.get("next_executable_owner"))
        or _non_empty_text(action.get("owner"))
        or _non_empty_text(owner_route.get("next_owner")),
    }


def _current_work_unit_identity(current_work_unit: Mapping[str, Any]) -> dict[str, Any]:
    status = _non_empty_text(current_work_unit.get("status"))
    if status not in {"executable_owner_action", "typed_blocker"}:
        return {}
    opl_authorization_typed_blocker = (
        status == "typed_blocker"
        and _current_work_unit_opl_authorization_required(current_work_unit)
    )
    if status == "typed_blocker" and not opl_authorization_typed_blocker:
        return {}
    state = _mapping(current_work_unit.get("state"))
    currentness_basis = _mapping(current_work_unit.get("currentness_basis"))
    action_type = _non_empty_text(current_work_unit.get("action_type"))
    work_unit_id = _non_empty_text(current_work_unit.get("work_unit_id"))
    source_eval_id = current_ai_reviewer_gate_replay_source_eval_id(
        study={"current_work_unit": current_work_unit},
        current={},
        action_type=action_type,
        work_unit_id=work_unit_id,
    )
    eval_bound_fingerprint = current_ai_reviewer_gate_replay_fingerprint(
        study_id=_non_empty_text(current_work_unit.get("study_id")),
        action_type=action_type,
        work_unit_id=work_unit_id,
        source_eval_id=source_eval_id,
    )
    fingerprint = _first_currentness_fingerprint(
        current_work_unit.get("work_unit_fingerprint"),
        current_work_unit.get("action_fingerprint"),
        currentness_basis.get("work_unit_fingerprint"),
        currentness_basis.get("source_fingerprint"),
        study_id=_non_empty_text(current_work_unit.get("study_id")),
        action_type=action_type,
        work_unit_id=work_unit_id,
    )
    if fingerprint is None:
        fingerprint = eval_bound_fingerprint
    elif (
        eval_bound_fingerprint is not None
        and control_identity.is_synthetic_current_owner_ticket(fingerprint)
    ):
        fingerprint = eval_bound_fingerprint
    fingerprints = [
        item
        for item in (
            eval_bound_fingerprint,
            _non_empty_text(current_work_unit.get("work_unit_fingerprint")),
            _non_empty_text(current_work_unit.get("action_fingerprint")),
            _non_empty_text(currentness_basis.get("work_unit_fingerprint")),
            _non_empty_text(currentness_basis.get("source_fingerprint")),
        )
        if item is not None
        and (
            not control_identity.is_synthetic_current_owner_ticket(item)
            or item == fingerprint
        )
    ]
    return {
        "action_ids": [item for item in (action_type, work_unit_id) if item is not None],
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "work_unit_fingerprints": list(dict.fromkeys(fingerprints)),
        "source_ref": _non_empty_text(state.get("source_ref")),
        "source": _non_empty_text(state.get("source")) or "canonical_current_work_unit",
        "next_owner": _non_empty_text(current_work_unit.get("owner")),
        "opl_execution_authorization_required": opl_authorization_typed_blocker,
    }


def _canonical_provider_admission_work_unit_id(
    *,
    action_type: str | None,
    work_unit_id: str | None,
) -> str | None:
    if action_type == "run_gate_clearing_batch" and work_unit_id in PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS:
        return "publication_gate_replay"
    return work_unit_id


def _current_control_action_requests_provider_admission(action: Mapping[str, Any]) -> bool:
    action_type = _non_empty_text(action.get("action_type"))
    if action_type is None:
        return False
    if _non_empty_text(action.get("status")) not in {
        "queued",
        "pending",
        "ready",
        "transition_request_pending",
    }:
        return False
    owner = _non_empty_text(action.get("next_executable_owner")) or _non_empty_text(action.get("owner"))
    return _current_control_executable_owner(action_type=action_type, owner=owner) is not None


def _current_control_owner_allowed(*, action_type: str, owner: str | None) -> bool:
    expected_owners = CURRENT_CONTROL_PROVIDER_ADMISSION_ACTION_OWNERS.get(action_type)
    return owner in expected_owners if expected_owners is not None else False


def _current_control_executable_owner(
    *,
    action_type: str,
    owner: str | None,
    dispatch_payload: Mapping[str, Any] | None = None,
    owner_route: Mapping[str, Any] | None = None,
) -> str | None:
    if _current_control_owner_allowed(action_type=action_type, owner=owner):
        return owner
    if owner not in OPL_RUNTIME_ROUTE_OWNERS:
        return None
    for candidate in (
        _non_empty_text(_mapping(dispatch_payload).get("next_executable_owner")),
        _non_empty_text(_mapping(owner_route).get("next_owner")),
        CURRENT_CONTROL_PROVIDER_ADMISSION_DEFAULT_EXECUTABLE_OWNERS.get(action_type),
    ):
        if _current_control_owner_allowed(action_type=action_type, owner=candidate):
            return candidate
    return None


def _dispatch_authority_allows_current_control_provider_admission(
    *,
    action_type: str,
    dispatch_authority: str | None,
) -> bool:
    allowed = CURRENT_CONTROL_PROVIDER_ADMISSION_DISPATCH_AUTHORITIES.get(action_type)
    return dispatch_authority in allowed if allowed is not None else False


def _current_control_action_dispatch_path(
    action: Mapping[str, Any],
    *,
    study_root: Path,
    action_type: str,
) -> Path | None:
    explicit = handoff_dispatch_path(action)
    if explicit is not None:
        return _resolve_dispatch_ref(explicit, study_root=study_root)
    root = Path(study_root).expanduser().resolve()
    for relative_root in (
        PAPER_PROGRESS_TRANSITION_REQUESTS,
        OWNER_CALLABLE_ADAPTERS,
    ):
        candidate = root / relative_root / f"{action_type}.json"
        if candidate.exists():
            return candidate
    return root / PAPER_PROGRESS_TRANSITION_REQUESTS / f"{action_type}.json"


def _resolve_dispatch_ref(ref: str, *, study_root: Path) -> Path:
    path = Path(ref).expanduser()
    if path.is_absolute():
        return path.resolve()
    root = Path(study_root).expanduser().resolve()
    study_id = root.name
    if len(path.parts) >= 2 and path.parts[:2] == ("studies", study_id):
        return (root.parent.parent / path).resolve()
    return (root / path).resolve()


def _merge_owner_route_currentness(
    *,
    dispatch_payload: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    work_unit_id: str,
    work_unit_fingerprint: str,
) -> dict[str, Any]:
    route = _mapping(dispatch_payload.get("owner_route"))
    if not route:
        route = dict(owner_route)
    basis = currentness_identity.normalize_currentness_sources(
        currentness_identity.owner_route_basis(route),
        currentness_identity.owner_route_basis(owner_route),
        {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
        },
    )
    route = currentness_identity.with_owner_route_basis(route, basis=basis)
    source_refs = {
        **_mapping(route.get("source_refs")),
        **{
            key: value
            for key, value in _mapping(owner_route.get("source_refs")).items()
            if key not in _mapping(route.get("source_refs")) or key == "owner_route_currentness_basis"
        },
    }
    source_refs["owner_route_currentness_basis"] = currentness_identity.normalize_currentness_sources(
        source_refs.get("owner_route_currentness_basis"),
        basis,
    )
    route["source_refs"] = source_refs
    route["work_unit_fingerprint"] = work_unit_fingerprint
    return route
