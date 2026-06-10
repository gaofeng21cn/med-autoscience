from __future__ import annotations

import importlib
from collections.abc import Mapping
from typing import Any


REQUIRED_KEYS = {
    "surface_kind",
    "schema_version",
    "status",
    "study_id",
    "quest_id",
    "stage_id",
    "owner",
    "action_type",
    "work_unit_id",
    "work_unit_fingerprint",
    "action_fingerprint",
    "input_refs",
    "required_output_contract",
    "acceptance_refs",
    "state",
    "currentness_basis",
    "authority_boundary",
}


def _module():
    return importlib.import_module("med_autoscience.controllers.current_work_unit")


def _assert_contract_shape(work_unit: Mapping[str, Any]) -> None:
    assert set(work_unit) == REQUIRED_KEYS
    assert work_unit["surface_kind"] == "current_work_unit"
    assert work_unit["schema_version"] == 1
    assert work_unit["status"] in {
        "executable_owner_action",
        "running_provider_attempt",
        "typed_blocker",
        "blocked_current_work_unit",
    }
    assert work_unit["authority_boundary"]["top_level_truth"] == "status"
    assert work_unit["authority_boundary"]["mas_owner_authority_preserved"] is True
    assert work_unit["authority_boundary"]["stage_transition_authority"] == "OPL Stage Transition Authority"
    assert work_unit["authority_boundary"]["stage_authority_role"] == (
        "non_authoritative_observation_and_intent_producer"
    )
    assert work_unit["authority_boundary"]["can_write_stage_current_pointer"] is False
    assert work_unit["authority_boundary"]["can_write_current_owner_delta"] is False
    assert work_unit["authority_boundary"]["can_write_stage_terminal_state"] is False


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


