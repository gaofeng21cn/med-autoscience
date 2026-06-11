from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.agent_tool_arsenal import (
    build_agent_tool_arsenal_completeness_diagnostic,
    build_agent_tool_arsenal_index,
    build_capability_invocation_plan,
    build_tool_result_envelope_schema,
    get_tool_use_card,
)
from med_autoscience.hosted_ordinary_path_consumption import (
    build_hosted_ordinary_path_consumption_evidence,
)
from med_autoscience.mcp_server_parts.handler_adapter import (
    call_mode_handler,
    optional_mapping,
    require_string,
)
from med_autoscience.mcp_server_parts.tool_result_rendering import json_text, tool_text_result


def call_agent_tool_arsenal(
    arguments: dict[str, Any],
    *,
    action_catalog: Mapping[str, Any],
    mcp_tool_manifest: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return call_mode_handler(
        tool_name="agent_tool_arsenal",
        arguments=arguments,
        handlers={
            "index": lambda value: _index(value, action_catalog=action_catalog),
            "card": _card,
            "plan": _plan,
            "result_envelope_schema": _result_envelope_schema,
            "completeness_diagnostic": lambda value: _completeness_diagnostic(
                value,
                action_catalog=action_catalog,
                mcp_tool_manifest=mcp_tool_manifest,
            ),
            "hosted_consumption": lambda value: _hosted_consumption(
                value,
                action_catalog=action_catalog,
            ),
        },
    )


def _index(
    arguments: dict[str, Any],
    *,
    action_catalog: Mapping[str, Any],
) -> dict[str, Any]:
    result = build_agent_tool_arsenal_index(action_catalog)
    return tool_text_result(json_text(result), structured=result)


def _card(arguments: dict[str, Any]) -> dict[str, Any]:
    result = get_tool_use_card(require_string(arguments, "tool_id"))
    return tool_text_result(json_text(result), structured=result)


def _plan(arguments: dict[str, Any]) -> dict[str, Any]:
    current_owner_delta = optional_mapping(
        arguments.get("current_owner_delta"),
        field_name="current_owner_delta",
    )
    if current_owner_delta is None:
        raise ValueError("current_owner_delta is required for agent_tool_arsenal plan mode")
    result = build_capability_invocation_plan(current_owner_delta=current_owner_delta)
    return tool_text_result(json_text(result), structured=result)


def _result_envelope_schema(arguments: dict[str, Any]) -> dict[str, Any]:
    result = build_tool_result_envelope_schema()
    return tool_text_result(json_text(result), structured=result)


def _completeness_diagnostic(
    arguments: dict[str, Any],
    *,
    action_catalog: Mapping[str, Any],
    mcp_tool_manifest: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    result = build_agent_tool_arsenal_completeness_diagnostic(
        arsenal=build_agent_tool_arsenal_index(action_catalog),
        mcp_tool_manifest=tuple(mcp_tool_manifest),
    )
    return tool_text_result(json_text(result), structured=result)


def _hosted_consumption(
    arguments: dict[str, Any],
    *,
    action_catalog: Mapping[str, Any],
) -> dict[str, Any]:
    current_owner_delta = optional_mapping(
        arguments.get("current_owner_delta"),
        field_name="current_owner_delta",
    )
    if current_owner_delta is None:
        raise ValueError("current_owner_delta is required for hosted_consumption mode")
    result = build_hosted_ordinary_path_consumption_evidence(
        current_owner_delta=current_owner_delta,
        arsenal=build_agent_tool_arsenal_index(action_catalog),
    )
    return tool_text_result(json_text(result), structured=result)


__all__ = ["call_agent_tool_arsenal"]
