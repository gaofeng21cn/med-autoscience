from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers.opl_stage_promotion_runtime import (
    promotion_audit_from_deliverable_root,
    promotion_audit_from_stage_projection,
)


def test_stage_projection_audit_accepts_promoted_terminal_current_pointer() -> None:
    audit = promotion_audit_from_stage_projection(
        {
            "surface_kind": "mas_opl_physical_stage_folder_projection",
            "stage_id": "06-manuscript_authoring",
            "status": "observed",
            "latest_attempt_id": "attempt-002",
            "manifest_ref": "stages/06-manuscript_authoring/attempts/attempt-002/manifest.json",
            "receipt_ref": "stages/06-manuscript_authoring/attempts/attempt-002/receipts/owner.json",
            "current_outputs": ["paper/draft.md"],
            "required_outputs": ["paper/draft.md"],
            "owner_receipt_refs": ["receipts/owner.json"],
            "decision_receipt_refs": ["receipts/decision.json"],
            "typed_blocker_refs": [],
            "promotion": {
                "state": "current_pointer_promoted",
                "pointer_stage_matches": True,
                "pointer_attempt_matches": True,
                "pointer_terminal_status": "success",
                "latest_attempt_id": "attempt-002",
                "missing_outputs": [],
            },
            "semantic_validation": {
                "status": "accepted",
                "owner_receipt_refs": ["receipts/owner.json"],
                "decision_receipt_refs": ["receipts/decision.json"],
                "typed_blocker_refs": [],
            },
            "consumability": {"status": "passed", "failed_checks": []},
            "lineage": {"status": "observed"},
            "retention": {"status": "covered"},
        }
    )

    assert audit["status"] == "promotable_current"
    assert audit["fail_closed"] is False
    assert audit["fail_closed_reasons"] == []
    assert audit["current_pointer"]["terminal_status"] == "success"
    assert audit["authority_boundary"] == {
        "read_only": True,
        "writes_current_pointer": False,
        "writes_mas_truth": False,
        "writes_paper_or_eval": False,
        "writes_controller_decisions": False,
        "can_authorize_artifact_mutation": False,
        "can_authorize_publication_ready": False,
    }


def test_stage_projection_audit_fails_closed_for_stale_pointer_partial_commit_and_rollback() -> None:
    audit = promotion_audit_from_stage_projection(
        {
            "stage_id": "06-manuscript_authoring",
            "status": "observed",
            "latest_attempt_id": "attempt-003",
            "current_outputs": ["paper/draft.md"],
            "required_outputs": ["paper/draft.md", "paper/tables.md"],
            "owner_receipt_refs": [],
            "decision_receipt_refs": [],
            "typed_blocker_refs": [],
            "promotion": {
                "state": "current_pointer_stale",
                "pointer_stage_matches": True,
                "pointer_attempt_matches": False,
                "pointer_terminal_status": "running",
                "latest_attempt_id": "attempt-003",
                "missing_outputs": ["paper/tables.md"],
            },
            "semantic_validation": {
                "status": "missing_domain_receipt",
                "missing": ["owner_receipt_refs", "domain_decision_receipt_refs"],
            },
            "consumability": {
                "status": "blocked",
                "failed_checks": ["current_truth", "receipt_authority", "domain_validation"],
            },
            "lineage": {"status": "observed"},
            "retention": {"status": "covered"},
        }
    )

    assert audit["status"] == "blocked"
    assert audit["fail_closed"] is True
    assert set(audit["fail_closed_reasons"]) >= {
        "current_pointer_stale",
        "current_pointer_invalid_status",
        "partial_commit",
        "receipt_required",
        "missing_domain_receipt",
        "rollback_candidate",
    }
    assert audit["current_pointer"]["terminal_status"] == "running"
    assert audit["latest_pointer"]["attempt_id"] == "attempt-003"


def test_deliverable_root_audit_reports_orphan_output_and_historical_pointer_tombstone(
    tmp_path: Path,
) -> None:
    deliverable_root = tmp_path / "deliverable"
    attempt_root = deliverable_root / "stages" / "06-manuscript_authoring" / "attempts" / "attempt-002"
    orphan_root = deliverable_root / "stages" / "06-manuscript_authoring" / "attempts" / "attempt-003"
    receipt_root = attempt_root / "receipts"
    tombstone_root = deliverable_root / "tombstones"
    receipt_root.mkdir(parents=True)
    orphan_root.mkdir(parents=True)
    tombstone_root.mkdir(parents=True)
    _write_json(
        deliverable_root / "current.json",
        {
            "current_stage": {
                "stage_id": "06-manuscript_authoring",
                "latest_attempt_id": "attempt-001",
                "status": "success",
            }
        },
    )
    (attempt_root.parent.parent / "latest").write_text("attempt-002", encoding="utf-8")
    _write_json(
        attempt_root / "manifest.json",
        {
            "required_outputs": ["paper/draft.md"],
            "present_outputs": ["paper/draft.md"],
            "owner_receipt_refs": ["receipts/owner.json"],
            "decision_receipt_refs": ["receipts/decision.json"],
            "output_hashes": [{"path": "paper/draft.md", "sha256": "a" * 64}],
            "restore_refs": ["restore/proof.json"],
        },
    )
    _write_json(receipt_root / "owner.json", {"status": "accepted"})
    _write_json(orphan_root / "manifest.json", {"present_outputs": ["paper/newer.md"]})
    _write_json(
        tombstone_root / "current-pointer-attempt-001.json",
        {
            "surface_kind": "historical_current_pointer_tombstone",
            "stage_id": "06-manuscript_authoring",
            "attempt_id": "attempt-001",
        },
    )

    audit = promotion_audit_from_deliverable_root(
        deliverable_root=deliverable_root,
        stage_id="06-manuscript_authoring",
    )

    assert audit["status"] == "blocked"
    assert set(audit["fail_closed_reasons"]) >= {
        "current_pointer_stale",
        "orphan_output",
        "historical_pointer_tombstone",
    }
    assert audit["current_pointer"]["attempt_id"] == "attempt-001"
    assert audit["latest_pointer"]["attempt_id"] == "attempt-002"
    assert audit["orphan_outputs"][0]["attempt_id"] == "attempt-003"
    assert audit["historical_pointer_tombstones"][0]["attempt_id"] == "attempt-001"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
