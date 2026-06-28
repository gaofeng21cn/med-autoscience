from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
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
from med_autoscience.cli_parts.paper_mission_commands import (
    PAPER_MISSION_START_OR_RESUME_TASK_KIND,
    build_paper_mission_readback,
)
from med_autoscience.profiles import WorkspaceProfile

from .. import opl_stage_attempt_carrier_packets
from .. import opl_provider_ready_adapter
from .. import publication_aftercare
from ..provider_admission_parts.provider_admission_current_control_actions import (
    _study_current_action_for_provider_admission,
)
from ..provider_admission_parts.provider_admission_current_control_identity import (
    provider_admission_current_control_action,
)
from ..domain_action_request_materializer_parts import currentness_identity
from ..study_domain_transition_table_parts import family_transition_spec
from .accepted_owner_gate_route_back import accepted_owner_gate_route_back_action
from .authority_boundary import authority_boundary_payload
from .controller_route_back_tasks import controller_decision_route_back_task
from .default_executor_dispatch_tasks import retired_default_paper_dispatch_diagnostics
from med_autoscience.controllers.domain_dispatch_evidence_payload import (
    build_domain_dispatch_evidence_record_payload,
)
from .domain_handler_functional_closure import build_domain_handler_functional_closure_projection
from .export_study_projection import (
    build_study_projection,
    mapping,
    read_json_object,
    study_roots,
    text,
    workspace_relative,
)
from .guarded_apply_tasks import DEFAULT_GUARDED_APPLY_TARGETS, provider_hosted_guarded_apply_tasks
from .owner_route_handoff_tasks import owner_route_handoff_task
from .owner_source_refs import owner_controller_decision_refs
from .paper_mission_consumption_route_handoff import (
    latest_paper_mission_consumption_route_handoff,
    paper_mission_handoff_stage_packet_refs,
)
from .opl_supervisor_decision_request_tasks import opl_supervisor_decision_request_task
from .supervisor_typed_blocker_resolution import (
    current_supervisor_decision as _current_supervisor_decision,
    supervisor_stop_decision_matches_current_work_unit as _supervisor_stop_decision_matches_current_work_unit,
    supervisor_stop_decision_resolution_shapes as _supervisor_stop_decision_resolution_shapes,
)
from .substrate_adapter import build_opl_substrate_adapter_projection
from .task_kinds import ALLOWED_TASK_KINDS, RETIRED_DIAGNOSTIC_TASK_KINDS
from .transition_readback_consumption import (
    current_owner_action_supersedes_transition_request,
    currentness_consumes_current_control_transition_request,
)
from med_autoscience.controllers.study_progress_parts.paper_autonomy_supervisor_decision import (
    provider_admission_supervisor_gate,
)


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
    functional_closure = build_domain_handler_functional_closure_projection(
        profile=profile,
        profile_ref=profile_ref,
        allowed_task_kinds=ALLOWED_TASK_KINDS,
        opl_production_proof=opl_production_proof,
        opl_production_proof_ref=opl_production_proof_ref,
    )
    pending_tasks, retired_dispatch_diagnostics, paper_mission_default_tasks = _pending_family_tasks(
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
            "default_action_intent": PAPER_MISSION_START_OR_RESUME_TASK_KIND,
            "default_queue_source": "/paper_mission_default_tasks",
            "legacy_queue_source": "/pending_family_tasks",
            "allowed_task_kinds": sorted({*ALLOWED_TASK_KINDS, PAPER_MISSION_START_OR_RESUME_TASK_KIND}),
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
        "functional_consumer_boundary": functional_closure["functional_consumer_boundary"],
        "ars_learning_projection": build_ars_learning_projection(),
        "autosci_learning_projection": build_autosci_learning_projection(),
        "evo_scientist_learning_projection": build_evo_scientist_learning_projection(),
        "external_learning_adoption_closure": build_external_learning_adoption_closure(),
        "display_pack_agent_capability": display_pack_capability_discover(repo_root=_repo_root()),
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
            "repair_command": f"medautosci domain-handler export --profile {profile_ref} --format json",
            "safe_reconcile_hint": (
                "Use OPL provider/runtime manager wakeup plus medautosci domain-handler export/dispatch; "
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
        "paper_mission_default_tasks": paper_mission_default_tasks,
        "pending_family_tasks_policy": _pending_family_tasks_policy(),
        "pending_family_tasks": pending_tasks,
        "retired_default_paper_dispatch_diagnostics": retired_dispatch_diagnostics,
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
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    tasks: list[dict[str, Any]] = []
    paper_mission_default_tasks: list[dict[str, Any]] = []
    retired_dispatch_diagnostics: list[dict[str, Any]] = []
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
        retired_diagnostic = retired_default_paper_dispatch_diagnostics(
            profile=profile,
            study_id=study_id,
        )
        if retired_diagnostic is not None:
            retired_dispatch_diagnostics.append(retired_diagnostic)
        current_progress = _fresh_study_progress(
            study=study,
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            progress_by_study_id=progress_by_study_id,
        )
        paper_mission_default_tasks.append(
            _paper_mission_start_or_resume_task(
                profile=profile,
                profile_ref=profile_ref,
                study_id=study_id,
            )
        )
        current_owner_action = _export_current_owner_action(
            study=study,
            current_progress=current_progress,
        )
        ordinary_task_blocker = _ordinary_pending_tasks_blocker(current_progress=current_progress)
        if ordinary_task_blocker and not current_owner_action:
            resolution_task = _current_typed_blocker_owner_resolution_task(
                study=study,
                current_progress=current_progress,
                profile=profile,
                profile_ref=profile_ref,
                study_id=study_id,
            )
            if resolution_task is not None:
                supervisor_request_task = opl_supervisor_decision_request_task(
                    resolution_task=resolution_task,
                    current_progress=current_progress,
                    profile=profile,
                    profile_ref=profile_ref,
                    study_id=study_id,
                )
                if supervisor_request_task is not None:
                    tasks.append(supervisor_request_task)
                tasks.append(resolution_task)
                continue
            if _ordinary_blocker_allows_owner_route_handoff(
                ordinary_task_blocker=ordinary_task_blocker,
                current_progress=current_progress,
            ):
                handoff_task = owner_route_handoff_task(
                    study=study,
                    profile=profile,
                    profile_ref=profile_ref,
                    study_id=study_id,
                )
                if handoff_task is not None:
                    tasks.append(handoff_task)
            continue
        current_work_unit = mapping(current_progress.get("current_work_unit"))
        current_execution_envelope = _export_current_execution_envelope(
            study=study,
            current_progress=current_progress,
        )
        legacy_route_tasks_blocked = _legacy_route_tasks_blocked_by_current_owner_action(
            current_owner_action=current_owner_action,
            current_work_unit=current_work_unit,
            current_execution_envelope=current_execution_envelope,
        )
        if not legacy_route_tasks_blocked:
            tasks.extend(
                _paper_autonomy_tasks(
                    study=study,
                    profile=profile,
                    profile_ref=profile_ref,
                    study_id=study_id,
                )
            )
        if ordinary_task_blocker or legacy_route_tasks_blocked:
            continue
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
            current_progress=current_progress,
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
        )
        if controller_task is not None:
            tasks.append(controller_task)
    ordinary_tasks, retired_task_diagnostics = _split_retired_default_paper_tasks(tasks)
    retired_dispatch_diagnostics.extend(retired_task_diagnostics)
    return (
        _mark_non_default_paper_mission_tasks(ordinary_tasks),
        retired_dispatch_diagnostics,
        paper_mission_default_tasks,
    )


def _paper_mission_start_or_resume_task(
    *,
    profile: WorkspaceProfile,
    profile_ref: Path,
    study_id: str,
) -> dict[str, Any]:
    dispatch_run_id = _paper_mission_default_dispatch_run_id(study_id)
    readback = build_paper_mission_readback(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        paper_mission_command="start",
        dry_run=True,
        source="domain-handler-export",
    )
    route_handoff = latest_paper_mission_consumption_route_handoff(
        workspace_root=profile.workspace_root,
        study_id=study_id,
    )
    carrier = mapping(readback.get("opl_runtime_carrier"))
    default_route_handoff = _paper_mission_default_route_handoff(
        route_handoff=route_handoff,
        readback=readback,
        current_carrier=carrier,
    )
    if default_route_handoff:
        carrier = mapping(default_route_handoff.get("opl_runtime_carrier")) or carrier
    stage_packet_refs = _paper_mission_stage_packet_refs(readback)
    if default_route_handoff:
        stage_packet_refs = paper_mission_handoff_stage_packet_refs(
            default_route_handoff,
            fallback_refs=stage_packet_refs,
        )
    payload = {
        "profile": str(profile_ref),
        "profile_ref": str(profile_ref),
        "workspace_root": str(profile.workspace_root),
        "domain_workspace_root": str(profile.workspace_root),
        "repo_root": str(profile.workspace_root),
        "study_id": study_id,
        "paper_mission_command": "drive",
        "run_id": dispatch_run_id,
        "submit_opl_runtime": False,
        "dry_run": False,
        "dispatch_execution_boundary": {
            "mode": "non_authority_candidate_package_and_consumption_ledger",
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "runtime_queue_submission_requires_explicit_submit_opl_runtime": True,
        },
        "diagnostic_readback_command": "start",
        "diagnostic_readback_dry_run": True,
        "paper_mission": readback,
    }
    if carrier:
        payload.update(
            {
                "opl_runtime_carrier": carrier,
                "opl_domain_progress_transition_request": carrier,
                "dispatch_authority": "paper_mission_transaction",
                "action_type": text(carrier.get("action_type")),
                "work_unit_id": text(carrier.get("work_unit_id")),
                "work_unit_fingerprint": text(
                    carrier.get("work_unit_fingerprint")
                ),
                "action_fingerprint": text(carrier.get("work_unit_fingerprint")),
                "source_fingerprint": text(carrier.get("work_unit_fingerprint")),
                "route_identity_key": text(carrier.get("route_identity_key")),
                "attempt_idempotency_key": text(
                    carrier.get("attempt_idempotency_key")
                ),
                "request_idempotency_key": text(
                    carrier.get("request_idempotency_key")
                ),
                "next_executable_owner": "med-autoscience",
                "provider_attempt_or_lease_required": False,
                "provider_completion_is_domain_completion": False,
                "stage_transition_authority_boundary": carrier.get(
                    "authority_boundary"
                ),
                "stage_packet_refs": stage_packet_refs,
            }
        )
        if stage_packet_refs:
            payload["stage_packet_ref"] = stage_packet_refs[0]
    if route_handoff and default_route_handoff is None:
        payload["paper_mission_consumption_ledger_diagnostic"] = (
            _ignored_paper_mission_handoff_diagnostic(
                route_handoff=route_handoff,
                readback=readback,
                current_carrier=carrier,
            )
        )
    if default_route_handoff:
        enriched_route_handoff = _enriched_paper_mission_route_handoff(
            route_handoff=default_route_handoff,
            workspace_root=profile.workspace_root,
            profile_ref=profile_ref,
        )
        payload.update(
            {
                "opl_route_handoff": enriched_route_handoff,
                "opl_route_handoff_record": enriched_route_handoff,
                "paper_mission_default_handoff_source": (
                    "paper_mission_consumption_ledger"
                ),
                "paper_mission_default_handoff_ref": text(
                    default_route_handoff.get("source_ref")
                ),
                "opl_route_command": mapping(enriched_route_handoff.get("opl_route_command")),
                "route_command_kind": text(enriched_route_handoff.get("route_command_kind")),
                "route_target": text(enriched_route_handoff.get("route_target")),
                "paper_mission_transaction_ref": text(
                    enriched_route_handoff.get("paper_mission_transaction_ref")
                ),
                "opl_route_command_ref": text(
                    enriched_route_handoff.get("opl_route_command_ref")
                ),
                "candidate_ref": text(enriched_route_handoff.get("candidate_ref")),
                "source_ref": text(enriched_route_handoff.get("source_ref")),
                "mission_id": text(enriched_route_handoff.get("mission_id")),
                "route_identity_key": text(
                    enriched_route_handoff.get("route_identity_key")
                ),
                "attempt_idempotency_key": text(
                    enriched_route_handoff.get("attempt_idempotency_key")
                ),
                "request_idempotency_key": text(
                    enriched_route_handoff.get("request_idempotency_key")
                ),
                "next_executable_owner": "one-person-lab",
            }
        )
    task = {
        "task_id": f"paper-mission-start-or-resume::{study_id}",
        "domain_id": "medautoscience",
        "task_kind": PAPER_MISSION_START_OR_RESUME_TASK_KIND,
        "recommended_task_kind": PAPER_MISSION_START_OR_RESUME_TASK_KIND,
        "action_intent": PAPER_MISSION_START_OR_RESUME_TASK_KIND,
        "default_paper_mission_entry": True,
        "migration_diagnostic_only": False,
        "source": "mas-domain-handler-export",
        "profile": str(profile_ref),
        "study_id": study_id,
        "payload": payload,
        "authority_boundary": {
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang": False,
            "forbidden_authority_writes": readback["forbidden_authority_writes"],
        },
    }
    if default_route_handoff:
        task.update(
            {
                "opl_route_handoff": enriched_route_handoff,
                "opl_route_handoff_record": enriched_route_handoff,
                "paper_mission_default_handoff_source": (
                    "paper_mission_consumption_ledger"
                ),
                "paper_mission_default_handoff_ref": text(
                    default_route_handoff.get("source_ref")
                ),
                "route_command_kind": text(enriched_route_handoff.get("route_command_kind")),
                "route_target": text(enriched_route_handoff.get("route_target")),
                "paper_mission_transaction_ref": text(
                    enriched_route_handoff.get("paper_mission_transaction_ref")
                ),
                "opl_route_command_ref": text(
                    enriched_route_handoff.get("opl_route_command_ref")
                ),
                "candidate_ref": text(enriched_route_handoff.get("candidate_ref")),
                "source_ref": text(enriched_route_handoff.get("source_ref")),
                "mission_id": text(enriched_route_handoff.get("mission_id")),
                "route_identity_key": text(
                    enriched_route_handoff.get("route_identity_key")
                ),
                "attempt_idempotency_key": text(
                    enriched_route_handoff.get("attempt_idempotency_key")
                ),
                "request_idempotency_key": text(
                    enriched_route_handoff.get("request_idempotency_key")
                ),
                "workspace_root": str(profile.workspace_root),
                "domain_workspace_root": str(profile.workspace_root),
                "repo_root": str(profile.workspace_root),
                "profile_ref": str(profile_ref),
            }
        )
    return task


def _paper_mission_default_dispatch_run_id(study_id: str) -> str:
    return f"domain-handler-default-drive-{_slug(study_id)}"


def _paper_mission_default_route_handoff(
    *,
    route_handoff: Mapping[str, Any] | None,
    readback: Mapping[str, Any],
    current_carrier: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not route_handoff:
        return None
    handoff_carrier = mapping(route_handoff.get("opl_runtime_carrier"))
    if not _carrier_has_opl_intake_identity(current_carrier):
        return None
    if not _carrier_has_opl_intake_identity(handoff_carrier):
        return None
    current_transaction_ref = (
        text(current_carrier.get("paper_mission_transaction_ref"))
        or text(mapping(readback.get("paper_mission_transaction")).get("transaction_id"))
    )
    if (
        text(route_handoff.get("paper_mission_transaction_ref"))
        != current_transaction_ref
    ):
        return None
    current_route_ref = text(current_carrier.get("opl_route_command_ref")) or (
        f"{current_transaction_ref}#opl_route_command"
        if current_transaction_ref
        else None
    )
    if text(route_handoff.get("opl_route_command_ref")) != current_route_ref:
        return None
    for field in (
        "paper_mission_transaction_ref",
        "opl_route_command_ref",
        "route_identity_key",
        "attempt_idempotency_key",
        "request_idempotency_key",
    ):
        current_value = text(current_carrier.get(field))
        if current_value and text(handoff_carrier.get(field)) != current_value:
            return None
    return dict(route_handoff)


def _carrier_has_opl_intake_identity(carrier: Mapping[str, Any]) -> bool:
    return all(
        text(carrier.get(field))
        for field in (
            "route_identity_key",
            "attempt_idempotency_key",
            "request_idempotency_key",
            "paper_mission_transaction_ref",
            "opl_route_command_ref",
        )
    )


def _enriched_paper_mission_route_handoff(
    *,
    route_handoff: Mapping[str, Any],
    workspace_root: Path,
    profile_ref: Path,
) -> dict[str, Any]:
    carrier = mapping(route_handoff.get("opl_runtime_carrier"))
    return {
        **dict(route_handoff),
        "workspace_root": str(workspace_root),
        "domain_workspace_root": str(workspace_root),
        "repo_root": str(workspace_root),
        "profile_ref": str(profile_ref),
        "route_identity_key": text(carrier.get("route_identity_key")),
        "attempt_idempotency_key": text(carrier.get("attempt_idempotency_key")),
        "request_idempotency_key": text(carrier.get("request_idempotency_key")),
        "idempotency_key": text(carrier.get("idempotency_key")),
        "action_type": text(carrier.get("action_type")),
        "work_unit_id": text(carrier.get("work_unit_id")),
        "work_unit_fingerprint": text(carrier.get("work_unit_fingerprint")),
        "opl_domain_progress_transition_request": carrier,
    }


def _ignored_paper_mission_handoff_diagnostic(
    *,
    route_handoff: Mapping[str, Any],
    readback: Mapping[str, Any],
    current_carrier: Mapping[str, Any],
) -> dict[str, Any]:
    handoff_carrier = mapping(route_handoff.get("opl_runtime_carrier"))
    return {
        "surface_kind": "paper_mission_consumption_ledger_diagnostic",
        "status": "ignored_for_default_paper_mission_task",
        "reason": "handoff_identity_does_not_match_current_paper_mission_readback",
        "source_ref": text(route_handoff.get("source_ref")),
        "paper_mission_transaction_ref": text(
            route_handoff.get("paper_mission_transaction_ref")
        ),
        "current_paper_mission_transaction_ref": (
            text(current_carrier.get("paper_mission_transaction_ref"))
            or text(
                mapping(readback.get("paper_mission_transaction")).get(
                    "transaction_id"
                )
            )
        ),
        "opl_route_command_ref": text(route_handoff.get("opl_route_command_ref")),
        "current_opl_route_command_ref": text(
            current_carrier.get("opl_route_command_ref")
        ),
        "route_identity_key": text(handoff_carrier.get("route_identity_key")),
        "current_route_identity_key": text(current_carrier.get("route_identity_key")),
    }


def _paper_mission_stage_packet_refs(readback: Mapping[str, Any]) -> list[str]:
    carrier = mapping(readback.get("opl_runtime_carrier"))
    refs = [
        text(carrier.get("stage_run_ref")),
        text(readback.get("materialized_mission_ref")),
        text(readback.get("candidate_manifest_ref")),
    ]
    transaction = mapping(readback.get("paper_mission_transaction"))
    refs.extend(
        [
            text(transaction.get("stage_run_ref")),
            text(transaction.get("transaction_id")),
        ]
    )
    return [ref for ref in refs if ref]


def _split_retired_default_paper_tasks(
    tasks: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ordinary_tasks: list[dict[str, Any]] = []
    retired_diagnostics: list[dict[str, Any]] = []
    for task in tasks:
        if text(task.get("task_kind")) == "paper_mission/stage-outcome":
            retired_diagnostics.append(_retired_default_paper_task_diagnostic(task))
            continue
        ordinary_tasks.append(task)
    return ordinary_tasks, retired_diagnostics


def _mark_non_default_paper_mission_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    marked: list[dict[str, Any]] = []
    for task in tasks:
        if (
            text(task.get("task_kind")) == PAPER_MISSION_START_OR_RESUME_TASK_KIND
            and task.get("default_paper_mission_entry") is True
        ):
            marked.append(task)
            continue
        marked.append(
            {
                **task,
                "default_paper_mission_entry": False,
                "paper_mission_default_role": "diagnostic_or_explicit_owner_handoff",
                "can_select_next_paper_stage": False,
                "can_authorize_provider_admission": False,
                "counts_as_paper_progress": False,
            }
        )
    return marked


def _retired_default_paper_task_diagnostic(task: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **task,
        "surface_kind": "retired_default_paper_dispatch_task_diagnostic",
        "default_paper_mission_entry": False,
        "migration_diagnostic_only": True,
        "ordinary_schedulable": False,
        "active_caller_class": "diagnostic_only",
        "action_intent": PAPER_MISSION_START_OR_RESUME_TASK_KIND,
        "replacement_task_kind": PAPER_MISSION_START_OR_RESUME_TASK_KIND,
        "diagnostic_role": "retired_default_paper_dispatch",
    }


def _current_control_transition_request_tasks(
    *,
    study: Mapping[str, Any],
    current_progress: Mapping[str, Any] | None = None,
    current_owner_action: Mapping[str, Any] | None = None,
    profile: WorkspaceProfile,
    profile_ref: Path,
    study_id: str,
) -> list[dict[str, Any]]:
    candidate = _study_current_action_for_provider_admission(study)
    if not candidate:
        return []
    mas_owner_action_source = text(candidate.get("mas_owner_action_source"))
    if not _current_control_transition_request_source_supported(mas_owner_action_source):
        return []
    source_surface = text(candidate.get("source_surface")) or mas_owner_action_source
    transition_request = mapping(candidate.get("opl_domain_progress_transition_request"))
    if not transition_request:
        return []
    action = provider_admission_current_control_action(candidate)
    action_type = text(action.get("action_type")) or text(candidate.get("action_type"))
    work_unit_id = text(action.get("work_unit_id")) or text(candidate.get("work_unit_id"))
    work_unit_fingerprint = (
        text(action.get("work_unit_fingerprint"))
        or text(candidate.get("work_unit_fingerprint"))
        or text(candidate.get("action_fingerprint"))
    )
    if mas_owner_action_source.startswith(
        "opl_current_control_state."
    ) and currentness_consumes_current_control_transition_request(
        current_progress or study,
        action_type=action_type,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
    ):
        return []
    if mas_owner_action_source.startswith(
        "opl_current_control_state."
    ) and current_owner_action_supersedes_transition_request(
        current_owner_action or {},
        action_type=action_type,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
    ):
        return []
    source_fingerprint = (
        text(candidate.get("action_fingerprint"))
        or work_unit_fingerprint
        or text(mapping(transition_request.get("aggregate_identity")).get("work_unit_fingerprint"))
        or _fingerprint(transition_request)
    )
    source_refs = [
        {
            "role": "opl_domain_progress_transition_request",
            "ref": text(transition_request.get("idempotency_key")) or source_fingerprint,
            "exists": True,
        },
        {
            "role": "current_owner_action_source",
            "ref": source_surface,
            "exists": True,
        },
    ]
    identity_refs = _current_control_transition_identity_refs(
        action,
        profile=profile,
        study_id=study_id,
        action_type=action_type,
    )
    if identity_refs:
        action = {**action, **identity_refs}
    candidate_owner_route = mapping(candidate.get("owner_route"))
    owner_route = mapping(action.get("owner_route")) or candidate_owner_route
    owner_route_currentness_basis = _current_control_transition_currentness_basis(
        transition_request=transition_request,
        owner_route=owner_route,
        candidate_owner_route=candidate_owner_route,
        action=action,
        candidate=candidate,
        study=study,
    )
    transition_request = currentness_identity.normalize_transition_request_currentness(
        transition_request,
        owner_route_currentness_basis,
    )
    action = currentness_identity.normalize_action_handoff_currentness(
        action,
        owner_route_currentness_basis,
    )
    action = _with_current_control_transition_owner_route_basis(
        action,
        owner_route_currentness_basis,
    )
    action["opl_domain_progress_transition_request"] = transition_request
    evidence_record_payload = build_domain_dispatch_evidence_record_payload(
        task_kind="paper_mission/stage-outcome",
        study_id=study_id,
        reason="current_control_transition_request_pending",
        evidence_refs=source_refs,
        source_fingerprint=source_fingerprint,
        profile_name=profile.name,
    )
    payload = {
        "profile": str(profile_ref),
        "study_id": study_id,
        "quest_id": text(candidate.get("quest_id")) or study_id,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "source_fingerprint": source_fingerprint,
        **identity_refs,
        "authority_boundary": "mas_domain_progress_transition_request_only",
        "next_executable_owner": text(candidate.get("next_executable_owner")),
        "owner_route_currentness_basis": owner_route_currentness_basis,
        "provider_admission_pending": False,
        "provider_admission_requires_opl_runtime_result": True,
        "opl_domain_progress_transition_request": transition_request,
        "paper_progress_policy_result": mapping(candidate.get("paper_progress_policy_result")),
        "current_control_action": action,
    }
    return [
        {
            "domain_id": "medautoscience",
            "task_kind": "paper_mission/stage-outcome",
            "study_id": study_id,
            "quest_id": text(candidate.get("quest_id")) or study_id,
            "action_type": action_type,
            "domain_owner": text(candidate.get("next_executable_owner")),
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "priority": 75,
            "source": "mas-domain-handler-export",
            "requires_approval": False,
            "dedupe_key": (
                f"mas:{profile.name}:{study_id}:current-control-transition-request:"
                f"{action_type}:{source_fingerprint}"
            ),
            "source_fingerprint": source_fingerprint,
            "reason": "current_control_transition_request_pending",
            "payload": {key: value for key, value in payload.items() if value not in (None, "", [], {})},
            "source_refs": [ref for ref in source_refs if ref.get("ref") not in (None, "")],
            **identity_refs,
            "dispatch_owner": "one-person-lab",
            "domain_truth_owner": "med-autoscience",
            "queue_owner": "one-person-lab",
            "profile_name": profile.name,
            "provider_admission_pending": False,
            "provider_admission_requires_opl_runtime_result": True,
            "opl_domain_progress_transition_request": transition_request,
            "domain_dispatch_evidence_record_payload": evidence_record_payload,
        }
    ]


def _current_control_transition_currentness_basis(
    *,
    transition_request: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    candidate_owner_route: Mapping[str, Any],
    action: Mapping[str, Any],
    candidate: Mapping[str, Any],
    study: Mapping[str, Any],
) -> dict[str, Any]:
    current_work_unit = mapping(study.get("current_work_unit"))
    basis = currentness_identity.normalize_currentness_sources(
        mapping(transition_request.get("currentness_basis")),
        currentness_identity.owner_route_basis(owner_route),
        currentness_identity.owner_route_basis(candidate_owner_route),
        mapping(candidate.get("owner_route_currentness_basis")),
        mapping(current_work_unit.get("currentness_basis")),
        mapping(action.get("currentness_basis")),
        mapping(candidate.get("currentness_basis")),
    )
    strong_action_identity = currentness_identity.normalize_currentness_sources(action, candidate)
    for key in ("source_fingerprint", "work_unit_id", "work_unit_fingerprint"):
        if text(strong_action_identity.get(key)) is not None:
            basis[key] = strong_action_identity[key]
    if text(basis.get("work_unit_fingerprint")) is not None:
        basis["route_epoch"] = basis["work_unit_fingerprint"]
    basis.pop("source", None)
    return basis


def _with_current_control_transition_owner_route_basis(
    action: Mapping[str, Any],
    currentness_basis: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(action)
    basis = {key: value for key, value in currentness_basis.items() if value not in (None, "", [], {})}
    payload["owner_route_currentness_basis"] = basis
    owner_route = mapping(payload.get("owner_route"))
    if owner_route:
        source_refs = dict(mapping(owner_route.get("source_refs")))
        source_refs["owner_route_currentness_basis"] = basis
        owner_route["source_refs"] = source_refs
        currentness_contract = dict(mapping(owner_route.get("currentness_contract")))
        currentness_contract["basis"] = basis
        owner_route["currentness_contract"] = currentness_contract
        payload["owner_route"] = owner_route
    return payload


def _current_control_transition_identity_refs(
    action: Mapping[str, Any],
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str | None,
) -> dict[str, Any]:
    explicit_refs = _current_control_action_stage_packet_refs(action)
    stage_packet_ref = text(explicit_refs.get("stage_packet_ref"))
    stage_packet_refs = list(explicit_refs.get("stage_packet_refs") or [])
    dispatch_ref = text(action.get("dispatch_ref"))
    dispatch_refs = _current_control_transition_dispatch_refs(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        explicit_dispatch_ref=dispatch_ref,
    )
    if dispatch_ref is None:
        dispatch_ref = text(dispatch_refs.get("dispatch_ref"))
    dispatch_stage_packet_ref = text(dispatch_refs.get("stage_packet_ref"))
    if dispatch_stage_packet_ref is not None and (
        stage_packet_ref is None
        or _is_generated_current_work_unit_stage_packet_ref(stage_packet_ref)
    ):
        stage_packet_ref = dispatch_stage_packet_ref
        stage_packet_refs = [
            ref
            for ref in stage_packet_refs
            if not _is_generated_current_work_unit_stage_packet_ref(ref)
        ]
    for ref in dispatch_refs.get("stage_packet_refs") or []:
        text_ref = text(ref)
        if text_ref is not None and text_ref not in stage_packet_refs:
            stage_packet_refs.append(text_ref)
    if stage_packet_ref is not None and stage_packet_ref not in stage_packet_refs:
        stage_packet_refs.insert(0, stage_packet_ref)
    checkpoint_refs = list(explicit_refs.get("checkpoint_refs") or [])
    if not checkpoint_refs:
        checkpoint_refs = list(stage_packet_refs)
    return {
        key: value
        for key, value in {
            "dispatch_ref": dispatch_ref,
            "stage_packet_ref": stage_packet_ref,
            "stage_packet_refs": list(dict.fromkeys(stage_packet_refs)),
            "checkpoint_refs": list(dict.fromkeys(checkpoint_refs)),
        }.items()
        if value not in (None, "", [], {})
    }


def _is_generated_current_work_unit_stage_packet_ref(ref: str | None) -> bool:
    return bool(ref and ref.startswith("mas://current-work-unit/") and ref.endswith("/stage-packet"))


def _current_control_action_stage_packet_refs(action: Mapping[str, Any]) -> dict[str, Any]:
    source_refs = mapping(action.get("source_refs"))
    owner_route_refs = mapping(mapping(action.get("owner_route")).get("source_refs"))
    handoff_packet = mapping(action.get("handoff_packet"))
    handoff_refs = mapping(handoff_packet.get("source_refs"))
    current_control_action = mapping(action.get("current_control_action"))
    current_control_refs = mapping(current_control_action.get("source_refs"))
    stage_packet_ref = _first_text_value(
        action.get("stage_packet_ref"),
        source_refs.get("stage_packet_ref"),
        owner_route_refs.get("stage_packet_ref"),
        handoff_packet.get("stage_packet_ref"),
        handoff_refs.get("stage_packet_ref"),
        current_control_action.get("stage_packet_ref"),
        current_control_refs.get("stage_packet_ref"),
    )
    stage_packet_refs = _dedupe_text_items(
        action.get("stage_packet_refs"),
        source_refs.get("stage_packet_refs"),
        owner_route_refs.get("stage_packet_refs"),
        handoff_packet.get("stage_packet_refs"),
        handoff_refs.get("stage_packet_refs"),
        current_control_action.get("stage_packet_refs"),
        current_control_refs.get("stage_packet_refs"),
    )
    if stage_packet_ref is not None and stage_packet_ref not in stage_packet_refs:
        stage_packet_refs.insert(0, stage_packet_ref)
    checkpoint_refs = _dedupe_text_items(
        action.get("checkpoint_refs"),
        source_refs.get("checkpoint_refs"),
        owner_route_refs.get("checkpoint_refs"),
        handoff_packet.get("checkpoint_refs"),
        handoff_refs.get("checkpoint_refs"),
        current_control_action.get("checkpoint_refs"),
        current_control_refs.get("checkpoint_refs"),
    ) or list(stage_packet_refs)
    return {
        key: value
        for key, value in {
            "stage_packet_ref": stage_packet_ref,
            "stage_packet_refs": stage_packet_refs,
            "checkpoint_refs": checkpoint_refs,
        }.items()
        if value not in (None, "", [], {})
    }


def _first_text_value(*values: object) -> str | None:
    for value in values:
        result = text(value)
        if result is not None:
            return result
    return None


def _dedupe_text_items(*values: object) -> list[str]:
    refs: list[str] = []
    for value in values:
        if isinstance(value, str):
            text_value = text(value)
            if text_value is not None and text_value not in refs:
                refs.append(text_value)
            continue
        if not isinstance(value, list | tuple | set):
            continue
        for item in value:
            text_value = text(item)
            if text_value is not None and text_value not in refs:
                refs.append(text_value)
    return refs


def _current_control_transition_dispatch_refs(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str | None,
    explicit_dispatch_ref: str | None,
) -> dict[str, Any]:
    if action_type is None:
        return {}
    dispatch_path = _current_control_transition_dispatch_path(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        explicit_dispatch_ref=explicit_dispatch_ref,
    )
    dispatch = read_json_object(dispatch_path)
    if not dispatch or text(dispatch.get("action_type")) != action_type:
        return {}
    stage_packet_path = opl_stage_attempt_carrier_packets.dispatch_stage_packet_path(
        dispatch,
        fallback_dispatch_path=dispatch_path,
    )
    if not stage_packet_path.is_file():
        return {}
    dispatch_ref = workspace_relative(dispatch_path, workspace_root=profile.workspace_root)
    stage_packet_ref = workspace_relative(stage_packet_path, workspace_root=profile.workspace_root)
    return {
        "dispatch_ref": dispatch_ref,
        "stage_packet_ref": stage_packet_ref,
        "stage_packet_refs": [stage_packet_ref],
    }


def _current_control_transition_dispatch_path(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str,
    explicit_dispatch_ref: str | None,
) -> Path:
    ref = text(explicit_dispatch_ref)
    if ref is not None:
        path = Path(ref).expanduser()
        if path.is_absolute():
            return path
        workspace_path = profile.workspace_root / path
        if workspace_path.is_file():
            return workspace_path
    return (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / f"{action_type}.json"
    )


def _current_control_transition_request_source_supported(source: str | None) -> bool:
    if source is None:
        return False
    if source.startswith("opl_current_control_state."):
        return True
    return source == "paper_recovery_state.next_safe_action.successor_owner_action"


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


def _legacy_route_tasks_blocked_by_current_owner_action(
    *,
    current_owner_action: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    current_execution_envelope: Mapping[str, Any],
) -> bool:
    work_unit_status = text(current_work_unit.get("status"))
    if work_unit_status == "executable_owner_action":
        return True
    envelope_state = text(current_execution_envelope.get("state_kind")) or text(
        current_execution_envelope.get("execution_state_kind")
    )
    return envelope_state == "executable_owner_action" and bool(current_owner_action or current_work_unit)


def _ordinary_pending_tasks_blocked_status(status: str | None) -> bool:
    return status in {
        "typed_blocker",
        "running_provider_attempt",
        "blocked_current_work_unit",
        "blocked_typed_owner",
        "parked",
    }


def _ordinary_blocker_allows_owner_route_handoff(
    *,
    ordinary_task_blocker: Mapping[str, Any],
    current_progress: Mapping[str, Any],
) -> bool:
    if text(ordinary_task_blocker.get("source")) != "current_work_unit":
        return False
    if text(ordinary_task_blocker.get("state_kind")) != "blocked_current_work_unit":
        return False
    current_work_unit = mapping(current_progress.get("current_work_unit"))
    current_work_unit_state = mapping(current_work_unit.get("state"))
    if text(current_work_unit_state.get("blocker_type")) != "current_work_unit_unresolved":
        return False
    return not (
        text(current_work_unit.get("work_unit_id"))
        or text(current_work_unit.get("work_unit_fingerprint"))
        or text(current_work_unit.get("action_fingerprint"))
    )


def _current_typed_blocker_owner_resolution_task(
    *,
    study: Mapping[str, Any],
    current_progress: Mapping[str, Any],
    profile: WorkspaceProfile,
    profile_ref: Path,
    study_id: str,
) -> dict[str, Any] | None:
    current_work_unit = mapping(current_progress.get("current_work_unit"))
    current_execution_envelope = mapping(current_progress.get("current_execution_envelope"))
    if text(current_work_unit.get("status")) != "typed_blocker":
        return None
    typed_blocker = _current_typed_blocker(
        current_work_unit=current_work_unit,
        current_execution_envelope=current_execution_envelope,
    )
    supervisor_decision = _current_supervisor_decision(current_progress)
    owner = _current_owner_for_resolution(
        current_work_unit=current_work_unit,
        current_execution_envelope=current_execution_envelope,
    )
    if not _typed_blocker_owner_resolution_supported(
        owner=owner,
        typed_blocker=typed_blocker,
        current_work_unit=current_work_unit,
        supervisor_decision=supervisor_decision,
    ):
        return None
    required_owner = _required_owner_for_typed_blocker_resolution(owner)
    reason = "current_work_unit_typed_blocker_owner_resolution"
    source_fingerprint = _fingerprint(
        {
            "profile": profile.name,
            "study_id": study_id,
            "reason": reason,
            "current_work_unit": dict(current_work_unit),
            "typed_blocker": dict(typed_blocker),
            "supervisor_decision_id": text(supervisor_decision.get("decision_id")),
        }
    )
    source_refs = _typed_blocker_source_refs(
        study=study,
        current_work_unit=current_work_unit,
        typed_blocker=typed_blocker,
        supervisor_decision=supervisor_decision,
        profile=profile,
        study_id=study_id,
    )
    evidence_record_payload = build_domain_dispatch_evidence_record_payload(
        task_kind="domain_route/reconcile-apply",
        study_id=study_id,
        reason=reason,
        evidence_refs=source_refs,
        source_fingerprint=source_fingerprint,
        profile_name=profile.name,
    )
    return {
        "domain_id": "medautoscience",
        "task_kind": "domain_route/reconcile-apply",
        "recommended_task_kind": "domain_route/reconcile-apply",
        "priority": 60,
        "source": "mas-domain-handler-export",
        "requires_approval": False,
        "dedupe_key": f"mas:{profile.name}:{study_id}:current-typed-blocker:{source_fingerprint}",
        "source_fingerprint": source_fingerprint,
        "domain_truth_owner": "med-autoscience",
        "queue_owner": "one-person-lab",
        "reason": reason,
        "source_refs": source_refs,
        "domain_dispatch_evidence_record_payload": evidence_record_payload,
        "payload": {
            "profile": str(profile_ref),
            "study_id": study_id,
            "source_fingerprint": source_fingerprint,
            "continuation_reason": reason,
            "current_work_unit": dict(current_work_unit),
            "current_execution_envelope": dict(current_execution_envelope),
            "typed_blocker": dict(typed_blocker),
            **(
                {
                    "paper_autonomy_supervisor_decision": dict(supervisor_decision),
                    "paper_autonomy_obligation": dict(
                        mapping(supervisor_decision.get("paper_autonomy_obligation"))
                    ),
                }
                if supervisor_decision
                else {}
            ),
            "authority_boundary": "mas_domain_route_refs_only_opl_stage_attempt_owner",
            "required_owner_action": {
                "owner": required_owner,
                "action_type": text(current_work_unit.get("action_type")),
                "work_unit_id": text(current_work_unit.get("work_unit_id")),
                "work_unit_fingerprint": (
                    text(current_work_unit.get("work_unit_fingerprint"))
                    or text(current_work_unit.get("action_fingerprint"))
                ),
                "accepted_resolution_shapes": _typed_blocker_resolution_shapes(
                    owner=required_owner,
                    typed_blocker=typed_blocker,
                    current_work_unit=current_work_unit,
                    supervisor_decision=supervisor_decision,
                ),
            },
        },
    }


def _typed_blocker_owner_resolution_supported(
    *,
    owner: str | None,
    typed_blocker: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    supervisor_decision: Mapping[str, Any],
) -> bool:
    if _supervisor_stop_decision_matches_current_work_unit(
        supervisor_decision=supervisor_decision,
        current_work_unit=current_work_unit,
    ):
        return False
    if _canonical_owner(owner) == "one-person-lab":
        return True
    if _canonical_owner(owner) != "MedAutoScience":
        return False
    return _typed_blocker_identity(typed_blocker) == "no_selected_dispatch_for_requested_action_types"


def _required_owner_for_typed_blocker_resolution(owner: str | None) -> str | None:
    if _canonical_owner(owner) == "one-person-lab":
        return "one-person-lab"
    return owner


def _typed_blocker_resolution_shapes(
    *,
    owner: str | None,
    typed_blocker: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    supervisor_decision: Mapping[str, Any],
) -> list[str]:
    shapes: list[str] = []
    if _supervisor_stop_decision_matches_current_work_unit(
        supervisor_decision=supervisor_decision,
        current_work_unit=current_work_unit,
    ):
        shapes.extend(_supervisor_stop_decision_resolution_shapes(
            current_work_unit=current_work_unit,
            supervisor_decision=supervisor_decision,
        ))
    if (
        _canonical_owner(owner) == "MedAutoScience"
        and _typed_blocker_identity(typed_blocker) == "no_selected_dispatch_for_requested_action_types"
    ):
        shapes.extend(
            [
                "current_selected_mas_dispatch",
                "accepted_owner_receipt_for_materialized_gate_artifact",
            ]
        )
    for shape in (
        "matching_provider_attempt_or_lease_binding",
        "matching_terminal_closeout_receipt",
        "identity_different_successor_owner_action",
        "stable_typed_blocker",
        "human_gate",
    ):
        if shape not in shapes:
            shapes.append(shape)
    return shapes


def _canonical_owner(owner: str | None) -> str | None:
    normalized = text(owner)
    if normalized in {"one-person-lab", "opl", "OPL"}:
        return "one-person-lab"
    if normalized in {"MedAutoScience", "med-autoscience", "medautosci", "mas"}:
        return "MedAutoScience"
    return normalized


def _typed_blocker_identity(typed_blocker: Mapping[str, Any]) -> str | None:
    return (
        text(typed_blocker.get("blocker_id"))
        or text(typed_blocker.get("blocker_type"))
        or text(typed_blocker.get("reason"))
        or text(typed_blocker.get("blocked_reason"))
    )


def _current_owner_for_resolution(
    *,
    current_work_unit: Mapping[str, Any],
    current_execution_envelope: Mapping[str, Any],
) -> str | None:
    return (
        text(current_work_unit.get("owner"))
        or text(mapping(current_work_unit.get("state")).get("owner"))
        or text(current_execution_envelope.get("owner"))
        or text(mapping(current_execution_envelope.get("typed_blocker")).get("owner"))
    )


def _current_typed_blocker(
    *,
    current_work_unit: Mapping[str, Any],
    current_execution_envelope: Mapping[str, Any],
) -> Mapping[str, Any]:
    work_unit_state = mapping(current_work_unit.get("state"))
    return (
        mapping(work_unit_state.get("typed_blocker"))
        or mapping(current_work_unit.get("typed_blocker"))
        or mapping(current_execution_envelope.get("typed_blocker"))
    )


def _typed_blocker_source_refs(
    *,
    study: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    typed_blocker: Mapping[str, Any],
    supervisor_decision: Mapping[str, Any],
    profile: WorkspaceProfile,
    study_id: str,
) -> list[dict[str, Any]]:
    study_root = Path(text(study.get("study_root")) or profile.studies_root / study_id)
    refs: list[dict[str, Any]] = [
        {
            "role": "current_work_unit",
            "ref": "study_progress.current_work_unit",
            "exists": True,
            "status": text(current_work_unit.get("status")),
            "owner": text(current_work_unit.get("owner")),
            "action_type": text(current_work_unit.get("action_type")),
            "work_unit_id": text(current_work_unit.get("work_unit_id")),
            "work_unit_fingerprint": (
                text(current_work_unit.get("work_unit_fingerprint"))
                or text(current_work_unit.get("action_fingerprint"))
            ),
        }
    ]
    typed_blocker_ref = text(typed_blocker.get("source_ref")) or text(current_work_unit.get("source_ref"))
    if typed_blocker_ref is not None:
        refs.append(
            {
                "role": "typed_blocker",
                "ref": typed_blocker_ref,
                "exists": (profile.workspace_root / typed_blocker_ref).exists()
                or (study_root / typed_blocker_ref).exists(),
            }
        )
    if supervisor_decision:
        refs.append(
            {
                "role": "paper_autonomy_supervisor_decision",
                "ref": text(supervisor_decision.get("decision_id"))
                or text(supervisor_decision.get("paper_autonomy_obligation_ref"))
                or "study_progress.paper_recovery_state.supervisor_decision",
                "exists": True,
                "decision": text(supervisor_decision.get("decision")),
                "identity_match": supervisor_decision.get("identity_match") is True,
            }
        )
    return refs


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
    if _supervisor_decision_blocks_owner_action(current_progress):
        return {}
    current_work_unit = mapping(current_progress.get("current_work_unit"))
    current_execution_envelope = mapping(current_progress.get("current_execution_envelope"))
    owner_gate_action = accepted_owner_gate_route_back_action(
        current_progress=current_progress,
        current_work_unit=current_work_unit,
    )
    if owner_gate_action:
        return owner_gate_action
    envelope_state = text(current_execution_envelope.get("state_kind")) or text(
        current_execution_envelope.get("execution_state_kind")
    )
    if _ordinary_pending_tasks_blocked_status(text(current_work_unit.get("status"))) or (
        _ordinary_pending_tasks_blocked_status(envelope_state)
    ):
        return {}
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


def _supervisor_decision_blocks_owner_action(current_progress: Mapping[str, Any]) -> bool:
    return provider_admission_supervisor_gate(current_progress).get("blocked") is True


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
        "owner_route",
        "owner_route_currentness_basis",
        "source_fingerprint",
        "work_unit_fingerprint",
    ):
        value = projection_action.get(key)
        current_value = merged.get(key)
        if value is not None and (
            current_value is None
            or (
                key
                in {
                    "target_surface",
                    "next_action",
                    "owner_route",
                    "owner_route_currentness_basis",
                }
                and not mapping(current_value)
            )
        ):
            merged[key] = value
    owner_route = mapping(merged.get("owner_route"))
    currentness_basis = mapping(merged.get("owner_route_currentness_basis"))
    if owner_route and currentness_basis:
        merged["owner_route"] = currentness_identity.normalize_owner_route_currentness(
            owner_route,
            currentness_basis,
        )
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


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", value).strip("-").lower() or "study"


__all__ = ["export_family_domain_handler"]
