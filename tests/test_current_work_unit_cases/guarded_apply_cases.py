from __future__ import annotations

import importlib

from tests.test_current_work_unit_cases.shared import _assert_contract_shape, _module


def _guarded_apply_current_owner_delta(**overrides: object) -> dict[str, object]:
    contract = importlib.import_module(
        "med_autoscience.controllers.guarded_apply_owner_delta_contract"
    ).guarded_apply_current_owner_delta_contract()
    return {**contract, "lineage_ref": "sat-current-guarded-apply", **overrides}


def test_current_work_unit_projects_guarded_apply_owner_answer_missing_as_unique_action() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-cvd-mortality-risk",
            "quest_id": "002-dm-cvd-mortality-risk",
            "current_stage": "paper_autonomy/guarded-apply",
            "stage_kernel_projection": {
                "current_owner_delta": _guarded_apply_current_owner_delta(),
            },
        },
        actions=[
            {
                "source_surface": "action_queue",
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "next_work_unit": "stale_ai_reviewer_recheck",
                "work_unit_id": "stale_ai_reviewer_recheck",
            }
        ],
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "med-autoscience"
    assert work_unit["action_type"] == "paper_autonomy/guarded-apply"
    assert work_unit["work_unit_id"] == "domain_owner_receipt_quality_gate_or_typed_blocker_required"
    assert work_unit["work_unit_fingerprint"] == "sat-current-guarded-apply"
    assert work_unit["state"]["owner_answer_missing"] is True
    assert work_unit["state"]["owner_answer_still_required"] is True
    assert work_unit["required_output_contract"]["accepted_return_shape"] == [
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]


def test_current_work_unit_blocks_invalid_guarded_apply_owner_delta_identity() -> None:
    module = _module()

    invalid_delta = _guarded_apply_current_owner_delta(
        lineage_ref=None,
        accepted_answer_shape=[
            "domain_owner_receipt_ref",
            "quality_gate_receipt_ref",
            "typed_blocker_ref",
        ],
        accepted_return_shapes=[
            "domain_owner_receipt_ref",
            "quality_gate_receipt_ref",
            "typed_blocker_ref",
        ],
        domain_ready_authorized=True,
    )
    invalid_delta.pop("lineage_ref", None)
    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-cvd-mortality-risk",
            "quest_id": "002-dm-cvd-mortality-risk",
            "current_stage": "paper_autonomy/guarded-apply",
            "stage_kernel_projection": {"current_owner_delta": invalid_delta},
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "blocked_current_work_unit"
    assert work_unit["state"]["typed_blocker"]["blocker_id"] == "current_owner_delta_identity_missing_or_invalid"
    assert set(work_unit["state"]["typed_blocker"]["missing_required_fields"]) == {
        "lineage_ref",
        "domain_ready_authorized_false",
        "accepted_answer_shape.human_gate_ref",
        "accepted_answer_shape.route_back_evidence_ref",
    }
    assert work_unit["work_unit_id"] == "domain_owner_receipt_quality_gate_or_typed_blocker_required"


def test_current_work_unit_blocks_guarded_apply_delta_with_existing_owner_answer_ref() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-cvd-mortality-risk",
            "quest_id": "002-dm-cvd-mortality-risk",
            "current_stage": "paper_autonomy/guarded-apply",
            "stage_kernel_projection": {
                "current_owner_delta": _guarded_apply_current_owner_delta(
                    latest_owner_answer_ref="mas://owner-answer/already-recorded"
                ),
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "blocked_current_work_unit"
    assert work_unit["state"]["typed_blocker"]["blocker_id"] == "current_owner_delta_identity_missing_or_invalid"
    assert work_unit["state"]["typed_blocker"]["missing_required_fields"] == [
        "latest_owner_answer_ref_must_be_null"
    ]


def test_current_work_unit_owner_answer_missing_rejects_unbound_running_provider_proof() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-cvd-mortality-risk",
            "quest_id": "002-dm-cvd-mortality-risk",
            "current_stage": "paper_autonomy/guarded-apply",
            "stage_kernel_projection": {
                "current_owner_delta": _guarded_apply_current_owner_delta(),
            },
        },
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-current-guarded-apply",
            "active_stage_attempt_id": "sat-current-guarded-apply",
            "active_workflow_id": "wf-current-guarded-apply",
            "stage_id": "paper_autonomy/guarded-apply",
            "lineage_ref": "sat-current-guarded-apply",
            "work_unit_id": "domain_owner_receipt_quality_gate_or_typed_blocker_required",
            "work_unit_fingerprint": "sat-current-guarded-apply",
            "action_type": "paper_autonomy/guarded-apply",
            "route_back_evidence_ref": "opl://not-a-mas-owner-answer",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
                "lineage_ref": "sat-current-guarded-apply",
                "work_unit_id": "domain_owner_receipt_quality_gate_or_typed_blocker_required",
                "work_unit_fingerprint": "sat-current-guarded-apply",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["state"]["owner_answer_missing"] is True
    assert work_unit["status"] != "running_provider_attempt"
