from __future__ import annotations

import importlib

import pytest


pytestmark = pytest.mark.meta


def test_retained_capability_absorb_surface_keeps_mds_oracle_consumed_by_mas_owners() -> None:
    module = importlib.import_module("med_autoscience.controllers.mds_retained_capability_absorb")

    surface = module.build_mds_retained_capability_absorb_surface()

    assert surface["surface"] == "mds_retained_capability_absorb"
    assert surface["schema_version"] == 1
    assert surface["owner"] == "MedAutoScience"
    assert surface["mds_authority"] == "none"
    assert surface["retained_owner_order"] == ["Runtime OS", "Artifact OS", "Quality OS", "Evaluation OS"]
    assert surface["authority_contract"] == {
        "runtime_authority_owner": "Runtime OS",
        "artifact_authority_owner": "Artifact OS",
        "quality_authority_owner": "Quality OS",
        "lesson_authority_owner": "Evaluation OS",
        "mds_can_authorize_runtime": False,
        "mds_can_authorize_artifacts": False,
        "mds_can_authorize_quality_ready": False,
        "mds_can_authorize_publication_ready": False,
        "mds_can_authorize_submission_ready": False,
        "mechanical_oracle_can_authorize_quality_ready": False,
        "mechanical_oracle_can_authorize_publication_ready": False,
        "mechanical_oracle_can_authorize_submission_ready": False,
        "quality_ready_requires_ai_reviewer_provenance": True,
        "publication_ready_requires_publication_eval_and_controller_decisions": True,
        "submission_ready_requires_artifact_runtime_proof_and_controller_decisions": True,
    }

    groups = surface["retained_capability_groups"]
    assert [group["capability_id"] for group in groups] == [
        "runtime_execution_recovery_replay",
        "artifact_inventory",
        "package_locator",
        "paper_contract_health",
        "manuscript_coverage",
        "prompt_stage_discipline",
        "memory_and_lesson_store",
    ]

    runtime_group = groups[0]
    assert runtime_group["capability_id"] == "runtime_execution_recovery_replay"
    assert runtime_group["consumption_contract"] == "execution/recovery replay consumer"
    assert runtime_group["mds_oracle_fixture"] == "legacy_med_deepscientist_runtime_replay_oracle_fixture"
    assert runtime_group["mds_fixture_role"] == "legacy_oracle"
    assert runtime_group["mas_consumer_surfaces"] == ["study_runtime_status", "runtime_watch"]

    artifact_group = groups[1]
    assert artifact_group["capability_id"] == "artifact_inventory"
    assert artifact_group["consumption_contract"] == "artifact inventory parity"
    assert artifact_group["mds_oracle_fixture"] == "compat_med_deepscientist_artifact_inventory_oracle_fixture"
    assert artifact_group["mds_fixture_role"] == "compat_oracle"
    assert artifact_group["mas_consumer_surfaces"] == [
        "artifact_inventory",
    ]
    assert artifact_group["mechanical_signal_outcome"] == "request_artifact_review"

    package_group = groups[2]
    assert package_group["capability_id"] == "package_locator"
    assert package_group["consumption_contract"] == "current package locator parity"
    assert package_group["mas_consumer_surfaces"] == [
        "submission_minimal",
        "current_package locator",
        "artifact_runtime_proof",
    ]
    assert package_group["mechanical_signal_outcome"] == "request_package_review"

    quality_groups = groups[3:6]
    assert [group["capability_id"] for group in quality_groups] == [
        "paper_contract_health",
        "manuscript_coverage",
        "prompt_stage_discipline",
    ]
    for quality_group in quality_groups:
        assert quality_group["owner"] == "Quality OS"
        assert quality_group["requires_ai_reviewer_provenance"] is True
        assert quality_group["mechanical_signal_outcome"].startswith("request_")
        assert quality_group["mechanical_oracle_can_authorize_quality_ready"] is False
        assert quality_group["mechanical_oracle_can_authorize_publication_ready"] is False
        assert quality_group["mechanical_oracle_can_authorize_submission_ready"] is False

    lesson_group = groups[6]
    assert lesson_group["capability_id"] == "memory_and_lesson_store"
    assert lesson_group["owner"] == "Evaluation OS"
    assert lesson_group["mechanical_signal_outcome"] == "request_lesson_review"

    for group in groups:
        assert group["owner"] in {"Runtime OS", "Artifact OS", "Quality OS", "Evaluation OS"}
        assert group["mds_authority"] == "none"
        assert group["mds_fixture_role"] in {"legacy_oracle", "compat_oracle", "legacy_compat_oracle"}
        assert group["can_authorize_quality_ready"] is False
        assert group["can_authorize_publication_ready"] is False
        assert group["can_authorize_submission_ready"] is False
        assert group["supersede_proof"]["mas_owned"] is True
        assert group["supersede_proof"]["mds_mechanical_signal_role"] == "evidence_only"
        assert group["supersede_proof"]["mechanical_signal_can_only"] in {
            "request_runtime_review",
            "request_artifact_review",
            "request_package_review",
            "request_paper_health_review",
            "request_coverage_review",
            "request_stage_review",
            "request_lesson_review",
        }
        assert group["supersede_proof"]["quality_ready_authorized"] is False
        assert group["supersede_proof"]["publication_ready_authorized"] is False
        assert group["supersede_proof"]["submission_ready_authorized"] is False

    validation = module.validate_mds_retained_capability_absorb_surface(surface)
    assert validation["ok"] is True
    assert validation["issues"] == []


