from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.domain_health_diagnostic_parts import provider_admission
from med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback import (
    candidate_opl_transition_readback as _candidate_opl_transition_readback,
    has_opl_transition_readback as _has_opl_transition_readback,
)
from med_autoscience.controllers.current_work_unit import action_supersedes_typed_blocker

from .owner_action_admission import provider_attempt_proof_for_current_action
from .paper_autonomy_supervisor_decision import (
    provider_admission_supervisor_gate,
    supervisor_block_projection,
)
from .shared import _mapping_copy, _non_empty_text

_REQUEST_ONLY_OWNER_ACTION_SOURCES = {
    "gate_clearing_batch_followthrough.actionable_current_work_unit",
    "paper_recovery_state.next_safe_action.successor_owner_action",
}
_OPL_TRANSITION_LIVE_READBACK_SOURCE = "opl_domain_progress_transition_runtime_live_readback"


def provider_admission_projection_fields(
    *,
    payload: Mapping[str, Any],
    handoff: Mapping[str, Any],
    study_root: Path,
) -> dict[str, Any]:
    running_proof = _handoff_running_proof_consumes_provider_admission(
        payload=payload,
        handoff=handoff,
    )
    if running_proof is not None:
        return running_proof
    terminal_closeout = _handoff_terminal_closeout_consumes_provider_admission(
        payload=payload,
        handoff=handoff,
    )
    if terminal_closeout is not None:
        return terminal_closeout
    handoff_fields = _identity_bound_handoff_provider_admission_fields(
        handoff=handoff,
        payload=payload,
        study_root=study_root,
    )
    if handoff_fields is not None:
        return handoff_fields
    if _handoff_typed_blocker_consumes_current_action(payload=payload, handoff=handoff):
        return {
            "provider_admission_pending_count": 0,
            "provider_admission_candidates": [],
        }
    current_control_payload = _current_control_payload_for_provider_admission(
        payload=payload,
        handoff=handoff,
    )
    candidates = provider_admission.current_control_provider_admission_candidates(
        current_control_payload,
        study_root=study_root,
        status_payload=payload,
        current_control_ref=_non_empty_text(_mapping_copy(handoff.get("refs")).get("latest_path"))
        or _non_empty_text(handoff.get("source_path")),
    )
    normalized_candidates = [
        _candidate_with_opl_runtime_readback(
            _transition_request_only_candidate(candidate)
            if _request_only_owner_action_candidate(candidate)
            else dict(candidate),
            study_root=study_root,
        )
        for candidate in candidates
    ]
    provider_admission_candidates = [
        candidate
        for candidate in normalized_candidates
        if _has_opl_transition_readback(candidate)
        and not _request_only_owner_action_candidate(candidate)
    ]
    transition_request_candidates = [
        candidate
        for candidate in normalized_candidates
        if not (
            _has_opl_transition_readback(candidate)
            and not _request_only_owner_action_candidate(candidate)
        )
    ]
    gate_payload = {
        **dict(payload),
        "provider_admission_pending_count": len(provider_admission_candidates),
        "provider_admission_candidates": provider_admission_candidates,
        "transition_request_pending_count": len(transition_request_candidates),
        "transition_request_candidates": list(transition_request_candidates),
    }
    supervisor_gate = provider_admission_supervisor_gate(gate_payload)
    if supervisor_gate.get("blocked") is True:
        supervisor_decision = _mapping_copy(supervisor_gate.get("supervisor_decision"))
        return {
            "provider_admission_pending_count": 0,
            "provider_admission_candidates": [],
            "transition_request_pending_count": len(transition_request_candidates),
            "transition_request_candidates": list(transition_request_candidates),
            "paper_autonomy_supervisor_decision": supervisor_decision,
            "provider_admission_blocked_by_supervisor_decision": supervisor_block_projection(supervisor_gate),
        }
    return {
        "provider_admission_pending_count": len(provider_admission_candidates),
        "provider_admission_candidates": provider_admission_candidates,
        "transition_request_pending_count": len(transition_request_candidates),
        "transition_request_candidates": list(transition_request_candidates),
    }


