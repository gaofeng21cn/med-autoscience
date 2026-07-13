from __future__ import annotations

import json
from pathlib import Path
import tomllib

import pytest


pytestmark = pytest.mark.meta
REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _manifest() -> dict[str, object]:
    return json.loads(_read("contracts/test-lane-manifest.json"))


def test_smoke_lane_paths_match_its_make_recipe() -> None:
    paths = _manifest()["lanes"]["smoke"]["paths"]

    assert paths == ["tests/test_smoke_entrypoints.py"]
    expected_recipe = f"\t@$(call run_isolated_python,-m pytest {' '.join(paths)} -q)"
    smoke_recipe = _read("Makefile").split("test-smoke:\n", 1)[1].split("\n\n", 1)[0]
    assert smoke_recipe == expected_recipe


def test_test_lane_manifest_registers_pytest_markers() -> None:
    manifest_markers = set(_manifest()["marker_registry"])
    marker_lines = tomllib.loads(_read("pyproject.toml"))["tool"]["pytest"]["ini_options"]["markers"]
    registered_markers = {line.split(":", maxsplit=1)[0] for line in marker_lines}

    assert manifest_markers == registered_markers
