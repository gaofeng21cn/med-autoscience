from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def test_external_learning_adoption_closure_separates_contracts_from_worker_landing() -> None:
    module = importlib.import_module("med_autoscience.external_learning_adoption_closure")

    closure = module.build_external_learning_adoption_closure()
    frameworks = {item["framework_id"]: item for item in closure["frameworks"]}

    assert closure["surface_kind"] == "mas_external_learning_adoption_closure"
    assert closure["completion_definition"] == {
        "contract_only_is_not_landed": True,
        "landed_requires_execution_slot_or_owner_surface": True,
        "worker_or_executor_must_declare_allowed_writes": True,
        "worker_or_executor_must_preserve_forbidden_authority": True,
        "tests_must_cover_nonblocking_refs_only_behavior": True,
    }
    assert closure["progress_first_friction_guard"] == {
        "mainline_waits_for_sidecar": False,
        "sidecar_missing_blocks_dispatch": False,
        "sidecar_failure_blocks_current_owner_action": False,
        "sidecar_budget_exhaustion_blocks_owner_action": False,
        "owner_policy_wins": True,
        "advisory_refs_count_as_paper_progress": False,
    }

    assert frameworks["evo_scientist_evoskills"]["closure_status"] == (
        "sidecar_execution_slot_landed"
    )
    for framework_id in (
        "academic_research_skills",
        "autosci_omegawiki",
        "ark_progress_first",
        "aris",
        "paperspine",
        "paperorchestra",
    ):
        assert frameworks[framework_id]["closure_status"] == "sidecar_or_worker_landed"
        assert "sidecar" in frameworks[framework_id]["owner_surface"]
    assert closure["counts"]["framework_count"] == 10
    assert closure["counts"]["sidecar_execution_slot_count"] == 7
    assert closure["counts"]["contract_or_projection_only_gap_count"] == 0
    assert closure["counts"]["not_landed_gap_count"] == 0
    for framework in frameworks.values():
        assert framework["friction_policy"]["can_block_current_owner_action"] is False
        assert framework["authority_boundary"]["can_write_publication_eval"] is False
        assert framework["authority_boundary"]["can_authorize_publication_quality"] is False


