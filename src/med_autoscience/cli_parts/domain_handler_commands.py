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
    owner_route_handoff: Any,
    owner_route_reconcile: Any,
) -> int | None:
    if args.command != "domain-handler":
        return None

    if args.domain_handler_command == "export":
        profile_ref = Path(args.profile)
        profile = load_profile(profile_ref)
        result = owner_route_handoff.export_family_domain_handler(
            profile=profile,
            profile_ref=profile_ref,
            opl_production_proof_ref=args.opl_production_proof,
        )
        _print_json(result)
        return 0

    if args.domain_handler_command == "dispatch":
        result = owner_route_handoff.dispatch_family_domain_handler_task(task_path=Path(args.task))
        _print_json(result)
        return 0 if bool(result.get("accepted")) else 1

    if args.domain_handler_command == "dispatch-evidence-payload":
        profile_ref = Path(args.profile)
        profile = load_profile(profile_ref)
        workorder = load_json_object_file(args.workorder)
        payload_export = load_module(
            "med_autoscience.controllers.owner_route_handoff_parts.domain_dispatch_evidence_payload_export"
        )
        study_id = payload_export.study_id_from_workorder(workorder)
        owner_route_scan = owner_route_reconcile.scan_domain_routes(
            profile=profile,
            study_ids=(study_id,) if study_id else tuple(),
            apply_safe_actions=False,
            developer_supervisor_mode=None,
        )
        result = payload_export.build_dispatch_evidence_payload_export(
            profile=profile,
            profile_ref=profile_ref,
            workorder=workorder,
            owner_route_scan=owner_route_scan,
        )
        _print_json(result)
        ready_statuses = {"typed_blocker_payload_ready", "owner_receipt_payload_ready"}
        return 0 if result.get("status") in ready_statuses else 1

    return None


def _print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


__all__ = ["handle_domain_handler_command"]
