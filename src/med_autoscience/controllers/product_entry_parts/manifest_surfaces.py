from __future__ import annotations

from . import shared as _shared
from . import program_surfaces as _program_surfaces
from . import workspace_surfaces as _workspace_surfaces
from .manifest_rendering import (
    render_product_entry_manifest_markdown,
    render_product_entry_preflight_markdown,
    render_product_entry_start_markdown,
    render_product_entry_status_markdown,
    render_skill_catalog_markdown,
)
from .manifest_shell_surfaces import (
    _build_manifest_shell_surfaces,
)

def _module_reexport(module) -> None:
    names = getattr(module, "__all__", None) or vars(module).keys()
    for name in names:
        if not name.startswith("__") and name != "_module_reexport":
            value = getattr(module, name)
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_program_surfaces)
_module_reexport(_workspace_surfaces)


from .manifest_status_surface import build_product_entry_status_payload as _build_product_entry_status_payload
from med_autoscience.controllers import opl_provider_ready_adapter
from med_autoscience.controllers.opl_unique_control_plane_boundary_parts import consumer_migration
from med_autoscience.controllers import study_domain_transition_table
from med_autoscience.stage_skill_surface_projection import build_stage_skill_surface_projection
from med_autoscience.stage_quality_contract import build_stage_quality_pack_contract
from med_autoscience.ars_learning_projection import build_ars_learning_projection


def _build_product_positioning() -> dict[str, Any]:
    return {
        "surface_kind": "mas_product_positioning",
        "public_role": "Foundry Agent",
        "package_role": "OPL-compatible package built on OPL Framework",
        "framework": "OPL Framework",
        "direct_app_skill_path": True,
        "authority_boundary": {
            "medical_research_truth_owner": "MedAutoScience",
            "quality_verdict_owner": "MedAutoScience",
            "runtime_owner": "OPL provider/runtime manager for generic cadence; MedAutoScience for domain owner receipts",
            "artifact_publication_authority_owner": "MedAutoScience",
            "opl_role": "framework_package_host_and_projection_consumer",
            "opl_is_runtime_kernel": False,
            "can_write_domain_truth": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
        },
        "non_goals": [
            "no_new_runtime_mechanism",
            "not_an_opl_runtime_kernel_claim",
            "not_a_default_hermes_target",
            "not_a_default_mds_target",
            "not_a_default_local_scheduler_target",
        ],
    }


def _build_source_provenance_refs_surface() -> dict[str, Any]:
    return _build_shared_source_provenance_surface(
        summary=(
            "MAS exposes MedDeepScientist and source-intake provenance as OPL-indexable refs only; "
            "these refs do not define runtime dependency, source body ownership, or publication authority."
        ),
        source_provenance_ref={
            "surface_kind": "source_provenance",
            "ref": "docs/references/med-deepscientist/source_provenance.json",
        },
        historical_fixture_ref={
            "surface_kind": "historical_fixture_ref",
            "ref": "fixtures/med-deepscientist/parity/",
        },
        explicit_archive_import_ref={
            "surface_kind": "explicit_archive_import_ref",
            "command": "uv run python -m med_autoscience.cli backend-audit --mode archive-import",
        },
        parity_oracle_ref={
            "surface_kind": "parity_oracle_ref",
            "ref": "program:med_deepscientist_retained_capability_parity",
        },
        authority_boundary=[
            "opl_provider_runtime_is_default_generic_owner",
            "source_refs_do_not_define_runtime_dependency",
            "archive_import_is_explicit_one_way_provenance",
            "opl_projection_reads_refs_only",
        ],
        capability_classification="source_provenance_only",
        recommended_audit_command="uv run python -m med_autoscience.cli backend-audit",
    )


