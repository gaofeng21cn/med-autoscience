from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json_object_file(path: str | Path) -> dict[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("JSON payload file must contain an object")
    return payload


def _load_optional_json_object_from_args(
    args: argparse.Namespace,
    *,
    json_attr: str,
    file_attr: str,
    label: str,
) -> dict[str, object] | None:
    payload_json = getattr(args, json_attr, None)
    payload_file = getattr(args, file_attr, None)
    if payload_file and payload_json:
        raise SystemExit(f"Specify at most one of --{json_attr.replace('_', '-')} or --{file_attr.replace('_', '-')}")
    if payload_file:
        return _load_json_object_file(payload_file)
    if not payload_json:
        return None
    payload = json.loads(str(payload_json))
    if not isinstance(payload, dict):
        raise SystemExit(f"{label} JSON must contain an object")
    return payload


def _load_visual_audit_review_from_args(args: argparse.Namespace) -> dict[str, object]:
    payload_json = getattr(args, "visual_audit_review_json", None)
    payload_file = getattr(args, "visual_audit_review_file", None)
    if payload_file:
        return _load_json_object_file(payload_file)
    payload = json.loads(str(payload_json))
    if not isinstance(payload, dict):
        raise SystemExit("visual audit review JSON must contain an object")
    return payload


def handle_display_pack_command(args: argparse.Namespace) -> dict[str, Any] | None:
    if args.command == "display-pack-agent-discover":
        from med_autoscience.display_pack_agent import display_pack_capability_discover

        return display_pack_capability_discover(
            repo_root=Path(args.repo_root) if args.repo_root else None,
            paper_root=Path(args.paper_root) if args.paper_root else None,
            include_templates=bool(args.include_templates),
        )

    if args.command == "display-pack-agent-plan":
        from med_autoscience.display_pack_agent import display_pack_figure_plan

        return display_pack_figure_plan(
            repo_root=Path(args.repo_root) if args.repo_root else None,
            paper_root=Path(args.paper_root) if args.paper_root else None,
            figure_request=_load_optional_json_object_from_args(
                args,
                json_attr="figure_request_json",
                file_attr="figure_request_file",
                label="figure request",
            ),
            max_recommendations=int(args.max_recommendations),
        )

    if args.command == "display-pack-agent-preflight":
        from med_autoscience.display_pack_agent import display_pack_preflight

        return display_pack_preflight(
            repo_root=Path(args.repo_root) if args.repo_root else None,
            paper_root=Path(args.paper_root) if args.paper_root else None,
            template_id=str(args.template_id or ""),
            figure_request=_load_optional_json_object_from_args(
                args,
                json_attr="figure_request_json",
                file_attr="figure_request_file",
                label="figure request",
            ),
            check_runtime_dependencies=not bool(args.skip_runtime_dependency_check),
        )

    if args.command == "display-pack-agent-render":
        from med_autoscience.display_pack_agent import display_pack_render

        return display_pack_render(
            repo_root=Path(args.repo_root) if args.repo_root else None,
            paper_root=Path(args.paper_root),
            figure_request=_load_optional_json_object_from_args(
                args,
                json_attr="figure_request_json",
                file_attr="figure_request_file",
                label="figure request",
            ),
            visual_audit_review=_load_optional_json_object_from_args(
                args,
                json_attr="visual_audit_review_json",
                file_attr="visual_audit_review_file",
                label="visual audit review",
            ),
        )

    if args.command == "display-pack-list-templates":
        from med_autoscience.display_pack_usability import list_display_pack_templates

        return list_display_pack_templates(
            repo_root=Path(args.repo_root),
            paper_root=Path(args.paper_root) if args.paper_root else None,
            kind=str(args.kind),
            renderer_family=str(args.renderer_family),
            audit_family=str(args.audit_family),
            paper_family=str(args.paper_family),
            query=str(args.query),
        )

    if args.command == "display-pack-describe-template":
        from med_autoscience.display_pack_usability import describe_display_pack_template

        return describe_display_pack_template(
            repo_root=Path(args.repo_root),
            paper_root=Path(args.paper_root) if args.paper_root else None,
            template_id=str(args.template_id),
        )

    if args.command == "display-pack-scaffold-render":
        from med_autoscience.display_pack_usability import scaffold_display_pack_render

        return scaffold_display_pack_render(
            repo_root=Path(args.repo_root),
            paper_root=Path(args.paper_root),
            template_id=str(args.template_id),
            data_payload_file=Path(args.data_payload_file),
            figure_id=str(args.figure_id),
            claim_ref=str(args.claim_ref),
            cohort_ref=str(args.cohort_ref),
            endpoint_ref=str(args.endpoint_ref),
            risk_horizon=str(args.risk_horizon),
        )

    if args.command == "display-pack-golden":
        from med_autoscience.display_pack_usability import (
            check_display_pack_golden,
            refresh_display_pack_golden,
        )

        golden_kwargs = {
            "repo_root": Path(args.repo_root),
            "paper_root": Path(args.paper_root),
            "template_id": str(args.template_id),
            "data_payload_file": Path(args.data_payload_file),
            "golden_root": Path(args.golden_root),
            "figure_id": str(args.figure_id),
        }
        if args.display_pack_golden_command == "refresh":
            return refresh_display_pack_golden(**golden_kwargs)
        if args.display_pack_golden_command == "check":
            return check_display_pack_golden(**golden_kwargs)
        raise SystemExit(f"Unsupported display-pack-golden command: {args.display_pack_golden_command}")

    if args.command == "display-pack-render-candidate":
        from med_autoscience.display_pack_e2e_runtime import render_display_pack_candidate_asset

        return render_display_pack_candidate_asset(
            repo_root=Path(args.repo_root),
            template_id=str(args.template_id),
            display_payload_file=Path(args.display_payload_file),
            output_dir=Path(args.output_dir),
        )

    if args.command != "display-pack-e2e":
        return None

    from med_autoscience.display_pack_e2e_runtime import materialize_display_pack_publication_manifest

    return materialize_display_pack_publication_manifest(
        repo_root=Path(args.repo_root),
        paper_root=Path(args.paper_root),
        visual_audit_review=_load_visual_audit_review_from_args(args),
        figure_ids=list(getattr(args, "figure_id", []) or []),
    )
