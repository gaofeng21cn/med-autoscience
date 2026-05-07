from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _lane_manifest() -> dict[str, object]:
    return json.loads(_read("contracts/test-lane-manifest.json"))


def test_smoke_lane_is_minimal_read_only_entry_contract() -> None:
    makefile = _read("Makefile")
    manifest = _lane_manifest()

    assert manifest["lanes"]["smoke"]["paths"] == [
        "tests/test_smoke_entrypoints.py",
        "tests/test_line_budget.py",
    ]
    assert "test-smoke:" in makefile
    assert (
        "\tuv run pytest tests/test_smoke_entrypoints.py tests/test_line_budget.py -q"
        in makefile
    )
    smoke_block = makefile.split("test-smoke:", maxsplit=1)[1].split(
        "\ntest-regression:",
        maxsplit=1,
    )[0]
    assert "test_test_command_surfaces.py" not in smoke_block


def test_test_lane_manifest_registers_pytest_markers() -> None:
    manifest = _lane_manifest()
    pyproject = tomllib.loads(_read("pyproject.toml"))
    marker_lines = pyproject["tool"]["pytest"]["ini_options"]["markers"]
    marker_names = {line.split(":", maxsplit=1)[0] for line in marker_lines}

    assert set(manifest["marker_registry"]) <= marker_names
    for marker_name in ("contract", "integration", "materialization_heavy", "soak_or_golden"):
        assert marker_name in manifest["marker_registry"]
