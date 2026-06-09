from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import quest_state

from .. import publication_aftercare
from .. import reviewer_refinement_loop
from .. import stage_knowledge_plane
from ..domain_action_request_materializer_parts import current_writer_handoff
from ..domain_health_diagnostic_parts import provider_admission
from ..default_executor_action_policy import (
    SUPPORTED_ACTION_TYPES,
    request_output_surface_for_action_type,
    request_owner_for_action_type,
)
from ..study_progress_parts import repair_progress_projection
from .authority_boundary import authority_boundary_payload


_STUDY_SOURCE_REFS: tuple[tuple[str, Path, str], ...] = (
    ("safe_reconcile_dry_run", Path("artifacts/supervision/reconcile/latest.json"), "safe_reconcile"),
    ("controller_receipt", Path("artifacts/runtime/supervisor_dispatch_receipt/latest.json"), "controller_receipt"),
    ("controller_decisions", Path("artifacts/controller_decisions/latest.json"), "controller_decisions"),
    ("autonomy_slo_status", Path("artifacts/autonomy/slo_status/latest.json"), "slo_status"),
    ("publication_eval", Path("artifacts/publication_eval/latest.json"), "publication_eval"),
    ("paper_work_unit_outbox_receipts", Path("artifacts/runtime/paper_work_unit_outbox/receipts.jsonl"), "paper_work_unit_receipts"),
    ("owner_route_handoff", Path("artifacts/supervision/owner_route_handoff/latest.json"), "owner_route_handoff"),
)
_OPL_CURRENT_CONTROL_REF = Path("runtime/artifacts/supervision/opl_current_control_state/latest.json")
_LEGACY_OPL_CURRENT_CONTROL_REF = Path("artifacts/supervision/opl_current_control_state/latest.json")
_DEFAULT_EXECUTOR_EXECUTION_LATEST = Path(
    "artifacts/supervision/consumer/default_executor_execution/latest.json"
)
_CURRENTNESS_BASIS_KEYS = (
    "owner_reason",
    "runtime_health_epoch",
    "source_eval_id",
    "truth_epoch",
    "work_unit_fingerprint",
    "work_unit_id",
)
READINESS_ACTION_TYPE = "complete_medical_paper_readiness_surface"
READINESS_REPAIR_REASON = "medical_paper_readiness_repair_required"
READINESS_REPAIR_ACTION_TYPES = frozenset(
    {
        "run_quality_repair_batch",
        "run_gate_clearing_batch",
    }
)


def mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def text(value: object) -> str | None:
    value_text = str(value or "").strip()
    return value_text or None


def read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return dict(payload) if isinstance(payload, dict) else None


def workspace_relative(path: Path, *, workspace_root: Path) -> str:
    try:
        return str(path.relative_to(workspace_root))
    except ValueError:
        return str(path)


def source_ref(*, study_root: Path, role: str, relative_path: Path, workspace_root: Path) -> dict[str, Any]:
    path = study_root / relative_path
    return {"ref_kind": "repo_path", "role": role, "ref": workspace_relative(path, workspace_root=workspace_root), "exists": path.exists()}


def build_study_projection(*, study_root: Path, profile: WorkspaceProfile) -> dict[str, Any]:
    source_refs = [
        source_ref(
            study_root=study_root,
            role=role,
            relative_path=relative_path,
            workspace_root=profile.workspace_root,
        )
        for role, relative_path, _ in _STUDY_SOURCE_REFS
    ]
    payload: dict[str, Any] = {
        "study_id": study_root.name,
        "study_root": str(study_root),
        "domain_owned_source_refs": source_refs,
    }
    for _, relative_path, field_name in _STUDY_SOURCE_REFS:
        if field_name not in payload:
            payload[field_name] = read_json_object(study_root / relative_path)
    current_control_handoff = current_control_owner_route_handoff_record(
        study_root=study_root,
        profile=profile,
        existing_record=mapping(payload.get("owner_route_handoff")),
    )
    if current_control_handoff is not None:
        payload["owner_route_handoff"] = current_control_handoff
    current_control_owner_action = current_control_owner_action_record(
        study_root=study_root,
        profile=profile,
    )
    current_writer_owner_action = current_writer_handoff_owner_action_record(
        study_root=study_root,
        profile=profile,
    )
    stage_native_owner_action = stage_native_next_action_owner_action_record(
        study_root=study_root,
        profile=profile,
    )
    provider_admission_owner_action = provider_admission_owner_action_record(
        study_root=study_root,
    )
    owner_route_reconcile_repair_action = owner_route_reconcile_readiness_repair_owner_action_record(
        study_root=study_root,
        profile=profile,
    )
    current_readiness_owner_action = current_readiness_owner_action_record(
        study_root=study_root,
        profile=profile,
        controller_decision=mapping(payload.get("controller_decisions")),
    )
    current_owner_action = (
        current_writer_owner_action
        or provider_admission_owner_action
        or stage_native_owner_action
        or owner_route_reconcile_repair_action
        or current_control_owner_action
        or current_readiness_owner_action
    )
    if current_owner_action is not None:
        payload["current_owner_action"] = current_owner_action
    current_owner_route_handoff_exists = (
        current_control_handoff is not None or current_owner_action is not None
    )
    payload["paper_autonomy_loop"] = paper_autonomy_loop_projection(
        study_root=study_root,
        current_owner_route_handoff_exists=current_owner_route_handoff_exists,
    )
    payload["publication_aftercare"] = publication_aftercare_projection(
        study_root=study_root,
        current_owner_route_handoff_exists=current_owner_route_handoff_exists,
    )
    payload["memory_paper_soak_proof"] = memory_paper_soak_proof_projection(
        study_root=study_root,
        profile=profile,
    )
    payload["autonomy_continuation"] = autonomy_continuation_projection(payload)
    return payload


