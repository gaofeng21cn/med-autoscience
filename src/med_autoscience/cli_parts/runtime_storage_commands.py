from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def register_runtime_storage_parsers(subparsers: argparse._SubParsersAction) -> None:
    maintain_parser = subparsers.add_parser("maintain-runtime-storage")
    _add_profile_and_storage_selector_options(maintain_parser)
    _add_storage_cleanup_options(maintain_parser)
    _add_restore_proof_compaction_options(maintain_parser)
    maintain_parser.set_defaults(_command_parser=maintain_parser)

    audit_parser = subparsers.add_parser("workspace-storage-audit")
    audit_parser.add_argument("--profile", required=True)
    audit_parser.add_argument("--study-id", type=str)
    audit_parser.add_argument("--all-studies", action="store_true")
    audit_parser.add_argument("--stopped-only", action="store_true")
    audit_parser.add_argument("--apply", action="store_true")
    audit_parser.add_argument("--git-only", action="store_true")
    audit_parser.add_argument("--reinitialize-empty-workspace-git", action="store_true")
    audit_parser.add_argument("--retire-workspace-root-git", action="store_true")
    _add_storage_cleanup_options(audit_parser)
    _add_restore_proof_compaction_options(audit_parser)
    audit_parser.set_defaults(_command_parser=audit_parser)


def handle_runtime_storage_command(
    args: argparse.Namespace,
    *,
    parser: argparse.ArgumentParser,
    runtime_storage_maintenance: Any,
    load_profile: Any,
) -> int | None:
    if args.command == "maintain-runtime-storage":
        if bool(args.study_id) == bool(args.quest_root):
            parser.error("Specify exactly one of --study-id or --quest-root")
        profile = load_profile(args.profile)
        common_kwargs = _storage_maintenance_kwargs(args)
        if args.quest_root:
            result = runtime_storage_maintenance.maintain_quest_runtime_storage(
                profile=profile,
                quest_root=Path(args.quest_root),
                **common_kwargs,
            )
        else:
            result = runtime_storage_maintenance.maintain_runtime_storage(
                profile=profile,
                study_id=args.study_id,
                study_root=None,
                **common_kwargs,
            )
        _print_json(result)
        return 0

    if args.command == "workspace-storage-audit":
        if args.git_only and args.restore_proof_compaction:
            _command_parser(args, parser).error("--restore-proof-compaction is not supported with --git-only")
        profile = load_profile(args.profile)
        result = runtime_storage_maintenance.audit_workspace_storage(
            profile=profile,
            study_id=args.study_id,
            all_studies=bool(args.all_studies),
            stopped_only=bool(args.stopped_only),
            apply=bool(args.apply),
            git_only=bool(args.git_only),
            reinitialize_empty_workspace_git=bool(args.reinitialize_empty_workspace_git),
            retire_workspace_root_git=bool(args.retire_workspace_root_git),
            **_storage_maintenance_kwargs(args),
        )
        _print_json(result)
        return 0

    return None


def _command_parser(args: argparse.Namespace, fallback: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser = getattr(args, "_command_parser", None)
    return parser if isinstance(parser, argparse.ArgumentParser) else fallback


def _add_profile_and_storage_selector_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--profile", required=True)
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--study-id", type=str)
    selector.add_argument("--quest-root", type=str)


def _add_storage_cleanup_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--no-worktrees", action="store_true")
    parser.add_argument("--older-than-hours", type=int, default=6)
    parser.add_argument("--jsonl-max-mb", type=int, default=64)
    parser.add_argument("--text-max-mb", type=int, default=16)
    parser.add_argument("--event-segment-max-mb", type=int, default=64)
    parser.add_argument("--slim-jsonl-threshold-mb", type=int, default=8)
    parser.add_argument("--no-slim-oversized-jsonl", action="store_true")
    parser.add_argument("--dedupe-worktree-min-mb", type=int, default=16)
    parser.add_argument("--no-dedupe-worktrees", action="store_true")
    parser.add_argument("--head-lines", type=int, default=200)
    parser.add_argument("--tail-lines", type=int, default=200)
    parser.add_argument("--allow-live-runtime", action="store_true")
    parser.add_argument("--refs-only-state-index-pilot", action="store_true")
    parser.add_argument("--refs-only-state-index-only", action="store_true")


def _add_restore_proof_compaction_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--restore-proof-compaction", action="store_true")
    parser.add_argument("--restore-proof-canary", action="store_true")
    parser.add_argument("--restore-proof-canary-entry-limit", type=int, default=20)
    parser.add_argument("--restore-proof-bucket", action="append", dest="restore_proof_buckets")
    parser.add_argument("--include-parked-controller-stop", action="store_true")
    parser.add_argument("--include-operator-confirmed-parked-active", action="store_true")


def _storage_maintenance_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "include_worktrees": not bool(args.no_worktrees),
        "older_than_seconds": int(args.older_than_hours) * 3600,
        "jsonl_max_mb": int(args.jsonl_max_mb),
        "text_max_mb": int(args.text_max_mb),
        "event_segment_max_mb": int(args.event_segment_max_mb),
        "slim_jsonl_threshold_mb": None
        if bool(args.no_slim_oversized_jsonl)
        else int(args.slim_jsonl_threshold_mb),
        "dedupe_worktree_min_mb": None if bool(args.no_dedupe_worktrees) else int(args.dedupe_worktree_min_mb),
        "head_lines": int(args.head_lines),
        "tail_lines": int(args.tail_lines),
        "allow_live_runtime": bool(args.allow_live_runtime),
        "restore_proof_compaction": bool(args.restore_proof_compaction),
        "restore_proof_canary": bool(args.restore_proof_canary),
        "restore_proof_canary_entry_limit": int(args.restore_proof_canary_entry_limit),
        "restore_proof_buckets": tuple(args.restore_proof_buckets or ()),
        "include_parked_controller_stop": bool(args.include_parked_controller_stop),
        "include_operator_confirmed_parked_active": bool(args.include_operator_confirmed_parked_active),
        "refs_only_state_index_pilot": bool(args.refs_only_state_index_pilot),
        "refs_only_state_index_only": bool(args.refs_only_state_index_only),
    }


def _print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


__all__ = ["handle_runtime_storage_command", "register_runtime_storage_parsers"]
