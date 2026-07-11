from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _manifest() -> dict[str, object]:
    return json.loads(_read("contracts/test-lane-manifest.json"))


def test_fast_lane_uses_its_manifest_paths_and_verify_entrypoint() -> None:
    fast_paths = _manifest()["lanes"]["fast"]["paths"]
    assert fast_paths == [
        "tests/test_smoke_entrypoints.py",
        "tests/test_line_budget.py",
        "tests/test_test_lane_governance.py",
    ]

    makefile = _read("Makefile")
    fast_block = makefile.split("test-fast:", maxsplit=1)[1].split(
        "\ntest-meta:", maxsplit=1
    )[0]
    assert "scripts/run-pytest-clean.sh $(FAST_TESTS) -q" in fast_block
    assert "test-regression" not in fast_block

    verify_script = _read("scripts/verify.sh")
    verify_fast = verify_script.split('if [[ "${lane}" == "fast" ]]', maxsplit=1)[
        1
    ].split('if [[ "${lane}" == "meta" ]]', maxsplit=1)[0]
    assert "make test-fast" in verify_fast


def test_top_level_lane_entries_are_unique_and_resolvable() -> None:
    manifest = _manifest()
    marker_registry = set(manifest["marker_registry"])

    for lane_id, lane in manifest["lanes"].items():
        for key in ("paths", "markers"):
            values = lane.get(key, [])
            assert len(values) == len(set(values)), f"{lane_id} duplicates {key}"
        assert set(lane.get("markers", [])) <= marker_registry
        for path in lane.get("paths", []):
            assert (REPO_ROOT / path).is_file(), path
