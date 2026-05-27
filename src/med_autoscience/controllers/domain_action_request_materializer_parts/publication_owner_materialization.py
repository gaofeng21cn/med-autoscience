from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import ai_reviewer_publication_eval_records
from med_autoscience.controllers import domain_action_request_lifecycle
from med_autoscience.controllers.default_executor_action_policy import (
    SUPPORTED_ACTION_TYPES as SUPPORTED_REQUEST_ACTION_TYPES,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part


CURRENT_AI_REVIEWER_MATERIALIZATION_WORK_UNIT = "materialize_current_ai_reviewer_record_through_mas_owner_surface"
STORY_SURFACE_BRIDGE_AUTHORITY = "domain_action_request_materializer_story_surface_bridge"


def materialization_action(
    *,
    profile: WorkspaceProfile,
    action: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not _current_ai_reviewer_materialization_work_unit(action):
        return None
    study_id = _text(action.get("study_id"))
    if study_id is None:
        return None
    owner_route = owner_route_part.ensure_owner_route_v2(
        _mapping(action.get("owner_route")) or _mapping(_mapping(action.get("handoff_packet")).get("owner_route"))
    )
    source_refs = _mapping(owner_route.get("source_refs"))
    source_eval_id = _text(source_refs.get("source_eval_id"))
    study_root = _study_root(profile, study_id)
    current_record = ai_reviewer_publication_eval_records.latest_current_ai_reviewer_publication_eval_record(
        study_root=study_root,
        current_publication_eval=None,
    )
    if current_record is None:
        return _ai_reviewer_currentness_action(action=action, study_root=study_root, owner_route=owner_route)
    record, record_ref_path = current_record
    record_eval_id = _text(record.get("eval_id"))
    story_refs = _story_surface_delta_refs(study_root, source_eval_id or record_eval_id)
    if not story_refs:
        return _story_surface_delta_action(
            action=action,
            owner_route=owner_route,
            record_ref_path=record_ref_path,
        )
    return _gate_clearing_action(
        action=action,
        owner_route=owner_route,
        study_root=study_root,
        source_eval_id=source_eval_id,
        record_eval_id=record_eval_id,
        record_ref_path=record_ref_path,
        story_refs=story_refs,
    )


def _ai_reviewer_currentness_action(
    *,
    action: Mapping[str, Any],
    study_root: Path,
    owner_route: Mapping[str, Any],
) -> dict[str, Any]:
    request = domain_action_request_lifecycle.read_ai_reviewer_request(study_root=study_root)
    lifecycle = _mapping(_mapping(request).get("request_lifecycle"))
    blocked_reason = (
        _text(lifecycle.get("blocked_reason"))
        or domain_action_request_lifecycle.AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_MANUSCRIPT
    )
    rewritten_route = _rewrite_owner_route(
        owner_route=owner_route,
        next_owner="ai_reviewer",
        owner_reason=blocked_reason,
        allowed_actions=["return_to_ai_reviewer_workflow"],
        work_unit_id=_ai_reviewer_record_production_work_unit_id(blocked_reason),
    )
    return _with_owner_route(
        {
            **dict(action),
            "action_type": "return_to_ai_reviewer_workflow",
            "owner": "ai_reviewer",
            "request_owner": "ai_reviewer",
            "recommended_owner": "ai_reviewer",
            "reason": blocked_reason,
            "required_output_surface": "artifacts/publication_eval/latest.json",
            "next_work_unit": _ai_reviewer_record_production_work_unit_id(blocked_reason),
            "materialization_decision": "ai_reviewer_currentness_required",
            "required_currentness_refs": list(lifecycle.get("required_currentness_refs") or []),
        },
        rewritten_route,
    )


def _ai_reviewer_record_production_work_unit_id(blocked_reason: str | None) -> str:
    if blocked_reason == domain_action_request_lifecycle.AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_INPUTS:
        return "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    if blocked_reason == domain_action_request_lifecycle.AI_REVIEWER_RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN:
        return "produce_ai_reviewer_publication_eval_record_against_current_analysis_harmonization"
    return "produce_ai_reviewer_publication_eval_record_against_current_manuscript"


def _story_surface_delta_action(
    *,
    action: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    record_ref_path: Path,
) -> dict[str, Any]:
    rewritten_route = _rewrite_owner_route(
        owner_route=owner_route,
        next_owner="write",
        owner_reason="manuscript_story_surface_delta_missing",
        allowed_actions=["run_quality_repair_batch"],
        work_unit_id="dm002_current_publication_hardening_after_current_ai_reviewer_eval",
    )
    return _with_owner_route(
        {
            **dict(action),
            "action_type": "run_quality_repair_batch",
            "owner": "write",
            "request_owner": "write",
            "recommended_owner": "write",
            "reason": "manuscript_story_surface_delta_missing",
            "required_output_surface": (
                "canonical manuscript story-surface delta or "
                "typed blocker:manuscript_story_surface_delta_missing"
            ),
            "next_work_unit": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
            "materialization_decision": "story_surface_delta_or_typed_blocker_required",
            "reviewer_record_ref": str(record_ref_path.resolve()),
        },
        rewritten_route,
    )


def _gate_clearing_action(
    *,
    action: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    study_root: Path,
    source_eval_id: str | None,
    record_eval_id: str | None,
    record_ref_path: Path,
    story_refs: list[str],
) -> dict[str, Any]:
    if not _current_package_fresh_for_eval(study_root, source_eval_id or record_eval_id):
        rewritten_route = _rewrite_owner_route(
            owner_route=owner_route,
            next_owner="gate_clearing_batch",
            owner_reason="current_package_freshness_required",
            allowed_actions=["run_gate_clearing_batch"],
            work_unit_id="current_package_freshness_required",
        )
        materialization_decision = "current_package_freshness_required"
    else:
        rewritten_route = _rewrite_owner_route(
            owner_route=owner_route,
            next_owner="gate_clearing_batch",
            owner_reason="publication_owner_materialization_required",
            allowed_actions=["run_gate_clearing_batch"],
            work_unit_id="publication_gate_replay",
        )
        materialization_decision = "publication_gate_replay"
    return _with_owner_route(
        {
            **dict(action),
            "action_type": "run_gate_clearing_batch",
            "owner": "gate_clearing_batch",
            "request_owner": "gate_clearing_batch",
            "recommended_owner": "gate_clearing_batch",
            "reason": _text(rewritten_route.get("owner_reason")),
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
            "next_work_unit": _text(_mapping(rewritten_route.get("source_refs")).get("work_unit_id")),
            "materialization_decision": materialization_decision,
            "reviewer_record_ref": str(record_ref_path.resolve()),
            "source_eval_id": source_eval_id or record_eval_id,
            "story_surface_delta_refs": story_refs,
        },
        rewritten_route,
    )


def _current_ai_reviewer_materialization_work_unit(action: Mapping[str, Any]) -> bool:
    owner_route = _mapping(action.get("owner_route")) or _mapping(_mapping(action.get("handoff_packet")).get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    return (
        _text(action.get("controller_work_unit_id"))
        == CURRENT_AI_REVIEWER_MATERIALIZATION_WORK_UNIT
        or _text(action.get("next_work_unit"))
        == CURRENT_AI_REVIEWER_MATERIALIZATION_WORK_UNIT
        or _text(source_refs.get("work_unit_id"))
        == CURRENT_AI_REVIEWER_MATERIALIZATION_WORK_UNIT
    )


def _story_surface_delta_refs(study_root: Path, source_eval_id: str | None) -> list[str]:
    evidence = _read_json_object(
        study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
    )
    if not isinstance(evidence, Mapping):
        return []
    if source_eval_id and _text(evidence.get("source_eval_id")) not in {None, source_eval_id}:
        return []
    hygiene = _mapping(evidence.get("manuscript_surface_hygiene"))
    if hygiene.get("story_surface_delta_present") is not True:
        return []
    return [text for item in hygiene.get("story_surface_delta_refs") or [] if (text := _text(item))]


def _current_package_fresh_for_eval(study_root: Path, source_eval_id: str | None) -> bool:
    freshness = _read_json_object(
        study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json"
    )
    if not isinstance(freshness, Mapping):
        return False
    if _text(freshness.get("status")) != "current":
        return False
    return not source_eval_id or _text(freshness.get("source_eval_id")) == source_eval_id


def _with_owner_route(action: Mapping[str, Any], owner_route: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(action)
    payload["owner_route"] = dict(owner_route)
    handoff_packet = dict(_mapping(payload.get("handoff_packet")))
    handoff_packet["owner_route"] = dict(owner_route)
    if idempotency_key := _text(owner_route.get("idempotency_key")):
        handoff_packet["idempotency_key"] = idempotency_key
    payload["handoff_packet"] = handoff_packet
    return payload


def _rewrite_owner_route(
    *,
    owner_route: Mapping[str, Any],
    next_owner: str,
    owner_reason: str,
    allowed_actions: list[str],
    work_unit_id: str,
) -> dict[str, Any]:
    route = owner_route_part.ensure_owner_route_v2(owner_route)
    source_refs = dict(_mapping(route.get("source_refs")))
    original_owner_reason = _text(route.get("owner_reason")) or _text(route.get("failure_signature"))
    original_idempotency_key = _text(route.get("idempotency_key"))
    original_work_unit_id = _text(source_refs.get("work_unit_id"))
    if _is_runtime_to_story_surface_bridge(
        original_owner_reason=original_owner_reason,
        original_work_unit_id=original_work_unit_id,
        owner_reason=owner_reason,
        work_unit_id=work_unit_id,
    ):
        source_refs["materialized_work_unit_id"] = work_unit_id
        if original_owner_reason == "ai_reviewer_assessment_required":
            source_refs["materialized_from_action_type"] = "return_to_ai_reviewer_workflow"
        source_refs["bridged_from_owner_reason"] = original_owner_reason
        source_refs["bridge_authority"] = STORY_SURFACE_BRIDGE_AUTHORITY
        if original_idempotency_key is not None:
            source_refs["bridged_from_idempotency_key"] = original_idempotency_key
    else:
        source_refs["work_unit_id"] = work_unit_id
    source_refs["blocked_reason"] = owner_reason
    route.update(
        {
            "next_owner": next_owner,
            "owner_reason": owner_reason,
            "failure_signature": owner_reason,
            "allowed_actions": list(allowed_actions),
            "blocked_actions": sorted(set(SUPPORTED_REQUEST_ACTION_TYPES) - set(allowed_actions)),
            "source_refs": source_refs,
        }
    )
    route["idempotency_key"] = "::".join(
        item
        for item in (
            "owner-route",
            _text(route.get("study_id")),
            _text(route.get("source_fingerprint")),
            next_owner,
            owner_reason,
            ",".join(allowed_actions),
        )
        if item
    )
    return owner_route_part.ensure_owner_route_v2(route)


def _is_runtime_to_story_surface_bridge(
    *,
    original_owner_reason: str | None,
    original_work_unit_id: str | None,
    owner_reason: str,
    work_unit_id: str,
) -> bool:
    return (
        original_owner_reason in {"quest_waiting_opl_runtime_owner_route", "ai_reviewer_assessment_required"}
        and original_work_unit_id == CURRENT_AI_REVIEWER_MATERIALIZATION_WORK_UNIT
        and owner_reason == "manuscript_story_surface_delta_missing"
        and work_unit_id == "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
    )


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _study_root(profile: WorkspaceProfile, study_id: str) -> Path:
    return profile.studies_root / study_id


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["materialization_action"]
