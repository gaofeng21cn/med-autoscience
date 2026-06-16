from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers import paper_progress_policy_adapter
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    mapping as _mapping,
    non_empty_text as _non_empty_text,
)


def candidate_with_opl_transition_request(
    candidate: Mapping[str, Any],
    *,
    source: str,
    current_action_source: str | None = None,
) -> dict[str, Any]:
    payload = dict(candidate)
    policy_result = _mapping(payload.get("paper_progress_policy_result"))
    transition_request = _mapping(payload.get("opl_domain_progress_transition_request")) or _mapping(
        policy_result.get("opl_domain_progress_transition_request")
    )
    if not policy_result or not transition_request:
        policy_result = paper_progress_policy_adapter.build_policy_result(
            {
                "study_id": _non_empty_text(payload.get("study_id")),
                "quest_id": _non_empty_text(payload.get("quest_id")),
                "current_work_unit": _candidate_current_work_unit(payload),
                "current_executable_owner_action": _candidate_current_action(
                    payload,
                    current_action_source=current_action_source,
                ),
            },
            source=source,
        )
        transition_request = _mapping(policy_result.get("opl_domain_progress_transition_request"))
    if policy_result:
        payload["paper_progress_policy_result"] = dict(policy_result)
    if transition_request:
        payload["opl_domain_progress_transition_request"] = dict(transition_request)
    return payload


def _candidate_current_work_unit(candidate: Mapping[str, Any]) -> dict[str, Any]:
    currentness_basis = _mapping(candidate.get("currentness_basis"))
    return {
        key: value
        for key, value in {
            "surface_kind": "current_work_unit",
            "status": "executable_owner_action",
            "owner": _non_empty_text(candidate.get("next_executable_owner"))
            or _non_empty_text(candidate.get("owner")),
            "action_type": _non_empty_text(candidate.get("action_type")),
            "work_unit_id": _non_empty_text(candidate.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(candidate.get("work_unit_fingerprint"))
            or _non_empty_text(candidate.get("action_fingerprint")),
            "action_fingerprint": _non_empty_text(candidate.get("action_fingerprint"))
            or _non_empty_text(candidate.get("work_unit_fingerprint")),
            "currentness_basis": dict(currentness_basis) if currentness_basis else None,
        }.items()
        if value not in (None, "", [], {})
    }


def _candidate_current_action(
    candidate: Mapping[str, Any],
    *,
    current_action_source: str | None,
) -> dict[str, Any]:
    currentness_basis = _mapping(candidate.get("currentness_basis"))
    return {
        key: value
        for key, value in {
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": current_action_source or _non_empty_text(candidate.get("source")),
            "next_owner": _non_empty_text(candidate.get("next_executable_owner"))
            or _non_empty_text(candidate.get("owner")),
            "owner": _non_empty_text(candidate.get("next_executable_owner"))
            or _non_empty_text(candidate.get("owner")),
            "action_type": _non_empty_text(candidate.get("action_type")),
            "work_unit_id": _non_empty_text(candidate.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(candidate.get("work_unit_fingerprint"))
            or _non_empty_text(candidate.get("action_fingerprint")),
            "action_fingerprint": _non_empty_text(candidate.get("action_fingerprint"))
            or _non_empty_text(candidate.get("work_unit_fingerprint")),
            "currentness_basis": dict(currentness_basis) if currentness_basis else None,
        }.items()
        if value not in (None, "", [], {})
    }
