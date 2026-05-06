from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from med_autoscience.runtime_protocol.runtime_lifecycle_contract import MIGRATION_RUN_MODES, WORKSPACE_CLASSIFICATIONS
from med_autoscience.runtime_protocol.runtime_lifecycle_read_model import SUPPORTED_SURFACES


def register_runtime_lifecycle_parsers(subparsers: argparse._SubParsersAction) -> None:
    inventory_parser = subparsers.add_parser("runtime-lifecycle-inventory")
    _add_scope_args(inventory_parser)

    read_parser = subparsers.add_parser("runtime-lifecycle-read")
    _add_scope_args(read_parser)
    _add_surface_args(read_parser)
    read_parser.add_argument("--legacy-restore-import-diagnostic", action="store_true")

    export_parser = subparsers.add_parser("runtime-lifecycle-export")
    _add_scope_args(export_parser)
    _add_surface_args(export_parser)
    export_parser.add_argument("--format", choices=("json", "markdown"), default="json")
    export_parser.add_argument("--output-path", type=str)
    export_parser.add_argument("--legacy-restore-import-diagnostic", action="store_true")

    ledger_parser = subparsers.add_parser("runtime-lifecycle-ledger")
    ledger_parser.add_argument("--workspace-root", required=True, type=str)
    ledger_parser.add_argument("--mode", choices=MIGRATION_RUN_MODES, default="dry_run")
    ledger_parser.add_argument("--workspace-classification", choices=WORKSPACE_CLASSIFICATIONS, required=True)
    ledger_parser.add_argument("--migration-run-id", type=str)
    ledger_parser.add_argument("--skipped-reason", action="append", default=[])
    ledger_parser.add_argument("--next-required-action", type=str)
    ledger_parser.add_argument("--output-root", type=str)
    ledger_parser.add_argument("--write", action="store_true")
    ledger_parser.add_argument("--write-compat-export", action="store_true")

    materialize_parser = subparsers.add_parser("runtime-quest-materialize")
    materialize_parser.add_argument("--workspace-root", required=True, type=str)
    materialize_parser.add_argument("--quest-id", required=True, type=str)
    materialize_parser.add_argument("--node-id", required=True, type=str)
    materialize_parser.add_argument("--mode", choices=("dry_run", "apply"), default="dry_run")


def handle_runtime_lifecycle_command(
    args: argparse.Namespace,
    *,
    runtime_lifecycle_read_model: Any,
    runtime_lifecycle_migration: Any,
    quest_materializer: Any,
) -> int | None:
    if args.command == "runtime-lifecycle-inventory":
        result = runtime_lifecycle_read_model.build_lifecycle_inventory(**_scope_kwargs(args))
        _print_json(result)
        return 0

    if args.command == "runtime-lifecycle-read":
        result = runtime_lifecycle_read_model.read_compatibility_projection(
            surface=args.surface,
            report_group=args.report_group,
            legacy_restore_import_diagnostic=bool(args.legacy_restore_import_diagnostic),
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
            legacy_restore_import_diagnostic=bool(args.legacy_restore_import_diagnostic),
            **_scope_kwargs(args),
        )
        _print_json(result)
        return 0

    if args.command == "runtime-lifecycle-ledger":
        result = runtime_lifecycle_migration.build_migration_ledger(
            workspace_root=Path(args.workspace_root),
            mode=args.mode,
            workspace_classification=args.workspace_classification,
            migration_run_id=args.migration_run_id,
            skipped_reasons=tuple(args.skipped_reason or ()),
            next_required_action=args.next_required_action,
            output_root=Path(args.output_root) if args.output_root else None,
            write=bool(args.write),
            write_compat_export=bool(args.write_compat_export),
        )
        _print_json(result)
        return 0

    if args.command == "runtime-quest-materialize":
        result = quest_materializer.materialize_quest_workspace(
            workspace_root=Path(args.workspace_root),
            quest_id=args.quest_id,
            node_id=args.node_id,
            mode=args.mode,
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
        choices=tuple(sorted(SUPPORTED_SURFACES)),
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
