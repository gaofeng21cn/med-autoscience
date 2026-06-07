from __future__ import annotations

import argparse
import importlib
import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

from med_autoscience import dev_preflight, dev_preflight_contract
from med_autoscience.agent_entry.renderers import render_stage_route_contract_payload, sync_agent_entry_assets
from med_autoscience.cli_public_surface import (
    GROUPED_COMMAND_PROGS,
    maybe_handle_public_help,
    normalize_public_command_argv,
)
from med_autoscience.figure_routes import supported_required_route_help
from med_autoscience.json_payload import json_safe
from med_autoscience.medical_prose_review_request import materialize_ai_medical_prose_review_from_response
from med_autoscience.overlay import installer as overlay_installer
from med_autoscience.profiles import load_profile, profile_to_dict
from med_autoscience.cli_parts.authority_operations import handle_authority_operation_command
from med_autoscience.cli_parts.parser import build_parser as _build_cli_parser
from med_autoscience.cli_parts.payloads import _load_optional_object_payload_from_args, _parse_key_value_pairs
from med_autoscience.cli_parts.runtime_storage_commands import handle_runtime_storage_command
from med_autoscience.cli_parts.stage_memory_commands import handle_stage_memory_command
from med_autoscience.cli_parts.study_action_commands import handle_study_action_command
from med_autoscience.cli_parts.study_read_commands import handle_study_read_command
from med_autoscience.cli_parts.domain_health_diagnostic_commands import handle_domain_health_diagnostic_command
from med_autoscience.cli_parts.domain_handler_commands import handle_domain_handler_command
from med_autoscience.cli_parts.workspace_data_commands import handle_workspace_data_command

@lru_cache(maxsize=None)
def _load_module(module_name: str) -> Any:
    return importlib.import_module(module_name)


def _load_controller(module_name: str) -> Any:
    return _load_module(f"med_autoscience.controllers.{module_name}")


def _load_adapter(module_name: str) -> Any:
    return _load_module(f"med_autoscience.adapters.{module_name}")


def _load_analysis_bundle_controller() -> Any:
    return _load_module("med_autoscience.study_runtime_analysis_bundle")


def _load_workspace_python_environment_controller() -> Any:
    return _load_module("med_autoscience.workspace_python_environment")


def _load_doctor_module() -> Any:
    return _load_module("med_autoscience.doctor")


class _LazyModuleProxy:
    def __init__(self, loader) -> None:
        object.__setattr__(self, "_loader", loader)

    def __getattr__(self, name: str) -> Any:
        return getattr(object.__getattribute__(self, "_loader")(), name)


