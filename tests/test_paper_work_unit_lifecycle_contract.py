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


def test_paper_work_unit_lifecycle_contract_declares_publication_handoff_owner_gate() -> None:
    registry = importlib.import_module("med_autoscience.runtime_control.owner_callable_registry")

    lifecycle = registry.paper_work_unit_lifecycle_for_action("publication_handoff_owner_gate")

    assert lifecycle is not None
    assert lifecycle["owner"] == "publication_gate_owner"
    assert lifecycle["allowed_writes"] == [
        "artifacts/stage_outputs/08-publication_package_handoff/handoff_owner_receipt.json",
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/owner_receipt.json",
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
        "artifacts/stage_outputs/08-publication_package_handoff/stage_manifest.json",
        "artifacts/stage_outputs/08-publication_package_handoff/current.json",
        "artifacts/stage_outputs/08-publication_package_handoff/projection/current_owner_delta.json",
    ]
    assert "artifacts/publication_eval/latest.json" in lifecycle["forbidden_writes"]
    assert "controller_decisions/latest.json" in lifecycle["forbidden_writes"]
    assert lifecycle["completion_proof"]["publication_ready_claim_authorized"] is False
    assert lifecycle["completion_proof"]["submission_ready_claim_authorized"] is False
    assert lifecycle["completion_proof"]["terminal_projection_writer"] == (
        "publication_handoff_stage_projection.py"
    )


def test_paper_work_unit_lifecycle_contract_declares_readiness_stage_native_closeout_writes() -> None:
    registry = importlib.import_module("med_autoscience.runtime_control.owner_callable_registry")

    lifecycle = registry.paper_work_unit_lifecycle_for_action(
        "complete_medical_paper_readiness_surface"
    )

    assert lifecycle is not None
    assert lifecycle["owner"] == "MedAutoScience"
    assert lifecycle["allowed_writes"] == [
        "artifacts/medical_paper/readiness.json",
        "artifacts/medical_paper/*.json",
        "artifacts/medical_paper/actions/**",
        "artifacts/controller_decisions/latest.json",
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/owner_receipt.json",
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
        "artifacts/stage_outputs/08-publication_package_handoff/stage_manifest.json",
        "artifacts/stage_outputs/08-publication_package_handoff/current.json",
        "artifacts/stage_outputs/08-publication_package_handoff/projection/current_owner_delta.json",
    ]
    assert (
        "artifacts/stage_outputs/08-publication_package_handoff/handoff_owner_receipt.json"
        in lifecycle["forbidden_writes"]
    )
    assert lifecycle["completion_proof"][
        "terminal_stage_owner_answer_requires_trusted_opl_binding"
    ] is True
    assert lifecycle["completion_proof"]["terminal_projection_writer"] == (
        "publication_handoff_stage_projection.py"
    )