def autonomy_continuation_projection(study: Mapping[str, Any]) -> dict[str, Any]:
    slo_status = mapping(study.get("slo_status"))
    progress_pressure = mapping(slo_status.get("progress_pressure"))
    pressure_status = text(progress_pressure.get("status"))
    stop_allowed = progress_pressure.get("stop_allowed") is True
    continuation_required = progress_pressure.get("continuation_required") is True
    if pressure_status == "advance_now" and continuation_required and not stop_allowed:
        return {
            "surface_kind": "mas_autonomy_continuation_projection",
            "eligible_for_auto_dispatch": True,
            "status": "progress_pressure_continue",
            "operator_label": "continue_owner_route",
            "replacement_owner": "one-person-lab",
            "recommended_task_kind": "domain_route/reconcile-apply",
            "workspace_profile": None,
            "progress_pressure": dict(progress_pressure),
        }
    return {
        "surface_kind": "mas_autonomy_continuation_projection",
        "eligible_for_auto_dispatch": False,
        "status": "retired_runtime_liveness_scheduler_signal",
        "operator_label": None,
        "replacement_owner": "one-person-lab",
        "recommended_task_kind": None,
        "workspace_profile": None,
    }


def current_control_owner_route_handoff_record(
    *,
    study_root: Path,
    profile: WorkspaceProfile,
    existing_record: Mapping[str, Any],
) -> dict[str, Any] | None:
    handoff_path, payload = _current_control_payload(profile.workspace_root)
    if payload is None:
        return None
    matching = _matching_current_control_study(payload, study_id=study_root.name)
    if matching is None:
        return None
    current_recorded_at = text(matching.get("handoff_generated_at")) or text(payload.get("generated_at"))
    if not _current_control_supersedes_existing(
        current_recorded_at=current_recorded_at,
        existing_record=existing_record,
    ):
        return None
    owner_route = mapping(matching.get("owner_route"))
    if text(owner_route.get("next_owner")) != "one-person-lab":
        return None
    reason = text(owner_route.get("owner_reason"))
    if reason is None:
        return None
    currentness_contract = mapping(owner_route.get("currentness_contract"))
    currentness_basis = _currentness_basis(currentness_contract)
    if currentness_basis is None:
        return None
    runtime_health = mapping(matching.get("runtime_health"))
    quest_id = text(matching.get("quest_id")) or study_root.name
    quest_root = text(matching.get("quest_root"))
    runtime_state_path = text(matching.get("runtime_state_path"))
    if runtime_state_path is None and quest_root is not None:
        runtime_state_path = str(quest_state.canonical_runtime_state_path(Path(quest_root)))
    owner_route_handoff_ref = str(_OPL_CURRENT_CONTROL_REF)
    handoff = {
        "surface_kind": "mas_runtime_owner_route_handoff",
        "domain_truth_owner": "med-autoscience",
        "queue_owner": "one-person-lab",
        "dispatch_surface": "medautosci domain-handler export -> medautosci domain-handler dispatch",
        "recommended_task_kind": "domain_route/reconcile-apply",
        "study_id": study_root.name,
        "quest_id": quest_id,
        "runtime_state_path": runtime_state_path,
        "source": "opl_current_control_state_owner_route_handoff",
        "reason": reason,
        "repair_kind": text(runtime_health.get("canonical_runtime_action")) or reason,
        "recorded_at": current_recorded_at,
        "work_unit_fingerprint": currentness_basis["work_unit_fingerprint"],
        "owner_route_currentness_basis": currentness_basis,
        "owner_route_currentness_contract": dict(currentness_contract),
        "owner_route_attempt_protocol": dict(mapping(owner_route.get("owner_route_attempt_protocol"))),
        "owner_route_idempotency_key": text(owner_route.get("idempotency_key")),
        "runtime_health": dict(runtime_health),
        "authority_boundary": {
            "mas_writes_generic_runtime_queue": False,
            "mas_submits_runtime_chat": False,
            "mas_resumes_provider_worker": False,
            "opl_writes_mas_truth": False,
            "mas_owner_receipt_required": True,
        },
    }
    return {
        "surface_kind": "mas_runtime_owner_route_handoff_record",
        "schema_version": 1,
        "source": "opl_current_control_state_owner_route_handoff",
        "study_id": study_root.name,
        "quest_id": quest_id,
        "recorded_at": current_recorded_at,
        "runtime_state_mutated": False,
        "owner_route_handoff_ref": owner_route_handoff_ref,
        "source_ref_role": "opl_current_control_state_owner_route",
        "source_relative_path": str(_OPL_CURRENT_CONTROL_REF),
        "supersedes_recorded_at": _existing_handoff_recorded_at(existing_record),
        "handoff": handoff,
    }


def current_control_owner_action_record(
    *,
    study_root: Path,
    profile: WorkspaceProfile,
) -> dict[str, Any] | None:
    handoff_path, payload = _current_control_payload(profile.workspace_root)
    if payload is None:
        return None
    action = _matching_current_control_action(payload, study_id=study_root.name)
    if action is None:
        return None
    action_type = text(action.get("action_type"))
    if action_type is None:
        return None
    owner_route = mapping(action.get("owner_route"))
    currentness_contract = mapping(owner_route.get("currentness_contract"))
    currentness_basis = _currentness_basis(currentness_contract)
    if currentness_basis is None:
        return None
    next_work_unit = mapping(action.get("controller_next_work_unit"))
    work_unit_id = text(next_work_unit.get("unit_id")) or currentness_basis.get("work_unit_id")
    if work_unit_id is None:
        return None
    current_recorded_at = text(mapping(action.get("consumption")).get("first_seen_at")) or text(
        payload.get("generated_at")
    )
    return {
        "surface_kind": "mas_current_owner_action_record",
        "schema_version": 1,
        "source": "opl_current_control_state_action_queue",
        "study_id": study_root.name,
        "quest_id": text(action.get("quest_id")) or study_root.name,
        "recorded_at": current_recorded_at,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "recommended_task_kind": "domain_owner/default-executor-dispatch",
        "owner_route_currentness_basis": currentness_basis,
        "owner_route": dict(owner_route),
        "currentness_status": "current_owner_action_active",
        "source_ref_role": "opl_current_control_state_action_queue",
        "source_relative_path": str(_OPL_CURRENT_CONTROL_REF),
        "authority_boundary": {
            "mas_writes_generic_runtime_queue": False,
            "mas_submits_runtime_chat": False,
            "mas_resumes_provider_worker": False,
            "opl_writes_mas_truth": False,
            "mas_owner_receipt_required": True,
        },
    }


