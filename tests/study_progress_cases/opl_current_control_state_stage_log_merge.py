from __future__ import annotations

import importlib
from pathlib import Path

from .shared import _write_json, make_profile, write_study


def test_study_progress_merges_live_stage_log_when_handoff_study_entry_lacks_it(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    domain_status = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    mcp_projection = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        quest_id="quest-001",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="A reproducible diabetes mortality prediction manuscript.",
        paper_urls=["https://example.org/diabetes-mortality"],
        journal_shortlist=["Journal of Clinical Epidemiology"],
        minimum_sci_ready_evidence_package=["main_result_table", "claim_evidence_map"],
    )
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-05-28T13:40:08+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": None,
                    "active_stage_attempt_id": "sat-live-queue",
                    "active_workflow_id": "wf-live-queue",
                    "running_provider_attempt": True,
                    "runtime_health": {
                        "health_status": "running",
                        "runtime_liveness_status": "live",
                    },
                }
            ],
        },
    )
    live_stage_log = {
        "surface_kind": "opl_stage_progress_log_summary",
        "projection_scope": "current_control_state",
        "attempt_count": 1,
        "completed_attempt_count": 0,
        "blocked_attempt_count": 0,
        "runner_progress_event_count": 2,
        "missing_usage_telemetry_attempt_count": 1,
        "attempt_refs": ["/stage_attempt_workbench/attempts/sat-live-queue/stage_progress_log"],
        "authority_boundary": {
            "opl": "stage_attempt_progress_observability_projection_only",
            "domain": "truth_quality_artifact_gate_owner",
            "can_authorize_quality_verdict": False,
        },
    }
    monkeypatch.setattr(
        domain_status,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(profile.managed_runtime_home / "quests" / "quest-001"),
            "quest_status": "active",
            "decision": "blocked",
            "reason": "quest_waiting_opl_runtime_owner_route",
            "runtime_liveness_audit": {
                "status": "live",
                "source": "opl_current_control_state_provider_attempt",
                "provider_attempt_source": "opl_family_runtime_queue_inspect",
                "authority": "observability_only",
                "active_run_id": "opl-stage-attempt://sat-live-queue",
                "active_stage_attempt_id": "sat-live-queue",
                "active_workflow_id": "wf-live-queue",
                "running_provider_attempt": True,
                "handoff_path": str(handoff_path),
                "handoff_generated_at": "2026-05-28T13:40:08+00:00",
                "runtime_health": {
                    "health_status": "running",
                    "runtime_liveness_status": "live",
                },
                "stage_progress_log": live_stage_log,
            },
            "runtime_health_snapshot": {"health_status": "running"},
            "authority_snapshot": {},
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id="001-risk")
    compact = mcp_projection.compact_study_progress_projection(result)
    markdown = mcp_projection.render_mcp_study_progress_markdown(result)

    dashboard = result["opl_current_control_state_handoff"]
    assert dashboard["surface_kind"] == "opl_current_control_state_study_handoff"
    assert dashboard["active_run_id"] == "opl-stage-attempt://sat-live-queue"
    assert dashboard["active_stage_attempt_id"] == "sat-live-queue"
    assert dashboard["active_workflow_id"] == "wf-live-queue"
    assert dashboard["running_provider_attempt"] is True
    assert dashboard["stage_progress_log"]["attempt_count"] == 1
    assert dashboard["stage_progress_log"]["runner_progress_event_count"] == 2
    assert dashboard["stage_progress_log"]["attempt_refs"] == [
        "/stage_attempt_workbench/attempts/sat-live-queue/stage_progress_log"
    ]
    assert (
        dashboard["stage_progress_log"]["authority_boundary"]["can_authorize_quality_verdict"]
        is False
    )
    assert compact["opl_current_control_state_handoff"]["stage_progress_log"]["attempt_count"] == 1
    assert result["progress_first_monitoring_summary"]["active_stage_attempt_id"] == "sat-live-queue"
    assert result["progress_first_monitoring_summary"]["active_workflow_id"] == "wf-live-queue"
    assert result["progress_first_monitoring_summary"]["running_provider_attempt"] is True
    assert result["progress_first_monitoring_summary"]["stage_progress_log"]["attempt_count"] == 1
    assert result["progress_first_monitoring_summary"]["stage_progress_log"]["runner_progress_event_count"] == 2
    assert result["progress_first_monitoring_summary"]["authority_boundary"]["can_write_runtime_owned_surfaces"] is False
    assert "stage_progress_log: attempts `1`" in markdown


