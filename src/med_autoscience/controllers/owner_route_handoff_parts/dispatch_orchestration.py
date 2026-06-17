from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import yaml

from med_autoscience.profiles import WorkspaceProfile, load_profile

from .. import domain_owner_action_dispatch
from .. import opl_provider_ready_adapter
from .. import paper_repair_executor
from .. import publication_aftercare
from .. import real_paper_autonomy_soak_inventory
from ..opl_execution_boundary import (
    OPL_EXECUTION_AUTHORIZATION_BLOCKER,
    first_trusted_opl_execution_authorization,
)
from ..ai_reviewer_story_provenance_guard import (
    AI_REVIEWER_RECORD_MANUSCRIPT_STORY_PROVENANCE_LEAKAGE_BLOCKED_REASON,
)
from ..domain_action_request_lifecycle import (
    AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_INPUTS,
    AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_MANUSCRIPT,
    AI_REVIEWER_RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN,
)
from ..guarded_apply_owner_delta_contract import (
    guarded_apply_current_owner_delta_binding_summary,
    guarded_apply_current_owner_delta_validation,
    guarded_apply_identity_typed_blocker,
    normalize_guarded_apply_current_owner_delta,
)
from ..real_paper_autonomy_soak_inventory_parts import provider_guarded_apply
from .authority_boundary import authority_boundary_payload
from .dispatch_receipts import write_dispatch_receipt
from .task_kinds import ALLOWED_TASK_KINDS, FORBIDDEN_PAYLOAD_FLAGS

STABLE_PAPER_REPAIR_TYPED_BLOCKERS = frozenset(
    {
        "authority_route_blocked",
        "unsupported_owner_callable_surface",
        OPL_EXECUTION_AUTHORIZATION_BLOCKER,
        AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_INPUTS,
        AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_MANUSCRIPT,
        AI_REVIEWER_RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN,
        AI_REVIEWER_RECORD_MANUSCRIPT_STORY_PROVENANCE_LEAKAGE_BLOCKED_REASON,
    }
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, (list, tuple, set)):
        return []
    return [text for item in value if (text := _text(item)) is not None]


def _bool_or_none(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return dict(payload) if isinstance(payload, dict) else None


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False) + "\n", encoding="utf-8")


def _workspace_relative(path: Path, *, workspace_root: Path) -> str:
    try:
        return str(path.relative_to(workspace_root))
    except ValueError:
        return str(path)


def _load_task(task_path: Path) -> dict[str, Any]:
    payload = _read_json_object(task_path)
    if payload is None:
        raise ValueError(f"domain-handler task must be a JSON object: {task_path}")
    return payload


def _forbidden_write_requested(task: Mapping[str, Any]) -> bool:
    return bool(_forbidden_requested_writes(task))


def _forbidden_requested_writes(task: Mapping[str, Any]) -> list[str]:
    requested = opl_provider_ready_adapter.requested_writes_from_task(task)
    forbidden = {
        *FORBIDDEN_PAYLOAD_FLAGS,
        *opl_provider_ready_adapter.FORBIDDEN_AUTHORITY_WRITES,
    }
    return [item for item in requested if item in forbidden]


def _profile_from_task(task: Mapping[str, Any]) -> tuple[WorkspaceProfile | None, Path | None]:
    payload = _mapping(task.get("payload"))
    profile_ref = _text(payload.get("profile") or payload.get("profile_path"))
    if profile_ref is None:
        return None, None
    path = Path(profile_ref).expanduser()
    return load_profile(path), path


def _recommended_command(action_type: str, *, profile_ref: Path | None, study_id: str | None) -> str:
    profile_part = f" --profile {profile_ref}" if profile_ref is not None else " --profile <profile>"
    study_part = f" --studies {study_id}" if study_id else ""
    if action_type == "domain_route_recover":
        return f"uv run python -m med_autoscience.cli owner-route-reconcile{profile_part}{study_part}"
    if action_type in {"safe_reconcile_dry_run", "domain_route_owner_handoff"}:
        return f"uv run python -m med_autoscience.cli owner-route-reconcile{profile_part}{study_part} --developer-supervisor-mode external_observe"
    if action_type == "study_progress_read":
        study_selector = f" --study-id {study_id}" if study_id else ""
        return f"uv run python -m med_autoscience.cli study progress{profile_part}{study_selector} --format json"
    return f"uv run python -m med_autoscience.cli product entry_status{profile_part} --format json"


