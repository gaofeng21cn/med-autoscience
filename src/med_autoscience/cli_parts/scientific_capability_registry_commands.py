from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from med_autoscience.scientific_capability_registry import (
    build_scientific_capability_registry,
    invoke_scientific_capability,
    resolve_scientific_capabilities,
)


def register_scientific_capability_registry_parser(
    subparsers: argparse._SubParsersAction,
) -> None:
    parser = subparsers.add_parser("scientific-capability-registry")
    parser.add_argument("--mode", choices=("index", "resolve", "invoke"), required=True)
    parser.add_argument("--capability-id")
    parser.add_argument("--study-root")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--format", choices=("json",), default="json")
    current_delta = parser.add_mutually_exclusive_group()
    current_delta.add_argument("--current-owner-delta-json")
    current_delta.add_argument("--current-owner-delta-file")
    payload = parser.add_mutually_exclusive_group()
    payload.add_argument("--payload-json")
    payload.add_argument("--payload-file")


def handle_scientific_capability_registry_command(args: argparse.Namespace) -> int | None:
    if args.command != "scientific-capability-registry":
        return None

    current_owner_delta = _load_optional_json_object(
        payload_json=args.current_owner_delta_json,
        payload_file=args.current_owner_delta_file,
        label="current_owner_delta",
    )
    payload = _load_optional_json_object(
        payload_json=args.payload_json,
        payload_file=args.payload_file,
        label="payload",
    )

    if args.mode == "index":
        result = build_scientific_capability_registry()
    elif args.mode == "resolve":
        result = resolve_scientific_capabilities(
            current_owner_delta=current_owner_delta,
        )
    else:
        if not args.capability_id:
            raise SystemExit("--capability-id is required when --mode invoke")
        result = invoke_scientific_capability(
            capability_id=args.capability_id,
            current_owner_delta=current_owner_delta,
            study_root=Path(args.study_root) if args.study_root else None,
            apply=bool(args.apply),
            payload=payload,
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _load_optional_json_object(
    *,
    payload_json: str | None,
    payload_file: str | None,
    label: str,
) -> dict[str, Any] | None:
    if payload_file:
        payload = json.loads(Path(payload_file).read_text(encoding="utf-8"))
    elif payload_json:
        payload = json.loads(payload_json)
    else:
        return None
    if not isinstance(payload, dict):
        raise SystemExit(f"{label} JSON must contain an object")
    return payload


__all__ = [
    "handle_scientific_capability_registry_command",
    "register_scientific_capability_registry_parser",
]
