from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from med_autoscience.controllers.runtime_supervisor_scan_parts import current_truth_owner
from med_autoscience.controllers.runtime_supervisor_scan_parts import pending_user_messages
from med_autoscience.publication_eval_specificity_targets import specificity_target_status

DOWNSTREAM_PACKAGE_FRESHNESS_WORK_UNIT_IDS = {
    "publication_gate_replay",
    "submission_authority_sync_closure",
    "submission_delivery_sync_closure",
    "submission_minimal_refresh",
}
RUNTIME_PLATFORM_REPAIR_SOURCE = "runtime_supervisor_scan_platform_repair"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def text(value: object) -> str | None:
    item = str(value or "").strip()
    return item or None


def mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def controller_action_types(payload: Mapping[str, Any]) -> set[str]:
    actions = payload.get("controller_actions")
    if not isinstance(actions, list):
        return set()
    action_types: set[str] = set()
    for action in actions:
        if isinstance(action, Mapping):
            action_text = text(action.get("action_type"))
            if action_text is not None:
                action_types.add(action_text)
        elif (action_text := text(action)) is not None:
            action_types.add(action_text)
    return action_types


def mapping_has_actionable_controller_target(payload: Mapping[str, Any]) -> bool:
    actionable_keys = {
        "claim_id",
        "claim_ref",
        "figure_id",
        "figure_ref",
        "table_id",
        "table_ref",
        "metric_id",
        "metric_ref",
        "citation_id",
        "citation_ref",
        "evidence_row_id",
        "evidence_row_ref",
        "package_artifact",
        "artifact_path",
        "source_path",
    }
    if any(text(payload.get(key)) for key in actionable_keys):
        return True
    for key in (
        "blocking_artifact_refs",
        "blocker_details",
        "gate_blocker_details",
        "specificity_targets",
        "work_unit_targets",
        "gaps",
    ):
        value = payload.get(key)
        if isinstance(value, Mapping) and mapping_has_actionable_controller_target(value):
            return True
        if isinstance(value, list):
            for item in value:
                if isinstance(item, Mapping) and mapping_has_actionable_controller_target(item):
                    return True
    return False


def publication_action_for_work_unit(
    *,
    publication_eval_payload: Mapping[str, Any],
    work_unit_fingerprint: str | None,
) -> dict[str, Any] | None:
    if work_unit_fingerprint is None:
        return None
    actions = publication_eval_payload.get("recommended_actions")
    if not isinstance(actions, list):
        return None
    for action in actions:
        if not isinstance(action, Mapping):
            continue
        next_work_unit = mapping(action.get("next_work_unit"))
        action_fingerprint = text(action.get("work_unit_fingerprint")) or text(next_work_unit.get("fingerprint"))
        if action_fingerprint == work_unit_fingerprint and mapping_has_actionable_controller_target(action):
            return dict(action)
    return None