def build_product_entry_manifest(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    opl_production_proof_ref: str | Path | None = None,
) -> dict[str, Any]:
    mainline_payload = mainline_status.read_mainline_status()
    mainline_snapshot = _mainline_snapshot()
    build_doctor_report_fn = _controller_override("build_doctor_report", build_doctor_report)
    build_user_interaction_contract_fn = _controller_override(
        "_build_user_interaction_contract",
        _build_user_interaction_contract,
    )
    build_family_product_entry_orchestration = _controller_override(
        "_build_shared_family_product_entry_orchestration",
        _build_shared_family_product_entry_orchestration,
    )
    build_family_product_entry_manifest = _controller_override(
        "_build_shared_family_product_entry_manifest",
        _build_shared_family_product_entry_manifest,
    )
    validate_product_entry_manifest_contract = _controller_override(
        "_validate_product_entry_manifest_contract",
        _validate_product_entry_manifest_contract,
    )
    doctor_report = build_doctor_report_fn(profile)
    product_entry_preflight = _build_product_entry_preflight(
        doctor_report=doctor_report,
        profile_ref=profile_ref,
    )
    domain_entry_contract = _build_domain_entry_contract()
    user_interaction_contract = build_user_interaction_contract_fn()
    _validate_domain_entry_contract_shape(
        domain_entry_contract,
        context="product_entry_manifest.domain_entry_contract",
    )
    _validate_user_interaction_contract_shape(
        user_interaction_contract,
        context="product_entry_manifest.user_interaction_contract",
    )
    profile_arg = _profile_arg(profile_ref)
    prefix = _command_prefix(profile_ref)
    workspace_root = str(profile.workspace_root)
    action_catalog = _build_mas_action_catalog(profile_ref=profile_ref)
    manifest_shell_surfaces = _build_manifest_shell_surfaces(
        prefix=prefix,
        profile_arg=profile_arg,
        action_catalog=action_catalog,
        mainline_payload=mainline_payload,
        mainline_snapshot=mainline_snapshot,
        build_family_product_entry_orchestration=build_family_product_entry_orchestration,
    )
    product_entry_shell = manifest_shell_surfaces["product_entry_shell"]
    shared_handoff = manifest_shell_surfaces["shared_handoff"]
    operator_loop_actions = manifest_shell_surfaces["operator_loop_actions"]
    family_orchestration = manifest_shell_surfaces["family_orchestration"]
    progress_projection_command = manifest_shell_surfaces["progress_projection_command"]
    product_entry_guardrails = _build_product_entry_guardrails(
        profile=profile,
        profile_ref=profile_ref,
    )
    phase2_user_product_loop = _build_phase2_user_product_loop(
        profile=profile,
        profile_ref=profile_ref,
    )
    phase3_clearance_lane = _build_phase3_clearance_lane(
        profile=profile,
        profile_ref=profile_ref,
    )
    phase4_backend_deconstruction = _build_phase4_backend_deconstruction()
    source_provenance = _build_source_provenance_refs_surface()
    phase5_platform_target = _build_phase5_platform_target()
    product_entry_quickstart = manifest_shell_surfaces["product_entry_quickstart"]
    product_entry_start = manifest_shell_surfaces["product_entry_start"]
    product_entry_overview = manifest_shell_surfaces["product_entry_overview"]
    product_entry_readiness = manifest_shell_surfaces["product_entry_readiness"]
    managed_runtime_contract = _build_managed_runtime_contract(
        domain_owner=TARGET_DOMAIN_ID,
        executor_owner=CONTROLLED_BACKEND_EXECUTOR_OWNER,
        supervision_status_surface="study_progress",
        attention_queue_surface="workspace_cockpit",
        recovery_contract_surface="progress_projection",
    )
    runtime = {
        "runtime_owner": MAS_RUNTIME_OWNER,
        "domain_owner": TARGET_DOMAIN_ID,
        "executor_owner": CONTROLLED_BACKEND_EXECUTOR_OWNER,
        "runtime_substrate": MAS_RUNTIME_SUBSTRATE,
        "opl_runtime_ref": profile.opl_runtime_ref,
        "runtime_root": str(profile.runtime_root),
        "hermes_home_root": str(profile.hermes_home_root),
    }
    product_entry_surface = manifest_shell_surfaces["product_entry_surface"]
    operator_loop_surface = manifest_shell_surfaces["operator_loop_surface"]
    repo_mainline = {
        "program_id": mainline_snapshot.get("program_id"),
        "current_stage_id": mainline_snapshot.get("current_stage_id"),
        "current_stage_status": mainline_snapshot.get("current_stage_status"),
        "current_stage_summary": mainline_snapshot.get("current_stage_summary"),
        "current_program_phase_id": mainline_snapshot.get("current_program_phase_id"),
        "current_program_phase_status": mainline_snapshot.get("current_program_phase_status"),
        "current_program_phase_summary": mainline_snapshot.get("current_program_phase_summary"),
        "next_focus": list(mainline_snapshot.get("next_focus") or []),
    }
    single_project_boundary = dict(mainline_snapshot.get("single_project_boundary") or {})
    capability_owner_boundary = dict(mainline_snapshot.get("capability_owner_boundary") or {})
    product_entry_status = manifest_shell_surfaces["product_entry_status"]
    runtime_inventory = _build_runtime_inventory_surface(
        profile=profile,
        runtime=runtime,
        managed_runtime_contract=managed_runtime_contract,
        product_entry_preflight=product_entry_preflight,
        operator_loop_surface=operator_loop_surface,
    )
    task_lifecycle = _build_task_lifecycle_surface(
        repo_mainline=repo_mainline,
        product_entry_status=product_entry_status,
        product_entry_readiness=product_entry_readiness,
        family_orchestration=family_orchestration,
        operator_loop_surface=operator_loop_surface,
        product_entry_shell=product_entry_shell,
    )
    session_continuity = _build_session_continuity_surface(
        runtime=runtime,
        product_entry_preflight=product_entry_preflight,
        family_orchestration=family_orchestration,
        product_entry_shell=product_entry_shell,
        task_lifecycle=task_lifecycle,
        progress_projection_command=progress_projection_command,
    )
    progress_projection = _build_progress_projection_surface(
        profile=profile,
        repo_mainline=repo_mainline,
        product_entry_status=product_entry_status,
        product_entry_preflight=product_entry_preflight,
        product_entry_readiness=product_entry_readiness,
        family_orchestration=family_orchestration,
        operator_loop_surface=operator_loop_surface,
        product_entry_shell=product_entry_shell,
        progress_projection_command=progress_projection_command,
    )
    artifact_inventory = _build_artifact_inventory_surface(
        profile=profile,
        progress_projection=progress_projection,
        product_entry_shell=product_entry_shell,
        progress_projection_command=progress_projection_command,
    )
    opl_family_persistence_lifecycle_owner_route_adoption = build_product_entry_adoption_projection(
        workspace_root=profile.workspace_root,
    )
    family_stage_control_plane = build_family_stage_control_plane(
        family_action_catalog=action_catalog,
    )
    family_stage_control_plane_descriptor = dict(
        opl_family_persistence_lifecycle_owner_route_adoption["payload"]["family_stage_control_plane_descriptor"]
    )
    ars_learning_projection = build_ars_learning_projection()
    stage_quality_pack_contract = build_stage_quality_pack_contract()
    domain_memory_descriptor = build_domain_memory_descriptor()
    persistence_policy = _build_family_persistence_policy_surface(
        adoption=opl_family_persistence_lifecycle_owner_route_adoption,
        progress_projection=progress_projection,
        artifact_inventory=artifact_inventory,
    )
    lifecycle_ledger = _build_family_lifecycle_ledger_surface(
        adoption=opl_family_persistence_lifecycle_owner_route_adoption,
        session_continuity=session_continuity,
    )
    owner_route = _build_family_owner_route_surface(
        adoption=opl_family_persistence_lifecycle_owner_route_adoption,
        family_orchestration=family_orchestration,
        product_entry_shell=product_entry_shell,
        progress_projection=progress_projection,
        artifact_inventory=artifact_inventory,
    )
    opl_provider_ready_contract = opl_provider_ready_adapter.build_opl_provider_ready_contract(
        profile=profile,
        profile_ref=profile_ref,
        allowed_task_kinds=(
            "domain_route/owner-handoff",
            "paper_autonomy/repair-recheck",
            "paper_autonomy/ai-reviewer-recheck",
            "publication_aftercare/analysis-queue-progress",
            "publication_aftercare/reviewer-refresh",
            "paper_autonomy/gate-replay",
            "paper_autonomy/route-decision",
            "safe_reconcile/dry-run",
            "study_progress/read",
            "status/read",
            "notification/receipt",
        ),
        opl_production_proof=opl_provider_ready_adapter.load_opl_production_proof(
            opl_production_proof_ref
        ),
        opl_production_proof_ref=opl_production_proof_ref,
    )
    provider_guarded_soak_read_model = opl_provider_ready_contract["provider_guarded_soak_read_model"]
    provider_residency_read_model = opl_provider_ready_contract["provider_residency_read_model"]
    standard_domain_agent_skeleton = (
        opl_provider_ready_adapter.build_standard_domain_agent_skeleton_surface()
    )
    workspace_runtime_evidence_receipt = opl_provider_ready_contract["workspace_runtime_evidence_receipt"]
    functional_closure_status_projection = (
        opl_provider_ready_adapter.build_functional_closure_status_projection(
            provider_residency_read_model=provider_residency_read_model,
            provider_guarded_soak_read_model=provider_guarded_soak_read_model,
            managed_temporal_state_consistency=(
                opl_provider_ready_contract["managed_temporal_state_consistency"]
            ),
            owner_receipt_contract=opl_provider_ready_contract["owner_receipt_contract"],
            lifecycle_guarded_apply_proof=opl_provider_ready_contract["lifecycle_guarded_apply_proof"],
            workspace_runtime_evidence_receipt=workspace_runtime_evidence_receipt,
            legacy_retirement_tombstone_proof=(
                opl_provider_ready_contract["legacy_retirement_tombstone_proof"]
            ),
            standard_domain_agent_skeleton=standard_domain_agent_skeleton,
            domain_memory_descriptor=domain_memory_descriptor,
        )
    )
    skill_catalog = _build_skill_catalog_surface(
        runtime=runtime,
        family_orchestration=family_orchestration,
        session_continuity=session_continuity,
        progress_projection=progress_projection,
        artifact_inventory=artifact_inventory,
        product_entry_status=product_entry_status,
        domain_entry_contract=domain_entry_contract,
        product_entry_shell=product_entry_shell, skill_catalog_command=_json_surface_command(f"{prefix} skill-catalog --profile {profile_arg}"),
        action_catalog=action_catalog,
    )
    automation = _build_automation_surface(
        profile=profile,
        profile_ref=profile_ref,
        product_entry_status=product_entry_status,
    )

    payload = build_family_product_entry_manifest(
        manifest_kind=PRODUCT_ENTRY_MANIFEST_KIND,
        target_domain_id=TARGET_DOMAIN_ID,
        formal_entry={
            "default": "CLI",
            "supported_protocols": ["MCP"],
            "internal_surface": "controller",
        },
        workspace_locator={
            "workspace_surface_kind": "med_autoscience_workspace_profile",
            "profile_name": profile.name,
            "workspace_root": workspace_root,
            "profile_ref": str(Path(profile_ref).expanduser().resolve()) if profile_ref is not None else None,
        },
        runtime=runtime,
        managed_runtime_contract=managed_runtime_contract,
        repo_mainline=repo_mainline,
        product_entry_status=product_entry_status,
        product_entry_surface=product_entry_surface,
        operator_loop_surface=operator_loop_surface,
        operator_loop_actions=operator_loop_actions,
        recommended_shell="workspace_cockpit",
        recommended_command=product_entry_shell["workspace_cockpit"]["command"],
        product_entry_shell=product_entry_shell,
        shared_handoff=shared_handoff,
        runtime_inventory=runtime_inventory,
        task_lifecycle=task_lifecycle,
        persistence_policy=persistence_policy,
        lifecycle_ledger=lifecycle_ledger,
        owner_route=owner_route,
        session_continuity=session_continuity,
        progress_projection=progress_projection,
        artifact_inventory=artifact_inventory,
        skill_catalog=skill_catalog,
        automation=automation,
        product_entry_start=product_entry_start,
        product_entry_overview=product_entry_overview,
        product_entry_preflight=product_entry_preflight,
        product_entry_readiness=product_entry_readiness,
        product_entry_quickstart=product_entry_quickstart,
        family_orchestration=family_orchestration,
        remaining_gaps=list(mainline_payload.get("remaining_gaps") or []),
        schema_ref=PRODUCT_ENTRY_MANIFEST_SCHEMA_REF,
        domain_entry_contract=domain_entry_contract,
        user_interaction_contract=user_interaction_contract,
        notes=[
            "This manifest freezes the current MAS repo-tracked research product-entry shell only.",
            "It does not include the display / paper-figure asset line.",
            "It does not claim that a mature standalone medical frontend is already landed.",
        ],
        extra_payload={
            "schema_version": SCHEMA_VERSION,
            "family_action_catalog": action_catalog,
            "single_project_boundary": single_project_boundary,
            "capability_owner_boundary": capability_owner_boundary,
            "executor_defaults": {
                "default_executor_name": "codex_cli",
                "default_executor_mode": "autonomous",
                "default_model": "inherit_local_codex_default",
                "default_reasoning_effort": "inherit_local_codex_default",
                "executor_labels": {
                    "codex_cli": "Codex CLI",
                    "hermes_agent": "Hermes-Agent",
                },
                "executor_statuses": {
                    "codex_cli": "default",
                    "hermes_agent": "experimental",
                },
                "chat_completion_only_executor_forbidden": True,
                "hermes_agent_requires_full_agent_loop": True,
                "current_backend_chain": [
                    "med_autoscience domain surfaces -> MAS owner receipts / artifact authority refs / quality verdict refs",
                    "generic runtime/provider context -> OPL current_control_state refs-only handoff",
                    "historical med_deepscientist fixture/provenance refs only",
                ],
                "optional_executor_proofs": [
                    {
                        "executor_kind": "hermes_agent",
                        "entrypoint": "explicit Hermes-Agent proof lane for historical provenance / parity intake only",
                        "requires_full_agent_loop": True,
                        "default_model": "inherit_local_hermes_default",
                        "default_reasoning_effort": "inherit_local_hermes_default",
                    }
                ],
            },
            "phase2_user_product_loop": phase2_user_product_loop,
            "product_entry_guardrails": product_entry_guardrails,
            "phase3_clearance_lane": phase3_clearance_lane,
            "phase4_backend_deconstruction": phase4_backend_deconstruction,
            "source_provenance": source_provenance,
            "phase5_platform_target": phase5_platform_target,
            "product_positioning": _build_product_positioning(),
            "functional_consumer_boundary": consumer_migration.build_functional_consumer_boundary(),
            "opl_family_persistence_lifecycle_owner_route_adoption": (
                opl_family_persistence_lifecycle_owner_route_adoption
            ),
            "opl_provider_ready_contract": opl_provider_ready_contract,
            "opl_lifecycle_inventory": opl_provider_ready_contract["lifecycle_inventory"],
            "opl_unique_control_plane_handoff": (
                opl_provider_ready_contract["opl_unique_control_plane_handoff"]
            ),
            "owner_receipt_contract": opl_provider_ready_contract["owner_receipt_contract"],
            "domain_owner_receipt_contract": opl_provider_ready_contract["owner_receipt_contract"],
            "lifecycle_apply_requests": opl_provider_ready_contract["lifecycle_apply_requests"],
            "lifecycle_guarded_apply_proof": opl_provider_ready_contract["lifecycle_guarded_apply_proof"],
            "managed_temporal_state_consistency": (
                opl_provider_ready_contract["managed_temporal_state_consistency"]
            ),
            "legacy_retirement_tombstone_proof": (
                opl_provider_ready_contract["legacy_retirement_tombstone_proof"]
            ),
            "opl_domain_agent_skeleton_mapping": opl_provider_ready_contract["domain_agent_skeleton_mapping"],
            "standard_domain_agent_skeleton": standard_domain_agent_skeleton,
            "workspace_runtime_artifact_root_locator": (
                opl_provider_ready_contract["workspace_runtime_artifact_root_locator"]
            ),
            "workspace_runtime_evidence_receipt": (
                workspace_runtime_evidence_receipt
            ),
            "mas_functional_closure_status_projection": functional_closure_status_projection,
            "stage_quality_pack_contract": stage_quality_pack_contract,
            "stage_skill_surface_projection": build_stage_skill_surface_projection(),
            "ars_learning_projection": ars_learning_projection,
            "provider_guarded_soak_read_model": provider_guarded_soak_read_model,
            "provider_residency_read_model": provider_residency_read_model,
            "domain_memory_descriptor": domain_memory_descriptor,
            "family_stage_control_plane_descriptor": family_stage_control_plane_descriptor,
            "family_transition_spec_descriptor": (
                study_domain_transition_table.build_family_transition_spec_descriptor()
            ),
            "family_stage_control_plane": family_stage_control_plane,
        },
    )
    validate_product_entry_manifest_contract(payload)
    return payload


