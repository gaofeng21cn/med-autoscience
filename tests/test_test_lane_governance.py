from __future__ import annotations

import json
from pathlib import Path
import tomllib

import pytest


pytestmark = pytest.mark.meta
ROOT = Path(__file__).resolve().parents[1]


def test_lane_manifest_paths_and_markers_are_current() -> None:
    manifest = json.loads(
        (ROOT / "contracts/test-lane-manifest.json").read_text(encoding="utf-8")
    )
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    configured = {
        line.split(":", maxsplit=1)[0]
        for line in pyproject["tool"]["pytest"]["ini_options"]["markers"]
    }

    assert set(manifest["marker_registry"]) == configured
    for lane in manifest["lanes"].values():
        for path in lane.get("paths", []):
            assert (ROOT / path).exists(), path
        assert set(lane.get("markers", [])) <= configured


def test_verify_and_make_expose_only_current_standard_agent_lanes() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    verify = (ROOT / "scripts/verify.sh").read_text(encoding="utf-8")

    for lane in ("smoke", "fast", "meta", "regression", "full", "structure"):
        assert f"test-{lane}:" in makefile
        assert lane in verify
    for retired in ("display", "submission", "soak-golden", "control-plane"):
        assert f"test-{retired}:" not in makefile