def test_current_work_unit_projects_repair_progress_ai_reviewer_followup() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-cvd-mortality-risk",
            "quest_id": "002-dm-cvd-mortality-risk",
            "current_stage": "publication_supervision",
            "paper_progress_delta": {"count": 1},
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": "artifacts/stage_outputs/08/receipts/typed_blocker.json",
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {"state": "domain_owner_answer_recorded"},
                }
            },
        },
        actions=[
            {
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "next_owner": "ai_reviewer",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "study-progress-current-owner-ticket::002::ai-reviewer",
                "action_fingerprint": "study-progress-current-owner-ticket::002::ai-reviewer",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
                "acceptance_refs": ["artifacts/supervision/requests/ai_reviewer/latest.json"],
            }
        ],
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "ai_reviewer"
    assert work_unit["action_type"] == "return_to_ai_reviewer_workflow"
    assert work_unit["work_unit_id"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert work_unit["state"]["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert work_unit["currentness_basis"]["work_unit_fingerprint"] == (
        "study-progress-current-owner-ticket::002::ai-reviewer"
    )


def test_current_work_unit_projects_live_repair_progress_precedence_over_stage_readiness_blocker() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "queued",
            "paper_stage": "publishability_gate_blocked",
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
                    ),
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {
                        "state": "domain_owner_answer_recorded",
                        "owner_answer_kind": "typed_blocker",
                    },
                }
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "next_owner": "ai_reviewer",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "work_unit_fingerprint": "sha256:repair-progress-current",
            "action_fingerprint": "sha256:repair-progress-current",
            "action_type": "return_to_ai_reviewer_workflow",
            "allowed_actions": ["return_to_ai_reviewer_workflow"],
            "owner_receipt_required": True,
            "required_delta_kind": "ai_reviewer_publication_eval_delta_or_typed_blocker",
            "source_ref": "artifacts/controller/repair_execution_evidence/latest.json",
            "acceptance_refs": [
                "artifacts/controller/repair_execution_evidence/latest.json",
                "artifacts/controller/repair_execution_receipts/latest.json",
                "artifacts/supervision/requests/ai_reviewer/latest.json",
            ],
            "repair_progress_precedence": {
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "superseded_stage_native_action": "run_quality_repair_batch",
                "superseded_readiness_action": "complete_medical_paper_readiness_surface",
                "source_work_unit_id": "analysis_claim_evidence_repair",
                "source_fingerprint": "sha256:repair-progress-current",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "ai_reviewer"
    assert work_unit["action_type"] == "return_to_ai_reviewer_workflow"
    assert work_unit["work_unit_id"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert work_unit["state"]["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert work_unit["state"]["state_kind"] == "executable_owner_action"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_suppresses_consumed_current_owner_action_receipt() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
            "dispatch_consumption": {
                "consumption_status": "consumed",
                "receipt_ref": "artifacts/publication_eval/ai_reviewer_responses/current.json",
                "receipt_kind": "ai_reviewer_publication_eval",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "sha256:consumed-ai-reviewer",
                "canonical_work_unit_identity": {
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "work_unit_fingerprint": "sha256:consumed-ai-reviewer",
                },
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "next_owner": "ai_reviewer",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "work_unit_fingerprint": "sha256:consumed-ai-reviewer",
            "action_fingerprint": "sha256:consumed-ai-reviewer",
            "action_type": "return_to_ai_reviewer_workflow",
            "allowed_actions": ["return_to_ai_reviewer_workflow"],
        },
        next_owner="ai_reviewer",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "blocked_current_work_unit"
    assert work_unit["action_type"] is None
    assert work_unit["work_unit_id"] is None
    assert work_unit["state"]["blocker_type"] == "current_work_unit_unresolved"


def test_current_work_unit_suppresses_consumed_action_using_progress_current_action_identity() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "sha256:consumed-ai-reviewer",
                "action_fingerprint": "sha256:consumed-ai-reviewer",
            },
            "dispatch_consumption": {
                "consumption_status": "consumed",
                "receipt_ref": "artifacts/publication_eval/ai_reviewer_responses/current.json",
                "receipt_kind": "ai_reviewer_publication_eval",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "sha256:consumed-ai-reviewer",
                "canonical_work_unit_identity": {
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "work_unit_fingerprint": "sha256:consumed-ai-reviewer",
                },
            },
        },
        actions=[
            {
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            }
        ],
        next_owner="ai_reviewer",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "blocked_current_work_unit"
    assert work_unit["action_type"] is None
    assert work_unit["work_unit_id"] is None


def test_current_work_unit_preserves_readiness_blocker_over_next_forced_delta_without_paper_delta() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {"state": "domain_owner_answer_recorded"},
                }
            },
        },
        actions=[
            {
                "source": "study_progress.next_forced_delta.owner_action",
                "next_owner": "write",
                "work_unit_id": "manuscript_story_repair",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "write",
                    "surface_ref": "canonical manuscript story-surface delta or typed blocker:manuscript_story_surface_delta_missing",
                },
            }
        ],
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "MedAutoScience"
    assert work_unit["action_type"] == "complete_medical_paper_readiness_surface"
    assert work_unit["state"]["source"] == "stage_owner_answer"
    assert work_unit["state"]["typed_blocker"]["blocker_type"] == "medical_paper_readiness_missing"


