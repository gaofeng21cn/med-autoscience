#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from med_autoscience.controllers.real_paper_autonomy_soak_inventory import (
    DEFAULT_YANG_ROOT,
    build_real_paper_autonomy_guarded_apply_proof,
    build_real_paper_autonomy_soak_inventory,
    build_real_paper_autonomy_soak_closeout_projection,
    build_real_paper_autonomy_provider_hosted_paper_proof,
    build_real_paper_autonomy_soak_projection,
)
from med_autoscience.controllers.real_paper_autonomy_live_supervisor_canary import (
    DEFAULT_TARGET_STUDIES as DEFAULT_LIVE_CANARY_STUDIES,
    run_live_supervisor_canary,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run inventory for real-paper autonomy soak readiness.",
    )
    parser.add_argument(
        "--yang-root",
        default=str(DEFAULT_YANG_ROOT),
        help="Root containing Yang project workspaces. Defaults to /Users/gaofeng/workspace/Yang.",
    )
    parser.add_argument(
        "--profile",
        action="append",
        dest="profiles",
        help="Specific profile path to inspect. May be passed multiple times.",
    )
    parser.add_argument(
        "--mode",
        choices=(
            "inventory",
            "projection",
            "closeout",
            "provider-proof",
            "guarded-apply-proof",
            "live-supervisor-canary",
        ),
        default="inventory",
        help="Output mode. live-supervisor-canary runs read-only study progress plus DHD dry-run identity checks.",
    )
    parser.add_argument(
        "--study",
        action="append",
        dest="studies",
        help=(
            "Study id for live-supervisor-canary. May be passed multiple times; "
            "defaults to DM002/DM003 canonical study ids."
        ),
    )
    args = parser.parse_args()

    kwargs = {
        "yang_root": Path(args.yang_root),
        "profile_paths": [Path(path) for path in args.profiles] if args.profiles else None,
    }
    if args.mode == "live-supervisor-canary":
        if not args.profiles or len(args.profiles) != 1:
            raise SystemExit("live-supervisor-canary requires exactly one --profile")
        payload = run_live_supervisor_canary(
            profile_path=Path(args.profiles[0]),
            study_ids=tuple(args.studies or DEFAULT_LIVE_CANARY_STUDIES),
        )
    elif args.mode == "projection":
        payload = build_real_paper_autonomy_soak_projection(**kwargs)
    elif args.mode == "closeout":
        payload = build_real_paper_autonomy_soak_closeout_projection(**kwargs)
    elif args.mode == "provider-proof":
        payload = build_real_paper_autonomy_provider_hosted_paper_proof(**kwargs)
    elif args.mode == "guarded-apply-proof":
        payload = build_real_paper_autonomy_guarded_apply_proof(**kwargs)
    else:
        payload = build_real_paper_autonomy_soak_inventory(**kwargs)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
