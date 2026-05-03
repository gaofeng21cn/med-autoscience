#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _load_summary(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"lanes": [], "missing": True}
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid lane summary json: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"invalid lane summary payload: {path}: expected object")
    lanes = payload.get("lanes")
    if not isinstance(lanes, list):
        raise SystemExit(f"invalid lane summary payload: {path}: missing lanes list")
    return payload


def _lane_duration(lane: dict[str, Any]) -> int:
    value = lane.get("duration_seconds", 0)
    return value if isinstance(value, int) and value >= 0 else 0


def summarize_lane_summary(path: Path) -> str:
    payload = _load_summary(path)
    lanes = [lane for lane in payload.get("lanes", []) if isinstance(lane, dict)]
    if payload.get("missing"):
        return f"lane summary missing: {path}"
    if not lanes:
        return f"lane summary empty: {path}"

    slowest = max(lanes, key=_lane_duration)
    lines = [f"lane summary: {path}"]
    for lane in lanes:
        lines.append(
            "lane={lane} exit_code={exit_code} duration_seconds={duration_seconds} command={command}".format(
                lane=lane.get("lane", ""),
                exit_code=lane.get("exit_code", ""),
                duration_seconds=lane.get("duration_seconds", ""),
                command=lane.get("command", ""),
            )
        )
    lines.append(
        "slowest_lane={lane} duration_seconds={duration_seconds}".format(
            lane=slowest.get("lane", ""),
            duration_seconds=slowest.get("duration_seconds", ""),
        )
    )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: scripts/summarize-test-lane-durations.py <summary-json>", file=sys.stderr)
        return 2
    print(summarize_lane_summary(Path(argv[1])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
