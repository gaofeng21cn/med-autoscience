from __future__ import annotations

import argparse
import importlib
import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

from med_autoscience import dev_preflight
from med_autoscience.agent_entry.renderers import render_entry_modes_payload, sync_agent_entry_assets
from med_autoscience.cli_public_surface import (
    GROUPED_COMMAND_PROGS,
    maybe_handle_public_help,
    normalize_public_command_argv,
)
from med_autoscience.figure_routes import supported_required_route_help
from med_autoscience.overlay import installer as overlay_installer
from med_autoscience.profiles import load_profile, profile_to_dict

@lru_cache(maxsize=None)
def _load_module(module_name: str) -> Any:
    return importlib.import_module(module_name)


def _load_controller(module_name: str) -> Any:
    return _load_module(f"med_autoscience.controllers.{module_name}")


def _load_adapter(module_name: str) -> Any:
    return _load_module(f"med_autoscience.adapters.{module_name}")


def _load_analysis_bundle_controller() -> Any:
    return _load_module("med_autoscience.study_runtime_analysis_bundle")


def _load_doctor_module() -> Any:
    return _load_module("med_autoscience.doctor")


class _LazyModuleProxy:
    def __init__(self, loader) -> None:
        object.__setattr__(self, "_loader", loader)

    def __getattr__(self, name: str) -> Any:
        return getattr(object.__getattribute__(self, "_loader")(), name)


aris_sidecar_controller = _LazyModuleProxy(lambda: _load_controller("aris_sidecar"))
data_asset_gate = _LazyModuleProxy(lambda: _load_controller("data_asset_gate"))
data_assets = _LazyModuleProxy(lambda: _load_controller("data_assets"))
data_asset_updates_controller = _LazyModuleProxy(lambda: _load_controller("data_asset_updates"))
display_pack_surface_sync = _LazyModuleProxy(lambda: _load_controller("display_pack_surface_sync"))
display_surface_materialization = _LazyModuleProxy(lambda: _load_controller("display_surface_materialization"))
hermes_runtime_check = _LazyModuleProxy(lambda: _load_controller("hermes_runtime_check"))
hermes_supervision = _LazyModuleProxy(lambda: _load_controller("hermes_supervision"))
med_deepscientist_upgrade_check = _LazyModuleProxy(lambda: _load_controller("med_deepscientist_upgrade_check"))
runtime_storage_maintenance = _LazyModuleProxy(lambda: _load_controller("runtime_storage_maintenance"))
external_research_controller = _LazyModuleProxy(lambda: _load_controller("external_research"))
figure_loop_guard = _LazyModuleProxy(lambda: _load_controller("figure_loop_guard"))
journal_package_controller = _LazyModuleProxy(lambda: _load_controller("journal_package"))
journal_requirements_controller = _LazyModuleProxy(lambda: _load_controller("journal_requirements"))
journal_shortlist_controller = _LazyModuleProxy(lambda: _load_controller("journal_shortlist"))
ai_reviewer_publication_eval = _LazyModuleProxy(lambda: _load_controller("ai_reviewer_publication_eval"))
medical_literature_audit = _LazyModuleProxy(lambda: _load_controller("medical_literature_audit"))
medical_publication_surface = _LazyModuleProxy(lambda: _load_controller("medical_publication_surface"))
medical_reporting_audit = _LazyModuleProxy(lambda: _load_controller("medical_reporting_audit"))
mainline_status = _LazyModuleProxy(lambda: _load_controller("mainline_status"))
portfolio_memory_controller = _LazyModuleProxy(lambda: _load_controller("portfolio_memory"))
product_entry = _LazyModuleProxy(lambda: _load_controller("product_entry"))
publication_gate = _LazyModuleProxy(lambda: _load_controller("publication_gate"))
quality_repair_batch = _LazyModuleProxy(lambda: _load_controller("quality_repair_batch"))
reference_papers_controller = _LazyModuleProxy(lambda: _load_controller("reference_papers"))
runtime_watch = _LazyModuleProxy(lambda: _load_controller("runtime_watch"))
sidecar_provider_controller = _LazyModuleProxy(lambda: _load_controller("sidecar_provider"))
startup_data_readiness_controller = _LazyModuleProxy(lambda: _load_controller("startup_data_readiness"))
study_progress = _LazyModuleProxy(lambda: _load_controller("study_progress"))
study_cycle_profiler = _LazyModuleProxy(lambda: _load_controller("study_cycle_profiler"))
study_runtime_router = _LazyModuleProxy(lambda: _load_controller("study_runtime_router"))
study_delivery_sync = _LazyModuleProxy(lambda: _load_controller("study_delivery_sync"))
submission_minimal = _LazyModuleProxy(lambda: _load_controller("submission_minimal"))
submission_targets_controller = _LazyModuleProxy(lambda: _load_controller("submission_targets"))
time_to_event_direct_migration = _LazyModuleProxy(lambda: _load_controller("time_to_event_direct_migration"))
tooluniverse_adapter = _LazyModuleProxy(lambda: _load_adapter("tooluniverse"))
workspace_literature_controller = _LazyModuleProxy(lambda: _load_controller("workspace_literature"))
workspace_init_controller = _LazyModuleProxy(lambda: _load_controller("workspace_init"))
analysis_bundle_controller = _LazyModuleProxy(_load_analysis_bundle_controller)


