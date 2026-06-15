from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Callable


def overlay_request_from_args(
    args: argparse.Namespace,
    *,
    load_profile: Callable[[str], Any],
    load_doctor_module: Callable[[], Any],
) -> dict[str, object]:
    if getattr(args, "profile", None) and getattr(args, "quest_root", None):
        raise SystemExit("Specify at most one of --profile or --quest-root")
    if getattr(args, "profile", None):
        profile = load_profile(args.profile)
        request = load_doctor_module().overlay_request_from_profile(profile)
        if not profile.enable_medical_overlay:
            request["skill_ids"] = tuple()
        return request
    return {
        "quest_root": Path(args.quest_root) if getattr(args, "quest_root", None) else None,
        "skill_ids": None,
    }


__all__ = ["overlay_request_from_args"]
