from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
PARALLEL_FULL_LANES = (
    "test-regression",
    "test-meta",
    "test-display",
    "test-submission",
    "test-family",
)
def test_lane_duration_summary_script_reports_slowest_lane(tmp_path: Path) -> None:
    summary_path = tmp_path / "lanes.json"
    summary_path.write_text(
        json.dumps(
            {
                "lanes": [
                    {
                        "lane": "test-regression",
                        "command": "make test-regression",
                        "exit_code": 0,
                        "duration_seconds": 4,
                    },
                    {
                        "lane": "test-display",
                        "command": "make test-display",
                        "exit_code": 0,
                        "duration_seconds": 11,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        ["uv", "run", "python", "scripts/summarize-test-lane-durations.py", str(summary_path)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "lane=test-regression exit_code=0 duration_seconds=4 command=make test-regression" in result.stdout
    assert "lane=test-display exit_code=0 duration_seconds=11 command=make test-display" in result.stdout
    assert "slowest_lane=test-display duration_seconds=11" in result.stdout


def test_lane_duration_history_script_reports_per_lane_trends(tmp_path: Path) -> None:
    summary_dir = tmp_path / "history"
    baseline_dir = summary_dir / "2026-01-01"
    current_dir = summary_dir / "2026-01-02"
    baseline_dir.mkdir(parents=True)
    current_dir.mkdir()
    (current_dir / "current.json").write_text(
        json.dumps(
            {
                "lanes": [
                    {"lane": "regression", "duration_seconds": 10},
                    {"lane": "display", "duration_seconds": 30},
                ]
            }
        ),
        encoding="utf-8",
    )
    (baseline_dir / "previous.json").write_text(
        json.dumps(
            {
                "lanes": [
                    {"lane": "regression", "duration_seconds": 6},
                    {"lane": "display", "duration_seconds": 50},
                    {"lane": "display", "duration_seconds": -1},
                ]
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        ["uv", "run", "python", "scripts/summarize-test-lane-history.py", str(summary_dir)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert f"lane history summary: {summary_dir}" in result.stdout
    assert (
        f"lane=display samples=2 median_seconds=40 max_seconds=50 "
        f"slowest_seconds=50 slowest_summary={baseline_dir / 'previous.json'} "
        "delta_from_baseline_percent=-20.0"
        in result.stdout
    )
    assert f"slowest_lane=display duration_seconds=50 summary={baseline_dir / 'previous.json'}" in result.stdout
    assert (
        f"lane=regression samples=2 median_seconds=8 max_seconds=10 "
        f"slowest_seconds=10 slowest_summary={current_dir / 'current.json'} "
        "delta_from_baseline_percent=33.3"
        in result.stdout
    )


def test_lane_duration_history_script_accepts_explicit_baseline(tmp_path: Path) -> None:
    summary_dir = tmp_path / "history"
    summary_dir.mkdir()
    summary_path = summary_dir / "current.json"
    summary_path.write_text(
        json.dumps(
            {
                "lanes": [
                    {"lane": "regression", "duration_seconds": 12},
                    {"lane": "display", "duration_seconds": 36},
                ]
            }
        ),
        encoding="utf-8",
    )
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        json.dumps(
            {
                "lanes": [
                    {"lane": "regression", "duration_seconds": 10},
                    {"lane": "display", "duration_seconds": 40},
                    {"lane": "missing-later", "duration_seconds": 20},
                ]
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/summarize-test-lane-history.py",
            str(summary_dir),
            "--baseline",
            str(baseline_path),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (
        f"lane=display samples=1 median_seconds=36 max_seconds=36 slowest_seconds=36 "
        f"slowest_summary={summary_path} "
        "delta_from_baseline_percent=-10.0"
        in result.stdout
    )
    assert (
        f"lane=regression samples=1 median_seconds=12 max_seconds=12 slowest_seconds=12 "
        f"slowest_summary={summary_path} "
        "delta_from_baseline_percent=20.0"
        in result.stdout
    )


def test_lane_duration_history_json_contract_has_stable_schema_and_null_delta_semantics(
    tmp_path: Path,
) -> None:
    summary_dir = tmp_path / "history"
    summary_dir.mkdir()
    first_summary_path = summary_dir / "current-a.json"
    second_summary_path = summary_dir / "current-b.json"
    first_summary_path.write_text(
        json.dumps(
            {
                "lanes": [
                    {"lane": "regression", "duration_seconds": 12},
                    {"lane": "display", "duration_seconds": 36},
                ]
            }
        ),
        encoding="utf-8",
    )
    second_summary_path.write_text(
        json.dumps({"lanes": [{"lane": "regression", "duration_seconds": 13}]}),
        encoding="utf-8",
    )
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        json.dumps(
            {
                "lanes": [
                    {"lane": "regression", "duration_seconds": 10},
                    {"lane": "display", "duration_seconds": 0},
                ]
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/summarize-test-lane-history.py",
            str(summary_dir),
            "--baseline",
            str(baseline_path),
            "--format",
            "json",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert set(payload) == {"surface_kind", "summary_dir", "lanes"}
    assert isinstance(payload["lanes"], list)
    for lane in payload["lanes"]:
        assert set(lane) == {
            "lane",
            "samples",
            "median_seconds",
            "max_seconds",
            "slowest_seconds",
            "slowest_summary",
            "delta_from_baseline_percent",
        }
        for numeric_key in ("samples", "median_seconds", "max_seconds", "slowest_seconds"):
            numeric_value = lane[numeric_key]
            assert isinstance(numeric_value, int | float) and not isinstance(numeric_value, bool)
        delta = lane["delta_from_baseline_percent"]
        assert delta is None or (
            isinstance(delta, int | float) and not isinstance(delta, bool)
        )
    assert payload == {
        "surface_kind": "test_lane_history_summary",
        "summary_dir": str(summary_dir),
        "lanes": [
            {
                "lane": "display",
                "samples": 1,
                "median_seconds": 36,
                "max_seconds": 36,
                "slowest_seconds": 36,
                "slowest_summary": str(first_summary_path),
                "delta_from_baseline_percent": None,
            },
            {
                "lane": "regression",
                "samples": 2,
                "median_seconds": 12.5,
                "max_seconds": 13,
                "slowest_seconds": 13,
                "slowest_summary": str(second_summary_path),
                "delta_from_baseline_percent": 25.0,
            },
        ],
    }


def test_lane_duration_history_script_reports_null_delta_without_usable_baseline(tmp_path: Path) -> None:
    summary_dir = tmp_path / "history"
    summary_dir.mkdir()
    summary_path = summary_dir / "current.json"
    summary_path.write_text(
        json.dumps({"lanes": [{"lane": "regression", "duration_seconds": 12}]}),
        encoding="utf-8",
    )
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        json.dumps({"lanes": [{"lane": "regression", "duration_seconds": 0}]}),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/summarize-test-lane-history.py",
            str(summary_dir),
            "--baseline",
            str(baseline_path),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (
        f"lane=regression samples=1 median_seconds=12 max_seconds=12 slowest_seconds=12 "
        f"slowest_summary={summary_path} "
        "delta_from_baseline_percent=null"
        in result.stdout
    )


def test_lane_duration_history_script_reports_null_delta_when_history_is_too_short(tmp_path: Path) -> None:
    summary_dir = tmp_path / "history"
    summary_dir.mkdir()
    summary_path = summary_dir / "current.json"
    summary_path.write_text(
        json.dumps({"lanes": [{"lane": "regression", "duration_seconds": 12}]}),
        encoding="utf-8",
    )

    result = subprocess.run(
        ["uv", "run", "python", "scripts/summarize-test-lane-history.py", str(summary_dir)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (
        f"lane=regression samples=1 median_seconds=12 max_seconds=12 slowest_seconds=12 "
        f"slowest_summary={summary_path} "
        "delta_from_baseline_percent=null"
        in result.stdout
    )

