from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def handle_workbench_command(
    args: argparse.Namespace,
    *,
    product_entry: Any,
    progress_portal: Any,
    load_profile: Any,
) -> int | None:
    if args.command == "workspace-cockpit":
        profile = load_profile(args.profile)
        result = product_entry.read_workspace_cockpit(
            profile=profile,
            profile_ref=Path(args.profile),
        )
        if args.format == "json":
            _print_json(result)
        else:
            print(product_entry.render_workspace_cockpit_markdown(result), end="")
        return 0

    if args.command == "progress-portal":
        if bool(getattr(args, "enable_actions", False)) and not bool(args.serve):
            raise SystemExit("--enable-actions requires --serve")
        profile = load_profile(args.profile)
        common_kwargs = {
            "profile": profile,
            "profile_ref": Path(args.profile),
            "study_id": args.study_id,
            "study_root": Path(args.study_root) if args.study_root else None,
            "entry_mode": args.entry_mode,
            "open_browser": bool(args.open),
        }
        if args.serve:
            result = progress_portal.serve_progress_portal(
                **common_kwargs,
                host=str(args.host),
                port=int(args.port),
                interval_seconds=int(args.interval_seconds),
                enable_actions=bool(args.enable_actions),
            )
        else:
            result = progress_portal.materialize_progress_portal(**common_kwargs)
        if args.format == "json":
            _print_json(result)
        else:
            print(_render_progress_portal_command_text(result), end="")
        return 0

    return None


def _render_progress_portal_command_text(result: dict[str, Any]) -> str:
    lines = ["MAS Progress Portal"]
    status = result.get("status")
    if status:
        lines.append(f"status: {status}")
    url = result.get("url")
    if url:
        lines.append(f"url: {url}")
    html_path = result.get("html_path") or result.get("output_html_path")
    if html_path:
        lines.append(f"html: {html_path}")
    payload_path = result.get("payload_path")
    if payload_path:
        lines.append(f"payload: {payload_path}")
    hosted_package_path = result.get("hosted_package_path")
    if hosted_package_path:
        lines.append(f"hosted_package: {hosted_package_path}")
    return "\n".join(lines) + "\n"


def _print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


__all__ = ["handle_workbench_command"]