def current_writer_handoff_owner_action_record(
    *,
    study_root: Path,
    profile: WorkspaceProfile,
) -> dict[str, Any] | None:
    action = current_writer_handoff.current_quality_repair_writer_handoff_action(
        profile=profile,
        study_id=study_root.name,
    )
    if action is None:
        return None
    action_type = text(action.get("action_type"))
    if action_type is None:
        return None
    owner_route = mapping(action.get("owner_route"))
    currentness_basis = _owner_route_currentness_basis(owner_route)
    if currentness_basis is None:
        return None
    next_work_unit = mapping(action.get("next_work_unit"))
    work_unit_id = text(next_work_unit.get("unit_id")) or text(action.get("work_unit_id")) or currentness_basis.get(
        "work_unit_id"
    )
    if work_unit_id is None:
        return None
    writer_handoff = mapping(action.get("writer_worker_handoff"))
    recorded_at = text(writer_handoff.get("generated_at"))
    return {
        "surface_kind": "mas_current_owner_action_record",
        "schema_version": 1,
        "source": "quality_repair_batch_writer_handoff",
        "study_id": study_root.name,
        "quest_id": text(action.get("quest_id")) or study_root.name,
        "recorded_at": recorded_at,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "recommended_task_kind": "domain_owner/default-executor-dispatch",
        "owner_route_currentness_basis": currentness_basis,
        "owner_route": dict(owner_route),
        "currentness_status": "current_writer_handoff_active",
        "source_ref_role": "quality_repair_batch_writer_handoff",
        "source_relative_path": "studies/"
        f"{study_root.name}/artifacts/controller/quality_repair_batch/latest.json",
        "authority_boundary": {
            "mas_writes_generic_runtime_queue": False,
            "mas_submits_runtime_chat": False,
            "mas_resumes_provider_worker": False,
            "opl_writes_mas_truth": False,
            "mas_owner_receipt_required": True,
        },
    }


def stage_native_next_action_owner_action_record(
    *,
    study_root: Path,
    profile: WorkspaceProfile,
) -> dict[str, Any] | None:
    next_action = read_json_object(study_root / "control" / "next_action.json")
    if next_action is None:
        return None
    if text(next_action.get("status")) != "ready_for_owner_action":
        return None
    action_type = text(next_action.get("action_id")) or text(next_action.get("action_type"))
    if action_type not in SUPPORTED_ACTION_TYPES:
        return None
    owner = text(next_action.get("owner")) or request_owner_for_action_type(action_type)
    quest_id = _read_quest_id(study_root=study_root, fallback=study_root.name)
    owner_route = _stage_native_owner_route(
        study_id=study_root.name,
        quest_id=quest_id,
        action_type=action_type,
        owner=owner,
        next_action=next_action,
    )
    currentness_basis = _owner_route_currentness_basis(owner_route)
    if currentness_basis is None:
        return None
    return {
        "surface_kind": "mas_current_owner_action_record",
        "schema_version": 1,
        "source": "stage_native_workspace_next_action",
        "study_id": study_root.name,
        "quest_id": quest_id,
        "recorded_at": text(next_action.get("generated_at")) or text(next_action.get("recorded_at")),
        "action_type": action_type,
        "work_unit_id": currentness_basis["work_unit_id"],
        "recommended_task_kind": "domain_owner/default-executor-dispatch",
        "next_owner": owner,
        "allowed_actions": [action_type],
        "required_output_surface": text(next_action.get("required_output_surface"))
        or text(next_action.get("target_surface"))
        or request_output_surface_for_action_type(action_type),
        "source_ref_role": "stage_native_workspace_next_action",
        "source_relative_path": workspace_relative(
            study_root / "control" / "next_action.json",
            workspace_root=profile.workspace_root,
        ),
        "source_surface": text(next_action.get("source_surface")),
        "stage_index_ref": text(next_action.get("stage_index_ref")),
        "current_stage_id": text(next_action.get("current_stage_id")),
        "owner_route_currentness_basis": currentness_basis,
        "owner_route": dict(owner_route),
        "currentness_status": "stage_native_next_action_active",
        "authority_boundary": {
            "mas_writes_generic_runtime_queue": False,
            "mas_submits_runtime_chat": False,
            "mas_resumes_provider_worker": False,
            "opl_writes_mas_truth": False,
            "mas_owner_receipt_required": True,
        },
    }