def build_skill_catalog(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
) -> dict[str, Any]:
    manifest = build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    skill_catalog = dict(manifest.get("skill_catalog") or {})
    if not skill_catalog:
        raise ValueError("product entry manifest 缺少 skill_catalog。")
    recommended_shell = _non_empty_text(manifest.get("recommended_shell"))
    if recommended_shell is not None:
        skill_catalog["recommended_shell"] = recommended_shell
    recommended_command = _non_empty_text(manifest.get("recommended_command"))
    if recommended_command is not None:
        skill_catalog["recommended_command"] = recommended_command
    skill_catalog["manifest_command"] = (
        f"{_command(profile_ref, 'product-entry-manifest', '--profile', _profile_arg(profile_ref))} --format json"
    )
    return skill_catalog


def build_product_entry_status(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
) -> dict[str, Any]:
    build_product_entry_manifest_fn = _controller_override("build_product_entry_manifest", build_product_entry_manifest)
    read_workspace_cockpit_fn = _controller_override("read_workspace_cockpit", read_workspace_cockpit)
    validate_product_entry_status_contract = _controller_override(
        "_validate_product_entry_status_contract",
        _validate_product_entry_status_contract,
    )
    manifest = build_product_entry_manifest_fn(
        profile=profile,
        profile_ref=profile_ref,
    )
    workspace_cockpit = read_workspace_cockpit_fn(
        profile=profile,
        profile_ref=profile_ref,
    )
    payload = _build_product_entry_status_payload(
        manifest=manifest,
        workspace_cockpit=workspace_cockpit,
        schema_version=SCHEMA_VERSION,
        product_entry_status_kind=PRODUCT_ENTRY_STATUS_KIND,
        product_entry_status_schema_ref=PRODUCT_ENTRY_STATUS_SCHEMA_REF,
    )
    validate_product_entry_status_contract(payload)
    return payload


def build_product_entry_preflight(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
) -> dict[str, Any]:
    build_doctor_report_fn = _controller_override("build_doctor_report", build_doctor_report)
    doctor_report = build_doctor_report_fn(profile)
    return _build_product_entry_preflight(
        doctor_report=doctor_report,
        profile_ref=profile_ref,
    )


def build_product_entry_start(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
) -> dict[str, Any]:
    build_product_entry_manifest_fn = _controller_override("build_product_entry_manifest", build_product_entry_manifest)
    manifest = build_product_entry_manifest_fn(
        profile=profile,
        profile_ref=profile_ref,
    )
    return dict(manifest.get("product_entry_start") or {})

__all__ = [
    name
    for name in globals()
    if not name.startswith("__")
    and name not in {"_module_reexport", "_build_product_entry_status_payload"}
]
