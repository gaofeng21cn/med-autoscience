from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers.owner_route_reconcile_parts import action_projection
from med_autoscience.controllers.owner_route_reconcile_parts import domain_transition_actions
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


def test_scan_projects_current_ai_reviewer_record_materialization_controller_route_to_write_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = __import__("med_autoscience.controllers.owner_route_reconcile", fromlist=["owner_route_reconcile"])
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    work_unit_id = "materialize_current_ai_reviewer_record_through_mas_owner_surface"
    work_unit_fingerprint = f"domain-transition::route_back_same_line::{work_unit_id}"
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    decision_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": f"study-decision::{study_id}::{quest_id}::route_back_same_line::current-ai-reviewer",
                "study_id": study_id,
                "quest_id": quest_id,
                "requires_human_confirmation": False,
                "decision_type": "route_back_same_line",
                "route_target": "controller",
                "controller_actions": [
                    {
                        "action_type": "run_quality_repair_batch",
                        "payload_ref": str(
                            study_root
                            / "artifacts"
                            / "controller"
                            / "quality_repair_batch"
                            / "latest.json"
                        ),
                    }
                ],
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {
                    "unit_id": work_unit_id,
                    "lane": "controller",
                    "summary": (
                        "Consume the current AI reviewer record and decide publication quality "
                        "and downstream delivery routing under MAS authority."
                    ),
                },
            },
            ensure_ascii=False,
            indent=2,
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
        "quest_status": "active",
        "decision": "blocked",
        "reason": "quest_waiting_for_submission_metadata",
        "active_run_id": None,
        "runtime_liveness_audit": {
            "active_run_id": None,
            "runtime_audit": {"worker_running": False, "active_run_id": None},
        },
        "runtime_health_snapshot": {
            "attempt_state": "escalated",
            "canonical_runtime_action": "external_supervisor_required",
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            "retry_budget_remaining": 0,
            "worker_liveness_state": {"state": "not_live", "worker_running": False},
            "runtime_health_epoch": "runtime-health-dm002-current-ai-reviewer-materialize",
        },
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "route_back_same_line",
            "route_target": "controller",
            "owner": "controller",
            "controller_action": "request_opl_stage_attempt",
            "next_work_unit": {
                "unit_id": work_unit_id,
                "lane": "controller",
                "summary": (
                    "Consume the current AI reviewer record and decide publication quality "
                    "and downstream delivery routing under MAS authority."
                ),
            },
            "guard_boundary": {
                "runner_boundary": "mas_domain_read_model_only",
                "can_write_domain_truth": False,
                "can_execute_generic_state_machine": False,
                "opl_generic_runner_may_resume": False,
                "mas_owner_apply_receipt_required": False,
                "required_owner_surface": "artifacts/publication_eval/latest.json",
            },
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-event-dm002-current-ai-reviewer-materialize",
            "source_signature": "truth-source-dm002-current-ai-reviewer-materialize",
        },
    }
    progress_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "runtime_blocked",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::current-ai-reviewer-materialization",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
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
    assert action["request_owner"] == "write"
    assert action["recommended_owner"] == "write"
    assert action["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert action["next_work_unit"] == work_unit_id
    assert action["executable_work_unit"] == work_unit_id
    assert action["route_target"] == "write"
    assert action["original_route_target"] == "controller"
    assert action["domain_transition_decision_type"] == "route_back_same_line"
    assert study["next_owner"] == "write"
    assert study["blocked_reason"] == "quest_waiting_opl_runtime_owner_route"
    assert study["why_not_applied"] == "opl_stage_attempt_admission_required"
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["next_owner"] == "write"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]
    assert study["owner_route"]["owner_route_attempt_protocol"]["dispatchable"] is True
    assert study["owner_route"]["source_refs"]["work_unit_id"] == work_unit_id
    assert study["owner_route"]["source_refs"]["work_unit_fingerprint"] == work_unit_fingerprint


