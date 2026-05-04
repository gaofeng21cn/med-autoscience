#!/usr/bin/env python3
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path
from typing import Any


def _load_summary(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid lane summary json: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"invalid lane summary payload: {path}: expected object")
    lanes = payload.get("lanes")
    if not isinstance(lanes, list):
        raise SystemExit(f"invalid lane summary payload: {path}: missing lanes list")
    return payload


def _lane_duration(lane: dict[str, Any]) -> int | None:
    value = lane.get("duration_seconds")
    if isinstance(value, int) and value >= 0:
        return value
    return None


def _format_median(values: list[int]) -> str:
    median = statistics.median(values)
    if isinstance(median, int) or median.is_integer():
        return str(int(median))
    return f"{median:.1f}"


def summarize_lane_history(summary_dir: Path) -> str:
    if not summary_dir.exists():
        return f"lane history summary empty: {summary_dir}"
    if not summary_dir.is_dir():
        raise SystemExit(f"invalid lane summary directory: {summary_dir}")

    lane_records: dict[str, list[tuple[int, Path]]] = {}
    for path in sorted(summary_dir.rglob("*.json")):
        payload = _load_summary(path)
        for lane in payload["lanes"]:
            if not isinstance(lane, dict):
                continue
            lane_name = lane.get("lane")
            duration_seconds = _lane_duration(lane)
            if not isinstance(lane_name, str) or not lane_name or duration_seconds is None:
                continue
            lane_records.setdefault(lane_name, []).append((duration_seconds, path))

    if not lane_records:
        return f"lane history summary empty: {summary_dir}"

    lines = [f"lane history summary: {summary_dir}"]
    for lane_name in sorted(lane_records):
        records = lane_records[lane_name]
        durations = [duration for duration, _path in records]
        slowest_duration, slowest_path = max(records, key=lambda record: record[0])
        lines.append(
            "lane={lane} samples={samples} median_seconds={median} max_seconds={maximum} "
            "slowest_summary={slowest_summary}".format(
                lane=lane_name,
                samples=len(records),
                median=_format_median(durations),
                maximum=max(durations),
                slowest_summary=slowest_path,
            )
        )
        lines.append(
            "slowest_lane={lane} duration_seconds={duration_seconds} summary={summary}".format(
                lane=lane_name,
                duration_seconds=slowest_duration,
                summary=slowest_path,
            )
        )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: scripts/summarize-test-lane-history.py <summary-dir>", file=sys.stderr)
        return 2
    print(summarize_lane_history(Path(argv[1])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
