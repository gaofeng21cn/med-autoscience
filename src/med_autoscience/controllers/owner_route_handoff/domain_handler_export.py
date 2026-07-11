from __future__ import annotations

from datetime import datetime, timezone
import re
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
from med_autoscience.display_pack_agent import display_pack_capability_discover
from med_autoscience.domain_entry_contract import domain_entry_handler_target
from med_autoscience.paper_mission_domain import DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND
from med_autoscience.profiles import WorkspaceProfile

from .. import opl_provider_ready_adapter
from .. import publication_aftercare
from ..domain_handler_export.paper_mission_task_shaping import (
    mark_non_default_paper_mission_tasks as _mark_non_default_paper_mission_tasks,
    paper_mission_consumption_route_handoff_task as _paper_mission_consumption_route_handoff_task,
    paper_mission_start_or_resume_task as _paper_mission_start_or_resume_task,
)
from .. import opl_domain_progress_transition_contract
from ..study_domain_transition_table import family_transition_spec
from .authority_boundary import authority_boundary_payload
from .export_study_projection import (
    build_study_projection,
    mapping,
    study_roots,
    text,
    workspace_relative,
)
from .guarded_apply_tasks import DEFAULT_GUARDED_APPLY_TARGETS, provider_hosted_guarded_apply_tasks
from .owner_source_refs import owner_controller_decision_refs
from .substrate_adapter import build_opl_substrate_adapter_projection
from .task_kinds import ALLOWED_TASK_KINDS, RETIRED_DIAGNOSTIC_TASK_KINDS


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def export_family_domain_handler(
    *,
    profile: WorkspaceProfile,
    profile_ref: Path,
    opl_production_proof_ref: str | Path | None = None,
    study_ids: tuple[str, ...] = (),
    progress_by_study_id: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    requested_study_ids = {str(study_id).strip() for study_id in study_ids if str(study_id).strip()}
    studies = [
        build_study_projection(study_root=study_root, profile=profile)
        for study_root in study_roots(profile)
        if not requested_study_ids or study_root.name in requested_study_ids
    ]
    generated_at = _now_iso()
    opl_production_proof = opl_provider_ready_adapter.load_opl_production_proof(opl_production_proof_ref)
    provider_availability = opl_provider_ready_adapter.build_provider_availability_from_opl_proof(
        opl_production_proof=opl_production_proof,
        proof_ref=opl_production_proof_ref,
    )
    provider_ready_contract = opl_provider_ready_adapter.build_opl_provider_ready_contract(
        profile=profile,
        profile_ref=profile_ref,
        allowed_task_kinds=ALLOWED_TASK_KINDS,
        opl_production_proof=opl_production_proof,
        opl_production_proof_ref=opl_production_proof_ref,
    )
    workspace_runtime_evidence_receipt = (
        opl_provider_ready_adapter.build_workspace_runtime_evidence_receipt_surface(profile=profile)
    )
    standard_domain_agent_skeleton = (
        opl_provider_ready_adapter.build_standard_domain_agent_skeleton_surface()
    )
    functional_closure_status_projection = (
        opl_provider_ready_adapter.build_functional_closure_status_projection(
            provider_residency_read_model=provider_ready_contract["provider_residency_read_model"],
            provider_guarded_soak_read_model=provider_ready_contract["provider_guarded_soak_read_model"],
            managed_temporal_state_consistency=provider_ready_contract["managed_temporal_state_consistency"],
            owner_receipt_contract=provider_ready_contract["owner_receipt_contract"],
            lifecycle_guarded_apply_proof=provider_ready_contract["lifecycle_guarded_apply_proof"],
            workspace_runtime_evidence_receipt=workspace_runtime_evidence_receipt,
            standard_domain_agent_skeleton=standard_domain_agent_skeleton,
        )
    )
    pending_tasks, paper_mission_default_tasks = _pending_family_tasks(
        studies=studies,
        profile=profile,
        profile_ref=profile_ref,
        provider_availability=provider_availability,
        opl_production_proof_ref=opl_production_proof_ref,
        progress_by_study_id=progress_by_study_id,
    )
    return {
        "surface_kind": "mas_family_domain_handler_export",
        "version": "mas-family-domain-handler.v1",
        "target_domain_id": "mas",
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
                "owner_callable_adapter_kind": "codex_cli_default",
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
            "entrypoint": domain_entry_handler_target("domain-handler-dispatch"),
            "default_action_intent": DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND,
            "default_queue_source": "/paper_mission_default_tasks",
            "legacy_queue_source": "/pending_family_tasks",
            "allowed_task_kinds": sorted({*ALLOWED_TASK_KINDS, DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND}),
            "retired_diagnostic_task_kinds": sorted(RETIRED_DIAGNOSTIC_TASK_KINDS),
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
        "ars_learning_projection": build_ars_learning_projection(),
        "autosci_learning_projection": build_autosci_learning_projection(),
        "evo_scientist_learning_projection": build_evo_scientist_learning_projection(),
        "external_learning_adoption_closure": build_external_learning_adoption_closure(),
        "display_pack_agent_capability": display_pack_capability_discover(repo_root=_repo_root()),
        "family_transition_spec_descriptor": (
            family_transition_spec.build_family_transition_spec_descriptor()
        ),
        "provider_ready_adapter": provider_ready_contract,
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
            provider_ready_contract["opl_unique_control_plane_handoff"]
        ),
        "workspace_runtime_evidence_receipt": workspace_runtime_evidence_receipt,
        "standard_domain_agent_skeleton": standard_domain_agent_skeleton,
        "mas_functional_closure_status_projection": functional_closure_status_projection,
        "family_opl_current_control_state_handoff": {
            "surface_kind": "family_opl_current_control_state_handoff",
            "version": "family-opl-current-control-state-handoff.v1",
            "target_domain_id": "mas",
            "handoff_id": f"{profile.name}_mas_family_opl_current_control_state_handoff",
            "adapter_id": "opl_family_runtime_provider_wakeup_to_mas_domain_handler",
            "cadence": {"interval_seconds": 60},
            "current_control_state_freshness": {"state": "unknown", "observed_at": generated_at, "max_age_seconds": 180},
            "slo_state": {
                "state": _aggregate_slo_state(studies),
                "summary": "MAS exposes SLO state as read-only projection for OPL family-runtime indexing.",
            },
            "repair_command": domain_entry_handler_target("domain-handler-export"),
            "safe_reconcile_hint": (
                "Use the OPL provider/runtime manager plus the generated MAS domain-handler targets; "
                "MAS default surfaces stay in standard OPL Agent shape."
            ),
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
        "paper_mission_default_tasks": paper_mission_default_tasks,
        "pending_family_tasks_policy": _pending_family_tasks_policy(),
        "pending_family_tasks": pending_tasks,
        "studies": studies,
    }


def _pending_family_tasks_policy() -> dict[str, Any]:
    return {
        "default_paper_mission_queue_source": "/paper_mission_default_tasks",
        "legacy_mixed_queue_source": "/pending_family_tasks",
        "pending_family_tasks_role": "mixed_explicit_owner_handoff_and_migration_compatibility_queue",
        "legacy_dispatch_diagnostics_source": "/retired_default_paper_dispatch_diagnostics",
        "ordinary_consumer_forbidden_task_kinds": sorted(RETIRED_DIAGNOSTIC_TASK_KINDS),
        "legacy_task_kinds_must_not_hydrate_from_pending_family_tasks": True,
        "ordinary_consumer_rule": (
            "OPL consumers that want the MAS paper loop must hydrate only "
            "/paper_mission_default_tasks unless an explicit owner handoff task "
            "was selected by a MAS StageTerminalDecision or authority receipt."
        ),
        "non_default_task_policy": {
            "default_paper_mission_entry": False,
            "paper_mission_default_role": "diagnostic_or_explicit_owner_handoff",
            "can_select_next_paper_stage": False,
            "can_authorize_provider_admission": False,
            "counts_as_paper_progress": False,
        },
    }


def _pending_family_tasks(
    *,
    studies: list[Mapping[str, Any]],
    profile: WorkspaceProfile,
    profile_ref: Path,
    provider_availability: Mapping[str, Any],
    opl_production_proof_ref: str | Path | None,
    progress_by_study_id: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    tasks: list[dict[str, Any]] = []
    paper_mission_default_tasks: list[dict[str, Any]] = []
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
            progress_by_study_id=progress_by_study_id,
        )
        paper_mission_default_task = _paper_mission_start_or_resume_task(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
        )
        paper_mission_default_tasks.append(paper_mission_default_task)
        default_route_handoff = mapping(
            paper_mission_default_task.get("opl_route_handoff")
        )
        if default_route_handoff:
            tasks.append(
                _paper_mission_consumption_route_handoff_task(
                    enriched_route_handoff=default_route_handoff,
                    profile=profile,
                    profile_ref=profile_ref,
                    study_id=study_id,
                )
            )
        current_owner_action = _export_current_owner_action(
            study=study,
            current_progress=current_progress,
        )
        if current_owner_action or _stage_outcome_blocks_legacy_tasks(current_progress):
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
            publication_aftercare.build_publication_aftercare_pending_tasks(
                profile_name=profile.name,
                profile_ref=profile_ref,
                study_id=study_id,
                projection=mapping(study.get("publication_aftercare")),
            )
        )
    return (
        _mark_non_default_paper_mission_tasks(tasks),
        paper_mission_default_tasks,
    )


