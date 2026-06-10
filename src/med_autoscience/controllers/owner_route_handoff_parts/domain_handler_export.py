from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.ars_learning_projection import build_ars_learning_projection
from med_autoscience.autosci_learning_projection import build_autosci_learning_projection
from med_autoscience.evo_scientist_learning_projection import (
    build_evo_scientist_learning_projection,
)
from med_autoscience.external_learning_adoption_closure import (
    build_external_learning_adoption_closure,
)
from med_autoscience.profiles import WorkspaceProfile

from .. import opl_provider_ready_adapter
from .. import publication_aftercare
from ..study_domain_transition_table_parts import family_transition_spec
from .authority_boundary import authority_boundary_payload
from .controller_route_back_tasks import controller_decision_route_back_task
from .default_executor_dispatch_tasks import default_executor_dispatch_tasks
from med_autoscience.controllers.domain_dispatch_evidence_payload import (
    build_domain_dispatch_evidence_record_payload,
)
from .domain_handler_functional_closure import build_domain_handler_functional_closure_projection
from .export_study_projection import (
    build_study_projection,
    mapping,
    study_roots,
    text,
    workspace_relative,
)
from .guarded_apply_tasks import DEFAULT_GUARDED_APPLY_TARGETS, provider_hosted_guarded_apply_tasks
from .owner_route_handoff_tasks import owner_route_handoff_task
from .owner_source_refs import owner_controller_decision_refs
from .substrate_adapter import build_opl_substrate_adapter_projection
from .task_kinds import ALLOWED_TASK_KINDS


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def export_family_domain_handler(
    *,
    profile: WorkspaceProfile,
    profile_ref: Path,
    opl_production_proof_ref: str | Path | None = None,
) -> dict[str, Any]:
    studies = [build_study_projection(study_root=study_root, profile=profile) for study_root in study_roots(profile)]
    generated_at = _now_iso()
    opl_production_proof = opl_provider_ready_adapter.load_opl_production_proof(opl_production_proof_ref)
    provider_availability = opl_provider_ready_adapter.build_provider_availability_from_opl_proof(
        opl_production_proof=opl_production_proof,
        proof_ref=opl_production_proof_ref,
    )
    functional_closure = build_domain_handler_functional_closure_projection(
        profile=profile,
        profile_ref=profile_ref,
        allowed_task_kinds=ALLOWED_TASK_KINDS,
        opl_production_proof=opl_production_proof,
        opl_production_proof_ref=opl_production_proof_ref,
    )
    pending_tasks = _pending_family_tasks(
        studies=studies,
        profile=profile,
        profile_ref=profile_ref,
        provider_availability=provider_availability,
        opl_production_proof_ref=opl_production_proof_ref,
    )
    return {
        "surface_kind": "mas_family_domain_handler_export",
        "version": "mas-family-domain-handler.v1",
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
            "executor_adapter_requirement": {
                "owner": "one-person-lab",
                "generic_executor_adapter_owner": "one-person-lab",
                "default_executor_kind": "codex_cli_default",
                "required_capability": "opl_executor_adapter_receipt",
                "mas_accepts": "typed_closeout_or_domain_task_receipt",
                "mas_local_codex_cli_scope": "standalone_diagnostics_only",
                "external_executor_opt_in_policy": "explicit_opl_opt_in_then_typed_receipt_only",
                "mas_owned_hermes_or_claude_executor": False,
                "mas_does_not_provide": [
                    "hosted_executor",
                    "hermes_executor_adapter",
                    "claude_executor_adapter",
                ],
            },
            "optional_executor_adapters": [
                {
                    "adapter_id": "hermes_agent",
                    "display_name": "Hermes-Agent",
                    "classification": "explicit_optional_executor_adapter",
                    "runtime_policy": "explicit_opl_opt_in_then_typed_receipt_only",
                    "executor_policy": "not_a_mas_executor_adapter",
                    "default_provider": False,
                }
            ],
            "role": "stage_attempt_queue_wakeup_retry_dead_letter_human_gate_receipt_projection_transport",
            "not_authority_for": ["study_truth", "publication_quality", "artifact_gate", "paper_package"],
        },
        "dispatch": {
            "entrypoint": "medautosci domain-handler dispatch --task <task.json> --format json",
            "allowed_task_kinds": sorted(ALLOWED_TASK_KINDS),
            "receipt_policy": "MAS writes a domain control receipt only; paper, publication, and package truth remain untouched.",
            "receipt_refs": opl_provider_ready_adapter.receipt_refs_for_profile(profile),
        },
        "authority_boundary": authority_boundary_payload(),
        "opl_substrate_adapter": build_opl_substrate_adapter_projection(
            profile=profile,
            studies=studies,
            authority_boundary_payload=authority_boundary_payload,
            workspace_relative=lambda path: workspace_relative(path, workspace_root=profile.workspace_root),
            text=text,
            mapping=mapping,
        ),
        "functional_consumer_boundary": functional_closure["functional_consumer_boundary"],
        "ars_learning_projection": build_ars_learning_projection(),
        "autosci_learning_projection": build_autosci_learning_projection(),
        "evo_scientist_learning_projection": build_evo_scientist_learning_projection(),
        "external_learning_adoption_closure": build_external_learning_adoption_closure(),
        "family_transition_spec_descriptor": (
            family_transition_spec.build_family_transition_spec_descriptor()
        ),
        "provider_ready_adapter": functional_closure["provider_ready_contract"],
        "managed_temporal_state_consistency": (
            opl_provider_ready_adapter.build_managed_temporal_state_consistency_read_model(
                provider_availability=provider_availability,
            )
        ),
        "owner_receipt_contract": opl_provider_ready_adapter.build_owner_receipt_contract_surface(
            provider_availability=provider_availability,
        ),
        "domain_owner_receipt_contract": opl_provider_ready_adapter.build_owner_receipt_contract_surface(
            provider_availability=provider_availability,
        ),
        "lifecycle_apply_requests": opl_provider_ready_adapter.build_lifecycle_apply_requests_surface(),
        "lifecycle_guarded_apply_proof": (
            opl_provider_ready_adapter.build_lifecycle_guarded_apply_proof_surface()
        ),
        "opl_unique_control_plane_handoff": (
            functional_closure["provider_ready_contract"]["opl_unique_control_plane_handoff"]
        ),
        "workspace_runtime_evidence_receipt": functional_closure["workspace_runtime_evidence_receipt"],
        "standard_domain_agent_skeleton": functional_closure["standard_domain_agent_skeleton"],
        "mas_functional_closure_status_projection": (
            functional_closure["functional_closure_status_projection"]
        ),
        "family_opl_current_control_state_handoff": {
            "surface_kind": "family_opl_current_control_state_handoff",
            "version": "family-opl-current-control-state-handoff.v1",
            "target_domain_id": "medautoscience",
            "handoff_id": f"{profile.name}_mas_family_opl_current_control_state_handoff",
            "adapter_id": "opl_family_runtime_provider_wakeup_to_mas_domain_handler",
            "cadence": {"interval_seconds": 60},
            "current_control_state_freshness": {"state": "unknown", "observed_at": generated_at, "max_age_seconds": 180},
            "slo_state": {
                "state": _aggregate_slo_state(studies),
                "summary": "MAS exposes SLO state as read-only projection for OPL family-runtime indexing.",
            },
            "repair_command": f"medautosci owner-route-reconcile --profile {profile_ref} --developer-supervisor-mode developer_apply_safe",
            "safe_reconcile_hint": (
                "Use OPL provider/runtime manager wakeup plus medautosci domain-handler dispatch; "
                "MAS default surfaces stay in standard OPL Agent shape."
            ),
            "standard_agent_purity": functional_closure["functional_consumer_boundary"][
                "standard_agent_purity"
            ],
            "domain_owned_source_refs": _aggregate_domain_refs(studies),
            "read_only_authority_boundary": {
                "projection_owner": "one-person-lab",
                "domain_owner": "med-autoscience",
                "runtime_owner": "one-person-lab",
                "scheduler_owner": "one-person-lab",
                "authority": "read_only_projection",
                "forbidden_authorities": authority_boundary_payload()["forbidden_authorities"],
            },
        },
        "pending_family_tasks": pending_tasks,
        "studies": studies,
    }


