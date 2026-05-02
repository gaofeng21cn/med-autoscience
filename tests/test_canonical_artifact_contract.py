from __future__ import annotations

import importlib

import pytest


pytestmark = pytest.mark.meta


def test_canonical_artifact_contract_forbids_current_package_as_authority() -> None:
    module = importlib.import_module("med_autoscience.controllers.canonical_artifact_contract")

    contract = module.build_canonical_artifact_contract()

    assert contract["surface"] == "canonical_artifact_contract"
    assert contract["artifact_owner"] == "MedAutoScience Artifact OS"
    assert contract["current_package_can_be_edit_source"] is False
    assert contract["submission_minimal_can_be_edit_source"] is False
    assert contract["artifacts_final_can_be_edit_source"] is False
    assert contract["current_package_can_be_quality_authority"] is False
    assert contract["submission_minimal_can_be_quality_authority"] is False
    assert contract["artifacts_final_can_be_quality_authority"] is False
    assert contract["derived_package_can_authorize_submission"] is False
    assert [layer["layer_id"] for layer in contract["artifact_layers"]] == [
        "canonical_sources",
        "derived_manuscript",
        "submission_package",
        "human_handoff_mirror",
    ]
    assert contract["rebuild_chain"] == [
        "study_charter",
        "evidence_ledger",
        "analysis_outputs",
        "ai_reviewer_quality_decision",
        "canonical_manuscript_source",
        "derived_submission_package",
    ]
    assert {
        item["path"]: (item["edit_source"], item["quality_authority"])
        for item in contract["derived_paths"]
    } == {
        "manuscript/current_package/": (False, False),
        "artifacts/final/": (False, False),
        "current_package.zip": (False, False),
        "submission_minimal/": (False, False),
    }
    assert {
        item["target"]: item["must_rebuild_from"] for item in contract["rebuild_requirements"]
    } == {
        "manuscript": ["canonical_sources", "ai_reviewer_quality_decision"],
        "figures": ["canonical_sources", "ai_reviewer_quality_decision"],
        "tables": ["canonical_sources", "ai_reviewer_quality_decision"],
        "submission_package": ["canonical_sources", "ai_reviewer_quality_decision"],
    }


def test_artifact_rebuild_integrity_contract_proves_each_generated_artifact_source_chain() -> None:
    module = importlib.import_module("med_autoscience.controllers.canonical_artifact_contract")

    contract = module.build_artifact_rebuild_integrity_contract()

    assert contract["surface"] == "artifact_rebuild_integrity_contract"
    assert contract["derived_artifact_can_authorize_submission"] is False
    assert contract["derived_artifact_can_be_quality_authority"] is False
    assert contract["derived_artifact_can_be_edit_source"] is False
    proofs_by_target = {proof["target"]: proof for proof in contract["rebuild_proofs"]}
    assert set(proofs_by_target) == {"manuscript", "tables", "figures", "submission_package"}

    expected_roles = {
        "manuscript": "generated_manuscript_projection",
        "tables": "generated_table_projection",
        "figures": "generated_figure_projection",
        "submission_package": "generated_submission_delivery_projection",
    }
    for target, proof in proofs_by_target.items():
        assert proof["generated_artifact_role"] == expected_roles[target]
        assert proof["derived_artifact_can_authorize_submission"] is False
        assert proof["source_refs"]
        assert proof["fingerprint_refs"]
        assert proof["quality_decision_ref"] == "artifacts/publication_eval/latest.json"
        assert proof["controller_decision_ref"] == "controller_decisions/latest.json"


def test_artifact_rebuild_integrity_validation_fails_when_proof_loses_authority_refs() -> None:
    module = importlib.import_module("med_autoscience.controllers.canonical_artifact_contract")
    contract = module.build_artifact_rebuild_integrity_contract()
    contract["derived_artifact_can_authorize_submission"] = True
    contract["rebuild_proofs"][0]["source_refs"] = []
    contract["rebuild_proofs"][1]["fingerprint_refs"] = []
    contract["rebuild_proofs"][2]["quality_decision_ref"] = ""
    contract["rebuild_proofs"][3]["controller_decision_ref"] = "submission_minimal/manifest.json"
    contract["rebuild_proofs"][3]["derived_artifact_can_authorize_submission"] = True

    validation = module.validate_artifact_rebuild_integrity_contract(contract)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} == {
        "derived_artifact_authorizes_submission",
        "rebuild_proof_missing_source_refs",
        "rebuild_proof_missing_fingerprint_refs",
        "rebuild_proof_missing_quality_decision_ref",
        "rebuild_proof_controller_decision_ref_not_controller_owned",
        "rebuild_proof_authorizes_submission_from_derived_artifact",
    }


def test_canonical_artifact_validation_fails_when_package_becomes_source() -> None:
    module = importlib.import_module("med_autoscience.controllers.canonical_artifact_contract")
    contract = module.build_canonical_artifact_contract()
    contract["current_package_can_be_edit_source"] = True
    contract["submission_minimal_can_be_quality_authority"] = True
    contract["derived_paths"][0]["quality_authority"] = True
    contract["rebuild_requirements"][0]["must_rebuild_from"] = ["canonical_sources"]
    contract["artifact_layers"][0]["authority"] = "current_package"

    validation = module.validate_canonical_artifact_contract(contract)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} == {
        "current_package_used_as_edit_source",
        "submission_minimal_used_as_quality_authority",
        "derived_path_used_as_quality_authority",
        "rebuild_requirement_missing_input",
        "canonical_layer_authority_drift",
    }


def test_ai_first_drift_audit_tracks_canonical_artifact_contract() -> None:
    module = importlib.import_module("med_autoscience.ai_first_drift_audit")

    result = module.run_ai_first_drift_audit()

    assert result["status"] == "pass"
    assert "canonical_artifact_contract_forbids_current_package_authority" not in result["summary"][
        "failed_check_ids"
    ]
