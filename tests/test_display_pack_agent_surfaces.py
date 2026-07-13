from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta
REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_json(relative_path: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def test_display_capability_is_stage_affordance_not_private_public_action() -> None:
    catalog = _read_json("contracts/action_catalog.json")
    manifest = _read_json("agent/stages/manifest.json")
    capability_map = _read_json("contracts/capability_map.json")
    action_ids = {action["action_id"] for action in catalog["actions"]}

    assert not any(action_id.startswith("display_pack") for action_id in action_ids)
    for stage in manifest["stages"]:
        capability_refs = {
            ref["ref"] for ref in stage["tool_affordance_boundary"]["capability_refs"]
        }
        assert "medical_analysis_manuscript_figure_and_review_workspace_operation" in (
            capability_refs
        )

    figure_capability = next(
        capability
        for capability in capability_map["capabilities"]
        if capability["capability_id"] == "medical-figure-design"
    )
    assert figure_capability["physical_source_ref"]["ref"].endswith(
        "skills/medical-figure-design/SKILL.md"
    )
    assert figure_capability["authority_boundary"]["can_mutate_artifact_body"] is False
    assert figure_capability["authority_boundary"]["can_authorize_quality_or_export"] is False
    assert figure_capability["authority_boundary"]["closeout_requires_mas_owner_surface"] is True
