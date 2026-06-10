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
    assert frameworks["academic_research_skills"]["closure_status"] == (
        "thin_projection_landed_worker_scaleout_gap"
    )
    assert frameworks["ark_progress_first"]["closure_status"] == "contract_only_gap"
    assert frameworks["aris"]["closure_status"] == "history_only_gap"
    assert frameworks["paperspine"]["closure_status"] == "not_landed_gap"
    assert frameworks["paperspine"]["owner_surface"] == "none"
    assert closure["counts"]["contract_or_projection_only_gap_count"] >= 3
    assert closure["counts"]["not_landed_gap_count"] == 1
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
    candidate_ids = {item["framework_id"] for item in result["advisory_candidates"] if "framework_id" in item}
    assert {"nature_skills", "paperspine", "co_scientist", "academic_research_skills"} <= candidate_ids
    assert "artifacts/publication_eval/latest.json" in result["forbidden_writes"]
    assert result["allowed_writes"] == ["artifacts/advisory/external_learning_sidecar/latest.json"]
    assert result["authority_boundary"]["can_write_controller_decisions"] is False
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()


def test_external_learning_sidecar_owner_action_executes_without_authority_writes(
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

    assert executed["execution_status"] == "executed"
    assert executed["blocked_reason"] is None
    assert request_path.is_file()
    assert result_path.is_file()
    assert output_readiness.required_output_pending(
        profile=profile,
        study_id=study_id,
        action_type="run_external_learning_sidecar",
        current_study={},
    ) is False
    assert not (study_root / "paper" / "draft.md").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()
