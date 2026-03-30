from __future__ import annotations

import argparse
import json
from pathlib import Path

from med_autoscience.doctor import (
    build_doctor_report,
    overlay_request_from_profile,
    render_doctor_report,
    render_profile,
)
from med_autoscience.controllers import (
    autofigure_edit_sidecar as autofigure_edit_sidecar_controller,
    aris_sidecar as aris_sidecar_controller,
    data_asset_gate,
    data_assets,
    data_asset_updates as data_asset_updates_controller,
    deepscientist_upgrade_check,
    figure_loop_guard,
    medical_publication_surface,
    publication_gate,
    reference_papers as reference_papers_controller,
    runtime_watch,
    sidecar_provider as sidecar_provider_controller,
    startup_data_readiness as startup_data_readiness_controller,
    study_delivery_sync,
    submission_minimal,
    submission_targets as submission_targets_controller,
)
from med_autoscience.adapters import tooluniverse as tooluniverse_adapter
from med_autoscience.figure_routes import supported_required_route_help
from med_autoscience.overlay import installer as overlay_installer
from med_autoscience.profiles import load_profile, profile_to_dict


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
    if payload_file:
        return json.loads(Path(payload_file).read_text(encoding="utf-8"))
    return json.loads(payload_json)


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="medautosci")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor_parser = subparsers.add_parser("doctor")
    doctor_parser.add_argument("--profile", required=True)

    show_profile_parser = subparsers.add_parser("show-profile")
    show_profile_parser.add_argument("--profile", required=True)
    show_profile_parser.add_argument("--format", choices=("text", "json"), default="text")

    watch_parser = subparsers.add_parser("watch")
    watch_parser.add_argument("--quest-root", type=str)
    watch_parser.add_argument("--runtime-root", type=str)
    watch_parser.add_argument("--apply", action="store_true")

    init_data_assets_parser = subparsers.add_parser("init-data-assets")
    init_data_assets_parser.add_argument("--workspace-root", required=True)

    data_assets_status_parser = subparsers.add_parser("data-assets-status")
    data_assets_status_parser.add_argument("--workspace-root", required=True)

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

    resolve_submission_targets_parser = subparsers.add_parser("resolve-submission-targets")
    resolve_submission_targets_parser.add_argument("--profile", type=str)
    resolve_submission_targets_parser.add_argument("--study-root", type=str)
    resolve_submission_targets_parser.add_argument("--quest-root", type=str)

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

    overlay_status_parser = subparsers.add_parser("overlay-status")
    overlay_status_parser.add_argument("--quest-root", type=str)
    overlay_status_parser.add_argument("--profile", type=str)

    install_overlay_parser = subparsers.add_parser("install-medical-overlay")
    install_overlay_parser.add_argument("--quest-root", type=str)
    install_overlay_parser.add_argument("--profile", type=str)

    reapply_overlay_parser = subparsers.add_parser("reapply-medical-overlay")
    reapply_overlay_parser.add_argument("--quest-root", type=str)
    reapply_overlay_parser.add_argument("--profile", type=str)

    bootstrap_parser = subparsers.add_parser("bootstrap")
    bootstrap_parser.add_argument("--profile", required=True)

    deepscientist_upgrade_check_parser = subparsers.add_parser("deepscientist-upgrade-check")
    deepscientist_upgrade_check_parser.add_argument("--profile", required=True)
    deepscientist_upgrade_check_parser.add_argument("--refresh", action="store_true")
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

    if args.command == "deepscientist-upgrade-check":
        profile = load_profile(args.profile)
        result = deepscientist_upgrade_check.run_upgrade_check(profile, refresh=bool(args.refresh))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "watch":
        if bool(args.quest_root) == bool(args.runtime_root):
            parser.error("Specify exactly one of --quest-root or --runtime-root")
        if args.quest_root:
            result = runtime_watch.run_watch_for_quest(
                quest_root=Path(args.quest_root),
                apply=args.apply,
            )
        else:
            result = runtime_watch.run_watch_for_runtime(
                runtime_root=Path(args.runtime_root),
                apply=args.apply,
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
        if profile.enable_medical_overlay:
            overlay_request = overlay_request_from_profile(profile)
            overlay_install = overlay_installer.install_medical_overlay(**overlay_request)
            overlay_status = overlay_installer.describe_medical_overlay(**overlay_request)
        workspace_root = profile.workspace_root
        data_assets_refresh = data_asset_updates_controller.refresh_data_assets(workspace_root=workspace_root)
        result = {
            "profile": profile.name,
            "doctor": {
                "workspace_exists": doctor_report.workspace_exists,
                "runtime_exists": doctor_report.runtime_exists,
                "studies_exists": doctor_report.studies_exists,
                "portfolio_exists": doctor_report.portfolio_exists,
                "deepscientist_runtime_exists": doctor_report.deepscientist_runtime_exists,
                "medical_overlay_enabled": doctor_report.medical_overlay_enabled,
                "medical_overlay_ready": (
                    bool(overlay_status.get("all_targets_ready")) if overlay_status is not None else doctor_report.medical_overlay_ready
                ),
                "medical_overlay_scope": doctor_report.profile.medical_overlay_scope,
                "research_route_bias_policy": doctor_report.profile.research_route_bias_policy,
                "preferred_study_archetypes": list(doctor_report.profile.preferred_study_archetypes),
            },
            "overlay_install": overlay_install,
            "overlay_status": overlay_status,
            "data_assets": data_assets_refresh,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    parser.error(f"unsupported command: {args.command}")
    return 2


def entrypoint() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    entrypoint()
