from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.opl_execution_boundary import OPL_EXECUTION_AUTHORIZATION_BLOCKER
from med_autoscience.controllers.owner_callable_adapter_projection import (
    domain_progress_transition_requests,
)
from med_autoscience.controllers.provider_admission.managed_wakeup import _non_empty_text
from med_autoscience.controllers.provider_admission.provider_admission import (
    candidate_with_authority_boundaries,
    handoff_dispatch_path,
    handoff_work_unit_id,
)
from med_autoscience.controllers.provider_admission.provider_admission_helpers import (
    mapping as _mapping,
)
from med_autoscience.controllers.provider_admission.provider_admission_report_current_action_identity import (
    candidate_with_current_action_identity,
)
from med_autoscience.controllers.provider_admission.provider_admission_report_same_tick_identity import (
    same_tick_candidate_matches_current_action as _same_tick_candidate_matches_current_action,
    same_tick_candidate_with_stage_run_identity as _same_tick_candidate_with_stage_run_identity,
    same_tick_progress_current_actions as _same_tick_progress_current_actions,
    same_tick_text_items as _same_tick_text_items,
)
from med_autoscience.controllers.provider_admission.provider_admission_transition_request import (
    candidate_with_opl_transition_request as _candidate_with_opl_transition_request,
)
from med_autoscience.profiles import WorkspaceProfile


def provider_admission_candidates_from_same_tick_materialize(
    *,
    profile: WorkspaceProfile,
    materialize_result: Mapping[str, Any],
    fallback_candidates: list[dict[str, Any]],
    progress_currentness: Mapping[str, Any] | None = None,
    source_kind: str = "same_tick_terminal_handoff",
) -> list[dict[str, Any]]:
    fallback_by_identity = {
        (_non_empty_text(candidate.get("study_id")), _non_empty_text(candidate.get("action_type"))): candidate
        for candidate in fallback_candidates
    }
    current_action_by_study = _same_tick_progress_current_actions(progress_currentness)
    candidates: list[dict[str, Any]] = []
    for dispatch in _same_tick_materialized_transition_dispatches(materialize_result):
        if not isinstance(dispatch, Mapping):
            continue
        if _non_empty_text(dispatch.get("dispatch_status")) not in {"ready", "transition_request_pending"}:
            continue
        study_id = _non_empty_text(dispatch.get("study_id"))
        action_type = _non_empty_text(dispatch.get("action_type"))
        base = dict(fallback_by_identity.get((study_id, action_type), {}))
        dispatch_refs = _mapping(dispatch.get("refs"))
        stage_packet_ref = (
            _non_empty_text(dispatch.get("stage_packet_ref"))
            or _non_empty_text(dispatch_refs.get("stage_packet_ref"))
            or _non_empty_text(dispatch_refs.get("stage_packet_path"))
            or _non_empty_text(dispatch_refs.get("immutable_dispatch_path"))
            or _non_empty_text(base.get("stage_packet_ref"))
        )
        stage_packet_refs = (
            _same_tick_text_items(dispatch.get("stage_packet_refs"))
            or _same_tick_text_items(dispatch_refs.get("stage_packet_refs"))
            or _same_tick_text_items(base.get("stage_packet_refs"))
        )
        if stage_packet_ref is not None and stage_packet_ref not in stage_packet_refs:
            stage_packet_refs.append(stage_packet_ref)
        stage_packet_ref = _workspace_relative_ref(
            stage_packet_ref,
            workspace_root=profile.workspace_root,
        )
        stage_packet_refs = [
            ref
            for ref in (
                _workspace_relative_ref(item, workspace_root=profile.workspace_root)
                for item in stage_packet_refs
            )
            if ref is not None
        ]
        if stage_packet_ref is not None and stage_packet_ref not in stage_packet_refs:
            stage_packet_refs.insert(0, stage_packet_ref)
        candidate = {
            **base,
            "surface": "opl_provider_admission_candidate",
            "schema_version": 1,
            "status": "transition_request_pending",
            "dispatch_status": "transition_request_pending",
            "source": _non_empty_text(base.get("source")) or "same_tick_materialized_dispatch",
            "study_id": study_id,
            "quest_id": _non_empty_text(dispatch.get("quest_id")) or _non_empty_text(base.get("quest_id")),
            "action_type": action_type,
            "work_unit_id": _non_empty_text(dispatch.get("work_unit_id"))
            or _non_empty_text(base.get("work_unit_id"))
            or handoff_work_unit_id(dispatch),
            "work_unit_fingerprint": _non_empty_text(dispatch.get("work_unit_fingerprint"))
            or _non_empty_text(dispatch.get("action_fingerprint"))
            or _non_empty_text(base.get("work_unit_fingerprint")),
            "action_fingerprint": _non_empty_text(dispatch.get("action_fingerprint"))
            or _non_empty_text(dispatch.get("work_unit_fingerprint"))
            or _non_empty_text(base.get("action_fingerprint")),
            "dispatch_path": _non_empty_text(dispatch.get("dispatch_path"))
            or _non_empty_text(base.get("dispatch_path"))
            or handoff_dispatch_path(dispatch),
            "stage_packet_ref": stage_packet_ref,
            "stage_packet_refs": stage_packet_refs or None,
            "dispatch_authority": _non_empty_text(dispatch.get("dispatch_authority"))
            or _non_empty_text(base.get("dispatch_authority")),
            "blocked_reason": OPL_EXECUTION_AUTHORIZATION_BLOCKER,
            "next_executable_owner": _non_empty_text(dispatch.get("next_executable_owner"))
            or _non_empty_text(base.get("next_executable_owner")),
            "required_output_surface": _non_empty_text(dispatch.get("required_output_surface"))
            or _non_empty_text(base.get("required_output_surface")),
            "provider_attempt_or_lease_required": False,
            "opl_transition_runtime_required": True,
            "provider_admission_pending": False,
            "provider_admission_requires_opl_runtime_result": True,
            "provider_completion_is_domain_completion": False,
            "owner_route_current": True,
            "same_tick_materialized_provider_admission": True,
            "same_tick_materialization_source": source_kind,
        }
        currentness_basis = _same_tick_materialized_currentness_basis(
            candidate,
            base=base,
            materialize_result=materialize_result,
        )
        if currentness_basis:
            candidate["currentness_basis"] = currentness_basis
        candidate = _same_tick_candidate_with_stage_run_identity(candidate)
        candidate = _candidate_with_opl_transition_request(
            candidate,
            source="domain_diagnostic.provider_admission_same_tick_materialized_dispatch",
            current_action_source="same_tick_materialized_dispatch",
        )
        if candidate["study_id"] is not None and candidate["action_type"] is not None:
            current_action_identity = current_action_by_study.get(candidate["study_id"])
            if current_action_identity is not None and not _same_tick_candidate_matches_current_action(
                candidate,
                current_action_identity=current_action_identity,
            ):
                continue
            candidate = candidate_with_current_action_identity(
                candidate,
                current_action_identity=current_action_identity,
            )
            candidates.append(
                candidate_with_authority_boundaries(
                    {key: value for key, value in candidate.items() if value is not None}
                )
            )
    return candidates