def _file_digest(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    except OSError:
        return "missing"


def _owner_capability_fingerprint(*, action_type: str) -> str:
    owner_files = [
        Path(__file__),
        Path(paper_repair_executor.__file__ or ""),
        Path(domain_owner_action_dispatch.__file__ or ""),
    ]
    payload = {
        "action_type": action_type,
        "owner_files": [
            {
                "name": path.name,
                "digest": _file_digest(path),
            }
            for path in owner_files
            if str(path)
        ],
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:20]
    return f"mas-domain-handler-owner-capability:{digest}"


def _execute_paper_repair(
    *,
    profile: WorkspaceProfile | None,
    study_id: str | None,
    task: Mapping[str, Any],
) -> dict[str, Any] | None:
    if profile is None or study_id is None:
        return None
    payload = _mapping(task.get("payload"))
    work_unit = _mapping(payload.get("repair_work_unit"))
    if not work_unit:
        return {
            "surface": "paper_repair_executor",
            "accepted": False,
            "execution_status": "blocked",
            "typed_blocker": "owner_callable_surface_missing",
            "blocked_reason": "repair_work_unit_missing",
        }
    study_root = profile.studies_root / study_id
    quest_id = _canonical_paper_repair_quest_id(
        study_root=study_root,
        payload=payload,
        work_unit=work_unit,
        study_id=study_id,
    )
    return paper_repair_executor.dispatch_repair_work_unit(
        profile=profile,
        study_id=study_id,
        quest_id=quest_id,
        study_root=study_root,
        repair_work_unit=work_unit,
        review_finding=_mapping(payload.get("review_finding")),
        authority_route_context=_mapping(payload.get("authority_route_context")) or None,
        route_context=_mapping(payload.get("route_context")) or None,
        opl_execution_authorization=_opl_execution_authorization(task),
        apply=True,
    )


def _opl_execution_authorization(task: Mapping[str, Any]) -> Mapping[str, Any] | None:
    payload = _mapping(task.get("payload"))
    return first_trusted_opl_execution_authorization(
        payload.get("opl_execution_authorization"),
        payload.get("opl_provider_attempt"),
        payload.get("stage_attempt"),
        task.get("opl_execution_authorization"),
        task.get("opl_provider_attempt"),
        task.get("stage_attempt"),
    )


def _trusted_opl_execution_authorization(candidate: Mapping[str, Any] | None) -> bool:
    return first_trusted_opl_execution_authorization(candidate) is not None


def _canonical_paper_repair_quest_id(
    *,
    study_root: Path,
    payload: Mapping[str, Any],
    work_unit: Mapping[str, Any],
    study_id: str,
) -> str:
    binding_quest_id = _quest_id_from_runtime_binding(study_root / "runtime_binding.yaml")
    return (
        binding_quest_id
        or _text(payload.get("quest_id"))
        or _text(work_unit.get("quest_id"))
        or f"quest-{study_id}"
    )


def _quest_id_from_runtime_binding(path: Path) -> str | None:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(payload, Mapping):
        return None
    return _text(payload.get("quest_id"))


def _execute_ai_reviewer_recheck(
    *,
    profile: WorkspaceProfile | None,
    study_id: str | None,
    task: Mapping[str, Any],
) -> dict[str, Any] | None:
    if profile is None:
        return None
    authorization = _opl_execution_authorization(task)
    if not _trusted_opl_execution_authorization(authorization):
        return {
            "surface": "domain_owner_action_dispatch",
            "accepted": False,
            "execution_status": "blocked",
            "typed_blocker": "opl_execution_authorization_required",
            "blocked_reason": "opl_execution_authorization_required",
            "retryable": False,
            "authority_boundary": "mas_ai_reviewer_recheck_requires_opl_attempt_lease_or_receipt",
        }
    return domain_owner_action_dispatch.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,) if study_id else (),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )


