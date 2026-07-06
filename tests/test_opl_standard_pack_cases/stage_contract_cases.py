from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.opl_standard_pack import build_standard_pack

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read_contract(name: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / "contracts" / f"{name}.json").read_text(encoding="utf-8"))


def test_opl_standard_pack_declares_single_ordinary_default_stage() -> None:
    generated = build_standard_pack()
    profile = _read_contract("golden_path_profile")

    default_stage_ids = [
        stage["stage_id"]
        for stage in generated["stage_control_plane"]["stages"]
        if stage.get("selected_executor", {}).get("default_executor") is True
        and stage.get("selected_executor", {}).get("lane_kind") != "variant"
    ]

    assert default_stage_ids == profile["ordinary_path"]["stage_refs"] == [
        "direction_and_route_selection"
    ]
    assert profile["ordinary_path"]["path_role"] == "ordinary_default"
    assert profile["default_surface_policy"]["ordinary_route_count"] == 1