def _pending_family_tasks(
    *,
    studies: list[Mapping[str, Any]],
    profile: WorkspaceProfile,
    profile_ref: Path,
    provider_availability: Mapping[str, Any],
    opl_production_proof_ref: str | Path | None,
) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    guarded_apply_targets = _guarded_apply_targets(studies)
    tasks.extend(
        provider_hosted_guarded_apply_tasks(
            profile=profile,
            profile_ref=profile_ref,
            provider_availability=provider_availability,
            opl_production_proof_ref=opl_production_proof_ref,
            owner_source_refs_by_target={
                target: owner_controller_decision_refs(
                    profile=profile,
                    target_study_id=target,
                )
                for target in guarded_apply_targets
            },
            target_studies=guarded_apply_targets,
        )
    )
    for study in studies:
        study_id = text(study.get("study_id"))
        if study_id is None:
            continue
        current_progress = _fresh_study_progress(
            study=study,
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
        )
        ordinary_task_blocker = _ordinary_pending_tasks_blocker(current_progress=current_progress)
        if ordinary_task_blocker:
            continue
        tasks.extend(
            _paper_autonomy_tasks(
                study=study,
                profile=profile,
                profile_ref=profile_ref,
                study_id=study_id,
            )
        )
        tasks.extend(
            default_executor_dispatch_tasks(
                profile=profile,
                profile_ref=profile_ref,
                study_id=study_id,
                current_owner_action=_export_current_owner_action(
                    study=study,
                    current_progress=current_progress,
                ),
                current_work_unit=mapping(current_progress.get("current_work_unit")),
                current_execution_envelope=_export_current_execution_envelope(
                    study=study,
                    current_progress=current_progress,
                ),
            )
        )
        tasks.extend(
            publication_aftercare.build_publication_aftercare_pending_tasks(
                profile_name=profile.name,
                profile_ref=profile_ref,
                study_id=study_id,
                projection=mapping(study.get("publication_aftercare")),
            )
        )
        handoff_task = owner_route_handoff_task(
            study=study,
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
        )
        if handoff_task is not None:
            tasks.append(handoff_task)
        continuation_task = _autonomy_progress_pressure_task(
            study=study,
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
        )
        if continuation_task is not None:
            tasks.append(continuation_task)
        controller_task = controller_decision_route_back_task(
            study=study,
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
        )
        if controller_task is not None:
            tasks.append(controller_task)
    return tasks


