from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    mapping as _mapping,
    non_empty_text as _non_empty_text,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission import (
    _study_current_action_for_provider_admission,
)
from med_autoscience.runtime_control import owner_route_attempt_protocol


def same_tick_candidate_with_stage_run_identity(candidate: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(candidate)
    study_id = _non_empty_text(payload.get("study_id"))
    fingerprint = _non_empty_text(payload.get("work_unit_fingerprint")) or _non_empty_text(
        payload.get("action_fingerprint")
    )
    route_key = _non_empty_text(payload.get("route_identity_key"))
    if route_key is None and study_id is not None and fingerprint is not None:
        route_key = f"provider-admission::{study_id}::{fingerprint}"
    attempt_key = _non_empty_text(payload.get("attempt_idempotency_key")) or route_key
    dispatch_ref = _non_empty_text(payload.get("dispatch_ref")) or _non_empty_text(payload.get("dispatch_path"))
    stage_packet_ref = _non_empty_text(payload.get("stage_packet_ref"))
    stage_packet_refs = same_tick_text_items(payload.get("stage_packet_refs"))
    if stage_packet_ref is not None and stage_packet_ref not in stage_packet_refs:
        stage_packet_refs.append(stage_packet_ref)
    for key, value in {
        "dispatch_ref": dispatch_ref,
        "stage_packet_ref": stage_packet_ref,
        "route_identity_key": route_key,
        "attempt_idempotency_key": attempt_key,
        "idempotency_key": attempt_key,
    }.items():
        if value is not None:
            payload[key] = value
    if stage_packet_refs:
        payload["stage_packet_refs"] = stage_packet_refs
        payload.setdefault("checkpoint_refs", list(stage_packet_refs))
    source_refs = dict(_mapping(payload.get("source_refs")))
    for key, value in {
        "dispatch_ref": dispatch_ref,
        "stage_packet_ref": stage_packet_ref,
        "route_identity_key": route_key,
        "attempt_idempotency_key": attempt_key,
    }.items():
        if value is not None:
            source_refs[key] = value
    if stage_packet_refs:
        source_refs["stage_packet_refs"] = stage_packet_refs
    if source_refs:
        payload["source_refs"] = source_refs
    return payload


def same_tick_text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _non_empty_text(value)
        return [text] if text is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        text = _non_empty_text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def same_tick_progress_current_actions(
    progress_currentness: Mapping[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    current_actions: dict[str, dict[str, Any]] = {}
    for study_id, payload in _mapping(progress_currentness).items():
        normalized_study_id = _non_empty_text(study_id)
        if normalized_study_id is None:
            continue
        current = _mapping(_mapping(payload).get("current_executable_owner_action"))
        if not current:
            continue
        current_work_unit = _mapping(_mapping(payload).get("current_work_unit"))
        current_work_unit_basis = _mapping(current_work_unit.get("currentness_basis"))
        next_action = _mapping(current.get("next_action"))
        repair_precedence = _mapping(current.get("repair_progress_precedence"))
        current_action_basis = owner_route_attempt_protocol.normalize_currentness_sources(
            _mapping(current.get("currentness_basis")),
            _mapping(current.get("owner_route_currentness_basis")),
            {
                "source_eval_id": current.get("source_eval_id"),
                "source_fingerprint": current.get("source_fingerprint"),
                "work_unit_id": current.get("work_unit_id") or next_action.get("action_id"),
                "work_unit_fingerprint": current.get("work_unit_fingerprint")
                or current.get("action_fingerprint"),
                "action_fingerprint": current.get("action_fingerprint")
                or current.get("work_unit_fingerprint"),
            },
            current_work_unit_basis,
        )
        allowed_actions = same_tick_text_items(current.get("allowed_actions"))
        explicit_fingerprints = same_tick_text_items(
            [
                current.get("work_unit_fingerprint"),
                current.get("action_fingerprint"),
                current.get("source_fingerprint"),
                repair_precedence.get("source_fingerprint"),
                current_work_unit.get("work_unit_fingerprint"),
                current_work_unit.get("action_fingerprint"),
                current_work_unit_basis.get("work_unit_fingerprint"),
                current_work_unit_basis.get("source_fingerprint"),
            ]
        )
        projected_action = _study_current_action_for_provider_admission(
            {
                "study_id": normalized_study_id,
                "quest_id": _non_empty_text(_mapping(payload).get("quest_id")) or normalized_study_id,
                "current_executable_owner_action": dict(current),
                **(
                    {"current_work_unit": dict(_mapping(_mapping(payload).get("current_work_unit")))}
                    if _mapping(_mapping(payload).get("current_work_unit"))
                    else {}
                ),
                **(
                    {"domain_transition": dict(_mapping(_mapping(payload).get("domain_transition")))}
                    if _mapping(_mapping(payload).get("domain_transition"))
                    else {}
                ),
                **(
                    {
                        "progress_first_monitoring_summary": dict(
                            _mapping(_mapping(payload).get("progress_first_monitoring_summary"))
                        )
                    }
                    if _mapping(_mapping(payload).get("progress_first_monitoring_summary"))
                    else {}
                ),
                **(
                    {"intervention_lane": dict(_mapping(_mapping(payload).get("intervention_lane")))}
                    if _mapping(_mapping(payload).get("intervention_lane"))
                    else {}
                ),
            }
        )
        if projected_action is not None:
            explicit_fingerprints.extend(
                same_tick_text_items(
                    [
                        projected_action.get("work_unit_fingerprint"),
                        projected_action.get("action_fingerprint"),
                    ]
                )
            )
        current_actions[normalized_study_id] = {
            "action_type": _non_empty_text(current.get("action_type")),
            "action_ids": list(
                dict.fromkeys(
                    [
                        *allowed_actions,
                        *same_tick_text_items([current.get("action_type"), next_action.get("action_id")]),
                    ]
                )
            ),
            "work_unit_id": _non_empty_text(current.get("work_unit_id"))
            or _non_empty_text(next_action.get("action_id")),
            "currentness_basis": current_action_basis or None,
            "explicit_fingerprints": _same_tick_current_action_fingerprints(
                current=current,
                work_unit_id=(
                    _non_empty_text(current.get("work_unit_id"))
                    or _non_empty_text(next_action.get("action_id"))
                ),
                existing_fingerprints=explicit_fingerprints,
            ),
            "source_ref": _non_empty_text(current.get("source_ref"))
            or _non_empty_text(current.get("latest_owner_answer_ref")),
        }
    return current_actions


def same_tick_candidate_matches_current_action(
    candidate: Mapping[str, Any],
    *,
    current_action_identity: Mapping[str, Any],
) -> bool:
    action_type = _non_empty_text(candidate.get("action_type"))
    work_unit_id = _non_empty_text(candidate.get("work_unit_id"))
    work_unit_fingerprint = _non_empty_text(candidate.get("work_unit_fingerprint")) or _non_empty_text(
        candidate.get("action_fingerprint")
    )
    if action_type is None:
        return False
    expected_action_type = _non_empty_text(current_action_identity.get("action_type"))
    if expected_action_type is not None and action_type != expected_action_type:
        return False
    action_ids = {
        item
        for item in same_tick_text_items(current_action_identity.get("action_ids"))
    }
    if action_ids and action_type not in action_ids:
        return False
    expected_work_unit_id = _non_empty_text(current_action_identity.get("work_unit_id"))
    if expected_work_unit_id is not None and work_unit_id != expected_work_unit_id:
        return False
    expected_fingerprints = {
        fingerprint
        for fingerprint in same_tick_text_items(current_action_identity.get("explicit_fingerprints"))
        if not _same_tick_synthetic_current_owner_ticket(fingerprint)
    }
    if expected_fingerprints:
        return work_unit_fingerprint in expected_fingerprints
    expected_source_ref = _non_empty_text(current_action_identity.get("source_ref"))
    if expected_source_ref is not None:
        return work_unit_fingerprint is not None and expected_source_ref in work_unit_fingerprint
    if _same_tick_materialized_candidate(candidate):
        return False
    return True


def _same_tick_current_action_fingerprints(
    *,
    current: Mapping[str, Any],
    work_unit_id: str | None,
    existing_fingerprints: list[str],
) -> list[str]:
    fingerprints = list(existing_fingerprints)
    source_ref = _non_empty_text(current.get("source_ref")) or _non_empty_text(
        current.get("latest_owner_answer_ref")
    )
    target_surface = _mapping(current.get("target_surface"))
    surface_key = _non_empty_text(current.get("surface_key")) or _non_empty_text(
        target_surface.get("surface_key")
    )
    if work_unit_id is not None and source_ref is not None:
        fingerprints.append(
            "stage-current-owner-delta::"
            f"{work_unit_id}::{surface_key or 'unspecified_surface'}::{source_ref}"
        )
    return list(dict.fromkeys(fingerprints))


def _same_tick_materialized_candidate(candidate: Mapping[str, Any]) -> bool:
    if candidate.get("same_tick_materialized_provider_admission") is True:
        return True
    return _non_empty_text(candidate.get("source")) == "same_tick_materialized_dispatch"


def _same_tick_synthetic_current_owner_ticket(value: object) -> bool:
    text = _non_empty_text(value)
    return bool(text and text.startswith("study-progress-current-owner-ticket::"))


__all__ = [
    "same_tick_candidate_matches_current_action",
    "same_tick_candidate_with_stage_run_identity",
    "same_tick_progress_current_actions",
    "same_tick_text_items",
]
