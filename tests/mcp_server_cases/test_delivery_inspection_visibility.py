from __future__ import annotations

import importlib


def _payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "study_id": "001-risk",
        "current_stage": "publication_supervision",
        "paper_stage": "write",
        "delivery_inspection": {
            "surface_kind": "study_delivery_inspection_projection",
            "study_id": "001-risk",
            "status": "layout_migration_pending_sync",
            "summary": "Delivery package is visible; layout migration still needs the next authorized sync.",
            "source_labels": {
                "submission_minimal": "controller-authorized source",
                "current_package": "human-facing mirror",
            },
            "layout_migration_pending_sync": True,
            "layout_migration_upgrade_note": "layout migration 会在下一次 authorized sync 升级",
            "authority": "observability_projection_only",
            "can_authorize_submission": False,
            "can_authorize_publication_quality": False,
            "can_dispatch_delivery_sync": False,
            "large_detail": {"omitted": True},
        },
    }


def test_mcp_compacts_and_renders_delivery_inspection_projection() -> None:
    module = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")

    compact = module.compact_study_progress_projection(_payload())
    markdown = module.render_mcp_study_progress_markdown(_payload())

    delivery = compact["delivery_inspection"]
    assert delivery["status"] == "layout_migration_pending_sync"
    assert delivery["source_labels"] == {
        "submission_minimal": "controller-authorized source",
        "current_package": "human-facing mirror",
        "inspection_package": "human-inspection-only snapshot",
    }
    assert delivery["layout_migration_upgrade_note"] == "layout migration 会在下一次 authorized sync 升级"
    assert "legacy_layout_upgrade_note" not in delivery
    assert "legacy_layout_pending_sync" not in delivery
    assert delivery["authority"] == "observability_projection_only"
    assert delivery["can_authorize_submission"] is False
    assert delivery["can_authorize_publication_quality"] is False
    assert delivery["can_dispatch_delivery_sync"] is False
    assert "large_detail" not in delivery
    assert markdown.strip()