def test_current_work_unit_projects_gate_consumption_action_over_stage_readiness_blocker() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {"state": "domain_owner_answer_recorded"},
                }
            },
        },
        actions=[
            {
                "source": "study_progress.next_forced_delta.owner_action",
                "next_owner": "write",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "action_type": "run_gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "write",
                    "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                },
            }
        ],
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == "ai_reviewer_record_gate_consumption"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_projects_gate_consumption_action_over_opl_authorization_residue_after_paper_delta() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "owner_action": {
                    "next_owner": "gate_clearing_batch",
                    "work_unit_id": "ai_reviewer_record_gate_consumption",
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
            },
        },
        actions=[
            {
                "source": "study_progress.next_forced_delta.owner_action",
                "next_owner": "gate_clearing_batch",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "action_type": "run_gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "gate_clearing_batch",
                    "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                },
            }
        ],
        typed_blocker={
            "blocker_type": "opl_execution_authorization_required",
            "owner": "write",
        },
        next_owner="write",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "gate_clearing_batch"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == "ai_reviewer_record_gate_consumption"
    assert work_unit["state"]["source"] == "study_progress.next_forced_delta.owner_action"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_projects_next_forced_story_repair_over_stage_readiness_blocker_after_paper_delta() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {"state": "domain_owner_answer_recorded"},
                }
            },
        },
        actions=[
            {
                "source": "study_progress.next_forced_delta.owner_action",
                "next_owner": "write",
                "work_unit_id": "manuscript_story_repair",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "write",
                    "surface_ref": "canonical manuscript story-surface delta or typed blocker:manuscript_story_surface_delta_missing",
                },
            }
        ],
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "manuscript_story_repair"
    assert work_unit["state"]["source"] == "study_progress.next_forced_delta.owner_action"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_projects_current_dpcc_gate_replay_over_stage_readiness_blocker() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "paper_progress_delta": {"count": 1},
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "reason": "paper_progress_delta_observed",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "owner_action": {
                    "next_owner": "finalize",
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
            },
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "receipts/typed_blocker.json"
                    ),
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {"state": "domain_owner_answer_recorded"},
                }
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": "finalize",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "review_current_paper_delta",
            "target_surface": {
                "ref_kind": "route_obligation",
                "route_target": "finalize",
                "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "finalize"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    assert work_unit["state"]["source"] == "study_progress.next_forced_delta.owner_action"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_projects_matching_current_control_repair_over_stage_readiness_blocker_after_paper_delta() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "reason": "paper_progress_delta_observed",
                "work_unit_id": "manuscript_story_repair",
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "write",
                    "surface_ref": (
                        "canonical manuscript story-surface delta or "
                        "typed blocker:manuscript_story_surface_delta_missing"
                    ),
                },
                "owner_action": {
                    "next_owner": "write",
                    "work_unit_id": "manuscript_story_repair",
                    "allowed_actions": ["run_quality_repair_batch"],
                    "owner_receipt_required": True,
                },
            },
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {"state": "domain_owner_answer_recorded"},
                }
            },
        },
        actions=[
            {
                "source": "opl_current_control_state_action_queue",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "manuscript_story_repair",
                "next_work_unit": "manuscript_story_repair",
                "action_fingerprint": "gate-replay-route-back::write::publication-blockers::497d1260db522f01",
                "work_unit_fingerprint": "gate-replay-route-back::write::publication-blockers::497d1260db522f01",
                "authority": "observability_only",
            }
        ],
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "manuscript_story_repair"
    assert work_unit["state"]["source"] == "opl_current_control_state_action_queue"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_preserves_readiness_blocker_over_mismatched_current_control_repair_after_paper_delta() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "reason": "paper_progress_delta_observed",
                "work_unit_id": "manuscript_story_repair",
                "owner_action": {
                    "next_owner": "write",
                    "work_unit_id": "manuscript_story_repair",
                    "allowed_actions": ["run_quality_repair_batch"],
                },
            },
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {"state": "domain_owner_answer_recorded"},
                }
            },
        },
        actions=[
            {
                "source": "opl_current_control_state_action_queue",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "stale_writer_repair",
                "next_work_unit": "stale_writer_repair",
                "authority": "observability_only",
            }
        ],
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "MedAutoScience"
    assert work_unit["action_type"] == "complete_medical_paper_readiness_surface"
    assert work_unit["state"]["source"] == "stage_owner_answer"
    assert work_unit["state"]["typed_blocker"]["blocker_type"] == "medical_paper_readiness_missing"


