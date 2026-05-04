from __future__ import annotations

from collections.abc import Mapping
from itertools import chain
from typing import Any


SURFACE_KIND = "control_plane_lifecycle_report"
EMPTY_SEQUENCE: tuple[Any, ...] = ()


def _display_value(value: Any, default: Any) -> Any:
    if value:
        return value
    return default


def _mapping_value(source: Mapping[str, Any], key: str, default: Any) -> Any:
    return _display_value(source.get(key), default)


def _mapping_items(value: Any):
    if not isinstance(value, Mapping):
        return EMPTY_SEQUENCE
    return value.items()


def _sequence_value(value: Any):
    if not isinstance(value, list | tuple):
        return EMPTY_SEQUENCE
    return value


def render_lifecycle_operations_report_markdown(report: Mapping[str, Any]) -> str:
    lines = _markdown_summary_lines(report)
    lines.extend(_markdown_operational_summary_lines(report))
    lines.extend(_markdown_source_total_lines(report))
    lines.extend(_markdown_study_lines(report))
    lines.append("")
    return "\n".join(lines)


def _markdown_summary_lines(report: Mapping[str, Any]) -> list[str]:
    summary = dict(report.get("summary") or {})
    projection = dict(report.get("projection_completeness") or {})
    lines = [
        "# Control Plane Lifecycle Report",
        "",
        f"- surface: `{_mapping_value(report, 'surface', SURFACE_KIND)}`",
        f"- workspace count: `{_mapping_value(report, 'workspace_count', 0)}`",
        f"- total bytes: `{_mapping_value(summary, 'total_bytes', 0)}`",
        f"- classified files: `{_mapping_value(summary, 'classified_file_count', 0)}`",
        f"- statistical files: `{_mapping_value(summary, 'statistical_file_count', 0)}`",
    ]
    lines.extend(_markdown_projection_summary_lines(projection))
    return lines


def _markdown_projection_summary_lines(projection: Mapping[str, Any]) -> list[str]:
    return [
        f"- complete studies: `{_mapping_value(projection, 'complete_study_count', 0)}`",
        f"- incomplete studies: `{_mapping_value(projection, 'incomplete_study_count', 0)}`",
    ]


def _markdown_operational_summary_lines(report: Mapping[str, Any]) -> list[str]:
    operational_summary = report.get("operational_summary")
    if not isinstance(operational_summary, Mapping):
        return []
    storage_budget = _mapping_value(operational_summary, "storage_budget", {})
    storage_budget_mapping = storage_budget if isinstance(storage_budget, Mapping) else {}
    lines = [
        "",
        "## Operational Summary",
        "",
        (
            f"- storage budget: `{_mapping_value(storage_budget_mapping, 'mode', 'bounded_read_only')}`, "
            f"bytes `{_mapping_value(storage_budget_mapping, 'total_bytes', 0)}`"
        ),
        f"- top growth buckets: {_markdown_top_growth_buckets(operational_summary)}",
        f"- blocked cleanup reasons: {_markdown_blocked_cleanup_reasons(operational_summary)}",
        f"- projection regeneration candidates: {_markdown_projection_candidates(operational_summary)}",
        f"- restore contract gaps: {_markdown_restore_contract_gaps(operational_summary)}",
    ]
    lines.extend(["", "## Bloat Sources", ""])
    return lines


def _markdown_top_growth_buckets(operational_summary: Mapping[str, Any]) -> str:
    buckets = _sequence_value(operational_summary.get("top_growth_buckets"))
    text = "; ".join(
        f"`{_mapping_value(_mapping_or_empty(bucket), 'source_bucket', 'other')}` "
        f"{_mapping_value(_mapping_or_empty(bucket), 'bytes', 0)} bytes"
        for bucket in buckets
    )
    return _display_value(text, "none")


def _markdown_blocked_cleanup_reasons(operational_summary: Mapping[str, Any]) -> str:
    reasons = _sequence_value(operational_summary.get("blocked_cleanup_reasons"))
    text = "; ".join(
        f"`{_mapping_value(_mapping_or_empty(reason), 'reason', 'unknown')}` "
        f"x{_mapping_value(_mapping_or_empty(reason), 'count', 0)}"
        for reason in reasons
    )
    return _display_value(text, "none")


def _markdown_projection_candidates(operational_summary: Mapping[str, Any]) -> str:
    candidates = _sequence_value(operational_summary.get("projection_regeneration_candidates"))
    text = "; ".join(
        f"`{_mapping_value(_mapping_or_empty(candidate), 'workspace_relative_path', 'unknown')}`"
        for candidate in candidates
    )
    return _display_value(text, "none")


def _markdown_restore_contract_gaps(operational_summary: Mapping[str, Any]) -> str:
    gaps = _sequence_value(operational_summary.get("restore_contract_gaps"))
    text = "; ".join(
        f"`{_mapping_value(_mapping_or_empty(gap), 'workspace_relative_path', 'unknown')}`"
        for gap in gaps
    )
    return _display_value(text, "none")


def _mapping_or_empty(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _markdown_source_total_lines(report: Mapping[str, Any]) -> list[str]:
    lines = list(map(_markdown_source_total_line, _mapping_items(report.get("source_totals"))))
    if "operational_summary" not in report:
        lines = ["", "## Bloat Sources", "", *lines]
    lines.extend(["", "## Studies", ""])
    return lines


def _markdown_source_total_line(item: tuple[Any, Any]) -> str:
    source_kind, totals = item
    totals_mapping = totals if isinstance(totals, Mapping) else {}
    return (
        f"- `{source_kind}`: bytes `{_mapping_value(totals_mapping, 'bytes', 0)}`, "
        f"files `{_mapping_value(totals_mapping, 'file_count', 0)}`, "
        f"scan `{_mapping_value(totals_mapping, 'scan_mode', 'none')}`"
    )


def _markdown_study_lines(report: Mapping[str, Any]) -> list[str]:
    workspaces = _sequence_value(report.get("workspaces"))
    return list(chain.from_iterable(map(_markdown_workspace_study_lines, workspaces)))


def _markdown_workspace_study_lines(workspace: Any) -> list[str]:
    if not isinstance(workspace, Mapping):
        return []
    return list(map(_markdown_study_line, _sequence_value(workspace.get("studies"))))


def _markdown_study_line(study: Any) -> str:
    study_mapping = study if isinstance(study, Mapping) else {}
    completeness = _mapping_value(study_mapping, "projection_completeness", {})
    completeness_mapping = completeness if isinstance(completeness, Mapping) else {}
    return (
        f"- `{_mapping_value(study_mapping, 'study_id', 'workspace')}`: "
        f"`{_mapping_value(completeness_mapping, 'status', 'unknown')}`, "
        f"blockers: {_joined_or_none(_sequence_value(completeness_mapping.get('blockers')))}"
    )


def _joined_or_none(values: tuple[Any, ...] | list[Any]) -> str:
    text = ", ".join(str(value) for value in values)
    return _display_value(text, "none")
