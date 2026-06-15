from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

from med_autoscience.agent_entry.renderers import (
    render_stage_route_contract_payload,
    sync_agent_entry_assets,
)
from med_autoscience.foundry_command_surface import (
    build_foundry_command_surface_projection,
    is_foundry_command,
    operation_from_command,
    render_foundry_command_surface_text,
)
from med_autoscience.profiles import profile_to_dict


def handle_public_root_command(
    args: argparse.Namespace,
    *,
    dev_preflight: Any,
    dev_preflight_contract: Any,
    load_profile: Callable[[str], Any],
    load_doctor_module: Callable[[], Any],
    mainline_status: Any,
) -> int | None:
    if is_foundry_command(args.command):
        payload = build_foundry_command_surface_projection(operation=operation_from_command(args.command))
        if args.format == "json":
            _print_json(payload)
        else:
            print(render_foundry_command_surface_text(payload), end="")
        return 0

    if args.command == "doctor":
        profile = load_profile(args.profile)
        doctor = load_doctor_module()
        print(doctor.render_doctor_report(doctor.build_doctor_report(profile)), end="")
        return 0

    if args.command == "show-profile":
        profile = load_profile(args.profile)
        if args.format == "json":
            _print_json(profile_to_dict(profile))
        else:
            print(load_doctor_module().render_profile(profile), end="")
        return 0

    if args.command == "mainline-status":
        result = mainline_status.read_mainline_status()
        if args.format == "json":
            _print_json(result)
        else:
            print(mainline_status.render_mainline_status_markdown(result), end="")
        return 0

    if args.command == "mainline-phase":
        result = mainline_status.read_mainline_phase_status(args.phase)
        if args.format == "json":
            _print_json(result)
        else:
            print(mainline_status.render_mainline_phase_markdown(result), end="")
        return 0

    if args.command == "show-stage-route-contract":
        _print_json(render_stage_route_contract_payload())
        return 0

    if args.command == "sync-agent-entry-assets":
        result = sync_agent_entry_assets(repo_root=Path(args.repo_root))
        _print_json(result)
        return 0

    if args.command == "preflight-changes":
        return _handle_preflight_changes_command(args, dev_preflight=dev_preflight)

    if args.command == "preflight-contract-report":
        result = dev_preflight_contract.build_preflight_contract_report()
        _print_json(result)
        return 0

    return None


def _handle_preflight_changes_command(
    args: argparse.Namespace,
    *,
    dev_preflight: Any,
) -> int:
    input_mode = "files"
    if args.staged:
        input_mode = "staged"
    elif args.base_ref:
        input_mode = "base_ref"
    if args.base_ref:
        result = dev_preflight.run_ci_preflight(base_ref=args.base_ref, repo_root=Path.cwd())
    else:
        changed_files = dev_preflight.collect_changed_files(
            repo_root=Path.cwd(),
            files=list(args.files or []),
            staged=bool(args.staged),
            base_ref=args.base_ref,
        )
        result = dev_preflight.run_preflight(
            changed_files=changed_files,
            repo_root=Path.cwd(),
            input_mode=input_mode,
        )
    if args.format == "json":
        _print_json(result.to_dict())
    else:
        print(dev_preflight.render_preflight_text(result), end="")
    return 0 if result.ok else 1


def _print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


__all__ = ["handle_public_root_command"]