def test_current_work_unit_projects_matching_current_control_repair_over_prior_action_blocker_after_paper_delta() -> None:
    module = _module()

    for blocked_reason in (
        "domain_owner_action_dispatch_execution_count_zero",
        "no_selected_dispatch_for_requested_action_types",
        "stage_packet_superseded_by_current_consumed_domain_transition",
    ):
        work_unit = module.build_current_work_unit(
            progress={
                "study_id": "002-dm-china-us-mortality-attribution",
                "quest_id": "002-dm-china-us-mortality-attribution",
                "current_stage": "publication_supervision",
                "progress_first_sprint_state": {"paper_progress_delta_counted": True},
                "next_forced_delta": {
                    "required_delta_kind": "review_current_paper_delta",
                    "reason": "paper_progress_delta_observed",
                    "work_unit_id": "manuscript_story_repair",
                    "owner_action": {
                        "next_owner": "write",
                        "work_unit_id": "manuscript_story_repair",
                        "allowed_actions": ["run_quality_repair_batch"],
                        "owner_receipt_required": True,
                    },
                },
                "stage_kernel_projection": {
                    "current_owner_delta": {
                        "owner": "MedAutoScience",
                        "action": "complete_medical_paper_readiness_surface",
                        "reason": "medical_paper_readiness_missing",
                        "source_ref": (
                            "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
                        ),
                        "source_kind": "typed_blocker",
                        "latest_owner_answer_kind": "typed_blocker",
                        "hard_gate": {"state": "domain_owner_answer_recorded"},
                    }
                },
            },
            actions=[
                {
                    "source": "opl_current_control_state_action_queue",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "manuscript_story_repair",
                    "next_work_unit": "manuscript_story_repair",
                    "action_fingerprint": "gate-replay-route-back::write::publication-blockers::497d1260db522f01",
                    "work_unit_fingerprint": "gate-replay-route-back::write::publication-blockers::497d1260db522f01",
                    "authority": "observability_only",
                }
            ],
            blocked_reason=blocked_reason,
            next_owner="write",
        )

        _assert_contract_shape(work_unit)
        assert work_unit["status"] == "executable_owner_action"
        assert work_unit["owner"] == "write"
        assert work_unit["action_type"] == "run_quality_repair_batch"
        assert work_unit["work_unit_id"] == "manuscript_story_repair"
        assert work_unit["state"]["source"] == "opl_current_control_state_action_queue"
        assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_preserves_prior_action_blocker_over_mismatched_current_control_repair() -> None:
    module = _module()

    for blocked_reason in (
        "domain_owner_action_dispatch_execution_count_zero",
        "no_selected_dispatch_for_requested_action_types",
        "stage_packet_superseded_by_current_consumed_domain_transition",
    ):
        work_unit = module.build_current_work_unit(
            progress={
                "study_id": "002-dm-china-us-mortality-attribution",
                "quest_id": "002-dm-china-us-mortality-attribution",
                "current_stage": "publication_supervision",
                "progress_first_sprint_state": {"paper_progress_delta_counted": True},
                "next_forced_delta": {
                    "required_delta_kind": "review_current_paper_delta",
                    "reason": "paper_progress_delta_observed",
                    "work_unit_id": "manuscript_story_repair",
                    "owner_action": {
                        "next_owner": "write",
                        "work_unit_id": "manuscript_story_repair",
                        "allowed_actions": ["run_quality_repair_batch"],
                        "owner_receipt_required": True,
                    },
                },
            },
            actions=[
                {
                    "source": "opl_current_control_state_action_queue",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "stale_writer_repair",
                    "next_work_unit": "stale_writer_repair",
                    "authority": "observability_only",
                }
            ],
            blocked_reason=blocked_reason,
            next_owner="write",
        )

        _assert_contract_shape(work_unit)
        assert work_unit["status"] == "typed_blocker"
        assert work_unit["owner"] == "write"
        assert work_unit["work_unit_id"] is None
        assert work_unit["state"]["typed_blocker"]["blocker_type"] == blocked_reason


