from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


FRAMEWORK_IDS = {
    "kdense_byok",
    "openscience_artifact_provenance",
    "co_scientist",
    "nature_skills",
    "academicforge_claude_science",
    "academic_research_skills",
    "autosci_omegawiki",
    "evo_scientist_evoskills",
    "ark_progress_first",
    "aris",
    "paperspine",
    "paperorchestra",
    "open_auto_research",
}
WORKER_IDS = {
    "paperspine",
    "paperorchestra",
    "academic_research_skills",
    "aris",
    "ark_progress_first",
    "autosci_omegawiki",
    "kdense_byok",
    "openscience_artifact_provenance",
}


def test_external_learning_adoption_closure_keeps_landing_current_and_non_authoritative() -> None:
    module = importlib.import_module("med_autoscience.external_learning_adoption_closure")
    closure = module.build_external_learning_adoption_closure()
    frameworks = {
        item["framework_id"]: item for item in closure["frameworks"]
    }

    assert closure["surface_kind"] == "mas_external_learning_adoption_closure"
    assert set(frameworks) == FRAMEWORK_IDS
    assert closure["counts"]["framework_count"] == len(FRAMEWORK_IDS)
    assert closure["counts"]["contract_or_projection_only_gap_count"] == 0
    assert closure["counts"]["not_landed_gap_count"] == 0
    assert set(module.SIDECAR_WORKER_REGISTRY) == WORKER_IDS
    assert "nature_skills" not in module.SIDECAR_WORKER_REGISTRY

    for framework in frameworks.values():
        assert framework["friction_policy"]["can_block_current_owner_action"] is False
        assert framework["authority_boundary"]["can_write_publication_eval"] is False
        assert framework["authority_boundary"][
            "can_authorize_publication_quality"
        ] is False
    assert closure["authority_boundary"]["can_write_domain_truth"] is False
    assert closure["authority_boundary"]["can_write_owner_receipt"] is False
    assert closure["authority_boundary"]["can_close_stage"] is False


def test_external_learning_sidecar_apply_writes_only_refs_only_advisory_result(
    tmp_path: Path,
) -> None:
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
    worker_results = {
        item["framework_id"]: item for item in result["advisory_worker_results"]
    }
    candidate_worker_ids = {
        item["framework_id"]
        for item in result["advisory_candidates"]
        if item.get("framework_id") in module.SIDECAR_WORKER_REGISTRY
    }

    assert json.loads(result_path.read_text(encoding="utf-8")) == result
    assert result["status"] == "executed"
    assert result["refs_only"] is True
    assert result["body_included"] is False
    assert result["mainline_waits_for_sidecar"] is False
    assert result["can_block_current_owner_action"] is False
    assert result["allowed_writes"] == [str(module.SIDECAR_RESULT_RELATIVE_PATH)]
    assert set(worker_results) == candidate_worker_ids
    for worker in worker_results.values():
        assert worker["refs_only"] is True
        assert worker["body_included"] is False
        assert worker["allowed_writes"] == []
        assert worker["can_block_current_owner_action"] is False
        assert worker["authority_boundary"]["can_write_publication_eval"] is False
        assert worker["authority_boundary"][
            "can_authorize_publication_quality"
        ] is False

    written_files = sorted(
        str(path.relative_to(study_root))
        for path in study_root.rglob("*")
        if path.is_file()
    )
    assert written_files == [str(module.SIDECAR_RESULT_RELATIVE_PATH)]


def test_external_learning_sidecar_owner_action_writes_opl_request_only(
    tmp_path: Path,
) -> None:
    router = importlib.import_module(
        "med_autoscience.controllers.stage_outcome_authority.action_router"
    )
    output_readiness = importlib.import_module(
        "med_autoscience.controllers.stage_outcome_authority.output_readiness"
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
    assert dry_run["status"] == "opl_capability_request_preview"
    assert dry_run["request_only"] is True
    assert dry_run["mas_local_capability_actuator"] is False

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
    request_path = (
        study_root
        / "artifacts/supervision/requests/external_learning_sidecar/latest.json"
    )

    assert executed["execution_status"] == "blocked"
    assert executed["blocked_reason"] == "opl_capability_runtime_required"
    assert executed["typed_blocker"]["owner"] == "one-person-lab"
    assert executed["status"] == "opl_capability_request_pending"
    assert executed["request_only"] is True
    assert executed["mas_can_invoke_capability_sidecar"] is False
    assert executed["opl_capability_runtime_required"] is True
    assert request_path.is_file()
    assert output_readiness.required_output_pending(
        profile=profile,
        study_id=study_id,
        action_type="run_external_learning_sidecar",
        current_study={},
    ) is True
    assert not (
        study_root / "artifacts/advisory/external_learning_sidecar/latest.json"
    ).exists()
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
