from __future__ import annotations

from typing import Any

from med_autoscience.controllers.study_runtime_types import StudyRuntimeStatus
from med_autoscience.mcp_server_parts.study_progress_projection import (
    compact_open_auto_research_soak_for_mcp,
    compact_study_progress_projection,
    compact_study_runtime_result_for_mcp,
    render_mcp_open_auto_research_soak_markdown,
    render_mcp_study_progress_markdown,
)

from .tool_result_rendering import json_text, tool_text_result


def serialize_study_runtime_result(result: dict[str, Any] | StudyRuntimeStatus) -> dict[str, Any]:
    if isinstance(result, StudyRuntimeStatus):
        return result.to_dict()
    if isinstance(result, dict):
        return dict(result)
    raise TypeError("study runtime controller result must be dict or StudyRuntimeStatus")


def render_study_runtime_status_result(result: dict[str, Any] | StudyRuntimeStatus) -> dict[str, Any]:
    serialized = serialize_study_runtime_result(result)
    progress_projection = serialized.get("progress_projection")
    if isinstance(progress_projection, dict):
        return tool_text_result(
            render_mcp_study_progress_markdown(progress_projection),
            structured=compact_study_runtime_result_for_mcp(serialized),
        )
    return tool_text_result(json_text(serialized), structured=serialized)


def render_study_progress_result(result: dict[str, Any]) -> dict[str, Any]:
    return tool_text_result(
        render_mcp_study_progress_markdown(result),
        structured=compact_study_progress_projection(result),
    )


def render_open_auto_research_soak_result(
    result: dict[str, Any],
    *,
    allow_controller_writes: bool,
) -> dict[str, Any]:
    return tool_text_result(
        render_mcp_open_auto_research_soak_markdown(result),
        structured=compact_open_auto_research_soak_for_mcp(
            result,
            allow_controller_writes=allow_controller_writes,
        ),
    )


def render_serialized_study_runtime_result(result: dict[str, Any] | StudyRuntimeStatus) -> dict[str, Any]:
    serialized = serialize_study_runtime_result(result)
    return tool_text_result(json_text(serialized), structured=serialized)