def test_current_work_unit_treats_accepted_repair_progress_followup_reason_as_current_action() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-cvd-mortality-risk",
            "quest_id": "002-dm-cvd-mortality-risk",
            "current_stage": "publication_supervision",
        },
        actions=[
            {
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "repair-source-current",
                "repair_progress_followup": {
                    "accepted_owner_receipt": True,
                    "source_fingerprint": "repair-source-current",
                },
            }
        ],
        blocked_reason="repair_progress_ai_reviewer_recheck_required",
        next_owner="ai_reviewer",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "ai_reviewer"
    assert work_unit["action_type"] == "return_to_ai_reviewer_workflow"
    assert work_unit["work_unit_fingerprint"] == "repair-source-current"
    assert work_unit["state"]["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_preserves_readiness_typed_blocker_over_stale_handoff_action() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": "artifacts/stage_outputs/08/receipts/typed_blocker.json",
                    "source_kind": "typed_blocker",
                },
                "stage_run_kernel": {"status": "TypedBlocked"},
            },
        },
        actions=[
            {
                "source_surface": "action_queue",
                "action_type": "complete_medical_paper_readiness_surface",
                "owner": "MedAutoScience",
                "next_work_unit": "complete_medical_paper_readiness_surface",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "allowed_actions": ["complete_medical_paper_readiness_surface"],
            }
        ],
        blocked_reason="medical_paper_readiness_not_ready",
        next_owner="MedAutoScience",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "MedAutoScience"
    assert work_unit["state"]["source"] == "stage_owner_answer"
    assert work_unit["state"]["typed_blocker"]["blocker_type"] == "medical_paper_readiness_missing"
    assert work_unit["state"]["stale_queue_or_handoff_can_override"] is False


def test_current_work_unit_accepts_strict_running_provider_proof() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
        },
        actions=[
            {
                "source_surface": "action_queue",
                "action_type": "run_gate_clearing_batch",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            }
        ],
        blocked_reason="medical_paper_readiness_not_ready",
        next_owner="gate_clearing_batch",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-live",
            "active_stage_attempt_id": "sat-live",
            "active_workflow_id": "wf-live",
            "work_unit_id": "publication_gate_replay",
            "action_type": "run_gate_clearing_batch",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "running_provider_attempt"
    assert work_unit["owner"] == "gate_clearing_batch"
    assert work_unit["work_unit_id"] == "publication_gate_replay"
    assert work_unit["state"]["strict_running_proof"] is True
    assert work_unit["state"]["provider_attempt_proof"]["active_stage_attempt_id"] == "sat-live"


