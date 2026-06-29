from __future__ import annotations

import json
from pathlib import Path

import pytest

from med_autoscience.controllers.next_action_envelope import (
    ACTION_FAMILIES,
    FAMILY_BLOCKED_TYPED,
    FAMILY_HUMAN_APPROVAL,
    FAMILY_MISSION_COMPLETE,
    FAMILY_PAPER_GATE_PUBLISHABILITY_REPLAY,
    FAMILY_PAPER_PACKAGE_SUBMISSION_MINIMAL,
    FAMILY_PAPER_REVIEW_AI_REVIEWER,
    FAMILY_PAPER_WRITE_PROSE_REPAIR,
    FAMILY_RUNTIME_OPL_ROUTE,
    compile_next_action_envelope,
    resolve_action_family,
)
from med_autoscience.paper_mission_opl_readback import paper_mission_next_action_envelope


pytestmark = [pytest.mark.contract]

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_contract_matches_runtime_action_families_and_forbids_exact_id_authority() -> None:
    contract = json.loads(
        (REPO_ROOT / "contracts" / "next_action_envelope_contract.json").read_text(
            encoding="utf-8"
        )
    )

    assert set(contract["allowed_action_families"]) == ACTION_FAMILIES
    assert contract["authority_boundary_required"]["action_family_authority"] is True
    assert contract["authority_boundary_required"]["exact_work_unit_id_authority"] is False
    assert "exact_work_unit_id_selects_authority_route" in contract["forbidden_authorities"]


@pytest.mark.parametrize(
    ("work_unit_id", "expected_family"),
    [
        ("dm002_medical_prose_write_repair_after_quality_batch", FAMILY_PAPER_WRITE_PROSE_REPAIR),
        ("dm002_after_story_repair_medical_prose_hardening", FAMILY_PAPER_WRITE_PROSE_REPAIR),
        (
            "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
            FAMILY_PAPER_WRITE_PROSE_REPAIR,
        ),
        ("dm003_medical_prose_authority_revise", FAMILY_PAPER_WRITE_PROSE_REPAIR),
        ("produce_ai_reviewer_publication_eval_record_against_current_inputs", FAMILY_PAPER_REVIEW_AI_REVIEWER),
        ("dm003_publication_gate_replay_after_current_ai_reviewer_record", FAMILY_PAPER_GATE_PUBLISHABILITY_REPLAY),
        ("submission_minimal_refresh", FAMILY_PAPER_PACKAGE_SUBMISSION_MINIMAL),
    ],
)
def test_exact_work_unit_ids_resolve_to_semantic_action_family(
    work_unit_id: str,
    expected_family: str,
) -> None:
    assert resolve_action_family(work_unit_id=work_unit_id) == expected_family


def test_compile_envelope_from_stage_outcome_uses_family_as_authority() -> None:
    envelope = compile_next_action_envelope(
        stage_outcome={
            "study_id": "002-dm-china-us-mortality-attribution",
            "stage_id": "publication_supervision",
            "work_unit_id": "dm002_medical_prose_write_repair_after_quality_batch",
            "work_unit_fingerprint": "publication-blockers::f117",
            "decision_signature": "sig-dm002",
            "outcome": {"kind": "next_stage_transition"},
        },
        outcome_ref="/tmp/stage_closure_decision.json",
        owner_route={
            "next_owner": "analysis-campaign",
            "allowed_actions": ["run_quality_repair_batch"],
            "idempotency_key": "owner-route::dm002::repair",
        },
    )

    assert envelope["surface_kind"] == "mas_next_action_envelope"
    assert envelope["action_family"] == FAMILY_PAPER_WRITE_PROSE_REPAIR
    assert envelope["action_kind"] == "paper_write"
    assert envelope["owner"] == "analysis-campaign"
    assert envelope["executor_target"] == "mas_owner_callable"
    assert envelope["authority_boundary"]["action_family_authority"] is True
    assert envelope["authority_boundary"]["exact_work_unit_id_authority"] is False
    assert envelope["authority_boundary"]["can_claim_stage_complete"] is False
    assert envelope["authority_source"] == "mas_next_action_compiler"
    assert envelope["legacy_fields_are_diagnostic"] is True
    assert envelope["legacy_field_diagnostic_roles"]["work_unit_id"] == (
        "diagnostic_currentness_id"
    )
    assert envelope["legacy_field_diagnostic_roles"][
        "current_executable_owner_action"
    ] == "diagnostic_readback_only"
    assert envelope["idempotency_key"] == "owner-route::dm002::repair"
    assert envelope["semantic_progress_signature"] == "sig-dm002"


