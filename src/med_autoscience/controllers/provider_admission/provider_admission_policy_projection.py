from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers import paper_progress_policy_adapter
from med_autoscience.controllers.opl_transition_readback import (
    candidate_opl_transition_readback,
)
from med_autoscience.controllers.provider_admission.provider_admission_helpers import (
    mapping as _mapping,
    non_empty_text as _non_empty_text,
)


def candidate_with_paper_progress_policy_result(
    candidate: Mapping[str, Any],
    *,
    execution: Mapping[str, Any],
) -> dict[str, Any]:
    candidate_with_readback = dict(candidate)
    for key in (
        "opl_domain_progress_transition_result",
        "opl_domain_progress_runtime_result",
        "opl_runtime_result",
    ):
        readback = _mapping(execution.get(key)) or _mapping(candidate.get(key))
        if readback:
            candidate_with_readback[key] = dict(readback)
    existing_policy = _mapping(execution.get("paper_progress_policy_result")) or _mapping(
        candidate_with_readback.get("paper_progress_policy_result")
    )
    existing_transition_request = _mapping(
        existing_policy.get("opl_domain_progress_transition_request")
    )
    has_readback = bool(candidate_opl_transition_readback(candidate_with_readback))
    existing_transition_kind = _non_empty_text(
        existing_transition_request.get("recommended_transition_kind")
    )
    existing_policy_matches_readback = (
        not has_readback
        or existing_transition_kind == paper_progress_policy_adapter.START_PROVIDER_ATTEMPT
    )
    if existing_policy and existing_transition_request and existing_policy_matches_readback:
        policy_result = existing_policy
    else:
        policy_result = paper_progress_policy_adapter.build_policy_result(
            _paper_progress_policy_payload(candidate_with_readback, execution=execution),
            source="domain_diagnostic.provider_admission_candidate",
        )
    if not policy_result:
        return dict(candidate_with_readback)
    payload = {
        **dict(candidate_with_readback),
        "paper_progress_policy_result": dict(policy_result),
        "opl_domain_progress_transition_request": _mapping(
            policy_result.get("opl_domain_progress_transition_request")
        ),
    }
    return with_readback_backed_status(payload)


def with_readback_backed_status(candidate: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(candidate)
    has_readback = bool(candidate_opl_transition_readback(payload))
    if has_readback:
        payload["status"] = "provider_admission_pending"
        payload["provider_admission_pending"] = True
        payload["provider_attempt_or_lease_required"] = True
        payload["provider_admission_requires_opl_runtime_result"] = False
        return payload
    payload["status"] = "transition_request_pending"
    payload["provider_admission_pending"] = False
    payload["provider_attempt_or_lease_required"] = False
    payload["provider_admission_requires_opl_runtime_result"] = True
    payload["opl_transition_runtime_required"] = True
    return payload


def _paper_progress_policy_payload(
    candidate: Mapping[str, Any],
    *,
    execution: Mapping[str, Any],
) -> dict[str, Any]:
    currentness_basis = _mapping(candidate.get("currentness_basis"))
    current_action = {
        "surface_kind": "current_executable_owner_action",
        "status": "ready",
        "source": _non_empty_text(candidate.get("source")) or _non_empty_text(execution.get("source")),
        "next_owner": _non_empty_text(candidate.get("next_executable_owner"))
        or _non_empty_text(execution.get("next_executable_owner")),
        "owner": _non_empty_text(candidate.get("next_executable_owner"))
        or _non_empty_text(execution.get("next_executable_owner")),
        "action_type": _non_empty_text(candidate.get("action_type")),
        "work_unit_id": _non_empty_text(candidate.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(candidate.get("work_unit_fingerprint")),
        "action_fingerprint": _non_empty_text(candidate.get("action_fingerprint"))
        or _non_empty_text(candidate.get("work_unit_fingerprint")),
        "currentness_basis": dict(currentness_basis) if currentness_basis else None,
    }
    current_work_unit = {
        "surface_kind": "current_work_unit",
        "status": "executable_owner_action",
        "owner": current_action["next_owner"],
        "action_type": current_action["action_type"],
        "work_unit_id": current_action["work_unit_id"],
        "work_unit_fingerprint": current_action["work_unit_fingerprint"],
        "action_fingerprint": current_action["action_fingerprint"],
        "currentness_basis": dict(currentness_basis) if currentness_basis else None,
    }
    return {
        "study_id": _non_empty_text(candidate.get("study_id")),
        "quest_id": _non_empty_text(candidate.get("quest_id")),
        "current_work_unit": current_work_unit,
        "current_executable_owner_action": current_action,
        "paper_recovery_state": _provider_admission_recovery(candidate),
    }


def _provider_admission_recovery(candidate: Mapping[str, Any]) -> dict[str, Any]:
    has_readback = bool(candidate_opl_transition_readback(candidate))
    if not has_readback:
        return {
            "surface_kind": "paper_recovery_state",
            "phase": "transition_request_pending",
            "next_safe_action": {
                "kind": "await_opl_transition_readback",
                "owner": "one-person-lab",
                "provider_admission_allowed": False,
                "provider_admission_requires_opl_runtime_result": True,
            },
        }
    return {
        "surface_kind": "paper_recovery_state",
        "phase": "admission_pending",
        "next_safe_action": {
            "kind": "admit_provider_attempt",
            "owner": _non_empty_text(candidate.get("next_executable_owner"))
            or _non_empty_text(candidate.get("owner")),
            "provider_admission_allowed": True,
        },
    }
