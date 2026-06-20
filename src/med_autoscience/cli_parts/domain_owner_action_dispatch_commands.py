from __future__ import annotations

import argparse
import json
from typing import Any


def handle_domain_owner_action_dispatch_command(
    args: argparse.Namespace,
    *,
    domain_owner_action_dispatch: Any,
    load_profile: Any,
) -> int | None:
    if args.command != "domain-owner-action-dispatch":
        return None

    profile = load_profile(args.profile)
    study_ids = tuple(args.studies or ())
    if args.study_id:
        study_ids = (*study_ids, args.study_id)
    result = domain_owner_action_dispatch.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=study_ids,
        mode=args.mode,
        apply=bool(args.apply),
        action_types=tuple(args.action_types or ()),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


__all__ = ["handle_domain_owner_action_dispatch_command"]
