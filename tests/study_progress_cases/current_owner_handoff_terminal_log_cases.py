from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_current_owner_handoff_action_keeps_scalar_remaining_blocker_text() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_owner_handoff_projection"
    )

    action = module.current_owner_handoff_action(
        {
            "opl_current_control_state_handoff": {
                "latest_terminal_stage_log": {
                    "status": "handoff_ready",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "paper_stage_log": {
                        "current_owner": "ai_reviewer",
                        "remaining_blockers": "ai_reviewer_record_stale_after_current_inputs",
                    },
                },
            },
        }
    )

    assert action is not None
    assert action["blocked_reason"] == "ai_reviewer_record_stale_after_current_inputs"


def test_current_owner_handoff_action_ignores_structured_remaining_blocker_payload() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_owner_handoff_projection"
    )

    action = module.current_owner_handoff_action(
        {
            "opl_current_control_state_handoff": {
                "latest_terminal_stage_log": {
                    "status": "handoff_ready",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "paper_stage_log": {
                        "current_owner": "ai_reviewer",
                        "remaining_blockers": {
                            "reason": "ai_reviewer_record_stale_after_current_inputs"
                        },
                    },
                },
            },
        }
    )

    assert action is not None
    assert action["blocked_reason"] is None


def test_terminal_stage_log_missing_user_progress_fields_projects_typed_blocker(tmp_path: Path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff"
    )
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    closeout_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "stage_attempt_closeouts"
        / "sat-001.closeout.json"
    )
    _write_json(
        closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "study_id": "001-risk",
            "stage_attempt_id": "sat-001",
            "stage_id": "domain_owner/default-executor-dispatch",
            "action_type": "run_quality_repair_batch",
            "status": "completed",
            "generated_at": "2026-05-31T01:00:00+00:00",
            "closeout_refs": ["artifacts/supervision/consumer/default_executor_execution/sat-001.json"],
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "stage_name": "current_story_surface_repair",
                "problem_summary": "Story-surface repair attempt reached provider completion.",
                "stage_goal": "Produce a user-readable repair delta or stable blocker.",
                "outcome": "completed",
                "remaining_blockers": [],
                "duration": {"seconds": 42},
                "token_usage": {"total_tokens": 1200},
                "cost": {"usd": 0.04},
                "usage_refs": ["usage://sat-001"],
                "cost_refs": ["cost://sat-001"],
                "evidence_refs": [
                    "artifacts/supervision/consumer/default_executor_execution/sat-001.json"
                ],
            },
        },
    )

    handoff = module.opl_current_control_state_study_handoff_projection(
        profile=profile,
        study_id="001-risk",
    )

    assert handoff is not None
    terminal_log = handoff["latest_terminal_stage_log"]
    assert terminal_log["status"] == "typed_blocker"
    assert terminal_log["typed_blocker_reason"] == "typed_closeout_packet_required"
    assert terminal_log["diagnostic"] == "user_stage_log_missing_required_progress_fields"
    assert terminal_log["missing_user_stage_log_fields"] == [
        "stage_work_done",
        "paper_work_done",
        "changed_stage_surfaces",
        "changed_paper_surfaces",
        "progress_delta_classification",
    ]
    assert terminal_log["missing_domain_fields"] == terminal_log["missing_user_stage_log_fields"]
    assert terminal_log["semantic_gap"] == {
        "reason": "domain_closeout_provided_incomplete_user_stage_log",
        "missing_domain_fields": [
            "stage_work_done",
            "paper_work_done",
            "changed_stage_surfaces",
            "changed_paper_surfaces",
            "progress_delta_classification",
        ],
        "source": "paper_stage_log",
        "owner": "MedAutoScience",
    }
    assert terminal_log["paper_stage_log"]["outcome"] == "typed_blocker"
    assert terminal_log["paper_stage_log"]["remaining_blockers"] == [
        "typed_closeout_packet_required"
    ]


def test_terminal_stage_log_infers_missing_delta_classification_from_paper_surfaces(tmp_path: Path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff"
    )
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    closeout_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "stage_attempt_closeouts"
        / "sat-002.closeout.json"
    )
    _write_json(
        closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "study_id": "001-risk",
            "stage_attempt_id": "sat-002",
            "stage_id": "domain_owner/default-executor-dispatch",
            "action_type": "run_quality_repair_batch",
            "status": "completed",
            "generated_at": "2026-05-31T01:00:00+00:00",
            "closeout_refs": ["artifacts/supervision/consumer/default_executor_execution/sat-002.json"],
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "stage_name": "current_story_surface_repair",
                "problem_summary": "Story-surface repair produced manuscript-facing changes.",
                "stage_goal": "Produce a user-readable repair delta or stable blocker.",
                "stage_work_done": ["Updated manuscript-facing surfaces."],
                "paper_work_done": ["Updated manuscript-facing surfaces."],
                "changed_stage_surfaces": [
                    "studies/001-risk/paper/draft.md",
                ],
                "changed_paper_surfaces": [
                    "studies/001-risk/paper/draft.md",
                ],
                "outcome": "completed",
                "remaining_blockers": [],
                "duration": {"seconds": 42},
                "token_usage": {"total_tokens": 1200},
                "cost": {"usd": 0.04},
                "usage_refs": ["usage://sat-002"],
                "cost_refs": ["cost://sat-002"],
                "evidence_refs": [
                    "artifacts/supervision/consumer/default_executor_execution/sat-002.json"
                ],
            },
        },
    )

    handoff = module.opl_current_control_state_study_handoff_projection(
        profile=profile,
        study_id="001-risk",
    )

    assert handoff is not None
    terminal_log = handoff["latest_terminal_stage_log"]
    assert terminal_log["status"] == "completed"
    assert "typed_blocker_reason" not in terminal_log
    assert terminal_log["missing_user_stage_log_fields"] == ["progress_delta_classification"]
    assert terminal_log["paper_stage_log"]["progress_delta_classification"] == "deliverable_progress"
    assert (
        terminal_log["paper_stage_log"]["progress_delta_classification_source"]
        == "inferred_from_changed_paper_surfaces"
    )


__all__ = [name for name in globals() if name.startswith("test_")]