def _execute_guarded_apply(
    *,
    profile_ref: Path | None,
    study_id: str | None,
    task_id: str,
    task: Mapping[str, Any],
) -> dict[str, Any] | None:
    if profile_ref is None or study_id is None:
        return None
    payload = _mapping(task.get("payload"))
    current_owner_delta = _current_owner_delta_from_task(task)
    provider_attempt_id = (
        _text(payload.get("provider_attempt_id"))
        or _text(payload.get("attempt_id"))
        or task_id
    )
    idempotency_key = _text(payload.get("idempotency_key")) or f"{task_id}:guarded_apply"
    target_studies = payload.get("target_studies")
    targets = (
        [str(item) for item in target_studies if _text(item)]
        if isinstance(target_studies, list)
        else [study_id]
    )
    validation = guarded_apply_current_owner_delta_validation(current_owner_delta)
    if validation.get("valid") is not True:
        return provider_guarded_apply.build_guarded_apply_current_owner_delta_typed_blocker_receipt(
            schema_version=real_paper_autonomy_soak_inventory.SCHEMA_VERSION,
            surface=real_paper_autonomy_soak_inventory.PROVIDER_HOSTED_GUARDED_APPLY_RECEIPT_SURFACE,
            provider_attempt_id=provider_attempt_id,
            idempotency_key=idempotency_key,
            target_studies=targets,
            typed_blocker=guarded_apply_identity_typed_blocker(current_owner_delta) or {},
            current_owner_delta=current_owner_delta,
        )
    if payload.get("provider_ready") is False:
        return provider_guarded_apply.build_provider_unavailable_guarded_apply_receipt(
            schema_version=real_paper_autonomy_soak_inventory.SCHEMA_VERSION,
            surface=real_paper_autonomy_soak_inventory.PROVIDER_HOSTED_GUARDED_APPLY_RECEIPT_SURFACE,
            provider_attempt_id=provider_attempt_id,
            idempotency_key=idempotency_key,
            target_studies=targets,
            reason=_text(payload.get("provider_unavailable_reason")) or "provider_ready_false",
            current_owner_delta=current_owner_delta,
        )
    return real_paper_autonomy_soak_inventory.build_real_paper_autonomy_provider_hosted_guarded_apply_receipt(
        profile_path=profile_ref,
        provider_attempt_id=provider_attempt_id,
        idempotency_key=idempotency_key,
        target_studies=targets,
        current_owner_delta=current_owner_delta,
    )


def _current_owner_delta_from_task(task: Mapping[str, Any]) -> dict[str, Any]:
    payload = _mapping(task.get("payload"))
    candidates = (
        payload.get("current_owner_delta"),
        payload.get("opl_current_owner_delta"),
        payload.get("stage_run_current_owner_delta"),
        task.get("current_owner_delta"),
        task.get("opl_current_owner_delta"),
        task.get("stage_run_current_owner_delta"),
    )
    for candidate in candidates:
        delta = normalize_guarded_apply_current_owner_delta(_mapping(candidate))
        if delta:
            return delta
    compact = {
        key: value
        for key, value in {
            "surface_kind": "opl_current_owner_delta",
            "default_planning_root": _text(payload.get("default_planning_root") or task.get("default_planning_root")),
            "stage_id": _text(payload.get("stage_id") or task.get("stage_id")),
            "lineage_ref": _text(payload.get("lineage_ref") or task.get("lineage_ref")),
            "current_owner": _text(payload.get("current_owner") or task.get("current_owner")),
            "owner": _text(payload.get("owner") or task.get("owner")),
            "desired_delta": _text(payload.get("desired_delta") or task.get("desired_delta")),
            "desired_delta_kind": _text(payload.get("desired_delta_kind") or task.get("desired_delta_kind")),
            "accepted_answer_shape": _string_list(
                payload.get("accepted_answer_shape") or task.get("accepted_answer_shape")
            ),
            "accepted_return_shapes": _string_list(
                payload.get("accepted_return_shapes") or task.get("accepted_return_shapes")
            ),
            "latest_owner_answer_ref": _text(
                payload.get("latest_owner_answer_ref") or task.get("latest_owner_answer_ref")
            ),
            "domain_ready_authorized": _bool_or_none(
                payload.get("domain_ready_authorized")
                if "domain_ready_authorized" in payload
                else task.get("domain_ready_authorized")
            ),
            "owner_answer_missing": _bool_or_none(
                payload.get("owner_answer_missing")
                if "owner_answer_missing" in payload
                else task.get("owner_answer_missing")
            ),
            "owner_answer_still_required": _bool_or_none(
                payload.get("owner_answer_still_required")
                if "owner_answer_still_required" in payload
                else task.get("owner_answer_still_required")
            ),
        }.items()
        if value not in (None, [], {})
    }
    return normalize_guarded_apply_current_owner_delta(compact)


