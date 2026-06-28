from __future__ import annotations

from tests.test_current_work_unit_cases.gate_followthrough_currentness_cases_cases.terminal_routeback_cases import *  # noqa: F403,F401
from tests.test_current_work_unit_cases.gate_followthrough_currentness_cases_cases.publication_eval_repair_cases import *  # noqa: F403,F401
from tests.test_current_work_unit_cases.shared import _assert_contract_shape, _module


def test_current_work_unit_does_not_terminally_block_actionable_gate_followthrough() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    replay_work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    actionable_work_unit_id = "medical_prose_write_repair"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260611T122549Z::sat_64c5fb484e8ee7b3971786ee"
    )
    fingerprint = (
        "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
        f"{replay_work_unit_id}::{source_eval_id}"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": source_eval_id,
                "work_unit_id": replay_work_unit_id,
                "work_unit_fingerprint": "sha256:fresh-gate-receipt",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": replay_work_unit_id,
                    "current_publication_work_unit_id": actionable_work_unit_id,
                    "explicit_work_unit_fingerprint_matches_current": False,
                    "lacks_specific_blocker_object": False,
                    "current_actionability_status": "actionable",
                },
                "current_publication_work_unit": {
                    "unit_id": actionable_work_unit_id,
                    "lane": "write",
                },
                "gate_replay_status": "blocked",
                "blocking_issue_count": 3,
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
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": "finalize",
            "work_unit_id": replay_work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "source_eval_id": source_eval_id,
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
            "owner_receipt_required": True,
        },
        next_owner="finalize",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "finalize"
    assert work_unit["work_unit_id"] == replay_work_unit_id
    assert work_unit["state"]["source"] == "study_progress.next_forced_delta.owner_action"


