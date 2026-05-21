from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers.domain_route_scan_parts import platform_repair
from tests.domain_route_scan_cases.owner_route_test_helpers import (
    assert_owner_route_required,
)
from med_autoscience.controllers.domain_route_scan_parts import action_projection
from med_autoscience.controllers.domain_route_scan_parts import domain_transition_actions
from med_autoscience.developer_supervisor_mode import DeveloperSupervisorMode
from tests.study_runtime_test_helpers import make_profile, write_study


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


def _write_repair_lifecycle(*, study_root: Path, study_id: str, quest_id: str, apply_result: dict[str, object]) -> None:
    platform_repair.write_runtime_platform_repair_lifecycle(
        study_root=study_root,
        supervision_latest_relative_path=Path("artifacts/supervision/domain_route_scan/latest.json"),
        study_id=study_id,
        quest_id=quest_id,
        apply_result=apply_result,
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


def test_domain_transition_routes_unit_harmonized_analysis_work_unit_to_analysis_owner() -> None:
    actions = domain_transition_actions.actions(
        {
            "domain_transition": {
                "decision_type": "route_back_same_line",
                "route_target": "analysis-campaign",
                "owner": "analysis-campaign",
                "next_work_unit": {
                    "unit_id": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
                    "lane": "analysis-campaign",
                    "summary": (
                        "Add uncertainty intervals, grouped calibration evidence, and "
                        "reproducibility details to the unit-harmonized external validation."
                    ),
                },
                "guard_boundary": {"opl_generic_runner_may_resume": False},
            }
        }
    )

    assert actions is not None
    assert len(actions) == 1
    action = actions[0]
    assert action["action_type"] == "unit_harmonized_external_validation_rerun"
    assert action["owner"] == "analysis_harmonization_owner"
    assert action["request_owner"] == "analysis_harmonization_owner"
    assert action["recommended_owner"] == "analysis_harmonization_owner"
    assert action["reason"] == "unit_harmonized_rerun_required"
    assert action["next_work_unit"] == "unit_harmonized_external_validation_rerun"
    assert action["executable_work_unit"] == "unit_harmonized_external_validation_rerun"
    assert action["controller_work_unit_id"] == "unit_harmonized_validation_uncertainty_and_grouped_calibration"
    assert action["controller_next_work_unit"]["unit_id"] == (
        "unit_harmonized_validation_uncertainty_and_grouped_calibration"
    )
    assert action["required_output_surface"] == (
        "unit-harmonized external-validation rerun evidence or "
        "typed blocker:unit_harmonized_rerun_required"
    )
    assert action["paper_package_mutation_allowed"] is False
    assert action["quality_gate_relaxation_allowed"] is False
    assert action["medical_claim_authoring_allowed"] is False


def test_action_queue_honors_runtime_redrive_domain_transition_over_completed_truth() -> None:
    actions = _queue(
        {
            "quest_status": "completed",
            "study_completion_contract": {"ready": True, "status": "resolved"},
            "domain_transition": _unit_harmonized_analysis_domain_transition(),
        }
    )

    assert [item["action_type"] for item in actions] == ["unit_harmonized_external_validation_rerun"]
    assert actions[0]["owner"] == "analysis_harmonization_owner"
    assert actions[0]["reason"] == "unit_harmonized_rerun_required"


def test_scan_projects_runtime_redrive_domain_transition_and_owner_action(monkeypatch, tmp_path: Path) -> None:
    scan = __import__("med_autoscience.controllers.domain_route_scan", fromlist=["domain_route_scan"])
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "completed",
        "study_completion_contract": {"ready": True, "status": "resolved"},
        "domain_transition": _unit_harmonized_analysis_domain_transition(study_id=study_id),
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-domain-transition",
            "source_signature": "truth-source-dm002-domain-transition",
        },
    }
    progress_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "managed_runtime_supervision_gap",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::unit-harmonized-routeback",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "ai_reviewer"},
    }
    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval_payload),
    )

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["domain_transition"]["decision_type"] == "route_back_same_line"
    assert study["domain_transition"]["route_target"] == "analysis-campaign"
    assert study["domain_transition"]["next_work_unit"]["unit_id"] == (
        "unit_harmonized_validation_uncertainty_and_grouped_calibration"
    )
    assert [item["action_type"] for item in study["action_queue"]] == ["unit_harmonized_external_validation_rerun"]
    assert [item["action_type"] for item in result["action_queue"]] == ["unit_harmonized_external_validation_rerun"]
    action = study["action_queue"][0]
    assert action["owner"] == "analysis_harmonization_owner"
    assert action["reason"] == "unit_harmonized_rerun_required"
    assert action["controller_work_unit_id"] == (
        study["domain_transition"]["next_work_unit"]["unit_id"]
    )
    assert action["executable_work_unit"] == "unit_harmonized_external_validation_rerun"
    assert action["handoff_packet"]["next_executable_owner"] == "analysis_harmonization_owner"
    assert study["blocked_reason"] == "unit_harmonized_rerun_required"
    assert study["next_owner"] == "analysis_harmonization_owner"