def test_new_study_exact_work_unit_id_is_diagnostic_when_family_is_canonical() -> None:
    work_unit_id = "dm004_unregistered_owner_surface_refresh_after_source_sync"
    envelope = compile_next_action_envelope(
        stage_outcome={
            "study_id": "004-new-study-family-route",
            "stage_id": "publication_supervision",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": "dm004::source-sync::001",
            "decision_signature": "sig-dm004-family-route",
            "action_family": FAMILY_PAPER_REVIEW_AI_REVIEWER,
            "outcome": {"kind": "next_stage_transition"},
        },
        outcome_ref="/tmp/dm004/stage_closure_decision.json",
        owner_route={
            "next_owner": "ai_reviewer",
            "idempotency_key": "owner-route::dm004::ai-reviewer",
        },
    )

    assert envelope["action_family"] == FAMILY_PAPER_REVIEW_AI_REVIEWER
    assert envelope["action_kind"] == "owner_review"
    assert envelope["owner"] == "ai_reviewer"
    assert envelope["executor_target"] == "mas_owner_callable"
    assert envelope["work_unit_id"] == work_unit_id
    assert envelope["authority_boundary"]["action_family_authority"] is True
    assert envelope["authority_boundary"]["exact_work_unit_id_authority"] is False
    assert envelope["legacy_field_diagnostic_roles"]["work_unit_id"] == (
        "diagnostic_currentness_id"
    )
    assert envelope["expected_output_contract"] == {
        "output_kind": "ai_reviewer_publication_eval",
        "accepted_refs": ["publication_eval_record_ref", "publication_eval_latest_ref"],
    }
    assert envelope["semantic_progress_signature"] == "sig-dm004-family-route"


def test_runtime_route_envelope_keeps_opl_as_receipt_owner_not_stage_authority() -> None:
    envelope = compile_next_action_envelope(
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        stage_id="submission_milestone_candidate",
        stage_outcome={
            "outcome": {"kind": "next_stage_transition"},
            "work_unit_id": "submission_milestone_candidate::followthrough::followthrough-02",
        },
        route_command={
            "command_kind": "resume_stage",
            "runtime_owner": "one-person-lab",
            "request_idempotency_key": "request::003::followthrough",
            "attempt_idempotency_key": "attempt::003::followthrough",
            "work_unit_id": "submission_milestone_candidate::followthrough::followthrough-02",
            "route_target": "opl_runtime_live_readback",
        },
    )

    assert envelope["action_family"] == FAMILY_RUNTIME_OPL_ROUTE
    assert envelope["action_kind"] == "submit_to_opl_runtime"
    assert envelope["owner"] == "one-person-lab"
    assert envelope["idempotency_key"] == "request::003::followthrough"
    assert envelope["executor_target"] == "opl_domain_progress_transition_runtime"
    assert envelope["runtime_receipt_authority"] == "opl_transition_receipt_only"
    assert envelope["completion_authority"] == "stage_outcome_only"
    assert envelope["authority_boundary"]["can_submit_to_opl_runtime"] is True
    assert envelope["authority_boundary"]["can_write_runtime_queue"] is False
    assert envelope["authority_boundary"]["can_write_provider_attempt"] is False
    assert envelope["retry_or_stop_policy"]["semantic_budget_resets_from_transport"] is False


def test_opl_transition_receipt_owner_family_supersedes_runtime_route_redrive() -> None:
    envelope = compile_next_action_envelope(
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        stage_id="submission_milestone_candidate",
        stage_outcome={
            "outcome": {"kind": "next_stage_transition"},
            "work_unit_id": "submission_milestone_candidate::followthrough::followthrough-02",
        },
        route_command={
            "command_kind": "resume_stage",
            "runtime_owner": "one-person-lab",
            "request_idempotency_key": "request::003::followthrough",
            "work_unit_id": "submission_milestone_candidate::followthrough::followthrough-02",
            "route_target": "opl_runtime_live_readback",
        },
        owner_route={
            "action_family": FAMILY_PAPER_GATE_PUBLISHABILITY_REPLAY,
            "next_owner": "mas_authority_kernel",
            "opl_transition_receipt": {
                "surface_kind": "opl_transition_receipt",
                "receipt_status": "terminal_closeout_observed",
                "can_claim_paper_progress": False,
            },
        },
    )

    assert envelope["action_family"] == FAMILY_PAPER_GATE_PUBLISHABILITY_REPLAY
    assert envelope["action_kind"] == "quality_gate_replay"
    assert envelope["owner"] == "mas_authority_kernel"
    assert envelope["executor_target"] == "mas_owner_callable"
    assert envelope["authority_boundary"]["can_submit_to_opl_runtime"] is False


