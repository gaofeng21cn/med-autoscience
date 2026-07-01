from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.opl_transition_readback import (
    candidate_opl_transition_readback,
    LIVE_READBACK_PROVIDER_ADMISSION_OUTCOME,
    non_advancing_apply_opl_transition_readback,
    provider_admission_opl_transition_readback,
)
from med_autoscience.controllers.paper_mission_owner_surface_parts.opl_provider_attempts import (
    terminal_provider_attempt_closeout_for_study,
)
from med_autoscience.controllers.study_transition_receipt_consumption_parts.owner_callable_candidates import (
    owner_callable_receipt_candidates,
)
from med_autoscience.controllers.study_transition_receipt_consumption_parts.missing_refs_typed_closeout import (
    is_blocked_typed_closeout,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol.layout import build_workspace_runtime_layout_for_profile

from .opl_current_control_state_handoff_values import (
    _copy_mapping_keys,
    _current_control_currentness_fields,
    _first_present_mapping_value,
    _observability_mapping,
    _owner_route_projection,
    _stage_progress_log_mapping,
    _strict_running_provider_attempt,
    _string_list,
    _work_unit_identity,
)
from .opl_current_control_state_handoff_identity import bind_live_attempt_to_handoff_identity
from .opl_current_control_state_handoff_parts.lifecycle import (
    build_readonly_ai_repair_lifecycle_projection,
    current_status_publication_gate_stationary,
    current_status_suppresses_ai_repair_lifecycle,
    read_ai_repair_lifecycle,
)
from .opl_current_control_state_handoff_parts.mode_fields import (
    _opl_current_control_state_mode_fields,
)
from .opl_current_control_state_handoff_parts.terminal_closeout import (
    LIVE_ATTEMPT_SUPERSEDED_BLOCKERS,
    LIVE_ATTEMPT_SUPERSEDED_NEXT_OWNERS,
    _action_with_handoff_packet_readback,
    _apply_matching_terminal_closeout_to_handoff,
    _apply_typed_owner_callable_adapter_closeout_to_handoff,
    _handoff_candidate_list,
    _handoff_has_complete_current_transition_readback,
    _handoff_live_attempt_identity_stale,
    _live_attempt_supersedes_handoff_blocker,
    _newer_typed_closeout_blocks_stale_current_control,
    _provider_admission_terminal_closeout_consumed,
    _stage_ref_items,
    _terminal_closeout_matches_handoff_action,
    _terminal_matching_handoff_candidates,
)
from .opl_current_control_state_handoff_parts.transition_readbacks import (
    _matching_with_live_log_transition_readbacks,
    _top_level_provider_admission_candidates_for_study,
    _top_level_transition_request_candidates_for_study,
    _transition_candidates_with_live_log_readback,
    _transition_request_identity_key,
)
from .opl_current_control_state_terminal_logs import (
    _latest_terminal_stage_log_projection,
    _latest_typed_owner_callable_closeout_projection,
    _typed_closeout_supersedes_terminal,
)
from .shared_base import _mapping_copy, _non_empty_text, _read_json_object

LIVE_ATTEMPT_HANDOFF_KEYS = (
    "active_run_id",
    "active_stage_attempt_id",
    "active_workflow_id",
    "running_provider_attempt",
)
ATTEMPT_IDENTITY_KEYS = (
    "action_type",
    "work_unit_id",
    "next_work_unit",
    "work_unit_fingerprint",
    "action_fingerprint",
    "lineage_ref",
)



def opl_current_control_state_handoff_path(*, profile: WorkspaceProfile) -> Path:
    return (
        build_workspace_runtime_layout_for_profile(profile).runtime_artifacts_root
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )




def opl_current_control_state_study_handoff_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
) -> dict[str, Any] | None:
    handoff_path = opl_current_control_state_handoff_path(profile=profile)
    payload = _read_json_object(handoff_path)
    latest_terminal_stage_log = _latest_terminal_stage_log_projection(
        profile=profile,
        study_id=study_id,
    )
    latest_typed_closeout = _latest_typed_owner_callable_closeout_projection(
        profile=profile,
        study_id=study_id,
    )
    if payload is None:
        if latest_terminal_stage_log is None and latest_typed_closeout is None:
            return None
        return _closeout_only_study_handoff_projection(
            handoff_path=handoff_path,
            latest_terminal_stage_log=latest_terminal_stage_log,
            latest_typed_closeout=latest_typed_closeout,
            study_id=study_id,
        )
    matching = None
    for item in payload.get("studies") or []:
        if isinstance(item, Mapping) and _non_empty_text(item.get("study_id")) == study_id:
            matching = dict(item)
            break
    matching_top_level_provider_admissions = _top_level_provider_admission_candidates_for_study(
        payload,
        study_id=study_id,
    )
    matching_provider_admissions = [
        dict(item)
        for item in matching.get("provider_admission_candidates") or []
        if isinstance(item, Mapping)
    ] if matching is not None else []
    matching_top_level_transition_requests = _top_level_transition_request_candidates_for_study(
        payload,
        study_id=study_id,
    )
    matching_top_level_transition_requests = _transition_candidates_with_live_log_readback(
        profile=profile,
        candidates=matching_top_level_transition_requests,
    )
    latest_opl_terminal_closeout = _latest_opl_terminal_provider_attempt_closeout_projection(
        profile=profile,
        study_id=study_id,
        payload=payload,
        matching=matching,
        matching_top_level_provider_admissions=matching_top_level_provider_admissions,
        matching_top_level_transition_requests=matching_top_level_transition_requests,
    )
    if latest_opl_terminal_closeout is not None:
        latest_terminal_stage_log = latest_opl_terminal_closeout
    latest_terminal_consumed_readback = _latest_provider_admission_terminal_consumed_readback_for_study(
        payload,
        study_id=study_id,
    )
    if matching is None:
        if (
            latest_terminal_stage_log is None
            and latest_typed_closeout is None
            and not latest_terminal_consumed_readback
            and not matching_top_level_provider_admissions
            and not matching_top_level_transition_requests
        ):
            return None
        projection = _closeout_only_study_handoff_projection(
            handoff_path=handoff_path,
            latest_terminal_stage_log=latest_terminal_stage_log,
            latest_typed_closeout=latest_typed_closeout,
            study_id=study_id,
            payload=payload,
        )
        if matching_top_level_provider_admissions:
            projection = _apply_top_level_provider_admissions_to_handoff(
                projection,
                matching_top_level_provider_admissions,
            )
        if matching_top_level_transition_requests:
            projection = _apply_top_level_transition_requests_to_handoff(
                projection,
                matching_top_level_transition_requests,
            )
        if latest_terminal_consumed_readback:
            projection = _apply_terminal_consumed_readback_to_handoff(
                projection,
                latest_terminal_consumed_readback,
            )
        return projection
    matching = _matching_with_live_log_transition_readbacks(
        profile=profile,
        matching=matching,
    )
    action_queue = [
        {
            **_copy_mapping_keys(
                item,
                (
                    "action_type",
                    "study_id",
                    "quest_id",
                    "summary",
                    "status",
                    "owner",
                    "surface",
                    "action_id",
                    "fingerprint",
                    "action_fingerprint",
                    "work_unit_fingerprint",
                    "authority",
                    "queue_age_hours",
                    "queued_first_seen_at",
                    "repeat_fingerprint",
                    "next_work_unit",
                    "controller_work_unit_id",
                    "work_unit_id",
                    "source_eval_id",
                    "source_fingerprint",
                    "owner_pickup",
                    "consumption",
                    "route_identity_key",
                    "attempt_idempotency_key",
                    "idempotency_key",
                    "provider_admission_identity",
                    "dispatch_ref",
                    "dispatch_path",
                    "stage_packet_ref",
                    "stage_packet_refs",
                    "checkpoint_refs",
                    "source_refs",
                    "opl_domain_progress_transition_live_readback",
                    "opl_domain_progress_transition_runtime_live_readback",
                    "opl_domain_progress_transition_result",
                ),
            ),
            "source": "opl_current_control_state_action_queue",
        }
        for item in matching.get("action_queue") or []
        if isinstance(item, Mapping)
    ]
    why_not_applied = _string_list(matching.get("why_not_applied"))
    matching_terminal_stage_log = _observability_mapping(matching.get("latest_terminal_stage_log"))
    active_run_id = _non_empty_text(matching.get("active_run_id"))
    active_stage_attempt_id = _non_empty_text(matching.get("active_stage_attempt_id"))
    active_workflow_id = _non_empty_text(matching.get("active_workflow_id"))
    running_provider_attempt = _strict_running_provider_attempt(
        matching,
        active_run_id=active_run_id,
        active_stage_attempt_id=active_stage_attempt_id,
        active_workflow_id=active_workflow_id,
    )
    projection = {
        "surface_kind": "opl_current_control_state_study_handoff",
        "read_model": "study_opl_current_control_state_handoff_projection",
        "authority": "observability_only",
        "source_path": str(handoff_path),
        "generated_at": _non_empty_text(payload.get("generated_at")),
        "study_id": study_id,
        "quest_status": _non_empty_text(matching.get("quest_status")),
        "active_run_id": active_run_id,
        "active_stage_attempt_id": active_stage_attempt_id,
        "active_workflow_id": active_workflow_id,
        "running_provider_attempt": running_provider_attempt,
        "runtime_owner": "one-person-lab" if running_provider_attempt else None,
        "provider_attempt_owner": "one-person-lab" if running_provider_attempt else None,
        "queue_owner": "one-person-lab" if running_provider_attempt else None,
        "action_type": _non_empty_text(matching.get("action_type")),
        "work_unit_id": _work_unit_identity(matching.get("work_unit_id")),
        "next_work_unit": _work_unit_identity(matching.get("next_work_unit")),
        "work_unit_fingerprint": _non_empty_text(matching.get("work_unit_fingerprint")),
        "action_fingerprint": _non_empty_text(matching.get("action_fingerprint"))
        or _non_empty_text(matching.get("work_unit_fingerprint")),
        "runtime_health": _copy_mapping_keys(
            matching.get("runtime_health"),
            (
                "health_status",
                "runtime_liveness_status",
                "summary",
                "blocked_reason",
                *ATTEMPT_IDENTITY_KEYS,
            ),
        ),
        "artifact_delta": _copy_mapping_keys(
            matching.get("artifact_delta"),
            ("status", "summary", "latest_artifact_at", "latest_meaningful_delta_at"),
        ),
        "gate_specificity": _copy_mapping_keys(
            matching.get("gate_specificity"),
            ("status", "summary", "blocked_reason", "required_action"),
        ),
        "ai_reviewer_status": _copy_mapping_keys(
            matching.get("ai_reviewer_status"),
            ("status", "summary", "owner", "trace_complete", "blocked_reason"),
        ),
        "stage_progress_log": _stage_progress_log_mapping(matching.get("stage_progress_log")),
        "owner_route": _owner_route_projection(matching.get("owner_route")),
        "queue_slo": _copy_mapping_keys(
            matching.get("queue_slo"),
            (
                "max_queue_age_hours",
                "owner_pickup_overdue_count",
                "developer_supervisor_attention_required_count",
            ),
        ),
        "owner_pickup_overdue": bool(matching.get("owner_pickup_overdue")),
        "developer_supervisor_attention_required": bool(
            matching.get("developer_supervisor_attention_required")
        ),
        "action_queue": [item for item in action_queue if item],
        "why_not_applied": why_not_applied,
        "next_owner": _non_empty_text(matching.get("next_owner")),
        "external_supervisor_required": bool(matching.get("external_supervisor_required")),
        "blocked_reason": _non_empty_text(matching.get("blocked_reason")),
    }
    projection.update(_current_control_currentness_fields(matching))
    _copy_opl_transition_readback_fields(projection, matching)
    provider_admission_candidates = [
        *matching_provider_admissions,
        *matching_top_level_provider_admissions,
    ]
    if provider_admission_candidates:
        projection = _apply_top_level_provider_admissions_to_handoff(
            projection,
            provider_admission_candidates,
        )
    if matching_top_level_transition_requests:
        projection = _apply_top_level_transition_requests_to_handoff(
            projection,
            matching_top_level_transition_requests,
        )
    projection = _apply_action_queue_provider_readbacks_to_handoff(projection)
    if _typed_closeout_supersedes_terminal(
        typed_closeout=latest_typed_closeout,
        terminal_stage_log=latest_terminal_stage_log or matching_terminal_stage_log,
    ):
        typed_closeout = _observability_mapping(latest_typed_closeout)
        projection["latest_typed_owner_callable_closeout"] = typed_closeout
        if _newer_typed_closeout_blocks_stale_current_control(
            typed_closeout=typed_closeout,
            projection=projection,
            handoff_path=handoff_path,
        ):
            projection["blocked_reason"] = _non_empty_text(typed_closeout.get("blocked_reason"))
            projection["next_owner"] = _non_empty_text(typed_closeout.get("next_owner")) or projection["next_owner"]
            projection = _apply_typed_owner_callable_adapter_closeout_to_handoff(
                projection,
                allow_stale_identity_override=True,
            )
        elif not _handoff_has_complete_current_transition_readback(projection):
            projection["blocked_reason"] = _non_empty_text(typed_closeout.get("blocked_reason"))
            projection["next_owner"] = _non_empty_text(typed_closeout.get("next_owner")) or projection["next_owner"]
            projection = _apply_typed_owner_callable_adapter_closeout_to_handoff(projection)
    if latest_terminal_stage_log is not None:
        projection["latest_terminal_stage_log"] = latest_terminal_stage_log
    elif matching_terminal_stage_log:
        projection["latest_terminal_stage_log"] = matching_terminal_stage_log
    if latest_terminal_consumed_readback:
        projection = _apply_terminal_consumed_readback_to_handoff(
            projection,
            latest_terminal_consumed_readback,
        )
    projection.update(_opl_current_control_state_mode_fields(payload))
    return _apply_matching_terminal_closeout_to_handoff(projection)


