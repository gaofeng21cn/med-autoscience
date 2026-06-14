from __future__ import annotations

from tests.test_current_work_unit_cases.shared import _assert_contract_shape, _module


def test_current_work_unit_uses_progress_first_embedded_actionable_gate_followthrough() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )

    embedded_action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "next_owner": "write",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        "action_fingerprint": "publication-blockers::0915410f804b3697",
        "source_eval_id": source_eval_id,
        "owner_route_currentness_basis": {
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "source_eval_id": source_eval_id,
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "explicit_publication_work_unit_id": "medical_prose_write_repair",
        },
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "owner_receipt_required": True,
        "target_surface": {
            "ref_kind": "publication_work_unit",
            "route_target": "write",
            "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
        },
        "acceptance_refs": [
            f"/workspace/studies/{study_id}/artifacts/controller/gate_clearing_batch/latest.json"
        ],
    }

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "progress_first_monitoring_summary": {
                "current_executable_owner_action": embedded_action,
            },
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": source_eval_id,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "medical_prose_write_repair",
                    "selected_publication_work_unit_id": "medical_prose_write_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "explicit_work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "current_work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "explicit_work_unit_fingerprint_matches_current": True,
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                    "summary": "Repair structured medical reporting and manuscript voice.",
                },
                "gate_replay_status": "blocked",
                "gate_replay_blockers": [
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                ],
                "latest_record_path": (
                    f"/workspace/studies/{study_id}/artifacts/controller/"
                    "gate_clearing_batch/latest.json"
                ),
            },
        },
        typed_blocker={
            "surface_kind": "mas_typed_blocker",
            "blocker_id": "publication_gate_replay_blocked",
            "blocker_type": "publication_gate_replay_blocked",
            "blocked_reason": "publication_gate_replay_blocked",
            "owner": "publication_gate",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
            "source_ref": (
                f"/workspace/studies/{study_id}/artifacts/supervision/consumer/"
                "default_executor_execution/sat_d2b4c700b31294ab17c225d4.closeout.json"
            ),
        },
        next_owner="publication_gate",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "medical_prose_write_repair"
    assert work_unit["work_unit_fingerprint"] == "publication-blockers::0915410f804b3697"
    assert work_unit["state"]["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"
