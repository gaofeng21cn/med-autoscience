from __future__ import annotations

from datetime import datetime, timezone
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

from .. import publication_aftercare
from ..domain_handler_export.paper_mission_task_shaping import (
    mark_non_default_paper_mission_tasks as _mark_non_default_paper_mission_tasks,
    paper_mission_route_handoff_task as _paper_mission_route_handoff_task,
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
)
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
    pending_tasks, paper_mission_default_tasks = _pending_family_tasks(
        studies=studies,
        profile=profile,
        profile_ref=profile_ref,
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
        "runtime_handoff": {
            "owner": "one-person-lab",
            "runtime_domain_id": "mas",
            "registration_ref": "contracts/domain_route_profile.json",
            "standard_agent_interface_ref": "contracts/domain_descriptor.json#/standard_agent_interface",
            "provider_proof_ref": str(opl_production_proof_ref) if opl_production_proof_ref else None,
            "mas_role": "emit_domain_intent_and_consume_canonical_runtime_payload",
            "mas_reads_or_builds_provider_state": False,
        },
        "dispatch": {
            "entrypoint": domain_entry_handler_target("domain-handler-dispatch"),
            "default_action_intent": DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND,
            "default_queue_source": "/paper_mission_default_tasks",
            "legacy_queue_source": "/pending_family_tasks",
            "allowed_task_kinds": sorted({*ALLOWED_TASK_KINDS, DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND}),
            "retired_diagnostic_task_kinds": sorted(RETIRED_DIAGNOSTIC_TASK_KINDS),
            "receipt_policy": "MAS returns a domain result; OPL Runway persists the transport receipt.",
            "transport_receipt_owner": "one-person-lab",
            "mas_persists_transport_receipt": False,
        },
        "authority_boundary": authority_boundary_payload(),
        "domain_ref_projection": {
            "state_index_owner": "one-person-lab",
            "source_ref_contract": "med_autoscience.opl_domain_pack.state_index_source_refs.source_adapter_contract",
            "domain_owned_source_refs": _aggregate_domain_refs(studies),
            "body_included": False,
        },
        "ars_learning_projection": build_ars_learning_projection(),
        "autosci_learning_projection": build_autosci_learning_projection(),
        "evo_scientist_learning_projection": build_evo_scientist_learning_projection(),
        "external_learning_adoption_closure": build_external_learning_adoption_closure(),
        "display_pack_agent_capability": display_pack_capability_discover(repo_root=_repo_root()),
        "family_transition_spec_descriptor": (
            family_transition_spec.build_family_transition_spec_descriptor()
        ),
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
            "can_authorize_provider_attempt": False,
            "counts_as_paper_progress": False,
        },
    }


def _pending_family_tasks(
    *,
    studies: list[Mapping[str, Any]],
    profile: WorkspaceProfile,
    profile_ref: Path,
    progress_by_study_id: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    tasks: list[dict[str, Any]] = []
    paper_mission_default_tasks: list[dict[str, Any]] = []
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
                _paper_mission_route_handoff_task(
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


def _aggregate_domain_refs(studies: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for study in studies:
        for ref in study.get("domain_owned_source_refs") or []:
            if isinstance(ref, dict) and ref.get("exists") is True:
                refs.append(ref)
    return refs[:50]


__all__ = ["export_family_domain_handler"]