def _overlay_request_from_args(args: argparse.Namespace) -> dict[str, object]:
    if getattr(args, "profile", None) and getattr(args, "quest_root", None):
        raise SystemExit("Specify at most one of --profile or --quest-root")
    if getattr(args, "profile", None):
        profile = load_profile(args.profile)
        request = _load_doctor_module().overlay_request_from_profile(profile)
        if not profile.enable_medical_overlay:
            request["skill_ids"] = tuple()
        return request
    return {
        "quest_root": Path(args.quest_root) if getattr(args, "quest_root", None) else None,
        "skill_ids": None,
    }


def _load_json_payload_from_args(args: argparse.Namespace) -> dict[str, object]:
    payload_file = getattr(args, "payload_file", None)
    payload_json = getattr(args, "payload_json", None)
    if bool(payload_file) == bool(payload_json):
        raise SystemExit("Specify exactly one of --payload-file or --payload-json")
    payload: object
    if payload_file:
        payload = json.loads(Path(payload_file).read_text(encoding="utf-8"))
    else:
        payload = json.loads(payload_json)
    if not isinstance(payload, dict):
        raise SystemExit("JSON payload must be an object")
    return payload


def _load_optional_object_payload_from_args(
    *,
    payload_file: str | None,
    payload_json: str | None,
    file_label: str,
    json_label: str,
) -> dict[str, object] | None:
    if not payload_file and not payload_json:
        return None
    if bool(payload_file) == bool(payload_json):
        raise SystemExit(f"Specify exactly one of {file_label} or {json_label}")
    payload: object
    if payload_file:
        payload = json.loads(Path(payload_file).read_text(encoding="utf-8"))
    else:
        payload = json.loads(str(payload_json))
    if not isinstance(payload, dict):
        raise SystemExit("JSON payload must be an object")
    return payload