def _latest_opl_terminal_provider_attempt_closeout_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    payload: Mapping[str, Any],
    matching: Mapping[str, Any] | None,
    matching_top_level_provider_admissions: list[dict[str, Any]],
    matching_top_level_transition_requests: list[dict[str, Any]],
) -> dict[str, Any] | None:
    preferred_actions = _current_control_provider_admission_candidates(
        payload=payload,
        matching=matching,
        matching_top_level_provider_admissions=matching_top_level_provider_admissions,
        matching_top_level_transition_requests=matching_top_level_transition_requests,
    )
    if not preferred_actions:
        return None
    closeout = terminal_provider_attempt_closeout_for_study(
        profile=profile,
        study_id=study_id,
        timeout_seconds=8.0,
        max_inspect_count=2,
        preferred_actions=preferred_actions,
    )
    if not closeout:
        return None
    if not any(
        _terminal_closeout_matches_handoff_action(terminal=closeout, action=action)
        for action in preferred_actions
    ):
        return None
    return closeout


def refresh_handoff_with_terminal_closeout_candidates(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    handoff: Mapping[str, Any] | None,
    candidates: list[Mapping[str, Any]],
) -> dict[str, Any] | None:
    if handoff is None:
        return None
    preferred_actions = [
        dict(item)
        for item in candidates
        if isinstance(item, Mapping) and _terminal_consumption_candidate_can_anchor_terminal_probe(item)
    ]
    if not preferred_actions:
        return dict(handoff)
    closeout = terminal_provider_attempt_closeout_for_study(
        profile=profile,
        study_id=study_id,
        timeout_seconds=8.0,
        max_inspect_count=2,
        preferred_actions=preferred_actions,
    )
    if not closeout:
        closeout = _terminal_owner_callable_adapter_closeout_for_preferred_actions(
            profile=profile,
            study_id=study_id,
            preferred_actions=preferred_actions,
        )
    if not closeout:
        return dict(handoff)
    if not any(
        _terminal_closeout_matches_handoff_action(terminal=closeout, action=action)
        for action in preferred_actions
    ):
        return dict(handoff)
    refreshed = {
        **dict(handoff),
        "latest_terminal_stage_log": closeout,
        "active_stage_attempt_id": _non_empty_text(closeout.get("stage_attempt_id")),
        "active_run_id": (
            f"opl-stage-attempt://{stage_attempt_id}"
            if (stage_attempt_id := _non_empty_text(closeout.get("stage_attempt_id"))) is not None
            else None
        ),
        "transition_request_pending_count": len(preferred_actions),
        "transition_request_candidates": preferred_actions,
    }
    return _apply_matching_terminal_closeout_to_handoff(refreshed)


