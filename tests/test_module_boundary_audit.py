from __future__ import annotations

import importlib

import pytest


pytestmark = pytest.mark.meta


def test_module_boundary_audit_report_declares_owner_and_authority_boundaries() -> None:
    module = importlib.import_module("med_autoscience.controllers.module_boundary_audit")

    report = module.build_module_boundary_audit_report()
    by_group = {group["group_id"]: group for group in report["module_groups"]}

    assert report["surface"] == "mas_mds_module_boundary_audit_report"
    assert list(by_group) == list(module.GROUP_IDS)
    assert by_group["mas_core"]["writable_authority_surfaces"] == [
        "study_truth",
        "user_visible_next_action",
    ]
    assert "publication_readiness" in by_group["quality_os"]["writable_authority_surfaces"]
    assert by_group["runtime_authority_refs"]["lifecycle_authority_owner"] == "one-person-lab"
    assert by_group["artifact_delivery"]["writable_authority_surfaces"] == ["artifact_authority"]
    for group_id in ("runtime_authority_refs", "product_entry_projection", "observability_os", "mds_backend_oracle"):
        group = by_group[group_id]
        assert group["writable_authority_surfaces"] == []
        assert group["may_control_runtime"] is False
    assert report["target_architecture"]["opl_progress_spine_owner"] == "one-person-lab"
    assert module.validate_module_boundary_audit_report(report)["ok"] is True


def test_module_boundary_audit_validation_fails_closed_on_authority_and_control_drift() -> None:
    module = importlib.import_module("med_autoscience.controllers.module_boundary_audit")
    report = module.build_module_boundary_audit_report()
    by_group = {group["group_id"]: group for group in report["module_groups"]}

    by_group["product_entry_projection"]["writable_authority_surfaces"] = ["user_visible_next_action"]
    by_group["product_entry_projection"]["may_be_study_truth"] = True
    by_group["observability_os"]["may_control_runtime"] = True
    by_group["observability_os"]["may_authorize_publication"] = True
    by_group["observability_os"]["may_select_tool_for_runtime"] = True
    by_group["mds_backend_oracle"]["writable_authority_surfaces"] = ["publication_readiness", "artifact_authority"]
    by_group["mds_backend_oracle"]["may_control_runtime"] = True
    by_group["artifact_delivery"]["writable_authority_surfaces"] += ["study_truth"]
    by_group["maintainability"]["writable_authority_surfaces"] = ["canonical_runtime_action", "progress_projection"]
    by_group["maintainability"]["modifies_runtime_or_study_truth"] = True
    by_group["runtime_authority_refs"]["owned_progress_spine_surfaces"] = ["transactional_outbox", "fixed_point_reconciler"]
    by_group["product_entry_projection"]["may_generate_workbench_action"] = True
    by_group["mas_core"]["writable_authority_surfaces"].append("provider_attempt")
    by_group["mas_core"]["may_authorize_provider_attempt"] = True
    report["target_architecture"]["high_aggregation_low_coupling_acceptance"][
        "projection_authority_claims_allowed"
    ] = True

    validation = module.validate_module_boundary_audit_report(report)
    issue_codes = {issue["code"] for issue in validation["issues"]}

    assert validation["ok"] is False
    assert issue_codes == {
        "projection_layer_claims_authority", "projection_layer_can_be_study_truth",
        "non_authority_hub_claims_authority", "non_authority_hub_controls_runtime_or_publication",
        "non_authority_hub_can_be_study_truth", "non_authority_hub_modifies_truth",
        "observability_direct_control", "mds_claims_mas_authority",
        "mds_claims_runtime_or_publication_authority", "artifact_delivery_becomes_study_truth",
        "maintainability_modifies_runtime_or_study_truth", "mas_claims_opl_runtime_lifecycle_authority",
        "mas_claims_opl_progress_spine_authority", "mas_private_progress_spine_capability_enabled",
        "unknown_authority_surface", "acceptance_flag_not_fail_closed",
    }
