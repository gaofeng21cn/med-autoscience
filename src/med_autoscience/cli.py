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
from med_autoscience.cli_parts.parser import build_parser as _build_cli_parser
from med_autoscience.cli_parts.payloads import _parse_key_value_pairs

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




def _serialize_study_runtime_result(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return dict(result)
    study_runtime_types = _load_controller("study_runtime_types")
    if isinstance(result, study_runtime_types.StudyRuntimeStatus):
        return result.to_dict()
    raise TypeError("study runtime controller result must be dict or StudyRuntimeStatus")



def build_parser() -> argparse.ArgumentParser:
    return _build_cli_parser(study_cycle_profiler=study_cycle_profiler)


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

    if args.command == "workspace-storage-audit":
        if bool(args.study_id) and bool(args.all_studies):
            parser.error("Specify at most one of --study-id or --all-studies")
        profile = load_profile(args.profile)
        result = runtime_storage_maintenance.audit_workspace_storage(
            profile=profile,
            study_id=args.study_id,
            all_studies=bool(args.all_studies) or not bool(args.study_id),
            stopped_only=bool(args.stopped_only),
            apply=bool(args.apply),
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