def provider_admission_owner_action_record(
    *,
    study_root: Path,
) -> dict[str, Any] | None:
    repair_progress = repair_progress_projection.build_repair_progress_projection(study_root=study_root)
    if repair_progress.get("paper_delta_observed") is not True:
        return None
    if repair_progress.get("accepted_owner_receipt") is not True:
        return None
    current_action = _repair_progress_current_owner_action(repair_progress=repair_progress)
    candidates = provider_admission.persisted_provider_admission_candidates(
        study_root=study_root,
        status_payload={
            "study_id": study_root.name,
            "current_executable_owner_action": current_action,
        },
    )
    if not candidates:
        return None
    candidate = candidates[0]
    action_type = text(candidate.get("action_type"))
    work_unit_id = text(candidate.get("work_unit_id"))
    action_fingerprint = text(candidate.get("action_fingerprint")) or text(candidate.get("work_unit_fingerprint"))
    if action_type is None or work_unit_id is None:
        return None
    owner_route = _provider_admission_owner_route(candidate)
    currentness_basis = _owner_route_currentness_basis(owner_route)
    if currentness_basis is None:
        return None
    return {
        "surface_kind": "mas_current_owner_action_record",
        "schema_version": 1,
        "source": "default_executor_execution.provider_admission_identity",
        "study_id": study_root.name,
        "quest_id": text(candidate.get("quest_id")) or study_root.name,
        "recorded_at": text(candidate.get("recorded_at")),
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "recommended_task_kind": "domain_owner/default-executor-dispatch",
        "next_owner": text(candidate.get("next_executable_owner")),
        "allowed_actions": [action_type],
        "required_output_surface": text(candidate.get("required_output_surface")),
        "source_ref_role": "default_executor_execution_provider_admission_identity",
        "source_relative_path": text(candidate.get("execution_ref")),
        "source_surface": "default_executor_execution",
        "provider_admission_identity": dict(candidate),
        "provider_admission_identity_ref": text(candidate.get("execution_ref")),
        "repair_progress_followup": current_action,
        "owner_route_currentness_basis": currentness_basis,
        "owner_route": owner_route,
        "currentness_status": "provider_admission_identity_active",
        "authority_boundary": {
            "mas_writes_generic_runtime_queue": False,
            "mas_submits_runtime_chat": False,
            "mas_resumes_provider_worker": False,
            "opl_writes_mas_truth": False,
            "mas_owner_receipt_required": True,
        },
    }


def owner_route_reconcile_readiness_repair_owner_action_record(
    *,
    study_root: Path,
    profile: WorkspaceProfile,
) -> dict[str, Any] | None:
    handoff_path = profile.workspace_root / _OPL_CURRENT_CONTROL_REF
    payload = read_json_object(handoff_path)
    if payload is None:
        return None
    matching = _matching_current_control_study(payload, study_id=study_root.name)
    if matching is None:
        return None
    action = _readiness_repair_action_from_reconcile_study(matching)
    if action is None:
        return None
    action_type = text(action.get("action_type"))
    if action_type is None:
        return None
    owner_route = mapping(action.get("owner_route")) or mapping(matching.get("owner_route"))
    currentness_basis = _owner_route_currentness_basis(owner_route)
    if currentness_basis is None:
        return None
    work_unit_id = _repair_work_unit_id(action=action, currentness_basis=currentness_basis)
    if work_unit_id is None:
        return None
    consumption = mapping(action.get("consumption"))
    recorded_at = (
        text(consumption.get("first_seen_at"))
        or text(matching.get("handoff_generated_at"))
        or text(payload.get("generated_at"))
    )
    next_owner = _action_next_owner(action=action, owner_route=owner_route)
    allowed_actions = _allowed_actions_for_action(action=action, owner_route=owner_route, action_type=action_type)
    return {
        "surface_kind": "mas_current_owner_action_record",
        "schema_version": 1,
        "source": "owner_route_reconcile_readiness_blocker_repair",
        "study_id": study_root.name,
        "quest_id": text(action.get("quest_id")) or text(matching.get("quest_id")) or study_root.name,
        "recorded_at": recorded_at,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "recommended_task_kind": "domain_owner/default-executor-dispatch",
        "next_owner": next_owner,
        "allowed_actions": allowed_actions,
        "required_output_surface": text(action.get("required_output_surface")),
        "source_eval_id": text(action.get("source_eval_id")),
        "publication_eval_gap_ids": _text_list(action.get("publication_eval_gap_ids")),
        "readiness_blocker_followup_superseded": text(action.get("readiness_blocker_followup_superseded")),
        "readiness_blocker_ref": text(action.get("readiness_blocker_ref")) or text(action.get("source_ref")),
        "source_ref_role": "opl_current_control_state_readiness_blocker_repair",
        "source_relative_path": str(_OPL_CURRENT_CONTROL_REF),
        "owner_route_currentness_basis": currentness_basis,
        "owner_route": dict(owner_route),
        "currentness_status": "readiness_blocker_derived_repair_active",
        "authority_boundary": {
            "mas_writes_generic_runtime_queue": False,
            "mas_submits_runtime_chat": False,
            "mas_resumes_provider_worker": False,
            "opl_writes_mas_truth": False,
            "mas_owner_receipt_required": True,
        },
    }


