from __future__ import annotations

import subprocess
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "profile-heavy-test-lanes.py"


def test_heavy_lane_profile_print_only_exposes_reproducible_duration_commands() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "display", "submission", "--durations", "20", "--print-only"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.splitlines() == [
        "uv run pytest -q -m display_heavy --durations=20",
        "uv run pytest -q -m submission_heavy --durations=20",
    ]


def test_heavy_lane_profile_defaults_cover_all_costly_lanes() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--print-only"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    lines = result.stdout.splitlines()
    assert "uv run pytest -q -m display_heavy --durations=50" in lines
    assert "uv run pytest -q -m submission_heavy --durations=50" in lines
    assert (
        "uv run pytest -q -m 'not meta and not display_heavy and not submission_heavy and not family' "
        "--durations=50"
    ) in lines


def test_heavy_lane_profile_rejects_non_positive_duration_window() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "display", "--durations", "0", "--print-only"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--durations must be a positive integer" in result.stderr
