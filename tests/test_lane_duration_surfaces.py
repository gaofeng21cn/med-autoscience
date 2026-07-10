import json
from pathlib import Path
import subprocess
import sys
import pytest

pytestmark = pytest.mark.meta
ROOT = Path(__file__).resolve().parents[1]


def _write(path, lanes):
    path.write_text(json.dumps({"lanes": lanes}), encoding="utf-8")


def _run(*args):
    return subprocess.run([sys.executable, *map(str, args)], cwd=ROOT, text=True, capture_output=True)


def test_lane_duration_summary_and_history_scripts_keep_advisory_schema(tmp_path):
    summary = tmp_path / "summary.json"
    _write(summary, [
        {"lane": "regression", "command": "make test-regression", "exit_code": 0, "duration_seconds": 4},
        {"lane": "display", "command": "make test-display", "exit_code": 0, "duration_seconds": 11},
    ])
    result = _run("scripts/summarize-test-lane-durations.py", summary)
    result.check_returncode()
    assert {
        "lane=regression exit_code=0 duration_seconds=4 command=make test-regression",
        "slowest_lane=display duration_seconds=11",
    } <= set(result.stdout.splitlines())
    history = tmp_path / "history"
    history.mkdir()
    _write(history / "a.json", [
        {"lane": "regression", "duration_seconds": 12},
        {"lane": "display", "duration_seconds": 36},
    ])
    _write(history / "b.json", [{"lane": "regression", "duration_seconds": 13}])
    baseline = tmp_path / "baseline.json"
    _write(baseline, [{"lane": "regression", "duration_seconds": 10}, {"lane": "display", "duration_seconds": 0}])
    result = _run("scripts/summarize-test-lane-history.py", history, "--baseline", baseline, "--format", "json")
    result.check_returncode()
    payload = json.loads(result.stdout)
    lanes = {lane["lane"]: lane for lane in payload["lanes"]}
    schema = set("lane samples median_seconds max_seconds slowest_seconds slowest_summary delta_from_baseline_percent".split())
    assert (payload["surface_kind"], payload["summary_dir"], set(payload)) == (
        "test_lane_history_summary", str(history), {"surface_kind", "summary_dir", "lanes"}
    )
    assert all(set(lane) == schema for lane in payload["lanes"])
    values = (lanes["regression"]["median_seconds"], lanes["regression"]["delta_from_baseline_percent"],
              lanes["display"]["delta_from_baseline_percent"])
    assert values == (12.5, 25.0, None)
