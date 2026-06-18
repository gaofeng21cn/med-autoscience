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
    assert contract["live_readback_contract"]["transaction_consistency"] == (
        helper.live_readback_transaction_consistency()
    )
    assert contract["mas_request_contract"]["forbidden_runtime_fields"] == (
        helper.request_forbidden_runtime_fields()
    )
    assert contract["projection_postcondition_contract"]["mas_projection_cannot_replace"] == list(
        helper.MAS_PROJECTION_CANNOT_REPLACE
    )


def test_helper_shapes_are_single_source_for_existing_runtime_consumers() -> None:
    helper = importlib.import_module(
        "med_autoscience.controllers.opl_domain_progress_transition_contract"
    )
    readback = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback"
    )
    boundaries = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_boundaries"
    )
    projection = importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.transition_request_projection"
    )

    assert readback.required_opl_transition_readback_shape() == helper.required_readback_shape()
    assert boundaries.domain_progress_transition_request_authority_boundary() == (
        helper.mas_request_authority_boundary()
    )
    assert projection._opl_transition_runtime_postcondition() == helper.runtime_postcondition()
    assert projection._mas_transition_projection_authority_boundary() == (
        helper.mas_projection_authority_boundary()
    )


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
