from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from datetime import datetime, timedelta, timezone
from typing import Any


SCHEMA_VERSION = 1
SURFACE_KIND = "storage_governance_policy_projection"
DEFAULT_THRESHOLD_SCHEMA: dict[str, Any] = {
    "workspace": {
        "warning_bytes": 50 * 1024 * 1024 * 1024,
        "critical_bytes": 100 * 1024 * 1024 * 1024,
    },
    "study": {
        "warning_bytes": 10 * 1024 * 1024 * 1024,
        "critical_bytes": 25 * 1024 * 1024 * 1024,
    },
    "growth": {
        "stable_ratio": 0.05,
        "growth_ratio": 0.2,
    },
}


class StorageGovernancePolicyKernel:
    def __init__(self, threshold_schema: Mapping[str, Any] | None = None) -> None:
        self.threshold_schema = _merge_threshold_schema(threshold_schema)

    def build_projection(self, lifecycle_report: Mapping[str, Any]) -> dict[str, Any]:
        workspaces = [_workspace_projection(workspace, threshold_schema=self.threshold_schema) for workspace in _sequence(lifecycle_report.get("workspaces"))]
        operations = _operation_samples(_sequence(lifecycle_report.get("workspaces")))
        recommended_operations = _recommended_operations(operations)
        restore_contract_gaps = _restore_contract_gaps(operations)
        budget_status = _budget_status(
            _int(_mapping(lifecycle_report.get("summary")).get("total_bytes")),
            self.threshold_schema["workspace"],
        )
        trend_summary = _trend_summary(lifecycle_report)
        return {
            "surface_kind": SURFACE_KIND,
            "schema_version": SCHEMA_VERSION,
            "mutation_policy": _mutation_policy(),
            "threshold_schema": self.threshold_schema,
            "budget_status": budget_status,
            "trend_delta": _trend_delta(lifecycle_report),
            "previous_snapshot": trend_summary["previous_snapshot"],
            "trend_summary": trend_summary,
            "alert_status": _alert_status(
                budget_status=budget_status,
                recommended_operations=recommended_operations,
                restore_contract_gaps=restore_contract_gaps,
            ),
            "top_growth_buckets": _top_growth_buckets(_mapping(lifecycle_report.get("source_totals"))),
            "blocked_reasons": _blocked_reasons(operations),
            "restore_contract_gaps": restore_contract_gaps,
            "recommended_operations": recommended_operations,
            "next_safe_action": _next_safe_action(
                recommended_operations=recommended_operations,
                restore_contract_gaps=restore_contract_gaps,
            ),
            "workspaces": workspaces,
        }


