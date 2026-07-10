from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

def handle_domain_handler_command(
    args: argparse.Namespace,
    *,
    load_profile: Callable[[str | Path], Any],
    load_json_object_file: Callable[[str | Path], dict[str, object]],
    load_module: Callable[[str], Any],
) -> int | None:
    if args.command != "domain-handler":
        return None

    if args.domain_handler_command == "export":
        profile_ref = Path(args.profile)
        profile = load_profile(profile_ref)
        study_ids = tuple(dict.fromkeys([*(args.studies or ()), *(args.study_ids or ())]))
        domain_handler_export = load_module(
            "med_autoscience.controllers.owner_route_handoff.domain_handler_export"
        )
        result = domain_handler_export.export_family_domain_handler(
            profile=profile,
            profile_ref=profile_ref,
            opl_production_proof_ref=args.opl_production_proof,
            study_ids=study_ids,
        )
        _print_json(result)
        return 0

    if args.domain_handler_command == "dispatch":
        task_path = Path(args.task)
        task = load_json_object_file(task_path)
        from med_autoscience.cli.paper_mission_commands import (
            DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND,
            paper_mission_domain_handler_dispatch_receipt,
        )

        if task.get("task_kind") == DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND:
            result = paper_mission_domain_handler_dispatch_receipt(
                task=task,
                task_path=task_path,
                load_profile=load_profile,
            )
            _print_json(result)
            return 0 if bool(result.get("accepted")) else 1
        dispatch_orchestration = load_module(
            "med_autoscience.controllers.owner_route_handoff.dispatch_orchestration"
        )
        result = dispatch_orchestration.dispatch_family_domain_handler_task(task_path=Path(args.task))
        _print_json(result)
        return 0 if bool(result.get("accepted")) else 1

    return None


def _print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


__all__ = ["handle_domain_handler_command"]
