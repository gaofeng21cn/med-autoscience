from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


RETIRED_STATUS = "retired"
RETIRED_REASON = "mas_is_standard_opl_agent_domain_health_diagnostic_control_plane_retired"


def retired_domain_health_diagnostic_report(*, target_kind: str, target: Path) -> dict[str, Any]:
    return {
        "surface_kind": "domain_health_diagnostic_retirement_notice",
        "status": RETIRED_STATUS,
        "reason": RETIRED_REASON,
        "target_kind": target_kind,
        "target": str(Path(target).expanduser()),
        "mas_is_standard_opl_agent": True,
        "dhd_is_control_plane": False,
        "replacement_owner": "one-person-lab",
        "replacement_surface": "opl current_control_state and provider readbacks",
        "apply_supported": False,
    }


def run_domain_health_diagnostic_for_quest(
    *,
    quest_root: Path,
    controller_runners: dict[str, Any] | None = None,
    apply: bool,
    persist_diagnostic_reports: bool | None = None,
) -> dict[str, Any]:
    del controller_runners, apply, persist_diagnostic_reports
    return retired_domain_health_diagnostic_report(target_kind="quest_root", target=quest_root)


def run_domain_health_diagnostic_for_runtime(
    *,
    runtime_root: Path,
    controller_runners: dict[str, Any] | None = None,
    apply: bool,
    persist_diagnostic_reports: bool | None = None,
    profile: Any | None = None,
    study_ids: tuple[str, ...] = (),
    diagnostic_scope: str = "full",
    request_opl_stage_attempts: bool = False,
    request_opl_owner_route_reconcile: bool = False,
) -> dict[str, Any]:
    del (
        controller_runners,
        apply,
        persist_diagnostic_reports,
        profile,
        study_ids,
        diagnostic_scope,
        request_opl_stage_attempts,
        request_opl_owner_route_reconcile,
    )
    return retired_domain_health_diagnostic_report(target_kind="runtime_root", target=runtime_root)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quest-root", type=Path)
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--refresh-diagnostic-reports", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if bool(args.quest_root) == bool(args.runtime_root):
        raise SystemExit("Specify exactly one of --quest-root or --runtime-root")
    if args.quest_root:
        result = run_domain_health_diagnostic_for_quest(
            quest_root=args.quest_root,
            apply=args.apply,
            persist_diagnostic_reports=args.apply or args.refresh_diagnostic_reports,
        )
    else:
        result = run_domain_health_diagnostic_for_runtime(
            runtime_root=args.runtime_root,
            apply=args.apply,
            persist_diagnostic_reports=args.apply or args.refresh_diagnostic_reports,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
