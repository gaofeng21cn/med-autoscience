from __future__ import annotations

import json
from pathlib import Path

import pytest

from med_autoscience.controllers.next_action_envelope import (
    ACTION_FAMILIES,
    FAMILY_BLOCKED_TYPED,
    FAMILY_HUMAN_APPROVAL,
    FAMILY_PAPER_GATE_PUBLISHABILITY_REPLAY,
    FAMILY_PAPER_PACKAGE_SUBMISSION_MINIMAL,
    FAMILY_PAPER_REVIEW_AI_REVIEWER,
    FAMILY_PAPER_WRITE_PROSE_REPAIR,
    FAMILY_RUNTIME_OPL_ROUTE,
    compile_next_action_envelope,
    resolve_action_family,
)


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
