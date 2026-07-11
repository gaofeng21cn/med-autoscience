from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "contracts" / "opl_domain_progress_transition_runtime_contract.json"


def _contract() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_opl_domain_progress_transition_runtime_contract_matches_helper_abi() -> None:
    helper = importlib.import_module(
        "med_autoscience.controllers.opl_domain_progress_transition_contract"
    )
    contract = _contract()
    runtime_identity = contract["runtime_identity"]

    assert contract["surface_kind"] == "opl_domain_progress_transition_runtime_contract"
    assert runtime_identity == {
        "runtime_id": helper.RUNTIME_ID,
        "runtime_owner": helper.RUNTIME_OWNER,
        "runtime_kind": helper.RUNTIME_KIND,
        "contract_ref": helper.CONTRACT_REF,
    }
    assert contract["transition_taxonomy"] == list(helper.TRANSITION_KINDS)
    assert contract["live_readback_contract"]["required_sections"] == list(
        helper.REQUIRED_READBACK_SECTIONS
    )
    assert contract["live_readback_contract"]["required_runtime_refs"] == list(
        helper.REQUIRED_RUNTIME_REFS
    )
    assert contract["live_readback_contract"]["identity_transaction_refs"] == list(
        helper.LIVE_READBACK_IDENTITY_TRANSACTION_REFS
    )
    assert contract["live_readback_contract"]["latest_transaction_required_flags"] == list(
        helper.LIVE_READBACK_LATEST_TRANSACTION_REQUIRED_FLAGS
    )
    assert contract["live_readback_contract"]["causality_transaction_ref_fields"] == list(
        helper.LIVE_READBACK_CAUSALITY_TRANSACTION_REF_FIELDS
    )
    assert contract["live_readback_contract"]["latest_transaction_ref_fields"] == list(
        helper.LIVE_READBACK_LATEST_TRANSACTION_REF_FIELDS
    )
    assert contract["live_readback_contract"]["read_model_rebuild_required_sections"] == list(
        helper.LIVE_READBACK_READ_MODEL_SECTIONS
    )
    assert contract["live_readback_contract"]["transaction_consistency"] == (
        helper.live_readback_transaction_consistency()
    )
    assert contract["live_readback_contract"]["provider_admission_identity_binding"] == {
        "required_fields": list(helper.PROVIDER_ADMISSION_READBACK_IDENTITY_FIELDS),
        "request_identity_field": helper.PROVIDER_ADMISSION_READBACK_REQUEST_IDENTITY_FIELD,
        "readback_must_match_current_transition_identity": True,
        "same_identity_live_readback_consumes_transition_request_pending": True,
        "stale_or_cross_identity_readback_counts_as_request_pending": True,
        "owner_callable_dispatch_uses_same_identity_binding": True,
        "missing_route_or_attempt_identity_counts_as_missing_opl_authorization": True,
    }
    assert contract["live_readback_contract"]["evidence_source_contract"] == (
        helper.live_readback_evidence_source_contract()
    )
    assert contract["live_readback_contract"]["evidence_source_contract"] == {
        "claimable_runtime_evidence_source_kinds": [
            "opl_runtime_live_readback",
            "opl_current_control_live_readback",
            "opl_stagerun_live_readback",
        ],
        "non_claimable_runtime_evidence_source_kinds": [
            "fixture_or_replay_readback",
            "unit_test_helper_readback",
            "mas_projection_payload",
            "historical_log_extract",
        ],
        "fresh_live_claim_requires_source_kind": True,
        "missing_source_kind_is_not_fresh_live_claim": True,
        "valid_shape_can_test_projection_rules_without_live_claim": True,
    }
    assert contract["mas_request_contract"]["required_identity_fields"] == [
        "study_id",
        "next_action.action_id",
        "next_action.idempotency_key",
        "next_action.action_family",
        "next_action.expected_output_contract.output_kind",
        "source_generation",
        "expected_version",
    ]
    assert contract["mas_request_contract"]["next_action_identity_policy"] == {
        "identity_source": "NextActionEnvelope",
        "required_next_action_identity_fields": list(helper.NEXT_ACTION_IDENTITY_FIELDS),
        "expected_output_kind": helper.OPL_DOMAIN_ROUTE_TRANSITION_RECEIPT_OUTPUT_KIND,
        "legacy_work_unit_id_role": "provenance_currentness_only",
        "legacy_attempt_id_role": "provenance_currentness_only",
        "exact_work_unit_id_authority": False,
    }
    assert contract["mas_request_contract"]["expected_output_contract"] == (
        helper.opl_transition_receipt_expected_output_contract()
    )
    assert contract["mas_request_contract"]["runtime_receipt_authority"] == (
        helper.opl_transition_receipt_authority_boundary()
    )
    assert contract["live_readback_contract"]["expected_output_contract"] == (
        helper.opl_transition_receipt_expected_output_contract()
    )
    assert contract["live_readback_contract"]["runtime_receipt_authority"] == (
        helper.opl_transition_receipt_authority_boundary()
    )
    assert contract["projection_postcondition_contract"]["expected_output_contract"] == (
        helper.opl_transition_receipt_expected_output_contract()
    )
    assert contract["projection_postcondition_contract"]["runtime_receipt_authority"] == (
        helper.opl_transition_receipt_authority_boundary()
    )
    assert (
        contract["projection_postcondition_contract"]["legacy_work_unit_identity_role"]
        == "provenance_currentness_only"
    )
    assert "queue_terminal_status" in contract["forbidden_completion_interpretations"]
    assert "provider_attempt_terminal_status" in contract["forbidden_completion_interpretations"]
    assert contract["mas_request_contract"]["forbidden_runtime_fields"] == (
        helper.request_forbidden_runtime_fields()
    )
    assert contract["projection_postcondition_contract"]["mas_projection_cannot_replace"] == list(
        helper.MAS_PROJECTION_CANNOT_REPLACE
    )
    assert contract["transition_spine_abi_contract"] == helper.transition_spine_abi_contract()


