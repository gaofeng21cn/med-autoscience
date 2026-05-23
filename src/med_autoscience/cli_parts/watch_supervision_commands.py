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
    load_profile: Any,
) -> int | None:
    if args.command == "domain-health-diagnostic":
        if bool(args.quest_root) == bool(args.runtime_root):
            parser.error("Specify exactly one of --quest-root or --runtime-root")
        if args.quest_root and args.profile:
            parser.error("--profile is only supported with --runtime-root")
        if args.quest_root and args.request_opl_stage_attempts:
            parser.error("--request-opl-stage-attempts is only supported with --runtime-root")
        if args.quest_root and args.request_opl_owner_route_reconcile:
            parser.error("--request-opl-owner-route-reconcile is only supported with --runtime-root")
        if args.request_opl_stage_attempts and not args.profile:
            parser.error("--request-opl-stage-attempts requires --profile")
        if args.request_opl_owner_route_reconcile and not args.request_opl_stage_attempts:
            parser.error("--request-opl-owner-route-reconcile requires --request-opl-stage-attempts")
        if args.request_opl_owner_route_reconcile and not args.apply:
            parser.error("--request-opl-owner-route-reconcile requires --apply")
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
                request_opl_stage_attempts=bool(args.request_opl_stage_attempts),
                request_opl_owner_route_reconcile=bool(args.request_opl_owner_route_reconcile),
            )
        _print_json(result)
        return 0

    return None


def _print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


__all__ = ["handle_watch_supervision_command"]
