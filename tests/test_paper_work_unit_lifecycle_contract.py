from __future__ import annotations

import importlib


def test_paper_work_unit_lifecycle_contract_declares_owner_writes_refs_and_completion_proof() -> None:
    registry = importlib.import_module("med_autoscience.runtime_control.owner_callable_registry")

    contract = registry.paper_work_unit_lifecycle_contract()
    quality_repair = contract["work_units"]["run_quality_repair_batch"]

    assert contract["surface_kind"] == "paper_work_unit_lifecycle_contract"
    assert quality_repair["owner"] == "quality_repair_batch"
    assert quality_repair["allowed_writes"] == [
        "paper/draft.md",
        "paper/build/review_manuscript.md",
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
        "artifacts/controller/quality_repair_batch/latest.json",
        "artifacts/controller/repair_execution_evidence/latest.json",
        "artifacts/supervision/requests/ai_reviewer/latest.json",
        "artifacts/controller/gate_replay_requests/latest.json",
    ]
    assert "artifacts/publication_eval/latest.json" in quality_repair["forbidden_writes"]
    assert "manuscript/current_package/**" in quality_repair["forbidden_writes"]
    assert quality_repair["required_input_refs"] == [
        "controller_decisions/latest.json",
        "publication_eval/latest.json",
        "paper_root",
    ]
    assert quality_repair["required_output_refs"] == [
        "paper/*",
        "artifacts/controller/quality_repair_batch/latest.json",
    ]
    assert quality_repair["completion_proof"]["requires_owner_receipt_or_typed_blocker"] is True
    assert quality_repair["completion_proof"]["required_refs"] == [
        "owner_receipt_ref",
        "required_output_ref",
        "artifact_delta_ref_or_gate_replay_ref_or_typed_blocker_ref",
    ]
    assert quality_repair["next_owner_rules"]["on_completed"] == [
        "ai_reviewer",
        "publication_gate",
        "delivery_sync",
        "controller_stop",
    ]
    assert quality_repair["next_owner_rules"]["on_blocked"] == [
        "write",
        "analysis_harmonization_owner",
        "source_provenance_owner",
        "decision",
        "awaiting_human",
    ]


def test_paper_work_unit_lifecycle_contract_resolves_action_specific_entry() -> None:
    registry = importlib.import_module("med_autoscience.runtime_control.owner_callable_registry")

    lifecycle = registry.paper_work_unit_lifecycle_for_action("return_to_ai_reviewer_workflow")

    assert lifecycle is not None
    assert lifecycle["owner"] == "ai_reviewer"
    assert lifecycle["allowed_writes"] == ["artifacts/publication_eval/latest.json"]
    assert "paper/**" in lifecycle["forbidden_writes"]
    assert "manuscript/current_package/**" in lifecycle["forbidden_writes"]
    assert lifecycle["completion_proof"]["currentness_required"] is True