def _parse_key_value_pairs(values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw in values:
        item = str(raw).strip()
        if not item:
            continue
        if "=" in item:
            key, note = item.split("=", 1)
        else:
            key, note = item, ""
        parsed[key.strip().upper()] = note.strip()
    return parsed


def _serialize_study_runtime_result(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return dict(result)
    study_runtime_types = _load_controller("study_runtime_types")
    if isinstance(result, study_runtime_types.StudyRuntimeStatus):
        return result.to_dict()
    raise TypeError("study runtime controller result must be dict or StudyRuntimeStatus")


def build_parser() -> argparse.ArgumentParser:
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

    watch_parser = subparsers.add_parser("watch")
    watch_parser.add_argument("--quest-root", type=str)
    watch_parser.add_argument("--runtime-root", type=str)
    watch_parser.add_argument("--profile", type=str)
    watch_parser.add_argument("--ensure-study-runtimes", action="store_true")
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

    runtime_remove_supervision_parser = subparsers.add_parser("runtime-remove-supervision")
    runtime_remove_supervision_parser.add_argument("--profile", required=True)
    runtime_remove_supervision_parser.add_argument("--interval-seconds", type=int, default=300)

    runtime_maintain_storage_parser = subparsers.add_parser("runtime-maintain-storage")
    runtime_maintain_storage_parser.add_argument("--profile", required=True)
    runtime_maintain_storage_parser.add_argument("--study-id", type=str)
    runtime_maintain_storage_parser.add_argument("--study-root", type=str)
    runtime_maintain_storage_parser.add_argument("--no-worktrees", action="store_true")
    runtime_maintain_storage_parser.add_argument("--older-than-hours", type=int, default=6)
    runtime_maintain_storage_parser.add_argument("--jsonl-max-mb", type=int, default=64)
    runtime_maintain_storage_parser.add_argument("--text-max-mb", type=int, default=16)
    runtime_maintain_storage_parser.add_argument("--event-segment-max-mb", type=int, default=64)
    runtime_maintain_storage_parser.add_argument("--no-slim-oversized-jsonl", action="store_true")
    runtime_maintain_storage_parser.add_argument("--slim-jsonl-threshold-mb", type=int, default=8)
    runtime_maintain_storage_parser.add_argument("--no-dedupe-worktrees", action="store_true")
    runtime_maintain_storage_parser.add_argument("--dedupe-worktree-min-mb", type=int, default=16)
    runtime_maintain_storage_parser.add_argument("--head-lines", type=int, default=200)
    runtime_maintain_storage_parser.add_argument("--tail-lines", type=int, default=200)
    runtime_maintain_storage_parser.add_argument("--allow-live-runtime", action="store_true")

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

    gate_parser = subparsers.add_parser("publication-gate")
    gate_parser.add_argument("--quest-root", required=True)
    gate_parser.add_argument("--apply", action="store_true")

    medical_literature_audit_parser = subparsers.add_parser("medical-literature-audit")
    medical_literature_audit_parser.add_argument("--quest-root", required=True)
    medical_literature_audit_parser.add_argument("--apply", action="store_true")

    medical_reporting_audit_parser = subparsers.add_parser("medical-reporting-audit")
    medical_reporting_audit_parser.add_argument("--quest-root", required=True)
    medical_reporting_audit_parser.add_argument("--apply", action="store_true")

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
    ensure_study_runtime_parser.add_argument("--force", action="store_true")
    study_runtime_status_parser = subparsers.add_parser("study-runtime-status")
    study_runtime_status_parser.add_argument("--profile", required=True)
    study_runtime_status_parser.add_argument("--study-id", type=str)
    study_runtime_status_parser.add_argument("--study-root", type=str)
    study_runtime_status_parser.add_argument("--entry-mode", type=str)
    study_progress_parser = subparsers.add_parser("study-progress")
    study_progress_parser.add_argument("--profile", required=True)
    study_progress_parser.add_argument("--study-id", type=str)
    study_progress_parser.add_argument("--study-root", type=str)
    study_progress_parser.add_argument("--entry-mode", type=str)
    study_progress_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
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
    study_cycle_profiler.add_workspace_cli_parser(subparsers)
    product_frontdesk_parser = subparsers.add_parser("product-frontdesk")
    product_frontdesk_parser.add_argument("--profile", required=True)
    product_frontdesk_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")

    product_preflight_parser = subparsers.add_parser("product-preflight")
    product_preflight_parser.add_argument("--profile", required=True)
    product_preflight_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")

    product_start_parser = subparsers.add_parser("product-start")
    product_start_parser.add_argument("--profile", required=True)
    product_start_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")

    product_entry_manifest_parser = subparsers.add_parser("product-entry-manifest")
    product_entry_manifest_parser.add_argument("--profile", required=True)
    product_entry_manifest_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")

    skill_catalog_parser = subparsers.add_parser("skill-catalog")
    skill_catalog_parser.add_argument("--profile", required=True)
    skill_catalog_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")

    build_product_entry_parser = subparsers.add_parser("build-product-entry")
    build_product_entry_parser.add_argument("--profile", required=True)
    build_product_entry_parser.add_argument("--study-id", type=str)
    build_product_entry_parser.add_argument("--study-root", type=str)
    build_product_entry_parser.add_argument("--entry-mode", choices=("direct", "opl-handoff"), default="direct")
    build_product_entry_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")

    launch_study_parser = subparsers.add_parser("launch-study")
    launch_study_parser.add_argument("--profile", required=True)
    launch_study_parser.add_argument("--study-id", type=str)
    launch_study_parser.add_argument("--study-root", type=str)
    launch_study_parser.add_argument("--entry-mode", type=str)
    launch_study_parser.add_argument("--allow-stopped-relaunch", action="store_true")
    launch_study_parser.add_argument("--force", action="store_true")
    launch_study_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")

    submit_study_task_parser = subparsers.add_parser("submit-study-task")
    submit_study_task_parser.add_argument("--profile", required=True)
    submit_study_task_parser.add_argument("--study-id", type=str)
    submit_study_task_parser.add_argument("--study-root", type=str)
    submit_study_task_parser.add_argument("--task-intent", required=True)
    submit_study_task_parser.add_argument("--entry-mode", type=str)
    submit_study_task_parser.add_argument("--journal-target", type=str)
    submit_study_task_parser.add_argument("--constraint", action="append", default=[])
    submit_study_task_parser.add_argument("--evidence-boundary", action="append", default=[])
    submit_study_task_parser.add_argument("--trusted-input", action="append", default=[])
    submit_study_task_parser.add_argument("--reference-paper", action="append", default=[])
    submit_study_task_parser.add_argument("--first-cycle-output", action="append", default=[])
    submit_study_task_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
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
    init_workspace_parser.add_argument("--no-git", action="store_true")

    backend_upgrade_check_parser = subparsers.add_parser("backend-upgrade-check")
    backend_upgrade_check_parser.add_argument("--profile", required=True)
    backend_upgrade_check_parser.add_argument("--refresh", action="store_true")

    hermes_runtime_check_parser = subparsers.add_parser("hermes-runtime-check")
    hermes_runtime_check_parser.add_argument("--profile")
    hermes_runtime_check_parser.add_argument("--hermes-agent-repo-root")
    hermes_runtime_check_parser.add_argument("--hermes-home-root")
    for command_name, prog in GROUPED_COMMAND_PROGS.items():
        choice = subparsers.choices.get(command_name)
        if choice is not None:
            choice.prog = prog
    return parser


def main(argv: list[str] | None = None) -> int:
    resolved_argv = list(argv) if argv is not None else list(sys.argv[1:])
    help_result = maybe_handle_public_help(resolved_argv)
    if help_result is not None:
        return help_result
    parser = build_parser()
    args = parser.parse_args(normalize_public_command_argv(resolved_argv))

    if args.command == "doctor":
        profile = load_profile(args.profile)
        doctor = _load_doctor_module()
        print(doctor.render_doctor_report(doctor.build_doctor_report(profile)), end="")
        return 0

    if args.command == "show-profile":
        profile = load_profile(args.profile)
        if args.format == "json":
            print(json.dumps(profile_to_dict(profile), ensure_ascii=False, indent=2))
        else:
            print(_load_doctor_module().render_profile(profile), end="")
        return 0

    if args.command == "mainline-status":
        result = mainline_status.read_mainline_status()
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(mainline_status.render_mainline_status_markdown(result), end="")
        return 0

    if args.command == "mainline-phase":
        result = mainline_status.read_mainline_phase_status(args.phase)
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(mainline_status.render_mainline_phase_markdown(result), end="")
        return 0

    if args.command == "show-agent-entry-modes":
        print(json.dumps(render_entry_modes_payload(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "sync-agent-entry-assets":
        result = sync_agent_entry_assets(repo_root=Path(args.repo_root))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "preflight-changes":
        input_mode = "files"
        if args.staged:
            input_mode = "staged"
        elif args.base_ref:
            input_mode = "base_ref"
        changed_files = dev_preflight.collect_changed_files(
            repo_root=Path.cwd(),
            files=list(args.files or []),
            staged=bool(args.staged),
            base_ref=args.base_ref,
        )
        result = dev_preflight.run_preflight(
            changed_files=changed_files,
            repo_root=Path.cwd(),
            input_mode=input_mode,
        )
        if args.format == "json":
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(dev_preflight.render_preflight_text(result), end="")
        return 0 if result.ok else 1

    if args.command == "backend-upgrade-check":
        profile = load_profile(args.profile)
        result = med_deepscientist_upgrade_check.run_upgrade_check(profile, refresh=bool(args.refresh))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "hermes-runtime-check":
        if not args.profile and not args.hermes_agent_repo_root:
            parser.error("Specify at least one of --profile or --hermes-agent-repo-root")
        profile = load_profile(args.profile) if args.profile else None
        result = hermes_runtime_check.run_hermes_runtime_check(
            profile=profile,
            hermes_agent_repo_root=Path(args.hermes_agent_repo_root) if args.hermes_agent_repo_root else None,
            hermes_home_root=Path(args.hermes_home_root) if args.hermes_home_root else None,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "ensure-study-runtime-analysis-bundle":
        result = analysis_bundle_controller.ensure_study_runtime_analysis_bundle()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "ensure-study-runtime":
        if bool(args.study_id) == bool(args.study_root):
            parser.error("Specify exactly one of --study-id or --study-root")
        profile = load_profile(args.profile)
        result = study_runtime_router.ensure_study_runtime(
            profile=profile,
            study_id=args.study_id,
            study_root=Path(args.study_root) if args.study_root else None,
            entry_mode=args.entry_mode,
            allow_stopped_relaunch=bool(args.allow_stopped_relaunch),
            force=bool(args.force),
            source="cli",
        )
        print(json.dumps(_serialize_study_runtime_result(result), ensure_ascii=False, indent=2))
        return 0

    if args.command == "study-runtime-status":
        if bool(args.study_id) == bool(args.study_root):
            parser.error("Specify exactly one of --study-id or --study-root")
        profile = load_profile(args.profile)
        result = study_runtime_router.study_runtime_status(
            profile=profile,
            study_id=args.study_id,
            study_root=Path(args.study_root) if args.study_root else None,
            entry_mode=args.entry_mode,
        )
        print(json.dumps(_serialize_study_runtime_result(result), ensure_ascii=False, indent=2))
        return 0

    if args.command == "study-progress":
        if bool(args.study_id) == bool(args.study_root):
            parser.error("Specify exactly one of --study-id or --study-root")
        profile = load_profile(args.profile)
        result = study_progress.read_study_progress(
            profile=profile,
            profile_ref=Path(args.profile),
            study_id=args.study_id,
            study_root=Path(args.study_root) if args.study_root else None,
            entry_mode=args.entry_mode,
        )
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(study_progress.render_study_progress_markdown(result), end="")
        return 0

    if args.command == "study-profile-cycle":
        return study_cycle_profiler.run_cli_command(
            args,
            profile_loader=load_profile,
            profile_study_cycle_runner=study_cycle_profiler.profile_study_cycle,
        )
    if args.command == "workspace-profile-cycles":
        return study_cycle_profiler.run_workspace_cli_command(
            args,
            profile_loader=load_profile,
            profile_workspace_cycles_runner=study_cycle_profiler.profile_workspace_cycles,
        )
    if args.command == "quality-repair-batch":
        if bool(args.study_id) == bool(args.study_root):
            parser.error("Specify exactly one of --study-id or --study-root")
        profile = load_profile(args.profile)
        study_root = Path(args.study_root) if args.study_root else None
        quest_id = str(args.quest_id or "").strip() or None
        if quest_id is None or study_root is None:
            status = study_runtime_router.study_runtime_status(
                profile=profile,
                study_id=args.study_id,
                study_root=study_root,
                entry_mode=None,
            )
            if study_root is None:
                resolved_study_root = status.get("study_root")
                if not isinstance(resolved_study_root, str) or not resolved_study_root.strip():
                    parser.error("Unable to resolve study_root for quality-repair-batch")
                study_root = Path(resolved_study_root)
            if quest_id is None:
                resolved_quest_id = str(status.get("quest_id") or "").strip()
                if not resolved_quest_id:
                    parser.error("Unable to resolve quest_id for quality-repair-batch")
                quest_id = resolved_quest_id
        result = quality_repair_batch.run_quality_repair_batch(
            profile=profile,
            study_id=args.study_id or study_root.name,
            study_root=study_root,
            quest_id=quest_id,
            source="cli",
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "materialize-ai-reviewer-publication-eval":
        if bool(args.study_id) == bool(args.study_root):
            parser.error("Specify exactly one of --study-id or --study-root")
        profile = load_profile(args.profile)
        result = ai_reviewer_publication_eval.materialize_ai_reviewer_publication_eval(
            profile=profile,
            study_id=args.study_id,
            study_root=Path(args.study_root) if args.study_root else None,
            entry_mode=args.entry_mode,
            record=_load_json_payload_from_args(args),
            source="cli",
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "workspace-cockpit":
        profile = load_profile(args.profile)
        result = product_entry.read_workspace_cockpit(
            profile=profile,
            profile_ref=Path(args.profile),
        )
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(product_entry.render_workspace_cockpit_markdown(result), end="")
        return 0

    if args.command == "product-frontdesk":
        profile = load_profile(args.profile)
        result = product_entry.build_product_frontdesk(
            profile=profile,
            profile_ref=Path(args.profile),
        )
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(product_entry.render_product_frontdesk_markdown(result), end="")
        return 0

    if args.command == "product-preflight":
        profile = load_profile(args.profile)
        result = product_entry.build_product_entry_preflight(
            profile=profile,
            profile_ref=Path(args.profile),
        )
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(product_entry.render_product_entry_preflight_markdown(result), end="")
        return 0

    if args.command == "product-start":
        profile = load_profile(args.profile)
        result = product_entry.build_product_entry_start(
            profile=profile,
            profile_ref=Path(args.profile),
        )
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(product_entry.render_product_entry_start_markdown(result), end="")
        return 0

    if args.command == "product-entry-manifest":
        profile = load_profile(args.profile)
        result = product_entry.build_product_entry_manifest(
            profile=profile,
            profile_ref=Path(args.profile),
        )
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(product_entry.render_product_entry_manifest_markdown(result), end="")
        return 0

    if args.command == "skill-catalog":
        profile = load_profile(args.profile)
        result = product_entry.build_skill_catalog(
            profile=profile,
            profile_ref=Path(args.profile),
        )
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(product_entry.render_skill_catalog_markdown(result), end="")
        return 0

    if args.command == "build-product-entry":
        if bool(args.study_id) == bool(args.study_root):
            parser.error("Specify exactly one of --study-id or --study-root")
        profile = load_profile(args.profile)
        result = product_entry.build_product_entry(
            profile=profile,
            profile_ref=Path(args.profile),
            study_id=args.study_id,
            study_root=Path(args.study_root) if args.study_root else None,
            direct_entry_mode=args.entry_mode,
        )
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(product_entry.render_build_product_entry_markdown(result), end="")
        return 0

    if args.command == "launch-study":
        if bool(args.study_id) == bool(args.study_root):
            parser.error("Specify exactly one of --study-id or --study-root")
        profile = load_profile(args.profile)
        result = product_entry.launch_study(
            profile=profile,
            profile_ref=Path(args.profile),
            study_id=args.study_id,
            study_root=Path(args.study_root) if args.study_root else None,
            entry_mode=args.entry_mode,
            allow_stopped_relaunch=bool(args.allow_stopped_relaunch),
            force=bool(args.force),
        )
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(product_entry.render_launch_study_markdown(result), end="")
        return 0

    if args.command == "submit-study-task":
        if bool(args.study_id) == bool(args.study_root):
            parser.error("Specify exactly one of --study-id or --study-root")
        profile = load_profile(args.profile)
        result = product_entry.submit_study_task(
            profile=profile,
            profile_ref=Path(args.profile),
            study_id=args.study_id,
            study_root=Path(args.study_root) if args.study_root else None,
            task_intent=args.task_intent,
            entry_mode=args.entry_mode,
            journal_target=args.journal_target,
            constraints=tuple(args.constraint or []),
            evidence_boundary=tuple(args.evidence_boundary or []),
            trusted_inputs=tuple(args.trusted_input or []),
            reference_papers=tuple(args.reference_paper or []),
            first_cycle_outputs=tuple(args.first_cycle_output or []),
        )
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(product_entry.render_submit_study_task_markdown(result), end="")
        return 0

    if args.command == "watch":
        if bool(args.quest_root) == bool(args.runtime_root):
            parser.error("Specify exactly one of --quest-root or --runtime-root")
        if args.quest_root and args.profile:
            parser.error("--profile is only supported with --runtime-root")
        if args.quest_root and args.ensure_study_runtimes:
            parser.error("--ensure-study-runtimes is only supported with --runtime-root")
        if args.quest_root and args.loop:
            parser.error("--loop is only supported with --runtime-root")
        if args.ensure_study_runtimes and not args.profile:
            parser.error("--ensure-study-runtimes requires --profile")
        if args.quest_root:
            result = runtime_watch.run_watch_for_quest(
                quest_root=Path(args.quest_root),
                apply=args.apply,
            )
        else:
            profile = load_profile(args.profile) if args.profile else None
            if args.loop:
                result = runtime_watch.run_watch_loop(
                    runtime_root=Path(args.runtime_root),
                    apply=args.apply,
                    profile=profile,
                    ensure_study_runtimes=bool(args.ensure_study_runtimes),
                    interval_seconds=args.interval_seconds,
                    max_ticks=args.max_ticks,
                )
            else:
                result = runtime_watch.run_watch_for_runtime(
                    runtime_root=Path(args.runtime_root),
                    apply=args.apply,
                    profile=profile,
                    ensure_study_runtimes=bool(args.ensure_study_runtimes),
                )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.loop and isinstance(result, dict) and list(result.get("tick_errors") or []):
            return 1
        return 0

    if args.command == "runtime-supervision-status":
        profile = load_profile(args.profile)
        result = hermes_supervision.read_supervision_status(
            profile=profile,
            interval_seconds=int(args.interval_seconds),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "runtime-ensure-supervision":
        profile = load_profile(args.profile)
        result = hermes_supervision.ensure_supervision(
            profile=profile,
            interval_seconds=int(args.interval_seconds),
            trigger_now=not bool(args.no_trigger_now),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "runtime-remove-supervision":
        profile = load_profile(args.profile)
        result = hermes_supervision.remove_supervision(
            profile=profile,
            interval_seconds=int(args.interval_seconds),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "runtime-maintain-storage":
        if bool(args.study_id) == bool(args.study_root):
            parser.error("Specify exactly one of --study-id or --study-root")
        profile = load_profile(args.profile)
        result = runtime_storage_maintenance.maintain_runtime_storage(
            profile=profile,
            study_id=args.study_id,
            study_root=Path(args.study_root) if args.study_root else None,
            include_worktrees=not bool(args.no_worktrees),
            older_than_seconds=max(1, int(args.older_than_hours)) * 3600,
            jsonl_max_mb=max(1, int(args.jsonl_max_mb)),
            text_max_mb=max(1, int(args.text_max_mb)),
            event_segment_max_mb=max(1, int(args.event_segment_max_mb)),
            slim_jsonl_threshold_mb=(
                None if bool(args.no_slim_oversized_jsonl) else max(1, int(args.slim_jsonl_threshold_mb))
            ),
            dedupe_worktree_min_mb=(
                None if bool(args.no_dedupe_worktrees) else max(1, int(args.dedupe_worktree_min_mb))
            ),
            head_lines=max(1, int(args.head_lines)),
            tail_lines=max(1, int(args.tail_lines)),
            allow_live_runtime=bool(args.allow_live_runtime),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "init-data-assets":
        result = data_assets.init_data_assets(workspace_root=Path(args.workspace_root))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "data-assets-status":
        result = data_assets.data_assets_status(workspace_root=Path(args.workspace_root))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "init-portfolio-memory":
        result = portfolio_memory_controller.init_portfolio_memory(workspace_root=Path(args.workspace_root))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "portfolio-memory-status":
        result = portfolio_memory_controller.portfolio_memory_status(workspace_root=Path(args.workspace_root))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "init-workspace-literature":
        result = workspace_literature_controller.init_workspace_literature(workspace_root=Path(args.workspace_root))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "workspace-literature-status":
        result = workspace_literature_controller.workspace_literature_status(workspace_root=Path(args.workspace_root))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "prepare-external-research":
        result = external_research_controller.prepare_external_research(
            workspace_root=Path(args.workspace_root),
            as_of_date=args.as_of_date,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "external-research-status":
        result = external_research_controller.external_research_status(workspace_root=Path(args.workspace_root))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "assess-data-asset-impact":
        result = data_assets.assess_data_asset_impact(workspace_root=Path(args.workspace_root))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "validate-public-registry":
        result = data_assets.validate_public_registry(workspace_root=Path(args.workspace_root))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "startup-data-readiness":
        result = startup_data_readiness_controller.startup_data_readiness(workspace_root=Path(args.workspace_root))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "apply-data-asset-update":
        result = data_asset_updates_controller.apply_data_asset_update(
            workspace_root=Path(args.workspace_root),
            payload=_load_json_payload_from_args(args),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "diff-private-release":
        result = data_assets.build_private_release_diff(
            workspace_root=Path(args.workspace_root),
            family_id=args.family_id,
            from_version=args.from_version,
            to_version=args.to_version,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "data-asset-gate":
        result = data_asset_gate.run_controller(
            quest_root=Path(args.quest_root),
            apply=args.apply,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "tooluniverse-status":
        result = tooluniverse_adapter.detect_tooluniverse(
            workspace_root=Path(args.workspace_root) if args.workspace_root else None,
            tooluniverse_root=Path(args.tooluniverse_root) if args.tooluniverse_root else None,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "export-submission-minimal":
        result = submission_minimal.create_submission_minimal_package(
            paper_root=Path(args.paper_root),
            publication_profile=args.publication_profile,
            citation_style=args.citation_style,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "materialize-display-surface":
        result = display_surface_materialization.materialize_display_surface(
            paper_root=Path(args.paper_root),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "sync-display-pack-surface":
        result = display_pack_surface_sync.sync_display_pack_surface(
            paper_root=Path(args.paper_root),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "time-to-event-direct-migration":
        result = time_to_event_direct_migration.run_time_to_event_direct_migration(
            study_root=Path(args.study_root),
            paper_root=Path(args.paper_root),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "resolve-reference-papers":
        result = reference_papers_controller.resolve_reference_papers(
            quest_root=Path(args.quest_root),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "recommend-aris-sidecar":
        result = aris_sidecar_controller.recommend_aris_sidecar(
            quest_root=Path(args.quest_root),
            payload=_load_json_payload_from_args(args),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "provision-aris-sidecar":
        result = aris_sidecar_controller.provision_aris_sidecar(
            quest_root=Path(args.quest_root),
            payload=_load_json_payload_from_args(args),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "import-aris-sidecar":
        result = aris_sidecar_controller.import_aris_sidecar_result(
            quest_root=Path(args.quest_root),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "recommend-sidecar":
        result = sidecar_provider_controller.recommend_sidecar(
            quest_root=Path(args.quest_root),
            provider_id=args.provider,
            payload=_load_json_payload_from_args(args),
            instance_id=args.instance_id,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "provision-sidecar":
        result = sidecar_provider_controller.provision_sidecar(
            quest_root=Path(args.quest_root),
            provider_id=args.provider,
            payload=_load_json_payload_from_args(args),
            instance_id=args.instance_id,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "import-sidecar":
        result = sidecar_provider_controller.import_sidecar_result(
            quest_root=Path(args.quest_root),
            provider_id=args.provider,
            instance_id=args.instance_id,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "resolve-submission-targets":
        result = submission_targets_controller.resolve_submission_targets(
            profile_path=Path(args.profile) if args.profile else None,
            study_root=Path(args.study_root) if args.study_root else None,
            quest_root=Path(args.quest_root) if args.quest_root else None,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "resolve-journal-shortlist":
        result = journal_shortlist_controller.resolve_journal_shortlist(
            study_root=Path(args.study_root),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "resolve-journal-requirements":
        result = journal_requirements_controller.resolve_journal_requirements(
            study_root=Path(args.study_root),
            journal_name=args.journal_name,
            journal_slug=args.journal_slug,
            official_guidelines_url=args.official_guidelines_url,
            publication_profile=args.publication_profile,
            requirements_payload=_load_optional_object_payload_from_args(
                payload_file=args.requirements_file,
                payload_json=args.requirements_json,
                file_label="--requirements-file",
                json_label="--requirements-json",
            ),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "materialize-journal-package":
        result = journal_package_controller.materialize_journal_package(
            paper_root=Path(args.paper_root),
            study_root=Path(args.study_root),
            journal_slug=args.journal_slug,
            publication_profile=args.publication_profile,
            confirmed_target=bool(args.confirmed_target),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "export-submission-targets":
        result = submission_targets_controller.export_submission_targets(
            paper_root=Path(args.paper_root) if args.paper_root else None,
            profile_path=Path(args.profile) if args.profile else None,
            study_root=Path(args.study_root) if args.study_root else None,
            quest_root=Path(args.quest_root) if args.quest_root else None,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "publication-gate":
        result = publication_gate.run_controller(
            quest_root=Path(args.quest_root),
            apply=args.apply,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "medical-literature-audit":
        result = medical_literature_audit.run_controller(
            quest_root=Path(args.quest_root),
            apply=args.apply,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "medical-reporting-audit":
        result = medical_reporting_audit.run_controller(
            quest_root=Path(args.quest_root),
            apply=args.apply,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "medical-publication-surface":
        result = medical_publication_surface.run_controller(
            quest_root=Path(args.quest_root),
            apply=args.apply,
            daemon_url=args.daemon_url,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "figure-loop-guard":
        result = figure_loop_guard.run_controller(
            quest_root=Path(args.quest_root),
            apply=args.apply,
            outbox_path=Path(args.outbox_path) if args.outbox_path else None,
            daemon_url=args.daemon_url,
            accepted_figures=_parse_key_value_pairs(list(args.accepted_figure or [])),
            figure_tickets=_parse_key_value_pairs(list(args.figure_ticket or [])),
            required_routes=list(args.required_route or []),
            min_figure_mentions=int(args.min_figure_mentions),
            min_reference_count=int(args.min_reference_count),
            recent_window=int(args.recent_window),
            source=str(args.source),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "sync-study-delivery":
        result = study_delivery_sync.sync_study_delivery(
            paper_root=Path(args.paper_root),
            stage=args.stage,
            publication_profile=args.publication_profile,
            promote_to_final=args.promote_to_final,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "overlay-status":
        result = overlay_installer.describe_medical_overlay(**_overlay_request_from_args(args))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "install-medical-overlay":
        result = overlay_installer.install_medical_overlay(**_overlay_request_from_args(args))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "reapply-medical-overlay":
        result = overlay_installer.reapply_medical_overlay(**_overlay_request_from_args(args))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "bootstrap":
        profile = load_profile(args.profile)
        workspace_surface_refresh = workspace_init_controller.init_workspace(
            workspace_root=profile.workspace_root,
            workspace_name=profile.name,
            dry_run=False,
            force=False,
            default_publication_profile=profile.default_publication_profile,
            default_citation_style=profile.default_citation_style,
            hermes_agent_repo_root=profile.hermes_agent_repo_root,
            hermes_home_root=profile.hermes_home_root,
        )
        doctor = _load_doctor_module()
        doctor_report = doctor.build_doctor_report(profile)
        overlay_install = None
        overlay_status = None
        overlay_bootstrap = None
        analysis_bundle = analysis_bundle_controller.ensure_study_runtime_analysis_bundle()
        if profile.enable_medical_overlay:
            overlay_request = doctor.overlay_request_from_profile(profile)
            overlay_bootstrap = overlay_installer.ensure_medical_overlay(
                **overlay_request,
                mode=profile.medical_overlay_bootstrap_mode,
            )
            overlay_install = overlay_bootstrap.get("action_result")
            overlay_status = overlay_bootstrap.get("post_status") or overlay_bootstrap.get("pre_status")
        workspace_root = profile.workspace_root
        data_assets_refresh = data_asset_updates_controller.refresh_data_assets(workspace_root=workspace_root)
        result = {
            "profile": profile.name,
            "workspace_surface_refresh": workspace_surface_refresh,
            "doctor": {
                "workspace_exists": doctor_report.workspace_exists,
                "runtime_exists": doctor_report.runtime_exists,
                "studies_exists": doctor_report.studies_exists,
                "portfolio_exists": doctor_report.portfolio_exists,
                "med_deepscientist_runtime_exists": doctor_report.med_deepscientist_runtime_exists,
                "medical_overlay_enabled": doctor_report.medical_overlay_enabled,
                "medical_overlay_ready": (
                    bool(overlay_status.get("all_targets_ready")) if overlay_status is not None else doctor_report.medical_overlay_ready
                ),
                "medical_overlay_scope": doctor_report.profile.medical_overlay_scope,
                "medical_overlay_bootstrap_mode": doctor_report.profile.medical_overlay_bootstrap_mode,
                "research_route_bias_policy": doctor_report.profile.research_route_bias_policy,
                "preferred_study_archetypes": list(doctor_report.profile.preferred_study_archetypes),
            },
            "analysis_bundle": analysis_bundle,
            "overlay_bootstrap": overlay_bootstrap,
            "overlay_install": overlay_install,
            "overlay_status": overlay_status,
            "data_assets": data_assets_refresh,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "ensure-study-runtime":
        profile = load_profile(args.profile)
        result = study_runtime_router.ensure_study_runtime(
            profile=profile,
            study_id=args.study_id,
            study_root=Path(args.study_root) if args.study_root else None,
            entry_mode=args.entry_mode,
            allow_stopped_relaunch=bool(args.allow_stopped_relaunch),
            force=bool(args.force),
            source="cli",
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "study-runtime-status":
        profile = load_profile(args.profile)
        result = study_runtime_router.study_runtime_status(
            profile=profile,
            study_id=args.study_id,
            study_root=Path(args.study_root) if args.study_root else None,
            entry_mode=args.entry_mode,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "init-workspace":
        result = workspace_init_controller.init_workspace(
            workspace_root=Path(args.workspace_root),
            workspace_name=str(args.workspace_name),
            dry_run=bool(args.dry_run),
            force=bool(args.force),
            default_publication_profile=str(args.default_publication_profile),
            default_citation_style=str(args.default_citation_style),
            hermes_agent_repo_root=Path(args.hermes_agent_repo_root) if args.hermes_agent_repo_root else None,
            hermes_home_root=Path(args.hermes_home_root) if args.hermes_home_root else None,
            initialize_git=not bool(args.no_git),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    parser.error(f"unsupported command: {args.command}")
    return 2

def entrypoint() -> None:
    raise SystemExit(main())

if __name__ == "__main__":
    entrypoint()
