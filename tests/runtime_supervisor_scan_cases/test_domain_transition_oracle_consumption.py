from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers.runtime_supervisor_scan_parts import platform_repair
from med_autoscience.controllers.runtime_supervisor_scan_parts import action_projection
from med_autoscience.developer_supervisor_mode import DeveloperSupervisorMode


def _queue(status: dict[str, object], progress: dict[str, object] | None = None) -> list[dict[str, object]]:
    return action_projection.action_queue(
        status,
        progress or {},
        study_root=Path("/tmp/study"),
        study_id="study-001",
        quest_id="study-001",
        publication_eval_payload={},
        gate_specificity={},
        ai_reviewer_assessment={},
        request_allowed_write_surfaces=[],
        control_allowed_write_surfaces=[],
        forbidden_actions=[],
    )


def test_action_queue_does_not_redrive_after_delivered_package_domain_transition() -> None:
    actions = _queue(
        {
            "domain_transition": {
                "decision_type": "delivered_package_handoff",
                "next_work_unit": {"unit_id": "package_review_handoff"},
                "guard_boundary": {"opl_generic_runner_may_resume": False},
            },
            "runtime_health_snapshot": {"canonical_runtime_action": "external_supervisor_required"},
            "controller_work_unit_next_route": {
                "recommended_next_route": "handoff_to_next_owner",
                "runtime_relaunch_required": False,
                "owner": "write/ai_reviewer",
                "next_work_unit": "manuscript_story_repair",
            },
        }
    )

    assert actions == []


def test_action_queue_does_not_redrive_human_gate_domain_transition() -> None:
    actions = _queue(
        {
            "domain_transition": {
                "decision_type": "human_gate",
                "next_work_unit": {"unit_id": "human_gate_resume"},
                "guard_boundary": {"opl_generic_runner_may_resume": False},
            },
            "continuation_state": {
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "controller_work_unit_pending",
            },
            "runtime_health_snapshot": {"canonical_runtime_action": "external_supervisor_required"},
        }
    )

    assert actions == []


def test_action_queue_does_not_redrive_stop_loss_terminal_domain_transition() -> None:
    actions = _queue(
        {
            "domain_transition": {
                "decision_type": "stop_loss",
                "route_target": "stop",
                "next_work_unit": {"unit_id": "stop_loss_handoff"},
                "guard_boundary": {"opl_generic_runner_may_resume": False},
            },
            "runtime_health_snapshot": {"canonical_runtime_action": "external_supervisor_required"},
        }
    )

    assert actions == []


def test_action_queue_does_not_redrive_fail_closed_domain_transition() -> None:
    actions = _queue(
        {
            "domain_transition": {
                "decision_type": "fail_closed",
                "route_target": "inspect",
                "next_work_unit": {"unit_id": "truth_conflict_inspection"},
                "typed_blocker": {"blocker_id": "truth_conflict"},
                "guard_boundary": {"opl_generic_runner_may_resume": False},
            },
            "runtime_health_snapshot": {"canonical_runtime_action": "external_supervisor_required"},
        }
    )

    assert actions == []


def test_action_queue_does_not_redrive_memory_writeback_receipt_consumed_transition() -> None:
    actions = _queue(
        {
            "domain_transition": {
                "decision_type": "memory_writeback_receipt_consumed",
                "route_target": "inspect",
                "controller_action": "review_publication_route_memory_writeback",
                "next_work_unit": {"unit_id": "publication_route_memory_writeback_receipt"},
                "guard_boundary": {
                    "opl_generic_runner_may_resume": False,
                    "memory_body_included": False,
                    "quality_authorized": False,
                    "submission_authorized": False,
                },
            },
            "runtime_health_snapshot": {"canonical_runtime_action": "external_supervisor_required"},
            "controller_work_unit_next_route": {
                "recommended_next_route": "handoff_to_next_owner",
                "runtime_relaunch_required": False,
                "owner": "write/ai_reviewer",
                "next_work_unit": "stale_memory_redrive",
            },
        }
    )

    assert actions == []


def test_action_queue_routes_publication_blocker_through_domain_transition_work_unit() -> None:
    actions = _queue(
        {
            "domain_transition": {
                "decision_type": "publication_gate_blocker",
                "route_target": "review",
                "controller_action": "run_gate_clearing_batch",
                "next_work_unit": {"unit_id": "publication_gate_replay", "lane": "review"},
                "typed_blocker": {"blocker_id": "publication_gate_blocked"},
                "guard_boundary": {"opl_generic_runner_may_resume": False},
            },
            "controller_work_unit_next_route": {
                "recommended_next_route": "handoff_to_next_owner",
                "runtime_relaunch_required": False,
                "owner": "write/ai_reviewer",
                "next_work_unit": "stale_old_work_unit",
            },
        }
    )

    assert [item["action_type"] for item in actions] == ["publication_gate_specificity_required"]
    assert actions[0]["reason"] == "domain_transition_publication_gate_blocker"
    assert actions[0]["controller_action"] == "run_gate_clearing_batch"
    assert actions[0]["domain_transition_decision_type"] == "publication_gate_blocker"
    assert actions[0]["next_work_unit"] == "publication_gate_replay"
    assert actions[0]["paper_package_mutation_allowed"] is False


