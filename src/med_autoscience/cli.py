from __future__ import annotations

import argparse
import importlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from med_autoscience.doctor import (
    build_doctor_report,
    overlay_request_from_profile,
    render_doctor_report,
    render_profile,
)
from med_autoscience import dev_preflight
from med_autoscience.agent_entry.renderers import render_entry_modes_payload, sync_agent_entry_assets
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
med_deepscientist_upgrade_check = _LazyModuleProxy(lambda: _load_controller("med_deepscientist_upgrade_check"))
external_research_controller = _LazyModuleProxy(lambda: _load_controller("external_research"))
figure_loop_guard = _LazyModuleProxy(lambda: _load_controller("figure_loop_guard"))
journal_shortlist_controller = _LazyModuleProxy(lambda: _load_controller("journal_shortlist"))
medical_literature_audit = _LazyModuleProxy(lambda: _load_controller("medical_literature_audit"))
medical_publication_surface = _LazyModuleProxy(lambda: _load_controller("medical_publication_surface"))
medical_reporting_audit = _LazyModuleProxy(lambda: _load_controller("medical_reporting_audit"))
portfolio_memory_controller = _LazyModuleProxy(lambda: _load_controller("portfolio_memory"))
publication_gate = _LazyModuleProxy(lambda: _load_controller("publication_gate"))
reference_papers_controller = _LazyModuleProxy(lambda: _load_controller("reference_papers"))
runtime_watch = _LazyModuleProxy(lambda: _load_controller("runtime_watch"))
sidecar_provider_controller = _LazyModuleProxy(lambda: _load_controller("sidecar_provider"))
startup_data_readiness_controller = _LazyModuleProxy(lambda: _load_controller("startup_data_readiness"))
study_progress = _LazyModuleProxy(lambda: _load_controller("study_progress"))
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
        request = overlay_request_from_profile(profile)
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

    bootstrap_parser = subparsers.add_parser("bootstrap")
    bootstrap_parser.add_argument("--profile", required=True)

    init_workspace_parser = subparsers.add_parser("init-workspace")
    init_workspace_parser.add_argument("--workspace-root", required=True)
    init_workspace_parser.add_argument("--workspace-name", required=True)
    init_workspace_parser.add_argument("--default-publication-profile", default="general_medical_journal")
    init_workspace_parser.add_argument("--default-citation-style", default="AMA")
    init_workspace_parser.add_argument("--dry-run", action="store_true")
    init_workspace_parser.add_argument("--force", action="store_true")

    med_deepscientist_upgrade_check_parser = subparsers.add_parser("med-deepscientist-upgrade-check")
    med_deepscientist_upgrade_check_parser.add_argument("--profile", required=True)
    med_deepscientist_upgrade_check_parser.add_argument("--refresh", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "doctor":
        profile = load_profile(args.profile)
        print(render_doctor_report(build_doctor_report(profile)), end="")
        return 0

    if args.command == "show-profile":
        profile = load_profile(args.profile)
        if args.format == "json":
            print(json.dumps(profile_to_dict(profile), ensure_ascii=False, indent=2))
        else:
            print(render_profile(profile), end="")
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

    if args.command == "med-deepscientist-upgrade-check":
        profile = load_profile(args.profile)
        result = med_deepscientist_upgrade_check.run_upgrade_check(profile, refresh=bool(args.refresh))
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
            study_id=args.study_id,
            study_root=Path(args.study_root) if args.study_root else None,
            entry_mode=args.entry_mode,
        )
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(study_progress.render_study_progress_markdown(result), end="")
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
        doctor_report = build_doctor_report(profile)
        overlay_install = None
        overlay_status = None
        overlay_bootstrap = None
        analysis_bundle = analysis_bundle_controller.ensure_study_runtime_analysis_bundle()
        if profile.enable_medical_overlay:
            overlay_request = overlay_request_from_profile(profile)
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
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    parser.error(f"unsupported command: {args.command}")
    return 2


def entrypoint() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    entrypoint()
