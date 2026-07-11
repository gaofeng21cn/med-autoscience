from __future__ import annotations

import importlib


def test_paper_work_unit_lifecycle_contract_contains_only_minimal_authority_callables() -> None:
    registry = importlib.import_module("med_autoscience.controllers.owner_callable_registry")

    contract = registry.paper_work_unit_lifecycle_contract()

    assert contract["surface_kind"] == "paper_work_unit_lifecycle_contract"
    assert set(contract["work_units"]) == {
        "publication_handoff_owner_gate",
        "complete_medical_paper_readiness_surface",
        "return_to_ai_reviewer_workflow",
        "run_external_learning_sidecar",
    }
    assert registry.paper_work_unit_lifecycle_for_action("run_quality_repair_batch") is None


def test_paper_work_unit_lifecycle_contract_resolves_action_specific_entry() -> None:
    registry = importlib.import_module("med_autoscience.controllers.owner_callable_registry")

    lifecycle = registry.paper_work_unit_lifecycle_for_action("return_to_ai_reviewer_workflow")

    assert lifecycle is not None
    assert lifecycle["owner"] == "ai_reviewer"
    assert lifecycle["allowed_writes"] == ["artifacts/publication_eval/latest.json"]
    assert "paper/**" in lifecycle["forbidden_writes"]
    assert "manuscript/current_package/**" in lifecycle["forbidden_writes"]
    assert lifecycle["completion_proof"]["currentness_required"] is True


def test_paper_work_unit_lifecycle_contract_declares_publication_handoff_owner_gate() -> None:
    registry = importlib.import_module("med_autoscience.controllers.owner_callable_registry")

    lifecycle = registry.paper_work_unit_lifecycle_for_action("publication_handoff_owner_gate")

    assert lifecycle is not None
    assert lifecycle["owner"] == "publication_gate_owner"
    assert lifecycle["allowed_writes"] == [
        "artifacts/publication_handoff/owner_receipt.json",
        "artifacts/publication_handoff/typed_blocker.json",
    ]
    assert "artifacts/publication_eval/latest.json" in lifecycle["forbidden_writes"]
    assert "controller_decisions/latest.json" in lifecycle["forbidden_writes"]
    assert lifecycle["completion_proof"]["publication_ready_claim_authorized"] is False
    assert lifecycle["completion_proof"]["submission_ready_claim_authorized"] is False
    assert lifecycle["completion_proof"]["opl_consumes_action_result_refs"] is True


def test_paper_work_unit_lifecycle_contract_declares_readiness_stage_native_closeout_writes() -> None:
    registry = importlib.import_module("med_autoscience.controllers.owner_callable_registry")

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
    ]
    assert "artifacts/stage_outputs/**" in lifecycle["forbidden_writes"]
    assert lifecycle["completion_proof"][
        "terminal_stage_owner_answer_requires_trusted_opl_binding"
    ] is True
    assert lifecycle["completion_proof"]["opl_consumes_action_result_refs"] is True


def test_paper_work_unit_lifecycle_contract_declares_external_learning_sidecar_nonblocking() -> None:
    registry = importlib.import_module("med_autoscience.controllers.owner_callable_registry")

    lifecycle = registry.paper_work_unit_lifecycle_for_action("run_external_learning_sidecar")

    assert lifecycle is not None
    assert lifecycle["owner"] == "external_learning_sidecar"
    assert lifecycle["allowed_writes"] == [
        "artifacts/supervision/requests/external_learning_sidecar/latest.json",
        "artifacts/advisory/external_learning_sidecar/latest.json",
    ]
    assert "artifacts/publication_eval/latest.json" in lifecycle["forbidden_writes"]
    assert "artifacts/controller_decisions/latest.json" in lifecycle["forbidden_writes"]
    assert "paper/**" in lifecycle["forbidden_writes"]
    assert lifecycle["completion_proof"] == {
        "requires_owner_receipt_or_typed_blocker": False,
        "refs_only_advisory": True,
        "mainline_waits_for_sidecar": False,
        "publication_ready_claim_authorized": False,
        "submission_ready_claim_authorized": False,
        "artifact_authority_authorized": False,
    }
    assert lifecycle["next_owner_rules"] == {
        "on_completed": ["current_owner_action_continues"],
        "on_blocked": ["current_owner_action_continues"],
    }
