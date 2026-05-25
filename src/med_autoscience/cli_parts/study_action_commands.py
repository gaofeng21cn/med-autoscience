from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable


STUDY_ACTION_COMMANDS = frozenset({"launch-study", "submit-study-task"})


def register_study_action_parsers(subparsers: argparse._SubParsersAction) -> None:
    launch_study_parser = subparsers.add_parser("launch-study")
    launch_study_parser.add_argument("--profile", required=True)
    launch_study_parser.add_argument("--study-id", type=str)
    launch_study_parser.add_argument("--study-root", type=str)
    launch_study_parser.add_argument("--entry-mode", type=str)
    launch_study_parser.add_argument("--allow-stopped-relaunch", action="store_true")
    launch_study_parser.add_argument("--explicit-user-wakeup", action="store_true")
    launch_study_parser.add_argument("--force", action="store_true")
    launch_study_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")

    submit_study_task_parser = subparsers.add_parser("submit-study-task")
    submit_study_task_parser.add_argument("--profile", required=True)
    submit_study_task_parser.add_argument("--study-id", type=str)
    submit_study_task_parser.add_argument("--study-root", type=str)
    submit_study_task_parser.add_argument("--task-intent", required=True)
    submit_study_task_parser.add_argument("--task-intake-kind", type=str)
    submit_study_task_parser.add_argument("--entry-mode", type=str)
    submit_study_task_parser.add_argument("--journal-target", type=str)
    submit_study_task_parser.add_argument("--constraint", action="append", default=[])
    submit_study_task_parser.add_argument("--evidence-boundary", action="append", default=[])
    submit_study_task_parser.add_argument("--trusted-input", action="append", default=[])
    submit_study_task_parser.add_argument("--reference-paper", action="append", default=[])
    submit_study_task_parser.add_argument("--first-cycle-output", action="append", default=[])
    submit_study_task_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")


def handle_study_action_command(
    args: argparse.Namespace,
    *,
    parser: argparse.ArgumentParser,
    study_domain_handlers: Any,
    load_profile: Callable[[str], Any],
) -> int | None:
    if args.command not in STUDY_ACTION_COMMANDS:
        return None
    if bool(args.study_id) == bool(args.study_root):
        parser.error(f"Specify exactly one of --study-id or --study-root for {args.command}")

    profile = load_profile(args.profile)
    profile_ref = Path(args.profile)
    study_root = Path(args.study_root) if args.study_root else None

    if args.command == "launch-study":
        result = study_domain_handlers.launch_study(
            profile=profile,
            profile_ref=profile_ref,
            study_id=args.study_id,
            study_root=study_root,
            entry_mode=args.entry_mode,
            allow_stopped_relaunch=bool(args.allow_stopped_relaunch),
            explicit_user_wakeup=bool(args.explicit_user_wakeup),
            force=bool(args.force),
        )
        return _emit_result(
            result,
            args=args,
            markdown_renderer=study_domain_handlers.render_launch_study_markdown,
        )

    if args.command == "submit-study-task":
        result = study_domain_handlers.submit_study_task(
            profile=profile,
            profile_ref=profile_ref,
            study_id=args.study_id,
            study_root=study_root,
            task_intent=args.task_intent,
            task_intake_kind=args.task_intake_kind,
            entry_mode=args.entry_mode,
            journal_target=args.journal_target,
            constraints=tuple(args.constraint or ()),
            evidence_boundary=tuple(args.evidence_boundary or ()),
            trusted_inputs=tuple(args.trusted_input or ()),
            reference_papers=tuple(args.reference_paper or ()),
            first_cycle_outputs=tuple(args.first_cycle_output or ()),
        )
        return _emit_result(
            result,
            args=args,
            markdown_renderer=study_domain_handlers.render_submit_study_task_markdown,
        )

    parser.error(f"unsupported study action command: {args.command}")
    return 2


def _emit_result(
    result: dict[str, Any],
    *,
    args: argparse.Namespace,
    markdown_renderer: Callable[[dict[str, Any]], str],
) -> int:
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(markdown_renderer(result), end="")
    return 0