def test_apply_runtime_platform_repair_does_not_redrive_terminal_domain_transition(
    monkeypatch,
    tmp_path: Path,
) -> None:
    quest_root = tmp_path / "runtime" / "quest-001"
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True)
    runtime_state_path.write_text(
        '{"status":"waiting_for_user","continuation_policy":"auto",'
        '"continuation_anchor":"decision","continuation_reason":"controller_work_unit_pending",'
        '"pending_user_message_count":0,'
        '"last_controller_decision_authorization":{"decision_id":"old","work_unit_id":"stale"}}\n',
        encoding="utf-8",
    )
    ensure_calls: list[dict[str, object]] = []

    def fake_ensure_study_runtime(**kwargs: object) -> dict[str, object]:
        ensure_calls.append(dict(kwargs))
        return {"decision": "resume"}

    monkeypatch.setattr(platform_repair.study_runtime_router, "ensure_study_runtime", fake_ensure_study_runtime)

    result = platform_repair.apply_runtime_platform_repair(
        profile=object(),
        study_id="study-001",
        study_root=tmp_path / "study",
        status={
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "waiting_for_user",
            "interaction_arbitration": {
                "classification": "controller_work_unit_pending_redrive",
                "action": "resume",
            },
            "domain_transition": {
                "decision_type": "delivered_package_handoff",
                "route_target": "human_gate",
                "controller_action": "wait_for_human_gate",
                "next_work_unit": {"unit_id": "package_review_handoff"},
                "guard_boundary": {"opl_generic_runner_may_resume": False},
            },
        },
        progress={},
        publication_eval_payload={},
        developer_mode=_developer_apply_safe_mode(),
        enabled=True,
        repair_required=True,
    )

    assert ensure_calls == []
    assert result is not None
    assert result["dispatch_status"] == "blocked"
    assert result["reason"] == "domain_transition_auto_redrive_blocked"
    assert result["domain_transition_decision_type"] == "delivered_package_handoff"


def test_apply_runtime_platform_repair_uses_current_domain_transition_route_over_stale_authorization(
    monkeypatch,
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    quest_root = tmp_path / "runtime" / "quest-002"
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    current_decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    runtime_state_path.parent.mkdir(parents=True)
    current_decision_path.parent.mkdir(parents=True)
    runtime_state_path.write_text(
        json.dumps(
            {
                "status": "waiting_for_user",
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "controller_work_unit_pending",
                "pending_user_message_count": 0,
                "last_controller_decision_authorization": {
                    "decision_id": "old-analysis-decision",
                    "route_target": "analysis-campaign",
                    "work_unit_id": "paper/rebuttal/review_matrix.md and action_plan.md",
                    "work_unit_fingerprint": "publication-blockers::old",
                    "controller_actions": ["run_quality_repair_batch"],
                },
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    current_decision_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": "fresh-bundle-stage-decision",
                "study_id": "study-002",
                "quest_id": "quest-002",
                "requires_human_confirmation": False,
                "controller_actions": [{"action_type": "ensure_study_runtime"}],
                "route_target": "finalize",
                "work_unit_fingerprint": (
                    "domain-transition::bundle_stage_finalize::submission_authority_sync_closure"
                ),
                "next_work_unit": {
                    "unit_id": "submission_authority_sync_closure",
                    "lane": "controller",
                    "summary": "Synchronize submission authority and package closure for the bundle-stage.",
                },
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    ensure_calls: list[dict[str, object]] = []

    def fake_ensure_study_runtime(**kwargs: object) -> dict[str, object]:
        ensure_calls.append(dict(kwargs))
        runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
        authorization = runtime_state["last_controller_decision_authorization"]
        assert authorization["decision_id"] == "fresh-bundle-stage-decision"
        assert authorization["route_target"] == "finalize"
        assert authorization["work_unit_id"] == "submission_authority_sync_closure"
        assert authorization["work_unit_fingerprint"] == (
            "domain-transition::bundle_stage_finalize::submission_authority_sync_closure"
        )
        return {
            "decision": "resume",
            "quest_status": "running",
            "runtime_liveness_audit": {
                "active_run_id": "run-fresh-bundle-stage",
                "runtime_audit": {"worker_running": True, "active_run_id": "run-fresh-bundle-stage"},
            },
        }

    monkeypatch.setattr(platform_repair.study_runtime_router, "ensure_study_runtime", fake_ensure_study_runtime)

    result = platform_repair.apply_runtime_platform_repair(
        profile=object(),
        study_id="study-002",
        study_root=study_root,
        status={
            "quest_id": "quest-002",
            "quest_root": str(quest_root),
            "quest_status": "waiting_for_user",
            "interaction_arbitration": {
                "classification": "controller_work_unit_pending_redrive",
                "action": "resume",
            },
            "domain_transition": {
                "decision_type": "bundle_stage_finalize",
                "route_target": "finalize",
                "controller_action": "continue_bundle_stage",
                "next_work_unit": {"unit_id": "submission_authority_sync_closure", "lane": "controller"},
                "guard_boundary": {"opl_generic_runner_may_resume": False},
            },
        },
        progress={},
        publication_eval_payload={"eval_id": "publication-eval::study-002::current"},
        developer_mode=_developer_apply_safe_mode(),
        enabled=True,
        repair_required=True,
    )

    assert len(ensure_calls) == 1
    assert result is not None
    assert result["dispatch_status"] == "applied"
    assert result["repair_kind"] == "domain_transition_bundle_stage_finalize_redrive"


def _developer_apply_safe_mode() -> DeveloperSupervisorMode:
    return DeveloperSupervisorMode(
        mode="developer_apply_safe",
        requested_mode="developer_apply_safe",
        mode_source="test",
        developer_mode_enabled=True,
        safe_actions_enabled=True,
        repo_level_repair_authority=True,
        scheduler_owner="test",
        codex_app_heartbeat_required=False,
        github_user_gate={"allowed": True},
        opl_family_user_config={"valid": True},
        authority_gate={"allowed": True},
    )