def _request_only_owner_action_candidate(candidate: Mapping[str, Any]) -> bool:
    if _non_empty_text(candidate.get("opl_transition_readback_source")) == _OPL_TRANSITION_LIVE_READBACK_SOURCE:
        return False
    basis = _mapping_copy(candidate.get("currentness_basis"))
    source_refs = _mapping_copy(candidate.get("source_refs"))
    source = (
        _non_empty_text(candidate.get("mas_owner_action_source"))
        or _non_empty_text(source_refs.get("mas_owner_action_source"))
        or _non_empty_text(basis.get("mas_owner_action_source"))
        or _non_empty_text(basis.get("source"))
    )
    return source in _REQUEST_ONLY_OWNER_ACTION_SOURCES


def _candidate_with_opl_runtime_readback(
    candidate: Mapping[str, Any],
    *,
    study_root: Path,
) -> dict[str, Any]:
    payload = dict(candidate)
    inline_readback = _candidate_opl_transition_readback(payload)
    if inline_readback:
        payload["opl_transition_readback_source"] = _opl_transition_readback_source(inline_readback)
        payload["status"] = "provider_admission_pending"
        payload["provider_admission_pending"] = True
        payload["provider_attempt_or_lease_required"] = True
        payload["provider_admission_requires_opl_runtime_result"] = False
    return payload


def _opl_transition_readback_source(readback: Mapping[str, Any]) -> str:
    return _OPL_TRANSITION_LIVE_READBACK_SOURCE


def _transition_request_only_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(candidate)
    for key in (
        "opl_domain_progress_transition_result",
        "opl_domain_progress_transition_live_readback",
        "opl_domain_progress_transition_runtime_live_readback",
        "opl_domain_progress_runtime_result",
        "opl_runtime_result",
    ):
        payload.pop(key, None)
    payload["status"] = "transition_request_pending"
    payload["provider_admission_pending"] = False
    payload["provider_attempt_or_lease_required"] = False
    payload["provider_admission_requires_opl_runtime_result"] = True
    payload["opl_transition_runtime_required"] = True
    return payload