def test_scan_story_surface_blocker_overrides_stale_ai_reviewer_lifecycle(monkeypatch, tmp_path: Path) -> None:
    scan = __import__("med_autoscience.controllers.domain_route_scan", fromlist=["domain_route_scan"])
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    eval_id = f"publication-eval::{study_id}::current-ai-reviewer"
    batch_path = study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"
    batch_path.parent.mkdir(parents=True)
    batch_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "blocked",
                "source_eval_id": eval_id,
                "blocked_reason": "manuscript_story_surface_delta_missing",
                "next_owner": "write",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "route_back_same_line",
            "route_target": "write",
            "owner": "write",
            "controller_action": "ensure_study_runtime",
            "next_work_unit": {
                "unit_id": "dm002_same_line_publication_paper_repair",
                "lane": "write",
                "summary": "Controller-authorized paper repair and package rebuild from latest evidence.",
            },
            "guard_boundary": {"opl_generic_runner_may_resume": False},
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-event-dm002-story-surface",
            "source_signature": "truth-source-dm002-story-surface",
        },
    }
    progress_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "managed_runtime_supervision_gap",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
        "ai_repair_lifecycle": {
            "surface": "ai_repair_lifecycle",
            "schema_version": 1,
            "state": "blocked",
            "blocked_reason": "domain_transition_ai_reviewer_re_eval",
            "next_owner": "ai_reviewer",
            "authority": "observability_only",
            "external_supervisor_required": False,
            "top_action": {
                "action_type": "controller_repair",
                "owner": "mas_controller",
                "repair_kind": "bounded_work_unit_redrive",
                "auto_apply_allowed": True,
            },
        },
    }
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "ai_reviewer"},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "route_target": "write",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
                "next_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                    "summary": "Repair medical journal prose quality against the current story surface.",
                },
            }
        ],
    }
    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval_payload),
    )

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["run_quality_repair_batch"]
    assert [item["action_type"] for item in result["action_queue"]] == ["run_quality_repair_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "write"
    assert action["reason"] == "manuscript_story_surface_delta_missing"
    assert action["next_work_unit"] == "medical_prose_write_repair"
    assert action["controller_route"]["authorization_basis"] == "quality_repair_story_surface_delta_blocker"
    assert study["owner_route"]["next_owner"] == "write"
    assert study["owner_route"]["owner_reason"] == "manuscript_story_surface_delta_missing"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]
    assert study["blocked_reason"] == "manuscript_story_surface_delta_missing"
    assert study["next_owner"] == "write"


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
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "study-002", quest_id="quest-002")
    quest_root = profile.runtime_root / "quest-002"
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

    assert result is not None
    _write_repair_lifecycle(
        study_root=study_root,
        study_id="study-002",
        quest_id="quest-002",
        apply_result=result,
    )
    runtime_state = assert_owner_route_required(
        apply_result=result,
        ensure_calls=ensure_calls,
        quest_root=quest_root,
    )
    assert result["repair_kind"] == "domain_transition_bundle_stage_finalize_redrive"
    authorization = runtime_state["last_controller_decision_authorization"]
    assert authorization["decision_id"] == "fresh-bundle-stage-decision"
    assert authorization["route_target"] == "finalize"
    assert authorization["work_unit_id"] == "submission_authority_sync_closure"
    assert authorization["work_unit_fingerprint"] == (
        "domain-transition::bundle_stage_finalize::submission_authority_sync_closure"
    )


