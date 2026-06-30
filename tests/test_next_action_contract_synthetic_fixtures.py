from __future__ import annotations

import pytest

from med_autoscience.controllers.next_action_envelope import (
    FAMILY_MISSION_COMPLETE,
    FAMILY_PAPER_REVIEW_AI_REVIEWER,
    FAMILY_RUNTIME_OPL_ROUTE,
    compile_next_action_envelope,
    resolve_action_family,
)
from med_autoscience.controllers import opl_domain_progress_transition_contract
from med_autoscience.paper_mission_opl_readback import paper_mission_next_action_envelope


pytestmark = [pytest.mark.contract]


def test_synthetic_new_study_route_uses_family_identity_not_exact_id_mapping() -> None:
    synthetic_work_unit_id = "dm004_never_mapped_owner_route_after_source_refresh"

    exact_id_only_family = resolve_action_family(work_unit_id=synthetic_work_unit_id)
    envelope = compile_next_action_envelope(
        stage_outcome={
            "study_id": "004-new-study-family-route",
            "stage_id": "publication_supervision",
            "work_unit_id": synthetic_work_unit_id,
            "work_unit_fingerprint": "dm004::never-mapped::001",
            "action_family": FAMILY_PAPER_REVIEW_AI_REVIEWER,
            "decision_signature": "dm004::ai-reviewer::semantic",
            "outcome": {"kind": "next_stage_transition"},
        },
        outcome_ref="synthetic://dm004/stage-outcome",
        owner_route={
            "next_owner": "ai_reviewer",
            "action_type": "produce_ai_reviewer_publication_eval_record",
            "idempotency_key": "next-action::dm004::ai-reviewer",
        },
    )

    assert exact_id_only_family != FAMILY_PAPER_REVIEW_AI_REVIEWER
    assert envelope["action_family"] == FAMILY_PAPER_REVIEW_AI_REVIEWER
    assert envelope["owner"] == "ai_reviewer"
    assert envelope["action_type"] == "produce_ai_reviewer_publication_eval_record"
    assert envelope["work_unit_id"] == synthetic_work_unit_id
    assert envelope["idempotency_key"] == "next-action::dm004::ai-reviewer"
    assert envelope["semantic_progress_signature"] == "dm004::ai-reviewer::semantic"
    assert envelope["authority_boundary"]["action_family_authority"] is True
    assert envelope["authority_boundary"]["exact_work_unit_id_authority"] is False
    assert envelope["legacy_field_diagnostic_roles"]["work_unit_id"] == "diagnostic_currentness_id"


def test_synthetic_new_study_runtime_route_uses_family_identity_not_exact_id_mapping() -> None:
    synthetic_work_unit_id = "dm004_unmapped_runtime_owner_route"

    exact_id_only_family = resolve_action_family(work_unit_id=synthetic_work_unit_id)
    envelope = compile_next_action_envelope(
        stage_outcome={
            "study_id": "004-new-study-runtime-route",
            "stage_id": "publication_supervision",
            "work_unit_id": synthetic_work_unit_id,
            "work_unit_fingerprint": "dm004::runtime::001",
            "action_family": FAMILY_RUNTIME_OPL_ROUTE,
            "decision_signature": "dm004::runtime-route::semantic",
            "outcome": {"kind": "next_stage_transition"},
        },
        outcome_ref="synthetic://dm004/runtime-stage-outcome",
        route_command={
            "command_kind": "resume_stage",
            "runtime_owner": "one-person-lab",
            "request_idempotency_key": "next-action::dm004::runtime-route",
            "attempt_idempotency_key": "attempt::dm004::legacy-only",
            "route_target": "opl_runtime_live_readback",
        },
    )

    assert exact_id_only_family != FAMILY_RUNTIME_OPL_ROUTE
    assert envelope["action_family"] == FAMILY_RUNTIME_OPL_ROUTE
    assert envelope["owner"] == "one-person-lab"
    assert envelope["executor_target"] == "opl_domain_progress_transition_runtime"
    assert envelope["work_unit_id"] == synthetic_work_unit_id
    assert envelope["idempotency_key"] == "next-action::dm004::runtime-route"
    assert envelope["semantic_progress_signature"] == "dm004::runtime-route::semantic"
    assert envelope["authority_boundary"]["action_family_authority"] is True
    assert envelope["authority_boundary"]["exact_work_unit_id_authority"] is False
    assert envelope["legacy_field_diagnostic_roles"]["work_unit_id"] == "diagnostic_currentness_id"