def current_readiness_owner_action_record(
    *,
    study_root: Path,
    profile: WorkspaceProfile,
    controller_decision: Mapping[str, Any],
) -> dict[str, Any] | None:
    if text(controller_decision.get("decision_type")) != "medical_paper_readiness_owner_blocker":
        return None
    next_action = mapping(controller_decision.get("readiness_next_action"))
    action_type = text(next_action.get("action_id"))
    if action_type != "complete_medical_paper_readiness_surface":
        return None
    surface_key = text(next_action.get("surface_key"))
    if surface_key is None:
        return None
    work_unit_id = action_type
    source_ref = workspace_relative(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        workspace_root=profile.workspace_root,
    )
    provider_handoff = _current_provider_handoff_execution(
        study_root=study_root,
        action_type=action_type,
        work_unit_id=work_unit_id,
    )
    provider_source_refs = mapping(mapping(provider_handoff.get("owner_route")).get("source_refs"))
    provider_basis = mapping(provider_source_refs.get("owner_route_currentness_basis"))
    provider_fingerprint = (
        text(provider_handoff.get("action_fingerprint"))
        or text(provider_handoff.get("work_unit_fingerprint"))
        or text(provider_source_refs.get("work_unit_fingerprint"))
        or text(provider_basis.get("work_unit_fingerprint"))
    )
    provider_truth_epoch = (
        text(provider_basis.get("truth_epoch"))
        or text(provider_source_refs.get("truth_epoch"))
        or text(provider_handoff.get("generated_at"))
    )
    provider_runtime_epoch = (
        text(provider_basis.get("runtime_health_epoch"))
        or text(provider_source_refs.get("runtime_health_epoch"))
        or text(provider_handoff.get("generated_at"))
    )
    owner_route_currentness_basis = {
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": provider_fingerprint or f"medical-paper-readiness::{surface_key}",
        "truth_epoch": provider_truth_epoch or text(controller_decision.get("generated_at")) or source_ref,
        "runtime_health_epoch": provider_runtime_epoch
        or text(controller_decision.get("generated_at"))
        or source_ref,
    }
    return {
        "surface_kind": "mas_current_owner_action_record",
        "schema_version": 1,
        "source": "controller_decisions.readiness_next_action",
        "study_id": study_root.name,
        "quest_id": study_root.name,
        "recorded_at": text(controller_decision.get("generated_at")),
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "recommended_task_kind": "domain_owner/default-executor-dispatch",
        "next_owner": "MedAutoScience",
        "allowed_actions": [action_type],
        "surface_key": surface_key,
        "next_action": dict(next_action),
        "target_surface": {
            "ref_kind": "mas_owner_surface",
            "surface_ref": action_type,
            "surface_key": surface_key,
        },
        "target_surface_specificity": "controller_decisions_readiness_next_action",
        "owner_route_currentness_basis": owner_route_currentness_basis,
        **({"work_unit_fingerprint": provider_fingerprint} if provider_fingerprint is not None else {}),
        **(
            {
                "provider_admission_identity_source": "default_executor_execution",
                "provider_admission_execution_ref": workspace_relative(
                    study_root / _DEFAULT_EXECUTOR_EXECUTION_LATEST,
                    workspace_root=profile.workspace_root,
                ),
            }
            if provider_handoff
            else {}
        ),
        "currentness_status": "current_readiness_owner_action_active",
        "source_ref_role": "controller_decisions_readiness_next_action",
        "source_relative_path": source_ref,
        "authority_boundary": {
            "mas_writes_generic_runtime_queue": False,
            "mas_submits_runtime_chat": False,
            "mas_resumes_provider_worker": False,
            "opl_writes_mas_truth": False,
            "mas_owner_receipt_required": True,
        },
    }


def _current_provider_handoff_execution(
    *,
    study_root: Path,
    action_type: str,
    work_unit_id: str,
) -> dict[str, Any]:
    payload = read_json_object(study_root / _DEFAULT_EXECUTOR_EXECUTION_LATEST)
    if payload is None:
        return {}
    for item in payload.get("executions") or []:
        if not isinstance(item, Mapping):
            continue
        if text(item.get("execution_status")) != "handoff_ready":
            continue
        if item.get("provider_attempt_or_lease_required") is not True and text(
            item.get("owner_callable_surface")
        ) != "opl_default_executor.stage_attempt":
            continue
        if item.get("owner_route_current") is False:
            continue
        if text(item.get("action_type")) != action_type:
            continue
        source_refs = mapping(mapping(item.get("owner_route")).get("source_refs"))
        candidate_work_unit = (
            text(source_refs.get("work_unit_id"))
            or text(item.get("work_unit_id"))
            or text(mapping(source_refs.get("owner_route_currentness_basis")).get("work_unit_id"))
        )
        if candidate_work_unit != work_unit_id:
            continue
        return dict(item)
    return {}


def _matching_current_control_study(
    payload: Mapping[str, Any],
    *,
    study_id: str,
) -> dict[str, Any] | None:
    for item in payload.get("studies") or []:
        if isinstance(item, Mapping) and text(item.get("study_id")) == study_id:
            return dict(item)
    return None


def _current_control_payload(workspace_root: Path) -> tuple[Path, dict[str, Any] | None]:
    for relative_path in (_OPL_CURRENT_CONTROL_REF, _LEGACY_OPL_CURRENT_CONTROL_REF):
        path = workspace_root / relative_path
        payload = read_json_object(path)
        if payload is not None:
            return path, payload
    return workspace_root / _OPL_CURRENT_CONTROL_REF, None


def _matching_current_control_action(
    payload: Mapping[str, Any],
    *,
    study_id: str,
) -> dict[str, Any] | None:
    for item in payload.get("action_queue") or []:
        if not isinstance(item, Mapping) or text(item.get("study_id")) != study_id:
            continue
        consumption_state = text(mapping(item.get("consumption")).get("state"))
        if consumption_state not in {None, "unconsumed"}:
            continue
        owner_route = mapping(item.get("owner_route"))
        action_type = text(item.get("action_type"))
        if action_type is None:
            continue
        allowed_actions = {
            text(entry)
            for entry in owner_route.get("allowed_actions") or []
            if text(entry) is not None
        }
        if allowed_actions and action_type not in allowed_actions:
            continue
        return dict(item)
    return None


def _readiness_repair_action_from_reconcile_study(
    study: Mapping[str, Any],
) -> dict[str, Any] | None:
    current_action = mapping(study.get("current_executable_owner_action"))
    current_allowed_actions = set(_text_list(current_action.get("allowed_actions")))
    current_work_unit_id = text(current_action.get("work_unit_id"))
    for item in study.get("action_queue") or []:
        if not isinstance(item, Mapping):
            continue
        if not _is_readiness_blocker_derived_repair_action(item):
            continue
        action_type = text(item.get("action_type"))
        if action_type is None:
            continue
        if current_allowed_actions and action_type not in current_allowed_actions:
            continue
        if current_work_unit_id is not None:
            owner_route = mapping(item.get("owner_route")) or mapping(study.get("owner_route"))
            basis = _owner_route_currentness_basis(owner_route) or {}
            if _repair_work_unit_id(action=item, currentness_basis=basis) != current_work_unit_id:
                continue
        return dict(item)
    return None


