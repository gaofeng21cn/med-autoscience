from __future__ import annotations

import json
import sys
from collections.abc import Callable, Iterable
from typing import Any, TextIO


ListTools = Callable[[], list[dict[str, Any]]]
CallTool = Callable[[str, dict[str, Any] | None], dict[str, Any]]


def success_response(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result,
    }


def error_response(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": code,
            "message": message,
        },
    }


def handle_request(
    request: dict[str, Any],
    *,
    protocol_version: str,
    server_name: str,
    server_version: str,
    list_tools: ListTools,
    call_tool: CallTool,
) -> dict[str, Any] | None:
    method = request.get("method")
    request_id = request.get("id")
    params = request.get("params") if isinstance(request.get("params"), dict) else {}

    if method == "notifications/initialized":
        return None
    if method == "initialize":
        return success_response(
            request_id,
            {
                "protocolVersion": protocol_version,
                "capabilities": {
                    "tools": {
                        "listChanged": False,
                    }
                },
                "serverInfo": {
                    "name": server_name,
                    "version": server_version,
                },
            },
        )
    if method == "ping":
        return success_response(request_id, {})
    if method == "tools/list":
        return success_response(request_id, {"tools": list_tools()})
    if method == "tools/call":
        name = params.get("name")
        if not isinstance(name, str) or not name:
            return error_response(request_id, -32602, "tools/call requires params.name")
        arguments = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
        return success_response(request_id, call_tool(name, arguments))
    if request_id is None:
        return None
    return error_response(request_id, -32601, f"Method not found: {method}")


def serve(
    *,
    protocol_version: str,
    server_name: str,
    server_version: str,
    list_tools: ListTools,
    call_tool: CallTool,
    input_stream: Iterable[str] | None = None,
    output_stream: TextIO | None = None,
) -> int:
    source = input_stream if input_stream is not None else sys.stdin
    sink = output_stream if output_stream is not None else sys.stdout
    for raw_line in source:
        line = raw_line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError as exc:
            response = error_response(None, -32700, f"Parse error: {exc}")
        else:
            if not isinstance(request, dict):
                response = error_response(None, -32600, "Invalid request")
            else:
                response = handle_request(
                    request,
                    protocol_version=protocol_version,
                    server_name=server_name,
                    server_version=server_version,
                    list_tools=list_tools,
                    call_tool=call_tool,
                )
        if response is not None:
            sink.write(json.dumps(response, ensure_ascii=False) + "\n")
            sink.flush()
    return 0
