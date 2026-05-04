#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex
import subprocess
import sys


LANE_MARKERS: dict[str, str] = {
    "display": "display_heavy",
    "submission": "submission_heavy",
    "regression": "not meta and not display_heavy and not submission_heavy and not family",
}


def profile_command(lane: str, *, durations: int) -> list[str]:
    try:
        marker = LANE_MARKERS[lane]
    except KeyError as exc:
        valid = ", ".join(sorted(LANE_MARKERS))
        raise SystemExit(f"unknown heavy test lane: {lane}; expected one of: {valid}") from exc
    return ["uv", "run", "pytest", "-q", "-m", marker, f"--durations={durations}"]


def profile_commands(lanes: list[str], *, durations: int) -> list[list[str]]:
    selected_lanes = lanes or sorted(LANE_MARKERS)
    return [profile_command(lane, durations=durations) for lane in selected_lanes]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="scripts/profile-heavy-test-lanes.py",
        usage="%(prog)s [display|submission|regression ...] [--durations N] [--print-only]",
    )
    parser.add_argument("lanes", nargs="*", choices=sorted(LANE_MARKERS))
    parser.add_argument("--durations", type=int, default=50)
    parser.add_argument("--print-only", action="store_true")
    args = parser.parse_args(argv[1:])

    if args.durations <= 0:
        raise SystemExit("--durations must be a positive integer")

    for command in profile_commands(args.lanes, durations=args.durations):
        print(shlex.join(command))
        if args.print_only:
            continue
        completed = subprocess.run(command, check=False)
        if completed.returncode != 0:
            return completed.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
