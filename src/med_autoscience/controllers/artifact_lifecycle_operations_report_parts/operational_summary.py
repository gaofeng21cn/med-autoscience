from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


DEFAULT_SUMMARY_LIMIT = 5


def build_lifecycle_operational_summary(
    *,
    summary: Mapping[str, Any],
    source_totals: Mapping[str, Any],
    retention_plan: Mapping[str, Any],
    workspaces: Iterable[Mapping[str, Any]],
    mutation_policy: Mapping[str, Any],
    limit: int = DEFAULT_SUMMARY_LIMIT,
) -> dict[str, Any]:
    workspace_list = [dict(workspace) for workspace in workspaces]
    operations = _workspace_operation_samples(workspace_list)
    return {
        "storage_budget": _storage_budget(
            summary=summary,
            retention_plan=retention_plan,
            mutation_policy=mutation_policy,
        ),
        "top_growth_buckets": _top_growth_buckets(source_totals, limit=limit),
        "blocked_cleanup_reasons": _blocked_cleanup_reasons(operations, limit=limit),
        "projection_regeneration_candidates": _projection_regeneration_candidates(
            operations,
            limit=limit,
        ),
        "restore_contract_gaps": _restore_contract_gaps(operations, limit=limit),
        "operation_listing": "bounded",
        "operation_sample_truncated": any(
            bool(_mapping(workspace.get("retention_plan")).get("operation_sample_truncated"))
            for workspace in workspace_list
        ),
    }


def _storage_budget(
    *,
    summary: Mapping[str, Any],
    retention_plan: Mapping[str, Any],
    mutation_policy: Mapping[str, Any],
) -> dict[str, Any]:
    retention_summary = _mapping(retention_plan.get("summary"))
    return {
        "mode": "bounded_read_only",
        "total_bytes": _int(summary.get("total_bytes")),
        "classified_bytes": _int(summary.get("classified_bytes")),
        "statistical_bytes": _int(summary.get("statistical_bytes")),
        "file_count": _int(summary.get("classified_file_count"))
        + _int(summary.get("statistical_file_count")),
        "read_only": bool(mutation_policy.get("read_only")),
        "physical_cleanup_performed": bool(mutation_policy.get("physical_cleanup_performed")),
        "cleanup_apply_supported": bool(mutation_policy.get("cleanup_apply_supported")),
        "operation_count": _int(retention_summary.get("operation_count")),
        "applyable_action_counts": dict(_mapping(retention_summary.get("applyable_action_counts"))),
    }


def _top_growth_buckets(source_totals: Mapping[str, Any], *, limit: int) -> list[dict[str, Any]]:
    buckets: list[dict[str, Any]] = []
    for source_bucket, totals_value in source_totals.items():
        totals = _mapping(totals_value)
        bytes_count = _int(totals.get("bytes"))
        if bytes_count <= 0:
            continue
        buckets.append(
            {
                "source_bucket": str(source_bucket),
                "bytes": bytes_count,
                "file_count": _int(totals.get("file_count")),
                "classified_file_count": _int(totals.get("classified_file_count")),
                "statistical_directory_count": _int(totals.get("statistical_directory_count")),
                "scan_mode": _text(totals.get("scan_mode")) or "none",
            }
        )
    return sorted(buckets, key=lambda item: (-item["bytes"], item["source_bucket"]))[:limit]


def _blocked_cleanup_reasons(
    operations: Iterable[Mapping[str, Any]],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    reasons: dict[str, dict[str, Any]] = {}
    for operation in operations:
        action = _text(operation.get("retention_action"))
        path = _text(operation.get("workspace_relative_path"))
        for blocker in _string_list(operation.get("blockers")):
            record = reasons.setdefault(
                blocker,
                {"reason": blocker, "count": 0, "actions": set(), "sample_paths": []},
            )
            record["count"] += 1
            if action:
                record["actions"].add(action)
            if path and path not in record["sample_paths"]:
                record["sample_paths"].append(path)
    return [
        {
            "reason": record["reason"],
            "count": record["count"],
            "actions": sorted(record["actions"]),
            "sample_paths": record["sample_paths"][:limit],
        }
        for record in sorted(reasons.values(), key=lambda item: (-item["count"], item["reason"]))[:limit]
    ]


def _projection_regeneration_candidates(
    operations: Iterable[Mapping[str, Any]],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    candidates = [
        {
            "workspace_relative_path": _text(operation.get("workspace_relative_path")),
            "retention_action": _text(operation.get("retention_action")),
            "role": _text(operation.get("role")),
            "lifecycle": _text(operation.get("lifecycle")),
            "removal_marker": _text(operation.get("removal_marker")),
            "physical_delete_allowed": bool(operation.get("physical_delete_allowed")),
            "canonical_regeneration_gate": dict(_mapping(operation.get("canonical_regeneration_gate"))),
            "blockers": _string_list(operation.get("blockers")),
        }
        for operation in operations
        if operation.get("retention_action") == "regenerate_projection_then_remove_stale"
    ]
    return sorted(candidates, key=lambda item: item["workspace_relative_path"])[:limit]


def _restore_contract_gaps(
    operations: Iterable[Mapping[str, Any]],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for operation in operations:
        gate = _mapping(operation.get("restore_contract_gate"))
        if not bool(gate.get("required")):
            continue
        status = _text(gate.get("status")) or "unknown"
        if status == "not_required":
            continue
        gaps.append(
            {
                "workspace_relative_path": _text(operation.get("workspace_relative_path")),
                "retention_action": _text(operation.get("retention_action")),
                "restore_contract_gate": dict(gate),
                "blockers": _string_list(operation.get("blockers")),
                "physical_archive_compress_allowed": bool(
                    operation.get("physical_archive_compress_allowed")
                ),
            }
        )
    return sorted(gaps, key=lambda item: item["workspace_relative_path"])[:limit]


def _workspace_operation_samples(workspaces: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    operations: list[Mapping[str, Any]] = []
    for workspace in workspaces:
        retention_plan = _mapping(workspace.get("retention_plan"))
        operations.extend(
            dict(operation)
            for operation in _sequence(retention_plan.get("operation_sample"))
            if isinstance(operation, Mapping)
        )
    return operations


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> tuple[Any, ...] | list[Any]:
    return value if isinstance(value, list | tuple) else ()


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _int(value: object) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


__all__ = [
    "DEFAULT_SUMMARY_LIMIT",
    "build_lifecycle_operational_summary",
]
