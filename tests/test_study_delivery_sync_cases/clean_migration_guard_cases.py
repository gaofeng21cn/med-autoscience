from __future__ import annotations

import importlib
from pathlib import Path

from .shared import dump_json, make_delivery_workspace


def _open_bundle_route_context() -> dict[str, object]:
    return {
        "authority_snapshot": {
            "surface": "authority_snapshot",
            "dispatch_gate": {
                "state": "open",
                "dispatch_allowed": True,
                "blocking_reasons": [],
            },
            "route_authorization": {
                "authorized": True,
                "paper_write_allowed": True,
                "bundle_build_allowed": True,
                "runtime_recovery_allowed": True,
            },
            "authority_refs": {
                "study_truth": {"epoch": "truth-1"},
                "runtime_health": {"epoch": "runtime-1"},
            },
        },
        "controller_route_context": {
            "control_surface": "gate_clearing_batch",
            "controller_action_type": "run_gate_clearing_batch",
            "work_unit_id": "submission_minimal_refresh",
            "requires_human_confirmation": False,
        },
    }


def test_sync_study_delivery_blocks_pending_clean_paper_authority_cutover(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)
    receipt_path = study_root / "artifacts" / "migration" / "paper_authority_cutover" / "latest.json"
    dump_json(
        receipt_path,
        {
            "schema_version": 1,
            "surface_kind": "paper_authority_clean_migration",
            "status": "awaiting_new_mas_authority",
            "study_id": study_root.name,
        },
    )

    result = module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
        route_context=_open_bundle_route_context(),
    )

    assert result["status"] == "paper_authority_clean_migration_pending"
    assert result["blocked_reason"] == "paper_authority_clean_migration_required"
    assert result["next_owner"] == "ai_reviewer"
    assert result["paper_authority_cutover_ref"] == str(receipt_path)
    assert not (study_root / "manuscript" / "delivery_manifest.json").exists()
    assert not (study_root / "manuscript" / "current_package").exists()
    assert not (study_root / "manuscript" / "current_package.zip").exists()