def _terminal_owner_callable_adapter_closeout_for_preferred_actions(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    preferred_actions: list[dict[str, Any]],
) -> dict[str, Any] | None:
    study_root = _study_root_for_owner_callable_candidates(profile=profile, study_id=study_id)
    if study_root is None:
        return None
    for execution, receipt_ref in owner_callable_receipt_candidates(
        study_root=study_root,
        allow_legacy_fallback=True,
    ):
        closeout = dict(execution)
        closeout.setdefault("receipt_ref", receipt_ref)
        closeout.setdefault("source", "mas_owner_callable_adapter_closeout")
        if any(_owner_callable_adapter_closeout_can_consume_preferred_action(closeout, action) for action in preferred_actions):
            return closeout
    return None


def _owner_callable_adapter_closeout_can_consume_preferred_action(
    closeout: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    if not _terminal_closeout_matches_handoff_action(terminal=closeout, action=action):
        return False
    if (
        provider_admission_opl_transition_readback(action)
        and _non_empty_text(closeout.get("owner_receipt_ref")) is None
    ):
        return False
    return True


def _study_root_for_owner_callable_candidates(
    *,
    profile: WorkspaceProfile,
    study_id: str,
) -> Path | None:
    candidates = [
        profile.studies_root / study_id,
        build_workspace_runtime_layout_for_profile(profile).workspace_root / "studies" / study_id,
        profile.workspace_root / "studies" / study_id,
    ]
    for candidate in candidates:
        try:
            resolved = candidate.expanduser().resolve()
        except OSError:
            continue
        if resolved.exists():
            return resolved
    return candidates[0].expanduser().resolve() if candidates else None


def _current_control_provider_admission_candidates(
    *,
    payload: Mapping[str, Any],
    matching: Mapping[str, Any] | None,
    matching_top_level_provider_admissions: list[dict[str, Any]],
    matching_top_level_transition_requests: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    candidates = [
        dict(item)
        for item in matching_top_level_provider_admissions
        if isinstance(item, Mapping) and provider_admission_opl_transition_readback(item)
    ]
    candidates.extend(
        dict(item)
        for item in matching_top_level_transition_requests or []
        if isinstance(item, Mapping) and _transition_request_candidate_can_anchor_terminal_probe(item)
    )
    if isinstance(matching, Mapping):
        candidates.extend(
            dict(item)
            for item in matching.get("provider_admission_candidates") or []
            if isinstance(item, Mapping) and provider_admission_opl_transition_readback(item)
        )
        candidates.extend(
            dict(item)
            for item in matching.get("transition_request_candidates") or []
            if isinstance(item, Mapping) and _transition_request_candidate_can_anchor_terminal_probe(item)
        )
    if not candidates:
        return []
    provider_pending = int(payload.get("provider_admission_pending_count") or 0) > 0
    transition_pending = int(payload.get("transition_request_pending_count") or 0) > 0
    if isinstance(matching, Mapping):
        provider_pending = provider_pending or int(matching.get("provider_admission_pending_count") or 0) > 0
        transition_pending = transition_pending or int(matching.get("transition_request_pending_count") or 0) > 0
    return candidates if provider_pending or transition_pending else []


def _transition_request_candidate_can_anchor_terminal_probe(candidate: Mapping[str, Any]) -> bool:
    if candidate_opl_transition_readback(candidate):
        return True
    if _non_empty_text(candidate.get("status")) != "transition_request_pending":
        return False
    return (
        _non_empty_text(candidate.get("action_type")) is not None
        and _work_unit_identity(candidate.get("work_unit_id")) is not None
        and (
            _non_empty_text(candidate.get("work_unit_fingerprint")) is not None
            or _non_empty_text(candidate.get("action_fingerprint")) is not None
        )
        and (
            _non_empty_text(candidate.get("attempt_idempotency_key")) is not None
            or _non_empty_text(_observability_mapping(candidate.get("source_refs")).get("attempt_idempotency_key"))
            is not None
        )
    )


def _terminal_consumption_candidate_can_anchor_terminal_probe(candidate: Mapping[str, Any]) -> bool:
    return provider_admission_opl_transition_readback(candidate) or _transition_request_candidate_can_anchor_terminal_probe(
        candidate
    )


def _apply_top_level_provider_admissions_to_handoff(
    projection: Mapping[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    updated = dict(projection)
    provider_candidates = _dedupe_provider_admission_candidates(
        [
            dict(item)
            for item in candidates
            if provider_admission_opl_transition_readback(item)
        ]
    )
    if not provider_candidates:
        updated["provider_admission_pending_count"] = 0
        updated["provider_admission_candidates"] = []
        return updated
    updated["provider_admission_pending_count"] = len(provider_candidates)
    updated["provider_admission_candidates"] = provider_candidates
    current = provider_candidates[0]
    for key in ("action_type", "work_unit_fingerprint", "action_fingerprint"):
        text = _non_empty_text(current.get(key))
        if text is not None:
            updated[key] = text
    work_unit_id = _work_unit_identity(current.get("work_unit_id"))
    if work_unit_id is not None:
        updated["work_unit_id"] = work_unit_id
    _copy_stage_packet_ref_family_to_projection(updated, current)
    if _non_empty_text(current.get("status")) == "provider_admission_pending" and provider_candidates:
        updated["blocked_reason"] = None
        updated.pop("typed_blocker", None)
    return updated


def _apply_top_level_transition_requests_to_handoff(
    projection: Mapping[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    if projection.get("running_provider_attempt") is True:
        request_candidates_for_running = [
            dict(item)
            for item in candidates
            if _transition_request_candidate_can_anchor_terminal_probe(item)
            and not provider_admission_opl_transition_readback(item)
        ]
        if any(_handoff_candidate_matches_projection(candidate, projection) for candidate in request_candidates_for_running):
            return _handoff_without_same_identity_pending(projection, request_candidates_for_running)
    request_candidates = [
        dict(item)
        for item in candidates
        if _transition_request_candidate_can_anchor_terminal_probe(item)
        and not provider_admission_opl_transition_readback(item)
    ]
    if not request_candidates:
        return dict(projection)
    updated = dict(projection)
    updated["transition_request_pending_count"] = len(request_candidates)
    updated["transition_request_candidates"] = request_candidates
    updated.setdefault("provider_admission_pending_count", 0)
    updated.setdefault("provider_admission_candidates", [])
    current = request_candidates[0]
    for key in ("action_type", "work_unit_fingerprint", "action_fingerprint"):
        text = _non_empty_text(current.get(key))
        if text is not None:
            updated[key] = text
    work_unit_id = _work_unit_identity(current.get("work_unit_id"))
    if work_unit_id is not None:
        updated["work_unit_id"] = work_unit_id
    _copy_stage_packet_ref_family_to_projection(updated, current)
    updated["next_owner"] = _non_empty_text(current.get("next_owner")) or updated.get("next_owner")
    updated["blocked_reason"] = _non_empty_text(current.get("blocked_reason")) or updated.get("blocked_reason")
    return updated


def _handoff_without_same_identity_pending(
    projection: Mapping[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    updated = dict(projection)
    matching_identity_keys = {
        key
        for candidate in candidates
        if _handoff_candidate_matches_projection(candidate, projection)
        for key in _handoff_candidate_runtime_identity_keys(candidate)
    }
    if not matching_identity_keys:
        return updated
    provider_candidates = [
        dict(item)
        for item in updated.get("provider_admission_candidates") or []
        if not _handoff_candidate_runtime_identity_keys(item).intersection(matching_identity_keys)
    ]
    transition_candidates = [
        dict(item)
        for item in updated.get("transition_request_candidates") or []
        if not _handoff_candidate_runtime_identity_keys(item).intersection(matching_identity_keys)
    ]
    updated["provider_admission_candidates"] = provider_candidates
    updated["provider_admission_pending_count"] = len(provider_candidates)
    updated["transition_request_candidates"] = transition_candidates
    updated["transition_request_pending_count"] = len(transition_candidates)
    updated["blocked_reason"] = None
    updated["external_supervisor_required"] = False
    return updated


def _handoff_candidate_runtime_identity_keys(candidate: Mapping[str, Any]) -> set[str]:
    readback = candidate_opl_transition_readback(candidate) or provider_admission_opl_transition_readback(
        candidate
    )
    readback_identity = _observability_mapping(readback.get("identity"))
    stage_run_identity = _observability_mapping(readback_identity.get("stage_run_identity"))
    idempotency_readback = _observability_mapping(readback.get("idempotency_readback"))
    provider_identity = _observability_mapping(candidate.get("provider_admission_identity"))
    source_refs = _observability_mapping(candidate.get("source_refs"))
    return {
        key
        for key in (
            _transition_request_identity_key(candidate),
            _non_empty_text(candidate.get("route_identity_key")),
            _non_empty_text(candidate.get("attempt_idempotency_key")),
            _non_empty_text(candidate.get("idempotency_key")),
            _non_empty_text(provider_identity.get("route_identity_key")),
            _non_empty_text(provider_identity.get("attempt_idempotency_key")),
            _non_empty_text(provider_identity.get("idempotency_key")),
            _non_empty_text(source_refs.get("route_identity_key")),
            _non_empty_text(source_refs.get("attempt_idempotency_key")),
            _non_empty_text(source_refs.get("idempotency_key")),
            _non_empty_text(stage_run_identity.get("route_identity_key")),
            _non_empty_text(stage_run_identity.get("attempt_idempotency_key")),
            _non_empty_text(readback_identity.get("idempotency_key")),
            _non_empty_text(idempotency_readback.get("idempotency_key")),
        )
        if key is not None
    }


def _handoff_candidate_matches_projection(
    candidate: Mapping[str, Any],
    projection: Mapping[str, Any],
) -> bool:
    for key in ("study_id", "action_type"):
        candidate_value = _non_empty_text(candidate.get(key))
        projection_value = _non_empty_text(projection.get(key))
        if candidate_value is not None and projection_value is not None and candidate_value != projection_value:
            return False
    candidate_work_unit = _work_unit_identity(candidate.get("work_unit_id")) or _work_unit_identity(
        candidate.get("next_work_unit")
    )
    projection_work_unit = _work_unit_identity(projection.get("work_unit_id")) or _work_unit_identity(
        projection.get("next_work_unit")
    )
    if candidate_work_unit is not None and projection_work_unit is not None and candidate_work_unit != projection_work_unit:
        return False
    candidate_fingerprint = _non_empty_text(candidate.get("work_unit_fingerprint")) or _non_empty_text(
        candidate.get("action_fingerprint")
    )
    projection_fingerprint = _non_empty_text(projection.get("work_unit_fingerprint")) or _non_empty_text(
        projection.get("action_fingerprint")
    )
    if (
        candidate_fingerprint is not None
        and projection_fingerprint is not None
        and candidate_fingerprint != projection_fingerprint
    ):
        return False
    for key in ("route_identity_key", "attempt_idempotency_key", "idempotency_key"):
        candidate_value = _non_empty_text(candidate.get(key))
        projection_value = _non_empty_text(projection.get(key))
        if candidate_value is not None and projection_value is not None and candidate_value == projection_value:
            return True
    return candidate_work_unit is not None and projection_work_unit is not None and candidate_work_unit == projection_work_unit


def _copy_stage_packet_ref_family_to_projection(
    projection: dict[str, Any],
    source: Mapping[str, Any],
) -> None:
    source_refs = _observability_mapping(source.get("source_refs"))
    stage_packet_ref = _non_empty_text(source.get("stage_packet_ref")) or _non_empty_text(
        source_refs.get("stage_packet_ref")
    )
    stage_packet_refs = _stage_ref_items(source.get("stage_packet_refs")) or _stage_ref_items(
        source_refs.get("stage_packet_refs")
    )
    if stage_packet_ref is not None and stage_packet_ref not in stage_packet_refs:
        stage_packet_refs.insert(0, stage_packet_ref)
    checkpoint_refs = _stage_ref_items(source.get("checkpoint_refs")) or _stage_ref_items(
        source_refs.get("checkpoint_refs")
    ) or list(stage_packet_refs)
    for key in ("dispatch_ref", "dispatch_path"):
        value = _non_empty_text(source.get(key)) or _non_empty_text(source_refs.get(key))
        if value is not None:
            projection[key] = value
    if stage_packet_ref is not None:
        projection["stage_packet_ref"] = stage_packet_ref
    if stage_packet_refs:
        projection["stage_packet_refs"] = stage_packet_refs
    if checkpoint_refs:
        projection["checkpoint_refs"] = checkpoint_refs




def _apply_action_queue_provider_readbacks_to_handoff(
    projection: Mapping[str, Any],
) -> dict[str, Any]:
    consumed = _observability_mapping(projection.get("provider_admission_terminal_closeout_consumed"))
    if consumed:
        terminal = _terminal_stage_log_from_terminal_consumed_readback(consumed)
        action_queue = _handoff_candidate_list(projection.get("action_queue"))
        matching_actions = _terminal_matching_handoff_candidates(
            terminal=terminal,
            candidates=action_queue,
        )
        if matching_actions:
            projection = {
                **dict(projection),
                "action_queue": [
                    dict(item)
                    for item in action_queue
                    if item not in matching_actions
                ],
                "consumed_action_queue": [
                    {
                        **dict(item),
                        "consumption": {
                            **_observability_mapping(item.get("consumption")),
                            "state": "consumed_by_provider_admission_terminal_readback",
                            "terminal_stage_attempt_id": _non_empty_text(
                                consumed.get("terminal_stage_attempt_id")
                            )
                            or _non_empty_text(consumed.get("stage_attempt_id")),
                        },
                    }
                    for item in matching_actions
                ],
            }
    projection_readback_candidate = _provider_readback_candidate_from_projection(projection)
    action_provider_candidates = [
        dict(item)
        for item in projection.get("action_queue") or []
        if isinstance(item, Mapping) and provider_admission_opl_transition_readback(_action_with_handoff_packet_readback(item))
    ]
    if projection_readback_candidate:
        action_provider_candidates.extend(
            _bind_projection_provider_readback_to_actions(
                projection,
                readback_candidate=projection_readback_candidate,
            )
        )
    action_provider_candidates = _dedupe_provider_admission_candidates(action_provider_candidates)
    if not action_provider_candidates:
        return dict(projection)
    updated = _apply_top_level_provider_admissions_to_handoff(
        projection,
        action_provider_candidates,
    )
    provider_keys = {
        _transition_request_identity_key(candidate)
        for candidate in action_provider_candidates
        if _transition_request_identity_key(candidate) is not None
    }
    remaining_transition_requests = [
        dict(item)
        for item in updated.get("transition_request_candidates") or []
        if _transition_request_identity_key(item) not in provider_keys
    ]
    updated["transition_request_candidates"] = remaining_transition_requests
    updated["transition_request_pending_count"] = len(remaining_transition_requests)
    updated["quest_status"] = "provider_admission_pending"
    return updated


def _dedupe_provider_admission_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()
    for candidate in candidates:
        identity = tuple(sorted(_handoff_candidate_runtime_identity_keys(candidate)))
        if not identity:
            identity = tuple(
                value
                for value in (
                    _non_empty_text(candidate.get("study_id")),
                    _work_unit_identity(candidate.get("work_unit_id"))
                    or _work_unit_identity(candidate.get("next_work_unit")),
                    _non_empty_text(candidate.get("work_unit_fingerprint"))
                    or _non_empty_text(candidate.get("action_fingerprint")),
                )
                if value is not None
            )
        if identity in seen:
            continue
        seen.add(identity)
        deduped.append(candidate)
    return deduped


def _provider_readback_candidate_from_projection(projection: Mapping[str, Any]) -> dict[str, Any]:
    readback = candidate_opl_transition_readback(projection)
    if not readback:
        return {}
    outcome_kind = _non_empty_text(_observability_mapping(readback.get("exactly_one_outcome")).get("outcome_kind"))
    if outcome_kind != LIVE_READBACK_PROVIDER_ADMISSION_OUTCOME:
        return {}
    identity = _provider_admission_identity_from_readback(readback)
    if not identity:
        return {}
    action_type = _non_empty_text(projection.get("action_type"))
    work_unit_id = _work_unit_identity(projection.get("work_unit_id")) or _work_unit_identity(
        identity.get("work_unit_id")
    )
    work_unit_fingerprint = _non_empty_text(projection.get("work_unit_fingerprint")) or _non_empty_text(
        projection.get("action_fingerprint")
    ) or _non_empty_text(identity.get("work_unit_fingerprint"))
    return {
        **identity,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": _non_empty_text(projection.get("action_fingerprint"))
        or work_unit_fingerprint,
        "next_executable_owner": _non_empty_text(projection.get("next_owner")),
        "owner": _non_empty_text(projection.get("next_owner")),
        "status": "provider_admission_pending",
        "provider_admission_pending": True,
        "transition_request_pending": False,
        "provider_attempt_or_lease_required": True,
        "provider_admission_requires_opl_runtime_result": False,
        "opl_domain_progress_transition_runtime_live_readback": readback,
    }



def _bind_projection_provider_readback_to_actions(
    projection: Mapping[str, Any],
    *,
    readback_candidate: Mapping[str, Any],
) -> list[dict[str, Any]]:
    bound: list[dict[str, Any]] = []
    for item in projection.get("action_queue") or []:
        if not isinstance(item, Mapping):
            continue
        action = _action_with_handoff_packet_readback(item)
        if not _same_provider_readback_identity(action, readback_candidate):
            continue
        action_readback = provider_admission_opl_transition_readback(action) or readback_candidate[
            "opl_domain_progress_transition_runtime_live_readback"
        ]
        bound.append(
            {
                **action,
                "status": "provider_admission_pending",
                "provider_admission_pending": True,
                "transition_request_pending": False,
                "provider_attempt_or_lease_required": True,
                "provider_admission_requires_opl_runtime_result": False,
                "provider_admission_identity": {
                    **_observability_mapping(action.get("provider_admission_identity")),
                    **dict(readback_candidate),
                },
                "opl_domain_progress_transition_runtime_live_readback": action_readback,
            }
        )
    return bound


def _same_provider_readback_identity(
    action: Mapping[str, Any],
    readback_candidate: Mapping[str, Any],
) -> bool:
    action_study = _non_empty_text(action.get("study_id"))
    readback_study = _non_empty_text(readback_candidate.get("study_id"))
    if action_study is not None and readback_study is not None and action_study != readback_study:
        return False
    action_work_unit = _work_unit_identity(action.get("work_unit_id")) or _work_unit_identity(
        action.get("next_work_unit")
    )
    readback_work_unit = _work_unit_identity(readback_candidate.get("work_unit_id"))
    if action_work_unit is None or readback_work_unit is None or action_work_unit != readback_work_unit:
        return False
    action_fingerprint = _non_empty_text(action.get("work_unit_fingerprint")) or _non_empty_text(
        action.get("action_fingerprint")
    )
    readback_fingerprint = _non_empty_text(readback_candidate.get("work_unit_fingerprint"))
    if action_fingerprint is None or readback_fingerprint is None or action_fingerprint != readback_fingerprint:
        return False
    for key in ("route_identity_key", "attempt_idempotency_key"):
        action_value = _non_empty_text(action.get(key))
        readback_value = _non_empty_text(readback_candidate.get(key))
        if action_value is not None and readback_value is not None and action_value != readback_value:
            return False
    return True


def _latest_provider_admission_terminal_consumed_readback_for_study(
    payload: Mapping[str, Any],
    *,
    study_id: str,
) -> dict[str, Any]:
    readback = _observability_mapping(payload.get("latest_provider_admission_terminal_consumed_readback"))
    if _non_empty_text(readback.get("status")) != "provider_admission_terminal_consumed":
        return {}
    identity = _observability_mapping(readback.get("currentness_identity"))
    readback_study = _non_empty_text(identity.get("study_id")) or _non_empty_text(readback.get("study_id"))
    if readback_study is not None and readback_study != study_id:
        return {}
    return dict(readback)


def _apply_terminal_consumed_readback_to_handoff(
    projection: Mapping[str, Any],
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    terminal = _terminal_stage_log_from_terminal_consumed_readback(readback)
    if not terminal:
        return dict(projection)
    updated = dict(projection)
    existing_terminal = _observability_mapping(updated.get("latest_terminal_stage_log"))
    if not existing_terminal:
        updated["latest_terminal_stage_log"] = terminal
    candidate_sources = [
        *_handoff_candidate_list(updated.get("provider_admission_candidates")),
        *_handoff_candidate_list(updated.get("transition_request_candidates")),
        *_handoff_candidate_list(updated.get("action_queue")),
    ]
    if candidate_sources and not _terminal_matching_handoff_candidates(
        terminal=terminal,
        candidates=candidate_sources,
    ):
        return updated
    updated = _apply_matching_terminal_closeout_to_handoff(updated)
    return _consume_terminal_matching_action_queue(
        updated,
        terminal=terminal,
        consumed_readback=readback,
    )


def _consume_terminal_matching_action_queue(
    projection: Mapping[str, Any],
    *,
    terminal: Mapping[str, Any],
    consumed_readback: Mapping[str, Any],
) -> dict[str, Any]:
    action_queue = _handoff_candidate_list(projection.get("action_queue"))
    matching_actions = _terminal_matching_handoff_candidates(
        terminal=terminal,
        candidates=action_queue,
    )
    if not matching_actions:
        return dict(projection)
    updated = dict(projection)
    consumed_entries = [
        {
            **dict(item),
            "consumption": {
                **_observability_mapping(item.get("consumption")),
                "state": "consumed_by_provider_admission_terminal_readback",
                "terminal_stage_attempt_id": _non_empty_text(
                    consumed_readback.get("terminal_stage_attempt_id")
                )
                or _non_empty_text(consumed_readback.get("stage_attempt_id")),
            },
        }
        for item in matching_actions
    ]
    prior_consumed = [
        dict(item)
        for item in updated.get("consumed_action_queue") or []
        if isinstance(item, Mapping)
    ]
    updated["consumed_action_queue"] = [*prior_consumed, *consumed_entries]
    updated["action_queue"] = [
        dict(item)
        for item in action_queue
        if item not in matching_actions
    ]
    updated["provider_admission_terminal_closeout_consumed"] = _provider_admission_terminal_closeout_consumed(
        terminal=terminal,
        matching_provider_admission=matching_actions[0],
    )
    return updated


def _terminal_stage_log_from_terminal_consumed_readback(
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    if _non_empty_text(readback.get("status")) != "provider_admission_terminal_consumed":
        return {}
    identity = _observability_mapping(readback.get("currentness_identity"))
    terminal = {
        "surface_kind": "stage_attempt_closeout_packet",
        "source": "opl_current_control_state.latest_provider_admission_terminal_consumed_readback",
        "status": _non_empty_text(readback.get("terminal_stage_attempt_status")) or "completed",
        "stage_attempt_id": _non_empty_text(readback.get("terminal_stage_attempt_id"))
        or _non_empty_text(identity.get("stage_attempt_id")),
        "action_type": _non_empty_text(identity.get("action_type")) or _non_empty_text(readback.get("action_type")),
        "work_unit_id": _work_unit_identity(identity.get("work_unit_id"))
        or _work_unit_identity(readback.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(identity.get("work_unit_fingerprint"))
        or _non_empty_text(identity.get("action_fingerprint"))
        or _non_empty_text(readback.get("work_unit_fingerprint")),
        "action_fingerprint": _non_empty_text(identity.get("action_fingerprint"))
        or _non_empty_text(identity.get("work_unit_fingerprint"))
        or _non_empty_text(readback.get("action_fingerprint")),
        "route_identity_key": _non_empty_text(identity.get("route_identity_key"))
        or _non_empty_text(readback.get("route_identity_key")),
        "attempt_idempotency_key": _non_empty_text(identity.get("attempt_idempotency_key"))
        or _non_empty_text(readback.get("attempt_idempotency_key")),
        "idempotency_key": _non_empty_text(identity.get("idempotency_key"))
        or _non_empty_text(readback.get("idempotency_key"))
        or _non_empty_text(identity.get("attempt_idempotency_key")),
        "closeout_refs": _string_list(readback.get("closeout_refs")),
        "provider_completion_is_domain_completion": readback.get("provider_completion_is_domain_completion"),
        "provider_completion_is_domain_ready": readback.get("provider_completion_is_domain_ready"),
    }
    return {key: value for key, value in terminal.items() if value not in (None, "", [], {})}


def _closeout_only_study_handoff_projection(
    *,
    handoff_path: Path,
    latest_terminal_stage_log: Mapping[str, Any] | None,
    latest_typed_closeout: Mapping[str, Any] | None,
    study_id: str,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    source_payload = _mapping_copy(payload)
    terminal_stage_log = _observability_mapping(latest_terminal_stage_log)
    typed_closeout = _observability_mapping(latest_typed_closeout)
    projection = {
        "surface_kind": "opl_current_control_state_study_handoff",
        "read_model": "study_opl_current_control_state_handoff_projection",
        "authority": "observability_only",
        "source_path": str(handoff_path),
        "generated_at": _non_empty_text(source_payload.get("generated_at"))
        or _non_empty_text(terminal_stage_log.get("generated_at")),
        "study_id": study_id,
        "quest_status": None,
        "active_run_id": None,
        "active_stage_attempt_id": _non_empty_text(terminal_stage_log.get("stage_attempt_id"))
        or _non_empty_text(typed_closeout.get("execution_id")),
        "active_workflow_id": None,
        "running_provider_attempt": False,
        "runtime_health": {},
        "artifact_delta": {},
        "gate_specificity": {},
        "ai_reviewer_status": {},
        "stage_progress_log": {},
        "owner_route": {},
        "queue_slo": {},
        "owner_pickup_overdue": False,
        "developer_supervisor_attention_required": False,
        "action_queue": [],
        "why_not_applied": [],
        "next_owner": _non_empty_text(typed_closeout.get("next_owner")),
        "external_supervisor_required": False,
        "blocked_reason": _non_empty_text(typed_closeout.get("blocked_reason"))
        or _non_empty_text(terminal_stage_log.get("typed_blocker_reason")),
    }
    if terminal_stage_log:
        projection["latest_terminal_stage_log"] = dict(terminal_stage_log)
    if typed_closeout:
        projection["latest_typed_owner_callable_closeout"] = dict(typed_closeout)
        projection = _apply_typed_owner_callable_adapter_closeout_to_handoff(projection)
    projection.update(_opl_current_control_state_mode_fields(source_payload))
    return projection


def opl_current_control_state_live_attempt_handoff_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    runtime_liveness_audit: Mapping[str, Any],
) -> dict[str, Any] | None:
    if _non_empty_text(runtime_liveness_audit.get("source")) != "opl_current_control_state_provider_attempt":
        return None
    stage_progress_log = _stage_progress_log_mapping(runtime_liveness_audit.get("stage_progress_log"))
    source_path = _non_empty_text(runtime_liveness_audit.get("handoff_path")) or str(
        opl_current_control_state_handoff_path(profile=profile)
    )
    runtime_health = _copy_mapping_keys(
        runtime_liveness_audit.get("runtime_health"),
        (
            "health_status",
            "runtime_liveness_status",
            "summary",
            "blocked_reason",
            *ATTEMPT_IDENTITY_KEYS,
        ),
    )
    active_run_id = _non_empty_text(runtime_liveness_audit.get("active_run_id"))
    active_stage_attempt_id = _non_empty_text(runtime_liveness_audit.get("active_stage_attempt_id"))
    active_workflow_id = _non_empty_text(runtime_liveness_audit.get("active_workflow_id"))
    running_provider_attempt = _strict_running_provider_attempt(
        runtime_liveness_audit,
        active_run_id=active_run_id,
        active_stage_attempt_id=active_stage_attempt_id,
        active_workflow_id=active_workflow_id,
    )
    return {
        "surface_kind": "opl_current_control_state_provider_attempt_handoff",
        "read_model": "study_opl_current_control_state_handoff_projection",
        "authority": _non_empty_text(runtime_liveness_audit.get("authority")) or "observability_only",
        "source_path": source_path,
        "generated_at": _non_empty_text(runtime_liveness_audit.get("handoff_generated_at")),
        "study_id": study_id,
        "quest_status": None,
        "active_run_id": active_run_id,
        "active_stage_attempt_id": active_stage_attempt_id,
        "active_workflow_id": active_workflow_id,
        "running_provider_attempt": running_provider_attempt,
        "action_type": _non_empty_text(runtime_liveness_audit.get("action_type")),
        "work_unit_id": _work_unit_identity(runtime_liveness_audit.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(runtime_liveness_audit.get("work_unit_fingerprint")),
        "action_fingerprint": _non_empty_text(runtime_liveness_audit.get("action_fingerprint"))
        or _non_empty_text(runtime_liveness_audit.get("work_unit_fingerprint")),
        "runtime_owner": "one-person-lab" if running_provider_attempt else None,
        "provider_attempt_owner": "one-person-lab" if running_provider_attempt else None,
        "queue_owner": "one-person-lab" if running_provider_attempt else None,
        "runtime_health": runtime_health,
        "artifact_delta": {},
        "gate_specificity": {},
        "ai_reviewer_status": {},
        "stage_progress_log": stage_progress_log,
        "queue_slo": {},
        "owner_pickup_overdue": False,
        "developer_supervisor_attention_required": False,
        "action_queue": [],
        "why_not_applied": [],
        "next_owner": "supervisor_only/live_provider_attempt",
        "external_supervisor_required": False,
        "blocked_reason": None,
    }


def _copy_opl_transition_readback_fields(
    projection: dict[str, Any],
    source: Mapping[str, Any],
) -> None:
    readback = candidate_opl_transition_readback(source)
    if not readback:
        return
    projection["opl_domain_progress_transition_runtime_live_readback"] = readback
    projection["provider_admission_identity"] = _provider_admission_identity_from_readback(readback)
    _apply_non_advancing_apply_readback_to_handoff(projection, source=source, readback=readback)


def _apply_non_advancing_apply_readback_to_handoff(
    projection: dict[str, Any],
    *,
    source: Mapping[str, Any],
    readback: Mapping[str, Any],
) -> None:
    readback_container = _observability_mapping(
        source.get("domain_progress_transition_non_advancing_apply_readback")
    )
    non_advancing = non_advancing_apply_opl_transition_readback(
        {
            **readback_container,
            "opl_domain_progress_transition_runtime_live_readback": readback,
        }
    )
    if not non_advancing:
        return
    readback_identity = _provider_admission_identity_from_readback(non_advancing)
    study_id = (
        _non_empty_text(projection.get("study_id"))
        or _non_empty_text(readback_identity.get("study_id"))
    )
    action_type = (
        _non_empty_text(readback_container.get("action_type"))
        or _non_empty_text(projection.get("action_type"))
        or _non_empty_text(_observability_mapping(non_advancing.get("identity")).get("transition_kind"))
    )
    work_unit_id = _work_unit_identity(readback_container.get("work_unit_id")) or _work_unit_identity(
        readback_identity.get("work_unit_id")
    )
    work_unit_fingerprint = (
        _non_empty_text(readback_container.get("work_unit_fingerprint"))
        or _non_empty_text(readback_identity.get("work_unit_fingerprint"))
    )
    typed_blocker = {
        key: value
        for key, value in {
            "surface_kind": "mas_current_control_typed_blocker_projection",
            "blocker_type": "non_advancing_apply",
            "blocked_reason": _non_empty_text(readback_container.get("reason"))
            or "opl_transition_request_missing_for_authorized_stage_packet",
            "source": "opl_current_control_state.domain_progress_transition_non_advancing_apply_readback",
            "owner": "one-person-lab",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": action_type,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "route_identity_key": _non_empty_text(readback_identity.get("route_identity_key")),
            "attempt_idempotency_key": _non_empty_text(readback_identity.get("attempt_idempotency_key")),
            "request_idempotency_key": _non_empty_text(readback_identity.get("request_idempotency_key")),
            "stage_run_id": _non_empty_text(readback_identity.get("stage_run_id")),
            "event_id": _non_empty_text(readback_identity.get("event_id")),
            "outbox_item_id": _non_empty_text(readback_identity.get("outbox_item_id")),
            "transaction_id": _non_empty_text(readback_identity.get("transaction_id")),
            "non_advancing_apply": True,
            "provider_admission_allowed": False,
            "current_executable_owner_action_allowed": False,
            "paper_progress_delta": False,
            "provider_completion_is_domain_completion": False,
            "authority_boundary": _non_advancing_apply_authority_boundary(readback_container),
        }.items()
        if value not in (None, "", [], {})
    }
    projection["running_provider_attempt"] = False
    projection["active_run_id"] = None
    projection["active_workflow_id"] = None
    projection["current_executable_owner_action"] = None
    projection["provider_admission_pending_count"] = 0
    projection["provider_admission_candidates"] = []
    projection["transition_request_pending_count"] = 0
    projection["transition_request_candidates"] = []
    projection["blocked_reason"] = typed_blocker["blocked_reason"]
    projection["next_owner"] = "one-person-lab"
    projection["typed_blocker"] = typed_blocker
    projection["current_work_unit"] = {
        "surface_kind": "current_work_unit",
        "schema_version": 1,
        "status": "typed_blocker",
        "study_id": study_id,
        "quest_id": study_id,
        "owner": "one-person-lab",
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": work_unit_fingerprint,
        "state": {
            "state_kind": "typed_blocker",
            "source": "opl_current_control_state.domain_progress_transition_non_advancing_apply_readback",
            "typed_blocker": typed_blocker,
        },
    }
    projection["current_execution_envelope"] = {
        "state_kind": "typed_blocker",
        "owner": "one-person-lab",
        "source": "opl_current_control_state.domain_progress_transition_non_advancing_apply_readback",
        "typed_blocker": typed_blocker,
    }
    projection["domain_progress_transition_non_advancing_apply_readback"] = dict(readback_container)
    projection["domain_progress_transition_projection_metadata"] = _observability_mapping(
        source.get("domain_progress_transition_projection_metadata")
    )


def _non_advancing_apply_authority_boundary(readback_container: Mapping[str, Any]) -> dict[str, Any]:
    boundary = _observability_mapping(readback_container.get("authority_boundary"))
    return {
        **boundary,
        "projection_only": True,
        "runtime_owner": "one-person-lab",
        "domain_truth_owner": "med-autoscience",
        "can_authorize_provider_admission": False,
        "can_start_provider_attempt": False,
        "provider_running_is_paper_progress": False,
        "provider_completion_is_domain_completion": False,
        "paper_progress_delta": False,
    }


def _provider_admission_identity_from_readback(readback: Mapping[str, Any]) -> dict[str, Any]:
    identity = _observability_mapping(readback.get("identity"))
    aggregate_identity = _observability_mapping(identity.get("aggregate_identity"))
    stage_run_identity = _observability_mapping(identity.get("stage_run_identity"))
    return {
        key: value
        for key, value in {
            "study_id": _non_empty_text(aggregate_identity.get("study_id")),
            "work_unit_id": _work_unit_identity(aggregate_identity.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(
                aggregate_identity.get("work_unit_fingerprint")
            ),
            "route_identity_key": _non_empty_text(stage_run_identity.get("route_identity_key")),
            "attempt_idempotency_key": _non_empty_text(
                stage_run_identity.get("attempt_idempotency_key")
            ),
            "request_idempotency_key": _non_empty_text(identity.get("idempotency_key"))
            or _non_empty_text(identity.get("request_idempotency_key")),
            "stage_run_id": _non_empty_text(stage_run_identity.get("stage_run_id")),
            "event_id": _non_empty_text(identity.get("latest_event_id"))
            or _non_empty_text(identity.get("event_id")),
            "outbox_item_id": _non_empty_text(identity.get("latest_outbox_item_id"))
            or _non_empty_text(identity.get("outbox_item_id")),
            "transaction_id": _non_empty_text(identity.get("latest_transaction_id"))
            or _non_empty_text(identity.get("transaction_id")),
        }.items()
        if value is not None
    }


def merge_live_attempt_observability_into_handoff(
    *,
    handoff: dict[str, Any] | None,
    live_attempt_handoff: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if handoff is None:
        return live_attempt_handoff
    if live_attempt_handoff is None:
        return handoff
    active_run_id = _non_empty_text(handoff.get("active_run_id"))
    live_active_run_id = _non_empty_text(live_attempt_handoff.get("active_run_id"))
    if active_run_id and live_active_run_id and active_run_id != live_active_run_id:
        return handoff
    merged = dict(handoff)
    live_attempt_running = live_attempt_handoff.get("running_provider_attempt") is True
    if live_attempt_running and _live_attempt_supersedes_handoff_blocker(merged):
        merged["external_supervisor_required"] = False
        merged["blocked_reason"] = None
        merged.pop("typed_blocker", None)
        merged["why_not_applied"] = [
            reason
            for reason in _string_list(merged.get("why_not_applied"))
            if reason not in LIVE_ATTEMPT_SUPERSEDED_BLOCKERS
        ]
        if _non_empty_text(merged.get("next_owner")) in LIVE_ATTEMPT_SUPERSEDED_NEXT_OWNERS:
            merged["next_owner"] = _non_empty_text(live_attempt_handoff.get("next_owner"))
    for key in LIVE_ATTEMPT_HANDOFF_KEYS:
        if (
            key == "active_stage_attempt_id"
            and live_attempt_running
            and _handoff_live_attempt_identity_stale(
                handoff=merged,
                live_attempt_handoff=live_attempt_handoff,
            )
        ):
            merged[key] = live_attempt_handoff[key]
            continue
        if key not in merged or merged.get(key) in {None, "", False}:
            if key in live_attempt_handoff:
                merged[key] = live_attempt_handoff[key]
    if live_attempt_running:
        for key in ("runtime_owner", "provider_attempt_owner", "queue_owner"):
            value = _non_empty_text(live_attempt_handoff.get(key)) or "one-person-lab"
            merged[key] = value
    if not _stage_progress_log_mapping(merged.get("stage_progress_log")):
        stage_progress_log = _stage_progress_log_mapping(live_attempt_handoff.get("stage_progress_log"))
        if stage_progress_log:
            merged["stage_progress_log"] = stage_progress_log
    live_runtime_health = _copy_mapping_keys(
        live_attempt_handoff.get("runtime_health"),
        ("health_status", "runtime_liveness_status", "summary", "blocked_reason"),
    )
    if live_runtime_health and (
        live_attempt_running
        or not _copy_mapping_keys(merged.get("runtime_health"), ("health_status", "runtime_liveness_status"))
    ):
        merged["runtime_health"] = live_runtime_health
    if live_attempt_running:
        merged = bind_live_attempt_to_handoff_identity(
            handoff=merged,
            live_attempt_handoff=live_attempt_handoff,
        )
    return _apply_matching_terminal_closeout_to_handoff(merged)