def test_transition_spine_abi_names_minimal_fields_for_each_boundary() -> None:
    helper = importlib.import_module(
        "med_autoscience.controllers.opl_domain_progress_transition_contract"
    )
    contract = _contract()["transition_spine_abi_contract"]

    assert contract["spine"] == list(helper.TRANSITION_SPINE_BOUNDARIES)
    assert set(contract["boundary_abi"]) == set(helper.TRANSITION_SPINE_BOUNDARIES)

    for boundary_name, boundary in contract["boundary_abi"].items():
        assert boundary["boundary"] == boundary_name
        assert set(boundary) == {
            "boundary",
            "owner",
            "role",
            "required_field_families",
            "required_minimal_fields",
            "authority_boundary",
            "forbidden_authority_flags",
        }
        assert boundary["required_field_families"] == list(helper.TRANSITION_SPINE_FIELD_FAMILIES)
        for field_family in helper.TRANSITION_SPINE_FIELD_FAMILIES:
            assert boundary["required_minimal_fields"][field_family]

    assert contract["boundary_abi"]["DomainIntent"]["owner"] == "med-autoscience"
    assert contract["boundary_abi"]["MAS OwnerAnswer"]["owner"] == "med-autoscience"
    assert contract["boundary_abi"]["OPL Command"]["owner"] == "one-person-lab"
    assert contract["boundary_abi"]["OPL Event"]["owner"] == "one-person-lab"
    assert contract["boundary_abi"]["TransactionalOutbox"]["owner"] == "one-person-lab"
    assert contract["boundary_abi"]["StageRun"]["owner"] == "one-person-lab"
    assert contract["boundary_abi"]["DerivedProjection"]["owner"] == "derived-projection-plane"

    assert contract["boundary_abi"]["DomainIntent"]["authority_boundary"] == {
        "domain_intent_owner": "med-autoscience",
        "runtime_execution_owner": "one-person-lab",
        "mas_can_create_opl_command": False,
        "mas_can_create_opl_event": False,
        "mas_can_create_opl_outbox_item": False,
        "mas_can_create_stage_run": False,
    }
    assert contract["boundary_abi"]["DerivedProjection"]["authority_boundary"] == {
        "projection_owner": "derived-projection-plane",
        "authority": False,
        "can_select_next_action": False,
        "can_claim_paper_progress": False,
        "rebuildable_from_event_and_owner_answer": True,
    }


def test_transition_spine_forbidden_interpretations_are_explicit_false_authority_flags() -> None:
    helper = importlib.import_module(
        "med_autoscience.controllers.opl_domain_progress_transition_contract"
    )
    contract = _contract()
    spine = contract["transition_spine_abi_contract"]

    expected = {
        "event_present_is_paper_progress",
        "outbox_emitted_is_paper_progress",
        "provider_completion_is_paper_progress",
        "provider_completion_is_mas_owner_answer",
        "projection_fresh_is_paper_progress",
        "queue_empty_is_paper_progress",
        "trace_visible_is_paper_progress",
        "stage_run_terminal_is_mas_owner_answer",
    }

    assert expected.issubset(spine["false_authority_flags"])
    assert spine["false_authority_flags"] == helper.transition_spine_false_authority_flags()
    assert all(value is False for value in spine["false_authority_flags"].values())

    forbidden_interpretations = set(contract["forbidden_completion_interpretations"])
    assert {
        "event_present_without_mas_owner_answer",
        "outbox_emitted_without_mas_owner_answer",
        "projection_fresh",
        "trace_visible",
        "queue_empty",
        "provider_completion_succeeded",
    }.issubset(forbidden_interpretations)


