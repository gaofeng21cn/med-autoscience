from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.profiles import WorkspaceProfile, load_profile

from . import reviewer_refinement_loop
from . import opl_provider_ready_adapter
from . import paper_repair_executor
from . import runtime_supervisor_dispatch_executor
from . import runtime_supervisor_reconcile
from . import stage_knowledge_plane


_FORBIDDEN_PAYLOAD_FLAGS = (
    "domain_truth_write",
    "artifact_gate_override",
    "study_truth_write",
    "publication_quality_verdict",
    "current_package_write",
    "memory_body_write",
    "publication_route_memory_writeback_accept",
    "memory_write_router_accept",
)
_STUDY_SOURCE_REFS: tuple[tuple[str, Path, str], ...] = (
    ("runtime_supervision_truth", Path("artifacts/runtime/runtime_supervision/latest.json"), "runtime_supervision"),
    ("runtime_supervision_truth_legacy_ref", Path("artifacts/runtime_supervision/latest.json"), "runtime_supervision"),
    ("autonomy_slo_status", Path("artifacts/autonomy/slo_status/latest.json"), "slo_status"),
    ("worker_lease", Path("artifacts/runtime/worker_lease/latest.json"), "worker_lease"),
    ("runtime_session", Path("artifacts/runtime/runtime_session/latest.json"), "runtime_session"),
    ("recovery_intent", Path("artifacts/runtime/recovery_intent/latest.json"), "recovery_intent"),
    ("safe_reconcile_dry_run", Path("artifacts/supervision/reconcile/latest.json"), "safe_reconcile"),
    ("controller_receipt", Path("artifacts/runtime/supervisor_dispatch_receipt/latest.json"), "controller_receipt"),
    ("controller_decisions", Path("artifacts/controller_decisions/latest.json"), "controller_decisions"),
    ("publication_eval", Path("artifacts/publication_eval/latest.json"), "publication_eval"),
    ("paper_work_unit_outbox_receipts", Path("artifacts/runtime/paper_work_unit_outbox/receipts.jsonl"), "paper_work_unit_receipts"),
)
_ALLOWED_TASK_KINDS = {
    "runtime_supervision/recover": "runtime_supervisor_recover",
    "runtime_supervisor/recover": "runtime_supervisor_recover",
    "runtime/recover": "runtime_supervisor_recover",
    "runtime_supervisor/reconcile-apply": "runtime_supervisor_reconcile_apply",
    "runtime/reconcile-apply": "runtime_supervisor_reconcile_apply",
    "autonomy/continue": "runtime_supervisor_reconcile_apply",
    "paper_autonomy/repair-recheck": "paper_repair_executor_dispatch",
    "paper_autonomy/ai-reviewer-recheck": "ai_reviewer_recheck_execute_dispatch",
    "paper_autonomy/gate-replay": "runtime_supervisor_reconcile_apply",
    "paper_autonomy/route-decision": "runtime_supervisor_reconcile_apply",
    "safe_reconcile/dry-run": "safe_reconcile_dry_run",
    "study_progress/read": "study_progress_read",
    "status/read": "status_read",
    "notification/receipt": "notification_receipt",
}
_AUTO_CONTINUATION_BLOCKING_DECISIONS = {"stop_loss", "terminal_stop", "completed"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return dict(payload) if isinstance(payload, dict) else None


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _workspace_relative(path: Path, *, workspace_root: Path) -> str:
    try:
        return str(path.relative_to(workspace_root))
    except ValueError:
        return str(path)


def _authority_boundary_payload() -> dict[str, Any]:
    return {
        "family_runtime_framework_owner": "one-person-lab",
        "online_runtime_provider_owner": "opl_family_runtime_provider",
        "typed_dispatch_owner": "one-person-lab",
        "domain_truth_owner": "med-autoscience",
        "quality_gate_owner": "med-autoscience",
        "artifact_authority_owner": "med-autoscience",
        "writes_domain_truth": False,
        "writes_artifact_gate": False,
        "forbidden_authorities": [
            "study_truth_write",
            "publication_quality_verdict",
            "artifact_gate_override",
            "current_package_write",
        ],
    }


def _source_ref(*, study_root: Path, role: str, relative_path: Path, workspace_root: Path) -> dict[str, Any]:
    path = study_root / relative_path
    return {
        "ref_kind": "repo_path",
        "role": role,
        "ref": _workspace_relative(path, workspace_root=workspace_root),
        "exists": path.exists(),
    }


def _study_projection(*, study_root: Path, profile: WorkspaceProfile) -> dict[str, Any]:
    source_refs = [
        _source_ref(
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
            payload[field_name] = _read_json_object(study_root / relative_path)
    payload["paper_autonomy_loop"] = _paper_autonomy_loop_projection(study_root=study_root)
    payload["memory_paper_soak_proof"] = _memory_paper_soak_proof_projection(
        study_root=study_root,
        profile=profile,
    )
    payload["autonomy_continuation"] = _autonomy_continuation_projection(
        study=payload,
        profile=profile,
    )
    return payload


def _study_roots(profile: WorkspaceProfile) -> list[Path]:
    if not profile.studies_root.is_dir():
        return []
    return sorted(path for path in profile.studies_root.iterdir() if path.is_dir())


def export_family_sidecar(*, profile: WorkspaceProfile, profile_ref: Path) -> dict[str, Any]:
    studies = [_study_projection(study_root=study_root, profile=profile) for study_root in _study_roots(profile)]
    pending_tasks = _pending_family_tasks(studies=studies, profile=profile, profile_ref=profile_ref)
    generated_at = _now_iso()
    return {
        "surface_kind": "mas_family_sidecar_export",
        "version": "mas-family-sidecar.v1",
        "target_domain_id": "medautoscience",
        "generated_at": generated_at,
        "profile": {
            "profile_name": profile.name,
            "profile_ref": str(profile_ref),
            "hermes_profile_configured": bool(profile.hermes_agent_repo_root or profile.hermes_home_root),
            "hermes_home_root": str(profile.hermes_home_root),
        },
        "workspace": {
            "workspace_root": str(profile.workspace_root),
            "runtime_root": str(profile.runtime_root),
            "studies_root": str(profile.studies_root),
            "workspace_exists": profile.workspace_root.exists(),
            "studies_root_exists": profile.studies_root.exists(),
        },
        "online_runtime_framework": {
            "owner": "one-person-lab",
            "framework_role": "codex_first_stage_led_provider_backed_runtime_framework",
            "stage_semantics": "human_expert_large_task_stage",
            "minimal_executor": "Codex CLI",
            "provider_abstraction": "opl_family_runtime_provider",
            "target_production_provider": "Temporal",
            "legacy_optional_providers": ["Hermes-Agent"],
            "role": "stage_attempt_queue_wakeup_retry_dead_letter_human_gate_receipt_projection_transport",
            "not_authority_for": ["study_truth", "publication_quality", "artifact_gate", "paper_package"],
        },
        "dispatch": {
            "entrypoint": "medautosci sidecar dispatch --task <task.json> --format json",
            "allowed_task_kinds": sorted(_ALLOWED_TASK_KINDS),
            "receipt_policy": "MAS writes a domain control receipt only; paper, publication, and package truth remain untouched.",
            "receipt_refs": opl_provider_ready_adapter.receipt_refs_for_profile(profile),
        },
        "authority_boundary": _authority_boundary_payload(),
        "provider_ready_adapter": opl_provider_ready_adapter.build_opl_provider_ready_contract(
            profile=profile,
            profile_ref=profile_ref,
            allowed_task_kinds=_ALLOWED_TASK_KINDS,
        ),
        "family_runtime_supervision": {
            "surface_kind": "family_runtime_supervision",
            "version": "family-runtime-supervision.v1",
            "target_domain_id": "medautoscience",
            "supervision_id": f"{profile.name}_mas_family_runtime_supervision",
            "adapter_id": "opl_family_runtime_provider_wakeup_to_mas_sidecar",
            "cadence": {"interval_seconds": 60},
            "lease_freshness": {"state": "unknown", "observed_at": generated_at, "max_age_seconds": 180},
            "slo_state": {
                "state": _aggregate_slo_state(studies),
                "summary": "MAS exposes SLO state as read-only projection for OPL family-runtime indexing.",
            },
            "repair_command": f"medautosci runtime ensure-supervision --profile {profile_ref}",
            "safe_reconcile_hint": "Use medautosci sidecar dispatch; OPL providers must not write study or publication truth.",
            "domain_owned_source_refs": _aggregate_domain_refs(studies),
            "read_only_authority_boundary": {
                "projection_owner": "one-person-lab",
                "runtime_owner": "med-autoscience",
                "scheduler_owner": "med-autoscience",
                "authority": "read_only_projection",
                "forbidden_authorities": _authority_boundary_payload()["forbidden_authorities"],
            },
        },
        "pending_family_tasks": pending_tasks,
        "studies": studies,
    }


def _hard_human_gate_required(controller: Mapping[str, Any]) -> bool:
    if bool(controller.get("requires_human_confirmation")):
        return True
    gates = controller.get("family_human_gates")
    return isinstance(gates, list) and len(gates) > 0


def _terminal_controller_decision(controller: Mapping[str, Any]) -> bool:
    decision_type = _text(controller.get("decision_type"))
    route_target = _text(controller.get("route_target"))
    return decision_type in _AUTO_CONTINUATION_BLOCKING_DECISIONS or route_target == "stop"


def _continuation_reason(study: Mapping[str, Any]) -> str | None:
    slo = _mapping(study.get("slo_status"))
    runtime = _mapping(study.get("runtime_supervision"))
    recovery = _mapping(study.get("recovery_intent"))
    controller = _mapping(study.get("controller_decisions"))
    if _hard_human_gate_required(controller):
        return None
    if _terminal_controller_decision(controller):
        return None
    if _text(slo.get("state")) == "breach":
        return _text(slo.get("breach_reason")) or "slo_breach"
    if _text(runtime.get("runtime_decision")) == "blocked":
        return _text(runtime.get("runtime_reason")) or "runtime_blocked"
    if _text(runtime.get("runtime_liveness_status")) == "parked":
        return _text(runtime.get("runtime_reason")) or "runtime_parked"
    if _text(recovery.get("current_action")) == "safe_reconcile_ready":
        return "safe_reconcile_ready"
    return None


def _paper_autonomy_loop_projection(*, study_root: Path) -> dict[str, Any]:
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
    accept = _mapping(refinement.get("accept"))
    repair_loop = _mapping(refinement.get("repair_loop"))
    repair_plan = _mapping(repair_loop.get("repair_plan"))
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
        "accept_status": _text(accept.get("status")),
        "repair_plan": dict(repair_plan),
        "repair_work_units": work_units,
        "source_eval_id": _text(_mapping(refinement.get("snapshot")).get("source_eval_id")),
        "source_refs": [
            {"role": "publication_eval", "ref": str(publication_eval_path), "exists": True},
        ],
        "authority_boundary": _authority_boundary_payload(),
    }


def _memory_paper_soak_proof_projection(*, study_root: Path, profile: WorkspaceProfile) -> dict[str, Any]:
    proof_path = stage_knowledge_plane.paper_soak_memory_apply_proof_path(study_root=study_root)
    proof = _read_json_object(proof_path)
    if proof is None:
        return {
            "surface_kind": "mas_memory_paper_soak_proof_projection",
            "status": "missing",
            "proof_ref": _workspace_relative(proof_path, workspace_root=profile.workspace_root),
            "receipt_refs": [],
            "authority_boundary": _authority_boundary_payload(),
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
        "status": _text(proof.get("status")) or "missing",
        "proof_ref": _workspace_relative(proof_path, workspace_root=profile.workspace_root),
        "receipt_refs": receipt_refs,
        "route_memory_ref_count": len(_mapping(proof.get("stage_entry")).get("publication_route_memory_refs") or []),
        "router_receipt_ref_count": len(proof.get("mas_router_receipt_refs") or []),
        "writeback_proposal_ref_count": len(proof.get("typed_closeout_writeback_proposals") or []),
        "source_fingerprint": _text(proof.get("source_fingerprint")),
        "authority_boundary": _mapping(proof.get("authority_boundary")) or _authority_boundary_payload(),
        "read_only_display_policy": _mapping(proof.get("read_only_display_policy")),
    }


def _autonomy_continuation_projection(*, study: Mapping[str, Any], profile: WorkspaceProfile) -> dict[str, Any]:
    controller = _mapping(study.get("controller_decisions"))
    reason = _continuation_reason(study)
    return {
        "surface_kind": "mas_autonomy_continuation_projection",
        "eligible_for_auto_dispatch": reason is not None,
        "blocked_by_human_gate": _hard_human_gate_required(controller),
        "blocked_by_terminal_decision": _terminal_controller_decision(controller),
        "reason": reason,
        "recommended_task_kind": "runtime_supervisor/reconcile-apply" if reason is not None else None,
        "recommended_domain_owner": "med-autoscience" if reason is not None else None,
        "workspace_profile": profile.name,
    }


def _pending_family_tasks(
    *,
    studies: list[Mapping[str, Any]],
    profile: WorkspaceProfile,
    profile_ref: Path,
) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for study in studies:
        study_id = _text(study.get("study_id"))
        if study_id is None:
            continue
        tasks.extend(
            _paper_autonomy_tasks(
                study=study,
                profile=profile,
                profile_ref=profile_ref,
                study_id=study_id,
            )
        )
        continuation = _mapping(study.get("autonomy_continuation"))
        if not continuation.get("eligible_for_auto_dispatch"):
            continue
        reason = _text(continuation.get("reason")) or "autonomy_continuation"
        task_kind = _text(continuation.get("recommended_task_kind")) or "runtime_supervisor/reconcile-apply"
        tasks.append(
            {
                "domain_id": "medautoscience",
                "task_kind": task_kind,
                "priority": 50,
                "source": "mas-sidecar-export",
                "requires_approval": False,
                "dedupe_key": f"mas:{profile.name}:{study_id}:autonomy-continuation:{reason}",
                "payload": {
                    "profile": str(profile_ref),
                    "study_id": study_id,
                    "continuation_reason": reason,
                    "authority_boundary": "mas_owner_reconcile_only",
                },
            }
        )
    return tasks


def _paper_autonomy_tasks(
    *,
    study: Mapping[str, Any],
    profile: WorkspaceProfile,
    profile_ref: Path,
    study_id: str,
) -> list[dict[str, Any]]:
    loop = _mapping(study.get("paper_autonomy_loop"))
    if loop.get("eligible_for_auto_dispatch") is not True:
        return []
    tasks: list[dict[str, Any]] = []
    for unit in loop.get("repair_work_units") or []:
        if not isinstance(unit, Mapping):
            continue
        unit_id = _text(unit.get("unit_id"))
        idempotency_key = _text(unit.get("idempotency_key"))
        if unit_id is None or idempotency_key is None:
            continue
        tasks.append(
            {
                "domain_id": "medautoscience",
                "task_kind": "paper_autonomy/repair-recheck",
                "priority": 40,
                "source": "mas-sidecar-export",
                "requires_approval": False,
                "dedupe_key": idempotency_key,
                "payload": {
                    "profile": str(profile_ref),
                    "study_id": study_id,
                    "paper_autonomy_reason": _text(loop.get("reason")) or "ai_reviewer_repair_recheck_required",
                    "repair_work_unit": dict(unit),
                    "authority_boundary": "mas_owner_reconcile_only",
                },
                "source_refs": list(unit.get("source_refs") or []),
                "dispatch_owner": "med-autoscience",
                "profile_name": profile.name,
            }
        )
    return tasks


def _aggregate_slo_state(studies: list[Mapping[str, Any]]) -> str:
    states = {
        _text(_mapping(study.get("slo_status")).get("state"))
        for study in studies
        if _mapping(study.get("slo_status"))
    }
    if "breach" in states:
        return "breach"
    if "watch" in states:
        return "watch"
    if "met" in states:
        return "met"
    return "unknown"


def _aggregate_domain_refs(studies: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for study in studies:
        for ref in study.get("domain_owned_source_refs") or []:
            if isinstance(ref, dict) and ref.get("exists") is True:
                refs.append(ref)
    return refs[:50]


def _load_task(task_path: Path) -> dict[str, Any]:
    payload = _read_json_object(task_path)
    if payload is None:
        raise ValueError(f"sidecar task must be a JSON object: {task_path}")
    return payload


def _forbidden_write_requested(task: Mapping[str, Any]) -> bool:
    return bool(_forbidden_requested_writes(task))


def _forbidden_requested_writes(task: Mapping[str, Any]) -> list[str]:
    requested = opl_provider_ready_adapter.requested_writes_from_task(task)
    forbidden = {
        *_FORBIDDEN_PAYLOAD_FLAGS,
        "study_truth",
        "publication_eval",
        "controller_decisions",
        "current_package",
        "artifact_gate",
        "memory_body_write",
        "publication_route_memory_body",
        "publication_route_memory_writeback_accept",
        "memory_write_router_accept",
    }
    return [item for item in requested if item in forbidden]


def _profile_from_task(task: Mapping[str, Any]) -> tuple[WorkspaceProfile | None, Path | None]:
    payload = _mapping(task.get("payload"))
    profile_ref = _text(payload.get("profile") or payload.get("profile_path"))
    if profile_ref is None:
        return None, None
    path = Path(profile_ref).expanduser()
    return load_profile(path), path


def _receipt_path(*, profile: WorkspaceProfile, task_id: str) -> Path:
    digest = hashlib.sha256(task_id.encode("utf-8")).hexdigest()[:20]
    return profile.workspace_root / "artifacts" / "runtime" / "opl_family_sidecar" / "dispatch_receipts" / f"{digest}.json"


def _recommended_command(action_type: str, *, profile_ref: Path | None, study_id: str | None) -> str:
    profile_part = f" --profile {profile_ref}" if profile_ref is not None else " --profile <profile>"
    study_part = f" --studies {study_id}" if study_id else ""
    if action_type == "runtime_supervisor_recover":
        return f"uv run python -m med_autoscience.cli runtime-supervisor-scan{profile_part}{study_part}"
    if action_type == "safe_reconcile_dry_run":
        return f"uv run python -m med_autoscience.cli runtime-supervisor-reconcile{profile_part}{study_part} --mode developer_apply_safe --dry-run"
    if action_type == "runtime_supervisor_reconcile_apply":
        return f"uv run python -m med_autoscience.cli runtime-supervisor-reconcile{profile_part}{study_part} --mode developer_apply_safe --apply"
    if action_type == "study_progress_read":
        return f"uv run python -m med_autoscience.cli study-progress{profile_part}{study_part} --format json"
    return f"uv run python -m med_autoscience.cli product-entry-status{profile_part} --format json"


def _execute_reconcile_apply(
    *,
    profile: WorkspaceProfile | None,
    study_id: str | None,
) -> dict[str, Any] | None:
    if profile is None:
        return None
    return runtime_supervisor_reconcile.supervisor_reconcile(
        profile=profile,
        study_ids=(study_id,) if study_id else (),
        mode="developer_apply_safe",
        apply=True,
    )


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
    return paper_repair_executor.dispatch_repair_work_unit(
        study_id=study_id,
        quest_id=_text(payload.get("quest_id")) or _text(work_unit.get("quest_id")) or f"quest-{study_id}",
        study_root=profile.studies_root / study_id,
        repair_work_unit=work_unit,
        review_finding=_mapping(payload.get("review_finding")),
        apply=True,
    )


def _execute_ai_reviewer_recheck(
    *,
    profile: WorkspaceProfile | None,
    study_id: str | None,
) -> dict[str, Any] | None:
    if profile is None:
        return None
    return runtime_supervisor_dispatch_executor.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,) if study_id else (),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )


def _base_dispatch_receipt(
    *,
    generated_at: str,
    task_id: str,
    task_kind: str,
    task_path: Path,
    action_type: str,
    profile_ref: Path | None,
    study_id: str | None,
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_family_sidecar_dispatch_receipt",
        "version": "mas-family-sidecar.v1",
        "accepted": True,
        "task_id": task_id,
        "task_kind": task_kind,
        "generated_at": generated_at,
        "source_task_ref": str(task_path),
        "will_start_llm_worker": False,
        "dispatch": {
            "action_type": action_type,
            "study_id": study_id,
            "recommended_domain_command": _recommended_command(action_type, profile_ref=profile_ref, study_id=study_id),
            "execution_policy": "guarded_domain_control_receipt_only",
        },
        "authority_boundary": _authority_boundary_payload(),
        "forbidden_write_guard_proof": opl_provider_ready_adapter.build_forbidden_write_guard_proof(
            result="accepted_no_forbidden_writes",
            task_id=task_id,
            task_kind=task_kind,
            requested_writes=(),
        ),
    }


def _apply_dispatch_action(
    *,
    receipt: dict[str, Any],
    action_type: str,
    profile: WorkspaceProfile | None,
    study_id: str | None,
    task: Mapping[str, Any],
) -> dict[str, Any]:
    if action_type == "runtime_supervisor_reconcile_apply":
        return _with_reconcile_apply(receipt=receipt, profile=profile, study_id=study_id)
    if action_type == "paper_repair_executor_dispatch":
        return _with_paper_repair(receipt=receipt, profile=profile, study_id=study_id, task=task)
    if action_type == "ai_reviewer_recheck_execute_dispatch":
        return _with_ai_reviewer_recheck(receipt=receipt, profile=profile, study_id=study_id)
    return receipt


def _with_reconcile_apply(
    *,
    receipt: dict[str, Any],
    profile: WorkspaceProfile | None,
    study_id: str | None,
) -> dict[str, Any]:
    result = _execute_reconcile_apply(profile=profile, study_id=study_id)
    receipt["will_start_llm_worker"] = bool(_mapping(result).get("will_start_llm"))
    receipt["dispatch"]["execution_policy"] = "mas_owner_reconcile_apply"
    receipt["dispatch"]["result"] = result
    return receipt


def _with_paper_repair(
    *,
    receipt: dict[str, Any],
    profile: WorkspaceProfile | None,
    study_id: str | None,
    task: Mapping[str, Any],
) -> dict[str, Any]:
    result = _execute_paper_repair(profile=profile, study_id=study_id, task=task)
    receipt["will_start_llm_worker"] = False
    receipt["dispatch"]["execution_policy"] = "mas_owner_paper_repair_execute"
    receipt["dispatch"]["result"] = result
    if _mapping(result).get("accepted") is False:
        receipt["accepted"] = False
        receipt["reason"] = _text(_mapping(result).get("typed_blocker")) or "paper_repair_executor_blocked"
    return receipt


def _with_ai_reviewer_recheck(
    *,
    receipt: dict[str, Any],
    profile: WorkspaceProfile | None,
    study_id: str | None,
) -> dict[str, Any]:
    result = _execute_ai_reviewer_recheck(profile=profile, study_id=study_id)
    receipt["will_start_llm_worker"] = bool(_mapping(result).get("executed_count"))
    receipt["dispatch"]["execution_policy"] = "mas_owner_ai_reviewer_execute_dispatch"
    receipt["dispatch"]["result"] = result
    return receipt


def _write_dispatch_receipt(
    *,
    receipt: dict[str, Any],
    profile: WorkspaceProfile | None,
    task_id: str,
) -> dict[str, Any]:
    if profile is None:
        return receipt
    path = _receipt_path(profile=profile, task_id=task_id)
    if path.exists():
        existing = _read_json_object(path)
        if existing is not None:
            existing["idempotent_noop"] = True
            return existing
    receipt["receipt_ref"] = _workspace_relative(path, workspace_root=profile.workspace_root)
    _write_json(path, receipt)
    return receipt


def dispatch_family_sidecar_task(*, task_path: Path) -> dict[str, Any]:
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
            detail=f"MAS sidecar cannot dispatch domain {domain_id}",
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
    action_type = _ALLOWED_TASK_KINDS.get(task_kind)
    if action_type is None:
        return _dispatch_error(
            generated_at=generated_at,
            task_id=task_id,
            task_kind=task_kind,
            reason="unsupported_task_kind",
            detail=f"Unsupported MAS sidecar task kind: {task_kind}",
        )
    profile, profile_ref = _profile_from_task(task)
    study_id = _text(_mapping(task.get("payload")).get("study_id"))
    receipt = _base_dispatch_receipt(
        generated_at=generated_at,
        task_id=task_id,
        task_kind=task_kind,
        task_path=task_path,
        action_type=action_type,
        profile_ref=profile_ref,
        study_id=study_id,
    )
    receipt = _apply_dispatch_action(
        receipt=receipt,
        action_type=action_type,
        profile=profile,
        study_id=study_id,
        task=task,
    )
    return _write_dispatch_receipt(receipt=receipt, profile=profile, task_id=task_id)


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
        "surface_kind": "mas_family_sidecar_dispatch_receipt",
        "version": "mas-family-sidecar.v1",
        "accepted": False,
        "generated_at": generated_at,
        "reason": reason,
        "forbidden_domain_truth_write": forbidden_domain_truth_write,
        "authority_boundary": _authority_boundary_payload(),
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