def _base_dispatch_receipt(
    *,
    generated_at: str,
    task_id: str,
    task_kind: str,
    task_path: Path,
    action_type: str,
    profile_ref: Path | None,
    study_id: str | None,
    source_fingerprint: str | None,
) -> dict[str, Any]:
    receipt = {
        "surface_kind": "mas_family_domain_handler_dispatch_receipt",
        "version": "mas-family-domain-handler.v1",
        "accepted": True,
        "task_id": task_id,
        "task_kind": task_kind,
        "generated_at": generated_at,
        "source_task_ref": str(task_path),
        "opl_attempt_admission_requested": False,
        "opl_attempt_admission_status": "not_requested",
        "dispatch": {
            "action_type": action_type,
            "study_id": study_id,
            "recommended_domain_command": _recommended_command(action_type, profile_ref=profile_ref, study_id=study_id),
            "execution_policy": "guarded_domain_control_receipt_only",
        },
        "authority_boundary": authority_boundary_payload(),
        "forbidden_write_guard_proof": opl_provider_ready_adapter.build_forbidden_write_guard_proof(
            result="accepted_no_forbidden_writes",
            task_id=task_id,
            task_kind=task_kind,
            requested_writes=(),
        ),
    }
    if source_fingerprint is not None:
        receipt["source_fingerprint"] = source_fingerprint
    return receipt


def _apply_dispatch_action(
    *,
    receipt: dict[str, Any],
    action_type: str,
    profile: WorkspaceProfile | None,
    profile_ref: Path | None,
    study_id: str | None,
    task: Mapping[str, Any],
) -> dict[str, Any]:
    if action_type == "domain_route_owner_handoff":
        return _with_domain_route_owner_handoff(receipt=receipt, task=task, study_id=study_id)
    if action_type == "paper_repair_executor_dispatch":
        return _with_paper_repair(receipt=receipt, profile=profile, study_id=study_id, task=task)
    if action_type == "ai_reviewer_recheck_execute_dispatch":
        return _with_ai_reviewer_recheck(receipt=receipt, profile=profile, study_id=study_id, task=task)
    if action_type == "paper_autonomy_guarded_apply":
        return _with_guarded_apply(
            receipt=receipt,
            profile_ref=profile_ref,
            study_id=study_id,
            task=task,
        )
    if action_type == "default_executor_dispatch_request":
        payload = _mapping(task.get("payload"))
        transition_request = _mapping(payload.get("opl_domain_progress_transition_request"))
        if transition_request:
            receipt["opl_attempt_admission_requested"] = False
            receipt["opl_attempt_admission_status"] = "not_requested"
            receipt["opl_domain_progress_transition_runtime_intake_requested"] = True
            receipt["opl_domain_progress_transition_runtime_intake_status"] = "requested"
            receipt["dispatch"]["execution_policy"] = (
                "opl_domain_progress_transition_runtime_intake_required"
            )
            receipt["dispatch"]["result"] = {
                "surface": "default_executor_transition_request_intake",
                "status": "opl_domain_progress_transition_runtime_intake_requested",
                "study_id": study_id,
                "next_owner": _text(payload.get("next_executable_owner")) or "write",
                "dispatch_ref": _text(payload.get("dispatch_ref")),
                "authority_boundary": "mas_domain_progress_transition_request_only",
                "provider_admission_requires_opl_runtime_result": True,
                "mas_can_authorize_provider_admission": False,
                "mas_can_create_opl_event": False,
                "mas_can_create_opl_outbox_record": False,
                "mas_can_create_opl_stage_run": False,
                "opl_domain_progress_transition_request": transition_request,
            }
            return receipt
        receipt["opl_attempt_admission_requested"] = False
        receipt["opl_attempt_admission_status"] = "not_requested"
        receipt["dispatch"]["result"] = {
            "surface": "default_executor_dispatch_request_blocker",
            "status": "opl_domain_progress_transition_request_required",
            "study_id": study_id,
            "next_owner": _text(payload.get("next_executable_owner")) or "write",
            "dispatch_ref": _text(payload.get("dispatch_ref")),
            "authority_boundary": "mas_default_executor_dispatch_request_only",
            "provider_admission_requires_opl_runtime_result": True,
            "mas_can_authorize_provider_admission": False,
        }
        return receipt
    return receipt


