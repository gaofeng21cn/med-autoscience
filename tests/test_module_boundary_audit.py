from __future__ import annotations

import importlib
import pytest


pytestmark = pytest.mark.meta


def test_module_boundary_audit_report_declares_layers_dependencies_and_authority_boundaries() -> None:
    module = importlib.import_module("med_autoscience.controllers.module_boundary_audit")

    report = module.build_module_boundary_audit_report()

    assert report["surface"] == "mas_mds_module_boundary_audit_report"
    assert report["verdict"] == "module_boundaries_declared_and_guarded"
    by_group = {group["group_id"]: group for group in report["module_groups"]}
    assert list(by_group) == [
        "mas_core",
        "quality_os",
        "runtime_authority_refs",
        "artifact_delivery",
        "product_entry_projection",
        "observability_os",
        "mds_backend_oracle",
        "maintainability",
    ]
    assert by_group["mas_core"]["layer"] == "authority"
    assert by_group["mas_core"]["hub_role"] == "authority"
    assert "study_truth" in by_group["mas_core"]["writable_authority_surfaces"]
    assert by_group["quality_os"]["may_authorize_publication"] is True
    assert by_group["quality_os"]["hub_role"] == "authority"
    assert "publication_readiness" in by_group["quality_os"]["writable_authority_surfaces"]
    runtime_refs = by_group["runtime_authority_refs"]
    assert runtime_refs["may_control_runtime"] is False
    assert runtime_refs["hub_role"] == "adapter"
    assert runtime_refs["writable_authority_surfaces"] == []
    assert runtime_refs["opl_runtime_control_owner"] == "one-person-lab"
    assert runtime_refs["domain_authority_ref_surfaces"] == [
        "runtime_health",
        "canonical_runtime_action",
    ]
    assert by_group["artifact_delivery"]["hub_role"] == "materializer"
    assert by_group["artifact_delivery"]["writable_authority_surfaces"] == ["artifact_authority"]
    assert by_group["product_entry_projection"]["hub_role"] == "read_model"
    assert by_group["product_entry_projection"]["projection_only"] is True
    assert by_group["product_entry_projection"]["writable_authority_surfaces"] == []
    assert by_group["observability_os"]["hub_role"] == "read_model"
    assert by_group["observability_os"]["projection_only"] is True
    assert by_group["observability_os"]["may_control_runtime"] is False
    assert "src/med_autoscience/controllers/outcome_provider_ops_projection.py" in by_group[
        "observability_os"
    ]["repo_targets"]
    assert by_group["mds_backend_oracle"]["owner"] == "MedDeepScientist"
    assert by_group["mds_backend_oracle"]["hub_role"] == "adapter"
    assert by_group["mds_backend_oracle"]["writable_authority_surfaces"] == []
    assert by_group["maintainability"]["hub_role"] == "adapter"
    assert by_group["maintainability"]["modifies_runtime_or_study_truth"] is False
    assert "product_entry_projection" in by_group["mas_core"]["forbidden_dependencies"]
    assert "mds_backend_oracle" in by_group["quality_os"]["forbidden_dependencies"]
    assert "src/med_autoscience/controllers/study_progress.py" in by_group["product_entry_projection"]["repo_targets"]
    assert "src/med_autoscience/controllers/audit_compaction_governance.py" in by_group["maintainability"]["repo_targets"]
    assert "src/med_autoscience/controllers/module_boundary_audit.py" in by_group["maintainability"]["repo_targets"]
    assert [item["boundary_id"] for item in report["truth_boundaries"]] == [
        "study_truth",
        "runtime_authority_refs",
        "quality_truth",
        "delivery_truth",
        "maintainability_truth",
    ]
    acceptance = report["target_architecture"]["high_aggregation_low_coupling_acceptance"]
    assert acceptance == {
        "all_repo_targets_grouped": True,
        "cross_group_dependencies_must_be_declared": True,
        "hub_roles_must_be_declared": True,
        "read_models_and_adapters_are_non_authority": True,
        "materializers_are_explicitly_scoped": True,
        "projection_authority_claims_allowed": False,
        "observability_direct_control_allowed": False,
        "mds_mas_authority_claims_allowed": False,
        "artifact_delivery_as_study_truth_allowed": False,
        "maintainability_truth_writes_allowed": False,
    }

    validation = module.validate_module_boundary_audit_report(report)

    assert validation["ok"] is True
    assert validation["issues"] == []


def test_module_boundary_audit_validation_fails_closed_on_authority_and_control_drift() -> None:
    module = importlib.import_module("med_autoscience.controllers.module_boundary_audit")
    report = module.build_module_boundary_audit_report()
    by_group = {group["group_id"]: group for group in report["module_groups"]}
    by_group["product_entry_projection"]["writable_authority_surfaces"] = ["user_visible_next_action"]
    by_group["product_entry_projection"]["may_be_study_truth"] = True
    by_group["observability_os"]["may_control_runtime"] = True
    by_group["observability_os"]["may_authorize_publication"] = True
    by_group["mds_backend_oracle"]["writable_authority_surfaces"] = [
        "publication_readiness",
        "runtime_health",
    ]
    by_group["mds_backend_oracle"]["may_control_runtime"] = True
    by_group["artifact_delivery"]["writable_authority_surfaces"] = [
        "artifact_authority",
        "study_truth",
    ]
    by_group["maintainability"]["writable_authority_surfaces"] = [
        "runtime_health",
        "progress_projection",
    ]
    by_group["maintainability"]["modifies_runtime_or_study_truth"] = True
    acceptance = report["target_architecture"]["high_aggregation_low_coupling_acceptance"]
    acceptance["projection_authority_claims_allowed"] = True
    acceptance["observability_direct_control_allowed"] = True
    acceptance["mds_mas_authority_claims_allowed"] = True
    acceptance["artifact_delivery_as_study_truth_allowed"] = True
    acceptance["maintainability_truth_writes_allowed"] = True

    validation = module.validate_module_boundary_audit_report(report)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} == {
        "projection_layer_claims_authority",
        "projection_layer_can_be_study_truth",
        "non_authority_hub_claims_authority",
        "non_authority_hub_controls_runtime_or_publication",
        "non_authority_hub_can_be_study_truth",
        "non_authority_hub_modifies_truth",
        "observability_direct_control",
        "mds_claims_mas_authority",
        "mds_claims_runtime_or_publication_authority",
        "artifact_delivery_becomes_study_truth",
        "maintainability_modifies_runtime_or_study_truth",
        "unknown_authority_surface",
        "acceptance_flag_not_fail_closed",
    }
