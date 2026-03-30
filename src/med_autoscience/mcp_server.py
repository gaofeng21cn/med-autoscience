from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from med_autoscience import __version__
from med_autoscience.controllers import (
    data_assets,
    deepscientist_upgrade_check,
    runtime_watch,
    startup_data_readiness as startup_data_readiness_controller,
)
from med_autoscience.doctor import build_doctor_report, overlay_request_from_profile, render_doctor_report, render_profile
from med_autoscience.overlay import installer as overlay_installer
from med_autoscience.profiles import load_profile


PROTOCOL_VERSION = "2025-03-26"
SERVER_NAME = "med-autoscience"


def _tool_text_result(text: str, *, structured: dict[str, Any] | None = None, is_error: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {
        "content": [
            {
                "type": "text",
                "text": text,
            }
        ],
        "isError": is_error,
    }
    if structured is not None:
        result["structuredContent"] = structured
    return result


def _json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _require_string(arguments: dict[str, Any], key: str) -> str:
    value = arguments.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value


def _optional_bool(arguments: dict[str, Any], key: str, *, default: bool = False) -> bool:
    value = arguments.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean")
    return value


def list_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": "doctor_report",
            "description": "Render a MedAutoScience doctor report for a workspace profile.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "profile_path": {"type": "string"},
                },
                "required": ["profile_path"],
                "additionalProperties": False,
            },
        },
        {
            "name": "show_profile",
            "description": "Render the resolved MedAutoScience workspace profile contract.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "profile_path": {"type": "string"},
                },
                "required": ["profile_path"],
                "additionalProperties": False,
            },
        },
        {
            "name": "overlay_status",
            "description": "Inspect MedAutoScience overlay status by profile or quest root.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "profile_path": {"type": "string"},
                    "quest_root": {"type": "string"},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "runtime_watch",
            "description": "Run MedAutoScience runtime watch in read-only mode for a quest or runtime root.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "quest_root": {"type": "string"},
                    "runtime_root": {"type": "string"},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "data_assets_status",
            "description": "Read the current MedAutoScience data-assets status for a workspace root.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "workspace_root": {"type": "string"},
                },
                "required": ["workspace_root"],
                "additionalProperties": False,
            },
        },
        {
            "name": "startup_data_readiness",
            "description": "Read the startup data readiness summary for a workspace root.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "workspace_root": {"type": "string"},
                },
                "required": ["workspace_root"],
                "additionalProperties": False,
            },
        },
        {
            "name": "deepscientist_upgrade_check",
            "description": "Run the MedAutoScience pre-upgrade audit for a bound DeepScientist checkout.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "profile_path": {"type": "string"},
                    "refresh": {"type": "boolean"},
                },
                "required": ["profile_path"],
                "additionalProperties": False,
            },
        },
    ]


def _call_doctor_report(arguments: dict[str, Any]) -> dict[str, Any]:
    profile = load_profile(_require_string(arguments, "profile_path"))
    report = build_doctor_report(profile)
    text = render_doctor_report(report)
    structured = {
        "profile": profile.name,
        "workspace_root": str(profile.workspace_root),
        "runtime_root": str(profile.runtime_root),
        "medical_overlay_ready": report.medical_overlay_ready,
    }
    return _tool_text_result(text, structured=structured)


def _call_show_profile(arguments: dict[str, Any]) -> dict[str, Any]:
    profile = load_profile(_require_string(arguments, "profile_path"))
    text = render_profile(profile)
    structured = {
        "name": profile.name,
        "workspace_root": str(profile.workspace_root),
        "runtime_root": str(profile.runtime_root),
        "medical_overlay_scope": profile.medical_overlay_scope,
    }
    return _tool_text_result(text, structured=structured)


