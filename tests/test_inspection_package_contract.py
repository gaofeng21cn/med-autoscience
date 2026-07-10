from __future__ import annotations

from pathlib import Path

import pytest


pytestmark = pytest.mark.contract

REPO_ROOT = Path(__file__).resolve().parents[1]
def test_delivery_inspection_projection_remains_observability_only_for_inspection_package_path() -> None:
    from med_autoscience.controllers.delivery_visibility_projection import (
        compact_delivery_inspection_projection,
    )

    projection = compact_delivery_inspection_projection(
        {
            "surface": "delivery_inspector",
            "schema_version": 1,
            "study_id": "001-risk",
            "freshness": {"verdict": "stale", "delivery_status": "stale_source_changed"},
            "mutation_policy": {"read_only": True, "writes_package": False},
            "source_package": {
                "role": "controller_authorized_source",
                "root": "/workspace/studies/001-risk/paper/submission_minimal",
                "exists": True,
                "layout_status": "v2",
            },
            "human_package": {
                "role": "human_facing_mirror",
                "root": "/workspace/studies/001-risk/manuscript/current_package",
                "exists": True,
                "layout_status": "v2",
            },
            "next_sync_owner_surface_ref": "mas:study_delivery_sync",
        }
    )

    assert projection is not None
    assert projection["authority"] == "observability_projection_only"
    assert projection["projection_only"] is True
    assert projection["can_authorize_submission"] is False
    assert projection["can_authorize_publication_quality"] is False
    assert projection["can_dispatch_delivery_sync"] is False
    assert projection["status"] == "stale"


def test_inspection_package_plan_distinguishes_allowed_outputs_from_submission_outputs() -> None:
    allowed_outputs = {
        "manuscript/inspection_package",
        "manuscript/inspection_package.zip",
        "artifacts/inspection_package/manifest.json",
        "artifacts/inspection_package/source_inventory.json",
        "artifacts/inspection_package/export_receipt.json",
    }
    forbidden_outputs = {
        "paper/submission_minimal",
        "manuscript/current_package",
        "manuscript/current_package.zip",
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
    }
    export_plan = {
        "surface_kind": "inspection_package",
        "authority": "human_inspection_only",
        "gate_blocked_snapshot": True,
        "not_for_submission": True,
        "allowed_outputs": sorted(allowed_outputs),
        "forbidden_writes": sorted(forbidden_outputs),
        "can_authorize_submission": False,
        "can_authorize_publication_quality": False,
        "can_clear_publishability_gate": False,
        "can_dispatch_delivery_sync": False,
    }

    assert export_plan["surface_kind"] == "inspection_package"
    assert export_plan["allowed_outputs"] == sorted(allowed_outputs)
    assert not set(export_plan["allowed_outputs"]) & set(export_plan["forbidden_writes"])
    assert "manuscript/current_package" in export_plan["forbidden_writes"]
    assert "artifacts/publication_eval/latest.json" in export_plan["forbidden_writes"]
    assert export_plan["can_authorize_submission"] is False
    assert export_plan["can_authorize_publication_quality"] is False
    assert export_plan["can_clear_publishability_gate"] is False
    assert export_plan["can_dispatch_delivery_sync"] is False