def test_current_work_unit_running_attempt_supersedes_ai_reviewer_recheck_blocker() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
        },
        blocked_reason="repair_progress_ai_reviewer_recheck_required",
        next_owner="ai_reviewer",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-live-ai-review",
            "active_stage_attempt_id": "sat-live-ai-review",
            "active_workflow_id": "wf-live-ai-review",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "action_type": "return_to_ai_reviewer_workflow",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "running_provider_attempt"
    assert work_unit["owner"] == "ai_reviewer"
    assert work_unit["work_unit_id"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_running_attempt_supersedes_provider_admission_current_control_blocker() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
        },
        blocked_reason="provider_admission_current_control_state_required",
        next_owner="one-person-lab",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-live-gate-replay",
            "active_stage_attempt_id": "sat-live-gate-replay",
            "active_workflow_id": "wf-live-gate-replay",
            "owner": "gate_clearing_batch",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "work_unit_fingerprint": "domain-transition::route_back_same_line::dpcc",
            "action_fingerprint": "domain-transition::route_back_same_line::dpcc",
            "action_type": "run_gate_clearing_batch",
            "runtime_health": {
                "health_status": "live",
                "runtime_liveness_status": "live",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::dpcc",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "running_provider_attempt"
    assert work_unit["owner"] == "one-person-lab"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    assert work_unit["work_unit_fingerprint"] == "domain-transition::route_back_same_line::dpcc"
    assert work_unit["state"]["provider_attempt_proof"]["active_stage_attempt_id"] == "sat-live-gate-replay"


def test_current_work_unit_running_attempt_supersedes_prior_dispatch_zero_blocker() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
        },
        blocked_reason="domain_owner_action_dispatch_execution_count_zero",
        next_owner="med-autoscience",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-live-current-gate",
            "active_stage_attempt_id": "sat-live-current-gate",
            "active_workflow_id": "wf-live-current-gate",
            "owner": "gate_clearing_batch",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "work_unit_fingerprint": (
                "study-progress-current-owner-ticket::003::"
                "dpcc_publication_gate_replay_after_current_ai_reviewer_record::run_gate_clearing_batch"
            ),
            "action_fingerprint": (
                "study-progress-current-owner-ticket::003::"
                "dpcc_publication_gate_replay_after_current_ai_reviewer_record::run_gate_clearing_batch"
            ),
            "action_type": "run_gate_clearing_batch",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "running_provider_attempt"
    assert work_unit["owner"] == "med-autoscience"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    assert work_unit["state"]["strict_running_proof"] is True
    assert work_unit["state"]["provider_attempt_proof"]["active_stage_attempt_id"] == "sat-live-current-gate"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_ignores_terminal_log_without_matching_attempt_id() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
        },
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-live-gate",
            "active_stage_attempt_id": "sat-live-gate",
            "active_workflow_id": "wf-live-gate",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "action_type": "return_to_ai_reviewer_workflow",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
            "latest_terminal_stage_log": {
                "stage_attempt_id": None,
                "status": "blocked",
                "source_path": "studies/003/artifacts/supervision/consumer/default_executor_execution/latest.json",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "running_provider_attempt"
    assert work_unit["work_unit_id"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert work_unit["state"]["provider_attempt_proof"]["active_stage_attempt_id"] == "sat-live-gate"


def test_current_work_unit_treats_handoff_ready_as_pending_evidence_not_running() -> None:
    module = _module()
    handoff = {
        "execution_status": "handoff_ready",
        "provider_attempt_or_lease_required": True,
        "running_provider_attempt": False,
        "provider_admission_pending_count": 1,
    }

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-cvd-mortality-risk",
            "quest_id": "002-dm-cvd-mortality-risk",
            "current_stage": "publication_supervision",
        },
        actions=[
            {
                "action_type": "run_quality_repair_batch",
                "owner": "write",
                "next_owner": "write",
                "next_work_unit": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                "authority": "mas_provider_admission_identity",
                "action_id": "provider-admission::002-dm::run_quality_repair_batch",
                "work_unit_fingerprint": "study-progress-current-owner-ticket::002::repair",
                "action_fingerprint": "study-progress-current-owner-ticket::002::repair",
            }
        ],
        provider_admission=handoff,
        blocked_reason="provider_admission_current_control_state_required",
        next_owner="write",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["state"]["provider_admission_pending"] is True
    assert work_unit["state"]["pending_provider_admission_evidence"]["execution_status"] == "handoff_ready"
    assert work_unit["status"] != "running_provider_attempt"


def test_current_work_unit_projects_guarded_apply_owner_answer_missing_over_stale_default_executor() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "paper_autonomy/guarded-apply",
            "current_owner_delta": {
                "surface_kind": "stage_run_current_owner_delta",
                "stage_id": "paper_autonomy/guarded-apply",
                "lineage_ref": "sat_d1bbac5b1671e6afc08d743d",
                "owner": "med-autoscience",
                "action": "paper_autonomy/guarded-apply",
                "desired_delta": "domain_owner_receipt_quality_gate_or_typed_blocker_required",
                "accepted_answer_shape": [
                    "domain_owner_receipt_ref",
                    "quality_gate_receipt_ref",
                    "typed_blocker_ref",
                    "human_gate_ref",
                    "route_back_evidence_ref",
                ],
                "latest_owner_answer_ref": None,
                "domain_ready_authorized": False,
                "hard_gate": {
                    "state": "owner_answer_missing",
                    "owner_answer_missing": True,
                    "owner_answer_still_required": True,
                },
            },
        },
        actions=[
            {
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "action_type": "run_quality_repair_batch",
                "owner": "write",
                "next_work_unit": "stale_default_executor_repair",
                "work_unit_id": "stale_default_executor_repair",
                "work_unit_fingerprint": "stale-default-executor-fingerprint",
            }
        ],
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "med-autoscience"
    assert work_unit["action_type"] == "paper_autonomy/guarded-apply"
    assert work_unit["work_unit_id"] == "domain_owner_receipt_quality_gate_or_typed_blocker_required"
    assert work_unit["stage_id"] == "paper_autonomy/guarded-apply"
    assert work_unit["state"]["source"] == "stage_kernel_projection.current_owner_delta"
    assert work_unit["state"]["owner_answer_missing"] is True
    assert work_unit["currentness_basis"]["lineage_ref"] == "sat_d1bbac5b1671e6afc08d743d"
    assert work_unit["required_output_contract"]["accepted_return_shape"] == [
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]
    assert work_unit["authority_boundary"]["can_write_current_owner_delta"] is False


