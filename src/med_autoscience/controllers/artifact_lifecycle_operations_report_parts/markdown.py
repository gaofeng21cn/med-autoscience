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
    lines.extend(["", "## Bloat Sources", ""])
    return lines


def _markdown_projection_summary_lines(projection: Mapping[str, Any]) -> list[str]:
    return [
        f"- complete studies: `{_mapping_value(projection, 'complete_study_count', 0)}`",
        f"- incomplete studies: `{_mapping_value(projection, 'incomplete_study_count', 0)}`",
    ]


def _markdown_source_total_lines(report: Mapping[str, Any]) -> list[str]:
    lines = list(map(_markdown_source_total_line, _mapping_items(report.get("source_totals"))))
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
