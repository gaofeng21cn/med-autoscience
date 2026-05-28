from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers.runtime_ai_repair_policy import default_executor_policy
from med_autoscience.controllers.default_executor_closeout_contract import default_executor_typed_closeout_contract
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part
from med_autoscience.study_decision_record import StudyDecisionActionType
from med_autoscience.controllers.story_surface_work_units import is_story_surface_delta_write_work_unit


BLOCKED_REASON = "manuscript_story_surface_delta_missing"
RUNTIME_OWNER_ROUTE_REASON = "quest_waiting_opl_runtime_owner_route"
NEXT_OWNER = "write"
REQUIRED_OUTPUT = (
    "canonical manuscript story-surface delta or "
    "typed blocker:manuscript_story_surface_delta_missing"
)
FORBIDDEN_SURFACES = [
    "manuscript/**",
    "current_package/**",
    "paper/current_package/**",
    "manuscript/current_package/**",
    "src/med_autoscience/platform/**",
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
]
ALLOWED_WRITE_SURFACES = [
    "paper/draft.md",
    "paper/build/review_manuscript.md",
    "paper/claim_evidence_map.json",
    "paper/evidence_ledger.json",
    "paper/review/**",
]
REQUEST_PACKET_REF = "artifacts/supervision/requests/quality_repair_batch/latest.json"


def should_emit_writer_handoff(blocked_repair_reason: str | None) -> bool:
    return blocked_repair_reason == BLOCKED_REASON


def build_writer_worker_handoff(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    quest_id: str,
    schema_version: int,
    source_eval_id: str | None,
    source_eval_artifact_path: str | None,
    source_summary_artifact_path: str | None,
    repair_execution_evidence_path: Path,
    blocked_repair_reason: str,
    authority_route_context: Mapping[str, Any] | None,
) -> dict[str, Any]:
    generated_at = _utc_now()
    owner_route = _writer_handoff_owner_route(
        study_id=study_id,
        quest_id=quest_id,
        source_eval_id=source_eval_id,
        blocked_repair_reason=blocked_repair_reason,
        authority_route_context=authority_route_context,
    )
    dispatch_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    typed_closeout_contract = default_executor_typed_closeout_contract(
        action_type=StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH.value
    )
    prompt_contract = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH.value,
        "next_executable_owner": NEXT_OWNER,
        "required_output_surface": REQUIRED_OUTPUT,
        "owner_route": owner_route,
        "idempotency_key": owner_route["idempotency_key"],
        "prompt_budget": {"max_prompt_tokens": 6000},
        "compact_evidence_packet_ref": "artifacts/supervision/compact_evidence_packets/run_quality_repair_batch.json",
        "do_not_repeat": True,
        "repeat_suppression_key": owner_route["work_unit_fingerprint"],
        "request_packet_ref": REQUEST_PACKET_REF,
        "source_eval_ref": source_eval_artifact_path,
        "source_summary_ref": source_summary_artifact_path,
        "repair_execution_evidence_ref": str(repair_execution_evidence_path),
        "required_closeout_packet": typed_closeout_contract,
        "terminal_output_instruction": typed_closeout_contract["terminal_output_instruction"],
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": True,
    }
    return {
        "surface": "default_executor_dispatch_request",
        "schema_version": schema_version,
        **default_executor_policy(),
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH.value,
        "action_id": f"quality-repair-writer-handoff::{study_id}::{source_eval_id or 'latest'}",
        "next_executable_owner": NEXT_OWNER,
        "required_output_surface": REQUIRED_OUTPUT,
        "dispatch_status": "ready",
        "typed_blocker_if_unresolved": blocked_repair_reason,
        "dispatch_authority": "quality_repair_batch_writer_handoff",
        "owner_route": owner_route,
        "idempotency_key": owner_route["idempotency_key"],
        "repeat_suppression_key": owner_route["work_unit_fingerprint"],
        "action_fingerprint": owner_route["work_unit_fingerprint"],
        "consumer_mutation_scope": "executor_dispatch_request_only",
        "required_closeout_packet": typed_closeout_contract,
        "terminal_output_instruction": typed_closeout_contract["terminal_output_instruction"],
        "prompt_contract": prompt_contract,
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": True,
        "source_action": {
            "surface": "quality_repair_batch",
            "blocked_reason": blocked_repair_reason,
            "source_eval_id": source_eval_id,
            "repair_execution_evidence_ref": str(repair_execution_evidence_path),
        },
        "refs": {
            "dispatch_path": str(dispatch_path),
            "request_path": str((profile.studies_root / study_id / REQUEST_PACKET_REF).resolve()),
            "source_eval_path": source_eval_artifact_path,
            "source_summary_path": source_summary_artifact_path,
            "repair_execution_evidence_path": str(repair_execution_evidence_path),
        },
        "handoff_semantics": {
            "status": "same_owner_writer_handoff_ready",
            "terminal_blocker": False,
            "expected_next_effect": "writer owner updates canonical manuscript story surface or emits typed blocker",
        },
        "generated_at": generated_at,
    }


