from __future__ import annotations

import importlib
import pytest


pytestmark = pytest.mark.meta


def test_architecture_owner_boundary_report_confirms_and_guards_duplicate_authority_risk() -> None:
    module = importlib.import_module("med_autoscience.controllers.architecture_owner_boundary")

    report = module.build_architecture_owner_boundary_report()

    assert report["surface"] == "mas_mds_architecture_owner_boundary_report"
    assert report["verdict"] == "structural_risk_confirmed_and_guarded"
    assert report["assessment"]["has_duplicate_authority_risk"] is True
    assert report["assessment"]["big_bang_rewrite_allowed"] is False
    assert report["assessment"]["recommended_strategy"] == (
        "owner_matrix_plus_strangler_refactor_plus_architecture_fitness_functions"
    )
    by_layer = {layer["layer_id"]: layer for layer in report["owner_layers"]}
    assert by_layer["mas_core"]["owner"] == "MedAutoScience"
    assert by_layer["mas_core"]["role"] == "authority"
    assert by_layer["mas_core"]["hub_role"] == "authority"
    assert "study_truth" in by_layer["mas_core"]["authority_surfaces"]
    assert by_layer["quality_os"]["owner"] == "MedAutoScience"
    assert by_layer["quality_os"]["hub_role"] == "authority"
    assert "publication_readiness" in by_layer["quality_os"]["authority_surfaces"]
    assert by_layer["runtime_os"]["owner"] == "MedAutoScience"
    assert by_layer["runtime_os"]["hub_role"] == "authority"
    assert "runtime_health" in by_layer["runtime_os"]["authority_surfaces"]
    assert by_layer["entry_projection"]["role"] == "projection"
    assert by_layer["entry_projection"]["hub_role"] == "read_model"
    assert by_layer["entry_projection"]["authority_surfaces"] == []
    assert by_layer["entry_projection"]["may_replace_authority"] is False
    assert by_layer["observability_os"]["role"] == "observability"
    assert by_layer["observability_os"]["hub_role"] == "read_model"
    assert by_layer["observability_os"]["authority_surfaces"] == []
    assert by_layer["mds_backend"]["owner"] == "MedDeepScientist"
    assert by_layer["mds_backend"]["role"] == "controlled_backend"
    assert by_layer["mds_backend"]["hub_role"] == "adapter"
    assert by_layer["mds_backend"]["authority_surfaces"] == []
    assert "publication_readiness" in by_layer["mds_backend"]["forbidden_authority_surfaces"]
    assert "canonical_runtime_action" in by_layer["mds_backend"]["forbidden_authority_surfaces"]
    assert by_layer["mds_backend"]["may_replace_authority"] is False
    assert {risk["risk_id"] for risk in report["duplication_risk_classes"]} == {
        "entry_projection_as_authority",
        "mds_oracle_as_quality_owner",
        "observability_as_control",
        "runtime_status_double_parse",
    }
    assert {item["basis_id"] for item in report["external_engineering_basis"]} >= {
        "strangler_fig",
        "architecture_fitness_functions",
        "team_topologies_cognitive_load",
    }


def test_architecture_owner_boundary_validation_fails_closed_on_owner_drift() -> None:
    module = importlib.import_module("med_autoscience.controllers.architecture_owner_boundary")
    report = module.build_architecture_owner_boundary_report()
    by_layer = {layer["layer_id"]: layer for layer in report["owner_layers"]}
    by_layer["entry_projection"]["authority_surfaces"] = ["user_visible_next_action"]
    by_layer["entry_projection"]["may_replace_authority"] = True
    by_layer["observability_os"]["authority_surfaces"] = ["publication_readiness"]
    by_layer["mds_backend"]["authority_surfaces"] = ["publication_readiness", "canonical_runtime_action"]
    by_layer["mds_backend"]["may_replace_authority"] = True
    by_layer["mas_core"]["authority_surfaces"] = []
    report["assessment"]["big_bang_rewrite_allowed"] = True

    validation = module.validate_architecture_owner_boundary_report(report)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} == {
        "big_bang_rewrite_unblocked",
        "projection_layer_claims_authority",
        "projection_layer_can_replace_authority",
        "non_authority_hub_claims_authority",
        "non_authority_hub_can_replace_authority",
        "mds_claims_mas_authority",
        "mds_can_replace_authority",
        "authority_hub_missing_authority_surface",
        "mas_authority_layer_missing_authority",
    }