def _with_domain_route_owner_handoff(
    *,
    receipt: dict[str, Any],
    task: Mapping[str, Any],
    study_id: str | None,
) -> dict[str, Any]:
    payload = _mapping(task.get("payload"))
    receipt["opl_attempt_admission_requested"] = True
    receipt["opl_attempt_admission_status"] = "requested"
    receipt["dispatch"]["execution_policy"] = "opl_route_hydration_stage_attempt_admission"
    receipt["dispatch"]["result"] = {
        "surface": "domain_route_owner_handoff_admission",
        "status": "opl_attempt_admission_requested",
        "study_id": study_id,
        "route_target": _text(payload.get("route_target")),
        "continuation_reason": _text(payload.get("continuation_reason")),
        "owner_route_handoff_ref": _text(payload.get("owner_route_handoff_ref")),
        "controller_decision_ref": _text(payload.get("controller_decision_ref")),
        "work_unit_fingerprint": _text(payload.get("work_unit_fingerprint")),
        "authority_boundary": "mas_domain_route_refs_only_opl_stage_attempt_owner",
        "mas_executes_reconcile_apply": False,
        "provider_completion_is_domain_completion": False,
    }
    return receipt


def _with_paper_repair(
    *,
    receipt: dict[str, Any],
    profile: WorkspaceProfile | None,
    study_id: str | None,
    task: Mapping[str, Any],
) -> dict[str, Any]:
    result = _execute_paper_repair(profile=profile, study_id=study_id, task=task)
    if _mapping(result).get("execution_status") == "handoff_ready":
        receipt["opl_attempt_admission_requested"] = True
        receipt["opl_attempt_admission_status"] = "requested"
    receipt["dispatch"]["execution_policy"] = "mas_owner_paper_repair_execute"
    receipt["dispatch"]["result"] = result
    if _mapping(result).get("execution_status") == "handoff_ready":
        receipt["dispatch"]["downstream_worker_handoff"] = _mapping(result).get(
            "writer_worker_handoff"
        ) or _mapping(result).get("ai_reviewer_record_worker_handoff")
    if _mapping(result).get("accepted") is False:
        typed_blocker = _text(_mapping(result).get("typed_blocker")) or "paper_repair_executor_blocked"
        if typed_blocker in STABLE_PAPER_REPAIR_TYPED_BLOCKERS:
            receipt["accepted"] = True
            receipt["stable_typed_blocker"] = typed_blocker
        else:
            receipt["accepted"] = False
            receipt["reason"] = typed_blocker
    return receipt


def _with_ai_reviewer_recheck(
    *,
    receipt: dict[str, Any],
    profile: WorkspaceProfile | None,
    study_id: str | None,
    task: Mapping[str, Any],
) -> dict[str, Any]:
    result = _execute_ai_reviewer_recheck(profile=profile, study_id=study_id, task=task)
    if _mapping(result).get("accepted") is False:
        receipt["accepted"] = True
        receipt["stable_typed_blocker"] = _text(_mapping(result).get("typed_blocker")) or "opl_execution_authorization_required"
        receipt["dispatch"]["execution_policy"] = "opl_attempt_lease_or_receipt_required"
    else:
        receipt["dispatch"]["execution_policy"] = "mas_owner_ai_reviewer_execute_dispatch"
    receipt["dispatch"]["result"] = result
    return receipt


def _with_guarded_apply(
    *,
    receipt: dict[str, Any],
    profile_ref: Path | None,
    study_id: str | None,
    task: Mapping[str, Any],
) -> dict[str, Any]:
    current_owner_delta = _current_owner_delta_from_task(task)
    result = _execute_guarded_apply(
        profile_ref=profile_ref,
        study_id=study_id,
        task_id=str(receipt.get("task_id") or "unknown_task"),
        task=task,
    )
    receipt["dispatch"]["execution_policy"] = "mas_owner_provider_hosted_guarded_apply"
    binding = guarded_apply_current_owner_delta_binding_summary(current_owner_delta)
    receipt["dispatch"]["current_owner_delta"] = current_owner_delta or None
    receipt["current_owner_delta"] = current_owner_delta or None
    receipt["dispatch"]["result_current_owner_delta_binding"] = binding
    receipt["dispatch"]["result"] = result
    return receipt