def test_retained_capability_validation_blocks_authority_and_ready_drift() -> None:
    module = importlib.import_module("med_autoscience.controllers.mds_retained_capability_absorb")
    surface = module.build_mds_retained_capability_absorb_surface()

    surface["authority_contract"]["mds_can_authorize_runtime"] = True
    surface["authority_contract"]["mechanical_oracle_can_authorize_quality_ready"] = True
    surface["authority_contract"]["mechanical_oracle_can_authorize_publication_ready"] = True
    surface["authority_contract"]["mechanical_oracle_can_authorize_submission_ready"] = True
    surface["authority_contract"]["quality_ready_requires_ai_reviewer_provenance"] = False
    surface["authority_contract"]["publication_ready_requires_publication_eval_and_controller_decisions"] = False
    surface["authority_contract"]["submission_ready_requires_artifact_runtime_proof_and_controller_decisions"] = False
    surface["retained_capability_groups"][0]["mds_authority"] = "runtime_authority"
    surface["retained_capability_groups"][1]["can_authorize_publication_ready"] = True
    surface["retained_capability_groups"][2]["can_authorize_quality_ready"] = True
    surface["retained_capability_groups"][3]["can_authorize_submission_ready"] = True
    surface["retained_capability_groups"][4]["supersede_proof"]["quality_ready_authorized"] = True
    surface["retained_capability_groups"][5]["supersede_proof"]["publication_ready_authorized"] = True
    surface["retained_capability_groups"][6]["supersede_proof"]["submission_ready_authorized"] = True

    validation = module.validate_mds_retained_capability_absorb_surface(surface)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} >= {
        "authority_drift",
        "quality_ready_drift",
        "publication_ready_drift",
        "submission_ready_drift",
        "supersede_proof_ready_authority_drift",
    }


def test_retained_capability_validation_requires_deepscientist_legacy_compat_or_oracle_markers() -> None:
    module = importlib.import_module("med_autoscience.controllers.mds_retained_capability_absorb")
    surface = module.build_mds_retained_capability_absorb_surface()
    surface["retained_capability_groups"][0]["mds_oracle_fixture"] = "med_deepscientist_runtime_fixture"
    surface["retained_capability_groups"][0]["mds_fixture_role"] = "backend"

    validation = module.validate_mds_retained_capability_absorb_surface(surface)

    assert validation["ok"] is False
    assert {
        "deepscientist_reference_missing_legacy_compat_or_oracle_marker",
        "invalid_mds_fixture_role",
    } <= {issue["code"] for issue in validation["issues"]}