def test_apply_runtime_platform_repair_redrives_story_surface_delta_before_gate_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "dm002", quest_id="quest-dm002")
    quest_root = profile.runtime_root / "quest-dm002"
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    eval_id = "publication-eval::dm002::current"
    runtime_state_path.parent.mkdir(parents=True)
    runtime_state_path.write_text(
        json.dumps(
            {
                "status": "waiting_for_user",
                "quest_id": "quest-dm002",
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "controller_work_unit_pending",
                "pending_user_message_count": 0,
                "last_controller_decision_authorization": {
                    "decision_id": "old-gate-recheck",
                    "route_target": "publication_gate",
                    "work_unit_id": "publication_gate_recheck",
                    "work_unit_fingerprint": "publication-blockers::old",
                    "controller_actions": ["run_gate_clearing_batch"],
                },
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    batch_path = study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"
    batch_path.parent.mkdir(parents=True)
    batch_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "blocked",
                "source_eval_id": eval_id,
                "next_owner": "write",
                "blocked_reason": "manuscript_story_surface_delta_missing",
                "repair_execution_evidence": {
                    "blockers": ["manuscript_story_surface_delta_missing"],
                },
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": eval_id,
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "route_target": "write",
                "route_key_question": "Can the manuscript be rewritten around the current validated story?",
                "route_rationale": "The current manuscript has not absorbed the latest story surface.",
                "work_unit_fingerprint": "publication-blockers::story-surface",
                "next_work_unit": {
                    "unit_id": "manuscript_story_repair",
                    "lane": "write",
                    "summary": "Repair the manuscript story from current evidence surfaces.",
                },
            }
        ],
    }
    ensure_calls: list[dict[str, object]] = []

    result = platform_repair.apply_runtime_platform_repair(
        profile=object(),
        study_id="dm002",
        study_root=study_root,
        status={
            "quest_id": "quest-dm002",
            "quest_root": str(quest_root),
            "quest_status": "waiting_for_user",
            "domain_transition": {
                "decision_type": "publication_gate_blocker",
                "route_target": "publication_gate",
                "controller_action": "run_gate_clearing_batch",
                "next_work_unit": {
                    "unit_id": "publication_gate_recheck",
                    "lane": "publication_gate",
                    "source_work_unit": {"unit_id": "manuscript_story_repair", "lane": "write"},
                },
                "typed_blocker": {"blocker_id": "publication_gate_blocked"},
            },
        },
        progress={},
        publication_eval_payload=publication_eval_payload,
        developer_mode=_developer_apply_safe_mode(),
        enabled=True,
        repair_required=True,
    )

    assert result is not None
    _write_repair_lifecycle(
        study_root=study_root,
        study_id="dm002",
        quest_id="quest-dm002",
        apply_result=result,
    )
    runtime_state = assert_owner_route_required(
        apply_result=result,
        ensure_calls=ensure_calls,
        quest_root=quest_root,
    )
    assert result["repair_kind"] == "domain_transition_publication_gate_blocker_story_surface_delta_redrive"
    assert result["domain_transition_controller_route"]["authorization_basis"] == (
        "quality_repair_story_surface_delta_blocker"
    )
    authorization = runtime_state["last_controller_decision_authorization"]
    assert authorization["authorization_basis"] == "quality_repair_story_surface_delta_blocker"
    assert authorization["route_target"] == "write"
    assert authorization["work_unit_id"] == "manuscript_story_repair"
    assert authorization["controller_actions"] == ["run_quality_repair_batch"]


