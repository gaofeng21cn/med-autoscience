from __future__ import annotations

import json
from typing import Any


def tool_text_result(text: str, *, structured: dict[str, Any] | None = None, is_error: bool = False) -> dict[str, Any]:
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


def json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)
