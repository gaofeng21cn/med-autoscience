from __future__ import annotations

import importlib
import json
from pathlib import Path

from med_autoscience.controllers.domain_owner_action_dispatch_parts import dispatch_contract
from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study
from tests.test_domain_owner_action_dispatch_cases.ai_reviewer_workflow_dispatch import (
    _complete_ai_reviewer_input_refs,
    _minimal_ai_reviewer_record,
    _write_medical_prose_review_request_inputs,
)


def test_execute_dispatch_hands_off_stale_medical_prose_review_request_to_ai_reviewer(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_medical_prose_review_request_inputs(study_root, study_id=study_id)
    input_refs = _complete_ai_reviewer_input_refs(study_root)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "supervisor_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "input_contract": {
                "required_refs": input_refs,
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
            },
            "ai_reviewer_record": _minimal_ai_reviewer_record(
                study_id,
                f"quest-{study_id}",
                "publication-eval::002::quest::2026-05-17T00:00:00+00:00",
            ),
        },
    )
    handoff_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_current_dispatch(
        handoff_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="return_to_ai_reviewer_workflow",
            owner="ai_reviewer",
            required_output_surface="artifacts/publication_eval/latest.json",
        ),
    )

    def stale_medical_prose_review(**_kwargs) -> dict[str, object]:
        raise ValueError("medical_prose_review_request_digest_mismatch")

    monkeypatch.setattr(
        module.action_execution.ai_reviewer_publication_eval_workflow,
        "run_ai_reviewer_publication_eval_workflow",
        stale_medical_prose_review,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert result["codex_dispatch_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "handoff_ready"
    assert execution["blocked_reason"] is None
    assert execution["action_class"] == "codex_worker_dispatch"
    assert execution["will_start_llm"] is True
    assert execution["next_owner"] == "ai_reviewer"
    request_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"
    assert execution["required_input_surface"] == str(request_path)
    assert execution["error"] == "medical_prose_review_request_digest_mismatch"
    rehydrated = json.loads(request_path.read_text(encoding="utf-8"))
    assert rehydrated["surface"] == "medical_prose_review_request"
    assert rehydrated["request_currentness"]["status"] == "current"
    assert execution["owner_result"]["medical_prose_review_request_rehydrated"] is True
    assert execution["owner_result"]["rehydrated_request_ref"] == str(request_path.resolve())
    production_request = execution["ai_reviewer_medical_prose_review_production_request"]
    assert production_request["surface"] == "ai_reviewer_medical_prose_review_production_request"
    assert production_request["request_kind"] == "produce_ai_reviewer_medical_prose_review_against_current_request"
    assert production_request["request_owner"] == "ai_reviewer"
    assert production_request["required_input_refs"]["medical_prose_review_request"] == str(request_path.resolve())
    assert production_request["required_output_surface"] == "artifacts/publication_eval/medical_prose_review.json"
    assert production_request["owner_callable_surface"] == "publication materialize-ai-medical-prose-review"
    assert production_request["authority_contract"] == {
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "publication_eval_latest_write_allowed": False,
        "controller_decision_write_allowed": False,
        "medical_prose_review_only_surface": True,
    }
    assert "artifacts/publication_eval/latest.json" in production_request["forbidden_surfaces"]
    assert "artifacts/controller_decisions/latest.json" in production_request["forbidden_surfaces"]
    assert execution["next_required_actions"] == [
        "produce_ai_reviewer_medical_prose_review_against_current_request",
        "return_to_ai_reviewer_workflow",
    ]
    handoff = execution["ai_reviewer_medical_prose_review_worker_handoff"]
    assert handoff["surface"] == "default_executor_dispatch_request"
    assert handoff["dispatch_status"] == "ready"
    assert handoff["dispatch_authority"] == "ai_reviewer_medical_prose_review_production_handoff"
    assert handoff["next_executable_owner"] == "ai_reviewer"
    assert handoff["required_output_surface"] == "artifacts/publication_eval/medical_prose_review.json"
    assert handoff["prompt_contract"]["allowed_write_surfaces"] == [
        "artifacts/publication_eval/medical_prose_review.json",
    ]
    assert (
        dispatch_contract.prompt_contract_error(
            handoff["prompt_contract"],
            forbidden_surfaces=module.FORBIDDEN_SURFACES,
        )
        is None
    )
    assert "artifacts/publication_eval/latest.json" in handoff["forbidden_surfaces"]
    assert "artifacts/controller_decisions/latest.json" in handoff["forbidden_surfaces"]
    assert execution["ai_reviewer_medical_prose_review_worker_handoff_path"] == str(handoff_path)
    assert json.loads(handoff_path.read_text(encoding="utf-8"))["dispatch_authority"] == (
        "ai_reviewer_medical_prose_review_production_handoff"
    )
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