def test_external_learning_sidecar_apply_writes_only_refs_only_advisory_result(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.external_learning_adoption_closure")
    study_root = tmp_path / "studies" / "001-risk"
    dispatch = {
        "action_type": "run_quality_repair_batch",
        "action_id": "dispatch-001",
        "refs": {"dispatch_path": "artifacts/supervision/consumer/current.json"},
        "owner_route": {
            "owner": "quality_repair_batch",
            "work_unit_id": "repair-manuscript-story",
            "work_unit_fingerprint": "fingerprint-001",
        },
    }

    result = module.run_external_learning_sidecar(
        study_root=study_root,
        dispatch=dispatch,
        apply=True,
    )
    result_path = study_root / module.SIDECAR_RESULT_RELATIVE_PATH

    assert result_path.is_file()
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert payload == result
    assert result["surface_kind"] == "mas_external_learning_sidecar_result"
    assert result["status"] == "executed"
    assert result["refs_only"] is True
    assert result["body_included"] is False
    assert result["mainline_waits_for_sidecar"] is False
    assert result["can_block_current_owner_action"] is False
    assert result["current_owner_action"]["action_type"] == "run_quality_repair_batch"
    candidate_ids = {
        item["framework_id"] for item in result["advisory_candidates"] if "framework_id" in item
    }
    assert {
        "nature_skills",
        "paperspine",
        "paperorchestra",
        "co_scientist",
        "academic_research_skills",
    } <= candidate_ids
    worker_ids = {item["framework_id"] for item in result["advisory_worker_results"]}
    assert {"paperspine", "paperorchestra", "academic_research_skills"} <= worker_ids
    assert all(item["refs_only"] is True for item in result["advisory_worker_results"])
    assert all(item["body_included"] is False for item in result["advisory_worker_results"])
    assert all(
        item["can_block_current_owner_action"] is False
        for item in result["advisory_worker_results"]
    )
    assert "artifacts/publication_eval/latest.json" in result["forbidden_writes"]
    assert result["allowed_writes"] == ["artifacts/advisory/external_learning_sidecar/latest.json"]
    assert result["authority_boundary"]["can_write_controller_decisions"] is False
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()


def test_external_learning_sidecar_runs_registered_generators_fail_open(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.external_learning_adoption_closure")
    study_root = tmp_path / "studies" / "001-risk"
    dispatch = {
        "action_type": "unit_harmonized_external_validation_rerun",
        "action_id": "dispatch-001",
        "refs": {"dispatch_path": "artifacts/supervision/consumer/current.json"},
        "owner_route": {
            "owner": "source_truth",
            "work_unit_id": "external-validation",
            "work_unit_fingerprint": "fingerprint-001",
        },
    }

    result = module.run_external_learning_sidecar(
        study_root=study_root,
        dispatch=dispatch,
        apply=False,
    )

    worker_results = {item["framework_id"]: item for item in result["advisory_worker_results"]}
    assert {"aris", "ark_progress_first", "autosci_omegawiki"} <= set(worker_results)
    assert worker_results["ark_progress_first"]["micro_canary_ref"] == (
        "external-learning:ark_progress_first:dispatch-001:micro_canary"
    )
    assert worker_results["autosci_omegawiki"]["source_candidate_proposal_refs"] == [
        "external-learning:autosci_omegawiki:dispatch-001:source_candidate_proposal"
    ]
    assert worker_results["aris"]["typed_input_contract_ref"] == (
        "external-learning:aris:fingerprint-001:typed-input-contract"
    )
    for item in worker_results.values():
        assert item["refs_only"] is True
        assert item["body_included"] is False
        assert item["allowed_writes"] == []
        assert item["authority_boundary"]["can_write_publication_eval"] is False
        assert item["authority_boundary"]["can_authorize_publication_quality"] is False
        assert item["can_block_current_owner_action"] is False


def test_external_learning_authoring_and_review_workers_do_not_write_files(tmp_path: Path) -> None:
    authoring = importlib.import_module("med_autoscience.external_learning_authoring_advisory")
    review = importlib.import_module("med_autoscience.external_learning_review_advisory")
    progress = importlib.import_module("med_autoscience.external_learning_progress_workers")
    dispatch = {
        "action_type": "run_quality_repair_batch",
        "action_id": "dispatch-authoring",
        "owner_route": {"owner": "write", "work_unit_id": "manuscript-story"},
        "refs": {
            "motivation_spine_refs": ["ref:motivation-spine"],
            "writing_rationale_matrix_refs": ["ref:writing-rationale"],
            "evidence_blueprint_refs": ["ref:evidence-blueprint"],
            "latex_safe_audit_refs": ["ref:latex-safe"],
            "authoring_dag_refs": ["ref:authoring-dag"],
            "outline_plot_refs": ["ref:outline-plot"],
            "literature_section_refs": ["ref:literature-section"],
            "autorater_refs": ["ref:autorater"],
        },
    }

    assert list(tmp_path.rglob("*")) == []
    paperspine = authoring.build_paperspine_manuscript_advisory(dispatch)
    paperorchestra = authoring.build_paperorchestra_authoring_advisory(dispatch)
    ars = review.build_ars_claim_support_advisory(dispatch)
    aris = review.build_aris_review_import_advisory(dispatch)
    ark = progress.build_ark_progress_worker_advisory(dispatch)
    autosci = progress.build_autosci_source_experiment_advisory(dispatch)

    assert paperspine["status"] == "advisory_ready"
    assert paperorchestra["status"] == "advisory_ready"
    assert ars["status"] == "ready"
    assert aris["status"] == "ready"
    assert ark["status"] == "candidate_refs_emitted"
    assert autosci["status"] == "candidate_refs_emitted"
    for item in (paperspine, paperorchestra, ars, aris, ark, autosci):
        assert item["allowed_writes"] == []
        assert item["refs_only"] is True
        assert item["body_included"] is False
        assert item["can_block_current_owner_action"] is False
    assert list(tmp_path.rglob("*")) == []


def test_external_learning_sidecar_owner_action_writes_opl_request_only(
    tmp_path: Path,
) -> None:
    router = importlib.import_module(
        "med_autoscience.controllers.domain_owner_action_dispatch_parts.action_router"
    )
    output_readiness = importlib.import_module(
        "med_autoscience.controllers.domain_owner_action_dispatch_parts.output_readiness"
    )
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-001")
    dispatch = {
        "action_type": "run_external_learning_sidecar",
        "action_id": "dispatch-external-learning",
        "owner_route": {
            "owner": "external_learning_sidecar",
            "work_unit_id": "external-learning-advisory",
            "work_unit_fingerprint": "external-learning-fingerprint",
        },
        "refs": {"dispatch_path": "artifacts/supervision/consumer/current.json"},
    }

    dry_run = router.execute_owner_dispatch_action(
        profile=profile,
        study_id=study_id,
        action_type="run_external_learning_sidecar",
        dispatch=dispatch,
        apply=False,
        execute_publication_gate_specificity=lambda **_: {},
        execute_ai_reviewer_workflow=lambda **_: {},
        quest_root_resolver=lambda *_: None,
    )
    assert dry_run["execution_status"] == "dry_run"
    assert dry_run["status"] == "opl_capability_request_preview"
    assert dry_run["request_only"] is True
    assert dry_run["mas_local_capability_actuator"] is False
    assert dry_run["opl_capability_runtime_required"] is True
    assert not (study_root / "artifacts" / "advisory" / "external_learning_sidecar" / "latest.json").exists()

    executed = router.execute_owner_dispatch_action(
        profile=profile,
        study_id=study_id,
        action_type="run_external_learning_sidecar",
        dispatch=dispatch,
        apply=True,
        execute_publication_gate_specificity=lambda **_: {},
        execute_ai_reviewer_workflow=lambda **_: {},
        quest_root_resolver=lambda *_: None,
    )
    request_path = study_root / "artifacts/supervision/requests/external_learning_sidecar/latest.json"
    result_path = study_root / "artifacts/advisory/external_learning_sidecar/latest.json"

    assert executed["execution_status"] == "blocked"
    assert executed["blocked_reason"] == "opl_capability_runtime_required"
    assert executed["typed_blocker"]["owner"] == "one-person-lab"
    assert executed["status"] == "opl_capability_request_pending"
    assert executed["request_only"] is True
    assert executed["mas_local_capability_actuator"] is False
    assert executed["mas_can_invoke_capability_sidecar"] is False
    assert executed["opl_capability_runtime_required"] is True
    assert executed["provider_admission_pending"] is False
    assert request_path.is_file()
    assert not result_path.exists()
    assert output_readiness.required_output_pending(
        profile=profile,
        study_id=study_id,
        action_type="run_external_learning_sidecar",
        current_study={},
    ) is True
    assert not (study_root / "paper" / "draft.md").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()