def _ordinary_pending_tasks_blocker(*, current_progress: Mapping[str, Any]) -> Mapping[str, Any]:
    current_work_unit = mapping(current_progress.get("current_work_unit"))
    work_unit_status = text(current_work_unit.get("status"))
    if _ordinary_pending_tasks_blocked_status(work_unit_status):
        return {
            "blocked": True,
            "source": "current_work_unit",
            "state_kind": work_unit_status,
        }
    current_execution_envelope = mapping(current_progress.get("current_execution_envelope"))
    envelope_state = text(current_execution_envelope.get("state_kind")) or text(
        current_execution_envelope.get("execution_state_kind")
    )
    if _ordinary_pending_tasks_blocked_status(envelope_state):
        return {
            "blocked": True,
            "source": "current_execution_envelope",
            "state_kind": envelope_state,
        }
    return {}


def _ordinary_pending_tasks_blocked_status(status: str | None) -> bool:
    return status in {
        "typed_blocker",
        "running_provider_attempt",
        "blocked_current_work_unit",
        "blocked_typed_owner",
        "parked",
    }


def _fresh_study_progress(
    *,
    study: Mapping[str, Any],
    profile: WorkspaceProfile,
    profile_ref: Path,
    study_id: str,
) -> Mapping[str, Any]:
    try:
        from med_autoscience.controllers import study_progress
    except ImportError:
        return {}
    study_root = Path(text(study.get("study_root")) or profile.studies_root / study_id)
    try:
        return study_progress.read_study_progress(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            study_root=study_root,
            sync_runtime_summary=False,
            materialize_read_model_artifacts=False,
        )
    except (FileNotFoundError, OSError, ValueError, TypeError, RuntimeError):
        return {}