def _is_readiness_blocker_derived_repair_action(action: Mapping[str, Any]) -> bool:
    action_type = text(action.get("action_type"))
    if action_type not in READINESS_REPAIR_ACTION_TYPES:
        return False
    owner_route = mapping(action.get("owner_route"))
    reason = (
        text(action.get("reason"))
        or text(owner_route.get("owner_reason"))
        or text(owner_route.get("failure_signature"))
    )
    if reason != READINESS_REPAIR_REASON:
        return False
    if text(action.get("readiness_blocker_followup_superseded")) != READINESS_ACTION_TYPE:
        return False
    if not _text_list(action.get("publication_eval_gap_ids")):
        return False
    consumption_state = text(mapping(action.get("consumption")).get("state"))
    return consumption_state in {None, "unconsumed"}


def _repair_work_unit_id(
    *,
    action: Mapping[str, Any],
    currentness_basis: Mapping[str, Any],
) -> str | None:
    next_work_unit = action.get("next_work_unit")
    next_work_unit_id = (
        text(mapping(next_work_unit).get("unit_id"))
        if isinstance(next_work_unit, Mapping)
        else text(next_work_unit)
    )
    return (
        text(action.get("controller_work_unit_id"))
        or text(action.get("executable_work_unit"))
        or next_work_unit_id
        or text(action.get("work_unit_id"))
        or text(currentness_basis.get("work_unit_id"))
    )


def _repair_progress_current_owner_action(*, repair_progress: Mapping[str, Any]) -> dict[str, Any]:
    ai_reviewer_request_ref = text(repair_progress.get("ai_reviewer_recheck_request_ref"))
    gate_replay_refs = _text_list(repair_progress.get("gate_replay_refs"))
    source_ref = text(repair_progress.get("repair_execution_evidence_ref")) or text(
        repair_progress.get("owner_receipt_ref")
    )
    if ai_reviewer_request_ref is not None:
        action_type = "return_to_ai_reviewer_workflow"
        work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
        next_owner = "ai_reviewer"
        target_surface = {
            "ref_kind": "route_obligation",
            "route_target": "review",
            "surface_ref": "artifacts/publication_eval/latest.json",
            "request_ref": ai_reviewer_request_ref,
            **({"gate_replay_request_ref": gate_replay_refs[0]} if gate_replay_refs else {}),
        }
        acceptance_refs = [ai_reviewer_request_ref, *gate_replay_refs]
    elif gate_replay_refs:
        action_type = "run_gate_clearing_batch"
        work_unit_id = "publication_gate_replay"
        next_owner = "gate_clearing_batch"
        target_surface = {
            "ref_kind": "route_obligation",
            "route_target": "finalize",
            "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
            "request_ref": gate_replay_refs[0],
        }
        acceptance_refs = gate_replay_refs
    else:
        action_type = None
        work_unit_id = None
        next_owner = None
        target_surface = {}
        acceptance_refs = []
    return {
        key: value
        for key, value in {
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "next_owner": next_owner,
            "work_unit_id": work_unit_id,
            "action_type": action_type,
            "allowed_actions": [action_type] if action_type is not None else [],
            "owner_receipt_required": True,
            "target_surface": target_surface or None,
            "target_surface_specificity": "repair_progress_followup_owner_surface",
            "source_ref": source_ref,
            "acceptance_refs": [
                ref
                for ref in [
                    text(repair_progress.get("repair_execution_evidence_ref")),
                    text(repair_progress.get("owner_receipt_ref")),
                    *acceptance_refs,
                ]
                if ref is not None
            ],
        }.items()
        if value is not None
    }


def _provider_admission_owner_route(candidate: Mapping[str, Any]) -> dict[str, Any]:
    source_refs = mapping(candidate.get("source_refs"))
    currentness_basis = mapping(candidate.get("currentness_basis"))
    work_unit_id = text(candidate.get("work_unit_id"))
    action_type = text(candidate.get("action_type"))
    action_fingerprint = text(candidate.get("action_fingerprint")) or text(candidate.get("work_unit_fingerprint"))
    merged_source_refs = {
        **dict(source_refs),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "provider_admission_identity_ref": text(candidate.get("execution_ref")),
        "dispatch_path": text(candidate.get("dispatch_path")),
        "blocked_reason": text(candidate.get("blocked_reason")),
        "owner_route_currentness_basis": {
            **dict(currentness_basis),
            **(
                {
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                }
                if work_unit_id is not None and action_fingerprint is not None
                else {}
            ),
        },
    }
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": text(candidate.get("study_id")),
        "quest_id": text(candidate.get("quest_id")),
        "truth_epoch": text(currentness_basis.get("truth_epoch")) or action_fingerprint,
        "runtime_health_epoch": text(currentness_basis.get("runtime_health_epoch"))
        or text(currentness_basis.get("source_eval_id"))
        or action_fingerprint,
        "work_unit_fingerprint": action_fingerprint,
        "source_fingerprint": action_fingerprint,
        "route_epoch": action_fingerprint,
        "current_owner": "med-autoscience",
        "next_owner": text(candidate.get("next_executable_owner")),
        "owner_reason": work_unit_id or action_type,
        "active_run_id": None,
        "allowed_actions": [action_type] if action_type is not None else [],
        "blocked_actions": [],
        "source_refs": {
            key: value for key, value in merged_source_refs.items() if value is not None
        },
        "idempotency_key": f"provider-admission::{text(candidate.get('study_id'))}::{action_fingerprint}",
    }


def _action_next_owner(
    *,
    action: Mapping[str, Any],
    owner_route: Mapping[str, Any],
) -> str | None:
    return (
        text(action.get("next_owner"))
        or text(action.get("owner"))
        or text(action.get("request_owner"))
        or text(action.get("recommended_owner"))
        or text(owner_route.get("next_owner"))
    )


