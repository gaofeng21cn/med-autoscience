from __future__ import annotations

from med_autoscience.controllers.opl_state_index_kernel import (
    ALLOWED_PAYLOAD_ROLES,
    FORBIDDEN_PAYLOAD_ROLES,
    build_state_index_kernel_rows,
    rebuild_state_index_kernel_report,
)


def _stage_artifact_index() -> dict[str, object]:
    return {
        "surface_kind": "stage_artifact_index",
        "domain_stage_pack_ref": "contracts/mas-paper-study-stage-pack.json",
        "stage_artifact_runtime_contract_ref": "contracts/opl-framework/stage-artifact-runtime-contract.json",
        "stages": [
            {
                "stage_id": "01-study_intake",
                "stage_folder_contract": {
                    "stage_folder_ref": "/opl/state/stages/01-study_intake",
                    "manifest_ref": "/opl/state/stages/01-study_intake/attempts/a1/manifest.json",
                    "receipt_ref": "/opl/state/stages/01-study_intake/attempts/a1/receipts/owner.json",
                    "current_pointer_ref": "/opl/state/current.json",
                },
                "physical_stage_folder_kernel": {
                    "stage_json_ref": "/opl/state/stages/01-study_intake/stage.json",
                    "attempt_json_ref": "/opl/state/stages/01-study_intake/attempts/a1/attempt.json",
                },
                "artifact_classification": {
                    "current": ["study_truth_snapshot.json"],
                    "manifest_hash_refs": [
                        {
                            "path": "study_truth_snapshot.json",
                            "sha256": "0" * 64,
                            "kind": "output",
                        }
                    ],
                    "receipt_hash_refs": [
                        {
                            "path": "owner.json",
                            "sha256": "1" * 64,
                            "kind": "receipt",
                        }
                    ],
                    "owner_receipt_refs": ["mas-owner-receipt:01-study_intake:a1"],
                    "typed_blocker_refs": ["mas-typed-blocker:source-gap"],
                    "decision_receipt_refs": ["mas-domain-decision:01-study_intake:a1"],
                    "retention": {
                        "restore_refs": ["restore-index:01-study_intake:a1"],
                    },
                },
            }
        ],
    }


def test_state_index_kernel_rows_are_refs_only_and_rebuildable() -> None:
    projection = build_state_index_kernel_rows(stage_artifact_index=_stage_artifact_index())

    assert projection["surface_kind"] == "opl_state_index_kernel_rows_projection"
    assert projection["index_authority"] == "derived_refs_only_rebuildable_read_model"
    assert projection["status"] == "ready_for_opl_sidecar_ingest"
    assert projection["violations"] == []
    assert projection["row_count"] == len(projection["rows"])
    assert all(row["body_included"] is False for row in projection["rows"])
    assert {row["payload_role"] for row in projection["rows"]} <= ALLOWED_PAYLOAD_ROLES
    assert not ({row["payload_role"] for row in projection["rows"]} & FORBIDDEN_PAYLOAD_ROLES)


def test_state_index_kernel_projects_expected_ref_families() -> None:
    projection = build_state_index_kernel_rows(stage_artifact_index=_stage_artifact_index())
    families = {row["row_family"] for row in projection["rows"]}

    assert {
        "stage_folder",
        "artifact",
        "artifact_hash",
        "receipt_hash",
        "owner_receipt",
        "typed_blocker",
        "decision_receipt",
        "restore",
    } <= families
    assert any(row["row_key"] == "current_pointer_ref" for row in projection["rows"])


def test_state_index_kernel_rebuild_report_diffs_previous_rows() -> None:
    previous = [
        {
            "stage_id": "01-study_intake",
            "row_family": "stage_folder",
            "row_key": "stale",
            "ref": "old-ref",
        }
    ]

    report = rebuild_state_index_kernel_report(
        stage_artifact_index=_stage_artifact_index(),
        previous_rows=previous,
    )

    assert report["surface_kind"] == "opl_state_index_kernel_rebuild_report"
    assert report["derived_index_rebuildable"] is True
    assert "01-study_intake|stage_folder|stale|old-ref" in report["removed_row_keys"]
    assert report["added_row_keys"]
    assert report["rows_projection"]["status"] == "ready_for_opl_sidecar_ingest"


def test_state_index_kernel_never_allows_domain_body_roles() -> None:
    assert {
        "study_truth_body",
        "publication_eval_body",
        "controller_decision_body",
        "manuscript_body",
        "paper_package_body",
        "memory_body",
        "artifact_body",
        "publication_quality_verdict_body",
        "owner_receipt_authority",
    } <= FORBIDDEN_PAYLOAD_ROLES
