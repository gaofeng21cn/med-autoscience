from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def handle_watch_supervision_command(
    args: argparse.Namespace,
    *,
    parser: argparse.ArgumentParser,
    domain_health_diagnostic: Any,
    domain_slo_scheduler_projection: Any,
    load_profile: Any,
) -> int | None:
    if args.command == "domain-health-diagnostic":
        if bool(args.quest_root) == bool(args.runtime_root):
            parser.error("Specify exactly one of --quest-root or --runtime-root")
        if args.quest_root and args.profile:
            parser.error("--profile is only supported with --runtime-root")
        if args.quest_root and args.ensure_study_runtimes:
            parser.error("--ensure-study-runtimes is only supported with --runtime-root")
        if args.quest_root and args.apply_supervisor_platform_repair:
            parser.error("--apply-supervisor-platform-repair is only supported with --runtime-root")
        if args.ensure_study_runtimes and not args.profile:
            parser.error("--ensure-study-runtimes requires --profile")
        if args.apply_supervisor_platform_repair and not args.ensure_study_runtimes:
            parser.error("--apply-supervisor-platform-repair requires --ensure-study-runtimes")
        if args.apply_supervisor_platform_repair and not args.apply:
            parser.error("--apply-supervisor-platform-repair requires --apply")
        if args.quest_root:
            result = domain_health_diagnostic.run_domain_health_diagnostic_for_quest(
                quest_root=Path(args.quest_root),
                apply=args.apply,
            )
        else:
            profile = load_profile(args.profile) if args.profile else None
            result = domain_health_diagnostic.run_domain_health_diagnostic_for_runtime(
                runtime_root=Path(args.runtime_root),
                apply=args.apply,
                profile=profile,
                ensure_study_runtimes=bool(args.ensure_study_runtimes),
                apply_supervisor_platform_repair=bool(args.apply_supervisor_platform_repair),
            )
        _print_json(result)
        return 0

    if args.command == "runtime-supervision-status":
        profile = load_profile(args.profile)
        result = domain_slo_scheduler_projection.read_supervision_status(
            profile=profile,
            interval_seconds=int(args.interval_seconds),
            manager=str(args.manager),
        )
        _print_json(result)
        return 0

    if args.command == "runtime-ensure-supervision":
        profile = load_profile(args.profile)
        result = domain_slo_scheduler_projection.ensure_supervision(
            profile=profile,
            interval_seconds=int(args.interval_seconds),
            trigger_now=not bool(args.no_trigger_now),
            manager=str(args.manager),
            dry_run=bool(args.dry_run),
            write_install_proof=bool(args.write_install_proof),
        )
        _print_json(result)
        return 0

    if args.command == "runtime-remove-supervision":
        profile = load_profile(args.profile)
        result = domain_slo_scheduler_projection.remove_supervision(
            profile=profile,
            interval_seconds=int(args.interval_seconds),
            manager=str(args.manager),
        )
        _print_json(result)
        return 0

    return None


def _print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


__all__ = ["handle_watch_supervision_command"]
