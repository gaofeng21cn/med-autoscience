from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import ai_reviewer_publication_eval_records
from med_autoscience.controllers import ai_reviewer_owner_output_consumption
from med_autoscience.controllers.ai_reviewer_record_work_units import (
    AI_REVIEWER_RECORD_CONSUMPTION_WORK_UNIT_IDS,
)
from med_autoscience.controllers import domain_action_request_lifecycle
from med_autoscience.controllers.default_executor_action_policy import (
    SUPPORTED_ACTION_TYPES as SUPPORTED_REQUEST_ACTION_TYPES,
)
from med_autoscience.controllers.gate_clearing_batch_work_units import PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS
from med_autoscience.controllers.story_surface_work_units import (
    is_story_surface_delta_write_work_unit,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.publication_eval_reviewer_os import current_ai_reviewer_route_back_action
from med_autoscience.runtime_control import owner_route as owner_route_part


CURRENT_AI_REVIEWER_MATERIALIZATION_WORK_UNIT = "materialize_current_ai_reviewer_record_through_mas_owner_surface"
CURRENT_MANUSCRIPT_PUBLICATION_SURFACE_RECHECK_WORK_UNIT = (
    "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck"
)
DM002_CURRENT_AI_REVIEWER_STORY_SURFACE_WORK_UNIT = "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
DEFAULT_CURRENT_AI_REVIEWER_STORY_SURFACE_WORK_UNIT = "medical_prose_write_repair"
AI_REVIEWER_STORY_SURFACE_BRIDGE_WORK_UNIT_IDS = frozenset(
    {
        CURRENT_AI_REVIEWER_MATERIALIZATION_WORK_UNIT,
        CURRENT_MANUSCRIPT_PUBLICATION_SURFACE_RECHECK_WORK_UNIT,
    }
)
AI_REVIEWER_PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS = PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS
AI_REVIEWER_RECORD_PRODUCTION_WORK_UNIT_IDS = frozenset(
    {
        "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
        "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        "produce_ai_reviewer_publication_eval_record_against_current_analysis_harmonization",
    }
)
AI_REVIEWER_CURRENT_RECORD_CONSUMPTION_WORK_UNIT_IDS = (
    AI_REVIEWER_STORY_SURFACE_BRIDGE_WORK_UNIT_IDS
    | AI_REVIEWER_RECORD_CONSUMPTION_WORK_UNIT_IDS
    | AI_REVIEWER_RECORD_PRODUCTION_WORK_UNIT_IDS
)
STORY_SURFACE_BRIDGE_AUTHORITY = "domain_action_request_materializer_story_surface_bridge"
PUBLICATION_OWNER_BRIDGE_AUTHORITY = "domain_action_request_materializer_publication_owner_bridge"
AI_REVIEWER_RECORD_OWNER_REASONS = frozenset(
    {
        "ai_reviewer_assessment_required",
        "domain_transition_ai_reviewer_re_eval",
    }
)
AI_REVIEWER_RECORD_CURRENTNESS_BLOCKED_REASONS = frozenset(
    {
        domain_action_request_lifecycle.AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_MANUSCRIPT,
        domain_action_request_lifecycle.AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_INPUTS,
        domain_action_request_lifecycle.AI_REVIEWER_RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN,
    }
)


def materialization_action(
    *,
    profile: WorkspaceProfile,
    action: Mapping[str, Any],
) -> dict[str, Any] | None:
    story_surface_work_unit = _current_ai_reviewer_materialization_work_unit(action)
    record_production_work_unit = _ai_reviewer_record_production_work_unit(action)
    if not story_surface_work_unit and not record_production_work_unit:
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
        current_record = _request_bound_current_ai_reviewer_record(study_root=study_root)
    if current_record is not None and not _record_consumes_request_currentness(
        study_root=study_root,
        record=current_record[0],
    ):
        current_record = None
    if _publication_gate_replay_work_unit(action):
        record_eval_id = _text(current_record[0].get("eval_id")) if current_record is not None else None
        return _publication_gate_replay_action(
            action=action,
            owner_route=owner_route,
            source_eval_id=record_eval_id or source_eval_id,
        )
    if current_record is None:
        if record_production_work_unit:
            return None
        return _ai_reviewer_currentness_action(action=action, study_root=study_root, owner_route=owner_route)
    record, record_ref_path = current_record
    record_eval_id = _text(record.get("eval_id"))
    if record_production_work_unit and _current_record_requires_write_routeback(record):
        return _story_surface_delta_action(
            action=action,
            owner_route=owner_route,
            record=record,
            record_ref_path=record_ref_path,
        )
    story_refs = _story_surface_delta_refs(study_root, source_eval_id or record_eval_id)
    if _current_record_allows_gate_replay(record):
        return _gate_clearing_action(
            action=action,
            owner_route=owner_route,
            study_root=study_root,
            source_eval_id=source_eval_id,
            record_eval_id=record_eval_id,
            record_ref_path=record_ref_path,
            story_refs=story_refs,
        )
    if not story_refs:
        return _story_surface_delta_action(
            action=action,
            owner_route=owner_route,
            record=record,
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
        source_eval_id=_source_eval_id_from_route(owner_route),
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
    record: Mapping[str, Any],
    record_ref_path: Path,
) -> dict[str, Any]:
    study_root = _record_study_root(record_ref_path)
    work_unit_id = _story_surface_work_unit_id(action=action, record=record)
    record_eval_id = _text(record.get("eval_id"))
    rewritten_route = _rewrite_owner_route(
        owner_route=owner_route,
        next_owner="write",
        owner_reason="manuscript_story_surface_delta_missing",
        allowed_actions=["run_quality_repair_batch"],
        work_unit_id=work_unit_id,
        source_eval_id=record_eval_id,
    )
    action_payload = {
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
        "next_work_unit": work_unit_id,
        "materialization_decision": "story_surface_delta_or_typed_blocker_required",
        "reviewer_record_ref": str(record_ref_path.resolve()),
        "source_eval_id": record_eval_id,
    }
    return _with_owner_route(
        _with_owner_output_consumption(
            action=action_payload,
            study_root=study_root,
            record=record,
            record_ref_path=record_ref_path,
        ),
        rewritten_route,
    )


def _with_owner_output_consumption(
    *,
    action: Mapping[str, Any],
    study_root: Path,
    record: Mapping[str, Any],
    record_ref_path: Path,
) -> dict[str, Any]:
    lifecycle = domain_action_request_lifecycle.project_ai_reviewer_request_lifecycle(
        study_root=study_root,
        publication_eval_payload=record,
    )
    return ai_reviewer_owner_output_consumption.with_owner_output_consumption(
        payload=action,
        publication_eval_payload=record,
        lifecycle=lifecycle,
    )


def _record_study_root(record_ref_path: Path) -> Path:
    resolved = record_ref_path.expanduser().resolve()
    for parent in resolved.parents:
        if parent.name == "artifacts":
            return parent.parent
    return resolved.parents[3]


def _record_consumes_request_currentness(
    *,
    study_root: Path,
    record: Mapping[str, Any],
) -> bool:
    blocked_reason = _request_record_currentness_blocked_reason(study_root=study_root)
    if blocked_reason is None:
        return True
    lifecycle = domain_action_request_lifecycle.project_ai_reviewer_request_lifecycle(
        study_root=study_root,
        publication_eval_payload=record,
    )
    return (
        isinstance(lifecycle, Mapping)
        and lifecycle.get("assessment_written") is True
        and _text(lifecycle.get("blocked_reason")) is None
    )


def _request_record_currentness_blocked_reason(*, study_root: Path) -> str | None:
    request = domain_action_request_lifecycle.read_ai_reviewer_request(study_root=study_root)
    lifecycle = _mapping(_mapping(request).get("request_lifecycle"))
    blocked_reason = _text(lifecycle.get("blocked_reason"))
    if blocked_reason in AI_REVIEWER_RECORD_CURRENTNESS_BLOCKED_REASONS:
        return blocked_reason
    return None


def _story_surface_work_unit_id(*, action: Mapping[str, Any], record: Mapping[str, Any]) -> str:
    route_back_action = current_ai_reviewer_route_back_action(dict(record))
    route_back_unit = _work_unit_id(_mapping(route_back_action).get("next_work_unit"))
    if route_back_unit and is_story_surface_delta_write_work_unit(route_back_unit):
        return route_back_unit
    if _text(action.get("study_id")) == "002-dm-china-us-mortality-attribution":
        return DM002_CURRENT_AI_REVIEWER_STORY_SURFACE_WORK_UNIT
    return DEFAULT_CURRENT_AI_REVIEWER_STORY_SURFACE_WORK_UNIT


def _current_record_requires_write_routeback(record: Mapping[str, Any]) -> bool:
    route_back_action = current_ai_reviewer_route_back_action(dict(record))
    if not isinstance(route_back_action, Mapping):
        return False
    return _text(route_back_action.get("route_target")) == "write"


def _current_record_allows_gate_replay(record: Mapping[str, Any]) -> bool:
    reviewer_os = _mapping(record.get("reviewer_operating_system"))
    readiness = _mapping(reviewer_os.get("publication_quality_readiness"))
    if _text(readiness.get("status")) != "ready":
        return False
    claim_alignment = _mapping(reviewer_os.get("claim_evidence_alignment"))
    if _text(claim_alignment.get("status")) != "ready":
        return False
    if claim_alignment.get("missing_required_fields") not in ([], ()):
        return False
    if claim_alignment.get("blockers") not in ([], ()):
        return False
    quality_assessment = _mapping(record.get("quality_assessment"))
    if not quality_assessment:
        return False
    if any(_text(_mapping(item).get("status")) != "ready" for item in quality_assessment.values()):
        return False
    if _current_record_requires_write_routeback(record):
        return False
    return True


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
            source_eval_id=source_eval_id or record_eval_id,
        )
        materialization_decision = "current_package_freshness_required"
    else:
        rewritten_route = _rewrite_owner_route(
            owner_route=owner_route,
            next_owner="gate_clearing_batch",
            owner_reason="publication_owner_materialization_required",
            allowed_actions=["run_gate_clearing_batch"],
            work_unit_id="publication_gate_replay",
            source_eval_id=source_eval_id or record_eval_id,
        )
        materialization_decision = "publication_gate_replay"
    source_refs = _mapping(rewritten_route.get("source_refs"))
    materialized_work_unit_id = _text(source_refs.get("materialized_work_unit_id"))
    work_unit_id = materialized_work_unit_id or _text(source_refs.get("work_unit_id"))
    return _with_owner_route(
        {
            **dict(action),
            "action_type": "run_gate_clearing_batch",
            "owner": "gate_clearing_batch",
            "request_owner": "gate_clearing_batch",
            "recommended_owner": "gate_clearing_batch",
            "reason": _text(rewritten_route.get("owner_reason")),
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
            "next_work_unit": work_unit_id,
            "materialization_decision": materialization_decision,
            "reviewer_record_ref": str(record_ref_path.resolve()),
            "source_eval_id": source_eval_id or record_eval_id,
            "story_surface_delta_refs": story_refs,
        },
        rewritten_route,
    )


