from __future__ import annotations

import json
from pathlib import Path


def _parse_key_value_pairs(values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw in values:
        item = str(raw).strip()
        if not item:
            continue
        if "=" in item:
            key, note = item.split("=", 1)
        else:
            key, note = item, ""
        parsed[key.strip().upper()] = note.strip()
    return parsed


def _load_optional_object_payload_from_args(
    *,
    payload_file: str | None,
    payload_json: str | None,
    file_label: str,
    json_label: str,
) -> dict[str, object] | None:
    if not payload_file and not payload_json:
        return None
    if bool(payload_file) == bool(payload_json):
        raise SystemExit(f"Specify exactly one of {file_label} or {json_label}")
    payload: object
    if payload_file:
        payload = json.loads(Path(payload_file).read_text(encoding="utf-8"))
    else:
        payload = json.loads(str(payload_json))
    if not isinstance(payload, dict):
        raise SystemExit("JSON payload must be an object")
    return payload
