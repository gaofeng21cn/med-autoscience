from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from med_autoscience.runtime_protocol import evo_scientist_sidecar_refs


def register_evo_scientist_sidecar_parsers(subparsers: argparse._SubParsersAction) -> None:
    sidecar_parser = subparsers.add_parser("evo-scientist-sidecar")
    sidecar_subparsers = sidecar_parser.add_subparsers(
        dest="evo_scientist_sidecar_command",
        required=True,
    )

    observe_parser = sidecar_subparsers.add_parser("observe")
    observe_parser.add_argument("--study-root", required=True)
    observe_source = observe_parser.add_mutually_exclusive_group()
    observe_source.add_argument("--event-file", type=str)
    observe_source.add_argument("--event-json", type=str)
    observe_apply = observe_parser.add_mutually_exclusive_group(required=True)
    observe_apply.add_argument("--apply", action="store_true")
    observe_apply.add_argument("--dry-run", action="store_true")
    observe_parser.add_argument("--format", choices=("json",), default="json")

    read_latest_parser = sidecar_subparsers.add_parser("read-latest")
    read_latest_parser.add_argument("--study-root", required=True)
    read_latest_parser.add_argument("--format", choices=("json",), default="json")


def handle_evo_scientist_sidecar_command(args: argparse.Namespace) -> int | None:
    if args.command != "evo-scientist-sidecar":
        return None

    if args.evo_scientist_sidecar_command == "observe":
        result = evo_scientist_sidecar_refs.write_evo_scientist_sidecar_observation(
            study_root=Path(args.study_root),
            event=_event_payload_from_args(args),
            apply=bool(args.apply),
        )
        _print_json(result)
        return 0

    if args.evo_scientist_sidecar_command == "read-latest":
        result = evo_scientist_sidecar_refs.read_latest_evo_scientist_sidecar_projection(
            study_root=Path(args.study_root),
        )
        _print_json(result)
        return 0

    return None


def _event_payload_from_args(args: argparse.Namespace) -> dict[str, Any]:
    if args.event_file:
        payload = json.loads(Path(args.event_file).read_text(encoding="utf-8"))
    elif args.event_json:
        payload = json.loads(args.event_json)
    else:
        payload = {"event_kind": "executor_turn_completed", "source": "cli"}
    if not isinstance(payload, dict):
        raise SystemExit("EvoScientist sidecar event payload must be a JSON object")
    return payload


def _print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


__all__ = [
    "handle_evo_scientist_sidecar_command",
    "register_evo_scientist_sidecar_parsers",
]
