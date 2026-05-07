from __future__ import annotations

import importlib

import pytest


pytestmark = pytest.mark.meta

EXPECTED_CAPABILITY_IDS = [
    "runtime_execution",
    "artifact_inventory",
    "paper_contract_health",
    "manuscript_coverage",
    "prompt_stage_discipline",
    "memory_and_lesson_store",
]


def _complete_proof_bundle_from_matrix(matrix: dict[str, object]) -> dict[str, object]:
    capabilities = []
    for capability in matrix["capabilities"]:
        capabilities.append(
            {
                "capability_id": capability["capability_id"],
                "mas_owner_surface": capability["mas_owner_surface"],
                "oracle_fixture_ref": capability["oracle_fixture_ref"],
                "parity_status": "passed",
                "rollback_surface": capability["rollback_surface"],
                "provenance_ref": capability["provenance_ref"],
                "quality_authority_allowed": False,
                "publication_ready_authority_allowed": False,
                "proof_ref": f"proof-bundles/mds-capability-parity/{capability['capability_id']}.json",
            }
        )
    return {
        "surface": "mds_capability_parity_proof_bundle",
        "schema_version": 1,
        "capabilities": capabilities,
    }


def test_mds_capability_parity_matrix_keeps_mds_backend_oracle_only() -> None:
    module = importlib.import_module("med_autoscience.controllers.mds_capability_parity")

    matrix = module.build_mds_capability_parity_matrix()

    assert matrix["surface"] == "mds_capability_parity_matrix"
    assert matrix["mds_role"] == "replaceable_backend_oracle"
    assert matrix["mds_quality_authority"] == "none"
    assert matrix["mas_owner"] == "MedAutoScience"
    assert matrix["physical_absorb_allowed"] == "after_parity_and_owner_cutover_only"
    assert [capability["capability_id"] for capability in matrix["capabilities"]] == EXPECTED_CAPABILITY_IDS
    assert matrix["capability_ids"] == EXPECTED_CAPABILITY_IDS
    assert [fixture["capability_id"] for fixture in matrix["retained_capability_oracle_fixtures"]] == EXPECTED_CAPABILITY_IDS
    assert matrix["parity_summary"] == {
        "capability_count": 6,
        "proof_count": 6,
        "oracle_fixture_count": 6,
        "quality_owner": "MedAutoScience",
        "mds_role": "replaceable_backend_oracle",
        "medical_quality_authority": "blocked_for_mds",
    }
    fixtures_by_capability = {
        fixture["capability_id"]: fixture for fixture in matrix["retained_capability_oracle_fixtures"]
    }
    for capability in matrix["capabilities"]:
        assert capability["mds_authority_role"] in {"backend", "behavior_oracle", "mechanical_oracle"}
        assert capability["can_authorize_medical_quality"] is False
        assert capability["quality_authority_allowed"] is False
        assert capability["publication_ready_authority_allowed"] is False
        assert capability["mas_owner_surface"]
        assert capability["oracle_fixture_ref"]
        assert capability["parity_status"] == "oracle_fixture_defined"
        assert capability["rollback_surface"]
        assert capability["provenance_ref"]
        assert fixtures_by_capability[capability["capability_id"]] == {
            "capability_id": capability["capability_id"],
            "mas_owner_surface": capability["mas_owner_surface"],
            "oracle_fixture_ref": capability["oracle_fixture_ref"],
            "parity_status": "oracle_fixture_defined",
            "rollback_surface": capability["rollback_surface"],
            "provenance_ref": capability["provenance_ref"],
            "quality_authority_allowed": False,
            "publication_ready_authority_allowed": False,
        }
        assert capability["required_parity_proof"]
        assert set(capability["parity_proof"]) == {"proof_kind", "mas_contract", "mds_oracle", "acceptance"}
        assert capability["parity_proof"]["mas_contract"]
        assert capability["parity_proof"]["mds_oracle"]
        assert capability["parity_proof"]["acceptance"]
        cutover_readiness = capability["cutover_readiness"]
        assert cutover_readiness["cutover_status"] == "blocked_pending_cutover_proofs"
        assert cutover_readiness["owner_switch_allowed"] is False
        assert cutover_readiness["required_gates"] == matrix["cutover_gates"]
        assert cutover_readiness["mas_side_contract"]
        assert cutover_readiness["mds_oracle_fixture"]
        assert cutover_readiness["oracle_fixture_ref"] == capability["oracle_fixture_ref"]
        assert cutover_readiness["provenance_ref"] == capability["provenance_ref"]
        assert cutover_readiness["quality_gate_not_relaxed"] is True
        assert cutover_readiness["rollback_surface"]
        assert cutover_readiness["old_mds_authority_surface_status"] in {"marked_oracle", "retired"}