def current_controller_authorization_payload(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
    read_json_object: Callable[[Path], dict[str, Any] | None],
    allow_specificity_work_unit: bool = False,
) -> dict[str, Any] | None:
    route = current_truth_owner.current_controller_runtime_route(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if route is None:
        if not allow_specificity_work_unit:
            return None
        route = specificity_controller_runtime_route(
            study_root=study_root,
            publication_eval_payload=publication_eval_payload,
            read_json_object=read_json_object,
        )
        if route is None:
            return None
    decision = read_json_object(Path(str(route["decision_path"])))
    if decision is None:
        return None
    work_unit = mapping(decision.get("next_work_unit"))
    work_unit_fingerprint = text(route.get("work_unit_fingerprint"))
    publication_action = publication_action_for_work_unit(
        publication_eval_payload=publication_eval_payload,
        work_unit_fingerprint=work_unit_fingerprint,
    )
    if publication_action is None:
        return None
    authorization: dict[str, Any] = {
        "decision_id": text(decision.get("decision_id")),
        "route_target": text(decision.get("route_target")),
        "work_unit_id": text(work_unit.get("unit_id")),
        "work_unit_fingerprint": work_unit_fingerprint,
        "publication_eval_id": text(publication_eval_payload.get("eval_id")),
        "publication_eval_ref": mapping(decision.get("publication_eval_ref")),
        "next_work_unit": _target_ready_next_work_unit(work_unit, publication_action),
        "controller_actions": sorted(controller_action_types(decision)),
        "source": RUNTIME_PLATFORM_REPAIR_SOURCE,
        "authorized_at": utc_now(),
    }
    for key in (
        "specificity_targets",
        "work_unit_targets",
        "blocking_artifact_refs",
        "blocker_details",
        "gate_blocker_details",
        "gaps",
        "source_path",
    ):
        if key in publication_action:
            authorization[key] = publication_action[key]
    return authorization


def _target_ready_next_work_unit(
    work_unit: Mapping[str, Any],
    publication_action: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(work_unit)
    if (
        text(payload.get("unit_id")) in current_truth_owner.SPECIFICITY_WORK_UNIT_IDS
        and specificity_target_status(publication_action.get("specificity_targets")).get("complete") is True
    ):
        payload.pop("non_executable_reason", None)
        payload.pop("required_target_kinds", None)
        if payload.get("controller_work_unit_executable") is False:
            payload.pop("controller_work_unit_executable", None)
    return payload


def specificity_controller_runtime_route(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
    read_json_object: Callable[[Path], dict[str, Any] | None],
) -> dict[str, Any] | None:
    decision_path = Path(study_root).expanduser().resolve() / "artifacts" / "controller_decisions" / "latest.json"
    decision = read_json_object(decision_path)
    if decision is None or decision.get("requires_human_confirmation") is True:
        return None
    work_unit = mapping(decision.get("next_work_unit"))
    work_unit_id = text(work_unit.get("unit_id"))
    if work_unit_id not in current_truth_owner.SPECIFICITY_WORK_UNIT_IDS:
        return None
    decision_fingerprint = text(decision.get("work_unit_fingerprint")) or text(work_unit.get("fingerprint"))
    publication_action = publication_action_for_work_unit(
        publication_eval_payload=publication_eval_payload,
        work_unit_fingerprint=decision_fingerprint,
    )
    if publication_action is None:
        return None
    return {
        "decision_path": str(decision_path),
        "decision_id": text(decision.get("decision_id")),
        "controller_actions": sorted(controller_action_types(decision)),
        "route_target": text(decision.get("route_target")),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": decision_fingerprint,
    }


def write_current_controller_authorization(
    *,
    runtime_state_path: Path,
    study_root: Path,
    study_id: str,
    quest_id: str | None,
    publication_eval_payload: Mapping[str, Any],
    read_json_object: Callable[[Path], dict[str, Any] | None],
    write_json: Callable[[Path, Mapping[str, Any]], None],
    append_json_line: Callable[[Path, Mapping[str, Any]], None],
    continuation_reason: str = "controller_work_unit_pending",
    repair_clear_reason: str = "current_controller_authorization",
    repair_extra: Mapping[str, Any] | None = None,
    allow_specificity_work_unit: bool = False,
    allow_pending_control_messages: bool = False,
    preserve_live_worker_state: bool = True,
) -> dict[str, Any] | None:
    authorization = current_controller_authorization_payload(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
        read_json_object=read_json_object,
        allow_specificity_work_unit=allow_specificity_work_unit,
    )
    if authorization is None:
        return None
    runtime_state = read_json_object(runtime_state_path)
    if runtime_state is None:
        return {"written": False, "reason": "runtime_state_missing_or_invalid", "path": str(runtime_state_path)}
    if pending_user_messages.pending_count(runtime_state) > 0 and not (
        allow_pending_control_messages
        and pending_user_messages.only_control_plane_messages(
            runtime_state_path=runtime_state_path,
            expected_count=pending_user_messages.pending_count(runtime_state),
        )
    ):
        return {"written": False, "reason": "pending_user_messages_present", "path": str(runtime_state_path)}
    preserved_active_run_id = text(runtime_state.get("active_run_id"))
    preserve_worker_state = (
        preserve_live_worker_state
        and runtime_state.get("worker_running") is True
        and preserved_active_run_id is not None
    )
    runtime_state["quest_id"] = text(runtime_state.get("quest_id")) or quest_id
    if not preserve_worker_state:
        runtime_state["active_run_id"] = None
        runtime_state["worker_running"] = False
    runtime_state["continuation_policy"] = "auto"
    runtime_state["continuation_anchor"] = "decision"
    runtime_state["continuation_reason"] = continuation_reason
    runtime_state["continuation_updated_at"] = utc_now()
    runtime_state["same_fingerprint_auto_turn_count"] = 0
    runtime_state["last_controller_decision_authorization"] = authorization
    cleared_keys: list[str] = []
    for key in (
        "retry_state",
        "last_stage_fingerprint",
        "last_stage_fingerprint_at",
        "blocked_turn_closeout",
        "last_liveness_reconcile_reason",
    ):
        if key in runtime_state:
            cleared_keys.append(key)
        runtime_state.pop(key, None)
    runtime_state["last_runtime_platform_repair"] = {
        "study_id": study_id,
        "quest_id": quest_id,
        "source": RUNTIME_PLATFORM_REPAIR_SOURCE,
        "clear_reason": repair_clear_reason,
        "cleared_keys": cleared_keys,
        "worker_state_preserved": preserve_worker_state,
        "preserved_active_run_id": preserved_active_run_id if preserve_worker_state else None,
        "applied_at": utc_now(),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
    }
    if repair_extra:
        runtime_state["last_runtime_platform_repair"].update(dict(repair_extra))
    write_json(runtime_state_path, runtime_state)
    append_json_line(
        runtime_state_path.parent / "events.jsonl",
        {
            "event_id": f"mas-runtime-platform-repair::{study_id}::{utc_now()}",
            "type": "mas.current_controller_authorization",
            "study_id": study_id,
            "quest_id": quest_id,
            "source": RUNTIME_PLATFORM_REPAIR_SOURCE,
            "work_unit_id": authorization.get("work_unit_id"),
            "work_unit_fingerprint": authorization.get("work_unit_fingerprint"),
            "cleared_keys": cleared_keys,
            "worker_state_preserved": preserve_worker_state,
            "preserved_active_run_id": preserved_active_run_id if preserve_worker_state else None,
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "created_at": utc_now(),
        },
    )
    return {
        "written": True,
        "path": str(runtime_state_path),
        "decision_id": authorization.get("decision_id"),
        "work_unit_id": authorization.get("work_unit_id"),
        "work_unit_fingerprint": authorization.get("work_unit_fingerprint"),
        "cleared_keys": cleared_keys,
        "worker_state_preserved": preserve_worker_state,
        "preserved_active_run_id": preserved_active_run_id if preserve_worker_state else None,
    }


def controller_authorization_points_to_upstream_work_unit(
    controller_authorization: Mapping[str, Any] | None,
) -> bool:
    authorization = mapping(controller_authorization)
    if not authorization:
        return False
    work_unit_id = text(authorization.get("work_unit_id")) or text(mapping(authorization.get("next_work_unit")).get("unit_id"))
    return work_unit_id is not None and work_unit_id not in DOWNSTREAM_PACKAGE_FRESHNESS_WORK_UNIT_IDS


def string_items(value: object) -> list[str]:
    if isinstance(value, str):
        item = value.strip()
        return [item] if item else []
    if not isinstance(value, Iterable) or isinstance(value, Mapping | bytes):
        return []
    return list(dict.fromkeys(item for value_item in value if (item := text(value_item)) is not None))


__all__ = [
    "controller_action_types",
    "controller_authorization_points_to_upstream_work_unit",
    "current_controller_authorization_payload",
    "mapping_has_actionable_controller_target",
    "publication_action_for_work_unit",
    "specificity_controller_runtime_route",
    "write_current_controller_authorization",
]