def test_paper_mission_projection_keeps_new_exact_route_target_diagnostic() -> None:
    transaction_id = "paper-mission-transaction::dm004::synthetic-family-route"
    route_target = "dm004_never_allowlisted_runtime_resume_target"
    envelope = paper_mission_next_action_envelope(
        transaction={
            "transaction_id": transaction_id,
            "study_id": "004-new-study-family-route",
            "stage_id": "publication_supervision",
            "stage_terminal_decision": {
                "decision_kind": "continue_same_stage",
                "status": "accepted_dm004_candidate",
                "reason": "DM004 candidate needs the same OPL resume handoff.",
                "next_owner": "mission_executor",
                "next_work_unit": route_target,
            },
            "opl_route_command": {
                "command_kind": "resume_stage",
                "target": route_target,
                "reason": "DM004 candidate accepted for runtime handoff.",
                "source_terminal_decision_ref": (
                    f"{transaction_id}#stage_terminal_decision"
                ),
                "stage_run_ref": "opl-stage-run://dm004/synthetic-family-route",
                "runtime_owner": "one-person-lab",
            },
        },
        diagnostic_refs=["synthetic://dm004/family-route"],
    )

    assert envelope is not None
    assert envelope["action_family"] == FAMILY_RUNTIME_OPL_ROUTE
    assert envelope["action_kind"] == "submit_to_opl_runtime"
    assert envelope["owner"] == "one-person-lab"
    assert envelope["executor_target"] == "opl_domain_progress_transition_runtime"
    assert envelope["work_unit_id"] == route_target
    assert envelope["idempotency_key"] != route_target
    assert envelope["authority_boundary"]["can_submit_to_opl_runtime"] is True
    assert envelope["authority_boundary"]["exact_work_unit_id_authority"] is False
    assert envelope["legacy_fields_are_diagnostic"] is True
    assert envelope["legacy_field_diagnostic_roles"]["work_unit_id"] == (
        "diagnostic_currentness_id"
    )
    assert {"role": "diagnostic", "ref": "synthetic://dm004/family-route"} in envelope[
        "diagnostic_refs"
    ]


def test_terminal_owner_outcomes_compile_to_stop_or_human_families() -> None:
    typed = compile_next_action_envelope(
        study_id="003",
        stage_id="review",
        stage_outcome={"outcome": {"kind": "typed_blocker"}, "work_unit_id": "same_signature"},
    )
    human = compile_next_action_envelope(
        study_id="003",
        stage_id="review",
        stage_outcome={"outcome": {"kind": "human_gate"}, "work_unit_id": "submit_approval"},
    )

    assert typed["action_family"] == FAMILY_BLOCKED_TYPED
    assert typed["retry_or_stop_policy"]["retry_allowed"] is False
    assert human["action_family"] == FAMILY_HUMAN_APPROVAL
    assert human["expected_output_contract"]["accepted_refs"] == ["human_gate_ref"]


def test_submission_ready_owner_receipt_compiles_to_mission_complete() -> None:
    envelope = compile_next_action_envelope(
        study_id="003",
        stage_id="submission_milestone_candidate",
        stage_outcome={
            "kind": "owner_receipt",
            "package_kind": "submission_ready_package",
            "freshness": "current",
            "can_submit": True,
            "quality_gate_status": "clear",
            "generated_from_current_source": True,
            "root": "/tmp/study/manuscript/current_package",
            "zip_exists": True,
            "known_blockers": [],
            "work_unit_id": "submission_ready_package",
            "decision_signature": "sig-submission-ready",
        },
    )

    assert envelope["action_family"] == FAMILY_MISSION_COMPLETE
    assert envelope["action_kind"] == "complete_mission"
    assert envelope["owner"] == "MedAutoScience"
    assert envelope["executor_target"] == "mas_terminal"
    assert envelope["retry_or_stop_policy"]["retry_allowed"] is False
    assert envelope["authority_boundary"]["can_submit_to_opl_runtime"] is False


def test_bare_owner_receipt_does_not_compile_to_mission_complete() -> None:
    envelope = compile_next_action_envelope(
        study_id="003",
        stage_id="submission_milestone_candidate",
        stage_outcome={
            "kind": "owner_receipt",
            "work_unit_id": "owner_receipt_materialization",
        },
    )

    assert envelope["action_family"] != FAMILY_MISSION_COMPLETE


def test_owner_receipt_without_current_package_proof_does_not_compile_to_mission_complete() -> None:
    envelope = compile_next_action_envelope(
        study_id="003",
        stage_id="submission_milestone_candidate",
        stage_outcome={
            "kind": "owner_receipt",
            "package_kind": "submission_ready_package",
            "can_submit": True,
            "quality_gate_status": "clear",
            "known_blockers": [],
            "work_unit_id": "submission_ready_package",
        },
    )

    assert envelope["action_family"] != FAMILY_MISSION_COMPLETE


def test_blocked_submission_ready_owner_receipt_does_not_compile_to_mission_complete() -> None:
    envelope = compile_next_action_envelope(
        study_id="003",
        stage_id="submission_milestone_candidate",
        stage_outcome={
            "kind": "owner_receipt",
            "package_kind": "submission_ready_package",
            "can_submit": True,
            "quality_gate_status": "blocked",
            "known_blockers": ["claim_evidence_consistency_failed"],
            "work_unit_id": "submission_ready_package",
        },
    )

    assert envelope["action_family"] != FAMILY_MISSION_COMPLETE