data_asset_gate = _LazyModuleProxy(lambda: _load_controller("data_asset_gate"))
data_assets = _LazyModuleProxy(lambda: _load_controller("data_assets"))
data_asset_updates_controller = _LazyModuleProxy(lambda: _load_controller("data_asset_updates"))
display_pack_surface_sync = _LazyModuleProxy(lambda: _load_controller("display_pack_surface_sync"))
display_surface_materialization = _LazyModuleProxy(lambda: _load_controller("display_surface_materialization"))
delivery_inspector = _LazyModuleProxy(lambda: _load_controller("delivery_inspector"))
domain_action_request_materializer = _LazyModuleProxy(lambda: _load_controller("domain_action_request_materializer"))
domain_owner_action_dispatch = _LazyModuleProxy(lambda: _load_controller("domain_owner_action_dispatch"))
stage_artifact_materializer = _LazyModuleProxy(lambda: _load_controller("stage_artifact_materializer"))
owner_route_reconcile = _LazyModuleProxy(lambda: _load_controller("owner_route_reconcile"))
workspace_monolith_migration = _LazyModuleProxy(lambda: _load_controller("workspace_monolith_migration"))
paper_authority_migration = _LazyModuleProxy(lambda: _load_controller("paper_authority_migration"))
study_config_migration = _LazyModuleProxy(lambda: _load_controller("study_config_migration"))
agent_lab_medical_manuscript_quality = _LazyModuleProxy(
    lambda: _load_controller("agent_lab_medical_manuscript_quality")
)
paper_autonomy_stability_evidence = _LazyModuleProxy(lambda: _load_controller("paper_autonomy_stability_evidence"))
backend_audit = _LazyModuleProxy(lambda: _load_controller("backend_audit"))
runtime_health_kernel = _LazyModuleProxy(lambda: _load_controller("runtime_health_kernel"))
runtime_storage_maintenance = _LazyModuleProxy(lambda: _load_controller("runtime_storage_maintenance"))
external_research_controller = _LazyModuleProxy(lambda: _load_controller("external_research"))
figure_loop_guard = _LazyModuleProxy(lambda: _load_controller("figure_loop_guard"))
gate_clearing_batch = _LazyModuleProxy(lambda: _load_controller("gate_clearing_batch"))
journal_package_controller = _LazyModuleProxy(lambda: _load_controller("journal_package"))
journal_requirements_controller = _LazyModuleProxy(lambda: _load_controller("journal_requirements"))
journal_shortlist_controller = _LazyModuleProxy(lambda: _load_controller("journal_shortlist"))
ai_reviewer_publication_eval = _LazyModuleProxy(lambda: _load_controller("ai_reviewer_publication_eval"))
medical_literature_audit = _LazyModuleProxy(lambda: _load_controller("medical_literature_audit"))
medical_paper_readiness_owner_blocker = _LazyModuleProxy(lambda: _load_controller("medical_paper_readiness_owner_blocker"))
medical_publication_surface = _LazyModuleProxy(lambda: _load_controller("medical_publication_surface"))
medical_reporting_audit = _LazyModuleProxy(lambda: _load_controller("medical_reporting_audit"))
workspace_authority_migration_audit = _LazyModuleProxy(lambda: _load_controller("workspace_authority_migration_audit"))
delivery_authority_backfill_apply = _LazyModuleProxy(lambda: _load_controller("delivery_authority_backfill_apply"))
artifact_lifecycle_operations_report = _LazyModuleProxy(lambda: _load_controller("artifact_lifecycle_operations_report"))
continuous_soak_summary = _LazyModuleProxy(lambda: _load_controller("continuous_soak_summary"))
mainline_status = _LazyModuleProxy(lambda: _load_controller("mainline_status"))
open_auto_research_soak = _LazyModuleProxy(lambda: _load_controller("open_auto_research_soak"))
portfolio_memory_controller = _LazyModuleProxy(lambda: _load_controller("portfolio_memory"))
product_entry = _LazyModuleProxy(lambda: _load_controller("product_entry"))
publication_aftercare = _LazyModuleProxy(lambda: _load_controller("publication_aftercare"))
publication_gate = _LazyModuleProxy(lambda: _load_controller("publication_gate"))
quality_repair_batch = _LazyModuleProxy(lambda: _load_controller("quality_repair_batch"))
reference_papers_controller = _LazyModuleProxy(lambda: _load_controller("reference_papers"))
domain_health_diagnostic = _LazyModuleProxy(lambda: _load_controller("domain_health_diagnostic"))
owner_route_handoff = _LazyModuleProxy(lambda: _load_controller("owner_route_handoff"))
stage_knowledge_plane = _LazyModuleProxy(lambda: _load_controller("stage_knowledge_plane"))
publication_route_memory_inventory = _LazyModuleProxy(lambda: _load_module("med_autoscience.controllers.stage_knowledge_plane_parts.publication_route_memory_inventory"))
real_paper_autonomy_soak_inventory = _LazyModuleProxy(lambda: _load_controller("real_paper_autonomy_soak_inventory"))
startup_data_readiness_controller = _LazyModuleProxy(lambda: _load_controller("startup_data_readiness"))
study_progress = _LazyModuleProxy(lambda: _load_controller("study_progress"))
study_cycle_profiler = _LazyModuleProxy(lambda: _load_controller("study_cycle_profiler"))
domain_status_projection = _LazyModuleProxy(lambda: _load_controller("domain_status_projection"))
study_state_matrix = _LazyModuleProxy(lambda: _load_controller("study_state_matrix"))
study_truth_kernel = _LazyModuleProxy(lambda: _load_controller("study_truth_kernel"))
study_delivery_sync = _LazyModuleProxy(lambda: _load_controller("study_delivery_sync"))
submission_inspection_export = _LazyModuleProxy(lambda: _load_controller("submission_inspection_export"))
submission_minimal = _LazyModuleProxy(lambda: _load_controller("submission_minimal"))
submission_targets_controller = _LazyModuleProxy(lambda: _load_controller("submission_targets"))
time_to_event_direct_migration = _LazyModuleProxy(lambda: _load_controller("time_to_event_direct_migration"))
tooluniverse_adapter = _LazyModuleProxy(lambda: _load_adapter("tooluniverse"))
workspace_literature_controller = _LazyModuleProxy(lambda: _load_controller("workspace_literature"))
workspace_init_controller = _LazyModuleProxy(lambda: _load_controller("workspace_init"))
analysis_bundle_controller = _LazyModuleProxy(_load_analysis_bundle_controller)
workspace_python_environment_controller = _LazyModuleProxy(_load_workspace_python_environment_controller)


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


