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


def test_execute_dispatch_allows_one_retry_then_suppresses_after_anti_loop_budget_and_indexes_receipt(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    route.update(
        {
            "schema_version": 2,
            "truth_epoch": route["route_epoch"],
            "runtime_health_epoch": "runtime-health-repeat",
            "work_unit_fingerprint": "publication-blockers::repeat-executor",
            "failure_signature": "ai_reviewer_assessment_required",
            "trace_id": "owner-route-trace::repeat-executor",
        }
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=route,
    )
    dispatch_payload["prompt_contract"].update(
        {
            "prompt_budget": {"max_prompt_tokens": 6000},
            "compact_evidence_packet_ref": "artifacts/supervision/compact_evidence_packets/return_to_ai_reviewer_workflow.json",
            "do_not_repeat": True,
            "repeat_suppression_key": "publication-blockers::repeat-executor",
        }
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch_payload)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": route,
                    "meaningful_artifact_delta": False,
                }
            ],
        },
    )
    legacy_execution_latest_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json"
    )
    execution_latest_path = study_root / module.EXECUTION_LATEST_RELATIVE_PATH
    prior_failure = {
        "surface": "default_executor_dispatch_execution",
        "study_id": study_id,
        "quest_id": f"quest-{study_id}",
        "action_type": "return_to_ai_reviewer_workflow",
        "execution_status": "blocked",
        "blocked_reason": "ai_reviewer_request_missing",
        "owner_route": route,
        "prompt_contract": dispatch_payload["prompt_contract"],
        "repeat_suppression_key": "publication-blockers::repeat-executor",
    }
    _write_json(
        legacy_execution_latest_path,
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "execution_ledger": [
                {**prior_failure, "execution_id": "legacy-execution::first"},
                {**prior_failure, "execution_id": "legacy-execution::second"},
            ],
        },
    )
    assert legacy_execution_latest_path.is_file()
    called = {"count": 0}

    def fake_ai_reviewer_workflow(**_) -> dict[str, object]:
        called["count"] += 1
        return {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "ai_reviewer_workflow",
        }

    monkeypatch.setattr(
        module,
        "_execute_ai_reviewer_workflow",
        fake_ai_reviewer_workflow,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["executed_count"] == 1
    assert result["repeat_suppressed_count"] == 0
    assert execution["execution_status"] == "executed"
    assert execution["owner_callable_surface"] == "ai_reviewer_workflow"
    assert called["count"] == 1
    assert execution["prompt_contract"]["repeat_suppression_key"] == "publication-blockers::repeat-executor"
    assert execution_latest_path.is_file()

    _write_json(
        execution_latest_path,
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "execution_ledger": [
                {**prior_failure, "execution_id": "execution::first"},
                {**prior_failure, "execution_id": "execution::second"},
            ],
        },
    )
    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["executed_count"] == 0
    assert result["repeat_suppressed_count"] == 1
    assert called["count"] == 1
    assert execution["execution_status"] == "repeat_suppressed"
    assert execution["repeat_suppressed"] is True
    assert execution["why_not_applied"] == "anti_loop_budget_exhausted"
    assert execution["owner_callable_surface"] is None
    assert execution["anti_loop_budget"]["failure_count"] == 2
    assert execution["anti_loop_budget"]["escalation_route"] == "publishability_repair_sprint"

    db_path = profile.workspace_root / "runtime" / "artifacts" / "domain_authority_refs.sqlite"
    assert execution["domain_authority_ref_index"]["status"] == "opl_state_index_source_adapter_emitted"
    assert execution["domain_authority_ref_index"]["indexed_table"] == "dispatch_receipts"
    assert execution["domain_authority_ref_index"]["sqlite_persisted"] is False
    assert execution["domain_authority_ref_index"]["opl_state_index_kernel_required"] is True
    assert not db_path.exists()
