from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable


LoadProfile = Callable[[str], Any]


def register_runtime_storage_parsers(subparsers: argparse._SubParsersAction) -> None:
    maintain_parser = subparsers.add_parser("runtime-maintain-storage")
    maintain_parser.add_argument("--profile", required=True)
    maintain_parser.add_argument("--study-id", type=str)
    maintain_parser.add_argument("--study-root", type=str)
    _add_storage_cleanup_options(maintain_parser)

    audit_parser = subparsers.add_parser("workspace-storage-audit")
    audit_parser.add_argument("--profile", required=True)
    audit_parser.add_argument("--study-id", type=str)
    audit_parser.add_argument("--all-studies", action="store_true")
    audit_parser.add_argument("--stopped-only", action="store_true")
    audit_parser.add_argument("--apply", action="store_true")
    _add_storage_cleanup_options(audit_parser)


def handle_runtime_storage_command(
    args: argparse.Namespace,
    *,
    parser: argparse.ArgumentParser,
    load_profile: LoadProfile,
    runtime_storage_maintenance: Any,
) -> int | None:
    if args.command == "runtime-maintain-storage":
        if bool(args.study_id) == bool(args.study_root):
            parser.error("Specify exactly one of --study-id or --study-root")
        result = runtime_storage_maintenance.maintain_runtime_storage(
            profile=load_profile(args.profile),
            study_id=args.study_id,
            study_root=Path(args.study_root) if args.study_root else None,
            **_storage_cleanup_options_from_args(args),
        )
        _print_json(result)
        return 0

    if args.command == "workspace-storage-audit":
        if bool(args.study_id) and bool(args.all_studies):
            parser.error("Specify at most one of --study-id or --all-studies")
        result = runtime_storage_maintenance.audit_workspace_storage(
            profile=load_profile(args.profile),
            study_id=args.study_id,
            all_studies=bool(args.all_studies) or not bool(args.study_id),
            stopped_only=bool(args.stopped_only),
            apply=bool(args.apply),
            **_storage_cleanup_options_from_args(args),
        )
        _print_json(result)
        return 0

    return None


def _add_storage_cleanup_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--no-worktrees", action="store_true")
    parser.add_argument("--older-than-hours", type=int, default=6)
    parser.add_argument("--jsonl-max-mb", type=int, default=64)
    parser.add_argument("--text-max-mb", type=int, default=16)
    parser.add_argument("--event-segment-max-mb", type=int, default=64)
    parser.add_argument("--no-slim-oversized-jsonl", action="store_true")
    parser.add_argument("--slim-jsonl-threshold-mb", type=int, default=8)
    parser.add_argument("--no-dedupe-worktrees", action="store_true")
    parser.add_argument("--dedupe-worktree-min-mb", type=int, default=16)
    parser.add_argument("--head-lines", type=int, default=200)
    parser.add_argument("--tail-lines", type=int, default=200)
    parser.add_argument("--allow-live-runtime", action="store_true")


def _storage_cleanup_options_from_args(args: argparse.Namespace) -> dict[str, object]:
    return {
        "include_worktrees": not bool(args.no_worktrees),
        "older_than_seconds": _positive_int(args.older_than_hours) * 3600,
        "jsonl_max_mb": _positive_int(args.jsonl_max_mb),
        "text_max_mb": _positive_int(args.text_max_mb),
        "event_segment_max_mb": _positive_int(args.event_segment_max_mb),
        "slim_jsonl_threshold_mb": (
            None if bool(args.no_slim_oversized_jsonl) else _positive_int(args.slim_jsonl_threshold_mb)
        ),
        "dedupe_worktree_min_mb": (
            None if bool(args.no_dedupe_worktrees) else _positive_int(args.dedupe_worktree_min_mb)
        ),
        "head_lines": _positive_int(args.head_lines),
        "tail_lines": _positive_int(args.tail_lines),
        "allow_live_runtime": bool(args.allow_live_runtime),
    }


def _positive_int(value: object) -> int:
    return max(1, int(value))


def _print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