def test_opl_contract_fixture_ignores_legacy_completion_surfaces_for_semantics() -> None:
    synthetic_target = "dm004_never_mapped_opl_transition_target"
    envelope = paper_mission_next_action_envelope(
        transaction={
            "transaction_id": "paper-mission-transaction::dm004::contract-fixture",
            "study_id": "004-new-study-family-route",
            "stage_id": "publication_supervision",
            "stage_terminal_decision": {
                "decision_kind": "continue_same_stage",
                "next_owner": "mission_executor",
                "next_work_unit": synthetic_target,
                "current_executable_owner_action": {
                    "surface_kind": "current_executable_owner_action",
                    "status": "complete",
                    "owner": "write",
                    "action_type": "legacy_complete_owner_action",
                },
                "action_queue": [
                    {
                        "surface_kind": "runtime_queue_row",
                        "status": "complete",
                        "action_family": FAMILY_MISSION_COMPLETE,
                    }
                ],
                "stage_attempt": {
                    "surface_kind": "stage_attempt",
                    "attempt_status": "succeeded",
                    "provider_result": "complete",
                },
                "delivery_mirror": {
                    "surface_kind": "study_delivery_mirror",
                    "freshness": "current",
                    "can_submit": True,
                },
            },
            "opl_route_command": {
                "command_kind": "resume_stage",
                "target": synthetic_target,
                "runtime_owner": "one-person-lab",
                "route_target": "opl_runtime_live_readback",
                "request_idempotency_key": "next-action::dm004::runtime-route",
                "attempt_idempotency_key": "attempt::dm004::legacy-complete",
            },
        },
        opl_runtime_carrier_readback={
            "surface_kind": "paper_mission_opl_runtime_carrier_readback",
            "carrier_status": "complete",
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "complete",
                "owner": "write",
            },
            "action_queue": [{"status": "complete"}],
            "stage_attempt": {"attempt_status": "succeeded"},
            "delivery_mirror": {"freshness": "current", "can_submit": True},
        },
        diagnostic_refs=[
            "legacy://current_executable_owner_action/complete",
            "legacy://runtime_queue/complete",
            "legacy://stage_attempt/succeeded",
            "legacy://delivery_mirror/current",
        ],
    )

    assert envelope is not None
    assert envelope["action_family"] == FAMILY_RUNTIME_OPL_ROUTE
    assert envelope["owner"] == "one-person-lab"
    assert envelope["executor_target"] == "opl_domain_progress_transition_runtime"
    assert envelope["idempotency_key"] == "next-action::dm004::runtime-route"
    assert envelope["runtime_receipt_authority"] == "opl_transition_receipt_only"
    assert envelope["completion_authority"] == "stage_outcome_only"
    assert envelope["authority_boundary"]["can_claim_stage_complete"] is False
    assert envelope["authority_boundary"]["can_claim_submission_ready"] is False
    assert envelope["authority_boundary"]["can_claim_publication_ready"] is False
    assert envelope["authority_boundary"]["can_write_runtime_queue"] is False
    assert envelope["authority_boundary"]["can_write_provider_attempt"] is False
    assert envelope["authority_boundary"]["exact_work_unit_id_authority"] is False
    assert envelope["retry_or_stop_policy"]["semantic_budget_resets_from_transport"] is False
    assert envelope["action_family"] != FAMILY_MISSION_COMPLETE
    assert "current_executable_owner_action" not in envelope
    assert "action_queue" not in envelope
    assert "stage_attempt" not in envelope
    assert "delivery_mirror" not in envelope