def owner_request_from_handoff(handoff: Mapping[str, Any]) -> dict[str, Any]:
    source_action = _mapping(handoff.get("source_action"))
    owner = _non_empty_text(handoff.get("next_executable_owner")) or NEXT_OWNER
    return {
        "request_kind": StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH.value,
        "status": "requested",
        "study_id": _non_empty_text(handoff.get("study_id")),
        "quest_id": _non_empty_text(handoff.get("quest_id")),
        "request_owner": owner,
        "expected_owner": owner,
        "next_executable_owner": owner,
        "action_type": StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH.value,
        "owner_route": _mapping(handoff.get("owner_route")),
        "source_action": source_action,
        "refs": _mapping(handoff.get("refs")),
        "request_packet_ref": REQUEST_PACKET_REF,
        "required_output_surface": _non_empty_text(handoff.get("required_output_surface")),
        "dispatch_authority": _non_empty_text(handoff.get("dispatch_authority")),
    }


def _writer_handoff_owner_route(
    *,
    study_id: str,
    quest_id: str,
    source_eval_id: str | None,
    blocked_repair_reason: str,
    authority_route_context: Mapping[str, Any] | None,
) -> dict[str, Any]:
    current_route = _current_owner_route_for_writer_handoff(
        study_id=study_id,
        quest_id=quest_id,
        source_eval_id=source_eval_id,
        blocked_repair_reason=blocked_repair_reason,
        authority_route_context=authority_route_context,
    )
    if current_route:
        return current_route
    controller_context = (
        dict(authority_route_context.get("controller_route_context") or {})
        if isinstance(authority_route_context, Mapping)
        else {}
    )
    work_unit_id = _non_empty_text(controller_context.get("work_unit_id")) or "medical_prose_write_repair"
    fingerprint = (
        _non_empty_text(controller_context.get("work_unit_fingerprint"))
        or f"quality-repair-writer-handoff::{study_id}::{source_eval_id or work_unit_id}"
    )
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": source_eval_id or fingerprint,
        "runtime_health_epoch": None,
        "work_unit_fingerprint": fingerprint,
        "failure_signature": blocked_repair_reason,
        "route_epoch": f"quality-repair-writer-handoff::{study_id}::{source_eval_id or 'latest'}",
        "source_fingerprint": fingerprint,
        "current_owner": "quality_repair_batch",
        "next_owner": NEXT_OWNER,
        "owner_reason": blocked_repair_reason,
        "active_run_id": None,
        "allowed_actions": [StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH.value],
        "blocked_actions": [],
        "idempotency_key": f"quality-repair-writer-handoff::{study_id}::{fingerprint}",
        "source_refs": {
            "source_eval_id": source_eval_id,
            "work_unit_id": work_unit_id,
            "blocked_reason": blocked_repair_reason,
        },
    }


