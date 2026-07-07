from __future__ import annotations

import argparse
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


def _load_json_payload_from_args(args: argparse.Namespace) -> dict[str, object]:
    payload_file = getattr(args, "payload_file", None)
    payload_json = getattr(args, "payload_json", None)
    if bool(payload_file) == bool(payload_json):
        raise SystemExit("Specify exactly one of --payload-file or --payload-json")
    return _load_optional_object_payload_from_args(
        payload_file=payload_file,
        payload_json=payload_json,
        file_label="--payload-file",
        json_label="--payload-json",
    ) or {}


def _load_json_object_file(path: str | Path) -> dict[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("JSON payload file must contain an object")
    return payload
