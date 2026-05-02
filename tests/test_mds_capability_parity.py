from __future__ import annotations

import importlib

import pytest


pytestmark = pytest.mark.meta


def test_mds_capability_parity_matrix_keeps_mds_backend_oracle_only() -> None:
    module = importlib.import_module("med_autoscience.controllers.mds_capability_parity")

    matrix = module.build_mds_capability_parity_matrix()

    assert matrix["surface"] == "mds_capability_parity_matrix"
    assert matrix["mds_role"] == "replaceable_backend_oracle"
    assert matrix["mds_quality_authority"] == "none"
    assert matrix["mas_owner"] == "MedAutoScience"
    assert matrix["physical_absorb_allowed"] == "after_parity_and_owner_cutover_only"
    assert [capability["capability_id"] for capability in matrix["capabilities"]] == [
        "runtime_execution",
        "artifact_inventory",
        "paper_contract_health",
        "manuscript_coverage",
        "prompt_stage_discipline",
        "memory_and_lesson_store",
    ]
    assert matrix["capability_ids"] == [
        "runtime_execution",
        "artifact_inventory",
        "paper_contract_health",
        "manuscript_coverage",
        "prompt_stage_discipline",
        "memory_and_lesson_store",
    ]
    assert matrix["parity_summary"] == {
        "capability_count": 6,
        "proof_count": 6,
        "quality_owner": "MedAutoScience",
        "mds_role": "replaceable_backend_oracle",
        "medical_quality_authority": "blocked_for_mds",
    }
    for capability in matrix["capabilities"]:
        assert capability["mds_authority_role"] in {"backend", "behavior_oracle", "mechanical_oracle"}
        assert capability["can_authorize_medical_quality"] is False
        assert capability["required_parity_proof"]
        assert set(capability["parity_proof"]) == {"proof_kind", "mas_contract", "mds_oracle", "acceptance"}
        assert capability["parity_proof"]["mas_contract"]
        assert capability["parity_proof"]["mds_oracle"]
        assert capability["parity_proof"]["acceptance"]


def test_mds_capability_parity_validation_blocks_quality_authority_drift() -> None:
    module = importlib.import_module("med_autoscience.controllers.mds_capability_parity")
    matrix = module.build_mds_capability_parity_matrix()
    matrix["capabilities"][0]["can_authorize_medical_quality"] = True
    matrix["capabilities"][1]["required_parity_proof"] = ""
    matrix["capabilities"][2]["parity_proof"] = {}

    validation = module.validate_mds_capability_parity_matrix(matrix)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} == {
        "mds_quality_authority_drift",
        "capability_missing_parity_proof",
        "capability_incomplete_parity_proof_detail",
    }
