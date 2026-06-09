from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def handle_retention_command(
    args: Any,
    *,
    parser: Any,
    legacy_ds_retirement: Any,
    restore_index_detail_retention: Any,
    historical_body_retention: Any,
    historical_directory_retention: Any,
    runtime_lifecycle_payload_retention: Any,
    retention_surface_housekeeping: Any,
    cold_store_dedupe: Any,
    cold_store_reference_audit: Any,
    semantic_cold_store_retention: Any,
) -> int | None:
    if args.command == "legacy-ds-retire":
        if bool(args.archive_retention_apply) and not bool(args.archive_retention):
            parser.error("--archive-retention-apply requires --archive-retention")
        if bool(args.archive_retention_apply) and not bool(args.apply):
            parser.error("--archive-retention-apply requires --apply")
        result = legacy_ds_retirement.run_legacy_ds_retirement(
            profile_path=Path(args.profile),
            apply=bool(args.apply),
            archive_retention=bool(args.archive_retention),
            archive_retention_apply=bool(args.archive_retention_apply),
            archive_retention_min_mb=int(args.archive_retention_min_mb),
            archive_retention_cold_store_root=Path(args.archive_retention_cold_store_root)
            if args.archive_retention_cold_store_root
            else None,
        )
        _print_json(result)
        return 0

    if args.command == "restore-index-detail-retention":
        result = restore_index_detail_retention.run_restore_index_detail_retention(
            root=Path(args.root),
            apply=bool(args.apply),
            cold_store_root=Path(args.cold_store_root),
            min_mb=int(args.min_mb),
            max_files=args.max_files,
        )
        _print_json(result)
        return 0

    if args.command == "historical-body-retention":
        result = historical_body_retention.run_historical_body_retention(
            root=Path(args.root),
            apply=bool(args.apply),
            cold_store_root=Path(args.cold_store_root),
            min_mb=int(args.min_mb),
            max_files=args.max_files,
        )
        _print_json(result)
        return 0

    if args.command == "historical-directory-retention":
        result = historical_directory_retention.run_historical_directory_retention(
            root=Path(args.root),
            apply=bool(args.apply),
            cold_store_root=Path(args.cold_store_root),
            min_mb=int(args.min_mb),
            max_directories=args.max_directories,
        )
        _print_json(result)
        return 0

    if args.command == "runtime-lifecycle-payload-retention":
        if bool(args.repair_stale_sidecars):
            result = runtime_lifecycle_payload_retention.repair_runtime_lifecycle_sqlite_sidecars(
                db_path=Path(args.db),
                apply=bool(args.apply),
            )
        else:
            if not args.cold_store_root:
                parser.error("--cold-store-root is required unless --repair-stale-sidecars is set")
            result = runtime_lifecycle_payload_retention.run_runtime_lifecycle_payload_retention(
                db_path=Path(args.db),
                apply=bool(args.apply),
                cold_store_root=Path(args.cold_store_root),
                min_mb=int(args.min_mb),
                max_rows=args.max_rows,
                compact=bool(args.compact),
            )
        _print_json(result)
        return 0

    if args.command == "retention-surface-housekeeping":
        result = retention_surface_housekeeping.run_retention_surface_housekeeping(
            root=Path(args.root),
            apply=bool(args.apply),
            max_directories=args.max_directories,
        )
        _print_json(result)
        return 0

    if args.command == "cold-store-dedupe":
        result = cold_store_dedupe.run_cold_store_dedupe(
            root=Path(args.root),
            apply=bool(args.apply),
            min_mb=int(args.min_mb),
            max_groups=args.max_groups,
        )
        _print_json(result)
        return 0

    if args.command == "cold-store-reference-audit":
        result = cold_store_reference_audit.run_cold_store_reference_audit(
            root=Path(args.root),
            reference_roots=tuple(Path(item) for item in args.reference_root),
            apply=bool(args.apply),
            min_mb=int(args.min_mb),
            max_objects=args.max_objects,
        )
        _print_json(result)
        return 0

    if args.command == "semantic-cold-store-retention":
        result = semantic_cold_store_retention.run_semantic_cold_store_retention(
            root=Path(args.root),
            reference_roots=tuple(Path(item) for item in args.reference_root),
            apply=bool(args.apply),
            retire_exact_raw_restore=bool(args.retire_exact_raw_restore),
            min_mb=int(args.min_mb),
            max_objects=args.max_objects,
            reference_file_lists=tuple(Path(item) for item in args.reference_file_list),
        )
        _print_json(result)
        return 0

    return None


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


__all__ = ["handle_retention_command"]