def test_current_work_unit_projects_nested_guarded_apply_delta_over_stale_handoff() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "queued",
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "surface_kind": "opl_current_owner_delta",
                    "default_planning_root": "current_owner_delta",
                    "stage_id": "paper_autonomy/guarded-apply",
                    "lineage_ref": "sat_57ba2f698a97b2bc7f64d91f",
                    "current_owner": "med-autoscience",
                    "desired_delta": "domain_owner_receipt_quality_gate_or_typed_blocker_required",
                    "accepted_answer_shape": [
                        "domain_owner_receipt_ref",
                        "quality_gate_receipt_ref",
                        "typed_blocker_ref",
                        "human_gate_ref",
                        "route_back_evidence_ref",
                    ],
                    "latest_owner_answer_ref": None,
                    "domain_ready_authorized": False,
                    "owner_answer_missing": True,
                    "owner_answer_still_required": True,
                },
            },
        },
        current_execution_envelope={
            "state_kind": "executable_owner_action",
            "owner": "write",
            "next_work_unit": "return_to_ai_reviewer_workflow",
        },
        blocked_reason="quest_waiting_opl_runtime_owner_route",
        next_owner="write",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["stage_id"] == "paper_autonomy/guarded-apply"
    assert work_unit["owner"] == "med-autoscience"
    assert work_unit["work_unit_id"] == "domain_owner_receipt_quality_gate_or_typed_blocker_required"
    assert work_unit["work_unit_fingerprint"] == "sat_57ba2f698a97b2bc7f64d91f"
    assert work_unit["state"]["source"] == "stage_kernel_projection.current_owner_delta"
    assert work_unit["state"]["owner_answer_missing"] is True


def test_current_work_unit_does_not_treat_unbound_running_attempt_as_guarded_apply_progress() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "paper_autonomy/guarded-apply",
            "current_owner_delta": {
                "surface_kind": "opl_current_owner_delta",
                "default_planning_root": "current_owner_delta",
                "stage_id": "paper_autonomy/guarded-apply",
                "lineage_ref": "sat_d1bbac5b1671e6afc08d743d",
                "current_owner": "med-autoscience",
                "desired_delta": "domain_owner_receipt_quality_gate_or_typed_blocker_required",
                "accepted_answer_shape": [
                    "domain_owner_receipt_ref",
                    "quality_gate_receipt_ref",
                    "typed_blocker_ref",
                    "human_gate_ref",
                    "route_back_evidence_ref",
                ],
                "latest_owner_answer_ref": None,
                "domain_ready_authorized": False,
                "owner_answer_missing": True,
                "owner_answer_still_required": True,
            },
        },
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-stale-default",
            "active_stage_attempt_id": "sat-stale-default",
            "active_workflow_id": "wf-stale-default",
            "stage_id": "domain_owner/default-executor-dispatch",
            "work_unit_id": "run_quality_repair_batch",
            "action_type": "run_quality_repair_batch",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["state"]["source"] == "stage_kernel_projection.current_owner_delta"
    assert work_unit["state"]["owner_answer_missing"] is True
    assert work_unit["status"] != "running_provider_attempt"