def _publication_gate_replay_action(
    *,
    action: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    source_eval_id: str | None,
) -> dict[str, Any]:
    route_work_unit_id = _route_work_unit_id(action=action, owner_route=owner_route) or "publication_gate_replay"
    rewritten_route = _rewrite_owner_route(
        owner_route=owner_route,
        next_owner="gate_clearing_batch",
        owner_reason=route_work_unit_id,
        allowed_actions=["run_gate_clearing_batch"],
        work_unit_id=route_work_unit_id,
        source_eval_id=source_eval_id,
    )
    return _with_owner_route(
        {
            **dict(action),
            "action_type": "run_gate_clearing_batch",
            "owner": "gate_clearing_batch",
            "request_owner": "gate_clearing_batch",
            "recommended_owner": "gate_clearing_batch",
            "reason": route_work_unit_id,
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
            "next_work_unit": route_work_unit_id,
            "materialization_decision": "publication_gate_replay",
            "source_eval_id": source_eval_id,
        },
        rewritten_route,
    )


def _publication_gate_replay_work_unit(action: Mapping[str, Any]) -> bool:
    owner_route = _mapping(action.get("owner_route")) or _mapping(_mapping(action.get("handoff_packet")).get("owner_route"))
    work_unit_id = _route_work_unit_id(action=action, owner_route=owner_route)
    if work_unit_id in AI_REVIEWER_PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS:
        return True
    next_work_unit = _mapping(action.get("controller_next_work_unit"))
    if _work_unit_id(next_work_unit) in AI_REVIEWER_PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS:
        return True
    return _text(next_work_unit.get("lane")) in {"publication_gate", "finalize"} and "gate_replay" in str(
        _work_unit_id(next_work_unit) or ""
    )