def test_mds_capability_cutover_gate_blocks_owner_switch_until_proofs_complete() -> None:
    module = importlib.import_module("med_autoscience.controllers.mds_capability_parity")

    gate = module.build_mds_capability_cutover_gate()

    assert gate["surface"] == "mds_capability_cutover_gate"
    assert gate["mds_role"] == "replaceable_backend_oracle"
    assert gate["mds_quality_authority"] == "none"
    assert gate["quality_authority_rule"] == "mds_can_never_authorize_medical_quality"
    assert gate["owner_switch_allowed"] is False
    assert gate["cutover_status"] == "blocked_pending_capability_proofs"
    assert gate["required_gates"] == [
        "mas_side_contract_exists",
        "mds_oracle_fixture_exists",
        "quality_gate_not_relaxed",
        "rollback_surface_exists",
        "old_mds_authority_surface_retired_or_marked_oracle",
    ]
    assert gate["summary"] == {
        "capability_count": 6,
        "owner_switch_allowed_count": 0,
        "blocked_capability_count": 6,
        "medical_quality_authority": "blocked_for_mds",
    }
    for capability in gate["capabilities"]:
        assert capability["cutover_status"] == "blocked_pending_cutover_proofs"
        assert capability["owner_switch_allowed"] is False
        assert capability["required_gates"] == gate["required_gates"]
        assert capability["mas_side_contract"]
        assert capability["mds_oracle_fixture"]
        assert capability["quality_gate_not_relaxed"] is True
        assert capability["rollback_surface"]
        assert capability["old_mds_authority_surface_status"] in {"marked_oracle", "retired"}
        assert capability["can_authorize_medical_quality"] is False
        assert capability["quality_authority_allowed"] is False
        assert capability["publication_ready_authority_allowed"] is False


def test_mds_capability_cutover_gate_allows_owner_switch_with_complete_proof_bundle() -> None:
    module = importlib.import_module("med_autoscience.controllers.mds_capability_parity")
    matrix = module.build_mds_capability_parity_matrix()
    proof_bundle = _complete_proof_bundle_from_matrix(matrix)

    gate = module.build_mds_capability_cutover_gate(proof_bundle)

    assert gate["proof_bundle_status"] == "complete"
    assert gate["owner_switch_allowed"] is True
    assert gate["summary"] == {
        "capability_count": 6,
        "owner_switch_allowed_count": 6,
        "blocked_capability_count": 0,
        "medical_quality_authority": "blocked_for_mds",
    }
    for capability in gate["capabilities"]:
        assert capability["owner_switch_allowed"] is True
        assert capability["parity_status"] == "passed"
        assert capability["quality_authority_allowed"] is False
        assert capability["publication_ready_authority_allowed"] is False


def test_mds_capability_parity_validation_blocks_quality_authority_drift() -> None:
    module = importlib.import_module("med_autoscience.controllers.mds_capability_parity")
    matrix = module.build_mds_capability_parity_matrix()
    matrix["capabilities"][0]["can_authorize_medical_quality"] = True
    matrix["capabilities"][1]["required_parity_proof"] = ""
    matrix["capabilities"][2]["parity_proof"] = {}
    matrix["capabilities"][3]["oracle_fixture_ref"] = ""
    matrix["capabilities"][4]["quality_authority_allowed"] = True
    matrix["capabilities"][5]["publication_ready_authority_allowed"] = True
    matrix["capabilities"][0]["rollback_surface"] = ""
    matrix["capabilities"][1]["provenance_ref"] = ""

    validation = module.validate_mds_capability_parity_matrix(matrix)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} >= {
        "mds_quality_authority_drift",
        "capability_missing_parity_proof",
        "capability_incomplete_parity_proof_detail",
        "capability_missing_oracle_fixture_ref",
        "capability_quality_authority_allowed",
        "capability_publication_ready_authority_allowed",
        "capability_missing_rollback_surface",
        "capability_missing_provenance_ref",
    }


def test_mds_capability_proof_bundle_validation_fails_closed_on_missing_fixture_authority_and_provenance() -> None:
    module = importlib.import_module("med_autoscience.controllers.mds_capability_parity")
    matrix = module.build_mds_capability_parity_matrix()
    proof_bundle = _complete_proof_bundle_from_matrix(matrix)
    proof_bundle["capabilities"][0]["oracle_fixture_ref"] = ""
    proof_bundle["capabilities"][1]["quality_authority_allowed"] = True
    proof_bundle["capabilities"][2]["publication_ready_authority_allowed"] = True
    proof_bundle["capabilities"][3]["rollback_surface"] = ""
    proof_bundle["capabilities"][4]["provenance_ref"] = ""

    validation = module.validate_mds_capability_proof_bundle(proof_bundle, matrix)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} >= {
        "proof_bundle_missing_oracle_fixture_ref",
        "proof_bundle_quality_authority_allowed",
        "proof_bundle_publication_ready_authority_allowed",
        "proof_bundle_missing_rollback_surface",
        "proof_bundle_missing_provenance_ref",
    }
