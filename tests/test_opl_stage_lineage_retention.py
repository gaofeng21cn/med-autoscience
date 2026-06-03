from __future__ import annotations

from med_autoscience.controllers.opl_stage_lineage_retention import (
    stage_lineage_retention_drilldown,
)


def test_lineage_retention_drilldown_unifies_stage_projection_event_families() -> None:
    stage_projection = {
        "stage_id": "01-study_intake",
        "latest_attempt_id": "attempt-001",
        "manifest_ref": "stage/attempts/attempt-001/manifest.json",
        "receipt_ref": "stage/attempts/attempt-001/receipts/owner.json",
        "current_pointer_ref": "deliverable/current.json",
        "current_outputs": ["study_truth_snapshot.json"],
        "required_outputs": ["study_truth_snapshot.json"],
        "manifest_hash_refs": [
            {"path": "study_truth_snapshot.json", "sha256": "0" * 64},
        ],
        "owner_receipt_refs": ["mas-owner-receipt:01-study_intake:attempt-001"],
        "restore_refs": ["restore-proof:01-study_intake:attempt-001"],
        "retention_refs": ["retention-ledger:01-study_intake:attempt-001"],
        "lineage": {
            "lineage_events_ref": "lineage/events.jsonl",
            "lineage_graph_ref": "lineage/graph.json",
            "missing": [],
        },
        "promotion": {
            "state": "current_pointer_promoted",
            "pointer_ref": "deliverable/current.json",
        },
        "current_pointer": {
            "artifact_refs": ["study_truth_snapshot.json"],
        },
    }

    drilldown = stage_lineage_retention_drilldown(stage_projection=stage_projection)

    assert drilldown["surface_kind"] == "opl_stage_lineage_retention_drilldown"
    assert drilldown["status"] == "ready"
    assert drilldown["read_only"] is True
    assert drilldown["cleanup_authorized"] is False
    assert drilldown["body_included"] is False
    assert drilldown["unified_event_model"] == "stage_attempt_manifest_receipt_current_pointer"
    assert drilldown["event_families"] == {
        "lineage_events": {
            "status": "observed",
            "refs": ["lineage/events.jsonl"],
            "missing": [],
            "body_included": False,
        },
        "lineage_graph": {
            "status": "observed",
            "refs": ["lineage/graph.json"],
            "missing": [],
            "body_included": False,
        },
        "manifest": {
            "status": "observed",
            "refs": ["stage/attempts/attempt-001/manifest.json"],
            "missing": [],
            "body_included": False,
        },
        "receipt": {
            "status": "observed",
            "refs": [
                "stage/attempts/attempt-001/receipts/owner.json",
                "mas-owner-receipt:01-study_intake:attempt-001",
            ],
            "missing": [],
            "body_included": False,
        },
        "current_pointer": {
            "status": "observed",
            "refs": ["deliverable/current.json"],
            "missing": [],
            "body_included": False,
        },
        "restore_proof": {
            "status": "observed",
            "refs": ["restore-proof:01-study_intake:attempt-001"],
            "missing": [],
            "body_included": False,
        },
        "retention_policy": {
            "status": "observed",
            "refs": ["retention-ledger:01-study_intake:attempt-001"],
            "missing": [],
            "body_included": False,
        },
    }
    assert drilldown["retention_restore_gate"] == {
        "surface_kind": "opl_stage_retention_restore_gate",
        "status": "passed",
        "failed_checks": [],
        "restore_contract_required_before_cleanup": True,
        "cleanup_authorized": False,
        "cleanup_authorized_by_projection": False,
        "current_pointer_to_orphan_artifact_forbidden": True,
        "orphan_current_pointer_artifact_refs": [],
        "body_included": False,
    }


def test_lineage_retention_drilldown_fails_closed_for_missing_refs_restore_and_orphan_pointer() -> None:
    drilldown = stage_lineage_retention_drilldown(
        refs={
            "stage_id": "01-study_intake",
            "current_pointer_ref": "deliverable/current.json",
            "current_pointer_artifact_refs": ["orphan-output.json"],
            "manifest_artifact_refs": ["study_truth_snapshot.json"],
            "cleanup_requested": True,
        }
    )

    assert drilldown["status"] == "blocked"
    assert drilldown["cleanup_authorized"] is False
    assert drilldown["event_families"]["lineage_events"]["missing"] == ["lineage_events_ref"]
    assert drilldown["event_families"]["lineage_graph"]["missing"] == ["lineage_graph_ref"]
    assert drilldown["event_families"]["manifest"]["missing"] == ["manifest_ref"]
    assert drilldown["event_families"]["receipt"]["missing"] == ["receipt_ref", "owner_receipt_refs"]
    assert drilldown["event_families"]["current_pointer"]["status"] == "observed"
    assert drilldown["event_families"]["restore_proof"]["missing"] == ["restore_proof_refs"]
    assert drilldown["retention_restore_gate"]["status"] == "blocked"
    assert drilldown["retention_restore_gate"]["failed_checks"] == [
        "lineage_events_ref",
        "lineage_graph_ref",
        "manifest_ref",
        "receipt_ref",
        "owner_receipt_refs",
        "restore_proof_refs",
        "retention_refs",
        "cleanup_not_authorized_by_projection",
        "current_pointer_to_orphan_artifact_forbidden",
    ]
    assert drilldown["retention_restore_gate"]["orphan_current_pointer_artifact_refs"] == [
        "orphan-output.json",
    ]
