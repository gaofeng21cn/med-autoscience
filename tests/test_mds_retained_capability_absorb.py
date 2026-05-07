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
    assert surface["retained_owner_order"] == ["Runtime OS", "Artifact OS", "Quality OS"]
    assert surface["authority_contract"] == {
        "runtime_authority_owner": "Runtime OS",
        "artifact_authority_owner": "Artifact OS",
        "quality_authority_owner": "Quality OS",
        "mds_can_authorize_runtime": False,
        "mds_can_authorize_artifacts": False,
        "mds_can_authorize_quality_ready": False,
        "mds_can_authorize_publication_ready": False,
        "mechanical_oracle_can_authorize_quality_ready": False,
        "mechanical_oracle_can_authorize_publication_ready": False,
        "quality_ready_requires_ai_reviewer_provenance": True,
        "publication_ready_requires_publication_eval_and_controller_decisions": True,
    }

    groups = surface["retained_capability_groups"]
    assert [group["owner"] for group in groups] == ["Runtime OS", "Artifact OS", "Quality OS"]

    runtime_group = groups[0]
    assert runtime_group["capability_id"] == "runtime_execution_recovery_replay"
    assert runtime_group["consumption_contract"] == "execution/recovery replay consumer"
    assert runtime_group["mds_oracle_fixture"] == "legacy_med_deepscientist_runtime_replay_oracle_fixture"
    assert runtime_group["mds_fixture_role"] == "legacy_oracle"
    assert runtime_group["mas_consumer_surfaces"] == ["study_runtime_status", "runtime_watch"]

    artifact_group = groups[1]
    assert artifact_group["capability_id"] == "artifact_inventory_package_locator"
    assert artifact_group["consumption_contract"] == "inventory/package locator parity"
    assert artifact_group["mds_oracle_fixture"] == "compat_med_deepscientist_artifact_locator_oracle_fixture"
    assert artifact_group["mds_fixture_role"] == "compat_oracle"
    assert artifact_group["mas_consumer_surfaces"] == [
        "artifact_inventory",
        "submission_minimal",
        "current_package locator",
    ]

    quality_group = groups[2]
    assert quality_group["capability_id"] == "quality_mechanical_oracle_input"
    assert quality_group["consumption_contract"] == "mechanical oracle input"
    assert quality_group["mds_oracle_fixture"] == "legacy_compat_med_deepscientist_quality_preflight_oracle_fixture"
    assert quality_group["mds_fixture_role"] == "legacy_compat_oracle"
    assert quality_group["requires_ai_reviewer_provenance"] is True
    assert quality_group["mechanical_oracle_can_authorize_quality_ready"] is False
    assert quality_group["mechanical_oracle_can_authorize_publication_ready"] is False

    for group in groups:
        assert group["owner"] in {"Runtime OS", "Artifact OS", "Quality OS"}
        assert group["mds_authority"] == "none"
        assert group["mds_fixture_role"] in {"legacy_oracle", "compat_oracle", "legacy_compat_oracle"}
        assert group["can_authorize_quality_ready"] is False
        assert group["can_authorize_publication_ready"] is False

    validation = module.validate_mds_retained_capability_absorb_surface(surface)
    assert validation["ok"] is True
    assert validation["issues"] == []


def test_retained_capability_validation_blocks_authority_and_ready_drift() -> None:
    module = importlib.import_module("med_autoscience.controllers.mds_retained_capability_absorb")
    surface = module.build_mds_retained_capability_absorb_surface()

    surface["authority_contract"]["mds_can_authorize_runtime"] = True
    surface["authority_contract"]["mechanical_oracle_can_authorize_quality_ready"] = True
    surface["authority_contract"]["mechanical_oracle_can_authorize_publication_ready"] = True
    surface["authority_contract"]["quality_ready_requires_ai_reviewer_provenance"] = False
    surface["authority_contract"]["publication_ready_requires_publication_eval_and_controller_decisions"] = False
    surface["retained_capability_groups"][0]["mds_authority"] = "runtime_authority"
    surface["retained_capability_groups"][1]["can_authorize_publication_ready"] = True
    surface["retained_capability_groups"][2]["can_authorize_quality_ready"] = True

    validation = module.validate_mds_retained_capability_absorb_surface(surface)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} >= {
        "authority_drift",
        "quality_ready_drift",
        "publication_ready_drift",
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
