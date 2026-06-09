from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


_RUNTIME_RETENTION_APPLY_HELP = "requires the matching retention flag and explicit storage --apply where available"


def register_runtime_storage_parsers(subparsers: argparse._SubParsersAction) -> None:
    maintain_parser = subparsers.add_parser("maintain-runtime-storage")
    _add_profile_and_storage_selector_options(maintain_parser)
    _add_storage_cleanup_options(maintain_parser)
    _add_restore_proof_compaction_options(maintain_parser)
    _add_runtime_retention_options(maintain_parser, include_cold_store_root=True)
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
    _add_runtime_retention_options(audit_parser, include_cold_store_root=True)
    audit_parser.set_defaults(_command_parser=audit_parser)


def handle_runtime_storage_command(
    args: argparse.Namespace,
    *,
    parser: argparse.ArgumentParser,
    runtime_storage_maintenance: Any,
    load_profile: Any,
) -> int | None:
    if args.command == "maintain-runtime-storage":
        if args.legacy_ds_root:
            if not args.restore_proof_compaction:
                _command_parser(args, parser).error("--legacy-ds-root requires --restore-proof-compaction")
            if args.restore_proof_canary:
                _command_parser(args, parser).error("--legacy-ds-root does not support --restore-proof-canary")
            _reject_runtime_retention_for_legacy_ds(args, parser)
            profile = load_profile(args.profile)
            result = runtime_storage_maintenance.maintain_legacy_ds_runtime_storage(
                profile=profile,
                ds_root=Path(args.legacy_ds_root),
                restore_proof_buckets=tuple(args.restore_proof_buckets or ()),
                restore_proof_max_shards=args.restore_proof_max_shards,
                refs_only_state_index_pilot=bool(args.refs_only_state_index_pilot),
            )
            _print_json(result)
            return 0
        retention_kwargs = _runtime_retention_kwargs(args, parser=parser)
        profile = load_profile(args.profile)
        common_kwargs = _storage_maintenance_kwargs(args)
        if args.quest_root:
            result = runtime_storage_maintenance.maintain_quest_runtime_storage(
                profile=profile,
                quest_root=Path(args.quest_root),
                **common_kwargs,
                **retention_kwargs,
            )
        else:
            result = runtime_storage_maintenance.maintain_runtime_storage(
                profile=profile,
                study_id=args.study_id,
                study_root=None,
                **common_kwargs,
                **retention_kwargs,
            )
        _print_json(result)
        return 0

    if args.command == "workspace-storage-audit":
        if args.git_only and args.restore_proof_compaction:
            _command_parser(args, parser).error("--restore-proof-compaction is not supported with --git-only")
        retention_kwargs = _runtime_retention_kwargs(args, parser=parser, workspace_apply=bool(args.apply))
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
            **retention_kwargs,
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
    selector.add_argument("--legacy-ds-root", type=str)


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
    parser.add_argument("--restore-proof-max-shards", type=int)
    parser.add_argument("--restore-proof-bucket", action="append", dest="restore_proof_buckets")
    parser.add_argument("--include-parked-controller-stop", action="store_true")
    parser.add_argument("--include-operator-confirmed-parked-active", action="store_true")


def _add_runtime_retention_options(parser: argparse.ArgumentParser, *, include_cold_store_root: bool) -> None:
    parser.add_argument("--archive-retention", action="store_true")
    parser.add_argument("--archive-retention-apply", action="store_true", help=_RUNTIME_RETENTION_APPLY_HELP)
    parser.add_argument("--archive-retention-min-mb", type=int, default=16)
    if include_cold_store_root:
        parser.add_argument("--archive-retention-cold-store-root", type=str)
    parser.add_argument("--report-retention", action="store_true")
    parser.add_argument("--report-retention-apply", action="store_true", help=_RUNTIME_RETENTION_APPLY_HELP)
    parser.add_argument("--report-retention-keep-recent-days", type=int, default=1)
    parser.add_argument("--report-retention-daily-samples", type=int, default=2)
    parser.add_argument("--report-retention-max-files", type=int)
    parser.add_argument("--attempt-evidence-capsules", action="store_true")
    parser.add_argument("--semantic-process-retention", action="store_true")
    parser.add_argument("--semantic-process-retention-apply", action="store_true", help=_RUNTIME_RETENTION_APPLY_HELP)
    parser.add_argument("--semantic-retention-max-log-bytes", type=int, default=256 * 1024)
    parser.add_argument("--semantic-retention-max-raw-bytes", type=int, default=1024 * 1024)
    parser.add_argument("--semantic-retention-keep-failed-raw", action="store_true", default=True)
    parser.add_argument("--semantic-retention-max-files", type=int)


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
        "restore_proof_max_shards": args.restore_proof_max_shards,
        "restore_proof_buckets": tuple(args.restore_proof_buckets or ()),
        "include_parked_controller_stop": bool(args.include_parked_controller_stop),
        "include_operator_confirmed_parked_active": bool(args.include_operator_confirmed_parked_active),
        "refs_only_state_index_pilot": bool(args.refs_only_state_index_pilot),
        "refs_only_state_index_only": bool(args.refs_only_state_index_only),
    }


