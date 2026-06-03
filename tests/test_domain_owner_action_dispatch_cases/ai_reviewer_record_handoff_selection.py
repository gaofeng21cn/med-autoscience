from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study
from med_autoscience.controllers.domain_owner_action_dispatch_parts.action_execution_parts.ai_reviewer_record_production import (
    build_ai_reviewer_record_production_request,
    build_ai_reviewer_record_worker_handoff,
)


def test_execute_dispatch_prefers_persisted_record_only_handoff_over_stale_consumer_inline(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    manuscript_path = study_root / "paper" / "draft.md"
    request_payload = {
        "surface": "supervisor_action_request",
        "study_id": study_id,
        "quest_id": study_id,
        "request_kind": "return_to_ai_reviewer_workflow",
        "request_owner": "ai_reviewer",
        "request_lifecycle": {
            "state": "requested",
            "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
            "stale_record_ref": "publication-eval::stale-record",
            "required_currentness_refs": [str(manuscript_path)],
        },
        "input_contract": {
            "required_refs": {
                "manuscript": {"path": str(manuscript_path), "present": True, "valid": True},
                "evidence_ledger": {
                    "path": str(study_root / "paper" / "evidence_ledger.json"),
                    "present": True,
                    "valid": True,
                },
                "review_ledger": {
                    "path": str(study_root / "paper" / "review" / "review_ledger.json"),
                    "present": True,
                    "valid": True,
                },
                "study_charter": {
                    "path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                    "present": True,
                    "valid": True,
                },
            },
            "all_required_refs_present": True,
            "missing_or_invalid_refs": [],
        },
    }
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        request_payload,
    )
    route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    route.update(
        {
            "failure_signature": "ai_reviewer_record_stale_after_current_manuscript",
            "owner_reason": "ai_reviewer_record_stale_after_current_manuscript",
            "source_refs": {
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
            },
        }
    )
    stale_inline_dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=route,
    )
    production_request = build_ai_reviewer_record_production_request(
        request=request_payload,
        required_refs={
            "manuscript": str(manuscript_path),
            "evidence_ledger": str(study_root / "paper" / "evidence_ledger.json"),
            "review_ledger": str(study_root / "paper" / "review" / "review_ledger.json"),
            "study_charter": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        },
        stale_record_ref="publication-eval::stale-record",
        required_currentness_refs=[str(manuscript_path)],
        request_kind="produce_ai_reviewer_publication_eval_record_against_current_manuscript",
    )
    persisted_handoff = build_ai_reviewer_record_worker_handoff(
        profile=profile,
        study_id=study_id,
        request=request_payload,
        dispatch=stale_inline_dispatch,
        production_request=production_request,
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    stale_inline_dispatch["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_current_dispatch(dispatch_path, profile, persisted_handoff)
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [stale_inline_dispatch],
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["execution_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "dry_run"
    assert execution["dispatch_authority"] == "ai_reviewer_record_production_handoff"
    assert execution["required_output_surface"] == (
        "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
    )
    assert execution["owner_callable_surface"] == "publication materialize-ai-reviewer-record"
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