def _allowed_actions_for_action(
    *,
    action: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    action_type: str,
) -> list[str]:
    allowed_actions = _text_list(owner_route.get("allowed_actions")) or _text_list(action.get("allowed_actions"))
    return allowed_actions or [action_type]


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in (text(entry) for entry in value) if item is not None]


def _owner_route_currentness_basis(owner_route: Mapping[str, Any]) -> dict[str, str] | None:
    source_refs = mapping(owner_route.get("source_refs"))
    embedded_basis = mapping(source_refs.get("owner_route_currentness_basis"))
    basis = {
        "owner_reason": text(owner_route.get("owner_reason"))
        or text(owner_route.get("failure_signature"))
        or text(source_refs.get("blocked_reason"))
        or text(embedded_basis.get("owner_reason")),
        "runtime_health_epoch": text(owner_route.get("runtime_health_epoch"))
        or text(source_refs.get("runtime_health_epoch"))
        or text(embedded_basis.get("runtime_health_epoch")),
        "source_eval_id": text(owner_route.get("source_eval_id"))
        or text(source_refs.get("source_eval_id"))
        or text(embedded_basis.get("source_eval_id")),
        "truth_epoch": text(owner_route.get("truth_epoch"))
        or text(owner_route.get("route_epoch"))
        or text(embedded_basis.get("truth_epoch")),
        "work_unit_fingerprint": text(owner_route.get("work_unit_fingerprint"))
        or text(source_refs.get("work_unit_fingerprint"))
        or text(embedded_basis.get("work_unit_fingerprint")),
        "work_unit_id": text(owner_route.get("work_unit_id"))
        or text(source_refs.get("work_unit_id"))
        or text(embedded_basis.get("work_unit_id")),
    }
    if basis["truth_epoch"] is None:
        return None
    if basis["work_unit_fingerprint"] is None:
        return None
    if basis["work_unit_id"] is None:
        return None
    if basis["runtime_health_epoch"] is None and basis["source_eval_id"] is None:
        return None
    return {key: value for key, value in basis.items() if value is not None}


def _stage_native_owner_route(
    *,
    study_id: str,
    quest_id: str,
    action_type: str,
    owner: str,
    next_action: Mapping[str, Any],
) -> dict[str, Any]:
    current_stage_id = text(next_action.get("current_stage_id")) or "unknown_stage"
    source_surface = text(next_action.get("source_surface")) or "control/next_action.json"
    fingerprint = f"stage-native-next-action::{current_stage_id}::{action_type}::{source_surface}"
    epoch = f"stage-native-next-action::{study_id}::{current_stage_id}"
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": epoch,
        "runtime_health_epoch": epoch,
        "work_unit_fingerprint": fingerprint,
        "failure_signature": action_type,
        "trace_id": f"owner-route-trace::{study_id}::{action_type}",
        "route_epoch": epoch,
        "source_fingerprint": fingerprint,
        "current_owner": "mas_controller",
        "next_owner": owner,
        "owner_reason": action_type,
        "active_run_id": None,
        "allowed_actions": [action_type],
        "blocked_actions": sorted(item for item in SUPPORTED_ACTION_TYPES if item != action_type),
        "source_refs": {
            "work_unit_id": action_type,
            "work_unit_fingerprint": fingerprint,
            "source_surface": source_surface,
            "stage_index_ref": text(next_action.get("stage_index_ref")),
            "current_stage_id": current_stage_id,
            "owner_route_currentness_basis": {
                "truth_epoch": epoch,
                "runtime_health_epoch": epoch,
                "work_unit_id": action_type,
                "work_unit_fingerprint": fingerprint,
            },
        },
        "idempotency_key": f"owner-route::{study_id}::{epoch}::{owner}::{action_type}",
    }


def _read_quest_id(*, study_root: Path, fallback: str) -> str:
    study_yaml = study_root / "study.yaml"
    try:
        content = study_yaml.read_text(encoding="utf-8")
    except OSError:
        return fallback
    for line in content.splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip() == "quest_id":
            return value.strip().strip("\"'") or fallback
    return fallback


def _current_control_supersedes_existing(
    *,
    current_recorded_at: str | None,
    existing_record: Mapping[str, Any],
) -> bool:
    existing_recorded_at = _existing_handoff_recorded_at(existing_record)
    if existing_recorded_at is None:
        return True
    if current_recorded_at is None:
        return False
    return current_recorded_at > existing_recorded_at


def _existing_handoff_recorded_at(record: Mapping[str, Any]) -> str | None:
    handoff = mapping(record.get("handoff"))
    return text(handoff.get("recorded_at")) or text(record.get("recorded_at"))


def _currentness_basis(contract: Mapping[str, Any]) -> dict[str, str] | None:
    basis = mapping(contract.get("basis"))
    missing = contract.get("missing_required_fields")
    if isinstance(missing, list) and any(text(item) for item in missing):
        return None
    currentness_basis = {key: text(basis.get(key)) for key in _CURRENTNESS_BASIS_KEYS}
    required_fields = [text(item) for item in contract.get("required_fields") or []]
    required_fields = [item for item in required_fields if item is not None]
    if not required_fields:
        required_fields = ["runtime_health_epoch", "truth_epoch", "work_unit_fingerprint"]
    for field in required_fields:
        if field == "runtime_health_epoch_or_source_eval_id":
            if currentness_basis.get("runtime_health_epoch") is None and currentness_basis.get("source_eval_id") is None:
                return None
            continue
        if currentness_basis.get(field) is None:
            return None
    return {key: value for key, value in currentness_basis.items() if value is not None}


def study_roots(profile: WorkspaceProfile) -> list[Path]:
    if not profile.studies_root.is_dir():
        return []
    return sorted(path for path in profile.studies_root.iterdir() if path.is_dir())