def _write_dispatch_receipt(
    *,
    receipt: dict[str, Any],
    profile: WorkspaceProfile | None,
    task_id: str,
    source_fingerprint: str | None = None,
    owner_capability_fingerprint: str | None = None,
) -> dict[str, Any]:
    return write_dispatch_receipt(
        receipt=receipt,
        profile=profile,
        task_id=task_id,
        source_fingerprint=source_fingerprint,
        owner_capability_fingerprint=owner_capability_fingerprint,
        read_json_object=_read_json_object,
        write_json=_write_json,
        workspace_relative=lambda path: _workspace_relative(path, workspace_root=profile.workspace_root)
        if profile is not None
        else str(path),
        text=_text,
        mapping=_mapping,
        now_iso=_now_iso,
        authority_boundary_payload=authority_boundary_payload,
        forbidden_write_guard_proof=opl_provider_ready_adapter.build_forbidden_write_guard_proof,
    )


def dispatch_family_domain_handler_task(*, task_path: Path) -> dict[str, Any]:
    generated_at = _now_iso()
    try:
        task = _load_task(task_path)
    except ValueError as exc:
        return _dispatch_error(generated_at=generated_at, reason="invalid_task", detail=str(exc))
    task_id = _text(task.get("task_id")) or "unknown_task"
    domain_id = _text(task.get("domain_id")) or "medautoscience"
    task_kind = _text(task.get("task_kind")) or "unknown"
    if domain_id != "medautoscience":
        return _dispatch_error(
            generated_at=generated_at,
            task_id=task_id,
            reason="wrong_domain",
            detail=f"MAS domain handler cannot dispatch domain {domain_id}",
        )
    if _forbidden_write_requested(task):
        forbidden_requested_writes = _forbidden_requested_writes(task)
        return _dispatch_error(
            generated_at=generated_at,
            task_id=task_id,
            task_kind=task_kind,
            reason="domain_truth_or_artifact_gate_write_forbidden",
            forbidden_domain_truth_write=True,
            requested_writes=opl_provider_ready_adapter.requested_writes_from_task(task),
            forbidden_requested_writes=forbidden_requested_writes,
        )
    action_type = ALLOWED_TASK_KINDS.get(task_kind)
    if action_type is None:
        return _dispatch_error(
            generated_at=generated_at,
            task_id=task_id,
            task_kind=task_kind,
            reason="unsupported_task_kind",
            detail=f"Unsupported MAS domain-handler task kind: {task_kind}",
        )
    profile, profile_ref = _profile_from_task(task)
    payload = _mapping(task.get("payload"))
    study_id = _text(payload.get("study_id"))
    source_fingerprint = _text(task.get("source_fingerprint"))
    owner_capability_fingerprint = _owner_capability_fingerprint(action_type=action_type)
    receipt = _base_dispatch_receipt(
        generated_at=generated_at,
        task_id=task_id,
        task_kind=task_kind,
        task_path=task_path,
        action_type=action_type,
        profile_ref=profile_ref,
        study_id=study_id,
        source_fingerprint=source_fingerprint,
    )
    receipt = _apply_dispatch_action(
        receipt=receipt,
        action_type=action_type,
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        task=task,
    )
    return _write_dispatch_receipt(
        receipt=receipt,
        profile=profile,
        task_id=task_id,
        source_fingerprint=source_fingerprint,
        owner_capability_fingerprint=owner_capability_fingerprint,
    )


def _dispatch_error(
    *,
    generated_at: str,
    reason: str,
    task_id: str | None = None,
    task_kind: str | None = None,
    detail: str | None = None,
    forbidden_domain_truth_write: bool = False,
    requested_writes: list[str] | None = None,
    forbidden_requested_writes: list[str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "surface_kind": "mas_family_domain_handler_dispatch_receipt",
        "version": "mas-family-domain-handler.v1",
        "accepted": False,
        "generated_at": generated_at,
        "reason": reason,
        "forbidden_domain_truth_write": forbidden_domain_truth_write,
        "authority_boundary": authority_boundary_payload(),
        "forbidden_write_guard_proof": opl_provider_ready_adapter.build_forbidden_write_guard_proof(
            result="blocked" if forbidden_domain_truth_write else "not_evaluated",
            task_id=task_id,
            task_kind=task_kind,
            requested_writes=requested_writes or forbidden_requested_writes or (),
        ),
    }
    if forbidden_requested_writes is not None:
        payload["forbidden_requested_writes"] = forbidden_requested_writes
    if task_id is not None:
        payload["task_id"] = task_id
    if task_kind is not None:
        payload["task_kind"] = task_kind
    if detail is not None:
        payload["detail"] = detail
    return payload


__all__ = ["ALLOWED_TASK_KINDS", "dispatch_family_domain_handler_task"]