def test_current_work_unit_actionable_gate_followthrough_supersedes_stale_readiness_blocker() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "required_input": "complete_medical_paper_readiness_surface",
                    "source_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
                    "source_kind": "typed_blocker",
                },
            },
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": "publication-eval::002::current",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "ai_reviewer_record_gate_consumption",
                    "current_publication_work_unit_id": "analysis_claim_evidence_repair",
                    "current_work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                },
                "gate_replay_status": "blocked",
                "gate_replay_blockers": ["claim_evidence_consistency_failed"],
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_owner": "analysis-campaign",
            "work_unit_id": "analysis_claim_evidence_repair",
            "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
            "action_fingerprint": "publication-blockers::497d1260db522f01",
            "source_eval_id": "publication-eval::002::current",
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "target_surface": {
                "ref_kind": "publication_work_unit",
                "route_target": "analysis-campaign",
                "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
            },
        },
        next_owner="MedAutoScience",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "analysis-campaign"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "analysis_claim_evidence_repair"
    assert work_unit["state"]["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"


def test_current_work_unit_actionable_gate_followthrough_supersedes_stale_ai_reviewer_blocker() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"
    source_eval_id = "publication-eval::002::current"
    work_unit_id = "medical_prose_quality_analysis_source_documentation_repair"
    fingerprint = "publication-blockers::5a4f2060d6d7d97e"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": source_eval_id,
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "ai_reviewer_record_gate_consumption",
                    "current_publication_work_unit_id": work_unit_id,
                    "current_work_unit_fingerprint": fingerprint,
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": work_unit_id,
                    "lane": "analysis-campaign",
                },
                "gate_replay_status": "blocked",
                "gate_replay_blockers": [
                    "medical_publication_surface_blocked",
                    "claim_evidence_consistency_failed",
                    "submission_hardening_incomplete",
                ],
                "latest_record_path": (
                    f"/workspace/studies/{study_id}/artifacts/controller/"
                    "gate_clearing_batch/latest.json"
                ),
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_owner": "analysis-campaign",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "source_eval_id": source_eval_id,
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "publication_gate_actionable_repair_delta_or_typed_blocker",
            "target_surface": {
                "ref_kind": "publication_work_unit",
                "route_target": "analysis-campaign",
                "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
            },
        },
        typed_blocker={
            "surface_kind": "mas_domain_typed_blocker",
            "schema_version": 1,
            "blocker_id": "ai_reviewer_record_stale_after_current_inputs",
            "blocker_type": "ai_reviewer_record_stale_after_current_inputs",
            "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
            "reason": "ai_reviewer_record_stale_after_current_inputs",
            "owner": "ai_reviewer",
            "next_owner": "ai_reviewer",
            "action_type": "return_to_ai_reviewer_workflow",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "work_unit_fingerprint": (
                "domain-transition::ai_reviewer_re_eval::"
                "produce_ai_reviewer_publication_eval_record_against_current_inputs"
            ),
            "source_ref": "artifacts/supervision/requests/ai_reviewer/latest.json",
        },
        next_owner="ai_reviewer",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "analysis-campaign"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == work_unit_id
    assert work_unit["work_unit_fingerprint"] == fingerprint
    assert work_unit["state"]["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"


def test_current_work_unit_actionable_gate_followthrough_supersedes_stale_selector_residue_for_new_unit() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "003-dpcc-primary-care-phenotype-treatment-gap::2026-06-20T05:46:03+00:00"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": source_eval_id,
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "analysis_claim_evidence_repair",
                    "selected_publication_work_unit_id": "analysis_claim_evidence_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "explicit_work_unit_fingerprint": "publication-blockers::2a234f3e48d8beb5",
                    "current_work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "explicit_work_unit_fingerprint_matches_current": False,
                    "fingerprint_or_source_signature_unchanged": False,
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
                "explicit_publication_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                },
                "selected_publication_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                },
                "gate_replay_status": "blocked",
                "gate_replay_blockers": [
                    "stale_submission_minimal_authority",
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
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_owner": "analysis-campaign",
            "work_unit_id": "analysis_claim_evidence_repair",
            "work_unit_fingerprint": "publication-blockers::2a234f3e48d8beb5",
            "action_fingerprint": "publication-blockers::2a234f3e48d8beb5",
            "source_eval_id": source_eval_id,
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "publication_gate_actionable_repair_delta_or_typed_blocker",
            "owner_route_currentness_basis": {
                "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                "source_eval_id": source_eval_id,
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::2a234f3e48d8beb5",
                "explicit_publication_work_unit_id": "analysis_claim_evidence_repair",
                "selected_publication_work_unit_id": "analysis_claim_evidence_repair",
            },
            "target_surface": {
                "ref_kind": "publication_work_unit",
                "route_target": "analysis-campaign",
                "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
            },
        },
        typed_blocker={
            "surface_kind": "mas_domain_typed_blocker",
            "blocker_id": "no_selected_dispatch_for_authorized_stage_packet",
            "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
            "blocked_reason": "no_selected_dispatch_for_authorized_stage_packet",
            "owner": "one-person-lab",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "source_ref": (
                f"/workspace/studies/{study_id}/artifacts/supervision/consumer/"
                "owner_callable_adapter_receipt/sat_08da46bea43329723d2fbbea.closeout.json"
            ),
        },
        next_owner="one-person-lab",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "analysis-campaign"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "analysis_claim_evidence_repair"
    assert work_unit["work_unit_fingerprint"] == "publication-blockers::2a234f3e48d8beb5"
    assert work_unit["state"]["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"


def test_current_work_unit_actionable_gate_followthrough_supersedes_stale_zero_dispatch_closeout() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"
    source_eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "002-dm-china-us-mortality-attribution::stage-attempt-sat_a9b2ffcc8f97a24837d729bf::"
        "2026-06-11T12:41:21+00:00"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": source_eval_id,
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "ai_reviewer_record_gate_consumption",
                    "current_publication_work_unit_id": "analysis_claim_evidence_repair",
                    "current_work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                    "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
                },
                "gate_replay_status": "blocked",
                "gate_replay_blockers": [
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "claim_evidence_consistency_failed",
                    "submission_hardening_incomplete",
                    "submission_surface_qc_failure_present",
                    "forbidden_manuscript_terminology",
                ],
                "latest_record_path": (
                    f"/workspace/studies/{study_id}/artifacts/controller/"
                    "gate_clearing_batch/latest.json"
                ),
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_owner": "analysis-campaign",
            "work_unit_id": "analysis_claim_evidence_repair",
            "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
            "action_fingerprint": "publication-blockers::497d1260db522f01",
            "source_eval_id": source_eval_id,
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "target_surface": {
                "ref_kind": "publication_work_unit",
                "route_target": "analysis-campaign",
                "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
            },
        },
        typed_blocker={
            "surface_kind": "mas_domain_typed_blocker",
            "schema_version": 1,
            "blocker_id": "stage_outcome_authority_zero_selected_dispatch",
            "status": "blocked",
            "reason": "stage_outcome_authority_zero_selected_dispatch",
            "owner": "gate_clearing_batch",
            "next_owner": "med-autoscience",
            "requested_action_type": "run_gate_clearing_batch",
            "blocker_type": "stage_outcome_authority_zero_selected_dispatch",
            "blocked_reason": "stage_outcome_authority_zero_selected_dispatch",
            "action_type": "run_gate_clearing_batch",
            "source_ref": (
                "artifacts/supervision/consumer/owner_callable_adapter_receipt/"
                "sat_8365e11154b896e37d7a5344.closeout.json"
            ),
        },
        next_owner="gate_clearing_batch",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "analysis-campaign"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "analysis_claim_evidence_repair"
    assert work_unit["work_unit_fingerprint"] == "publication-blockers::497d1260db522f01"
    assert work_unit["state"]["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"


def test_current_work_unit_actionable_gate_followthrough_supersedes_consumed_typed_closeout_packet() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260611T203520Z::sat_a48379bbe63bcd5e86b5d6db"
    )
    gate_work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    gate_fingerprint = (
        "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
        f"{gate_work_unit_id}::{source_eval_id}"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": source_eval_id,
                "work_unit_id": gate_work_unit_id,
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": gate_work_unit_id,
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                    "summary": "Repair medical prose blockers before package readiness.",
                },
                "gate_replay_status": "blocked",
                "gate_replay_blockers": [
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                ],
                "latest_record_path": (
                    f"/workspace/studies/{study_id}/artifacts/controller/"
                    "gate_clearing_batch/latest.json"
                ),
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_owner": "write",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "action_fingerprint": "publication-blockers::0915410f804b3697",
            "source_eval_id": source_eval_id,
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "target_surface": {
                "ref_kind": "publication_work_unit",
                "route_target": "write",
                "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
            },
        },
        typed_blocker={
            "surface_kind": "mas_domain_typed_blocker",
            "schema_version": 1,
            "blocker_id": "current_work_unit_already_typed_closeout_packet_required",
            "blocker_type": "current_work_unit_already_typed_closeout_packet_required",
            "blocked_reason": "current_work_unit_already_typed_closeout_packet_required",
            "reason": "current_work_unit_already_typed_closeout_packet_required",
            "owner": "one-person-lab",
            "next_owner": "one-person-lab",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": gate_work_unit_id,
            "work_unit_fingerprint": gate_fingerprint,
            "source_ref": (
                "artifacts/supervision/consumer/owner_callable_adapter_receipt/"
                "sat_cbe7d09ebd4ca572b544c073.closeout.json"
            ),
        },
        next_owner="one-person-lab",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "medical_prose_write_repair"
    assert work_unit["work_unit_fingerprint"] == "publication-blockers::0915410f804b3697"
    assert work_unit["state"]["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"


def test_current_work_unit_gate_followthrough_current_repair_supersedes_executed_transport_closeout() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )
    gate_fingerprint = "sha256:6423b231114cbec0e8d1ccb0b69adb117d0f2d8fa58d72751627c049a0dc10e4"
    repair_fingerprint = "publication-blockers::0915410f804b3697"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": source_eval_id,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": repair_fingerprint,
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "medical_prose_write_repair",
                    "selected_publication_work_unit_id": "medical_prose_write_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "explicit_work_unit_fingerprint": repair_fingerprint,
                    "current_work_unit_fingerprint": repair_fingerprint,
                    "explicit_work_unit_fingerprint_matches_current": True,
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
                "gate_replay_status": "blocked",
                "blocking_issue_count": 4,
                "gate_replay_blockers": [
                    "stale_submission_minimal_authority",
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                ],
                "latest_record_path": (
                    f"/workspace/studies/{study_id}/artifacts/controller/"
                    "gate_clearing_batch/latest.json"
                ),
            },
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "surface_kind": "mas_latest_terminal_stage_log_projection",
                    "action_type": "run_gate_clearing_batch",
                    "status": "executed",
                    "outcome": "executed",
                    "progress_delta_classification": "typed_blocker",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": gate_fingerprint,
                    "source_eval_id": source_eval_id,
                    "source_path": (
                        f"/workspace/studies/{study_id}/artifacts/supervision/consumer/"
                        "owner_callable_adapter_receipt/sat_gate.closeout.json"
                    ),
                },
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_owner": "write",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": repair_fingerprint,
            "action_fingerprint": repair_fingerprint,
            "source_eval_id": source_eval_id,
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "target_surface": {
                "ref_kind": "publication_work_unit",
                "route_target": "write",
                "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
            },
        },
        typed_blocker={
            "blocker_id": "executed",
            "blocker_type": "executed",
            "blocked_reason": "executed",
            "owner": "one-person-lab",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": gate_fingerprint,
            "action_fingerprint": gate_fingerprint,
        },
        blocked_reason="opl_execution_authorization_required",
        next_owner="one-person-lab",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "medical_prose_write_repair"
    assert work_unit["work_unit_fingerprint"] == repair_fingerprint
    assert work_unit["state"]["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_gate_followthrough_current_repair_accepts_gate_replay_selected_residue() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )
    gate_fingerprint = "sha256:b4db4d9482b86d4e71a8bd8ba5d0a9793e7eeea70d52bb9a5bbba53ff4c305eb"
    repair_fingerprint = "publication-blockers::0915410f804b3697"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": source_eval_id,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": repair_fingerprint,
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "medical_prose_write_repair",
                    "selected_publication_work_unit_id": "publication_gate_replay",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "explicit_work_unit_fingerprint": repair_fingerprint,
                    "current_work_unit_fingerprint": repair_fingerprint,
                    "explicit_work_unit_fingerprint_matches_current": True,
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
                "gate_replay_status": "blocked",
                "blocking_issue_count": 3,
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
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_owner": "write",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": repair_fingerprint,
            "action_fingerprint": repair_fingerprint,
            "source_eval_id": source_eval_id,
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "target_surface": {
                "ref_kind": "publication_work_unit",
                "route_target": "write",
                "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
            },
        },
        typed_blocker={
            "blocker_id": "executed",
            "blocker_type": "executed",
            "blocked_reason": "executed",
            "owner": "one-person-lab",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": gate_fingerprint,
            "action_fingerprint": gate_fingerprint,
        },
        next_owner="one-person-lab",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "medical_prose_write_repair"
    assert work_unit["work_unit_fingerprint"] == repair_fingerprint
    assert work_unit["state"]["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"


def test_current_work_unit_terminal_quality_repair_next_delta_blocks_stale_gate_followthrough_identity() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"
    stale_work_unit_id = "analysis_claim_evidence_repair"
    canonical_work_unit_id = "dm002_current_publication_hardening_after_current_ai_reviewer_eval"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": (
                    "publication-eval::002-dm-china-us-mortality-attribution::"
                    "002-dm-china-us-mortality-attribution::stage-attempt-sat_a9b2ffcc8f97a24837d729bf::"
                    "2026-06-11T12:41:21+00:00"
                ),
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "ai_reviewer_record_gate_consumption",
                    "current_publication_work_unit_id": stale_work_unit_id,
                    "current_work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": stale_work_unit_id,
                    "lane": "analysis-campaign",
                },
                "gate_replay_status": "blocked",
                "gate_replay_blockers": ["claim_evidence_consistency_failed"],
            },
            "opl_current_control_state_handoff": {
                "latest_terminal_stage_log": {
                    "stage_attempt_id": "sat_8fb0009e8384954d24ab28cf",
                    "stage_id": "stage_outcome/opl-handoff",
                    "action_type": "run_quality_repair_batch",
                    "status": "blocked",
                    "work_unit_id": stale_work_unit_id,
                    "typed_blocker": {
                        "blocker_id": "opl_execution_authorization_required",
                        "owner": "one-person-lab",
                    },
                    "paper_stage_log": {
                        "stage_name": canonical_work_unit_id,
                        "outcome": "typed_blocker",
                        "progress_delta_classification": "typed_blocker",
                        "remaining_blockers": [
                            "opl_execution_authorization_required",
                            "opl_work_unit_binding_mismatch",
                        ],
                        "next_forced_delta": {
                            "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                            "work_unit_id": canonical_work_unit_id,
                            "target_surface": {
                                "surface_ref": (
                                    "canonical manuscript story-surface delta or "
                                    "typed blocker:manuscript_story_surface_delta_missing"
                                ),
                            },
                            "owner_action": {
                                "next_owner": "write",
                                "action_type": "run_quality_repair_batch",
                                "work_unit_id": canonical_work_unit_id,
                            },
                        },
                    },
                    "source_path": (
                        f"/workspace/studies/{study_id}/artifacts/supervision/consumer/"
                        "owner_callable_adapter_receipt/sat_8fb0009e8384954d24ab28cf.closeout.json"
                    ),
                }
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": "write",
            "work_unit_id": canonical_work_unit_id,
            "work_unit_fingerprint": (
                "owner-route::write::manuscript_story_surface_delta_missing::"
                "run_quality_repair_batch"
            ),
            "action_fingerprint": (
                "owner-route::write::manuscript_story_surface_delta_missing::"
                "run_quality_repair_batch"
            ),
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "paper_progress_delta_or_typed_blocker",
            "terminal_stage_next_forced_delta": True,
        },
        next_owner="analysis-campaign",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "one-person-lab"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == canonical_work_unit_id
    assert work_unit["state"]["blocker_type"] == "opl_execution_authorization_required"
    assert work_unit["state"]["source"] == "terminal_closeout_typed_blocker"
    assert work_unit["state"]["typed_blocker"]["terminal_closeout_status"] == "blocked"
    assert work_unit["state"]["typed_blocker"]["terminal_closeout_outcome"] == "typed_blocker"


