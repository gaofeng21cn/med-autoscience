from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_accepts_materialized_story_surface_route_bridged_from_current_ai_reviewer_route(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    (profile.runtime_root / quest_id).mkdir(parents=True)
    work_unit_id = "materialize_current_ai_reviewer_record_through_mas_owner_surface"
    materialized_work_unit_id = "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
    work_unit_fingerprint = "truth-snapshot::dm002-current-ai-reviewer"
    current_route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    current_route.update(
        {
            "truth_epoch": "truth-event-000022",
            "route_epoch": "truth-event-000022",
            "runtime_health_epoch": "runtime-health-event-006244",
            "work_unit_fingerprint": work_unit_fingerprint,
            "source_fingerprint": "truth-snapshot::dm002-current",
            "failure_signature": "ai_reviewer_assessment_required",
            "owner_reason": "ai_reviewer_assessment_required",
            "idempotency_key": "owner-route::dm002::current-ai-reviewer",
            "source_refs": {
                "study_truth_epoch": "truth-event-000022",
                "runtime_health_epoch": "runtime-health-event-006244",
                "source_eval_id": "publication-eval::dm002::current",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "blocked_reason": "ai_reviewer_assessment_required",
            },
        }
    )
    bridged_route = dict(current_route)
    bridged_route.update(
        {
            "failure_signature": "manuscript_story_surface_delta_missing",
            "owner_reason": "manuscript_story_surface_delta_missing",
            "next_owner": "write",
            "allowed_actions": ["run_quality_repair_batch"],
            "blocked_actions": ["return_to_ai_reviewer_workflow"],
            "idempotency_key": "owner-route::dm002::story-surface-after-ai-reviewer",
            "source_refs": {
                **current_route["source_refs"],
                "blocked_reason": "manuscript_story_surface_delta_missing",
                "materialized_work_unit_id": materialized_work_unit_id,
                "materialized_from_action_type": "return_to_ai_reviewer_workflow",
                "bridged_from_owner_reason": "ai_reviewer_assessment_required",
                "bridged_from_idempotency_key": current_route["idempotency_key"],
                "bridge_authority": "domain_action_request_materializer_story_surface_bridge",
            },
        }
    )
    terminal_stall = {
        "surface_kind": "paper_progress_stall",
        "stalled": True,
        "terminal": True,
        "action_fingerprint": "paper_progress_stall::current-ai-reviewer-story-bridge",
        "stall_reasons": ["runtime_recovery_retry_budget_exhausted"],
    }
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=bridged_route,
    )
    dispatch_payload.update(
        {
            "dispatch_authority": "consumer_default_executor_dispatch",
            "source_action": {
                "action_type": "run_quality_repair_batch",
                "reason": "manuscript_story_surface_delta_missing",
                "route_target": "write",
                "next_work_unit": materialized_work_unit_id,
                "controller_work_unit_id": work_unit_id,
                "executable_work_unit": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "materialization_decision": "story_surface_delta_or_typed_blocker_required",
            },
            "paper_progress_stall": terminal_stall,
        }
    )
    ai_reviewer_paper_progress_stall = {
        "surface_kind": "paper_progress_stall",
        "stalled": True,
        "terminal": True,
        "action_fingerprint": "paper_progress_stall::dm002-current-ai-reviewer",
        "stall_reasons": ["runtime_recovery_retry_budget_exhausted"],
    }
    dispatch_payload["paper_progress_stall"] = ai_reviewer_paper_progress_stall
    dispatch_payload["prompt_contract"].update(
        {
            "owner_route": bridged_route,
            "idempotency_key": bridged_route["idempotency_key"],
            "repeat_suppression_key": work_unit_fingerprint,
            "paper_progress_stall": ai_reviewer_paper_progress_stall,
        }
    )
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
                    "quest_id": quest_id,
                    "owner_route": current_route,
                    "paper_progress_stall": ai_reviewer_paper_progress_stall,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": quest_id,
                            "action_type": "return_to_ai_reviewer_workflow",
                            "owner": "ai_reviewer",
                            "request_owner": "ai_reviewer",
                            "reason": "ai_reviewer_assessment_required",
                            "next_work_unit": work_unit_id,
                            "controller_work_unit_id": work_unit_id,
                            "owner_route": current_route,
                        }
                    ],
                }
            ],
        },
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [{**dispatch_payload, "refs": {"dispatch_path": str(dispatch_path)}}],
        },
    )
    monkeypatch.setattr(
        module.action_execution.quality_repair,
        "execute_quality_repair_batch",
        lambda **_: {
            "execution_status": "handoff_ready",
            "blocked_reason": None,
            "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
            "owner_result": {"status": "handoff_ready"},
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
    assert result["blocked_count"] == 0
    assert execution["execution_status"] == "handoff_ready"
    assert execution["owner_route_current"] is True
    assert execution["owner_route_basis"] == "bridged_writer_handoff"
    assert execution["paper_progress_stall_handoff_allowed"] is True