def test_study_progress_live_opl_attempt_supersedes_stale_handoff_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    domain_status = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        quest_id="quest-001",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="A reproducible diabetes mortality prediction manuscript.",
        paper_urls=["https://example.org/diabetes-mortality"],
        journal_shortlist=["Journal of Clinical Epidemiology"],
        minimum_sci_ready_evidence_package=["main_result_table"],
    )
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-01T08:09:03+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": None,
                    "running_provider_attempt": False,
                    "runtime_health": {
                        "health_status": "escalated",
                        "runtime_liveness_status": "live",
                        "blocking_reasons": ["live_worker_requires_worker_running"],
                    },
                    "why_not_applied": [
                        "opl_current_control_state.handoff_required",
                        "ai_reviewer_trace_missing",
                    ],
                    "next_owner": "external_supervisor",
                    "external_supervisor_required": True,
                    "blocked_reason": "runtime_recovery_not_authorized",
                }
            ],
        },
    )
    live_stage_log = {
        "surface_kind": "opl_stage_progress_log_summary",
        "projection_scope": "stage_attempt_workbench",
        "attempt_count": 1,
        "runner_progress_event_count": 4,
        "attempt_refs": ["/stage_attempt_workbench/attempts/sat-live/stage_progress_log"],
    }
    monkeypatch.setattr(
        domain_status,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(profile.managed_runtime_home / "quests" / "quest-001"),
            "quest_status": "active",
            "decision": "resume",
            "reason": "controller_work_unit_pending",
            "active_run_id": "opl-stage-attempt://sat-live",
            "runtime_liveness_audit": {
                "status": "live",
                "source": "opl_current_control_state_provider_attempt",
                "provider_attempt_source": "opl_family_runtime_queue_inspect",
                "authority": "observability_only",
                "active_run_id": "opl-stage-attempt://sat-live",
                "active_stage_attempt_id": "sat-live",
                "active_workflow_id": "wf-live",
                "running_provider_attempt": True,
                "handoff_path": str(handoff_path),
                "handoff_generated_at": "2026-06-01T08:10:00+00:00",
                "runtime_health": {
                    "health_status": "running",
                    "runtime_liveness_status": "live",
                },
                "stage_progress_log": live_stage_log,
            },
            "runtime_health_snapshot": {
                "health_status": "running",
                "worker_liveness_state": {"state": "live", "worker_running": True},
                "blocking_reasons": [],
            },
            "authority_snapshot": {},
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    dashboard = result["opl_current_control_state_handoff"]
    assert dashboard["active_run_id"] == "opl-stage-attempt://sat-live"
    assert dashboard["running_provider_attempt"] is True
    assert dashboard["runtime_health"]["health_status"] == "running"
    assert dashboard["runtime_health"]["runtime_liveness_status"] == "live"
    assert dashboard["external_supervisor_required"] is False
    assert dashboard["blocked_reason"] is None
    assert dashboard["why_not_applied"] == ["ai_reviewer_trace_missing"]
    assert dashboard["stage_progress_log"]["runner_progress_event_count"] == 4
    assert result["progress_first_monitoring_summary"]["active_run_id"] == "opl-stage-attempt://sat-live"
    assert result["progress_first_monitoring_summary"]["running_provider_attempt"] is True
    assert (
        result["progress_first_monitoring_summary"]["worker_liveness"]["runtime_liveness_status"]
        == "live"
    )
    assert "runtime_recovery_not_authorized" not in (
        result["user_visible_projection"].get("why_not_progressing") or ""
    )


def test_study_progress_projects_live_opl_attempt_without_stage_progress_log(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    domain_status = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        quest_id="quest-001",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="A reproducible diabetes mortality prediction manuscript.",
        paper_urls=["https://example.org/diabetes-mortality"],
        journal_shortlist=["Journal of Clinical Epidemiology"],
        minimum_sci_ready_evidence_package=["main_result_table"],
    )
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-05T03:00:00+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": None,
                    "running_provider_attempt": False,
                    "blocked_reason": "opl_stage_attempt_admission_required",
                    "why_not_applied": ["opl_stage_attempt_admission_required"],
                    "next_owner": "one-person-lab",
                    "external_supervisor_required": True,
                }
            ],
        },
    )
    monkeypatch.setattr(
        domain_status,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(profile.managed_runtime_home / "quests" / "quest-001"),
            "quest_status": "paused",
            "decision": "resume",
            "reason": "quest_paused",
            "active_run_id": "opl-stage-attempt://sat-live",
            "runtime_liveness_audit": {
                "status": "live",
                "source": "opl_current_control_state_provider_attempt",
                "provider_attempt_source": "opl_family_runtime_attempt_inspect",
                "authority": "observability_only",
                "active_run_id": "opl-stage-attempt://sat-live",
                "active_stage_attempt_id": "sat-live",
                "active_workflow_id": "wf-live",
                "running_provider_attempt": True,
                "handoff_path": str(handoff_path),
                "handoff_generated_at": "2026-06-05T03:01:00+00:00",
                "runtime_health": {
                    "health_status": "running",
                    "runtime_liveness_status": "live",
                    "provider_status": "running",
                },
            },
            "runtime_health_snapshot": {
                "health_status": "running",
                "worker_liveness_state": {"state": "live", "worker_running": True},
                "blocking_reasons": [],
            },
            "authority_snapshot": {},
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    dashboard = result["opl_current_control_state_handoff"]
    assert dashboard["active_run_id"] == "opl-stage-attempt://sat-live"
    assert dashboard["active_stage_attempt_id"] == "sat-live"
    assert dashboard["active_workflow_id"] == "wf-live"
    assert dashboard["running_provider_attempt"] is True
    assert dashboard["stage_progress_log"] == {}
    assert dashboard["runtime_health"]["health_status"] == "running"
    assert dashboard["runtime_health"]["runtime_liveness_status"] == "live"
    assert dashboard["external_supervisor_required"] is False
    assert dashboard["blocked_reason"] is None
    assert dashboard["why_not_applied"] == []
    assert result["progress_first_monitoring_summary"]["active_run_id"] == "opl-stage-attempt://sat-live"
    assert result["progress_first_monitoring_summary"]["active_stage_attempt_id"] == "sat-live"
    assert result["progress_first_monitoring_summary"]["running_provider_attempt"] is True
    assert result["progress_first_monitoring_summary"]["execution_state_kind"] == "running_provider_attempt"
    assert result["current_work_unit"]["status"] == "running_provider_attempt"
    assert result["current_execution_envelope"]["state_kind"] == "running_provider_attempt"
    assert result["active_run_id"] == "opl-stage-attempt://sat-live"
    assert result["current_stage"] == "managed_runtime_active"
    assert result["status_narration_contract"]["stage"]["current_stage"] == "managed_runtime_active"
    assert "auto_runtime_parked" not in result["operator_status_card"]
    assert "parked_state" not in result["operator_status_card"]


def test_running_provider_top_level_projection_yields_to_matching_owner_receipt_closeout() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.running_provider_status"
    )

    payload = {
        "current_stage": "auto_runtime_parked",
        "active_run_id": "opl-stage-attempt://sat-completed",
        "current_blockers": ["medical_paper_readiness_missing"],
        "current_work_unit": {"status": "running_provider_attempt"},
        "current_execution_envelope": {"state_kind": "running_provider_attempt"},
        "progress_first_monitoring_summary": {
            "running_provider_attempt": True,
            "active_stage_attempt_id": "sat-completed",
        },
        "opl_current_control_state_handoff": {
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-completed",
            "active_stage_attempt_id": "sat-completed",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
            "latest_terminal_stage_log": {
                "stage_attempt_id": "sat-completed",
                "status": "executed",
                "outcome": "owner_receipt",
                "closeout_refs": [
                    "studies/003/artifacts/supervision/consumer/default_executor_execution/"
                    "sat-completed.closeout.json",
                    "studies/003/artifacts/publication_eval/ai_reviewer_responses/"
                    "20260612T100912Z_publication_eval_record.json",
                ],
            },
        },
    }

    result = module.apply_running_provider_attempt_top_level_status(payload)

    assert result is payload
    assert result["current_stage"] == "auto_runtime_parked"
    assert result["current_blockers"] == ["medical_paper_readiness_missing"]