def paper_autonomy_loop_projection(
    *,
    study_root: Path,
    current_owner_route_handoff_exists: bool = False,
) -> dict[str, Any]:
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    if not publication_eval_path.exists():
        return {
            "surface_kind": "mas_paper_autonomy_loop_projection",
            "status": "missing_publication_eval",
            "eligible_for_auto_dispatch": False,
            "reason": None,
            "repair_work_units": [],
            "source_refs": [
                {"role": "publication_eval", "ref": str(publication_eval_path), "exists": False},
            ],
        }
    try:
        refinement = reviewer_refinement_loop.build_reviewer_refinement_loop_read_model(study_root=study_root)
    except (OSError, TypeError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        return {
            "surface_kind": "mas_paper_autonomy_loop_projection",
            "status": "blocked",
            "eligible_for_auto_dispatch": False,
            "reason": "reviewer_refinement_loop_unreadable",
            "blockers": [f"reviewer_refinement_loop_unreadable:{exc.__class__.__name__}"],
            "repair_work_units": [],
            "source_refs": [
                {"role": "publication_eval", "ref": str(publication_eval_path), "exists": True},
            ],
        }
    if current_owner_route_handoff_exists:
        return {
            "surface_kind": "mas_paper_autonomy_loop_projection",
            "status": "superseded_by_opl_current_owner_route",
            "eligible_for_auto_dispatch": False,
            "reason": "opl_current_owner_route_handoff_active",
            "accept_status": text(mapping(refinement.get("accept")).get("status")),
            "repair_plan": dict(mapping(mapping(refinement.get("repair_loop")).get("repair_plan"))),
            "repair_work_units": [],
            "source_eval_id": text(mapping(refinement.get("snapshot")).get("source_eval_id")),
            "source_refs": [
                {"role": "publication_eval", "ref": str(publication_eval_path), "exists": True},
            ],
            "currentness_status": "superseded_by_opl_current_owner_route",
            "authority_boundary": authority_boundary_payload(),
        }
    accept = mapping(refinement.get("accept"))
    repair_loop = mapping(refinement.get("repair_loop"))
    repair_plan = mapping(repair_loop.get("repair_plan"))
    accepted = accept.get("accepted") is True
    repair_required = any(
        repair_plan.get(key) is True
        for key in (
            "analysis_repair_required",
            "text_repair_required",
            "ai_reviewer_recheck_required",
        )
    )
    work_units = [dict(unit) for unit in refinement.get("repair_work_units") or [] if isinstance(unit, Mapping)]
    eligible = not accepted and repair_required and bool(work_units)
    return {
        "surface_kind": "mas_paper_autonomy_loop_projection",
        "status": "repair_recheck_ready" if eligible else ("accepted" if accepted else "blocked"),
        "eligible_for_auto_dispatch": eligible,
        "reason": "ai_reviewer_repair_recheck_required" if eligible else None,
        "accept_status": text(accept.get("status")),
        "repair_plan": dict(repair_plan),
        "repair_work_units": work_units,
        "source_eval_id": text(mapping(refinement.get("snapshot")).get("source_eval_id")),
        "source_refs": [
            {"role": "publication_eval", "ref": str(publication_eval_path), "exists": True},
        ],
        "authority_boundary": authority_boundary_payload(),
    }


def publication_aftercare_projection(
    *,
    study_root: Path,
    current_owner_route_handoff_exists: bool = False,
) -> dict[str, Any]:
    projection = publication_aftercare.build_publication_aftercare_plan(study_root=study_root)
    if not current_owner_route_handoff_exists:
        return projection
    result = dict(projection)
    result["currentness_status"] = "superseded_by_opl_current_owner_route"
    for entry_key in ("analysis_queue_entry", "reviewer_refresh_entry"):
        entry = mapping(result.get(entry_key))
        if not entry:
            continue
        result[entry_key] = {
            **dict(entry),
            "eligible_for_owner_route_task_ref": False,
            "currentness_status": "superseded_by_opl_current_owner_route",
        }
    return result


def memory_paper_soak_proof_projection(*, study_root: Path, profile: WorkspaceProfile) -> dict[str, Any]:
    proof_path = stage_knowledge_plane.paper_soak_memory_apply_proof_path(study_root=study_root)
    proof = read_json_object(proof_path)
    if proof is None:
        return {
            "surface_kind": "mas_memory_paper_soak_proof_projection",
            "status": "missing",
            "proof_ref": workspace_relative(proof_path, workspace_root=profile.workspace_root),
            "receipt_refs": [],
            "authority_boundary": authority_boundary_payload(),
            "read_only_display_policy": {
                "consumer": "OPL/Aion",
                "body_included": False,
                "can_write_mas_truth": False,
            },
        }
    receipt_refs = [
        dict(ref)
        for ref in proof.get("opl_aion_readonly_receipt_refs") or []
        if isinstance(ref, Mapping)
    ]
    return {
        "surface_kind": "mas_memory_paper_soak_proof_projection",
        "status": text(proof.get("status")) or "missing",
        "proof_ref": workspace_relative(proof_path, workspace_root=profile.workspace_root),
        "receipt_refs": receipt_refs,
        "route_memory_ref_count": len(mapping(proof.get("stage_entry")).get("publication_route_memory_refs") or []),
        "router_receipt_ref_count": len(proof.get("mas_router_receipt_refs") or []),
        "writeback_proposal_ref_count": len(proof.get("typed_closeout_writeback_proposals") or []),
        "source_fingerprint": text(proof.get("source_fingerprint")),
        "authority_boundary": mapping(proof.get("authority_boundary")) or authority_boundary_payload(),
        "read_only_display_policy": mapping(proof.get("read_only_display_policy")),
    }


__all__ = [
    "build_study_projection",
    "mapping",
    "study_roots",
    "text",
    "workspace_relative",
]