def test_apply_runtime_platform_repair_redrives_medical_prose_story_surface_delta(
    monkeypatch,
    tmp_path: Path,
) -> None:
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "dm003", quest_id="quest-dm003")
    quest_root = profile.runtime_root / "quest-dm003"
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    eval_id = "publication-eval::dm003::medical-prose-current"
    runtime_state_path.parent.mkdir(parents=True)
    runtime_state_path.write_text(
        json.dumps(
            {
                "status": "waiting_for_user",
                "quest_id": "quest-dm003",
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "controller_work_unit_pending",
                "pending_user_message_count": 0,
                "last_controller_decision_authorization": {
                    "decision_id": "old-gate-recheck",
                    "route_target": "publication_gate",
                    "work_unit_id": "publication_gate_recheck",
                    "work_unit_fingerprint": "publication-blockers::old",
                    "controller_actions": ["run_gate_clearing_batch"],
                },
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    batch_path = study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"
    batch_path.parent.mkdir(parents=True)
    batch_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "blocked",
                "source_eval_id": eval_id,
                "next_owner": "write",
                "blocked_reason": "manuscript_story_surface_delta_missing",
                "repair_execution_evidence": {
                    "blockers": ["manuscript_story_surface_delta_missing"],
                },
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": eval_id,
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "route_target": "write",
                "route_key_question": "Can the manuscript meet medical journal prose standards?",
                "route_rationale": "The current manuscript has not absorbed medical prose quality feedback.",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
                "next_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                    "summary": "Repair the manuscript for medical journal prose quality.",
                },
            }
        ],
    }
    ensure_calls: list[dict[str, object]] = []

    result = platform_repair.apply_runtime_platform_repair(
        profile=object(),
        study_id="dm003",
        study_root=study_root,
        status={
            "quest_id": "quest-dm003",
            "quest_root": str(quest_root),
            "quest_status": "waiting_for_user",
            "domain_transition": {
                "decision_type": "publication_gate_blocker",
                "route_target": "publication_gate",
                "controller_action": "run_gate_clearing_batch",
                "next_work_unit": {
                    "unit_id": "publication_gate_recheck",
                    "lane": "publication_gate",
                    "source_work_unit": {"unit_id": "medical_prose_write_repair", "lane": "write"},
                },
                "typed_blocker": {"blocker_id": "publication_gate_blocked"},
            },
        },
        progress={},
        publication_eval_payload=publication_eval_payload,
        developer_mode=_developer_apply_safe_mode(),
        enabled=True,
        repair_required=True,
    )

    assert result is not None
    _write_repair_lifecycle(
        study_root=study_root,
        study_id="dm003",
        quest_id="quest-dm003",
        apply_result=result,
    )
    runtime_state = assert_owner_route_required(
        apply_result=result,
        ensure_calls=ensure_calls,
        quest_root=quest_root,
    )
    authorization = runtime_state["last_controller_decision_authorization"]
    assert authorization["authorization_basis"] == "quality_repair_story_surface_delta_blocker"
    assert authorization["route_target"] == "write"
    assert authorization["work_unit_id"] == "medical_prose_write_repair"
    assert authorization["work_unit_fingerprint"] == "domain-transition::route_back_same_line::medical_prose_write_repair"
    assert authorization["controller_actions"] == ["run_quality_repair_batch"]


def test_domain_transition_routes_medical_prose_write_repair_to_quality_batch() -> None:
    actions = domain_transition_actions.actions(
        {
            "domain_transition": {
                "decision_type": "route_back_same_line",
                "route_target": "write",
                "owner": "write",
                "next_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                    "summary": "Repair medical journal prose quality.",
                },
                "guard_boundary": {"opl_generic_runner_may_resume": False},
            }
        }
    )

    assert actions is not None
    assert len(actions) == 1
    action = actions[0]
    assert action["action_type"] == "run_quality_repair_batch"
    assert action["owner"] == "write"
    assert action["request_owner"] == "write"
    assert action["recommended_owner"] == "write"
    assert action["next_work_unit"] == "medical_prose_write_repair"
    assert action["required_output_surface"] == "artifacts/publication_eval/latest.json"


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


def _unit_harmonized_analysis_domain_transition(study_id: str = "study-001") -> dict[str, object]:
    return {
        "study_id": study_id,
        "decision_type": "route_back_same_line",
        "route_target": "analysis-campaign",
        "owner": "analysis-campaign",
        "controller_action": "ensure_study_runtime",
        "next_work_unit": {
            "unit_id": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
            "lane": "analysis-campaign",
            "summary": (
                "Add uncertainty intervals, grouped calibration evidence, and "
                "reproducibility details to the unit-harmonized external validation."
            ),
        },
        "guard_boundary": {"opl_generic_runner_may_resume": False},
    }