def _handoff_running_proof_consumes_provider_admission(
    *,
    payload: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> dict[str, Any] | None:
    current_action = _mapping_copy(payload.get("current_executable_owner_action"))
    if not current_action:
        return None
    proof = provider_attempt_proof_for_current_action(
        handoff=handoff,
        current_action=current_action,
    )
    if proof is None:
        return None
    return {
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
        "transition_request_pending_count": 0,
        "transition_request_candidates": [],
        "provider_admission_running_proof_consumed": {
            "surface_kind": "provider_admission_running_proof_consumed",
            "source": "opl_current_control_state_handoff.running_provider_attempt",
            "status": "running_provider_attempt",
            "running_provider_attempt": True,
            "provider_attempt_proof": proof,
            "action_type": _non_empty_text(current_action.get("action_type")),
            "work_unit_id": _non_empty_text(current_action.get("work_unit_id"))
            or _non_empty_text(current_action.get("next_work_unit")),
            "work_unit_fingerprint": _non_empty_text(current_action.get("work_unit_fingerprint"))
            or _non_empty_text(current_action.get("action_fingerprint")),
            "authority_boundary": {
                "projection_only": True,
                "runtime_owner": "one-person-lab",
                "domain_truth_owner": "med-autoscience",
                "can_authorize_provider_admission": False,
                "can_start_provider_attempt": False,
                "provider_running_is_paper_progress": False,
                "provider_completion_is_domain_completion": False,
            },
        },
    }


def _handoff_terminal_closeout_consumes_provider_admission(
    *,
    payload: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> dict[str, Any] | None:
    typed_blocker = _handoff_terminal_typed_blocker(handoff)
    if not typed_blocker:
        return None
    current_action = _mapping_copy(payload.get("current_executable_owner_action"))
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    if not (
        _same_action_identity(current_work_unit, typed_blocker)
        or (current_action and _same_action_identity(current_action, typed_blocker))
    ):
        return None
    if current_action and action_supersedes_typed_blocker(
        action=current_action,
        blocker=typed_blocker,
        progress=payload,
    ):
        return None
    latest_terminal_stage_log = _mapping_copy(handoff.get("latest_terminal_stage_log"))
    return {
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
        "transition_request_pending_count": 0,
        "transition_request_candidates": [],
        "provider_admission_terminal_closeout_consumed": {
            "surface_kind": "provider_admission_terminal_closeout_consumed",
            "source": "opl_current_control_state_handoff.latest_terminal_stage_log",
            "stage_attempt_id": _non_empty_text(typed_blocker.get("stage_attempt_id"))
            or _non_empty_text(latest_terminal_stage_log.get("stage_attempt_id")),
            "blocker_type": _non_empty_text(typed_blocker.get("blocker_type"))
            or _non_empty_text(typed_blocker.get("blocked_reason"))
            or _non_empty_text(typed_blocker.get("blocker_id")),
            "typed_blocker": dict(typed_blocker),
            "latest_terminal_stage_log": latest_terminal_stage_log or None,
            "authority_boundary": {
                "projection_only": True,
                "runtime_owner": "one-person-lab",
                "domain_truth_owner": "med-autoscience",
                "can_authorize_provider_admission": False,
                "can_start_provider_attempt": False,
                "provider_completion_is_domain_completion": False,
            },
        },
    }


def _handoff_terminal_typed_blocker(handoff: Mapping[str, Any]) -> dict[str, Any]:
    typed_blocker = _mapping_copy(handoff.get("typed_blocker"))
    if not typed_blocker:
        handoff_work_unit = _mapping_copy(handoff.get("current_work_unit"))
        handoff_state = _mapping_copy(handoff_work_unit.get("state"))
        typed_blocker = (
            _mapping_copy(handoff_state.get("typed_blocker"))
            or _mapping_copy(handoff_work_unit.get("typed_blocker"))
        )
    if not typed_blocker:
        handoff_envelope = _mapping_copy(handoff.get("current_execution_envelope"))
        typed_blocker = _mapping_copy(handoff_envelope.get("typed_blocker"))
    if not typed_blocker:
        return {}
    latest_terminal_stage_log = _mapping_copy(handoff.get("latest_terminal_stage_log"))
    if _non_empty_text(typed_blocker.get("stage_attempt_id")) is not None:
        return typed_blocker
    if _non_empty_text(latest_terminal_stage_log.get("stage_attempt_id")) is None:
        return {}
    return {
        **typed_blocker,
        "stage_attempt_id": _non_empty_text(latest_terminal_stage_log.get("stage_attempt_id")),
    }


def _identity_bound_handoff_provider_admission_fields(
    *,
    handoff: Mapping[str, Any],
    payload: Mapping[str, Any],
    study_root: Path,
) -> dict[str, Any] | None:
    candidates = [
        _candidate_with_opl_runtime_readback(dict(item), study_root=study_root)
        for item in handoff.get("provider_admission_candidates") or []
        if isinstance(item, Mapping)
        and _has_opl_transition_readback(item)
    ]
    pending_count = int(handoff.get("provider_admission_pending_count") or 0)
    if pending_count <= 0 and not candidates:
        return None
    current_action = _mapping_copy(payload.get("current_executable_owner_action"))
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    if _non_empty_text(current_work_unit.get("status")) not in {
        "executable_owner_action",
        "owner_receipt_recorded",
    }:
        return None
    matching = [
        item
        for item in candidates
        if _same_action_identity(current_action, item) or _same_action_identity(current_work_unit, item)
    ]
    if not matching:
        return None
    return {
        "provider_admission_pending_count": len(matching),
        "provider_admission_candidates": matching,
        "transition_request_pending_count": 0,
        "transition_request_candidates": [],
    }


def _handoff_typed_blocker_consumes_current_action(
    *,
    payload: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> bool:
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    if _non_empty_text(current_work_unit.get("status")) != "executable_owner_action":
        return False
    current_action = _mapping_copy(payload.get("current_executable_owner_action"))
    if not current_action:
        return False
    handoff_work_unit = _mapping_copy(handoff.get("current_work_unit"))
    handoff_envelope = _mapping_copy(handoff.get("current_execution_envelope"))
    if _non_empty_text(handoff_work_unit.get("status")) not in {"typed_blocker", "blocked_current_work_unit"} and (
        _non_empty_text(handoff_envelope.get("state_kind")) != "typed_blocker"
    ):
        return False
    handoff_state = _mapping_copy(handoff_work_unit.get("state"))
    if (
        _non_empty_text(handoff_state.get("source")) != "accepted_closeout_consumed_pending"
        and _non_empty_text(handoff_envelope.get("source")) != "accepted_closeout_consumed_pending"
    ):
        return False
    typed_blocker = _mapping_copy(handoff_state.get("typed_blocker"))
    if not typed_blocker:
        typed_blocker = _mapping_copy(handoff_work_unit.get("typed_blocker"))
    if not typed_blocker:
        typed_blocker = _mapping_copy(handoff_envelope.get("typed_blocker"))
    if not typed_blocker:
        return False
    if action_supersedes_typed_blocker(
        action=current_action,
        blocker=typed_blocker,
        progress=payload,
    ):
        return False
    return _same_action_identity(current_work_unit, typed_blocker) or _same_action_identity(
        current_action,
        typed_blocker,
    )


def _same_action_identity(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    left_action = _non_empty_text(left.get("action_type"))
    right_action = _non_empty_text(right.get("action_type"))
    if left_action is not None and right_action is not None and left_action != right_action:
        return False
    left_work_unit = _non_empty_text(left.get("work_unit_id")) or _non_empty_text(left.get("next_work_unit"))
    right_work_unit = _non_empty_text(right.get("work_unit_id")) or _non_empty_text(right.get("next_work_unit"))
    if left_work_unit is not None and right_work_unit is not None and left_work_unit != right_work_unit:
        return False
    left_fingerprint = _non_empty_text(left.get("work_unit_fingerprint")) or _non_empty_text(
        left.get("action_fingerprint")
    )
    right_fingerprint = _non_empty_text(right.get("work_unit_fingerprint")) or _non_empty_text(
        right.get("action_fingerprint")
    )
    if left_fingerprint is not None and right_fingerprint is not None and left_fingerprint != right_fingerprint:
        return False
    return (
        left_action is not None
        and right_action is not None
        and left_work_unit is not None
        and right_work_unit is not None
        and left_fingerprint is not None
        and right_fingerprint is not None
    )


def _current_control_payload_for_provider_admission(
    *,
    payload: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> dict[str, Any]:
    current_control = _mapping_copy(handoff)
    study_action = _study_current_executable_owner_action(payload)
    if study_action:
        studies = [item for item in current_control.get("studies") or [] if isinstance(item, Mapping)]
        study_id = _non_empty_text(payload.get("study_id")) or _non_empty_text(study_action.get("study_id"))
        studies = [
            {**dict(item), **study_action} if _non_empty_text(item.get("study_id")) == study_id else item
            for item in studies
        ]
        if not any(_non_empty_text(item.get("study_id")) == study_id for item in studies):
            studies.append(study_action)
        current_control["studies"] = studies
    return current_control


def _study_current_executable_owner_action(payload: Mapping[str, Any]) -> dict[str, Any]:
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    if _non_empty_text(current_work_unit.get("status")) != "executable_owner_action":
        return {}
    current_action = _mapping_copy(payload.get("current_executable_owner_action"))
    if not current_action:
        return {}
    currentness_basis = _provider_admission_currentness_basis(
        payload=payload,
        current_action=current_action,
        current_work_unit=current_work_unit,
    )
    study_id = _non_empty_text(payload.get("study_id")) or _non_empty_text(current_work_unit.get("study_id"))
    work_unit_id = _non_empty_text(current_work_unit.get("work_unit_id")) or _non_empty_text(
        current_action.get("work_unit_id")
    )
    work_unit_fingerprint = _non_empty_text(current_work_unit.get("work_unit_fingerprint")) or _non_empty_text(
        current_action.get("work_unit_fingerprint")
    )
    action_fingerprint = _non_empty_text(current_work_unit.get("action_fingerprint")) or _non_empty_text(
        current_action.get("action_fingerprint")
    )
    source_refs = {
        key: value
        for key, value in {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": action_fingerprint,
            "mas_owner_action_source": _non_empty_text(current_action.get("source")),
            "owner_route_currentness_basis": currentness_basis or None,
        }.items()
        if value not in (None, "", [], {})
    }
    return {
        "study_id": study_id,
        "quest_id": _non_empty_text(payload.get("quest_id")) or _non_empty_text(current_work_unit.get("quest_id")),
        "current_work_unit": current_work_unit,
        "current_execution_envelope": _mapping_copy(payload.get("current_execution_envelope")),
        "current_executable_owner_action": current_action,
        "mas_owner_action_source": _non_empty_text(current_action.get("source")),
        "owner_route": {
            "next_owner": _non_empty_text(current_action.get("next_owner"))
            or _non_empty_text(current_work_unit.get("owner")),
            "allowed_actions": _text_list(current_action.get("allowed_actions"))
            or _text_list(current_work_unit.get("action_type")),
            "work_unit_fingerprint": work_unit_fingerprint,
            "source_refs": source_refs,
        },
    }


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = _non_empty_text(value)
        return [text] if text is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    items: list[str] = []
    for item in value:
        text = _non_empty_text(item)
        if text is not None and text not in items:
            items.append(text)
    return items


def _provider_admission_currentness_basis(
    *,
    payload: Mapping[str, Any],
    current_action: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
) -> dict[str, Any]:
    generated_at = _non_empty_text(payload.get("study_progress_generated_at")) or _non_empty_text(
        payload.get("generated_at")
    )
    basis = {
        **_mapping_copy(current_work_unit.get("currentness_basis")),
        **_mapping_copy(current_action.get("currentness_basis")),
        **_mapping_copy(current_action.get("owner_route_currentness_basis")),
    }
    source = _non_empty_text(current_action.get("source"))
    basis = {
        **basis,
        "source": _non_empty_text(basis.get("source")) or source,
        "mas_owner_action_source": _non_empty_text(basis.get("mas_owner_action_source")) or source,
        "source_eval_id": _non_empty_text(basis.get("source_eval_id"))
        or _non_empty_text(current_action.get("source_eval_id")),
        "source_ref": _non_empty_text(basis.get("source_ref")) or _non_empty_text(current_action.get("source_ref")),
        "source_surface": _non_empty_text(basis.get("source_surface"))
        or _non_empty_text(current_action.get("source_surface")),
        "work_unit_id": _non_empty_text(basis.get("work_unit_id"))
        or _non_empty_text(current_work_unit.get("work_unit_id"))
        or _non_empty_text(current_action.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(basis.get("work_unit_fingerprint"))
        or _non_empty_text(current_work_unit.get("work_unit_fingerprint"))
        or _non_empty_text(current_action.get("work_unit_fingerprint"))
        or _non_empty_text(current_action.get("action_fingerprint")),
        "truth_epoch": _non_empty_text(basis.get("truth_epoch"))
        or _non_empty_text(current_action.get("truth_epoch"))
        or generated_at,
        "runtime_health_epoch": _non_empty_text(basis.get("runtime_health_epoch"))
        or _non_empty_text(current_action.get("runtime_health_epoch"))
        or generated_at,
    }
    return {key: value for key, value in basis.items() if value not in (None, "", [], {})}