def _export_current_owner_action(
    *,
    study: Mapping[str, Any],
    current_progress: Mapping[str, Any],
) -> Mapping[str, Any]:
    progress_action = mapping(current_progress.get("current_executable_owner_action"))
    if progress_action:
        projection_action = mapping(study.get("current_owner_action"))
        if text(progress_action.get("action_type")) == text(projection_action.get("action_type")):
            return _merge_projection_owner_action_identity(
                progress_action=progress_action,
                projection_action=projection_action,
            )
        return progress_action
    projection_action = mapping(study.get("current_owner_action"))
    if text(projection_action.get("source")) == "opl_current_control_state_action_queue":
        return {}
    return projection_action


def _export_current_execution_envelope(
    *,
    study: Mapping[str, Any],
    current_progress: Mapping[str, Any],
) -> Mapping[str, Any]:
    progress_envelope = mapping(current_progress.get("current_execution_envelope"))
    if progress_envelope:
        return progress_envelope
    projection_action = mapping(study.get("current_owner_action"))
    if text(projection_action.get("source")) != "opl_current_control_state_action_queue":
        return {}
    return {
        "state_kind": "blocked_current_work_unit",
        "owner": "med-autoscience",
        "next_work_unit": None,
        "typed_blocker": {
            "blocker_type": "canonical_current_work_unit_required",
            "owner": "med-autoscience",
            "source": "domain_handler_export.current_control_action_queue_guard",
        },
    }


def _merge_projection_owner_action_identity(
    *,
    progress_action: Mapping[str, Any],
    projection_action: Mapping[str, Any],
) -> Mapping[str, Any]:
    if not projection_action:
        return progress_action
    merged = dict(progress_action)
    for key in (
        "surface_key",
        "target_surface",
        "target_surface_specificity",
        "next_action",
        "source_ref",
    ):
        value = projection_action.get(key)
        if value is not None and merged.get(key) is None:
            merged[key] = value
    if text(projection_action.get("source")) != "opl_current_control_state_action_queue":
        merged["source"] = text(projection_action.get("source")) or text(merged.get("source"))
    return merged


def _autonomy_progress_pressure_task(
    *,
    study: Mapping[str, Any],
    profile: WorkspaceProfile,
    profile_ref: Path,
    study_id: str,
) -> dict[str, Any] | None:
    continuation = mapping(study.get("autonomy_continuation"))
    if continuation.get("eligible_for_auto_dispatch") is not True:
        return None
    if text(continuation.get("recommended_task_kind")) != "domain_route/reconcile-apply":
        return None
    progress_pressure = mapping(continuation.get("progress_pressure"))
    if text(progress_pressure.get("status")) != "advance_now":
        return None
    next_work_unit_id = text(progress_pressure.get("next_work_unit_id"))
    study_root = Path(text(study.get("study_root")) or profile.studies_root / study_id)
    slo_path = study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json"
    source_ref = workspace_relative(slo_path, workspace_root=profile.workspace_root)
    source_fingerprint = _fingerprint(
        {
            "profile": profile.name,
            "study_id": study_id,
            "progress_pressure": dict(progress_pressure),
            "slo_state": text(mapping(study.get("slo_status")).get("state")),
            "breach_types": list(mapping(study.get("slo_status")).get("breach_types") or []),
        }
    )
    source_refs = [
        {
            "role": "mas_autonomy_progress_pressure",
            "ref": source_ref,
            "exists": slo_path.exists(),
        }
    ]
    evidence_record_payload = build_domain_dispatch_evidence_record_payload(
        task_kind="domain_route/reconcile-apply",
        study_id=study_id,
        reason="progress_pressure_continue",
        evidence_refs=source_refs,
        source_fingerprint=source_fingerprint,
        profile_name=profile.name,
    )
    return {
        "domain_id": "medautoscience",
        "task_kind": "domain_route/reconcile-apply",
        "recommended_task_kind": "domain_route/reconcile-apply",
        "priority": 65,
        "source": "mas-autonomy-progress-pressure",
        "requires_approval": False,
        "dedupe_key": f"mas:{profile.name}:{study_id}:progress-pressure:{source_fingerprint}",
        "source_fingerprint": source_fingerprint,
        "domain_truth_owner": "med-autoscience",
        "queue_owner": "one-person-lab",
        "reason": "progress_pressure_continue",
        "source_refs": source_refs,
        "dispatch_owner": "med-autoscience",
        "profile_name": profile.name,
        "domain_dispatch_evidence_record_payload": evidence_record_payload,
        "payload": {
            "profile": str(profile_ref),
            "study_id": study_id,
            "source_fingerprint": source_fingerprint,
            "continuation_reason": "progress_pressure_continue",
            "progress_pressure": dict(progress_pressure),
            "next_work_unit": (
                {
                    "unit_id": next_work_unit_id,
                    "source": "autonomy_progress_slo_status.progress_pressure",
                }
                if next_work_unit_id is not None
                else None
            ),
            "slo_status_ref": source_ref,
            "authority_boundary": "mas_owner_route_refs_only_opl_stage_attempt_owner",
        },
    }


