from __future__ import annotations

import importlib

from med_autoscience.controllers.next_action_envelope import SURFACE_KIND


def test_stage_closure_owner_receipt_suppresses_same_work_unit_domain_transition() -> None:
    materialized_readback = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_command_parts.materialized_mission_readback"
    )
    same_work_unit_next_action = {
        "surface_kind": SURFACE_KIND,
        "action_type": "request_opl_stage_attempt",
        "action_family": "paper.review.ai_reviewer",
        "stage_id": "review",
        "work_unit_id": "ai_reviewer_medical_prose_quality_review",
        "owner": "ai_reviewer",
    }
    stage_closure_decision = {
        "stage_id": "review",
        "work_unit_id": "ai_reviewer_medical_prose_quality_review",
        "outcome": {
            "kind": "owner_receipt",
            "package_kind": "current_package",
            "can_submit": False,
        },
    }

    assert materialized_readback._stage_closure_suppresses_domain_transition_next_action(
        stage_closure_decision=stage_closure_decision,
        next_action=None,
        domain_transition_next_action=same_work_unit_next_action,
    )
    assert materialized_readback._stage_closure_suppresses_domain_transition_next_action(
        stage_closure_decision=stage_closure_decision,
        next_action={
            "surface_kind": SURFACE_KIND,
            "action_family": "paper.package.submission_minimal",
            "work_unit_id": "submission_authority_owner_verdict",
        },
        domain_transition_next_action=same_work_unit_next_action,
    )
    assert not materialized_readback._stage_closure_suppresses_domain_transition_next_action(
        stage_closure_decision=stage_closure_decision,
        next_action={
            "surface_kind": SURFACE_KIND,
            "action_family": "paper.stage_closure.owner_consumption",
            "work_unit_id": "ai_reviewer_medical_prose_quality_review",
        },
        domain_transition_next_action=same_work_unit_next_action,
    )
    assert not materialized_readback._stage_closure_suppresses_domain_transition_next_action(
        stage_closure_decision=stage_closure_decision,
        next_action=None,
        domain_transition_next_action={
            **same_work_unit_next_action,
            "work_unit_id": "submission_package_finalize",
        },
    )
    assert not materialized_readback._stage_closure_suppresses_domain_transition_next_action(
        stage_closure_decision={
            **stage_closure_decision,
            "outcome": {
                "kind": "owner_receipt",
                "package_kind": "submission_ready_package",
                "can_submit": True,
            },
        },
        next_action=None,
        domain_transition_next_action=same_work_unit_next_action,
    )