def _stage_outcome_blocks_legacy_tasks(current_progress: Mapping[str, Any]) -> bool:
    stage_closure = mapping(current_progress.get("stage_closure"))
    outcome = mapping(stage_closure.get("outcome"))
    return text(outcome.get("kind")) in {
        "typed_blocker",
        "human_gate",
        "owner_receipt",
        "terminal",
    }


def _fresh_study_progress(
    *,
    study: Mapping[str, Any],
    profile: WorkspaceProfile,
    profile_ref: Path,
    study_id: str,
    progress_by_study_id: Mapping[str, Mapping[str, Any]] | None = None,
) -> Mapping[str, Any]:
    if progress_by_study_id is not None:
        current_progress = progress_by_study_id.get(study_id)
        if isinstance(current_progress, Mapping):
            return current_progress
    try:
        from med_autoscience.controllers.study_progress.projection import read_study_progress
    except ImportError:
        return {}
    study_root = Path(text(study.get("study_root")) or profile.studies_root / study_id)
    try:
        return read_study_progress(
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
    del study
    next_action = mapping(current_progress.get("next_action"))
    if not opl_domain_progress_transition_contract.next_action_identity_complete(next_action):
        return {}
    return next_action


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
                "task_kind": "domain_autonomy/repair-recheck",
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


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", value).strip("-").lower() or "study"


__all__ = ["export_family_domain_handler"]
