from __future__ import annotations

import argparse

from med_autoscience.cli_public_surface import GROUPED_COMMAND_PROGS
from med_autoscience.cli_parts.runtime_storage_commands import register_runtime_storage_parsers
from med_autoscience.cli_parts.study_action_commands import register_study_action_parsers
from med_autoscience.figure_routes import supported_required_route_help


ACTIVE_SUPERVISION_MANAGERS = ("opl",)
ACTIVE_SUPERVISION_ENSURE_MANAGERS = ("opl",)


def build_parser(*, study_cycle_profiler) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="medautosci")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor_parser = subparsers.add_parser("doctor")
    doctor_parser.add_argument("--profile", required=True)

    show_profile_parser = subparsers.add_parser("show-profile")
    show_profile_parser.add_argument("--profile", required=True)
    show_profile_parser.add_argument("--format", choices=("text", "json"), default="text")

    mainline_status_parser = subparsers.add_parser("mainline-status")
    mainline_status_parser.add_argument("--format", choices=("text", "json"), default="text")

    mainline_phase_parser = subparsers.add_parser("mainline-phase")
    mainline_phase_parser.add_argument("--phase", default="current")
    mainline_phase_parser.add_argument("--format", choices=("text", "json"), default="text")

    subparsers.add_parser("show-stage-route-contract")

    sync_agent_entry_assets_parser = subparsers.add_parser("sync-agent-entry-assets")
    sync_agent_entry_assets_parser.add_argument("--repo-root", default=".")

    preflight_parser = subparsers.add_parser("preflight-changes")
    preflight_sources = preflight_parser.add_mutually_exclusive_group(required=True)
    preflight_sources.add_argument("--files", nargs="+")
    preflight_sources.add_argument("--staged", action="store_true")
    preflight_sources.add_argument("--base-ref", type=str)
    preflight_parser.add_argument("--format", choices=("text", "json"), default="text")

    preflight_contract_report_parser = subparsers.add_parser("preflight-contract-report")
    preflight_contract_report_parser.add_argument("--format", choices=("json",), default="json")

    seed_parser = subparsers.add_parser("publication-route-memory-apply-seed")
    seed_parser.add_argument("--workspace-root", required=True)
    seed_source = seed_parser.add_mutually_exclusive_group(required=True)
    seed_source.add_argument("--seed-fixture")
    seed_source.add_argument("--seed-library")
    seed_apply_mode = seed_parser.add_mutually_exclusive_group(required=True)
    seed_apply_mode.add_argument("--apply", action="store_true")
    seed_apply_mode.add_argument("--dry-run", action="store_true")

    route_memory_inventory_parser = subparsers.add_parser("publication-route-memory-inventory")
    route_memory_inventory_parser.add_argument("--workspace-root", required=True)
    route_memory_inventory_parser.add_argument("--stage", type=str)
    route_memory_inventory_parser.add_argument("--route-family", action="append", dest="route_families")
    route_memory_inventory_parser.add_argument("--status", action="append", dest="statuses")
    route_memory_inventory_parser.add_argument("--include-card-body", action="store_true")

    stage_knowledge_packet_parser = subparsers.add_parser("stage-knowledge-packet")
    stage_knowledge_packet_parser.add_argument("--study-id", required=True)
    stage_knowledge_packet_parser.add_argument("--stage", required=True)
    stage_knowledge_packet_parser.add_argument("--study-root", required=True)
    stage_knowledge_packet_parser.add_argument("--workspace-root", required=True)
    stage_knowledge_packet_parser.add_argument("--quest-root", type=str)

    closeout_route_parser = subparsers.add_parser("stage-memory-closeout-route")
    closeout_route_parser.add_argument("--study-id", type=str)
    closeout_route_parser.add_argument("--stage", type=str)
    closeout_route_parser.add_argument("--study-root", required=True)
    closeout_route_parser.add_argument("--workspace-root", required=True)
    closeout_source = closeout_route_parser.add_mutually_exclusive_group(required=True)
    closeout_source.add_argument("--closeout-packet", type=str)
    closeout_source.add_argument("--closeout-payload", type=str)
    closeout_route_parser.add_argument("--materialize-closeout-packet", action="store_true")
    closeout_apply_mode = closeout_route_parser.add_mutually_exclusive_group(required=True)
    closeout_apply_mode.add_argument("--apply", action="store_true")
    closeout_apply_mode.add_argument("--dry-run", action="store_true")

    proof_parser = subparsers.add_parser("paper-soak-memory-proof")
    proof_parser.add_argument("--study-id", required=True)
    proof_parser.add_argument("--stage", required=True)
    proof_parser.add_argument("--study-root", required=True)
    proof_parser.add_argument("--workspace-root", required=True)

    soak_projection_parser = subparsers.add_parser("real-paper-autonomy-soak-projection")
    soak_projection_parser.add_argument("--yang-root", default="/Users/gaofeng/workspace/Yang")
    soak_projection_parser.add_argument("--profile", action="append", dest="profiles")
    soak_projection_parser.add_argument("--target-study", action="append", dest="target_studies")

    provider_proof_parser = subparsers.add_parser("real-paper-autonomy-provider-hosted-paper-proof")
    provider_proof_parser.add_argument("--yang-root", default="/Users/gaofeng/workspace/Yang")
    provider_proof_parser.add_argument("--profile", action="append", dest="profiles")
    provider_proof_parser.add_argument("--target-study", action="append", dest="target_studies")

    guarded_apply_proof_parser = subparsers.add_parser("real-paper-autonomy-guarded-apply-proof")
    guarded_apply_proof_parser.add_argument("--yang-root", default="/Users/gaofeng/workspace/Yang")
    guarded_apply_proof_parser.add_argument("--profile", action="append", dest="profiles")
    guarded_apply_proof_parser.add_argument("--target-study", action="append", dest="target_studies")

    domain_health_diagnostic_parser = subparsers.add_parser("domain-health-diagnostic")
    domain_health_diagnostic_parser.add_argument("--quest-root", type=str)
    domain_health_diagnostic_parser.add_argument("--runtime-root", type=str)
    domain_health_diagnostic_parser.add_argument("--profile", type=str)
    domain_health_diagnostic_parser.add_argument("--studies", nargs="+")
    domain_health_diagnostic_parser.add_argument("--request-opl-stage-attempts", action="store_true")
    domain_health_diagnostic_parser.add_argument("--request-opl-owner-route-reconcile", action="store_true")
    domain_health_diagnostic_apply = domain_health_diagnostic_parser.add_mutually_exclusive_group()
    domain_health_diagnostic_apply.add_argument("--dry-run", action="store_true")
    domain_health_diagnostic_apply.add_argument("--apply", action="store_true")

    domain_handler_parser = subparsers.add_parser("domain-handler")
    domain_handler_subparsers = domain_handler_parser.add_subparsers(
        dest="domain_handler_command",
        required=True,
    )
    domain_handler_export_parser = domain_handler_subparsers.add_parser("export")
    domain_handler_export_parser.add_argument("--profile", required=True)
    domain_handler_export_parser.add_argument("--opl-production-proof", type=str)
    domain_handler_export_parser.add_argument("--format", choices=("json",), default="json")
    domain_handler_dispatch_parser = domain_handler_subparsers.add_parser("dispatch")
    domain_handler_dispatch_parser.add_argument("--task", required=True)
    domain_handler_dispatch_parser.add_argument("--format", choices=("json",), default="json")
    domain_handler_dispatch_evidence_payload_parser = domain_handler_subparsers.add_parser(
        "dispatch-evidence-payload"
    )
    domain_handler_dispatch_evidence_payload_parser.add_argument("--profile", required=True)
    domain_handler_dispatch_evidence_payload_parser.add_argument("--workorder", required=True)
    domain_handler_dispatch_evidence_payload_parser.add_argument("--format", choices=("json",), default="json")
    domain_handler_stage_evidence_payload_parser = domain_handler_subparsers.add_parser(
        "stage-evidence-payload"
    )
    domain_handler_stage_evidence_payload_parser.add_argument("--profile", required=True)
    domain_handler_stage_evidence_payload_parser.add_argument("--workorder", required=True)
    domain_handler_stage_evidence_payload_parser.add_argument("--format", choices=("json",), default="json")

    owner_route_reconcile_parser = subparsers.add_parser("owner-route-reconcile")
    owner_route_reconcile_parser.add_argument("--profile", required=True)
    owner_route_reconcile_parser.add_argument("--studies", nargs="+")
    owner_route_reconcile_parser.add_argument("--apply-safe-actions", action="store_true")
    owner_route_reconcile_parser.add_argument(
        "--developer-supervisor-mode",
        choices=("internal_only", "external_observe", "developer_apply_safe"),
    )

    domain_action_request_materializer_parser = subparsers.add_parser("domain-action-request-materialize")
    domain_action_request_materializer_parser.add_argument("--profile", required=True)
    domain_action_request_materializer_parser.add_argument("--studies", nargs="+")
    domain_action_request_materializer_parser.add_argument(
        "--mode",
        choices=("developer_apply_safe",),
        required=True,
    )
    domain_action_request_materializer_apply = domain_action_request_materializer_parser.add_mutually_exclusive_group(required=True)
    domain_action_request_materializer_apply.add_argument("--dry-run", action="store_true")
    domain_action_request_materializer_apply.add_argument("--apply", action="store_true")

    domain_owner_action_dispatch_parser = subparsers.add_parser("domain-owner-action-dispatch")
    domain_owner_action_dispatch_parser.add_argument("--profile", required=True)
    domain_owner_action_dispatch_parser.add_argument("--studies", nargs="+")
    domain_owner_action_dispatch_parser.add_argument("--action-types", nargs="+")
    domain_owner_action_dispatch_parser.add_argument("--payload-file", type=str)
    domain_owner_action_dispatch_parser.add_argument("--payload-json", type=str)
    domain_owner_action_dispatch_parser.add_argument(
        "--mode",
        choices=("developer_apply_safe",),
        required=True,
    )
    domain_owner_action_dispatch_apply = domain_owner_action_dispatch_parser.add_mutually_exclusive_group(required=True)
    domain_owner_action_dispatch_apply.add_argument("--dry-run", action="store_true")
    domain_owner_action_dispatch_apply.add_argument("--apply", action="store_true")

    domain_owner_refresh_controller_decisions_parser = subparsers.add_parser(
        "domain-owner-action-refresh-controller-decisions"
    )
    domain_owner_refresh_controller_decisions_parser.add_argument("--profile", required=True)
    domain_owner_refresh_controller_decisions_parser.add_argument("--studies", nargs="+", required=True)
    domain_owner_refresh_controller_decisions_parser.add_argument(
        "--mode",
        choices=("developer_apply_safe",),
        required=True,
    )
    domain_owner_refresh_controller_decisions_apply = (
        domain_owner_refresh_controller_decisions_parser.add_mutually_exclusive_group(required=True)
    )
    domain_owner_refresh_controller_decisions_apply.add_argument("--dry-run", action="store_true")
    domain_owner_refresh_controller_decisions_apply.add_argument("--apply", action="store_true")

    stage_artifact_materialize_parser = subparsers.add_parser("stage-artifact-materialize")
    stage_artifact_materialize_parser.add_argument("--profile", required=True)
    stage_artifact_materialize_parser.add_argument("--studies", nargs="+", required=True)
    stage_artifact_materialize_parser.add_argument("--stage-id", action="append", dest="stage_ids")
    stage_artifact_materialize_mode = stage_artifact_materialize_parser.add_mutually_exclusive_group(required=True)
    stage_artifact_materialize_mode.add_argument("--dry-run", action="store_true")
    stage_artifact_materialize_mode.add_argument("--apply", action="store_true")

    readiness_owner_blocker_parser = subparsers.add_parser("medical-paper-readiness-owner-blocker")
    readiness_owner_blocker_parser.add_argument("--study-root", required=True)
    readiness_owner_blocker_parser.add_argument("--source", default="cli")
    readiness_owner_blocker_apply = readiness_owner_blocker_parser.add_mutually_exclusive_group(required=True)
    readiness_owner_blocker_apply.add_argument("--dry-run", action="store_true")
    readiness_owner_blocker_apply.add_argument("--apply", action="store_true")

    workspace_monolith_migrate_parser = subparsers.add_parser("workspace-monolith-migrate")
    workspace_monolith_migrate_parser.add_argument("--profile", required=True)
    workspace_monolith_migrate_mode = workspace_monolith_migrate_parser.add_mutually_exclusive_group(required=True)
    workspace_monolith_migrate_mode.add_argument("--dry-run", action="store_true")
    workspace_monolith_migrate_mode.add_argument("--apply", action="store_true")

    paper_authority_clean_migration_parser = subparsers.add_parser("paper-authority-clean-migration")
    paper_authority_clean_migration_parser.add_argument("--profile", required=True)
    paper_authority_clean_migration_parser.add_argument("--studies", nargs="+")
    paper_authority_clean_migration_mode = paper_authority_clean_migration_parser.add_mutually_exclusive_group(required=True)
    paper_authority_clean_migration_mode.add_argument("--dry-run", action="store_true")
    paper_authority_clean_migration_mode.add_argument("--apply", action="store_true")

    paper_clean_room_rebuild_parser = subparsers.add_parser("paper-clean-room-rebuild")
    paper_clean_room_rebuild_parser.add_argument("--profile", required=True)
    paper_clean_room_rebuild_parser.add_argument("--studies", nargs="+")
    paper_clean_room_rebuild_mode = paper_clean_room_rebuild_parser.add_mutually_exclusive_group(required=True)
    paper_clean_room_rebuild_mode.add_argument("--dry-run", action="store_true")
    paper_clean_room_rebuild_mode.add_argument("--apply", action="store_true")

    study_workspace_status_parser = subparsers.add_parser("study-workspace-status")
    study_workspace_status_parser.add_argument("--profile", required=True)
    study_workspace_status_parser.add_argument("--studies", nargs="+")
    study_workspace_status_mode = study_workspace_status_parser.add_mutually_exclusive_group(required=True)
    study_workspace_status_mode.add_argument("--dry-run", action="store_true")
    study_workspace_status_mode.add_argument("--apply", action="store_true")

    study_config_clean_migration_parser = subparsers.add_parser("study-config-clean-migration")
    study_config_clean_migration_parser.add_argument("--profile", required=True)
    study_config_clean_migration_parser.add_argument("--studies", nargs="+")
    study_config_clean_migration_mode = study_config_clean_migration_parser.add_mutually_exclusive_group(required=True)
    study_config_clean_migration_mode.add_argument("--dry-run", action="store_true")
    study_config_clean_migration_mode.add_argument("--apply", action="store_true")

    agent_lab_medical_quality_parser = subparsers.add_parser("agent-lab-medical-manuscript-quality-suite")
    agent_lab_medical_quality_parser.add_argument("--study-root", required=True)
    agent_lab_medical_quality_parser.add_argument("--reviewer-feedback-ref")
    agent_lab_medical_quality_mode = agent_lab_medical_quality_parser.add_mutually_exclusive_group(required=True)
    agent_lab_medical_quality_mode.add_argument("--dry-run", action="store_true")
    agent_lab_medical_quality_mode.add_argument("--apply", action="store_true")

    paper_autonomy_stability_evidence_parser = subparsers.add_parser("paper-autonomy-stability-evidence")
    paper_autonomy_stability_evidence_parser.add_argument("--yang-root", default="/Users/gaofeng/workspace/Yang")
    paper_autonomy_stability_evidence_parser.add_argument("--profiles", nargs="+")
    paper_autonomy_stability_evidence_parser.add_argument("--studies", nargs="+")

    subparsers.add_parser("ensure-analysis-bundle")

    study_state_matrix_parser = subparsers.add_parser("study-state-matrix")
    study_state_matrix_parser.add_argument("--profile", required=True)
    study_state_matrix_parser.add_argument("--studies", nargs="+")
    study_state_matrix_parser.add_argument("--entry-mode", type=str)
    study_state_matrix_parser.add_argument("--format", choices=("json", "markdown"), default="json")

    init_data_assets_parser = subparsers.add_parser("init-data-assets")
    init_data_assets_parser.add_argument("--workspace-root", required=True)

    data_assets_status_parser = subparsers.add_parser("data-assets-status")
    data_assets_status_parser.add_argument("--workspace-root", required=True)
    init_portfolio_memory_parser = subparsers.add_parser("init-portfolio-memory")
    init_portfolio_memory_parser.add_argument("--workspace-root", required=True)
    portfolio_memory_status_parser = subparsers.add_parser("portfolio-memory-status")
    portfolio_memory_status_parser.add_argument("--workspace-root", required=True)
    init_workspace_literature_parser = subparsers.add_parser("init-workspace-literature")
    init_workspace_literature_parser.add_argument("--workspace-root", required=True)
    workspace_literature_status_parser = subparsers.add_parser("workspace-literature-status")
    workspace_literature_status_parser.add_argument("--workspace-root", required=True)
    prepare_external_research_parser = subparsers.add_parser("prepare-external-research")
    prepare_external_research_parser.add_argument("--workspace-root", required=True)
    prepare_external_research_parser.add_argument("--as-of-date", type=str)
    external_research_status_parser = subparsers.add_parser("external-research-status")
    external_research_status_parser.add_argument("--workspace-root", required=True)
    assess_data_asset_impact_parser = subparsers.add_parser("assess-data-asset-impact")
    assess_data_asset_impact_parser.add_argument("--workspace-root", required=True)
    validate_public_registry_parser = subparsers.add_parser("validate-public-registry")
    validate_public_registry_parser.add_argument("--workspace-root", required=True)
    startup_data_readiness_parser = subparsers.add_parser("startup-data-readiness")
    startup_data_readiness_parser.add_argument("--workspace-root", required=True)
    apply_data_asset_update_parser = subparsers.add_parser("apply-data-asset-update")
    apply_data_asset_update_parser.add_argument("--workspace-root", required=True)
    apply_data_asset_update_parser.add_argument("--payload-file", type=str)
    apply_data_asset_update_parser.add_argument("--payload-json", type=str)

    diff_private_release_parser = subparsers.add_parser("diff-private-release")
    diff_private_release_parser.add_argument("--workspace-root", required=True)
    diff_private_release_parser.add_argument("--family-id", required=True)
    diff_private_release_parser.add_argument("--from-version", required=True)
    diff_private_release_parser.add_argument("--to-version", required=True)

    data_asset_gate_parser = subparsers.add_parser("data-asset-gate")
    data_asset_gate_parser.add_argument("--quest-root", required=True)
    data_asset_gate_parser.add_argument("--apply", action="store_true")

    tooluniverse_status_parser = subparsers.add_parser("tooluniverse-status")
    tooluniverse_status_parser.add_argument("--workspace-root", type=str)
    tooluniverse_status_parser.add_argument("--tooluniverse-root", type=str)

    export_parser = subparsers.add_parser("export-submission-minimal")
    export_parser.add_argument("--paper-root", required=True)
    export_parser.add_argument("--publication-profile", default="general_medical_journal")
    export_parser.add_argument("--citation-style", default="auto")

    inspection_export_parser = subparsers.add_parser("export-inspection-package")
    inspection_export_parser.add_argument("--profile", required=True)
    inspection_export_study = inspection_export_parser.add_mutually_exclusive_group(required=True)
    inspection_export_study.add_argument("--study-id", type=str)
    inspection_export_study.add_argument("--study-root", type=str)
    inspection_export_parser.add_argument("--publication-profile", type=str)
    inspection_export_parser.add_argument("--force-materialize", action="store_true")

    display_surface_parser = subparsers.add_parser("materialize-display-surface")
    display_surface_parser.add_argument("--paper-root", required=True)

    display_pack_surface_sync_parser = subparsers.add_parser("sync-display-pack-surface")
    display_pack_surface_sync_parser.add_argument("--paper-root", required=True)

    time_to_event_direct_migration_parser = subparsers.add_parser("time-to-event-direct-migration")
    time_to_event_direct_migration_parser.add_argument("--study-root", required=True)
    time_to_event_direct_migration_parser.add_argument("--paper-root", required=True)

    resolve_submission_targets_parser = subparsers.add_parser("resolve-submission-targets")
    resolve_submission_targets_parser.add_argument("--profile", type=str)
    resolve_submission_targets_parser.add_argument("--study-root", type=str)
    resolve_submission_targets_parser.add_argument("--quest-root", type=str)

    resolve_journal_shortlist_parser = subparsers.add_parser("resolve-journal-shortlist")
    resolve_journal_shortlist_parser.add_argument("--study-root", required=True, type=str)

    resolve_journal_requirements_parser = subparsers.add_parser("resolve-journal-requirements")
    resolve_journal_requirements_parser.add_argument("--study-root", required=True, type=str)
    resolve_journal_requirements_parser.add_argument("--journal-name", type=str)
    resolve_journal_requirements_parser.add_argument("--journal-slug", type=str)
    resolve_journal_requirements_parser.add_argument("--official-guidelines-url", required=True, type=str)
    resolve_journal_requirements_parser.add_argument("--publication-profile", type=str)
    resolve_journal_requirements_parser.add_argument("--requirements-file", type=str)
    resolve_journal_requirements_parser.add_argument("--requirements-json", type=str)

    materialize_journal_package_parser = subparsers.add_parser("materialize-journal-package")
    materialize_journal_package_parser.add_argument("--paper-root", required=True, type=str)
    materialize_journal_package_parser.add_argument("--study-root", required=True, type=str)
    materialize_journal_package_parser.add_argument("--journal-slug", required=True, type=str)
    materialize_journal_package_parser.add_argument("--publication-profile", type=str)
    materialize_journal_package_parser.add_argument("--confirmed-target", action="store_true")

    resolve_reference_papers_parser = subparsers.add_parser("resolve-reference-papers")
    resolve_reference_papers_parser.add_argument("--quest-root", required=True)

    export_submission_targets_parser = subparsers.add_parser("export-submission-targets")
    export_submission_targets_parser.add_argument("--paper-root", type=str)
    export_submission_targets_parser.add_argument("--profile", type=str)
    export_submission_targets_parser.add_argument("--study-root", type=str)
    export_submission_targets_parser.add_argument("--quest-root", type=str)

    delivery_inspect_parser = subparsers.add_parser("delivery-inspect")
    delivery_inspect_parser.add_argument("--profile", required=True)
    delivery_inspect_study = delivery_inspect_parser.add_mutually_exclusive_group(required=True)
    delivery_inspect_study.add_argument("--study-id", type=str)
    delivery_inspect_study.add_argument("--study-root", type=str)
    delivery_inspect_parser.add_argument("--publication-profile", type=str)
    delivery_inspect_parser.add_argument("--format", choices=("json", "markdown"), default="json")

    gate_parser = subparsers.add_parser("publication-gate")
    gate_parser.add_argument("--quest-root", required=True)
    gate_parser.add_argument("--apply", action="store_true")

    aftercare_parser = subparsers.add_parser("publication-aftercare-plan")
    aftercare_parser.add_argument("--study-root", required=True)
    aftercare_parser.add_argument("--quest-root")

    medical_literature_audit_parser = subparsers.add_parser("medical-literature-audit")
    medical_literature_audit_parser.add_argument("--quest-root", required=True)
    medical_literature_audit_parser.add_argument("--apply", action="store_true")

    medical_reporting_audit_parser = subparsers.add_parser("medical-reporting-audit")
    medical_reporting_audit_parser.add_argument("--quest-root", required=True)
    medical_reporting_audit_parser.add_argument("--apply", action="store_true")

    governance_report_parser = subparsers.add_parser("storage-governance-report")
    governance_report_parser.add_argument("--workspace-root", action="append", required=True)
    governance_report_parser.add_argument("--markdown", action="store_true")
    governance_report_parser.add_argument("--deep", action="store_true")
    governance_report_parser.add_argument("--max-files", type=int)
    governance_report_parser.add_argument("--max-seconds", type=float)

    backfill_apply_parser = subparsers.add_parser("delivery-authority-backfill-apply")
    backfill_apply_parser.add_argument("--workspace-root", action="append", required=True)
    backfill_apply_parser.add_argument("--apply", action="store_true")
    backfill_apply_parser.add_argument("--authority-snapshot-json")
    backfill_apply_parser.add_argument("--authority-snapshot-file")

    migration_audit_parser = subparsers.add_parser("workspace-authority-migration-audit")
    migration_audit_parser.add_argument("--workspace-root", action="append", required=True)

    lifecycle_report_parser = subparsers.add_parser("artifact-lifecycle-report")
    lifecycle_report_parser.add_argument("--workspace-root", action="append", required=True)
    lifecycle_report_parser.add_argument("--markdown", action="store_true")
    lifecycle_report_parser.add_argument("--deep", action="store_true")
    lifecycle_report_parser.add_argument("--max-files", type=int)
    lifecycle_report_parser.add_argument("--max-seconds", type=float)

    continuous_soak_summary_parser = subparsers.add_parser("artifact-lifecycle-continuous-soak-summary")
    continuous_soak_summary_parser.add_argument("--workspace-root", action="append", required=True)
    continuous_soak_summary_parser.add_argument("--deep", action="store_true")
    continuous_soak_summary_parser.add_argument("--max-files", type=int)
    continuous_soak_summary_parser.add_argument("--max-seconds", type=float)

    surface_parser = subparsers.add_parser("medical-publication-surface")
    surface_parser.add_argument("--quest-root", required=True)
    surface_parser.add_argument("--apply", action="store_true")
    surface_parser.add_argument("--daemon-url", default="http://127.0.0.1:20999")

    figure_loop_guard_parser = subparsers.add_parser("figure-loop-guard")
    figure_loop_guard_parser.add_argument("--quest-root", required=True)
    figure_loop_guard_parser.add_argument("--apply", action="store_true")
    figure_loop_guard_parser.add_argument("--outbox-path", type=str)
    figure_loop_guard_parser.add_argument("--daemon-url", type=str)
    figure_loop_guard_parser.add_argument("--accepted-figure", action="append", default=[])
    figure_loop_guard_parser.add_argument("--figure-ticket", action="append", default=[])
    figure_loop_guard_parser.add_argument("--required-route", action="append", default=[], help=supported_required_route_help())
    figure_loop_guard_parser.add_argument("--min-figure-mentions", type=int, default=12)
    figure_loop_guard_parser.add_argument("--min-reference-count", type=int, default=12)
    figure_loop_guard_parser.add_argument("--recent-window", type=int, default=120)
    figure_loop_guard_parser.add_argument("--source", default="medautosci-figure-loop-guard")

    delivery_parser = subparsers.add_parser("sync-study-delivery")
    delivery_parser.add_argument("--paper-root", required=True)
    delivery_parser.add_argument("--stage", choices=("submission_minimal", "finalize"), required=True)
    delivery_parser.add_argument("--publication-profile", default="general_medical_journal")
    delivery_parser.add_argument("--promote-to-final", action="store_true")

    overlay_status_parser = subparsers.add_parser("overlay-status")
    overlay_status_parser.add_argument("--quest-root", type=str)
    overlay_status_parser.add_argument("--profile", type=str)

    install_overlay_parser = subparsers.add_parser("install-medical-overlay")
    install_overlay_parser.add_argument("--quest-root", type=str)
    install_overlay_parser.add_argument("--profile", type=str)

    reapply_overlay_parser = subparsers.add_parser("reapply-medical-overlay")
    reapply_overlay_parser.add_argument("--quest-root", type=str)
    reapply_overlay_parser.add_argument("--profile", type=str)

    study_progress_parser = subparsers.add_parser("study-progress")
    study_progress_parser.add_argument("--profile", required=True)
    study_progress_parser.add_argument("--study-id", type=str)
    study_progress_parser.add_argument("--study-root", type=str)
    study_progress_parser.add_argument("--entry-mode", type=str)
    study_progress_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    open_auto_research_soak_parser = subparsers.add_parser("open-auto-research-soak")
    open_auto_research_soak_parser.add_argument("--profile", required=True)
    open_auto_research_soak_parser.add_argument("--study-id", type=str)
    open_auto_research_soak_parser.add_argument("--study-root", type=str)
    open_auto_research_soak_parser.add_argument("--entry-mode", type=str)
    open_auto_research_soak_parser.add_argument("--format", choices=("markdown", "json"), default="json")
    open_auto_research_soak_parser.add_argument("--allow-controller-writes", action="store_true")
    reconcile_study_truth_parser = subparsers.add_parser("reconcile-study-truth")
    reconcile_study_truth_parser.add_argument("--profile", required=True)
    reconcile_study_truth_parser.add_argument("--study-id", type=str)
    reconcile_study_truth_parser.add_argument("--study-root", type=str)
    reconcile_study_truth_parser.add_argument("--entry-mode", type=str)
    reconcile_runtime_health_parser = subparsers.add_parser("reconcile-runtime-health")
    reconcile_runtime_health_parser.add_argument("--profile", required=True)
    reconcile_runtime_health_parser.add_argument("--study-id", type=str)
    reconcile_runtime_health_parser.add_argument("--study-root", type=str)
    reconcile_runtime_health_parser.add_argument("--entry-mode", type=str)
    if study_cycle_profiler is not None:
        study_cycle_profiler.add_cli_parser(subparsers)
    quality_repair_batch_parser = subparsers.add_parser("quality-repair-batch")
    quality_repair_batch_parser.add_argument("--profile", required=True)
    quality_repair_batch_parser.add_argument("--study-id", type=str)
    quality_repair_batch_parser.add_argument("--study-root", type=str)
    quality_repair_batch_parser.add_argument("--quest-id", type=str)
    gate_clearing_batch_parser = subparsers.add_parser("gate-clearing-batch")
    gate_clearing_batch_parser.add_argument("--profile", required=True)
    gate_clearing_batch_parser.add_argument("--study-id", type=str)
    gate_clearing_batch_parser.add_argument("--study-root", type=str)
    gate_clearing_batch_parser.add_argument("--quest-id", type=str)
    ai_reviewer_eval_parser = subparsers.add_parser("materialize-ai-reviewer-publication-eval")
    ai_reviewer_eval_parser.add_argument("--profile", required=True)
    ai_reviewer_eval_parser.add_argument("--study-id", type=str)
    ai_reviewer_eval_parser.add_argument("--study-root", type=str)
    ai_reviewer_eval_parser.add_argument("--entry-mode", type=str)
    ai_reviewer_eval_parser.add_argument("--payload-file", type=str)
    ai_reviewer_eval_parser.add_argument("--payload-json", type=str)
    ai_reviewer_record_parser = subparsers.add_parser("materialize-ai-reviewer-publication-eval-record")
    ai_reviewer_record_parser.add_argument("--profile", required=True)
    ai_reviewer_record_parser.add_argument("--study-id", type=str)
    ai_reviewer_record_parser.add_argument("--study-root", type=str)
    ai_reviewer_record_parser.add_argument("--entry-mode", type=str)
    ai_reviewer_record_parser.add_argument("--payload-file", type=str)
    ai_reviewer_record_parser.add_argument("--payload-json", type=str)
    ai_reviewer_record_parser.add_argument(
        "--build-production-trace",
        action="store_true",
        help="Rebuild the production reviewer_operating_system trace from the current AI reviewer request/input refs before writing the record-only archive.",
    )
    ai_medical_prose_review_parser = subparsers.add_parser("materialize-ai-medical-prose-review")
    ai_medical_prose_review_parser.add_argument("--profile", required=True)
    ai_medical_prose_review_parser.add_argument("--study-id", type=str)
    ai_medical_prose_review_parser.add_argument("--study-root", type=str)
    ai_medical_prose_review_parser.add_argument("--entry-mode", type=str)
    ai_medical_prose_review_parser.add_argument("--request-ref", type=str)
    ai_medical_prose_review_parser.add_argument("--payload-file", type=str)
    ai_medical_prose_review_parser.add_argument("--payload-json", type=str)
    if study_cycle_profiler is not None:
        study_cycle_profiler.add_workspace_cli_parser(subparsers)
    register_study_action_parsers(subparsers)
    bootstrap_parser = subparsers.add_parser("bootstrap")
    bootstrap_parser.add_argument("--profile", required=True)
    init_workspace_parser = subparsers.add_parser("init-workspace")
    init_workspace_parser.add_argument("--workspace-root", required=True)
    init_workspace_parser.add_argument("--workspace-name", required=True)
    init_workspace_parser.add_argument("--default-publication-profile", default="general_medical_journal")
    init_workspace_parser.add_argument("--default-citation-style", default="AMA")
    init_workspace_parser.add_argument("--hermes-agent-repo-root")
    init_workspace_parser.add_argument("--hermes-home-root")
    init_workspace_parser.add_argument("--dry-run", action="store_true")
    init_workspace_parser.add_argument("--force", action="store_true")
    init_workspace_parser.add_argument("--with-git", action="store_true")

    backend_audit_parser = subparsers.add_parser("backend-audit")
    backend_audit_parser.add_argument("--profile", required=True)
    backend_audit_parser.add_argument("--refresh", action="store_true")
    register_runtime_storage_parsers(subparsers)

    for command_name, prog in GROUPED_COMMAND_PROGS.items():
        choice = subparsers.choices.get(command_name)
        if choice is not None:
            choice.prog = prog
    return parser