def _current_owner_route_for_writer_handoff(
    *,
    study_id: str,
    quest_id: str,
    source_eval_id: str | None,
    blocked_repair_reason: str,
    authority_route_context: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(authority_route_context, Mapping):
        return {}
    route = owner_route_part.ensure_owner_route_v2(_mapping(authority_route_context.get("current_owner_route")))
    if not route:
        return {}
    if _non_empty_text(route.get("study_id")) != study_id:
        return {}
    route_quest_id = _non_empty_text(route.get("quest_id"))
    if route_quest_id is not None and route_quest_id != quest_id:
        return {}
    if _non_empty_text(route.get("next_owner")) != NEXT_OWNER:
        return {}
    route_reason = _non_empty_text(route.get("owner_reason")) or _non_empty_text(route.get("failure_signature"))
    if not _route_source_eval_current(route=route, source_eval_id=source_eval_id):
        return {}
    if not owner_route_part.route_allows_action(
        action={
            "action_type": StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH.value,
            "next_executable_owner": NEXT_OWNER,
        },
        owner_route=route,
    ):
        return {}
    if route_reason == blocked_repair_reason:
        return route
    if not _current_route_can_bridge_to_story_surface_handoff(
        route=route,
        route_reason=route_reason,
        blocked_repair_reason=blocked_repair_reason,
        authority_route_context=authority_route_context,
    ):
        return {}
    return _bridged_story_surface_owner_route(
        route=route,
        source_eval_id=source_eval_id,
        blocked_repair_reason=blocked_repair_reason,
        route_reason=route_reason,
        authority_route_context=authority_route_context,
    )


def _route_source_eval_current(*, route: Mapping[str, Any], source_eval_id: str | None) -> bool:
    if source_eval_id is None:
        return True
    route_source_eval_id = _non_empty_text(_mapping(route.get("source_refs")).get("source_eval_id"))
    if route_source_eval_id is None:
        return True
    return route_source_eval_id == source_eval_id


def _current_route_can_bridge_to_story_surface_handoff(
    *,
    route: Mapping[str, Any],
    route_reason: str | None,
    blocked_repair_reason: str,
    authority_route_context: Mapping[str, Any],
) -> bool:
    if route_reason != RUNTIME_OWNER_ROUTE_REASON or blocked_repair_reason != BLOCKED_REASON:
        return False
    if not is_story_surface_delta_write_work_unit(
        _controller_work_unit_id(authority_route_context=authority_route_context, route=route)
    ):
        return False
    return all(
        _non_empty_text(route.get(field)) is not None
        for field in (
            "truth_epoch",
            "runtime_health_epoch",
            "work_unit_fingerprint",
            "source_fingerprint",
        )
    )


def _bridged_story_surface_owner_route(
    *,
    route: Mapping[str, Any],
    source_eval_id: str | None,
    blocked_repair_reason: str,
    route_reason: str | None,
    authority_route_context: Mapping[str, Any],
) -> dict[str, Any]:
    bridged = dict(route)
    source_refs = dict(_mapping(route.get("source_refs")))
    work_unit_id = _controller_work_unit_id(authority_route_context=authority_route_context, route=route)
    if source_eval_id is not None:
        source_refs["source_eval_id"] = source_eval_id
    if work_unit_id is not None:
        source_refs["work_unit_id"] = work_unit_id
    source_refs.update(
        {
            "blocked_reason": blocked_repair_reason,
            "bridged_from_owner_reason": route_reason,
            "bridged_from_idempotency_key": _non_empty_text(route.get("idempotency_key")),
            "bridge_authority": "quality_repair_batch_writer_handoff_currentness_bridge",
            "runtime_health_epoch": _non_empty_text(route.get("runtime_health_epoch")),
            "study_truth_epoch": _non_empty_text(route.get("truth_epoch")),
            "work_unit_fingerprint": _non_empty_text(route.get("work_unit_fingerprint")),
        }
    )
    bridged.update(
        {
            "failure_signature": blocked_repair_reason,
            "owner_reason": blocked_repair_reason,
            "current_owner": "quality_repair_batch",
            "route_epoch": (
                f"quality-repair-writer-handoff::{_non_empty_text(route.get('study_id')) or 'unknown-study'}::"
                f"{source_eval_id or _non_empty_text(route.get('route_epoch')) or 'latest'}"
            ),
            "idempotency_key": (
                f"quality-repair-writer-handoff::{_non_empty_text(route.get('study_id')) or 'unknown-study'}::"
                f"{_non_empty_text(route.get('work_unit_fingerprint')) or source_eval_id or 'latest'}"
            ),
            "source_refs": {key: value for key, value in source_refs.items() if value is not None},
        }
    )
    return owner_route_part.ensure_owner_route_v2(bridged)


def _controller_work_unit_id(
    *,
    authority_route_context: Mapping[str, Any],
    route: Mapping[str, Any],
) -> str | None:
    controller_context = _mapping(authority_route_context.get("controller_route_context"))
    source_refs = _mapping(route.get("source_refs"))
    return (
        _non_empty_text(controller_context.get("work_unit_id"))
        or _non_empty_text(source_refs.get("work_unit_id"))
        or _non_empty_text(route.get("work_unit_id"))
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


__all__ = [
    "NEXT_OWNER",
    "REQUEST_PACKET_REF",
    "build_writer_worker_handoff",
    "owner_request_from_handoff",
    "should_emit_writer_handoff",
]
