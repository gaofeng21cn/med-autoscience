from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_quality_repair_batch_allows_current_nonterminal_stall_after_safe_reconcile_refresh(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    quest_root = profile.runtime_root / f"quest-{study_id}"
    quest_root.mkdir(parents=True, exist_ok=True)
    work_unit_id = "current_manuscript_prose_currentness_and_gate_replay_write_closeout"
    work_unit_fingerprint = f"domain-transition::route_back_same_line::{work_unit_id}"
    source_eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "002-dm-china-us-mortality-attribution::20260528T230256Z::ai-reviewer-record"
    )
    route = _owner_route(study_id=study_id, action_type="run_quality_repair_batch", owner="write")
    route.update(
        {
            "failure_signature": "quest_waiting_opl_runtime_owner_route",
            "owner_reason": "quest_waiting_opl_runtime_owner_route",
            "source_fingerprint": "truth-snapshot::dm002-current-write-route",
            "work_unit_fingerprint": work_unit_fingerprint,
            "idempotency_key": "owner-route::dm002::write::quest-waiting-opl-runtime-owner-route",
            "currentness_contract": {
                "status": "currentness_basis_required",
                "basis": {
                    "source_eval_id": source_eval_id,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": work_unit_fingerprint,
                    "truth_epoch": "truth-event-000024",
                    "runtime_health_epoch": "runtime-health-event-006388",
                    "owner_reason": "quest_waiting_opl_runtime_owner_route",
                },
            },
            "source_refs": {
                "source_eval_id": source_eval_id,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "owner_route_currentness_basis": {
                    "source_eval_id": source_eval_id,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": work_unit_fingerprint,
                    "truth_epoch": "truth-event-000024",
                    "runtime_health_epoch": "runtime-health-event-006388",
                    "owner_reason": "quest_waiting_opl_runtime_owner_route",
                },
            },
        }
    )
    stale_dispatch_stall = {
        "surface_kind": "paper_progress_stall",
        "stalled": True,
        "terminal": False,
        "safe_reconcile_candidate": True,
        "action_fingerprint": "paper_progress_stall::old",
        "stall_reasons": ["same_fingerprint_loop"],
    }
    current_nonterminal_stall = {
        "surface_kind": "paper_progress_stall",
        "stalled": True,
        "terminal": False,
        "safe_reconcile_candidate": True,
        "action_fingerprint": "paper_progress_stall::current",
        "stall_reasons": ["same_fingerprint_loop"],
    }
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=route,
    )
    dispatch_payload["source_action"] = {
        "action_type": "run_quality_repair_batch",
        "route_target": "write",
        "source_eval_id": source_eval_id,
        "next_work_unit": {
            "unit_id": work_unit_id,
            "lane": "write",
        },
        "work_unit_fingerprint": work_unit_fingerprint,
    }
    dispatch_payload["prompt_contract"]["next_work_unit"] = {
        "unit_id": work_unit_id,
        "lane": "write",
    }
    dispatch_payload["paper_progress_stall"] = stale_dispatch_stall
    dispatch_payload["prompt_contract"]["paper_progress_stall"] = stale_dispatch_stall
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": route,
                    "paper_progress_stall": current_nonterminal_stall,
                }
            ],
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [{**dispatch_payload, "refs": {"dispatch_path": str(dispatch_path)}}],
        },
    )
    monkeypatch.setattr(module.action_execution, "quest_root_from_status", lambda *_: quest_root)
    called: dict[str, object] = {}

    def fake_run_quality_repair_batch(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        return {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"),
        }

    monkeypatch.setattr(
        module.action_execution.quality_repair.quality_repair_batch,
        "run_quality_repair_batch",
        fake_run_quality_repair_batch,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert execution["paper_progress_stall_handoff_allowed"] is True
    assert execution["paper_progress_stall_diagnostic"] == {
        "surface_kind": "paper_progress_stall_diagnostic",
        "status": "nonterminal_fingerprint_stale_diagnostic",
        "blocking": False,
        "blocked_reason": None,
        "handoff_allowed": True,
        "dispatch_action_fingerprint": "paper_progress_stall::old",
        "current_action_fingerprint": "paper_progress_stall::current",
        "current_terminal": False,
        "current_stalled": True,
    }
    assert execution["current_paper_progress_stall"]["action_fingerprint"] == "paper_progress_stall::current"
    assert execution["owner_callable_surface"] == "quality_repair_batch.run_quality_repair_batch"
    assert called["authority_route_context"]["work_unit_id"] == work_unit_id


def test_execute_quality_repair_batch_escalates_after_two_same_auto_failures(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    work_unit_id = "current_manuscript_prose_currentness_and_gate_replay_write_closeout"
    work_unit_fingerprint = f"domain-transition::route_back_same_line::{work_unit_id}"
    route = _owner_route(study_id=study_id, action_type="run_quality_repair_batch", owner="write")
    route.update(
        {
            "failure_signature": "quest_waiting_opl_runtime_owner_route",
            "owner_reason": "quest_waiting_opl_runtime_owner_route",
            "work_unit_fingerprint": work_unit_fingerprint,
            "source_refs": {
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "owner_route_currentness_basis": {
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": work_unit_fingerprint,
                },
            },
        }
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=route,
    )
    dispatch_payload["source_action"] = {
        "action_type": "run_quality_repair_batch",
        "route_target": "write",
        "next_work_unit": {"unit_id": work_unit_id, "lane": "write"},
        "work_unit_fingerprint": work_unit_fingerprint,
    }
    dispatch_payload["prompt_contract"]["next_work_unit"] = {"unit_id": work_unit_id, "lane": "write"}
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": route,
                    "paper_progress_stall": {
                        "surface_kind": "paper_progress_stall",
                        "stalled": True,
                        "terminal": False,
                        "safe_reconcile_candidate": True,
                        "action_fingerprint": "paper_progress_stall::current",
                        "stall_reasons": ["same_fingerprint_loop"],
                    },
                }
            ],
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [{**dispatch_payload, "refs": {"dispatch_path": str(dispatch_path)}}],
        },
    )
    latest_execution_path = (
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json"
    )
    previous_failure = {
        "study_id": study_id,
        "action_type": "run_quality_repair_batch",
        "execution_status": "blocked",
        "blocked_reason": "typed_closeout_packet_required",
        "repeat_suppression_key": work_unit_fingerprint,
        "work_unit_fingerprint": work_unit_fingerprint,
        "source_action": dispatch_payload["source_action"],
        "prompt_contract": dispatch_payload["prompt_contract"],
        "owner_result": {"status": "blocked"},
    }
    _write_json(
        latest_execution_path,
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_id,
            "executions": [],
            "execution_ledger": [
                {**previous_failure, "execution_id": "execution::first"},
                {**previous_failure, "execution_id": "execution::second"},
            ],
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["executed_count"] == 0
    assert execution["execution_status"] == "repeat_suppressed"
    assert execution["blocked_reason"] == "anti_loop_budget_exhausted"
    assert execution["typed_blocker"] == {
        "blocker_id": "typed_closeout_packet_required",
        "owner": "one-person-lab",
        "write_permitted": False,
        "escalation_route": "publishability_repair_sprint",
    }
    assert execution["anti_loop_budget"]["failure_count"] == 2
    assert execution["anti_loop_budget"]["next_allowed_outcomes"] == [
        "publishability_repair_sprint",
        "single_typed_blocker",
        "human_or_operator_gate",
    ]
    assert execution["paper_stage_log"]["progress_delta_classification"] == "no_user_visible_progress_delta"
    assert execution["paper_stage_log"]["paper_progress_delta"] == {"count": 0, "token_usage_total": 0}
    assert execution["paper_stage_log"]["platform_repair_delta"] == {"count": 0, "token_usage_total": 0}
