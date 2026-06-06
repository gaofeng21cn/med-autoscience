from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def handle_workspace_data_command(
    args: argparse.Namespace,
    *,
    data_asset_gate: Any,
    data_assets: Any,
    data_asset_updates_controller: Any,
    external_research_controller: Any,
    portfolio_memory_controller: Any,
    startup_data_readiness_controller: Any,
    tooluniverse_adapter: Any,
    workspace_init_controller: Any,
    workspace_literature_controller: Any,
    load_profile: Any,
    load_doctor_module: Any,
    overlay_installer: Any,
    analysis_bundle_controller: Any,
    workspace_python_environment_controller: Any,
    overlay_request_from_args: Any,
    load_json_payload_from_args: Any,
) -> int | None:
    if args.command == "init-data-assets":
        result = data_assets.init_data_assets(workspace_root=Path(args.workspace_root))
        _print_json(result)
        return 0

    if args.command == "data-assets-status":
        result = data_assets.data_assets_status(workspace_root=Path(args.workspace_root))
        _print_json(result)
        return 0

    if args.command == "init-portfolio-memory":
        result = portfolio_memory_controller.init_portfolio_memory(workspace_root=Path(args.workspace_root))
        _print_json(result)
        return 0

    if args.command == "portfolio-memory-status":
        result = portfolio_memory_controller.portfolio_memory_status(workspace_root=Path(args.workspace_root))
        _print_json(result)
        return 0

    if args.command == "init-workspace-literature":
        result = workspace_literature_controller.init_workspace_literature(workspace_root=Path(args.workspace_root))
        _print_json(result)
        return 0

    if args.command == "workspace-literature-status":
        result = workspace_literature_controller.workspace_literature_status(workspace_root=Path(args.workspace_root))
        _print_json(result)
        return 0

    if args.command == "prepare-external-research":
        result = external_research_controller.prepare_external_research(
            workspace_root=Path(args.workspace_root),
            as_of_date=args.as_of_date,
        )
        _print_json(result)
        return 0

    if args.command == "external-research-status":
        result = external_research_controller.external_research_status(workspace_root=Path(args.workspace_root))
        _print_json(result)
        return 0

    if args.command == "assess-data-asset-impact":
        result = data_assets.assess_data_asset_impact(workspace_root=Path(args.workspace_root))
        _print_json(result)
        return 0

    if args.command == "validate-public-registry":
        result = data_assets.validate_public_registry(workspace_root=Path(args.workspace_root))
        _print_json(result)
        return 0

    if args.command == "startup-data-readiness":
        result = startup_data_readiness_controller.startup_data_readiness(workspace_root=Path(args.workspace_root))
        _print_json(result)
        return 0

    if args.command == "apply-data-asset-update":
        result = data_asset_updates_controller.apply_data_asset_update(
            workspace_root=Path(args.workspace_root),
            payload=load_json_payload_from_args(args),
        )
        _print_json(result)
        return 0

    if args.command == "diff-private-release":
        result = data_assets.build_private_release_diff(
            workspace_root=Path(args.workspace_root),
            family_id=args.family_id,
            from_version=args.from_version,
            to_version=args.to_version,
        )
        _print_json(result)
        return 0

    if args.command == "data-asset-gate":
        result = data_asset_gate.run_controller(
            quest_root=Path(args.quest_root),
            apply=args.apply,
        )
        _print_json(result)
        return 0

    if args.command == "tooluniverse-status":
        result = tooluniverse_adapter.detect_tooluniverse(
            workspace_root=Path(args.workspace_root) if args.workspace_root else None,
            tooluniverse_root=Path(args.tooluniverse_root) if args.tooluniverse_root else None,
        )
        _print_json(result)
        return 0

    if args.command == "overlay-status":
        result = overlay_installer.describe_medical_overlay(**overlay_request_from_args(args))
        _print_json(result)
        return 0

    if args.command == "install-medical-overlay":
        result = overlay_installer.install_medical_overlay(**overlay_request_from_args(args))
        _print_json(result)
        return 0

    if args.command == "reapply-medical-overlay":
        result = overlay_installer.reapply_medical_overlay(**overlay_request_from_args(args))
        _print_json(result)
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
        supervision_bootstrap = {
            "surface_kind": "opl_current_control_state_handoff",
            "owner": "one-person-lab",
            "manager": "opl",
            "effect": "refs_only",
            "trigger_now": False,
            "mas_runtime_supervision_command_removed": True,
            "reason": "mas_runtime_scheduler_not_active_callable",
        }
        doctor = load_doctor_module()
        doctor_report = doctor.build_doctor_report(profile)
        overlay_install = None
        overlay_status = None
        overlay_bootstrap = None
        workspace_python_environment = workspace_python_environment_controller.ensure_workspace_python_environment(
            workspace_root=profile.workspace_root,
        )
        analysis_bundle = analysis_bundle_controller.ensure_analysis_bundle()
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
            "workspace_python_environment": workspace_python_environment,
            "analysis_bundle": analysis_bundle,
            "overlay_bootstrap": overlay_bootstrap,
            "overlay_install": overlay_install,
            "overlay_status": overlay_status,
            "data_assets": data_assets_refresh,
            "supervision_bootstrap": supervision_bootstrap,
        }
        _print_json(result)
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
            initialize_git=bool(args.with_git),
        )
        _print_json(result)
        return 0

    return None


def _print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


__all__ = ["handle_workspace_data_command"]
