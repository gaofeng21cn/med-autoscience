#!/usr/bin/env python3
from __future__ import annotations

import argparse
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


def _format_delta_percent(current: float, baseline: float | None) -> str:
    if baseline is None or baseline <= 0:
        return "null"
    return f"{((current - baseline) / baseline) * 100:.1f}"


def _delta_percent(current: float, baseline: float | None) -> float | None:
    if baseline is None or baseline <= 0:
        return None
    return round(((current - baseline) / baseline) * 100, 1)


def _numeric_median(values: list[int]) -> int | float:
    median = statistics.median(values)
    if isinstance(median, int) or median.is_integer():
        return int(median)
    return median


def _baseline_durations(path: Path) -> dict[str, float]:
    payload = _load_summary(path)
    lane_durations: dict[str, list[int]] = {}
    for lane in payload["lanes"]:
        if not isinstance(lane, dict):
            continue
        lane_name = lane.get("lane")
        duration_seconds = _lane_duration(lane)
        if not isinstance(lane_name, str) or not lane_name or duration_seconds is None:
            continue
        lane_durations.setdefault(lane_name, []).append(duration_seconds)
    return {
        lane_name: statistics.median(durations)
        for lane_name, durations in lane_durations.items()
        if durations
    }


def _lane_records(summary_dir: Path) -> dict[str, list[tuple[int, Path]]] | None:
    if not summary_dir.exists():
        return None
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
    return lane_records


def summarize_lane_history(summary_dir: Path, baseline_path: Path | None = None) -> str:
    lane_records = _lane_records(summary_dir)
    if not lane_records:
        return f"lane history summary empty: {summary_dir}"

    explicit_baselines = _baseline_durations(baseline_path) if baseline_path is not None else {}
    lines = [f"lane history summary: {summary_dir}"]
    for lane_name in sorted(lane_records):
        records = lane_records[lane_name]
        durations = [duration for duration, _path in records]
        median = statistics.median(durations)
        baseline_duration = explicit_baselines.get(lane_name)
        if baseline_path is None and len(records) >= 2:
            baseline_duration = records[0][0]
        slowest_duration, slowest_path = max(records, key=lambda record: record[0])
        lines.append(
            "lane={lane} samples={samples} median_seconds={median} max_seconds={maximum} "
            "slowest_seconds={slowest_seconds} slowest_summary={slowest_summary} "
            "delta_from_baseline_percent={delta}".format(
                lane=lane_name,
                samples=len(records),
                median=_format_median(durations),
                maximum=max(durations),
                slowest_seconds=slowest_duration,
                slowest_summary=slowest_path,
                delta=_format_delta_percent(median, baseline_duration),
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


def summarize_lane_history_json(summary_dir: Path, baseline_path: Path | None = None) -> dict[str, Any]:
    lane_records = _lane_records(summary_dir)
    explicit_baselines = _baseline_durations(baseline_path) if baseline_path is not None else {}
    payload: dict[str, Any] = {
        "surface_kind": "test_lane_history_summary",
        "summary_dir": str(summary_dir),
        "lanes": [],
    }
    if not lane_records:
        return payload

    lanes: list[dict[str, Any]] = []
    for lane_name in sorted(lane_records):
        records = lane_records[lane_name]
        durations = [duration for duration, _path in records]
        median = _numeric_median(durations)
        baseline_duration = explicit_baselines.get(lane_name)
        slowest_duration, slowest_path = max(records, key=lambda record: record[0])
        lanes.append(
            {
                "lane": lane_name,
                "samples": len(records),
                "median_seconds": median,
                "max_seconds": max(durations),
                "slowest_seconds": slowest_duration,
                "slowest_summary": str(slowest_path),
                "delta_from_baseline_percent": _delta_percent(float(median), baseline_duration),
            }
        )
    payload["lanes"] = lanes
    return payload


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="scripts/summarize-test-lane-history.py",
        usage="%(prog)s <summary-dir> [--baseline <json>] [--format text|json]",
    )
    parser.add_argument("summary_dir", metavar="<summary-dir>")
    parser.add_argument("--baseline", metavar="<json>")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv[1:])

    summary_dir = Path(args.summary_dir)
    baseline_path = Path(args.baseline) if args.baseline is not None else None
    if args.format == "json":
        print(json.dumps(summarize_lane_history_json(summary_dir, baseline_path), sort_keys=True))
    else:
        print(summarize_lane_history(summary_dir, baseline_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
