from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable


PRODUCT_ENTRY_CLI_COMMANDS = frozenset(
    {
        "product-frontdesk",
        "product-preflight",
        "product-start",
        "product-entry-manifest",
        "skill-catalog",
        "build-product-entry",
        "launch-study",
        "submit-study-task",
    }
)


def _emit_product_entry_result(
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


def handle_product_entry_command(
    args: argparse.Namespace,
    *,
    parser: argparse.ArgumentParser,
    product_entry: Any,
    load_profile: Callable[[str], Any],
) -> int | None:
    if args.command not in PRODUCT_ENTRY_CLI_COMMANDS:
        return None

    profile = load_profile(args.profile)
    profile_ref = Path(args.profile)

    if args.command == "product-frontdesk":
        result = product_entry.build_product_frontdesk(profile=profile, profile_ref=profile_ref)
        return _emit_product_entry_result(
            result,
            args=args,
            markdown_renderer=product_entry.render_product_frontdesk_markdown,
        )

    if args.command == "product-preflight":
        result = product_entry.build_product_entry_preflight(profile=profile, profile_ref=profile_ref)
        return _emit_product_entry_result(
            result,
            args=args,
            markdown_renderer=product_entry.render_product_entry_preflight_markdown,
        )

    if args.command == "product-start":
        result = product_entry.build_product_entry_start(profile=profile, profile_ref=profile_ref)
        return _emit_product_entry_result(
            result,
            args=args,
            markdown_renderer=product_entry.render_product_entry_start_markdown,
        )

    if args.command == "product-entry-manifest":
        result = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
        return _emit_product_entry_result(
            result,
            args=args,
            markdown_renderer=product_entry.render_product_entry_manifest_markdown,
        )

    if args.command == "skill-catalog":
        result = product_entry.build_skill_catalog(profile=profile, profile_ref=profile_ref)
        return _emit_product_entry_result(
            result,
            args=args,
            markdown_renderer=product_entry.render_skill_catalog_markdown,
        )

    if args.command == "build-product-entry":
        if bool(args.study_id) == bool(args.study_root):
            parser.error("Specify exactly one of --study-id or --study-root")
        result = product_entry.build_product_entry(
            profile=profile,
            profile_ref=profile_ref,
            study_id=args.study_id,
            study_root=Path(args.study_root) if args.study_root else None,
            direct_entry_mode=args.entry_mode,
        )
        return _emit_product_entry_result(
            result,
            args=args,
            markdown_renderer=product_entry.render_build_product_entry_markdown,
        )

    if args.command == "launch-study":
        if bool(args.study_id) == bool(args.study_root):
            parser.error("Specify exactly one of --study-id or --study-root")
        result = product_entry.launch_study(
            profile=profile,
            profile_ref=profile_ref,
            study_id=args.study_id,
            study_root=Path(args.study_root) if args.study_root else None,
            entry_mode=args.entry_mode,
            allow_stopped_relaunch=bool(args.allow_stopped_relaunch),
            force=bool(args.force),
        )
        return _emit_product_entry_result(
            result,
            args=args,
            markdown_renderer=product_entry.render_launch_study_markdown,
        )

    if args.command == "submit-study-task":
        if bool(args.study_id) == bool(args.study_root):
            parser.error("Specify exactly one of --study-id or --study-root")
        result = product_entry.submit_study_task(
            profile=profile,
            profile_ref=profile_ref,
            study_id=args.study_id,
            study_root=Path(args.study_root) if args.study_root else None,
            task_intent=args.task_intent,
            task_intake_kind=args.task_intake_kind,
            entry_mode=args.entry_mode,
            journal_target=args.journal_target,
            constraints=tuple(args.constraint or []),
            evidence_boundary=tuple(args.evidence_boundary or []),
            trusted_inputs=tuple(args.trusted_input or []),
            reference_papers=tuple(args.reference_paper or []),
            first_cycle_outputs=tuple(args.first_cycle_output or []),
        )
        return _emit_product_entry_result(
            result,
            args=args,
            markdown_renderer=product_entry.render_submit_study_task_markdown,
        )

    parser.error(f"unsupported product-entry command: {args.command}")
    return 2
