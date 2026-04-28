from __future__ import annotations

import importlib


def _projection(status: dict[str, object], **kwargs: object) -> dict[str, object]:
    module = importlib.import_module("med_autoscience.controllers.auto_runtime_parking")
    return module.build_auto_runtime_parked_projection(status, **kwargs)


def test_auto_runtime_parking_maps_package_ready_handoff() -> None:
    projection = _projection(
        {
            "decision": "blocked",
            "reason": "quest_parked_on_unchanged_finalize_state",
            "quest_status": "active",
        }
    )

    assert projection["parked"] is True
    assert projection["parked_state"] == "package_ready_handoff"
    assert projection["parked_owner"] == "user"
    assert projection["resource_release_expected"] is True
    assert projection["awaiting_explicit_wakeup"] is True
    assert projection["auto_execution_complete"] is True
    assert projection["legacy_current_stage"] == "manual_finishing"
    assert projection["reopen_policy"] == "user_feedback_first"


def test_auto_runtime_parking_maps_submission_metadata_gap() -> None:
    projection = _projection(
        {
            "decision": "blocked",
            "reason": "quest_waiting_for_submission_metadata",
            "quest_status": "waiting_for_user",
        }
    )

    assert projection["parked"] is True
    assert projection["parked_state"] == "external_metadata_pending"
    assert projection["auto_execution_complete"] is True


def test_auto_runtime_parking_maps_external_input_and_user_decision() -> None:
    external_input = _projection(
        {
            "decision": "blocked",
            "reason": "quest_waiting_for_external_input",
            "quest_status": "waiting_for_user",
        }
    )
    user_decision = _projection(
        {
            "decision": "blocked",
            "reason": "quest_waiting_for_user",
            "quest_status": "waiting_for_user",
        }
    )

    assert external_input["parked_state"] == "external_input_pending"
    assert user_decision["parked_state"] == "waiting_user_decision"


def test_auto_runtime_parking_maps_runtime_failure_classes() -> None:
    upstream = _projection(
        {
            "decision": "blocked",
            "quest_status": "retrying",
            "mds_failure_diagnosis": {
                "diagnosis_code": "codex_upstream_http_403",
                "retriable": False,
                "problem": "403 account balance is negative",
            },
        }
    )
    platform = _projection(
        {
            "decision": "blocked",
            "quest_status": "failed",
            "mds_failure_diagnosis": {
                "diagnosis_code": "minimax_tool_result_sequence_error",
                "retriable": False,
            },
        }
    )

    assert upstream["parked_state"] == "external_upstream_pending"
    assert upstream["parked_owner"] == "external_provider"
    assert platform["parked_state"] == "platform_repair_pending"
    assert platform["parked_owner"] == "mas_platform"


def test_auto_runtime_parking_maps_explicit_resume_and_preflight_contracts() -> None:
    explicit = _projection(
        {
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
            "quest_status": "stopped",
        }
    )
    initialized = _projection(
        {
            "decision": "noop",
            "reason": "quest_initialized_waiting_to_start",
            "quest_status": "created",
        }
    )
    preflight = _projection(
        {
            "decision": "blocked",
            "reason": "startup_boundary_not_ready_for_resume",
            "quest_status": "paused",
        }
    )

    assert explicit["parked_state"] == "explicit_resume_pending"
    assert initialized["parked_state"] == "explicit_resume_pending"
    assert preflight["parked_state"] == "preflight_contract_pending"
    assert preflight["parked_owner"] == "controller"


def test_auto_runtime_parking_does_not_hide_controller_owned_recovery_states() -> None:
    non_parked_reasons = [
        "quest_marked_running_but_no_live_session",
        "quest_stopped_by_controller_guard",
        "quest_waiting_on_invalid_blocking",
        "quest_completion_requested_before_publication_gate_clear",
        "quest_drifting_into_write_without_gate_approval",
        "quest_stale_decision_after_write_stage_ready",
    ]

    for reason in non_parked_reasons:
        projection = _projection(
            {
                "decision": "resume",
                "reason": reason,
                "quest_status": "stopped",
                "mds_failure_diagnosis": {
                    "diagnosis_code": "codex_upstream_http_502",
                    "retriable": False,
                },
            }
        )
        assert projection["parked"] is False, reason
        assert projection["parked_state"] is None, reason


def test_study_progress_task_intake_supersedes_prior_parked_projection(
    monkeypatch,
    tmp_path,
) -> None:
    progress = importlib.import_module("med_autoscience.controllers.study_progress")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    (quest_root / "artifacts" / "reports" / "publishability_gate").mkdir(parents=True, exist_ok=True)
    task_intake = importlib.import_module("med_autoscience.study_task_intake")
    task_intake.write_task_intake(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        entry_mode="full_research",
        task_intent=(
            "用户已对修改后投稿包给出新的审稿式反馈；这不是 submission metadata 收口，"
            "而是显式重新激活同一论文线，要求 MAS/MDS 以 revision/rebuttal 模式重新处理。"
        ),
        first_cycle_outputs=("revision checklist",),
    )

    monkeypatch.setattr(
        progress.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_root": str(quest_root),
            "quest_status": "active",
            "decision": "blocked",
            "reason": "quest_parked_on_unchanged_finalize_state",
            "publication_supervisor_state": {
                "supervisor_phase": "bundle_stage_ready",
                "current_required_action": "complete_bundle_stage",
            },
            "supervisor_tick_audit": {"required": False, "status": "not_required"},
        },
    )

    result = progress.read_study_progress(profile=profile, study_id="001-risk")

    assert result["current_stage"] == "publication_supervision"
    assert result["auto_runtime_parked"]["parked"] is False
    assert result["auto_runtime_parked"]["superseded_by_task_intake"] is True
    assert result["reopen_policy"] == "user_feedback_first"
