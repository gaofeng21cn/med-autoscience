from __future__ import annotations

import argparse

from med_autoscience.cli_public_surface import GROUPED_COMMAND_PROGS
from med_autoscience.cli_parts.live_console_commands import register_live_console_parsers
from med_autoscience.cli_parts.product_entry_parsers import register_product_entry_parsers
from med_autoscience.cli_parts.runtime_lifecycle_commands import register_runtime_lifecycle_parsers
from med_autoscience.cli_parts.runtime_storage_commands import register_runtime_storage_parsers
from med_autoscience.figure_routes import supported_required_route_help


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

    subparsers.add_parser("show-agent-entry-modes")

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

    watch_parser = subparsers.add_parser("watch")
    watch_parser.add_argument("--quest-root", type=str)
    watch_parser.add_argument("--runtime-root", type=str)
    watch_parser.add_argument("--profile", type=str)
    watch_parser.add_argument("--ensure-study-runtimes", action="store_true")
    watch_parser.add_argument("--apply-supervisor-platform-repair", action="store_true")
    watch_parser.add_argument("--apply", action="store_true")
    watch_parser.add_argument("--loop", action="store_true")
    watch_parser.add_argument("--interval-seconds", type=int, default=300)
    watch_parser.add_argument("--max-ticks", type=int)

    runtime_supervision_status_parser = subparsers.add_parser("runtime-supervision-status")
    runtime_supervision_status_parser.add_argument("--profile", required=True)
    runtime_supervision_status_parser.add_argument("--interval-seconds", type=int, default=300)

    runtime_ensure_supervision_parser = subparsers.add_parser("runtime-ensure-supervision")
    runtime_ensure_supervision_parser.add_argument("--profile", required=True)
    runtime_ensure_supervision_parser.add_argument("--interval-seconds", type=int, default=300)
    runtime_ensure_supervision_parser.add_argument("--no-trigger-now", action="store_true")
    runtime_ensure_supervision_parser.add_argument(
        "--manager",
        choices=("hermes", "systemd", "cron", "launchd", "docker"),
        default="hermes",
    )
    runtime_ensure_supervision_parser.add_argument("--write-install-proof", action="store_true")

    runtime_remove_supervision_parser = subparsers.add_parser("runtime-remove-supervision")
    runtime_remove_supervision_parser.add_argument("--profile", required=True)
    runtime_remove_supervision_parser.add_argument("--interval-seconds", type=int, default=300)

    runtime_supervisor_scan_parser = subparsers.add_parser("runtime-supervisor-scan")
    runtime_supervisor_scan_parser.add_argument("--profile", required=True)
    runtime_supervisor_scan_parser.add_argument("--studies", nargs="+")
    runtime_supervisor_scan_parser.add_argument("--apply-safe-actions", action="store_true")
    runtime_supervisor_scan_parser.add_argument("--apply-runtime-platform-repair", action="store_true")
    runtime_supervisor_scan_parser.add_argument(
        "--developer-supervisor-mode",
        choices=("internal_only", "external_observe", "developer_apply_safe"),
    )

    runtime_supervisor_consume_parser = subparsers.add_parser("runtime-supervisor-consume")
    runtime_supervisor_consume_parser.add_argument("--profile", required=True)
    runtime_supervisor_consume_parser.add_argument("--studies", nargs="+")
    runtime_supervisor_consume_parser.add_argument(
        "--mode",
        choices=("developer_apply_safe",),
        required=True,
    )
    runtime_supervisor_consume_apply = runtime_supervisor_consume_parser.add_mutually_exclusive_group(required=True)
    runtime_supervisor_consume_apply.add_argument("--dry-run", action="store_true")
    runtime_supervisor_consume_apply.add_argument("--apply", action="store_true")

    runtime_supervisor_execute_dispatch_parser = subparsers.add_parser("runtime-supervisor-execute-dispatch")
    runtime_supervisor_execute_dispatch_parser.add_argument("--profile", required=True)
    runtime_supervisor_execute_dispatch_parser.add_argument("--studies", nargs="+")
    runtime_supervisor_execute_dispatch_parser.add_argument("--action-types", nargs="+")
    runtime_supervisor_execute_dispatch_parser.add_argument(
        "--mode",
        choices=("developer_apply_safe",),
        required=True,
    )
    runtime_supervisor_execute_dispatch_apply = runtime_supervisor_execute_dispatch_parser.add_mutually_exclusive_group(required=True)
    runtime_supervisor_execute_dispatch_apply.add_argument("--dry-run", action="store_true")
    runtime_supervisor_execute_dispatch_apply.add_argument("--apply", action="store_true")

    runtime_supervisor_reconcile_parser = subparsers.add_parser("runtime-supervisor-reconcile")
    runtime_supervisor_reconcile_parser.add_argument("--profile", required=True)
    runtime_supervisor_reconcile_parser.add_argument("--studies", nargs="+")
    runtime_supervisor_reconcile_parser.add_argument(
        "--mode",
        choices=("developer_apply_safe",),
        required=True,
    )
    runtime_supervisor_reconcile_apply = runtime_supervisor_reconcile_parser.add_mutually_exclusive_group(required=True)
    runtime_supervisor_reconcile_apply.add_argument("--dry-run", action="store_true")
    runtime_supervisor_reconcile_apply.add_argument("--apply", action="store_true")

    runtime_supervisor_refresh_controller_decisions_parser = subparsers.add_parser(
        "runtime-supervisor-refresh-controller-decisions"
    )
    runtime_supervisor_refresh_controller_decisions_parser.add_argument("--profile", required=True)
    runtime_supervisor_refresh_controller_decisions_parser.add_argument("--studies", nargs="+", required=True)
    runtime_supervisor_refresh_controller_decisions_parser.add_argument(
        "--mode",
        choices=("developer_apply_safe",),
        required=True,
    )
    runtime_supervisor_refresh_controller_decisions_apply = (
        runtime_supervisor_refresh_controller_decisions_parser.add_mutually_exclusive_group(required=True)
    )
    runtime_supervisor_refresh_controller_decisions_apply.add_argument("--dry-run", action="store_true")
    runtime_supervisor_refresh_controller_decisions_apply.add_argument("--apply", action="store_true")

    workspace_monolith_migrate_parser = subparsers.add_parser("workspace-monolith-migrate")
    workspace_monolith_migrate_parser.add_argument("--profile", required=True)
    workspace_monolith_migrate_mode = workspace_monolith_migrate_parser.add_mutually_exclusive_group(required=True)
    workspace_monolith_migrate_mode.add_argument("--dry-run", action="store_true")
    workspace_monolith_migrate_mode.add_argument("--apply", action="store_true")

    paper_autonomy_stability_evidence_parser = subparsers.add_parser("paper-autonomy-stability-evidence")
    paper_autonomy_stability_evidence_parser.add_argument("--yang-root", default="/Users/gaofeng/workspace/Yang")
    paper_autonomy_stability_evidence_parser.add_argument("--profiles", nargs="+")
    paper_autonomy_stability_evidence_parser.add_argument("--studies", nargs="+")

    study_state_matrix_parser = subparsers.add_parser("study-state-matrix")
    study_state_matrix_parser.add_argument("--profile", required=True)
    study_state_matrix_parser.add_argument("--studies", nargs="+")
    study_state_matrix_parser.add_argument("--entry-mode", type=str)
    study_state_matrix_parser.add_argument("--format", choices=("json", "markdown"), default="json")

    register_runtime_lifecycle_parsers(subparsers)
    register_runtime_storage_parsers(subparsers)
    register_live_console_parsers(subparsers)

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

    recommend_aris_sidecar_parser = subparsers.add_parser("recommend-aris-sidecar")
    recommend_aris_sidecar_parser.add_argument("--quest-root", required=True)
    recommend_aris_sidecar_parser.add_argument("--payload-file", type=str)
    recommend_aris_sidecar_parser.add_argument("--payload-json", type=str)

    provision_aris_sidecar_parser = subparsers.add_parser("provision-aris-sidecar")
    provision_aris_sidecar_parser.add_argument("--quest-root", required=True)
    provision_aris_sidecar_parser.add_argument("--payload-file", type=str)
    provision_aris_sidecar_parser.add_argument("--payload-json", type=str)

    import_aris_sidecar_parser = subparsers.add_parser("import-aris-sidecar")
    import_aris_sidecar_parser.add_argument("--quest-root", required=True)

    recommend_sidecar_parser = subparsers.add_parser("recommend-sidecar")
    recommend_sidecar_parser.add_argument("--provider", required=True)
    recommend_sidecar_parser.add_argument("--quest-root", required=True)
    recommend_sidecar_parser.add_argument("--payload-file", type=str)
    recommend_sidecar_parser.add_argument("--payload-json", type=str)
    recommend_sidecar_parser.add_argument("--instance-id", type=str)

    provision_sidecar_parser = subparsers.add_parser("provision-sidecar")
    provision_sidecar_parser.add_argument("--provider", required=True)
    provision_sidecar_parser.add_argument("--quest-root", required=True)
    provision_sidecar_parser.add_argument("--payload-file", type=str)
    provision_sidecar_parser.add_argument("--payload-json", type=str)
    provision_sidecar_parser.add_argument("--instance-id", type=str)

    import_sidecar_parser = subparsers.add_parser("import-sidecar")
    import_sidecar_parser.add_argument("--provider", required=True)
    import_sidecar_parser.add_argument("--quest-root", required=True)
    import_sidecar_parser.add_argument("--instance-id", type=str)

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

    medical_literature_audit_parser = subparsers.add_parser("medical-literature-audit")
    medical_literature_audit_parser.add_argument("--quest-root", required=True)
    medical_literature_audit_parser.add_argument("--apply", action="store_true")

    medical_reporting_audit_parser = subparsers.add_parser("medical-reporting-audit")
    medical_reporting_audit_parser.add_argument("--quest-root", required=True)
    medical_reporting_audit_parser.add_argument("--apply", action="store_true")

    governance_report_parser = subparsers.add_parser("control-plane-governance-report")
    governance_report_parser.add_argument("--workspace-root", action="append", required=True)
    governance_report_parser.add_argument("--markdown", action="store_true")
    governance_report_parser.add_argument("--deep", action="store_true")
    governance_report_parser.add_argument("--max-files", type=int)
    governance_report_parser.add_argument("--max-seconds", type=float)

    backfill_apply_parser = subparsers.add_parser("control-plane-backfill-apply")
    backfill_apply_parser.add_argument("--workspace-root", action="append", required=True)
    backfill_apply_parser.add_argument("--apply", action="store_true")
    backfill_apply_parser.add_argument("--control-plane-snapshot-json")
    backfill_apply_parser.add_argument("--control-plane-snapshot-file")

    safe_cache_cleanup_apply_parser = subparsers.add_parser("control-plane-safe-cache-cleanup-apply")
    safe_cache_cleanup_apply_parser.add_argument("--workspace-root", action="append", required=True)
    safe_cache_cleanup_apply_parser.add_argument("--apply", action="store_true")
    safe_cache_cleanup_apply_parser.add_argument("--control-plane-snapshot-json")
    safe_cache_cleanup_apply_parser.add_argument("--control-plane-snapshot-file")
    safe_cache_cleanup_apply_parser.add_argument("--retention-report-json")
    safe_cache_cleanup_apply_parser.add_argument("--retention-report-file")

    migration_audit_parser = subparsers.add_parser("control-plane-migration-audit")
    migration_audit_parser.add_argument("--workspace-root", action="append", required=True)

    cleanup_apply_parser = subparsers.add_parser("control-plane-cleanup-apply")
    cleanup_apply_parser.add_argument("--workspace-root", action="append", required=True)
    cleanup_apply_parser.add_argument("--apply", action="store_true")
    cleanup_apply_parser.add_argument("--control-plane-snapshot-json")
    cleanup_apply_parser.add_argument("--control-plane-snapshot-file")
    cleanup_apply_parser.add_argument("--retention-report-json")
    cleanup_apply_parser.add_argument("--retention-report-file")

    lifecycle_report_parser = subparsers.add_parser("control-plane-lifecycle-report")
    lifecycle_report_parser.add_argument("--workspace-root", action="append", required=True)
    lifecycle_report_parser.add_argument("--markdown", action="store_true")
    lifecycle_report_parser.add_argument("--deep", action="store_true")
    lifecycle_report_parser.add_argument("--max-files", type=int)
    lifecycle_report_parser.add_argument("--max-seconds", type=float)

    continuous_soak_summary_parser = subparsers.add_parser("control-plane-continuous-soak-summary")
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

    subparsers.add_parser("ensure-study-runtime-analysis-bundle")

    ensure_study_runtime_parser = subparsers.add_parser("ensure-study-runtime")
    ensure_study_runtime_parser.add_argument("--profile", required=True)
    ensure_study_runtime_parser.add_argument("--study-id", type=str)
    ensure_study_runtime_parser.add_argument("--study-root", type=str)
    ensure_study_runtime_parser.add_argument("--entry-mode", type=str)
    ensure_study_runtime_parser.add_argument("--allow-stopped-relaunch", action="store_true")
    ensure_study_runtime_parser.add_argument("--explicit-user-wakeup", action="store_true")
    ensure_study_runtime_parser.add_argument("--force", action="store_true")
    pause_study_runtime_parser = subparsers.add_parser("pause-study-runtime")
    pause_study_runtime_parser.add_argument("--profile", required=True)
    pause_study_runtime_parser.add_argument("--study-id", type=str)
    pause_study_runtime_parser.add_argument("--study-root", type=str)
    pause_study_runtime_parser.add_argument("--entry-mode", type=str)
    pause_study_runtime_parser.add_argument("--force", action="store_true")
    study_runtime_status_parser = subparsers.add_parser("study-runtime-status")
    study_runtime_status_parser.add_argument("--profile", required=True)
    study_runtime_status_parser.add_argument("--study-id", type=str)
    study_runtime_status_parser.add_argument("--study-root", type=str)
    study_runtime_status_parser.add_argument("--entry-mode", type=str)
    study_runtime_status_parser.add_argument("--format", choices=("json",), default="json")
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
    study_cycle_profiler.add_cli_parser(subparsers)
    quality_repair_batch_parser = subparsers.add_parser("quality-repair-batch")
    quality_repair_batch_parser.add_argument("--profile", required=True)
    quality_repair_batch_parser.add_argument("--study-id", type=str)
    quality_repair_batch_parser.add_argument("--study-root", type=str)
    quality_repair_batch_parser.add_argument("--quest-id", type=str)
    ai_reviewer_eval_parser = subparsers.add_parser("materialize-ai-reviewer-publication-eval")
    ai_reviewer_eval_parser.add_argument("--profile", required=True)
    ai_reviewer_eval_parser.add_argument("--study-id", type=str)
    ai_reviewer_eval_parser.add_argument("--study-root", type=str)
    ai_reviewer_eval_parser.add_argument("--entry-mode", type=str)
    ai_reviewer_eval_parser.add_argument("--payload-file", type=str)
    ai_reviewer_eval_parser.add_argument("--payload-json", type=str)
    workspace_cockpit_parser = subparsers.add_parser("workspace-cockpit")
    workspace_cockpit_parser.add_argument("--profile", required=True)
    workspace_cockpit_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    progress_portal_parser = subparsers.add_parser("progress-portal")
    progress_portal_parser.add_argument("--profile", required=True)
    progress_portal_study = progress_portal_parser.add_mutually_exclusive_group()
    progress_portal_study.add_argument("--study-id", type=str)
    progress_portal_study.add_argument("--study-root", type=str)
    progress_portal_parser.add_argument("--entry-mode", type=str)
    progress_portal_parser.add_argument("--format", choices=("text", "json"), default="text")
    progress_portal_parser.add_argument("--open", action="store_true")
    progress_portal_parser.add_argument("--serve", action="store_true")
    progress_portal_parser.add_argument("--enable-actions", action="store_true")
    progress_portal_parser.add_argument("--host", default="127.0.0.1")
    progress_portal_parser.add_argument("--port", type=int, default=0)
    progress_portal_parser.add_argument("--interval-seconds", type=int, default=30)
    portal_console_soak_parser = subparsers.add_parser("portal-console-soak")
    portal_console_soak_parser.add_argument("--profile", required=True)
    portal_console_soak_study = portal_console_soak_parser.add_mutually_exclusive_group()
    portal_console_soak_study.add_argument("--study-id", type=str)
    portal_console_soak_study.add_argument("--study-root", type=str)
    portal_console_soak_parser.add_argument("--format", choices=("text", "json"), default="text")
    study_cycle_profiler.add_workspace_cli_parser(subparsers)
    register_product_entry_parsers(subparsers)
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

    hermes_runtime_check_parser = subparsers.add_parser("hermes-runtime-check")
    hermes_runtime_check_parser.add_argument("--profile")
    hermes_runtime_check_parser.add_argument("--hermes-agent-repo-root")
    hermes_runtime_check_parser.add_argument("--hermes-home-root")
    for command_name, prog in GROUPED_COMMAND_PROGS.items():
        choice = subparsers.choices.get(command_name)
        if choice is not None:
            choice.prog = prog
    return parser
