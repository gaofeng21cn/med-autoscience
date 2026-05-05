from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def register_runtime_lifecycle_parsers(subparsers: argparse._SubParsersAction) -> None:
    inventory_parser = subparsers.add_parser("runtime-lifecycle-inventory")
    _add_scope_args(inventory_parser)

    read_parser = subparsers.add_parser("runtime-lifecycle-read")
    _add_scope_args(read_parser)
    _add_surface_args(read_parser)

    export_parser = subparsers.add_parser("runtime-lifecycle-export")
    _add_scope_args(export_parser)
    _add_surface_args(export_parser)
    export_parser.add_argument("--format", choices=("json", "markdown"), default="json")
    export_parser.add_argument("--output-path", type=str)


def handle_runtime_lifecycle_command(
    args: argparse.Namespace,
    *,
    runtime_lifecycle_read_model: Any,
) -> int | None:
    if args.command == "runtime-lifecycle-inventory":
        result = runtime_lifecycle_read_model.build_lifecycle_inventory(**_scope_kwargs(args))
        _print_json(result)
        return 0

    if args.command == "runtime-lifecycle-read":
        result = runtime_lifecycle_read_model.read_compatibility_projection(
            surface=args.surface,
            report_group=args.report_group,
            **_scope_kwargs(args),
        )
        _print_json(result)
        return 0

    if args.command == "runtime-lifecycle-export":
        result = runtime_lifecycle_read_model.export_compatibility_projection(
            surface=args.surface,
            export_format=args.format,
            report_group=args.report_group,
            output_path=Path(args.output_path) if args.output_path else None,
            **_scope_kwargs(args),
        )
        _print_json(result)
        return 0

    return None


def _add_scope_args(parser: argparse.ArgumentParser) -> None:
    scope_group = parser.add_mutually_exclusive_group(required=True)
    scope_group.add_argument("--quest-root", type=str)
    scope_group.add_argument("--workspace-root", type=str)
    scope_group.add_argument("--db-path", type=str)


def _add_surface_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--surface",
        choices=("watch_state", "runtime_report", "workspace_storage_audit"),
        required=True,
    )
    parser.add_argument("--report-group", default="runtime_watch")


def _scope_kwargs(args: argparse.Namespace) -> dict[str, Path | None]:
    return {
        "quest_root": Path(args.quest_root) if getattr(args, "quest_root", None) else None,
        "workspace_root": Path(args.workspace_root) if getattr(args, "workspace_root", None) else None,
        "db_path": Path(args.db_path) if getattr(args, "db_path", None) else None,
    }


def _print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


__all__ = [
    "handle_runtime_lifecycle_command",
    "register_runtime_lifecycle_parsers",
]
