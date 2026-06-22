from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers.current_owner_delta_owner_answer import (
    materialize_current_owner_delta_owner_answer,
)
from med_autoscience.controllers.owner_answer_candidate_intake import (
    intake_owner_answer_candidate,
)


def register_current_owner_delta_owner_answer_parser(
    subparsers: argparse._SubParsersAction,
) -> None:
    parser = subparsers.add_parser("current-owner-delta-owner-answer")
    current_delta = parser.add_mutually_exclusive_group(required=True)
    current_delta.add_argument("--current-owner-delta-json")
    current_delta.add_argument("--current-owner-delta-file")
    parser.add_argument("--format", choices=("json",), default="json")

    candidate_parser = subparsers.add_parser("owner-answer-candidate-intake")
    candidate_parser.add_argument("--candidate-id", required=True, choices=("B002-0810", "B003-0751"))
    candidate_parser.add_argument("--candidate-path", required=True)
    candidate_parser.add_argument("--expected-sha256")
    candidate_parser.add_argument("--format", choices=("json",), default="json")


def handle_current_owner_delta_owner_answer_command(args: argparse.Namespace) -> int | None:
    if args.command == "current-owner-delta-owner-answer":
        current_owner_delta = _load_json_object(
            payload_json=args.current_owner_delta_json,
            payload_file=args.current_owner_delta_file,
            label="current_owner_delta",
        )
        result = materialize_current_owner_delta_owner_answer(current_owner_delta)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("status") != "blocked" else 2
    if args.command == "owner-answer-candidate-intake":
        result = intake_owner_answer_candidate(
            candidate_id=args.candidate_id,
            candidate_path=Path(args.candidate_path),
            expected_sha256=args.expected_sha256,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if result.get("status") != "governed_answer_consumed" else 0
    return None


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