def build_storage_governance_policy_projection(
    *,
    lifecycle_report: Mapping[str, Any],
    threshold_schema: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return StorageGovernancePolicyKernel(threshold_schema).build_projection(lifecycle_report)


def _workspace_projection(
    workspace: Any,
    *,
    threshold_schema: Mapping[str, Any],
) -> dict[str, Any]:
    workspace_mapping = _mapping(workspace)
    operations = _operation_samples([workspace_mapping])
    study_totals = _study_totals(workspace_mapping)
    return {
        "workspace_root": _text(workspace_mapping.get("workspace_root")),
        "budget_status": _budget_status(
            _int(_mapping(workspace_mapping.get("summary")).get("total_bytes")),
            _mapping(threshold_schema.get("workspace")),
        ),
        "top_growth_buckets": _top_growth_buckets(_mapping(workspace_mapping.get("source_totals"))),
        "blocked_reasons": _blocked_reasons(operations),
        "recommended_operations": _recommended_operations(operations),
        "next_safe_action": _next_safe_action(
            recommended_operations=_recommended_operations(operations),
            restore_contract_gaps=_restore_contract_gaps(operations),
        ),
        "studies": [
            _study_projection(study, total_bytes=study_totals.get(_text(_mapping(study).get("study_id")), 0), threshold_schema=threshold_schema)
            for study in _sequence(workspace_mapping.get("studies"))
        ],
    }


def _study_projection(
    study: Any,
    *,
    total_bytes: int,
    threshold_schema: Mapping[str, Any],
) -> dict[str, Any]:
    study_mapping = _mapping(study)
    return {
        "study_id": _text(study_mapping.get("study_id")),
        "workspace_relative_study_root": _text(study_mapping.get("workspace_relative_study_root")),
        "budget_status": _budget_status(total_bytes, _mapping(threshold_schema.get("study"))),
        "recommended_operations": [],
        "next_safe_action": {
            "action": "monitor_storage_governance_projection",
            "read_only": True,
            "reason": "no_study_level_operation_projection",
        },
    }


def _budget_status(total_bytes: int, thresholds: Mapping[str, Any]) -> dict[str, Any]:
    warning_bytes = _int(thresholds.get("warning_bytes"))
    critical_bytes = _int(thresholds.get("critical_bytes"))
    if critical_bytes and total_bytes >= critical_bytes:
        status = "critical"
    elif warning_bytes and total_bytes >= warning_bytes:
        status = "warning"
    else:
        status = "within_budget"
    return {
        "status": status,
        "total_bytes": total_bytes,
        "warning_bytes": warning_bytes,
        "critical_bytes": critical_bytes,
    }


def _trend_delta(report: Mapping[str, Any]) -> dict[str, Any]:
    current = _int(_mapping(report.get("summary")).get("total_bytes"))
    previous = _previous_total_bytes(report)
    delta = current - previous
    ratio = round(delta / previous, 6) if previous else None
    growth_thresholds = _mapping(_merge_threshold_schema(_mapping(report.get("threshold_schema"))).get("growth"))
    stable_ratio = float(growth_thresholds.get("stable_ratio") or 0.05)
    growth_ratio = float(growth_thresholds.get("growth_ratio") or 0.2)
    if previous == 0:
        growth_bucket = "baseline"
    elif ratio is not None and ratio < 0:
        growth_bucket = "decrease"
    elif ratio is not None and ratio <= stable_ratio:
        growth_bucket = "stable"
    elif ratio is not None and ratio <= growth_ratio:
        growth_bucket = "moderate_growth"
    else:
        growth_bucket = "growth"
    return {
        "current_bytes": current,
        "previous_bytes": previous,
        "delta_bytes": delta,
        "delta_ratio": ratio,
        "growth_bucket": growth_bucket,
    }


def _trend_summary(report: Mapping[str, Any]) -> dict[str, Any]:
    history = _mapping(report.get("storage_governance_history"))
    recordable_entry = _mapping(history.get("recordable_entry"))
    current = _int(recordable_entry.get("total_bytes")) or _int(_mapping(report.get("summary")).get("total_bytes"))
    history_entries = _history_entries(history)
    previous_snapshot = _previous_snapshot(report, history_entries=history_entries)
    observed_at = _text(recordable_entry.get("observed_at"))
    current_observed_at = _parse_observed_at(observed_at) or _latest_observed_at(history_entries)
    return {
        "current_bytes": current,
        "previous_snapshot": _snapshot_delta(current=current, snapshot=previous_snapshot),
        "windows": {
            "7d": _window_trend(
                current=current,
                current_observed_at=current_observed_at,
                history_entries=history_entries,
                window_days=7,
            ),
            "30d": _window_trend(
                current=current,
                current_observed_at=current_observed_at,
                history_entries=history_entries,
                window_days=30,
            ),
        },
        "history_sample_count": len(history_entries),
    }


def _history_entries(history: Mapping[str, Any]) -> list[dict[str, Any]]:
    entries = [
        {
            "observed_at": _text(_mapping(entry).get("observed_at")),
            "total_bytes": _int(_mapping(entry).get("total_bytes")),
        }
        for entry in _sequence(history.get("history_entries"))
        if _text(_mapping(entry).get("observed_at"))
    ]
    return sorted(entries, key=lambda item: item["observed_at"])


def _previous_snapshot(
    report: Mapping[str, Any],
    *,
    history_entries: list[dict[str, Any]],
) -> dict[str, Any] | None:
    history = _mapping(report.get("storage_governance_history"))
    previous_snapshot = _mapping(history.get("previous_snapshot"))
    if previous_snapshot:
        return {
            "observed_at": _text(previous_snapshot.get("observed_at")),
            "total_bytes": _int(previous_snapshot.get("total_bytes")),
        }
    previous_total_bytes = _int(_mapping(report.get("previous_summary")).get("total_bytes"))
    if previous_total_bytes:
        return {
            "observed_at": "",
            "total_bytes": previous_total_bytes,
        }
    return history_entries[-1] if history_entries else None


def _snapshot_delta(current: int, *, snapshot: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not snapshot:
        return None
    previous = _int(snapshot.get("total_bytes"))
    delta = current - previous
    return {
        "observed_at": _text(snapshot.get("observed_at")),
        "total_bytes": previous,
        "delta_bytes": delta,
        "delta_ratio": round(delta / previous, 6) if previous else None,
        "growth_bucket": _growth_bucket(previous=previous, current=current),
    }


def _window_trend(
    *,
    current: int,
    current_observed_at: datetime | None,
    history_entries: list[dict[str, Any]],
    window_days: int,
) -> dict[str, Any]:
    candidates = _window_candidates(
        current_observed_at=current_observed_at,
        history_entries=history_entries,
        window_days=window_days,
    )
    baseline = candidates[0] if candidates else None
    baseline_bytes = _int(_mapping(baseline).get("total_bytes"))
    delta = current - baseline_bytes if baseline else None
    return {
        "window_days": window_days,
        "sample_count": len(candidates) + 1,
        "baseline_bytes": baseline_bytes if baseline else None,
        "current_bytes": current,
        "delta_bytes": delta,
        "delta_ratio": round(delta / baseline_bytes, 6) if baseline_bytes and delta is not None else None,
        "growth_bucket": _growth_bucket(previous=baseline_bytes, current=current) if baseline else "baseline",
    }


def _window_candidates(
    *,
    current_observed_at: datetime | None,
    history_entries: list[dict[str, Any]],
    window_days: int,
) -> list[dict[str, Any]]:
    if current_observed_at is None:
        return history_entries[-1:]
    cutoff = current_observed_at - timedelta(days=window_days)
    candidates = [
        entry
        for entry in history_entries
        if (observed_at := _parse_observed_at(entry["observed_at"])) is not None
        and cutoff <= observed_at <= current_observed_at
    ]
    return candidates or history_entries[-1:]


def _previous_total_bytes(report: Mapping[str, Any]) -> int:
    trend_history = _mapping(report.get("storage_governance_history"))
    previous_snapshot = _mapping(trend_history.get("previous_snapshot"))
    previous = _int(previous_snapshot.get("total_bytes"))
    if previous:
        return previous
    return _int(_mapping(report.get("previous_summary")).get("total_bytes"))


def _latest_observed_at(history_entries: list[dict[str, Any]]) -> datetime | None:
    for entry in reversed(history_entries):
        observed_at = _parse_observed_at(entry["observed_at"])
        if observed_at is not None:
            return observed_at
    return None


def _parse_observed_at(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _growth_bucket(*, previous: int, current: int) -> str:
    if previous == 0:
        return "baseline"
    ratio = (current - previous) / previous
    if ratio < 0:
        return "decrease"
    if ratio <= DEFAULT_THRESHOLD_SCHEMA["growth"]["stable_ratio"]:
        return "stable"
    if ratio <= DEFAULT_THRESHOLD_SCHEMA["growth"]["growth_ratio"]:
        return "moderate_growth"
    return "growth"


def _alert_status(
    *,
    budget_status: Mapping[str, Any],
    recommended_operations: Iterable[Mapping[str, Any]],
    restore_contract_gaps: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    if list(restore_contract_gaps):
        return _alert_record(
            status="blocked_restore_contract",
            severity="blocked",
            reason="restore_contract_gap",
        )
    for operation in recommended_operations:
        if operation.get("operation_type") == "delete_safe_cache_candidate":
            return _alert_record(
                status="safe_cache_candidate_pending_approval",
                severity="warning",
                reason="safe_cache_candidate_available",
            )
    status = _text(budget_status.get("status")) or "within_budget"
    return _alert_record(status=status, severity=_budget_alert_severity(status), reason=f"storage_budget_{status}")


def _alert_record(*, status: str, severity: str, reason: str) -> dict[str, Any]:
    return {
        "status": status,
        "severity": severity,
        "reason": reason,
        "read_only": True,
        "physical_apply_performed": False,
    }


def _budget_alert_severity(status: str) -> str:
    return {
        "critical": "critical",
        "warning": "warning",
        "within_budget": "info",
    }.get(status, "info")


def _top_growth_buckets(source_totals: Mapping[str, Any], *, limit: int = 5) -> list[dict[str, Any]]:
    buckets = [
        {
            "source_bucket": str(bucket),
            "bytes": _int(_mapping(totals).get("bytes")),
            "file_count": _int(_mapping(totals).get("file_count")),
            "scan_mode": _text(_mapping(totals).get("scan_mode")) or "none",
        }
        for bucket, totals in source_totals.items()
        if _int(_mapping(totals).get("bytes")) > 0
    ]
    return sorted(buckets, key=lambda item: (-item["bytes"], item["source_bucket"]))[:limit]


def _blocked_reasons(operations: Iterable[Mapping[str, Any]], *, limit: int = 10) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    for operation in operations:
        counts.update(_string_list(operation.get("blockers")))
    return [
        {"reason": reason, "count": count}
        for reason, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def _recommended_operations(operations: Iterable[Mapping[str, Any]], *, limit: int = 10) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    for operation in operations:
        retention_action = _text(operation.get("retention_action"))
        if retention_action == "restore_contract_required" or _restore_gate_required(operation):
            recommendations.append(_operation_recommendation(operation, operation_type="restore_contract_gap"))
        elif retention_action == "delete_safe_cache" and bool(operation.get("physical_delete_allowed")):
            recommendations.append(_operation_recommendation(operation, operation_type="delete_safe_cache_candidate"))
        elif retention_action == "regenerate_projection_then_remove_stale":
            recommendations.append(_operation_recommendation(operation, operation_type="regenerate_projection_before_cleanup"))
    return sorted(
        recommendations,
        key=lambda item: (
            _operation_priority(str(item.get("operation_type") or "")),
            str(item.get("workspace_relative_path") or ""),
        ),
    )[:limit]


def _operation_recommendation(operation: Mapping[str, Any], *, operation_type: str) -> dict[str, Any]:
    return {
        "operation_type": operation_type,
        "workspace_relative_path": _text(operation.get("workspace_relative_path")),
        "retention_action": _text(operation.get("retention_action")),
        "read_only": True,
        "physical_apply_performed": False,
        "physical_delete_allowed": bool(operation.get("physical_delete_allowed")),
        "blockers": _string_list(operation.get("blockers")),
    }


def _operation_priority(operation_type: str) -> int:
    return {
        "restore_contract_gap": 0,
        "delete_safe_cache_candidate": 1,
        "regenerate_projection_before_cleanup": 2,
    }.get(operation_type, 99)


def _restore_contract_gaps(operations: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for operation in operations:
        if not _restore_gate_required(operation):
            continue
        gaps.append(
            {
                "workspace_relative_path": _text(operation.get("workspace_relative_path")),
                "retention_action": _text(operation.get("retention_action")),
                "restore_contract_gate": dict(_mapping(operation.get("restore_contract_gate"))),
                "blockers": _string_list(operation.get("blockers")),
            }
        )
    return sorted(gaps, key=lambda item: item["workspace_relative_path"])


def _restore_gate_required(operation: Mapping[str, Any]) -> bool:
    gate = _mapping(operation.get("restore_contract_gate"))
    return bool(gate.get("required")) and _text(gate.get("status")) not in {"", "not_required"}


def _next_safe_action(
    *,
    recommended_operations: Iterable[Mapping[str, Any]],
    restore_contract_gaps: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    if list(restore_contract_gaps):
        return {
            "action": "define_restore_contract_before_cleanup",
            "read_only": True,
            "reason": "restore_contract_gap",
        }
    for operation in recommended_operations:
        if operation.get("operation_type") == "delete_safe_cache_candidate":
            return {
                "action": "review_safe_cache_delete_candidate",
                "read_only": True,
                "reason": "safe_cache_candidate_available",
            }
    for operation in recommended_operations:
        if operation.get("operation_type") == "regenerate_projection_before_cleanup":
            return {
                "action": "regenerate_projection_before_cleanup_review",
                "read_only": True,
                "reason": "canonical_regeneration_required",
            }
    return {
        "action": "monitor_storage_governance_projection",
        "read_only": True,
        "reason": "no_safe_operation_candidate",
    }


def _operation_samples(workspaces: Iterable[Any]) -> list[Mapping[str, Any]]:
    operations: list[Mapping[str, Any]] = []
    for workspace in workspaces:
        retention_plan = _mapping(_mapping(workspace).get("retention_plan"))
        operations.extend(
            dict(operation)
            for operation in _sequence(retention_plan.get("operation_sample"))
            if isinstance(operation, Mapping)
        )
    return operations


def _study_totals(workspace: Mapping[str, Any]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for artifact in _sequence(workspace.get("artifact_sample")):
        artifact_mapping = _mapping(artifact)
        study_id = _text(artifact_mapping.get("study_id"))
        if not study_id:
            continue
        totals[study_id] = totals.get(study_id, 0) + _int(artifact_mapping.get("size_bytes"))
    return totals


def _merge_threshold_schema(threshold_schema: Mapping[str, Any] | None) -> dict[str, Any]:
    merged = {
        key: dict(value)
        for key, value in DEFAULT_THRESHOLD_SCHEMA.items()
    }
    for key, value in _mapping(threshold_schema).items():
        if isinstance(value, Mapping) and isinstance(merged.get(str(key)), dict):
            merged[str(key)].update(dict(value))
    return merged


def _mutation_policy() -> dict[str, Any]:
    return {
        "read_only": True,
        "writes_workspace": False,
        "physical_cleanup_performed": False,
        "cleanup_apply_supported": False,
    }


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
    "DEFAULT_THRESHOLD_SCHEMA",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "StorageGovernancePolicyKernel",
    "build_storage_governance_policy_projection",
]
