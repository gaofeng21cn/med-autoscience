from __future__ import annotations

import importlib
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta
REPO_ROOT = Path(__file__).resolve().parents[1]


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
    assert "study_truth" in by_layer["mas_core"]["authority_surfaces"]
    assert by_layer["quality_os"]["owner"] == "MedAutoScience"
    assert "publication_readiness" in by_layer["quality_os"]["authority_surfaces"]
    assert by_layer["runtime_os"]["owner"] == "MedAutoScience"
    assert "runtime_health" in by_layer["runtime_os"]["authority_surfaces"]
    assert by_layer["entry_projection"]["role"] == "projection"
    assert by_layer["entry_projection"]["authority_surfaces"] == []
    assert by_layer["entry_projection"]["may_replace_authority"] is False
    assert by_layer["observability_os"]["role"] == "observability"
    assert by_layer["observability_os"]["authority_surfaces"] == []
    assert by_layer["mds_backend"]["owner"] == "MedDeepScientist"
    assert by_layer["mds_backend"]["role"] == "controlled_backend"
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
        "mds_claims_mas_authority",
        "mds_can_replace_authority",
        "mas_authority_layer_missing_authority",
    }


def test_architecture_owner_boundary_docs_and_meta_gate_are_visible() -> None:
    architecture = (REPO_ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")
    invariants = (REPO_ROOT / "docs" / "invariants.md").read_text(encoding="utf-8")
    plan = (REPO_ROOT / "docs" / "program" / "mas_mds_owner_boundary_refactor_plan.md").read_text(
        encoding="utf-8"
    )
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")

    assert "mas_mds_architecture_owner_boundary_report" in architecture
    assert "architecture owner boundary fitness function" in invariants
    assert "结构性重复 authority 风险已经确认" in plan
    assert "strangler" in plan.lower()
    assert "architecture_fitness_functions" in plan
    assert "tests/test_architecture_owner_boundary.py" in makefile
