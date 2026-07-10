from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml


pytestmark = pytest.mark.meta
REPO_ROOT = Path(__file__).resolve().parents[1]


def test_stage_route_contract_projects_kernel_ordinary_progress_handoff() -> None:
    route = yaml.safe_load(
        (REPO_ROOT / "agent/stages/stage_route_contract.yaml").read_text(encoding="utf-8")
    )["ordinary_progress_handoff_policy"]
    kernel = json.loads(
        (REPO_ROOT / "contracts/stage_run_kernel_profile.json").read_text(encoding="utf-8")
    )["ordinary_progress_handoff"]

    assert route.pop("source_ref") == (
        "contracts/stage_run_kernel_profile.json#/ordinary_progress_handoff"
    )
    assert route == {
        key: value
        for key, value in kernel.items()
        if key not in {"surface_kind", "version"}
    }
