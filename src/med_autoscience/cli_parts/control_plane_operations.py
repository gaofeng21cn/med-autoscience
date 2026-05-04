from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping

from med_autoscience.cli_parts.payloads import _load_optional_object_payload_from_args
from med_autoscience.control_plane_command_catalog import CONTROL_PLANE_OPERATION_CLI_COMMANDS


_CONTROLLER_MODULES: Mapping[str, Any] | None = None


def _controller(module_name: str) -> Any:
    if _CONTROLLER_MODULES and module_name in _CONTROLLER_MODULES:
        return _CONTROLLER_MODULES[module_name]
    return importlib.import_module(f"med_autoscience.controllers.{module_name}")


def _workspace_roots(args: argparse.Namespace) -> list[Path]:
    return [Path(root) for root in args.workspace_root]


def _control_plane_snapshot(args: argparse.Namespace) -> dict[str, object] | None:
    return _load_optional_object_payload_from_args(
        payload_file=args.control_plane_snapshot_file,
        payload_json=args.control_plane_snapshot_json,
        file_label="--control-plane-snapshot-file",
        json_label="--control-plane-snapshot-json",
    )


def _retention_report(args: argparse.Namespace) -> dict[str, object] | None:
    return _load_optional_object_payload_from_args(
        payload_file=args.retention_report_file,
        payload_json=args.retention_report_json,
        file_label="--retention-report-file",
        json_label="--retention-report-json",
    )


def _emit_json(payload: dict[str, Any]) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _run_lifecycle_report(args: argparse.Namespace, *, governance: bool) -> int:
    lifecycle_report = _controller("artifact_lifecycle_operations_report")
    result = lifecycle_report.run_lifecycle_operations_report(
        workspace_roots=_workspace_roots(args),
        deep=bool(args.deep),
        max_files=args.max_files,
        max_seconds=args.max_seconds,
    )
    if governance:
        result = {
            **result,
            "surface": "storage_governance_report",
            "source_surface": result.get("surface"),
        }
    if args.markdown:
        print(lifecycle_report.render_lifecycle_operations_report_markdown(result))
        return 0
    return _emit_json(result)


def _run_cleanup_apply(args: argparse.Namespace, *, safe_cache_surface: bool) -> int:
    cleanup_apply = _controller("control_plane_cleanup_apply")
    cleanup_apply_kwargs: dict[str, object] = {
        "workspace_roots": _workspace_roots(args),
        "apply": args.apply,
        "control_plane_snapshot": _control_plane_snapshot(args),
    }
    report = _retention_report(args)
    if report is not None:
        cleanup_apply_kwargs["retention_report"] = report
    result = cleanup_apply.run_cleanup_apply(**cleanup_apply_kwargs)
    if safe_cache_surface:
        result = {
            **result,
            "surface": "control_plane_safe_cache_cleanup_apply",
            "source_surface": result.get("surface"),
        }
    return _emit_json(result)


def _handle_governance_report(args: argparse.Namespace) -> int:
    return _run_lifecycle_report(args, governance=True)


def _handle_safe_cache_cleanup_apply(args: argparse.Namespace) -> int:
    return _run_cleanup_apply(args, safe_cache_surface=True)


def _handle_migration_audit(args: argparse.Namespace) -> int:
    result = _controller("control_plane_migration_audit").run_migration_audit(
        workspace_roots=_workspace_roots(args),
        dry_run=True,
    )
    return _emit_json(result)


def _handle_backfill_apply(args: argparse.Namespace) -> int:
    result = _controller("control_plane_backfill_apply").run_backfill_apply(
        workspace_roots=_workspace_roots(args),
        apply=args.apply,
        control_plane_snapshot=_control_plane_snapshot(args),
    )
    return _emit_json(result)


def _handle_cleanup_apply(args: argparse.Namespace) -> int:
    return _run_cleanup_apply(args, safe_cache_surface=False)


def _handle_lifecycle_report(args: argparse.Namespace) -> int:
    return _run_lifecycle_report(args, governance=False)


def _handle_continuous_soak_summary(args: argparse.Namespace) -> int:
    result = _controller("continuous_soak_summary").build_continuous_soak_summary(
        workspace_roots=_workspace_roots(args),
        deep=bool(args.deep),
        max_files=args.max_files,
        max_seconds=args.max_seconds,
    )
    return _emit_json(result)


_CONTROL_PLANE_CLI_HANDLERS: dict[str, Callable[[argparse.Namespace], int]] = {
    "control-plane-governance-report": _handle_governance_report,
    "control-plane-safe-cache-cleanup-apply": _handle_safe_cache_cleanup_apply,
    "control-plane-migration-audit": _handle_migration_audit,
    "control-plane-backfill-apply": _handle_backfill_apply,
    "control-plane-cleanup-apply": _handle_cleanup_apply,
    "control-plane-lifecycle-report": _handle_lifecycle_report,
    "control-plane-continuous-soak-summary": _handle_continuous_soak_summary,
}


def handle_control_plane_operation_command(
    args: argparse.Namespace,
    *,
    controller_modules: Mapping[str, Any] | None = None,
) -> int | None:
    global _CONTROLLER_MODULES
    command = getattr(args, "command", "")
    if command not in CONTROL_PLANE_OPERATION_CLI_COMMANDS:
        return None
    previous_modules = _CONTROLLER_MODULES
    _CONTROLLER_MODULES = controller_modules
    try:
        return _CONTROL_PLANE_CLI_HANDLERS[command](args)
    finally:
        _CONTROLLER_MODULES = previous_modules