def test_canonical_envelope_identity_blocks_legacy_owner_action_resurrection() -> None:
    canonical_target = "dm004_canonical_opl_route_target"
    legacy_owner_action = {
        "surface_kind": "current_executable_owner_action",
        "status": "ready",
        "owner": "write",
        "next_owner": "write",
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "work_unit_id": "legacy_write_repair_target",
        "work_unit_fingerprint": "legacy-write-repair::fingerprint",
    }
    legacy_payload = {
        "current_executable_owner_action": legacy_owner_action,
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "executable_owner_action",
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "legacy_current_work_unit_target",
            "work_unit_fingerprint": "legacy-current-work-unit::fingerprint",
            "state": {"current_executable_owner_action": legacy_owner_action},
        },
        "provider_admission": {
            "surface_kind": "provider_admission",
            "status": "ready",
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "legacy_provider_admission_target",
            "request_idempotency_key": "legacy-provider-admission-request",
        },
        "domain_transition": {
            "decision_type": "route_back_same_line",
            "owner": "write",
            "controller_action": "run_quality_repair_batch",
            "next_work_unit": {"unit_id": "legacy_domain_transition_target"},
        },
    }

    envelope = paper_mission_next_action_envelope(
        transaction={
            "transaction_id": "paper-mission-transaction::dm004::canonical-envelope",
            "study_id": "004-new-study-family-route",
            "stage_id": "publication_supervision",
            "stage_terminal_decision": {
                "decision_kind": "continue_same_stage",
                "next_owner": "write",
                "next_work_unit": "legacy_decision_target",
                **legacy_payload,
            },
            "opl_route_command": {
                "command_kind": "resume_stage",
                "target": canonical_target,
                "runtime_owner": "one-person-lab",
                "route_target": "opl_runtime_live_readback",
                "request_idempotency_key": "next-action::dm004::canonical-runtime-route",
                "attempt_idempotency_key": "attempt::dm004::legacy-provider-attempt",
                **legacy_payload,
            },
            **legacy_payload,
        },
        opl_runtime_carrier={
            "study_id": "004-new-study-family-route",
            "stage_id": "publication_supervision",
            "work_unit_id": "legacy_carrier_work_unit",
            "target_runtime_owner": "legacy-runtime-owner",
            "request_idempotency_key": "legacy-carrier-request",
            **legacy_payload,
        },
        opl_runtime_carrier_readback={
            "surface_kind": "paper_mission_opl_runtime_carrier_readback",
            "carrier_status": "waiting_for_opl_runtime_live_readback",
            **legacy_payload,
        },
        diagnostic_refs=[
            "legacy://current_work_unit/ready",
            "legacy://current_executable_owner_action/write",
            "legacy://provider_admission/write",
            "legacy://domain_transition/write",
        ],
    )

    assert envelope is not None
    assert envelope["action_family"] == FAMILY_RUNTIME_OPL_ROUTE
    assert envelope["action_kind"] == "submit_to_opl_runtime"
    assert envelope["owner"] == "one-person-lab"
    assert envelope["executor_target"] == "opl_domain_progress_transition_runtime"
    assert envelope["work_unit_id"] == canonical_target
    assert envelope["idempotency_key"] == "next-action::dm004::canonical-runtime-route"
    assert envelope["expected_output_contract"]["output_kind"] == "opl_transition_receipt"
    assert envelope["authority_boundary"]["exact_work_unit_id_authority"] is False
    assert envelope["legacy_fields_are_diagnostic"] is True
    assert envelope["legacy_field_diagnostic_roles"]["current_work_unit"] == (
        "diagnostic_readback_only"
    )
    assert envelope["legacy_field_diagnostic_roles"][
        "current_executable_owner_action"
    ] == "diagnostic_readback_only"
    assert opl_domain_progress_transition_contract.next_action_identity(envelope) == {
        "surface_kind": "opl_next_action_identity",
        "identity_source": "NextActionEnvelope",
        "next_action_surface_kind": "mas_next_action_envelope",
        "action_id": envelope["action_id"],
        "idempotency_key": "next-action::dm004::canonical-runtime-route",
        "action_family": FAMILY_RUNTIME_OPL_ROUTE,
        "expected_output_contract": {"output_kind": "opl_transition_receipt"},
    }
    assert (
        opl_domain_progress_transition_contract.next_action_identity_complete(envelope)
        is True
    )
    for legacy_value in (
        "write",
        "run_quality_repair_batch",
        "legacy_current_work_unit_target",
        "legacy_provider_admission_target",
        "legacy_domain_transition_target",
        "legacy-provider-admission-request",
        "legacy-carrier-request",
    ):
        assert legacy_value not in opl_domain_progress_transition_contract.next_action_identity(
            envelope
        ).values()
        assert legacy_value not in envelope.values()


def test_legacy_only_completion_surfaces_do_not_create_next_action_envelope() -> None:
    envelope = paper_mission_next_action_envelope(
        transaction={
            "transaction_id": "paper-mission-transaction::dm004::legacy-only",
            "study_id": "004-new-study-family-route",
            "stage_id": "publication_supervision",
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "owner": "write",
                "action_type": "legacy_complete_owner_action",
                "action_family": FAMILY_MISSION_COMPLETE,
            },
            "action_queue": [
                {
                    "surface_kind": "runtime_queue_row",
                    "status": "ready",
                    "target": "dm004_legacy_queue_target",
                    "action_family": FAMILY_MISSION_COMPLETE,
                }
            ],
            "stage_attempt": {
                "surface_kind": "stage_attempt",
                "attempt_status": "succeeded",
                "provider_result": "complete",
            },
            "delivery_mirror": {
                "surface_kind": "study_delivery_mirror",
                "freshness": "current",
                "can_submit": True,
            },
        },
        opl_runtime_carrier_readback={
            "surface_kind": "paper_mission_opl_runtime_carrier_readback",
            "carrier_status": "complete",
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "owner": "write",
            },
            "action_queue": [{"status": "ready"}],
            "stage_attempt": {"attempt_status": "succeeded"},
            "delivery_mirror": {"freshness": "current", "can_submit": True},
        },
        diagnostic_refs=[
            "legacy://current_executable_owner_action/ready",
            "legacy://runtime_queue/ready",
            "legacy://stage_attempt/succeeded",
            "legacy://delivery_mirror/current",
        ],
    )

    assert envelope is None
