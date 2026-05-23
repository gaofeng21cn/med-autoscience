from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from med_autoscience.controllers.owner_route_reconcile_parts import current_truth_owner
from med_autoscience.controllers.story_surface_work_units import (
    is_story_surface_delta_write_work_unit,
)
from med_autoscience.publication_eval_specificity_targets import specificity_target_status

DOWNSTREAM_PACKAGE_FRESHNESS_WORK_UNIT_IDS = {
    "publication_gate_replay",
    "submission_authority_sync_closure",
    "submission_delivery_sync_closure",
    "submission_minimal_refresh",
}
CURRENT_CONTROLLER_AUTHORIZATION_SOURCE = "owner_route_reconcile_current_controller_authorization"


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
    action_types = controller_action_types(decision)
    publication_action = publication_action_for_work_unit(
        publication_eval_payload=publication_eval_payload,
        work_unit_fingerprint=work_unit_fingerprint,
    )
    domain_transition_allowed = current_truth_owner.domain_transition_runtime_route_allowed(
        work_unit_fingerprint=work_unit_fingerprint,
        action_types=action_types,
        work_unit_id=text(work_unit.get("unit_id")),
    )
    methodology_reframe_allowed = current_truth_owner.methodology_reframe_runtime_route_allowed(
        decision=decision,
        work_unit=work_unit,
        work_unit_fingerprint=work_unit_fingerprint,
        action_types=action_types,
        work_unit_id=text(work_unit.get("unit_id")),
    )
    if publication_action is None and not domain_transition_allowed and not methodology_reframe_allowed:
        return None
    authorization: dict[str, Any] = {
        "decision_id": text(decision.get("decision_id")),
        "route_target": text(decision.get("route_target")),
        "work_unit_id": text(work_unit.get("unit_id")),
        "work_unit_fingerprint": work_unit_fingerprint,
        "publication_eval_id": text(publication_eval_payload.get("eval_id")),
        "publication_eval_ref": mapping(decision.get("publication_eval_ref")),
        "next_work_unit": _target_ready_next_work_unit(work_unit, publication_action or {}),
        "controller_actions": sorted(action_types),
        "source": CURRENT_CONTROLLER_AUTHORIZATION_SOURCE,
        "authorized_at": utc_now(),
    }
    if domain_transition_allowed:
        authorization["authorization_basis"] = "controller_domain_transition"
    if methodology_reframe_allowed:
        authorization["authorization_basis"] = "controller_methodology_reframe"
    for key in (
        "specificity_targets",
        "work_unit_targets",
        "blocking_artifact_refs",
        "blocker_details",
        "gate_blocker_details",
        "gaps",
        "source_path",
    ):
        if publication_action is not None and key in publication_action:
            authorization[key] = publication_action[key]
    return authorization


def story_surface_delta_authorization_payload(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
    read_json_object: Callable[[Path], dict[str, Any] | None],
) -> dict[str, Any] | None:
    resolved_study_root = Path(study_root).expanduser().resolve()
    batch_path = resolved_study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"
    batch = read_json_object(batch_path)
    if batch is None:
        return None
    source_eval_id = text(batch.get("source_eval_id"))
    if source_eval_id is None or source_eval_id != text(publication_eval_payload.get("eval_id")):
        return None
    if text(batch.get("blocked_reason")) != "manuscript_story_surface_delta_missing":
        return None
    if text(batch.get("next_owner")) != "write":
        return None
    publication_action = _publication_story_repair_action(publication_eval_payload)
    if publication_action is None:
        return None
    next_work_unit = mapping(publication_action.get("next_work_unit"))
    work_unit_id = text(next_work_unit.get("unit_id"))
    if not is_story_surface_delta_write_work_unit(work_unit_id):
        return None
    gate_batch = mapping(batch.get("gate_clearing_batch"))
    work_unit_fingerprint = (
        text(publication_action.get("work_unit_fingerprint"))
        or text(gate_batch.get("work_unit_fingerprint"))
        or text(gate_batch.get("source_work_unit_fingerprint"))
    )
    return {
        "decision_id": None,
        "route_target": "write",
        "route_key_question": text(publication_action.get("route_key_question")),
        "route_rationale": text(publication_action.get("route_rationale")) or text(publication_action.get("reason")),
        "source_route_key_question": text(publication_action.get("route_key_question")),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "publication_eval_id": source_eval_id,
        "publication_eval_ref": {
            "eval_id": source_eval_id,
            "artifact_path": str((resolved_study_root / "artifacts" / "publication_eval" / "latest.json").resolve()),
        },
        "next_work_unit": dict(next_work_unit),
        "blocking_work_units": [dict(next_work_unit)],
        "controller_actions": ["run_quality_repair_batch"],
        "source": CURRENT_CONTROLLER_AUTHORIZATION_SOURCE,
        "authorized_at": utc_now(),
        "authorization_basis": "quality_repair_story_surface_delta_blocker",
        "quality_repair_batch_ref": str(batch_path),
    }


def _publication_story_repair_action(publication_eval_payload: Mapping[str, Any]) -> dict[str, Any] | None:
    actions = publication_eval_payload.get("recommended_actions")
    if not isinstance(actions, list):
        return None
    for action in actions:
        if not isinstance(action, Mapping):
            continue
        next_work_unit = mapping(action.get("next_work_unit"))
        if text(action.get("action_type")) != "route_back_same_line":
            continue
        if text(action.get("route_target")) != "write" and text(next_work_unit.get("lane")) != "write":
            continue
        if not is_story_surface_delta_write_work_unit(text(next_work_unit.get("unit_id"))):
            continue
        return dict(action)
    return None


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
    "CURRENT_CONTROLLER_AUTHORIZATION_SOURCE",
    "controller_action_types",
    "controller_authorization_points_to_upstream_work_unit",
    "current_controller_authorization_payload",
    "mapping_has_actionable_controller_target",
    "publication_action_for_work_unit",
    "specificity_controller_runtime_route",
]