def _same_tick_materialized_transition_dispatches(
    materialize_result: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return domain_progress_transition_requests(materialize_result)


def _workspace_relative_ref(value: str | None, *, workspace_root: Path) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    path = Path(text)
    if not path.is_absolute():
        return text
    try:
        return path.resolve().relative_to(workspace_root).as_posix()
    except (OSError, ValueError):
        return text


def _same_tick_materialized_currentness_basis(
    candidate: Mapping[str, Any],
    *,
    base: Mapping[str, Any],
    materialize_result: Mapping[str, Any],
) -> dict[str, Any]:
    base_basis = _mapping(base.get("currentness_basis"))
    work_unit_id = _non_empty_text(candidate.get("work_unit_id"))
    fingerprint = _non_empty_text(candidate.get("work_unit_fingerprint")) or _non_empty_text(
        candidate.get("action_fingerprint")
    )
    if work_unit_id is None or fingerprint is None:
        return dict(base_basis)
    generated_at = (
        _non_empty_text(base_basis.get("truth_epoch"))
        or _non_empty_text(materialize_result.get("generated_at"))
        or _non_empty_text(materialize_result.get("scanned_at"))
        or fingerprint
    )
    runtime_epoch = (
        _non_empty_text(base_basis.get("runtime_health_epoch"))
        or _non_empty_text(materialize_result.get("runtime_health_epoch"))
        or generated_at
    )
    basis = {
        **dict(base_basis),
        "work_unit_id": _non_empty_text(base_basis.get("work_unit_id")) or work_unit_id,
        "work_unit_fingerprint": _non_empty_text(base_basis.get("work_unit_fingerprint")) or fingerprint,
        "truth_epoch": generated_at,
        "runtime_health_epoch": runtime_epoch,
        "admission_identity_source": "same_tick_materialized_dispatch",
    }
    source_eval_id = _non_empty_text(base_basis.get("source_eval_id")) or _non_empty_text(
        candidate.get("source_eval_id")
    )
    if source_eval_id is not None:
        basis["source_eval_id"] = source_eval_id
    return {key: value for key, value in basis.items() if value not in (None, "", [], {})}


def same_tick_materialized_candidate(candidate: Mapping[str, Any]) -> bool:
    if candidate.get("same_tick_materialized_provider_admission") is True:
        return True
    return _non_empty_text(candidate.get("source")) == "same_tick_materialized_dispatch"


__all__ = [
    "provider_admission_candidates_from_same_tick_materialize",
    "same_tick_materialized_candidate",
]
