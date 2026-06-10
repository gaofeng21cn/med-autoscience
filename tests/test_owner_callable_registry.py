from __future__ import annotations

import importlib


def test_owner_callable_registry_exposes_paper_progress_slo_owners() -> None:
    module = importlib.import_module("med_autoscience.runtime_control.owner_callable_registry")

    registry = module.owner_callable_registry()

    assert set(registry) == {
        "MedAutoScience",
        "MAS/controller",
        "analysis_harmonization_owner",
        "ai_reviewer",
        "decision",
        "publication_gate",
        "publication_gate_owner",
        "provenance_limited_harmonization_owner",
        "quality_repair_batch",
        "source_provenance_owner",
        "gate_clearing_batch",
        "delivery_sync",
        "external_learning_sidecar",
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
    harmonization = module.owner_callable_for_action("unit_harmonized_external_validation_rerun")
    provenance = module.owner_callable_for_action("recover_transport_model_provenance")
    methodology_reframe = module.owner_callable_for_action("methodology_reframe_route_decision")
    provenance_limited = module.owner_callable_for_action("provenance_limited_harmonization_audit")
    delivery = module.owner_callable_for_action("sync_submission_minimal_delivery")
    handoff = module.owner_callable_for_action("publication_handoff_owner_gate")
    readiness = module.owner_callable_for_action("complete_medical_paper_readiness_surface")
    external_learning = module.owner_callable_for_action("run_external_learning_sidecar")

    assert gate["owner"] == "gate_clearing_batch"
    assert gate["gate_replay_target"] == "publication_gate.run_controller"
    assert ai_reviewer["owner"] == "ai_reviewer"
    assert ai_reviewer["required_outputs"] == ("artifacts/publication_eval/latest.json",)
    assert harmonization["owner"] == "analysis_harmonization_owner"
    assert harmonization["artifact_delta_predicate"] == (
        "unit_harmonized_rerun_evidence_or_analysis_owner_typed_blocker"
    )
    assert provenance["owner"] == "source_provenance_owner"
    assert provenance["required_outputs"] == (
        "canonical transport model provenance bundle",
        "typed blocker:transport_model_provenance_recovery_required",
    )
    assert methodology_reframe["owner"] == "decision"
    assert methodology_reframe["callable_surface"] == "decision_owner.methodology_reframe_route_decision"
    assert provenance_limited["owner"] == "provenance_limited_harmonization_owner"
    assert provenance_limited["artifact_delta_predicate"] == "provenance_limited_audit_or_route_typed_blocker"
    assert delivery["owner"] == "delivery_sync"
    assert delivery["artifact_delta_predicate"] == "submission_source_or_current_package_freshness_proof"
    assert handoff["owner"] == "publication_gate_owner"
    assert handoff["required_outputs"] == (
        "artifacts/stage_outputs/08-publication_package_handoff/handoff_owner_receipt.json",
        "typed blocker:publication_handoff_owner_gate_blocked",
    )
    assert readiness["owner"] == "MedAutoScience"
    assert readiness["callable_surface"] == "medical_paper_readiness.complete_medical_paper_readiness_surface"
    assert external_learning["owner"] == "external_learning_sidecar"
    assert external_learning["callable_surface"] == (
        "external_learning_sidecar.run_external_learning_sidecar"
    )
    assert external_learning["required_outputs"] == (
        "artifacts/advisory/external_learning_sidecar/latest.json",
        "refs-only advisory candidates",
    )
