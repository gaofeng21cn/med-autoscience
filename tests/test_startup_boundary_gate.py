from __future__ import annotations

import importlib
from pathlib import Path

from .study_runtime_test_helpers import make_profile


def test_render_boundary_custom_brief_requires_public_data_follow_through(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.startup_boundary_gate")
    profile = make_profile(tmp_path)
    study_root = tmp_path / "studies" / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)

    boundary_gate = module.evaluate_startup_boundary(
        profile=profile,
        study_root=study_root,
        study_payload={},
        execution={},
    )
    brief = module.render_boundary_custom_brief(existing_brief="", boundary_gate=boundary_gate)

    assert "Check `portfolio/data_assets/public/registry.json` before route lock" in brief
    assert "record retain / reject decisions through `apply-data-asset-update`" in brief
    assert "immediate download or materialization follow-through" in brief
