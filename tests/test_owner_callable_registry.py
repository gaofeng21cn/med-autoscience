from __future__ import annotations

import importlib


def test_owner_callable_registry_exposes_paper_progress_slo_owners() -> None:
    module = importlib.import_module("med_autoscience.runtime_control.owner_callable_registry")

    registry = module.owner_callable_registry()

    assert set(registry) == {
        "MAS/controller",
        "ai_reviewer",
        "publication_gate",
        "quality_repair_batch",
        "gate_clearing_batch",
        "delivery_sync",
    }
    for owner, payload in registry.items():
        assert payload["owner"] == owner
        assert payload["callable_surface"]
        assert payload["required_inputs"]
        assert payload["required_outputs"]
        assert payload["artifact_delta_predicate"]
        assert payload["idempotency_scope"]
        assert payload["source_fingerprint_scope"]


def test_owner_callable_registry_maps_actions_to_callable_surfaces() -> None:
    module = importlib.import_module("med_autoscience.runtime_control.owner_callable_registry")

    gate = module.owner_callable_for_action("run_gate_clearing_batch")
    ai_reviewer = module.owner_callable_for_action("return_to_ai_reviewer_workflow")
    delivery = module.owner_callable_for_action("sync_submission_minimal_delivery")

    assert gate["owner"] == "gate_clearing_batch"
    assert gate["gate_replay_target"] == "publication_gate.run_controller"
    assert ai_reviewer["owner"] == "ai_reviewer"
    assert ai_reviewer["required_outputs"] == ("artifacts/publication_eval/latest.json",)
    assert delivery["owner"] == "delivery_sync"
    assert delivery["artifact_delta_predicate"] == "submission_source_or_current_package_freshness_proof"
