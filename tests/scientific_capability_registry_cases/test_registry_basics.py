from __future__ import annotations

from tests.scientific_capability_registry_cases.common import (
    SCHOLARSKILLS_MODULE_IDS,
    importlib,
)


def test_scientific_capability_registry_resolves_current_delta_bound_candidates() -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    registry = module.build_scientific_capability_registry()
    capabilities = {
        item["capability_id"]: item for item in registry["capabilities"]
    }

    assert registry["surface_kind"] == "mas_scientific_capability_registry"
    assert registry["default_policy"]["fail_open"] is True
    assert registry["default_policy"]["always_on_scan"] is False
    assert registry["default_policy"]["wildcard_action_triggers_auto_select"] is False
    assert set(SCHOLARSKILLS_MODULE_IDS) <= set(capabilities)
    assert {
        "external_learning_authoring_advisory",
        "evo_scientist_progress_patterns",
        "light_external_skill_content_advisory",
        "co_scientist_current_owner_affordance",
        "reviewer_revision_feedbackops_oma_work_order",
        "nature_figure_display_contract_refs",
    } <= set(capabilities)

    resolution = module.resolve_scientific_capabilities(
        current_owner_delta={
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "repair-story",
            "work_unit_fingerprint": "sha256:repair",
        }
    )
    selected = {
        item["capability_id"]: item
        for item in resolution["selected_capabilities"]
    }

    assert resolution["status"] == "resolved"
    assert resolution["mainline_waits_for_capability"] is False
    assert resolution["missing_capability_blocks_owner_action"] is False
    assert selected
    for candidate in selected.values():
        assert candidate["refs_only"] is True
        assert candidate["can_block_current_owner_action"] is False
        assert candidate["authority_boundary"]["can_write_domain_truth"] is False
        assert candidate["authority_boundary"]["can_authorize_provider_admission"] is False


def test_scientific_capability_registry_wildcard_sidecars_require_explicit_capability_request() -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")

    implicit = module.resolve_scientific_capabilities(
        current_owner_delta={"action_type": "unknown_owner_action"}
    )
    assert implicit["status"] == "no_matching_capability"
    assert implicit["selected_capabilities"] == []

    explicit = module.resolve_scientific_capabilities(
        current_owner_delta={
            "action_type": "unknown_owner_action",
            "capability_families": ["progress_accelerator"],
        }
    )
    selected = {
        item["capability_id"]: item for item in explicit["selected_capabilities"]
    }
    patterns = selected["evo_scientist_progress_patterns"]
    assert patterns["wildcard_action_trigger_policy"]["auto_select"] is False
    assert patterns["wildcard_action_trigger_policy"][
        "requires_explicit_capability_request"
    ] is True
    assert patterns["descriptor_only"] is True
    assert patterns["can_block_current_owner_action"] is False


def test_registry_resolves_reviewer_revision_feedbackops_oma_cli_dispatch() -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    resolution = module.resolve_scientific_capabilities(
        current_owner_delta={
            "action_type": "reviewer_revision",
            "task_intent": "Major revision with OMA FeedbackOps coverage audit requirement.",
        }
    )
    selected = {
        item["capability_id"]: item
        for item in resolution["selected_capabilities"]
    }
    capability = selected["reviewer_revision_feedbackops_oma_work_order"]

    assert capability["invocation_kind"] == "mas_domain_feedbackops_dispatch_request"
    assert capability["callable_surface"] == (
        "med_autoscience.reviewer_revision_feedbackops_dispatch:"
        "build_reviewer_revision_feedbackops_dispatch_request"
    )
    assert "candidate:reviewer_revision_coverage_audit_ref" in capability["output_refs"]
    assert capability["authority_boundary"]["can_write_domain_truth"] is False
    assert capability["authority_boundary"]["can_write_owner_receipt"] is False