def test_current_ai_reviewer_materialization_loop_guard_blocks_stale_replay_but_allows_fresh_source(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = __import__("med_autoscience.controllers.owner_route_reconcile", fromlist=["owner_route_reconcile"])
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    work_unit_id = "materialize_current_ai_reviewer_record_through_mas_owner_surface"
    state = {
        "truth_source": "truth-source-dm002-current-ai-reviewer-materialize-v1",
        "eval_id": "publication-eval::dm002::current-ai-reviewer-materialization-v1",
    }

    def projection_inputs(**_: object) -> tuple[dict[str, object], dict[str, object], str, dict[str, object]]:
        publication_eval_payload = {
            "schema_version": 1,
            "eval_id": state["eval_id"],
            "study_id": study_id,
            "quest_id": quest_id,
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
                "ai_reviewer_required": False,
            },
        }
        status_payload = {
            "schema_version": 1,
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": quest_id,
            "quest_root": str(quest_root),
            "quest_status": "active",
            "decision": "blocked",
            "reason": "quest_waiting_for_submission_metadata",
            "active_run_id": None,
            "publication_eval": dict(publication_eval_payload),
            "runtime_liveness_audit": {
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
            "runtime_health_snapshot": {
                "attempt_state": "escalated",
                "canonical_runtime_action": "external_supervisor_required",
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
                "retry_budget_remaining": 0,
                "worker_liveness_state": {"state": "not_live", "worker_running": False},
                "runtime_health_epoch": "runtime-health-dm002-current-ai-reviewer-materialize",
            },
            "domain_transition": {
                "study_id": study_id,
                "decision_type": "route_back_same_line",
                "route_target": "controller",
                "owner": "controller",
                "controller_action": "request_opl_stage_attempt",
                "next_work_unit": {
                    "unit_id": work_unit_id,
                    "lane": "controller",
                    "summary": "Materialize the current AI reviewer record through MAS owner surface.",
                },
                "guard_boundary": {
                    "runner_boundary": "mas_domain_read_model_only",
                    "can_write_domain_truth": False,
                    "can_execute_generic_state_machine": False,
                    "opl_generic_runner_may_resume": False,
                    "mas_owner_apply_receipt_required": False,
                    "required_owner_surface": "artifacts/publication_eval/latest.json",
                },
            },
            "study_truth_snapshot": {
                "truth_epoch": "truth-event-dm002-current-ai-reviewer-materialize",
                "source_signature": state["truth_source"],
            },
        }
        progress_payload = {
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": quest_id,
            "quest_root": str(quest_root),
            "current_stage": "runtime_blocked",
            "paper_stage": "publishability_gate_blocked",
            "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            "study_truth_snapshot": status_payload["study_truth_snapshot"],
        }
        return status_payload, progress_payload, quest_id, publication_eval_payload

    monkeypatch.setattr(scan, "_read_study_projection_inputs", projection_inputs)

    first = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=True,
    )
    first_study = first["studies"][0]
    assert [item["action_type"] for item in first_study["action_queue"]] == ["run_quality_repair_batch"]
    assert first_study["owner_route"]["source_fingerprint"] == state["truth_source"]
    assert first_study["owner_route"]["source_refs"]["source_eval_id"] == state["eval_id"]

    stale_replay = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=True,
    )

    stale_study = stale_replay["studies"][0]
    assert stale_study["action_queue"] == []
    assert stale_replay["action_queue"] == []
    assert stale_study["repeat_suppression"]["repeat_suppressed"] is True
    assert stale_study["repeat_suppression"]["why_not_applied"] == "owner_route_loop_guard_stale_replay"
    assert stale_study["repeat_suppression"]["loop_guard"]["status"] == "stale_replay"
    assert stale_study["repeat_suppression"]["loop_guard"]["identity"] == {
        "study_id": study_id,
        "work_unit_id": work_unit_id,
        "source_fingerprint": state["truth_source"],
        "source_eval_id": state["eval_id"],
    }

    state["truth_source"] = "truth-source-dm002-current-ai-reviewer-materialize-v2"
    state["eval_id"] = "publication-eval::dm002::current-ai-reviewer-materialization-v2"
    fresh = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    fresh_study = fresh["studies"][0]
    assert [item["action_type"] for item in fresh_study["action_queue"]] == ["run_quality_repair_batch"]
    assert fresh_study["repeat_suppression"]["repeat_suppressed"] is False
    assert fresh_study["owner_route"]["source_fingerprint"] == state["truth_source"]
    assert fresh_study["owner_route"]["source_refs"]["source_eval_id"] == state["eval_id"]


def test_scan_projects_runtime_redrive_domain_transition_and_owner_action(monkeypatch, tmp_path: Path) -> None:
    scan = __import__("med_autoscience.controllers.owner_route_reconcile", fromlist=["owner_route_reconcile"])
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
        "current_stage": "managed_opl_runtime_owner_handoff_gap",
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
    scan = __import__("med_autoscience.controllers.owner_route_reconcile", fromlist=["owner_route_reconcile"])
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
            "controller_action": "request_opl_stage_attempt",
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
        "current_stage": "managed_opl_runtime_owner_handoff_gap",
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
                "work_unit_fingerprint": "dm002_same_line_publication_paper_repair_20260521",
                "next_work_unit": {
                    "unit_id": "dm002_same_line_publication_paper_repair",
                    "lane": "write",
                    "summary": "Controller-authorized paper repair and package rebuild from latest evidence.",
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
    assert action["next_work_unit"] == "dm002_same_line_publication_paper_repair"
    assert action["controller_route"]["authorization_basis"] == "quality_repair_story_surface_delta_blocker"
    assert study["owner_route"]["next_owner"] == "write"
    assert study["owner_route"]["owner_reason"] == "manuscript_story_surface_delta_missing"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]
    assert study["blocked_reason"] == "manuscript_story_surface_delta_missing"
    assert study["next_owner"] == "write"


def _unit_harmonized_analysis_domain_transition(study_id: str = "study-001") -> dict[str, object]:
    return {
        "study_id": study_id,
        "decision_type": "route_back_same_line",
        "route_target": "analysis-campaign",
        "owner": "analysis-campaign",
        "controller_action": "request_opl_stage_attempt",
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
