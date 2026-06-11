from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers.study_transition_receipt_consumption import (
    default_executor_execution_nonconsumable_closeout,
    default_executor_execution_receipt_consumption,
    mas_owner_apply_receipt_consumption,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_default_executor_consumes_accepted_paper_story_repair_owner_receipt(
    tmp_path: Path,
) -> None:
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = tmp_path / "studies" / study_id
    fingerprint = (
        "stage-native-next-action::08-publication_package_handoff::"
        "run_quality_repair_batch::artifacts/reports/medical_publication_surface/latest.json"
    )
    owner_route = {
        "idempotency_key": f"owner-route::{study_id}::stage-native-write-repair",
        "route_epoch": f"stage-native-next-action::{study_id}::08-publication_package_handoff",
        "truth_epoch": f"stage-native-next-action::{study_id}::08-publication_package_handoff",
        "runtime_health_epoch": f"stage-native-next-action::{study_id}::08-publication_package_handoff",
        "work_unit_fingerprint": fingerprint,
        "next_owner": "write",
        "allowed_actions": ["run_quality_repair_batch"],
        "source_refs": {
            "owner_route_currentness_basis": {
                "truth_epoch": f"stage-native-next-action::{study_id}::08-publication_package_handoff",
                "runtime_health_epoch": f"stage-native-next-action::{study_id}::08-publication_package_handoff",
                "work_unit_fingerprint": fingerprint,
                "work_unit_id": "run_quality_repair_batch",
            }
        },
    }
    draft_ref = str(study_root / "paper" / "draft.md")
    review_ref = str(study_root / "paper" / "build" / "review_manuscript.md")
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_id,
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "executed",
                    "execution_id": f"execution::{study_id}::run_quality_repair_batch::accepted-story-repair",
                    "idempotency_key": owner_route["idempotency_key"],
                    "current_owner_route": owner_route,
                    "prompt_contract": {"owner_route": owner_route},
                    "owner_result": {
                        "status": "progress_delta_candidate",
                        "receipt": {
                            "surface": "paper_story_repair_owner_receipt",
                            "accepted": True,
                            "execution_status": "progress_delta_candidate",
                            "direct_current_package_write": False,
                            "quality_authorized": False,
                            "submission_authorized": False,
                            "canonical_artifact_delta_refs": [
                                {"path": draft_ref, "artifact_role": "canonical_manuscript_story_surface"},
                                {"path": review_ref, "artifact_role": "canonical_manuscript_story_surface"},
                            ],
                            "repair_execution_evidence_ref": (
                                "artifacts/controller/repair_execution_evidence/latest.json"
                            ),
                        },
                        "repair_execution_evidence": {
                            "status": "progress_delta_candidate",
                            "progress_delta_candidate": True,
                            "canonical_artifact_delta": {"meaningful_artifact_delta": True},
                            "changed_artifact_refs": [
                                {"path": draft_ref, "artifact_role": "canonical_manuscript_story_surface"},
                                {"path": review_ref, "artifact_role": "canonical_manuscript_story_surface"},
                            ],
                        },
                        "quality_authorized": False,
                        "submission_authorized": False,
                        "current_package_write_authorized": False,
                    },
                }
            ],
        },
    )

    receipt = default_executor_execution_receipt_consumption(
        study_root=study_root,
        owner_route=owner_route,
        actions=[{"action_type": "run_quality_repair_batch"}],
    )

    assert receipt["status"] == "consumed"
    assert receipt["receipt_kind"] == "default_executor_execution"
    assert receipt["receipt_ref"] == "artifacts/supervision/consumer/default_executor_execution/latest.json"
    assert receipt["execution_id"].endswith("accepted-story-repair")
    assert receipt["owner_result_status"] == "progress_delta_candidate"
    assert receipt["repair_execution_evidence_status"] == "progress_delta_candidate"
    assert receipt["changed_artifact_ref_count"] == 2
    assert receipt["next_action"] == "do_not_redrive_consumed_owner_route"
    assert receipt["quality_authorized"] is False
    assert receipt["submission_authorized"] is False
    assert receipt["current_package_write_authorized"] is False
    assert (
        default_executor_execution_nonconsumable_closeout(
            study_root=study_root,
            owner_route=owner_route,
            actions=[{"action_type": "run_quality_repair_batch"}],
        )
        == {}
    )


def test_consumes_live_paper_story_repair_owner_receipt_from_controller_surface(
    tmp_path: Path,
) -> None:
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = tmp_path / "studies" / study_id
    draft_ref = str(study_root / "paper" / "draft.md")
    review_ref = str(study_root / "paper" / "build" / "review_manuscript.md")
    receipt_ref = study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json"
    evidence_ref = study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
    _write_json(
        receipt_ref,
        {
            "surface": "paper_story_repair_owner_receipt",
            "accepted": True,
            "execution_status": "progress_delta_candidate",
            "direct_current_package_write": False,
            "quality_authorized": False,
            "submission_authorized": False,
            "canonical_artifact_delta_refs": [
                {"path": draft_ref, "artifact_role": "canonical_manuscript_story_surface"},
                {"path": review_ref, "artifact_role": "canonical_manuscript_story_surface"},
            ],
        },
    )
    _write_json(
        evidence_ref,
        {
            "status": "progress_delta_candidate",
            "progress_delta_candidate": True,
            "canonical_artifact_delta": {
                "status": "fresh",
                "meaningful_artifact_delta": True,
                "changed_artifact_ref_count": 2,
                "artifact_refs": [
                    {"path": draft_ref, "artifact_role": "canonical_manuscript_story_surface"},
                    {"path": review_ref, "artifact_role": "canonical_manuscript_story_surface"},
                ],
            },
        },
    )

    receipt = mas_owner_apply_receipt_consumption(study_root=study_root)

    assert receipt["status"] == "consumed"
    assert receipt["receipt_kind"] == "mas_owner_apply_receipt"
    assert receipt["apply_result"] == "artifact_delta"
    assert receipt["receipt_surface"] == "paper_story_repair_owner_receipt"
    assert receipt["receipt_execution_status"] == "progress_delta_candidate"
    assert receipt["story_surface_delta_ref_count"] == 2
    assert receipt["quality_authorized"] is False
    assert receipt["submission_authorized"] is False
    assert receipt["current_package_write_authorized"] is False
    assert receipt["next_action"] == "honor_paper_story_repair_owner_receipt"


def test_rejects_paper_story_repair_owner_receipt_without_story_surface_refs(
    tmp_path: Path,
) -> None:
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = tmp_path / "studies" / study_id
    claim_map_ref = str(study_root / "paper" / "claim_evidence_map.json")
    evidence_ref = str(study_root / "paper" / "evidence_ledger.json")
    _write_json(
        study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json",
        {
            "surface": "paper_story_repair_owner_receipt",
            "accepted": True,
            "execution_status": "progress_delta_candidate",
            "direct_current_package_write": False,
            "quality_authorized": False,
            "submission_authorized": False,
            "canonical_artifact_delta_refs": [
                {"path": claim_map_ref, "artifact_role": "claim_evidence_map"},
                {"path": evidence_ref, "artifact_role": "evidence_ledger"},
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json",
        {
            "status": "progress_delta_candidate",
            "progress_delta_candidate": True,
            "canonical_artifact_delta": {
                "status": "fresh",
                "meaningful_artifact_delta": True,
                "artifact_refs": [
                    {"path": claim_map_ref, "artifact_role": "claim_evidence_map"},
                    {"path": evidence_ref, "artifact_role": "evidence_ledger"},
                ],
            },
        },
    )

    assert mas_owner_apply_receipt_consumption(study_root=study_root) == {}
