from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable


def handle_submission_delivery_command(
    args: argparse.Namespace,
    *,
    load_profile: Callable[[str], Any],
    delivery_inspector: Any,
    submission_targets_controller: Any,
) -> int | None:
    if args.command == "resolve-submission-targets":
        result = submission_targets_controller.resolve_submission_targets(
            profile_path=Path(args.profile) if args.profile else None,
            study_root=Path(args.study_root) if args.study_root else None,
            quest_root=Path(args.quest_root) if args.quest_root else None,
        )
        _print_json(result)
        return 0

    if args.command == "export-submission-targets":
        result = submission_targets_controller.export_submission_targets(
            paper_root=Path(args.paper_root) if args.paper_root else None,
            profile_path=Path(args.profile) if args.profile else None,
            study_root=Path(args.study_root) if args.study_root else None,
            quest_root=Path(args.quest_root) if args.quest_root else None,
        )
        _print_json(result)
        return 0

    if args.command == "delivery-inspect":
        profile = load_profile(args.profile)
        result = delivery_inspector.inspect_study_delivery(
            profile=profile,
            profile_ref=Path(args.profile),
            study_id=args.study_id,
            study_root=Path(args.study_root) if args.study_root else None,
            publication_profile=args.publication_profile,
        )
        if args.format == "json":
            _print_json(result)
        else:
            print(delivery_inspector.render_delivery_inspection_markdown(result), end="")
        return 0

    return None


def _print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


__all__ = ["handle_submission_delivery_command"]
