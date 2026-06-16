from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study
from tests.test_domain_owner_action_dispatch_cases.ai_reviewer_workflow_helpers import (
    _complete_ai_reviewer_input_refs,
)


def test_execute_dispatch_blocks_ai_reviewer_when_request_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        dispatch,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 1
    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "ai_reviewer_request_missing"
    assert execution["owner_callable_surface"] == "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
    assert execution["next_owner"] == "ai_reviewer"
    latest = json.loads(
        (
            study_root
            / "artifacts"
            / "supervision"
            / "consumer"
            / "default_executor_execution"
            / "latest.json"
        ).read_text(encoding="utf-8")
    )
    assert latest["blocked_count"] == 1
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "manuscript").exists()


def test_provider_hosted_stage_attempt_identity_authorizes_ai_reviewer_dispatch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "supervisor_request_handoff_packet",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {"blocked_reason": "paper_authority_clean_migration_required"},
            "input_contract": {
                "required_refs": _complete_ai_reviewer_input_refs(study_root),
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
            },
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "immutable"
        / "return_to_ai_reviewer_workflow"
        / "provider-hosted.json"
    )
    route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    route["source_refs"] = {
        "work_unit_id": "truth-snapshot::ai-reviewer-recheck",
        "blocked_reason": "paper_authority_clean_migration_required",
    }
    dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=route,
    )
    dispatch.pop("opl_execution_authorization", None)
    dispatch["prompt_contract"].pop("opl_execution_authorization", None)
    _write_current_dispatch(dispatch_path, profile, dispatch)
    monkeypatch.setenv("OPL_STAGE_ATTEMPT_ID", "sat-provider-hosted")
    monkeypatch.setenv("OPL_PROVIDER_ATTEMPT_REF", "opl://stage-attempts/sat-provider-hosted")
    monkeypatch.setenv(
        "OPL_ATTEMPT_LEASE_REF",
        "opl://stage-attempts/sat-provider-hosted/leases/frt-provider-hosted/active",
    )
    monkeypatch.setenv("OPL_ATTEMPT_LEASE_STATUS", "active")
    monkeypatch.setenv(
        "OPL_EXECUTION_AUTHORIZATION_DECISION_REF",
        "opl://stage-attempts/sat-provider-hosted/execution-authorizations/frt-provider-hosted/current",
    )
    monkeypatch.setenv("OPL_STAGE_ID", "domain_owner/default-executor-dispatch")
    monkeypatch.setenv("OPL_STAGE_PACKET_REF", str(dispatch_path))
    monkeypatch.setenv("OPL_STUDY_ID", study_id)
    monkeypatch.setenv("OPL_ACTION_TYPE", "return_to_ai_reviewer_workflow")
    monkeypatch.setenv("OPL_WORK_UNIT_ID", "truth-snapshot::ai-reviewer-recheck")
    monkeypatch.setenv("OPL_TASK_ID", "frt-provider-hosted")
    called: dict[str, object] = {}

    def fake_execute_ai_reviewer_workflow(**kwargs):
        called.update(kwargs)
        return {
            "execution_status": "handoff_ready",
            "blocked_reason": None,
            "owner_callable_surface": "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow",
            "next_owner": "ai_reviewer",
        }

    monkeypatch.setattr(module, "_execute_ai_reviewer_workflow", fake_execute_ai_reviewer_workflow)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 0, result
    assert result["handoff_ready_count"] == 1
    assert result["blocked_count"] == 0
    execution = result["executions"][0]
    assert execution["execution_status"] == "handoff_ready"
    assert execution["blocked_reason"] is None
    assert execution["owner_callable_surface"] == "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
    assert called["study_id"] == study_id
    assert Path(called["dispatch"]["refs"]["dispatch_path"]) == dispatch_path


def test_provider_hosted_stage_attempt_identity_mismatch_keeps_ai_reviewer_dispatch_blocked(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "immutable"
        / "return_to_ai_reviewer_workflow"
        / "provider-hosted.json"
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
    )
    dispatch.pop("opl_execution_authorization", None)
    dispatch["prompt_contract"].pop("opl_execution_authorization", None)
    _write_current_dispatch(dispatch_path, profile, dispatch)
    monkeypatch.setenv("OPL_STAGE_ATTEMPT_ID", "sat-provider-hosted")
    monkeypatch.setenv("OPL_PROVIDER_ATTEMPT_REF", "opl://stage-attempts/sat-provider-hosted")
    monkeypatch.setenv(
        "OPL_ATTEMPT_LEASE_REF",
        "opl://stage-attempts/sat-provider-hosted/leases/frt-provider-hosted/active",
    )
    monkeypatch.setenv("OPL_ATTEMPT_LEASE_STATUS", "active")
    monkeypatch.setenv(
        "OPL_EXECUTION_AUTHORIZATION_DECISION_REF",
        "opl://stage-attempts/sat-provider-hosted/execution-authorizations/frt-provider-hosted/current",
    )
    monkeypatch.setenv("OPL_STAGE_ID", "domain_owner/default-executor-dispatch")
    monkeypatch.setenv("OPL_STAGE_PACKET_REF", str(dispatch_path) + ".stale")
    monkeypatch.setenv("OPL_STUDY_ID", study_id)
    monkeypatch.setenv("OPL_ACTION_TYPE", "return_to_ai_reviewer_workflow")

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 1
    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "opl_execution_authorization_required"
    assert execution["owner_callable_surface"] is None
