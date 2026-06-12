from __future__ import annotations

from pathlib import Path
from typing import Any

from .progression import _domain_transition_route_repair
from .shared import (
    _mapping_copy,
    _non_empty_text,
    _read_json_object,
    _route_repair_summary,
    _timestamp_is_newer,
)


def progress_projection_respecting_current_domain_truth(
    *,
    study_root: Path,
    publication_eval_payload: dict[str, Any] | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    blockers = _current_blockers_respecting_controller_closure(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
        blockers=[
            str(item)
            for item in payload.get("current_blockers") or []
            if str(item or "").strip()
        ],
    )
    updated = dict(payload)
    changed = False
    if publication_eval_payload is not None and updated.get("publication_eval") != publication_eval_payload:
        updated["publication_eval"] = publication_eval_payload
        changed = True
    blockers_changed = blockers != payload.get("current_blockers")
    if blockers_changed:
        updated["current_blockers"] = blockers
        changed = True
    refreshed = _progress_projection_suppressing_stale_opl_route(updated)
    if refreshed is not updated:
        updated = refreshed
        changed = True
    if not changed:
        return payload
    if blockers_changed:
        user_visible = _mapping_copy(updated.get("user_visible_projection"))
        if user_visible:
            user_visible["current_blockers"] = blockers
            updated["user_visible_projection"] = user_visible
        status_contract = _mapping_copy(updated.get("status_narration_contract"))
        if status_contract:
            status_contract["current_blockers"] = blockers[:8]
            updated["status_narration_contract"] = status_contract
    return updated


def _current_blockers_respecting_controller_closure(
    *,
    study_root: Path,
    publication_eval_payload: dict[str, Any] | None,
    blockers: list[str],
) -> list[str]:
    if not _submission_authority_sync_closed_for_eval(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    ):
        return blockers
    return [
        blocker
        for blocker in blockers
        if _non_empty_text(blocker) != "stale_submission_minimal_authority"
    ]


def _progress_projection_suppressing_stale_opl_route(payload: dict[str, Any]) -> dict[str, Any]:
    handoff = _mapping_copy(payload.get("opl_current_control_state_handoff"))
    if _handoff_is_live_provider_attempt(handoff):
        return payload
    baseline = (
        _non_empty_text(handoff.get("generated_at"))
        or _non_empty_text(handoff.get("updated_at"))
        or _non_empty_text(handoff.get("recorded_at"))
    )
    lifecycle = _mapping_copy(payload.get("ai_repair_lifecycle"))
    intervention_lane = _mapping_copy(payload.get("intervention_lane"))
    if domain_truth_satisfies_opl_runtime_owner_route(
        payload,
        handoff,
    ) or domain_truth_satisfies_opl_runtime_owner_route(
        payload,
        intervention_lane,
    ):
        return _progress_projection_refreshing_route_back(payload)
    if baseline is None:
        baseline = _non_empty_text(lifecycle.get("last_apply_attempt_at"))
    if baseline is None:
        for item in payload.get("latest_events") or []:
            event = _mapping_copy(item)
            category = _non_empty_text(event.get("category"))
            source = _non_empty_text(event.get("source"))
            if category != "opl_runtime_owner_handoff" and source != "opl_runtime_owner_handoff":
                continue
            candidate = _non_empty_text(event.get("timestamp"))
            if candidate is not None and (baseline is None or _timestamp_is_newer(candidate, baseline)):
                baseline = candidate
    if not domain_truth_supersedes_opl_runtime_owner_route(payload.get("latest_events"), baseline=baseline):
        return payload
    if (
        _non_empty_text(handoff.get("blocked_reason")) != "quest_waiting_opl_runtime_owner_route"
        and _non_empty_text(lifecycle.get("blocked_reason")) != "quest_waiting_opl_runtime_owner_route"
        and _non_empty_text(intervention_lane.get("route_key_question")) != "quest_waiting_opl_runtime_owner_route"
    ):
        return payload
    return _progress_projection_refreshing_route_back(payload)


def domain_truth_supersedes_ai_repair_lifecycle(
    lifecycle_payload: dict[str, Any] | None,
    *,
    latest_events: object,
) -> bool:
    lifecycle = dict(lifecycle_payload or {})
    if _non_empty_text(lifecycle.get("blocked_reason")) != "quest_waiting_opl_runtime_owner_route":
        return False
    if (
        _non_empty_text(lifecycle.get("next_owner")) != "external_supervisor"
        and lifecycle.get("external_supervisor_required") is not True
    ):
        return False
    lifecycle_timestamp = (
        _non_empty_text(lifecycle.get("last_apply_attempt_at"))
        or _non_empty_text(lifecycle.get("generated_at"))
        or _non_empty_text(lifecycle.get("updated_at"))
        or _non_empty_text(lifecycle.get("emitted_at"))
        or _non_empty_text(lifecycle.get("recorded_at"))
    )
    if lifecycle_timestamp is None:
        return False
    return domain_truth_supersedes_opl_runtime_owner_route(latest_events, baseline=lifecycle_timestamp)


def domain_truth_satisfies_opl_runtime_owner_route(
    payload: dict[str, Any],
    route_payload: dict[str, Any] | None,
) -> bool:
    route = dict(route_payload or {})
    if not _route_waits_for_opl_runtime_owner(route):
        return False
    transition = _mapping_copy(payload.get("domain_transition"))
    receipt = _mapping_copy(transition.get("completion_receipt_consumption"))
    if _non_empty_text(receipt.get("status")) != "consumed":
        return False
    if _non_empty_text(transition.get("owner")) == "external_supervisor":
        return False
    receipt_ref = _non_empty_text(receipt.get("receipt_ref"))
    if receipt_ref is not None and "publication_eval" not in receipt_ref:
        return False
    route_work_unit_id = _route_work_unit_id(route)
    transition_work_unit_id = _non_empty_text(_mapping_copy(transition.get("next_work_unit")).get("unit_id"))
    if route_work_unit_id is not None and transition_work_unit_id is not None:
        return route_work_unit_id == transition_work_unit_id
    return True


def _route_waits_for_opl_runtime_owner(route: dict[str, Any]) -> bool:
    owner_route = _mapping_copy(route.get("owner_route"))
    why_not_applied = {
        _non_empty_text(item)
        for item in route.get("why_not_applied") or []
        if _non_empty_text(item) is not None
    }
    return (
        _non_empty_text(route.get("blocked_reason")) == "quest_waiting_opl_runtime_owner_route"
        or _non_empty_text(route.get("route_key_question")) == "quest_waiting_opl_runtime_owner_route"
        or _non_empty_text(owner_route.get("owner_reason")) == "quest_waiting_opl_runtime_owner_route"
        or _non_empty_text(owner_route.get("failure_signature")) == "quest_waiting_opl_runtime_owner_route"
        or "quest_waiting_opl_runtime_owner_route" in why_not_applied
    )


def _route_work_unit_id(route: dict[str, Any]) -> str | None:
    owner_route = _mapping_copy(route.get("owner_route"))
    source_refs = _mapping_copy(owner_route.get("source_refs"))
    currentness = _mapping_copy(source_refs.get("owner_route_currentness_basis"))
    return (
        _non_empty_text(route.get("work_unit_id"))
        or _non_empty_text(source_refs.get("work_unit_id"))
        or _non_empty_text(currentness.get("work_unit_id"))
    )


def domain_truth_supersedes_opl_runtime_owner_route(latest_events: object, *, baseline: object) -> bool:
    baseline_text = _non_empty_text(baseline)
    if baseline_text is None or not isinstance(latest_events, list):
        return False
    for item in latest_events:
        event = _mapping_copy(item)
        category = _non_empty_text(event.get("category"))
        source = _non_empty_text(event.get("source"))
        if category not in {"controller_decision", "publication_eval"} and source not in {
            "controller_decision",
            "publication_eval",
        }:
            continue
        if _timestamp_is_newer(event.get("timestamp"), baseline_text):
            return True
    return False


def _progress_projection_refreshing_route_back(payload: dict[str, Any]) -> dict[str, Any]:
    updated = dict(payload)
    updated["opl_current_control_state_handoff"] = None
    updated["ai_repair_lifecycle"] = None
    route_repair = _domain_transition_route_repair(updated)
    route_summary = _route_repair_summary(route_repair)
    if route_summary is not None:
        updated["next_system_action"] = route_summary
        domain_transition = _mapping_copy(updated.get("domain_transition"))
        owner = _non_empty_text(domain_transition.get("owner")) or _non_empty_text(
            domain_transition.get("route_target")
        )
        macro_state = _mapping_copy(updated.get("study_macro_state"))
        macro_details = _mapping_copy(macro_state.get("details"))
        if owner is not None:
            macro_details["decision_owner"] = owner
            macro_details["route_owner"] = owner
            macro_state["details"] = macro_details
            updated["study_macro_state"] = macro_state
        user_visible = _mapping_copy(updated.get("user_visible_projection"))
        if user_visible:
            user_visible["next_system_action"] = route_summary
            user_visible["next_step"] = route_summary
            if owner is not None:
                user_visible["next_owner"] = owner
            paper_progress = _mapping_copy(user_visible.get("paper_progress_state"))
            if paper_progress and owner is not None:
                paper_progress["next_owner"] = owner
                user_visible["paper_progress_state"] = paper_progress
            updated["user_visible_projection"] = user_visible
        status_contract = _mapping_copy(updated.get("status_narration_contract"))
        if status_contract:
            status_contract["next_step"] = route_summary
            updated["status_narration_contract"] = status_contract
        for key in ("operator_verdict", "recovery_contract", "autonomy_contract"):
            surface = _mapping_copy(updated.get(key))
            if not surface:
                continue
            if key == "autonomy_contract":
                surface["next_signal"] = route_summary
            else:
                surface["summary"] = route_summary
                if "reason_summary" in surface:
                    surface["reason_summary"] = route_summary
            if isinstance(route_repair, dict):
                for lane_key in (
                    "route_target",
                    "route_target_label",
                    "route_key_question",
                    "action_type",
                    "work_unit_id",
                ):
                    if route_repair.get(lane_key) not in (None, "", [], {}):
                        surface[lane_key] = route_repair[lane_key]
            updated[key] = surface
    intervention_lane = _mapping_copy(updated.get("intervention_lane"))
    if intervention_lane and isinstance(route_repair, dict):
        for lane_key in (
            "route_target",
            "route_target_label",
            "route_key_question",
            "route_rationale",
            "route_summary",
            "work_unit_id",
            "action_type",
        ):
            if route_repair.get(lane_key) not in (None, "", [], {}):
                intervention_lane[lane_key] = route_repair[lane_key]
        if route_repair.get("action_type") not in (None, "", [], {}):
            intervention_lane["recommended_action_id"] = route_repair["action_type"]
        intervention_lane.pop("handoff_source", None)
        if route_summary is not None:
            intervention_lane["summary"] = route_summary
        updated["intervention_lane"] = intervention_lane
    refs = _mapping_copy(updated.get("refs"))
    if refs:
        refs["ai_repair_lifecycle_path"] = None
        refs["opl_current_control_state_handoff_path"] = None
        updated["refs"] = refs
    return updated


def _handoff_is_live_provider_attempt(handoff: dict[str, Any]) -> bool:
    return (
        _non_empty_text(handoff.get("surface_kind")) == "opl_current_control_state_provider_attempt_handoff"
        and handoff.get("running_provider_attempt") is True
    )


def _submission_authority_sync_closed_for_eval(
    *,
    study_root: Path,
    publication_eval_payload: dict[str, Any] | None,
) -> bool:
    current_eval_id = _non_empty_text((publication_eval_payload or {}).get("eval_id"))
    if current_eval_id is None:
        return False
    lifecycle = _read_json_object(
        study_root / "artifacts" / "controller" / "publication_work_unit_lifecycle" / "latest.json"
    )
    freshness = _read_json_object(
        study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json"
    )
    return (
        _non_empty_text((lifecycle or {}).get("source_eval_id")) == current_eval_id
        and _non_empty_text((lifecycle or {}).get("status")) == "done"
        and _non_empty_text((freshness or {}).get("source_eval_id")) == current_eval_id
        and _non_empty_text((freshness or {}).get("status")) == "fresh"
    )


__all__ = [
    "_current_blockers_respecting_controller_closure",
    "domain_truth_supersedes_ai_repair_lifecycle",
    "progress_projection_respecting_current_domain_truth",
]