def _runtime_retention_kwargs(
    args: argparse.Namespace,
    *,
    parser: argparse.ArgumentParser,
    workspace_apply: bool = True,
) -> dict[str, Any]:
    command_parser = _command_parser(args, parser)
    archive_retention = bool(getattr(args, "archive_retention", False))
    archive_retention_apply = bool(getattr(args, "archive_retention_apply", False))
    report_retention = bool(getattr(args, "report_retention", False))
    report_retention_apply = bool(getattr(args, "report_retention_apply", False))
    semantic_process_retention = bool(getattr(args, "semantic_process_retention", False))
    semantic_process_retention_apply = bool(getattr(args, "semantic_process_retention_apply", False))
    attempt_evidence_capsules = bool(getattr(args, "attempt_evidence_capsules", False)) or semantic_process_retention
    if archive_retention_apply and not archive_retention:
        command_parser.error("--archive-retention-apply requires --archive-retention")
    if report_retention_apply and not report_retention:
        command_parser.error("--report-retention-apply requires --report-retention")
    if semantic_process_retention_apply and not semantic_process_retention:
        command_parser.error("--semantic-process-retention-apply requires --semantic-process-retention")
    if (archive_retention_apply or report_retention_apply or semantic_process_retention_apply) and not workspace_apply:
        command_parser.error("retention apply flags require workspace --apply")
    cold_store_root = getattr(args, "archive_retention_cold_store_root", None)
    return {
        "archive_retention": archive_retention,
        "archive_retention_apply": archive_retention_apply,
        "archive_retention_min_mb": int(getattr(args, "archive_retention_min_mb", 16)),
        "archive_retention_cold_store_root": Path(cold_store_root) if cold_store_root else None,
        "report_retention": report_retention,
        "report_retention_apply": report_retention_apply,
        "report_retention_keep_recent_days": int(getattr(args, "report_retention_keep_recent_days", 1)),
        "report_retention_daily_samples": int(getattr(args, "report_retention_daily_samples", 2)),
        "report_retention_max_files": getattr(args, "report_retention_max_files", None),
        "attempt_evidence_capsules": attempt_evidence_capsules,
        "semantic_process_retention": semantic_process_retention,
        "semantic_process_retention_apply": semantic_process_retention_apply,
        "semantic_retention_max_log_bytes": int(getattr(args, "semantic_retention_max_log_bytes", 256 * 1024)),
        "semantic_retention_max_raw_bytes": int(getattr(args, "semantic_retention_max_raw_bytes", 1024 * 1024)),
        "semantic_retention_keep_failed_raw": bool(getattr(args, "semantic_retention_keep_failed_raw", True)),
        "semantic_retention_max_files": getattr(args, "semantic_retention_max_files", None),
    }


def _reject_runtime_retention_for_legacy_ds(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    retention_flags = (
        "archive_retention",
        "archive_retention_apply",
        "report_retention",
        "report_retention_apply",
        "archive_retention_cold_store_root",
        "attempt_evidence_capsules",
        "semantic_process_retention",
        "semantic_process_retention_apply",
    )
    if any(bool(getattr(args, name, False)) for name in retention_flags):
        _command_parser(args, parser).error("runtime retention flags require --study-id or --quest-root")


def _print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


__all__ = ["handle_runtime_storage_command", "register_runtime_storage_parsers"]
