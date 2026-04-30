from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = "contracts/opl-gateway/family-contract-adoption.json"
DOC_PATH = "docs/references/opl_family_contract_adoption.md"


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _contract() -> dict[str, object]:
    return json.loads(_read(CONTRACT_PATH))


def test_mas_declares_thin_opl_family_contract_adoption() -> None:
    contract = _contract()
    doc = _read(DOC_PATH)

    assert contract["contract_kind"] == "mas_opl_family_contract_adoption.v1"
    assert contract["domain_id"] == "med-autoscience"
    assert contract["opl_role"] == "family-level projection consumer only"
    assert "不把 `OPL` 变成医学研究 owner" in doc


def test_mas_runtime_projection_maps_to_existing_runtime_truth_surfaces() -> None:
    contract = _contract()
    doc = _read(DOC_PATH)
    attempt = contract["attempt_projection"]

    for surface in ("study_runtime_status", "runtime_watch", "controller_decisions/latest.json"):
        assert surface in attempt["source_surfaces"]
        assert surface in doc
    assert attempt["maps_to_opl_contract"] == "opl_family_runtime_attempt_contract.v1"
    assert "study runtime truth" in attempt["owner_boundary"]


def test_mas_quality_projection_keeps_medical_quality_owner_and_blocks_claim_only_ready() -> None:
    contract = _contract()
    doc = _read(DOC_PATH)
    quality = contract["quality_projection"]

    for surface in (
        "study_charter",
        "evidence_ledger",
        "review_ledger",
        "publication_eval/latest.json",
    ):
        assert surface in quality["source_surfaces"]
        assert surface in doc
    assert quality["maps_to_opl_contract"] == "opl_family_domain_quality_projection_contract.v1"
    assert quality["claim_only_ready_forbidden"] is True
    for forbidden in ("claim-only ready", "generic persona QA", "non-medical QA gate", "OPL projection-only"):
        assert forbidden in doc


def test_mas_operator_and_incident_projection_require_source_refs_and_mas_closure() -> None:
    contract = _contract()
    doc = _read(DOC_PATH)
    incident = contract["incident_projection"]
    operator = contract["operator_projection"]

    assert incident["maps_to_opl_contract"] == "opl_family_incident_learning_loop.v1"
    assert "MAS-owned closure ref" in incident["closure_rule"]
    assert "ai_doctor_request" in incident["ai_doctor_boundary"]
    for surface in (
        "artifacts/autonomy/slo_status/latest.json",
        "artifacts/autonomy/ai_doctor_requests/*.json",
        "artifacts/autonomy/ai_doctor_diagnoses/*.json",
        "artifacts/autonomy/repair_actions/*.json",
    ):
        assert surface in incident["source_surfaces"]
        assert surface in doc
    for field in (
        "source_refs",
        "freshness",
        "owner_split",
        "next_surface_ref",
        "human_gate_reason",
        "autonomy_slo",
        "ai_doctor_state",
        "repair_recommendation",
    ):
        assert field in operator["required_fields"]
        assert field.replace("_", " ") in doc or field in doc
    for non_goal in contract["non_goals"]:
        assert non_goal not in ("", None)