def test_running_provider_top_level_projection_yields_to_progress_first_terminal_closeout() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.running_provider_status"
    )

    payload = {
        "current_stage": "auto_runtime_parked",
        "active_run_id": "opl-stage-attempt://sat-completed",
        "current_blockers": ["medical_paper_readiness_missing"],
        "current_work_unit": {"status": "running_provider_attempt"},
        "current_execution_envelope": {"state_kind": "running_provider_attempt"},
        "progress_first_monitoring_summary": {
            "running_provider_attempt": True,
            "active_stage_attempt_id": "sat-completed",
            "latest_terminal_stage": {
                "stage_attempt_id": "sat-completed",
                "status": "executed",
                "outcome": "owner_receipt",
                "closeout_refs": [
                    "studies/003/artifacts/supervision/consumer/default_executor_execution/"
                    "sat-completed.closeout.json",
                ],
            },
        },
        "opl_current_control_state_handoff": {
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-completed",
            "active_stage_attempt_id": "sat-completed",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
    }

    result = module.apply_running_provider_attempt_top_level_status(payload)

    assert result is payload
    assert result["current_stage"] == "auto_runtime_parked"
    assert result["current_blockers"] == ["medical_paper_readiness_missing"]


def test_study_progress_terminal_closeout_missing_owner_answer_blocks_stale_running(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    domain_status = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        quest_id="quest-001",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="A reproducible diabetes mortality prediction manuscript.",
        paper_urls=["https://example.org/diabetes-mortality"],
        journal_shortlist=["Journal of Clinical Epidemiology"],
        minimum_sci_ready_evidence_package=["main_result_table"],
    )
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-10T12:00:00+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": "opl-stage-attempt://sat-no-answer",
                    "active_stage_attempt_id": "sat-no-answer",
                    "active_workflow_id": "wf-no-answer",
                    "running_provider_attempt": True,
                    "runtime_health": {
                        "health_status": "running",
                        "runtime_liveness_status": "live",
                    },
                    "action_queue": [
                        {
                            "action_type": "return_to_ai_reviewer_workflow",
                            "status": "ready",
                            "owner": "ai_reviewer",
                            "work_unit_id": "ai-reviewer-record",
                            "work_unit_fingerprint": "wu-fp-1",
                            "stage_attempt_id": "sat-no-answer",
                        }
                    ],
                }
            ],
        },
    )
    latest_execution_path = (
        profile.studies_root
        / "001-risk"
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json"
    )
    _write_json(
        latest_execution_path,
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "generated_at": "2026-06-10T12:01:00+00:00",
            "study_id": "001-risk",
            "executions": [
                {
                    "generated_at": "2026-06-10T12:01:00+00:00",
                    "study_id": "001-risk",
                    "stage_attempt_id": "sat-no-answer",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "execution_status": "completed",
                    "paper_stage_log": {
                        "stage_name": "return_to_ai_reviewer_workflow",
                        "problem_summary": "Provider returned terminal closeout without owner answer.",
                        "stage_goal": "Produce an AI reviewer record or typed blocker.",
                        "stage_work_done": ["Inspected current inputs."],
                        "paper_work_done": ["No publication eval was written."],
                        "changed_stage_surfaces": [],
                        "changed_paper_surfaces": [],
                        "progress_delta_classification": "platform_repair",
                        "outcome": "completed_without_owner_answer",
                        "remaining_blockers": [],
                    },
                }
            ],
        },
    )
    monkeypatch.setattr(
        domain_status,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(profile.managed_runtime_home / "quests" / "quest-001"),
            "quest_status": "active",
            "decision": "blocked",
            "reason": "quest_waiting_opl_runtime_owner_route",
            "runtime_liveness_audit": {
                "status": "live",
                "source": "opl_current_control_state_provider_attempt",
                "provider_attempt_source": "opl_family_runtime_attempt_inspect",
                "authority": "observability_only",
                "active_run_id": "opl-stage-attempt://sat-no-answer",
                "active_stage_attempt_id": "sat-no-answer",
                "active_workflow_id": "wf-no-answer",
                "running_provider_attempt": True,
                "handoff_path": str(handoff_path),
                "handoff_generated_at": "2026-06-10T12:00:00+00:00",
                "runtime_health": {
                    "health_status": "running",
                    "runtime_liveness_status": "live",
                },
            },
            "runtime_health_snapshot": {
                "health_status": "running",
                "worker_liveness_state": {"state": "live", "worker_running": True},
                "blocking_reasons": [],
            },
            "authority_snapshot": {},
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    dashboard = result["opl_current_control_state_handoff"]
    assert dashboard["running_provider_attempt"] is False
    assert dashboard["active_run_id"] is None
    assert dashboard["action_queue"] == []
    assert dashboard["typed_blocker"]["blocker_id"] == "typed_closeout_packet_required"
    monitoring = result["progress_first_monitoring_summary"]
    assert monitoring["running_provider_attempt"] is False
    assert monitoring["execution_state_kind"] == "typed_blocker"
    assert monitoring["typed_blocker"]["blocker_id"] == "typed_closeout_packet_required"
    assert "typed_closeout_packet_required" in monitoring["current_blockers"]
