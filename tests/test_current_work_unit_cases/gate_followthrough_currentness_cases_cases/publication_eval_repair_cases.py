from __future__ import annotations

from tests.test_current_work_unit_cases.shared import _assert_contract_shape, _module


def test_current_work_unit_publication_eval_repair_supersedes_publication_gate_replay_blocker() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    closeout_ref = (
        f"/workspace/studies/{study_id}/artifacts/supervision/consumer/"
        "default_executor_execution/sat_d2b4c700b31294ab17c225d4.closeout.json"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "publication_eval": {
                "eval_id": "publication-eval::003::post-gate-blocked",
                "recommended_actions": [
                    {
                        "action_type": "route_back_same_line",
                        "priority": "now",
                        "route_target": "write",
                        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                        "next_work_unit": {
                            "unit_id": "medical_prose_write_repair",
                            "lane": "write",
                        },
                    }
                ],
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "publication_eval.recommended_actions.readiness_blocker_repair",
            "next_owner": "write",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "action_fingerprint": "publication-blockers::0915410f804b3697",
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "publication_eval_recommended_repair_delta_or_typed_blocker",
            "target_surface": {
                "ref_kind": "publication_eval_recommended_action",
                "route_target": "write",
                "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "next_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
            },
            "target_surface_specificity": "publication_eval_readiness_blocker_derived_repair",
        },
        typed_blocker={
            "surface_kind": "mas_typed_blocker",
            "blocker_id": "publication_gate_replay_blocked",
            "blocker_type": "publication_gate_replay_blocked",
            "blocked_reason": "publication_gate_replay_blocked",
            "owner": "publication_gate",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": "sha256:gate-replay",
            "source_ref": closeout_ref,
        },
        next_owner="publication_gate",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "medical_prose_write_repair"
    assert work_unit["work_unit_fingerprint"] == "publication-blockers::0915410f804b3697"
    assert work_unit["state"]["source"] == "publication_eval.recommended_actions.readiness_blocker_repair"