def _guarded_apply_targets(studies: list[Mapping[str, Any]]) -> tuple[str, ...]:
    live_study_ids_by_target: dict[str, str] = {}
    for study in studies:
        study_id = text(study.get("study_id"))
        study_root = text(study.get("study_root"))
        if study_id is None or study_root is None:
            continue
        if not (Path(study_root) / "study.yaml").exists():
            continue
        normalized_study_id = _guarded_apply_target_key(study_id)
        for target in DEFAULT_GUARDED_APPLY_TARGETS:
            target_key = _guarded_apply_target_key(target)
            if normalized_study_id == target_key and target_key not in live_study_ids_by_target:
                live_study_ids_by_target[target_key] = study_id
    live_target_ids = tuple(
        live_study_ids_by_target[_guarded_apply_target_key(target)]
        for target in DEFAULT_GUARDED_APPLY_TARGETS
        if _guarded_apply_target_key(target) in live_study_ids_by_target
    )
    return live_target_ids or DEFAULT_GUARDED_APPLY_TARGETS


def _guarded_apply_target_key(value: str) -> str:
    normalized = value.strip().lower().replace("_", "-")
    aliases = {
        "dm002": "002",
        "dm-002": "002",
        "dm003": "003",
        "dm-003": "003",
        "obesity": "obesity",
    }
    if normalized in aliases:
        return aliases[normalized]
    if normalized.startswith("002-"):
        return "002"
    if normalized.startswith("003-"):
        return "003"
    if "obesity" in normalized:
        return "obesity"
    return normalized


def _paper_autonomy_tasks(
    *,
    study: Mapping[str, Any],
    profile: WorkspaceProfile,
    profile_ref: Path,
    study_id: str,
) -> list[dict[str, Any]]:
    loop = mapping(study.get("paper_autonomy_loop"))
    if loop.get("eligible_for_auto_dispatch") is not True:
        return []
    tasks: list[dict[str, Any]] = []
    for unit in loop.get("repair_work_units") or []:
        if not isinstance(unit, Mapping):
            continue
        unit_id = text(unit.get("unit_id"))
        idempotency_key = text(unit.get("idempotency_key"))
        if unit_id is None or idempotency_key is None:
            continue
        tasks.append(
            {
                "domain_id": "medautoscience",
                "task_kind": "paper_autonomy/repair-recheck",
                "priority": 40,
                "source": "mas-domain-handler-export",
                "requires_approval": False,
                "dedupe_key": idempotency_key,
                "payload": {
                    "profile": str(profile_ref),
                    "study_id": study_id,
                    "paper_autonomy_reason": text(loop.get("reason")) or "ai_reviewer_repair_recheck_required",
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
        text(mapping(study.get("slo_status")).get("state"))
        for study in studies
        if mapping(study.get("slo_status"))
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


def _fingerprint(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


__all__ = ["export_family_domain_handler"]
