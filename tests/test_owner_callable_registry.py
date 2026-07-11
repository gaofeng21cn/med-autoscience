from __future__ import annotations

import importlib


EXPECTED_AUTHORITY_CALLABLES = {
    "publication_handoff_owner_gate": "publication_gate_owner",
    "complete_medical_paper_readiness_surface": "MedAutoScience",
    "return_to_ai_reviewer_workflow": "ai_reviewer",
    "run_external_learning_sidecar": "external_learning_sidecar",
}


def test_owner_callable_registry_contains_only_minimal_authority_callables() -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_callable_registry")

    registry = module.owner_callable_registry()

    assert len(registry) == 4
    assert {payload["action_type"]: owner for owner, payload in registry.items()} == (
        EXPECTED_AUTHORITY_CALLABLES
    )
    for owner, payload in registry.items():
        assert payload["owner"] == owner
        assert payload["callable_surface"]
        assert payload["required_inputs"]
        assert payload["required_outputs"]
        assert payload["artifact_delta_predicate"]
        assert payload["idempotency_scope"]
        assert payload["source_fingerprint_scope"]


def test_owner_callable_registry_rejects_domain_dispatch_actions() -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_callable_registry")

    for action_type in (
        "publication_gate_specificity_required",
        "run_quality_repair_batch",
        "unit_harmonized_external_validation_rerun",
        "recover_transport_model_provenance",
        "methodology_reframe_route_decision",
        "provenance_limited_harmonization_audit",
        "run_gate_clearing_batch",
        "sync_submission_minimal_delivery",
    ):
        assert module.owner_callable_for_action(action_type) is None


def test_owner_callable_registry_matches_authority_inventory_exactly() -> None:
    registry_module = importlib.import_module(
        "med_autoscience.controllers.owner_callable_registry"
    )
    inventory_module = importlib.import_module("med_autoscience.authority_kernel_inventory")

    registry_actions = {
        payload["action_type"] for payload in registry_module.owner_callable_registry().values()
    }
    inventory_actions = {
        ref.removeprefix("owner_callable:")
        for item in inventory_module.build_authority_kernel_inventory()["items"]
        for ref in item["active_caller_refs"]
        if ref.startswith("owner_callable:")
    }

    assert registry_actions == inventory_actions == set(EXPECTED_AUTHORITY_CALLABLES)