def test_current_work_unit_terminal_gate_routeback_action_supersedes_consumed_gate_blocker() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    gate_fingerprint = "sha256:12592784fb257f669d5a5678f6c3a6e93a03c5d16ec1d661d1f88c19692bb4df"
    closeout_ref = (
        f"/workspace/studies/{study_id}/artifacts/supervision/consumer/"
        "owner_callable_adapter_receipt/sat_e4dbaf4c7df74333010d29ae.closeout.json"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "stage_attempt_id": "sat_e4dbaf4c7df74333010d29ae",
                    "stage_id": "stage_outcome/opl-handoff",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": gate_fingerprint,
                    "status": "blocked",
                    "outcome": "blocked:publication_gate_replay_blocked",
                    "progress_delta_classification": "typed_blocker",
                    "remaining_blockers": [
                        "medical_publication_surface_blocked",
                        "reviewer_first_concerns_unresolved",
                        "submission_hardening_incomplete",
                    ],
                    "paper_stage_log": {
                        "progress_delta_classification": "typed_blocker",
                        "next_forced_delta": {
                            "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                            "work_unit_id": "publication_gate_replay",
                            "target_surface": {
                                "surface_ref": (
                                    "MAS publication gate route-back owner action for "
                                    "reviewer-first concerns and submission hardening"
                                ),
                            },
                            "owner_action": {
                                "next_owner": "write",
                                "action_type": "return_to_write",
                                "work_unit_id": "reviewer_first_publication_surface_repair",
                            },
                        },
                    },
                    "source_path": closeout_ref,
                    "closeout_refs": [closeout_ref],
                }
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": "write",
            "work_unit_id": "reviewer_first_publication_surface_repair",
            "work_unit_fingerprint": "route-currentness::003-dpcc-primary-care-phenotype-treatment-gap::fresh",
            "action_fingerprint": "route-currentness::003-dpcc-primary-care-phenotype-treatment-gap::fresh",
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "paper_progress_delta_or_typed_blocker",
            "target_surface": {
                "surface_ref": (
                    "MAS publication gate route-back owner action for reviewer-first concerns "
                    "and submission hardening"
                )
            },
            "terminal_stage_next_forced_delta": True,
            "acceptance_refs": [closeout_ref],
        },
        typed_blocker={
            "surface_kind": "mas_typed_blocker",
            "blocker_id": "publication_gate_replay_blocked",
            "blocker_type": "medical_publication_surface_blocked",
            "blocked_reason": "medical_publication_surface_blocked",
            "owner": "one-person-lab",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": gate_fingerprint,
            "source_ref": closeout_ref,
        },
        next_owner="one-person-lab",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "reviewer_first_publication_surface_repair"
    assert work_unit["state"]["source"] == "study_progress.next_forced_delta.owner_action"