def test_readback_shape_is_single_sourced_from_runtime_contract() -> None:
    helper = importlib.import_module(
        "med_autoscience.controllers.opl_domain_progress_transition_contract"
    )
    readback = importlib.import_module(
        "med_autoscience.controllers.opl_transition_readback"
    )
    assert readback.required_opl_transition_readback_shape() == helper.required_readback_shape()


def test_policy_adapter_request_uses_runtime_contract_and_remains_mas_request_only() -> None:
    helper = importlib.import_module(
        "med_autoscience.controllers.opl_domain_progress_transition_contract"
    )
    adapter = importlib.import_module("med_autoscience.controllers.paper_progress_policy_adapter")

    request = adapter.build_transition_request(
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        quest_id="quest-dm003",
        action_type="run_quality_repair_batch",
        work_unit_id="medical_prose_write_repair",
        work_unit_fingerprint="publication-blockers::0915410f804b3697",
        source_generation="truth-event-current",
        expected_version="truth-event-current",
        idempotency_context={"action_id": "act-1"},
    )

    assert request["surface_kind"] == "mas_domain_progress_transition_request"
    assert request["runtime_contract_ref"] == helper.CONTRACT_REF
    assert request["target_runtime_owner"] == helper.RUNTIME_OWNER
    assert request["target_runtime_kind"] == helper.RUNTIME_KIND
    assert request["provider_admission_requires_opl_readback_shape"] == (
        helper.required_readback_shape()
    )
    assert request["forbidden_runtime_fields"] == helper.request_forbidden_runtime_fields()
    assert set(helper.request_forbidden_runtime_fields()).isdisjoint(request)
    assert request["mas_can_create_opl_outbox_record"] is False
    assert request["mas_can_create_opl_event"] is False
    assert request["mas_can_create_opl_stage_run"] is False


def test_next_action_identity_requires_receipt_output_kind_not_legacy_attempt_or_work_unit() -> None:
    helper = importlib.import_module(
        "med_autoscience.controllers.opl_domain_progress_transition_contract"
    )
    next_action = {
        "surface_kind": "mas_next_action_envelope",
        "action_id": "next-action-001",
        "idempotency_key": "request::study::stage",
        "action_family": "runtime.opl_route",
        "expected_output_contract": {
            "output_kind": "opl_domain_route_transition_receipt"
        },
        "work_unit_id": "dm003_exact_stage_work_unit",
        "work_unit_fingerprint": "fingerprint::dm003",
        "attempt_idempotency_key": "attempt::legacy",
    }

    assert helper.next_action_identity(next_action) == {
        "surface_kind": "opl_next_action_identity",
        "identity_source": "NextActionEnvelope",
        "next_action_surface_kind": "mas_next_action_envelope",
        "action_id": "next-action-001",
        "idempotency_key": "request::study::stage",
        "action_family": "runtime.opl_route",
        "expected_output_contract": {
            "output_kind": "opl_domain_route_transition_receipt"
        },
    }
    assert helper.next_action_identity_complete(next_action) is True

    handoff = helper.opl_transition_handoff_contract(
        next_action,
        provenance={
            "work_unit_id": "dm003_exact_stage_work_unit",
            "attempt_idempotency_key": "attempt::legacy",
        },
    )

    assert handoff["next_action"] == helper.next_action_identity(next_action)
    assert handoff["next_action_identity_complete"] is True
    assert handoff["expected_output_contract"]["output_kind"] == (
        "opl_domain_route_transition_receipt"
    )
    assert handoff["runtime_receipt_authority"]["receipt_is_input_ref_only"] is True
    assert handoff["runtime_receipt_authority"]["can_claim_stage_complete"] is False
    assert handoff["runtime_receipt_authority"]["can_claim_paper_progress"] is False
    assert handoff["runtime_receipt_authority"]["attempt_terminal_is_paper_progress"] is False
    assert handoff["runtime_receipt_authority"]["provider_completion_is_domain_completion"] is False
    assert handoff["legacy_work_unit_identity_role"] == "provenance_currentness_only"
    assert handoff["exact_work_unit_id_authority"] is False
    assert handoff["provenance"]["work_unit_id"] == "dm003_exact_stage_work_unit"
    assert "attempt_idempotency_key" not in handoff["next_action"]

    wrong_output = {**next_action, "expected_output_contract": {"output_kind": "stage_complete"}}
    missing_action_id = {key: value for key, value in next_action.items() if key != "action_id"}

    assert helper.next_action_identity_complete(wrong_output) is False
    assert helper.next_action_identity_complete(missing_action_id) is False