def _route_work_unit_id(*, action: Mapping[str, Any], owner_route: Mapping[str, Any]) -> str | None:
    source_refs = _mapping(owner_route.get("source_refs"))
    return (
        _text(action.get("controller_work_unit_id"))
        or _text(action.get("executable_work_unit"))
        or _work_unit_id(action.get("next_work_unit"))
        or _work_unit_id(source_refs.get("work_unit_id"))
        or _work_unit_id(_mapping(source_refs.get("owner_route_currentness_basis")).get("work_unit_id"))
    )


def _current_ai_reviewer_materialization_work_unit(action: Mapping[str, Any]) -> bool:
    owner_route = _mapping(action.get("owner_route")) or _mapping(_mapping(action.get("handoff_packet")).get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    return (
        _text(action.get("controller_work_unit_id")) in AI_REVIEWER_STORY_SURFACE_BRIDGE_WORK_UNIT_IDS
        or _text(action.get("executable_work_unit")) in AI_REVIEWER_STORY_SURFACE_BRIDGE_WORK_UNIT_IDS
        or _text(action.get("next_work_unit")) in AI_REVIEWER_STORY_SURFACE_BRIDGE_WORK_UNIT_IDS
        or _text(source_refs.get("work_unit_id")) in AI_REVIEWER_STORY_SURFACE_BRIDGE_WORK_UNIT_IDS
        or _text(action.get("controller_work_unit_id")) in AI_REVIEWER_RECORD_CONSUMPTION_WORK_UNIT_IDS
        or _text(action.get("executable_work_unit")) in AI_REVIEWER_RECORD_CONSUMPTION_WORK_UNIT_IDS
        or _text(action.get("next_work_unit")) in AI_REVIEWER_RECORD_CONSUMPTION_WORK_UNIT_IDS
        or _text(source_refs.get("work_unit_id")) in AI_REVIEWER_RECORD_CONSUMPTION_WORK_UNIT_IDS
    )


def _ai_reviewer_record_production_work_unit(action: Mapping[str, Any]) -> bool:
    owner_route = _mapping(action.get("owner_route")) or _mapping(_mapping(action.get("handoff_packet")).get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    return (
        _text(action.get("controller_work_unit_id")) in AI_REVIEWER_RECORD_PRODUCTION_WORK_UNIT_IDS
        or _text(action.get("executable_work_unit")) in AI_REVIEWER_RECORD_PRODUCTION_WORK_UNIT_IDS
        or _text(action.get("next_work_unit")) in AI_REVIEWER_RECORD_PRODUCTION_WORK_UNIT_IDS
        or _text(source_refs.get("work_unit_id")) in AI_REVIEWER_RECORD_PRODUCTION_WORK_UNIT_IDS
    )


def _request_bound_current_ai_reviewer_record(*, study_root: Path) -> tuple[dict[str, Any], Path] | None:
    request = domain_action_request_lifecycle.read_ai_reviewer_request(study_root=study_root)
    if request is None:
        return None
    record = _mapping(
        request.get("ai_reviewer_record")
        or request.get("publication_eval_record")
        or request.get("record")
    )
    if not record:
        return None
    record_ref = _text(request.get("publication_eval_record_ref"))
    if record_ref is None:
        return None
    manuscript = ai_reviewer_publication_eval_records.current_manuscript_binding(study_root=study_root)
    if manuscript is None:
        return None
    if not ai_reviewer_publication_eval_records.record_matches_current_manuscript(
        record=record,
        manuscript=manuscript,
    ):
        return None
    record_path = _resolve_study_ref(study_root=study_root, ref=record_ref)
    return ai_reviewer_publication_eval_records.with_projection_source(record, record_path), record_path


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
    source_eval_id: str | None,
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
        source_refs["materialized_from_action_type"] = _materialized_from_action_type(
            original_owner_reason=original_owner_reason,
        )
        source_refs["bridged_from_owner_reason"] = original_owner_reason
        source_refs["bridge_authority"] = STORY_SURFACE_BRIDGE_AUTHORITY
        if original_idempotency_key is not None:
            source_refs["bridged_from_idempotency_key"] = original_idempotency_key
    elif _is_publication_owner_materialization_bridge(
        original_owner_reason=original_owner_reason,
        owner_reason=owner_reason,
        work_unit_id=work_unit_id,
    ):
        source_refs["materialized_work_unit_id"] = work_unit_id
        source_refs["materialized_from_action_type"] = _materialized_from_action_type(
            original_owner_reason=original_owner_reason,
        )
        source_refs["bridged_from_owner_reason"] = original_owner_reason
        source_refs["bridge_authority"] = PUBLICATION_OWNER_BRIDGE_AUTHORITY
        if original_idempotency_key is not None:
            source_refs["bridged_from_idempotency_key"] = original_idempotency_key
    else:
        source_refs["work_unit_id"] = work_unit_id
    if source_eval_id is not None:
        source_refs["source_eval_id"] = source_eval_id
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


def _source_eval_id_from_route(owner_route: Mapping[str, Any]) -> str | None:
    route = owner_route_part.ensure_owner_route_v2(owner_route)
    source_refs = _mapping(route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    publication_eval_ref = _mapping(source_refs.get("publication_eval_ref")) or _mapping(
        route.get("publication_eval_ref")
    )
    return (
        _text(source_refs.get("source_eval_id"))
        or _text(source_refs.get("publication_eval_id"))
        or _text(publication_eval_ref.get("eval_id"))
        or _text(route.get("source_eval_id"))
        or _text(route.get("publication_eval_id"))
        or _text(basis.get("source_eval_id"))
    )


def _is_runtime_to_story_surface_bridge(
    *,
    original_owner_reason: str | None,
    original_work_unit_id: str | None,
    owner_reason: str,
    work_unit_id: str,
) -> bool:
    return (
        original_owner_reason
        in {
            "quest_waiting_opl_runtime_owner_route",
            *AI_REVIEWER_RECORD_OWNER_REASONS,
            *AI_REVIEWER_RECORD_CURRENTNESS_BLOCKED_REASONS,
        }
        and original_work_unit_id in AI_REVIEWER_CURRENT_RECORD_CONSUMPTION_WORK_UNIT_IDS
        and owner_reason == "manuscript_story_surface_delta_missing"
        and is_story_surface_delta_write_work_unit(work_unit_id)
    )


def _is_publication_owner_materialization_bridge(
    *,
    original_owner_reason: str | None,
    owner_reason: str,
    work_unit_id: str,
) -> bool:
    return (
        original_owner_reason
        in {
            "quest_waiting_opl_runtime_owner_route",
            *AI_REVIEWER_RECORD_OWNER_REASONS,
            *AI_REVIEWER_RECORD_CURRENTNESS_BLOCKED_REASONS,
        }
        and owner_reason in {"current_package_freshness_required", "publication_owner_materialization_required"}
        and work_unit_id in {"current_package_freshness_required", "publication_gate_replay"}
    )


def _materialized_from_action_type(*, original_owner_reason: str | None) -> str:
    if original_owner_reason in {
        *AI_REVIEWER_RECORD_OWNER_REASONS,
        *AI_REVIEWER_RECORD_CURRENTNESS_BLOCKED_REASONS,
    }:
        return "return_to_ai_reviewer_workflow"
    return "run_quality_repair_batch"


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _study_root(profile: WorkspaceProfile, study_id: str) -> Path:
    return profile.studies_root / study_id


def _resolve_study_ref(*, study_root: Path, ref: str) -> Path:
    path = Path(ref).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (study_root / path).resolve()


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id")) or _text(value.get("work_unit_id"))
    return _text(value)


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["materialization_action"]
