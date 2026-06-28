from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup import _non_empty_text
from med_autoscience.controllers.opl_transition_readback import (
    candidate_opl_transition_readback,
    provider_admission_opl_transition_readback,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    mapping as _mapping,
)


def transition_request_only_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        dict(candidate)
        for candidate in candidates
        if not candidate_opl_transition_readback(candidate)
        and (
            _mapping(candidate.get("opl_domain_progress_transition_request"))
            or _mapping(_mapping(candidate.get("paper_progress_policy_result")).get(
                "opl_domain_progress_transition_request"
            ))
        )
        and candidate.get("provider_admission_requires_opl_runtime_result") is True
    ]


def filter_transition_requests_consumed_by_provider_readback(
    candidates: list[dict[str, Any]],
    *,
    provider_candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not candidates:
        return []
    provider_readback_keys = {
        candidate_core_identity_key(candidate)
        for candidate in provider_candidates
        if provider_admission_opl_transition_readback(candidate)
    }
    if not provider_readback_keys:
        return [dict(candidate) for candidate in candidates]
    return [
        dict(candidate)
        for candidate in candidates
        if candidate_core_identity_key(candidate) not in provider_readback_keys
    ]


def candidate_core_identity_key(candidate: Mapping[str, Any]) -> tuple[str | None, ...]:
    return (
        _non_empty_text(candidate.get("study_id")),
        _non_empty_text(candidate.get("action_type")),
        _non_empty_text(candidate.get("work_unit_id")),
        _non_empty_text(candidate.get("work_unit_fingerprint"))
        or _non_empty_text(candidate.get("action_fingerprint")),
    )
