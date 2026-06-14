from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers.current_owner_delta_owner_answer import (
    materialize_current_owner_delta_owner_answer,
)


def register_current_owner_delta_owner_answer_parser(
    subparsers: argparse._SubParsersAction,
) -> None:
    parser = subparsers.add_parser("current-owner-delta-owner-answer")
    current_delta = parser.add_mutually_exclusive_group(required=True)
    current_delta.add_argument("--current-owner-delta-json")
    current_delta.add_argument("--current-owner-delta-file")
    parser.add_argument("--format", choices=("json",), default="json")


def handle_current_owner_delta_owner_answer_command(args: argparse.Namespace) -> int | None:
    if args.command != "current-owner-delta-owner-answer":
        return None
    current_owner_delta = _load_json_object(
        payload_json=args.current_owner_delta_json,
        payload_file=args.current_owner_delta_file,
        label="current_owner_delta",
    )
    result = materialize_current_owner_delta_owner_answer(current_owner_delta)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") != "blocked" else 2


def _load_json_object(
    *,
    payload_json: str | None,
    payload_file: str | None,
    label: str,
) -> dict[str, Any]:
    if payload_file:
        payload = json.loads(Path(payload_file).read_text(encoding="utf-8"))
    elif payload_json:
        payload = json.loads(payload_json)
    else:
        raise SystemExit(f"{label} JSON is required")
    if not isinstance(payload, dict):
        raise SystemExit(f"{label} JSON must contain an object")
    return payload


__all__ = [
    "handle_current_owner_delta_owner_answer_command",
    "register_current_owner_delta_owner_answer_parser",
]