def _load_json_object_file(path: str | Path) -> dict[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("JSON payload file must contain an object")
    return payload


def _serialize_study_runtime_result(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        payload = dict(result)
        safe_payload = json_safe(payload)
        if not isinstance(safe_payload, dict):
            raise TypeError("study runtime controller result must serialize to a dict")
        return safe_payload
    study_runtime_types = _load_controller("study_runtime_types")
    if isinstance(result, study_runtime_types.ProgressProjectionStatus):
        payload = result.to_dict()
        safe_payload = json_safe(payload)
        if not isinstance(safe_payload, dict):
            raise TypeError("study runtime controller result must serialize to a dict")
        return safe_payload
    raise TypeError("study runtime controller result must be dict or ProgressProjectionStatus")


def _handle_delivery_inspect_command(args: argparse.Namespace) -> int:
    profile = load_profile(args.profile)
    result = delivery_inspector.inspect_study_delivery(
        profile=profile,
        profile_ref=Path(args.profile),
        study_id=args.study_id,
        study_root=Path(args.study_root) if args.study_root else None,
        publication_profile=args.publication_profile,
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(delivery_inspector.render_delivery_inspection_markdown(result), end="")
    return 0


def _handle_submission_export_or_delivery_inspect_command(args: argparse.Namespace) -> int:
    if args.command == "delivery-inspect":
        return _handle_delivery_inspect_command(args)
    result = submission_targets_controller.export_submission_targets(
        paper_root=Path(args.paper_root) if args.paper_root else None,
        profile_path=Path(args.profile) if args.profile else None,
        study_root=Path(args.study_root) if args.study_root else None,
        quest_root=Path(args.quest_root) if args.quest_root else None,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _resolve_study_and_quest_for_batch_command(
    args: argparse.Namespace,
    *,
    parser: argparse.ArgumentParser,
) -> tuple[Any, Path, str]:
    if bool(args.study_id) == bool(args.study_root):
        parser.error("Specify exactly one of --study-id or --study-root")
    profile = load_profile(args.profile)
    study_root = Path(args.study_root) if args.study_root else None
    quest_id = str(args.quest_id or "").strip() or None
    if quest_id is None or study_root is None:
        status = domain_status_projection.progress_projection(
            profile=profile,
            study_id=args.study_id,
            study_root=study_root,
            entry_mode=None,
        )
        if study_root is None:
            resolved_study_root = status.get("study_root")
            if not isinstance(resolved_study_root, str) or not resolved_study_root.strip():
                parser.error(f"Unable to resolve study_root for {args.command}")
            study_root = Path(resolved_study_root)
        if quest_id is None:
            resolved_quest_id = str(status.get("quest_id") or "").strip()
            if not resolved_quest_id:
                parser.error(f"Unable to resolve quest_id for {args.command}")
            quest_id = resolved_quest_id
    return profile, study_root, quest_id


def build_parser() -> argparse.ArgumentParser:
    return _build_cli_parser(study_cycle_profiler=study_cycle_profiler)


def main(argv: list[str] | None = None) -> int:
    resolved_argv = list(argv) if argv is not None else list(sys.argv[1:])
    help_result = maybe_handle_public_help(resolved_argv)
    if help_result is not None:
        return help_result
    parser = build_parser()
    args = parser.parse_args(normalize_public_command_argv(resolved_argv))
    authority_result = handle_authority_operation_command(
        args,
        controller_modules={
            "artifact_lifecycle_operations_report": artifact_lifecycle_operations_report,
            "delivery_authority_backfill_apply": delivery_authority_backfill_apply,
            "workspace_authority_migration_audit": workspace_authority_migration_audit,
            "continuous_soak_summary": continuous_soak_summary,
        },
    )
    if authority_result is not None:
        return authority_result

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

    if args.command == "show-stage-route-contract":
        print(json.dumps(render_stage_route_contract_payload(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "sync-agent-entry-assets":
        result = sync_agent_entry_assets(repo_root=Path(args.repo_root))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    domain_handler_result = handle_domain_handler_command(
        args,
        load_profile=load_profile,
        load_json_object_file=_load_json_object_file,
        load_module=_load_module,
        owner_route_handoff=owner_route_handoff,
        owner_route_reconcile=owner_route_reconcile,
    )
    if domain_handler_result is not None:
        return domain_handler_result

    if args.command == "preflight-changes":
        input_mode = "files"
        if args.staged:
            input_mode = "staged"
        elif args.base_ref:
            input_mode = "base_ref"
        if args.base_ref:
            result = dev_preflight.run_ci_preflight(base_ref=args.base_ref, repo_root=Path.cwd())
        else:
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

    if args.command == "preflight-contract-report":
        result = dev_preflight_contract.build_preflight_contract_report()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    stage_memory_result = handle_stage_memory_command(
        args,
        parser=parser,
        stage_knowledge_plane=stage_knowledge_plane,
        publication_route_memory_inventory=publication_route_memory_inventory,
        real_paper_autonomy_soak_inventory=real_paper_autonomy_soak_inventory,
        load_json_object_file=_load_json_object_file,
    )
    if stage_memory_result is not None:
        return stage_memory_result

    if args.command == "backend-audit":
        profile = load_profile(args.profile)
        result = backend_audit.run_backend_audit(profile, refresh=bool(args.refresh))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    runtime_storage_result = handle_runtime_storage_command(
        args,
        parser=parser,
        runtime_storage_maintenance=runtime_storage_maintenance,
        load_profile=load_profile,
    )
    if runtime_storage_result is not None:
        return runtime_storage_result

    study_read_result = handle_study_read_command(
        args,
        parser=parser,
        load_profile=load_profile,
        serialize_study_runtime_result=_serialize_study_runtime_result,
        study_progress=study_progress,
        domain_status_projection=domain_status_projection,
        study_state_matrix=study_state_matrix,
        study_truth_kernel=study_truth_kernel,
        runtime_health_kernel=runtime_health_kernel,
    )
    if study_read_result is not None:
        return study_read_result

    study_action_result = handle_study_action_command(
        args,
        parser=parser,
        study_domain_handlers=product_entry,
        load_profile=load_profile,
    )
    if study_action_result is not None:
        return study_action_result

    if args.command == "domain-action-request-materialize":
        profile = load_profile(args.profile)
        result = domain_action_request_materializer.materialize_domain_action_requests(
            profile=profile,
            study_ids=tuple(args.studies or ()),
            mode=args.mode,
            apply=bool(args.apply),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "domain-owner-action-dispatch":
        profile = load_profile(args.profile)
        consumer_payload = (
            _load_json_payload_from_args(args)
            if getattr(args, "payload_file", None) or getattr(args, "payload_json", None)
            else None
        )
        result = domain_owner_action_dispatch.dispatch_domain_owner_actions(
            profile=profile,
            study_ids=tuple(args.studies or ()),
            action_types=tuple(args.action_types or ()),
            mode=args.mode,
            apply=bool(args.apply),
            consumer_payload=consumer_payload,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "domain-owner-action-refresh-controller-decisions":
        profile = load_profile(args.profile)
        result = domain_owner_action_dispatch.refresh_controller_decisions_for_current_publication_eval(
            profile=profile,
            study_ids=tuple(args.studies or ()),
            mode=args.mode,
            apply=bool(args.apply),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "stage-artifact-materialize":
        profile = load_profile(args.profile)
        results = []
        for study_id in tuple(args.studies or ()):
            results.append(
                stage_artifact_materializer.materialize_stage_artifact_delta(
                    study_id=study_id,
                    study_root=profile.studies_root / study_id,
                    workspace_root=profile.workspace_root,
                    stage_ids=tuple(args.stage_ids or ()),
                    apply=bool(args.apply),
                )
            )
        print(
            json.dumps(
                {
                    "surface_kind": "stage_artifact_materialize_command",
                    "schema_version": 1,
                    "profile": profile.name,
                    "study_count": len(results),
                    "apply": bool(args.apply),
                    "results": results,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.command == "medical-paper-readiness-owner-blocker":
        result = medical_paper_readiness_owner_blocker.materialize_readiness_owner_blocker(
            study_root=Path(args.study_root),
            source=args.source,
            apply=bool(args.apply),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "open-auto-research-soak":
        if bool(args.study_id) == bool(args.study_root):
            parser.error("Specify exactly one of --study-id or --study-root")
        profile = load_profile(args.profile)
        result = open_auto_research_soak.run_open_auto_research_soak(
            profile=profile,
            study_id=args.study_id,
            study_root=Path(args.study_root) if args.study_root else None,
            entry_mode=args.entry_mode,
            allow_controller_writes=args.allow_controller_writes,
        )
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(open_auto_research_soak.render_open_auto_research_soak_markdown(result), end="")
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
        profile, study_root, quest_id = _resolve_study_and_quest_for_batch_command(args, parser=parser)
        result = quality_repair_batch.run_quality_repair_batch(
            profile=profile,
            study_id=args.study_id or study_root.name,
            study_root=study_root,
            quest_id=quest_id,
            source="cli",
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "gate-clearing-batch":
        profile, study_root, quest_id = _resolve_study_and_quest_for_batch_command(args, parser=parser)
        result = gate_clearing_batch.run_gate_clearing_batch(
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

    if args.command == "materialize-ai-reviewer-publication-eval-record":
        if bool(args.study_id) == bool(args.study_root):
            parser.error("Specify exactly one of --study-id or --study-root")
        profile = load_profile(args.profile)
        result = ai_reviewer_publication_eval.materialize_ai_reviewer_publication_eval_record(
            profile=profile,
            study_id=args.study_id,
            study_root=Path(args.study_root) if args.study_root else None,
            entry_mode=args.entry_mode,
            record=_load_json_payload_from_args(args),
            source="cli",
            build_production_trace=bool(args.build_production_trace),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "materialize-ai-medical-prose-review":
        if bool(args.study_id) == bool(args.study_root):
            parser.error("Specify exactly one of --study-id or --study-root")
        profile = load_profile(args.profile)
        status_payload = _serialize_study_runtime_result(
            domain_status_projection.progress_projection(
                profile=profile,
                study_id=args.study_id,
                study_root=Path(args.study_root) if args.study_root else None,
                entry_mode=args.entry_mode,
            )
        )
        resolved_study_root = str(status_payload.get("study_root") or "").strip()
        if not resolved_study_root:
            parser.error("Unable to resolve study_root for materialize-ai-medical-prose-review")
        result = materialize_ai_medical_prose_review_from_response(
            study_root=Path(resolved_study_root),
            response_payload=_load_json_payload_from_args(args),
            request_ref=args.request_ref,
        )
        output = {
            "status": "materialized",
            "source": "cli",
            "study_id": status_payload.get("study_id") or args.study_id or Path(resolved_study_root).name,
            "quest_id": status_payload.get("quest_id"),
            "artifact_path": result["artifact_path"],
            "surface": result["surface"],
            "assessment_owner": "ai_reviewer",
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0

    domain_health_diagnostic_result = handle_domain_health_diagnostic_command(
        args,
        parser=parser,
        domain_health_diagnostic=domain_health_diagnostic,
        load_profile=load_profile,
    )
    if domain_health_diagnostic_result is not None:
        return domain_health_diagnostic_result

    if args.command == "owner-route-reconcile":
        profile = load_profile(args.profile)
        explicit_study_ids = tuple(args.studies or ())
        study_ids = explicit_study_ids or owner_route_reconcile.resolve_owner_route_reconcile_study_ids(profile)
        result = owner_route_reconcile.scan_domain_routes(
            profile=profile,
            study_ids=study_ids,
            apply_safe_actions=bool(args.apply_safe_actions),
            developer_supervisor_mode=args.developer_supervisor_mode,
            retain_unscanned_studies=not bool(explicit_study_ids),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "workspace-monolith-migrate":
        result = workspace_monolith_migration.run_workspace_monolith_migration(
            profile_path=Path(args.profile),
            apply=bool(args.apply),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "paper-authority-clean-migration":
        result = paper_authority_migration.run_paper_authority_clean_migration(
            profile_path=Path(args.profile),
            study_ids=tuple(args.studies or ()),
            apply=bool(args.apply),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "study-config-clean-migration":
        result = study_config_migration.run_study_config_clean_migration(
            profile_path=Path(args.profile),
            study_ids=tuple(args.studies or ()),
            apply=bool(args.apply),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "agent-lab-medical-manuscript-quality-suite":
        if args.apply:
            result = agent_lab_medical_manuscript_quality.materialize_medical_manuscript_quality_agent_lab_suite(
                study_root=Path(args.study_root),
                reviewer_feedback_ref=args.reviewer_feedback_ref,
            )
        else:
            result = {
                "surface_kind": agent_lab_medical_manuscript_quality.SURFACE_KIND,
                "status": "dry_run",
                "study_id": Path(args.study_root).expanduser().resolve().name,
                "suite": agent_lab_medical_manuscript_quality.build_medical_manuscript_quality_agent_lab_suite(
                    study_root=Path(args.study_root),
                    reviewer_feedback_ref=args.reviewer_feedback_ref,
                ),
                "authority_boundary": dict(agent_lab_medical_manuscript_quality.AUTHORITY_BOUNDARY),
            }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "paper-autonomy-stability-evidence":
        result = paper_autonomy_stability_evidence.build_paper_autonomy_stability_evidence(
            yang_root=Path(args.yang_root),
            profile_paths=tuple(args.profiles or ()),
            study_ids=tuple(args.studies or ()),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "ensure-analysis-bundle":
        result = analysis_bundle_controller.ensure_analysis_bundle()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    workspace_data_result = handle_workspace_data_command(
        args,
        data_asset_gate=data_asset_gate,
        data_assets=data_assets,
        data_asset_updates_controller=data_asset_updates_controller,
        external_research_controller=external_research_controller,
        portfolio_memory_controller=portfolio_memory_controller,
        startup_data_readiness_controller=startup_data_readiness_controller,
        tooluniverse_adapter=tooluniverse_adapter,
        workspace_init_controller=workspace_init_controller,
        workspace_literature_controller=workspace_literature_controller,
        load_profile=load_profile,
        load_doctor_module=_load_doctor_module,
        overlay_installer=overlay_installer,
        analysis_bundle_controller=analysis_bundle_controller,
        workspace_python_environment_controller=workspace_python_environment_controller,
        overlay_request_from_args=_overlay_request_from_args,
        load_json_payload_from_args=_load_json_payload_from_args,
    )
    if workspace_data_result is not None:
        return workspace_data_result

    if args.command == "export-submission-minimal":
        result = submission_minimal.create_submission_minimal_package(
            paper_root=Path(args.paper_root),
            publication_profile=args.publication_profile,
            citation_style=args.citation_style,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "export-inspection-package":
        profile_ref = Path(args.profile)
        profile = load_profile(profile_ref)
        result = submission_inspection_export.export_inspection_package(
            profile=profile,
            profile_ref=profile_ref,
            study_id=args.study_id,
            study_root=Path(args.study_root) if args.study_root else None,
            publication_profile=args.publication_profile,
            force_materialize=args.force_materialize,
            source="cli",
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

    if args.command in {"export-submission-targets", "delivery-inspect"}:
        return _handle_submission_export_or_delivery_inspect_command(args)

    if args.command == "publication-gate":
        result = publication_gate.run_controller(
            quest_root=Path(args.quest_root),
            apply=args.apply,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "publication-aftercare-plan":
        result = publication_aftercare.build_publication_aftercare_plan(
            study_root=Path(args.study_root),
            quest_root=Path(args.quest_root) if args.quest_root else None,
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

    parser.error(f"unsupported command: {args.command}")
    return 2

def entrypoint() -> None:
    raise SystemExit(main())

if __name__ == "__main__":
    entrypoint()