def _call_overlay_status(arguments: dict[str, Any]) -> dict[str, Any]:
    profile_path = arguments.get("profile_path")
    quest_root = arguments.get("quest_root")
    if bool(profile_path) == bool(quest_root):
        raise ValueError("Specify exactly one of profile_path or quest_root")
    if isinstance(profile_path, str):
        profile = load_profile(profile_path)
        result = overlay_installer.describe_medical_overlay(**overlay_request_from_profile(profile))
    else:
        result = overlay_installer.describe_medical_overlay(quest_root=Path(_require_string(arguments, "quest_root")))
    return _tool_text_result(_json_text(result), structured=result)


def _call_runtime_watch(arguments: dict[str, Any]) -> dict[str, Any]:
    quest_root = arguments.get("quest_root")
    runtime_root = arguments.get("runtime_root")
    if bool(quest_root) == bool(runtime_root):
        raise ValueError("Specify exactly one of quest_root or runtime_root")
    if isinstance(quest_root, str):
        result = runtime_watch.run_watch_for_quest(quest_root=Path(quest_root), apply=False)
    else:
        result = runtime_watch.run_watch_for_runtime(runtime_root=Path(_require_string(arguments, "runtime_root")), apply=False)
    return _tool_text_result(_json_text(result), structured=result)


def _call_data_assets_status(arguments: dict[str, Any]) -> dict[str, Any]:
    result = data_assets.data_assets_status(workspace_root=Path(_require_string(arguments, "workspace_root")))
    return _tool_text_result(_json_text(result), structured=result)


def _call_startup_data_readiness(arguments: dict[str, Any]) -> dict[str, Any]:
    result = startup_data_readiness_controller.startup_data_readiness(
        workspace_root=Path(_require_string(arguments, "workspace_root"))
    )
    return _tool_text_result(_json_text(result), structured=result)


def _call_deepscientist_upgrade_check(arguments: dict[str, Any]) -> dict[str, Any]:
    profile = load_profile(_require_string(arguments, "profile_path"))
    result = deepscientist_upgrade_check.run_upgrade_check(profile, refresh=_optional_bool(arguments, "refresh"))
    return _tool_text_result(_json_text(result), structured=result)


TOOL_HANDLERS = {
    "doctor_report": _call_doctor_report,
    "show_profile": _call_show_profile,
    "overlay_status": _call_overlay_status,
    "runtime_watch": _call_runtime_watch,
    "data_assets_status": _call_data_assets_status,
    "startup_data_readiness": _call_startup_data_readiness,
    "deepscientist_upgrade_check": _call_deepscientist_upgrade_check,
}


def call_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return _tool_text_result(f"Unknown tool: {name}", is_error=True)
    try:
        return handler(arguments or {})
    except Exception as exc:
        return _tool_text_result(f"{type(exc).__name__}: {exc}", is_error=True)


def _success_response(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result,
    }


def _error_response(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": code,
            "message": message,
        },
    }


def handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    method = request.get("method")
    request_id = request.get("id")
    params = request.get("params") if isinstance(request.get("params"), dict) else {}

    if method == "notifications/initialized":
        return None
    if method == "initialize":
        return _success_response(
            request_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {
                    "tools": {
                        "listChanged": False,
                    }
                },
                "serverInfo": {
                    "name": SERVER_NAME,
                    "version": __version__,
                },
            },
        )
    if method == "ping":
        return _success_response(request_id, {})
    if method == "tools/list":
        return _success_response(request_id, {"tools": list_tools()})
    if method == "tools/call":
        name = params.get("name")
        if not isinstance(name, str) or not name:
            return _error_response(request_id, -32602, "tools/call requires params.name")
        arguments = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
        return _success_response(request_id, call_tool(name, arguments))
    if request_id is None:
        return None
    return _error_response(request_id, -32601, f"Method not found: {method}")


def serve() -> int:
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError as exc:
            response = _error_response(None, -32700, f"Parse error: {exc}")
        else:
            if not isinstance(request, dict):
                response = _error_response(None, -32600, "Invalid request")
            else:
                response = handle_request(request)
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


def entrypoint() -> None:
    raise SystemExit(serve())


if __name__ == "__main__":
    entrypoint()
