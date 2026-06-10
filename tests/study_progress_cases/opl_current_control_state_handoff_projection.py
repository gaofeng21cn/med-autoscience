from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def _runtime_state_path(quest_root: Path) -> Path:
    return quest_root / "artifacts" / "runtime" / "state" / "runtime_state.json"


def test_study_progress_projects_opl_current_control_state_handoff_and_mcp_markdown(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    mcp_projection = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff_projection",
            "schema_version": 1,
            "generated_at": "2026-05-04T06:00:00+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "running",
                    "active_run_id": "run-001",
                    "runtime_health": {
                        "health_status": "escalated",
                        "runtime_liveness_status": "stale",
                    },
                    "artifact_delta": {
                        "status": "stale",
                        "summary": "No meaningful artifact delta since last tick.",
                    },
                    "gate_specificity": {
                        "status": "blocked",
                        "blocked_reason": "publication_gate_specificity_required",
                    },
                    "ai_reviewer_status": {
                        "status": "trace_missing",
                        "summary": "AI reviewer workflow must recheck the repaired package.",
                    },
                    "stage_progress_log": {
                        "surface_kind": "opl_stage_progress_log_summary",
                        "projection_scope": "stage_attempt_workbench",
                        "attempt_count": 2,
                        "completed_attempt_count": 1,
                        "blocked_attempt_count": 1,
                        "duration_observed_attempt_count": 1,
                        "missing_usage_telemetry_attempt_count": 1,
                        "attempt_refs": [
                            "/stage_attempt_workbench/attempts/sat-001/stage_progress_log",
                            "/stage_attempt_workbench/attempts/sat-002/stage_progress_log",
                        ],
                        "authority_boundary": {
                            "opl": "stage_attempt_progress_observability_projection_only",
                            "domain": "truth_quality_artifact_gate_owner",
                            "can_authorize_quality_verdict": False,
                        },
                    },
                    "action_queue": [
                        {
                            "action_type": "publication_gate_specificity_required",
                            "summary": "Ask controller to specify the publication gate blocker.",
                            "fingerprint": "publication_gate_specificity_required::publication_gate_specificity_required",
                            "queue_age_hours": 6.0,
                            "owner_pickup": {
                                "state": "overdue",
                                "owner": "publication_gate",
                                "duration_hours": 6.0,
                                "pickup_overdue": True,
                            },
                            "consumption": {
                                "state": "attention_required",
                                "unconsumed_duration_hours": 6.0,
                                "developer_supervisor_attention_required": True,
                            },
                        },
                        {
                            "action_type": "return_to_ai_reviewer_workflow",
                            "summary": "Return the package to AI reviewer after gate specificity.",
                        },
                    ],
                    "queue_slo": {
                        "max_queue_age_hours": 6.0,
                        "owner_pickup_overdue_count": 1,
                        "developer_supervisor_attention_required_count": 1,
                    },
                    "owner_pickup_overdue": True,
                    "developer_supervisor_attention_required": True,
                    "why_not_applied": [
                        "runtime_recovery_retry_budget_exhausted",
                        "ai_reviewer_trace_missing",
                    ],
                    "next_owner": "external_supervisor",
                    "external_supervisor_required": True,
                    "blocked_reason": "runtime_recovery_not_authorized",
                }
            ],
        },
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "running",
            "decision": "blocked",
            "reason": "runtime_recovery_retry_budget_exhausted",
            "runtime_health_snapshot": {"attempt_state": "escalated", "retry_budget_remaining": 0},
            "authority_snapshot": {"control_state": "blocked_runtime_escalation"},
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id="001-risk")
    compact = mcp_projection.compact_study_progress_projection(result)
    markdown = mcp_projection.render_mcp_study_progress_markdown(result)

    dashboard = result["opl_current_control_state_handoff"]
    assert dashboard["source_path"] == str(handoff_path)
    assert dashboard["authority"] == "observability_only"
    assert dashboard["quest_status"] == "running"
    assert dashboard["active_run_id"] == "run-001"
    assert dashboard["runtime_health"]["health_status"] == "escalated"
    assert dashboard["artifact_delta"]["status"] == "stale"
    assert dashboard["gate_specificity"]["blocked_reason"] == "publication_gate_specificity_required"
    assert dashboard["ai_reviewer_status"]["status"] == "trace_missing"
    assert dashboard["stage_progress_log"]["surface_kind"] == "opl_stage_progress_log_summary"
    assert dashboard["stage_progress_log"]["attempt_count"] == 2
    assert dashboard["stage_progress_log"]["missing_usage_telemetry_attempt_count"] == 1
    assert dashboard["stage_progress_log"]["attempt_refs"] == [
        "/stage_attempt_workbench/attempts/sat-001/stage_progress_log",
        "/stage_attempt_workbench/attempts/sat-002/stage_progress_log",
    ]
    assert (
        dashboard["stage_progress_log"]["authority_boundary"]["can_authorize_quality_verdict"]
        is False
    )
    assert [item["action_type"] for item in dashboard["action_queue"]] == [
        "publication_gate_specificity_required",
        "return_to_ai_reviewer_workflow",
    ]
    assert dashboard["queue_slo"]["max_queue_age_hours"] == 6.0
    assert dashboard["owner_pickup_overdue"] is True
    assert dashboard["developer_supervisor_attention_required"] is True
    assert dashboard["action_queue"][0]["fingerprint"] == (
        "publication_gate_specificity_required::publication_gate_specificity_required"
    )
    assert dashboard["action_queue"][0]["source"] == "opl_current_control_state_action_queue"
    assert dashboard["action_queue"][0]["owner_pickup"]["state"] == "overdue"
    assert dashboard["action_queue"][0]["consumption"]["developer_supervisor_attention_required"] is True
    assert dashboard["why_not_applied"] == [
        "runtime_recovery_retry_budget_exhausted",
        "ai_reviewer_trace_missing",
    ]
    assert dashboard["next_owner"] == "external_supervisor"
    assert dashboard["external_supervisor_required"] is True
    assert result["refs"]["opl_current_control_state_handoff_path"] == str(handoff_path)
    assert compact["opl_current_control_state_handoff"]["blocked_reason"] == "runtime_recovery_not_authorized"
    assert compact["opl_current_control_state_handoff"]["queue_slo"]["owner_pickup_overdue_count"] == 1
    assert compact["opl_current_control_state_handoff"]["stage_progress_log"]["attempt_count"] == 2
    assert compact["opl_current_control_state_handoff"]["stage_progress_log"]["attempt_refs"] == [
        "/stage_attempt_workbench/attempts/sat-001/stage_progress_log",
        "/stage_attempt_workbench/attempts/sat-002/stage_progress_log",
    ]
    assert compact["opl_current_control_state_handoff"]["action_queue"][0]["queue_age_hours"] == 6.0
    assert compact["opl_current_control_state_handoff"]["action_queue"][0]["action_type"] == (
        "publication_gate_specificity_required"
    )
    assert compact["opl_current_control_state_handoff"]["action_queue"][0]["source"] == (
        "opl_current_control_state_action_queue"
    )
    assert "OPL Current Control State Handoff" in markdown
    assert "publication_gate_specificity_required" in markdown
    assert "owner_pickup: `overdue`" in markdown
    assert "stage_progress_log: attempts `2`" in markdown
    assert "missing_usage_telemetry_attempt_count: `1`" in markdown
    assert "developer_supervisor_attention_required: `True`" in markdown
    assert "runtime_recovery_retry_budget_exhausted" in markdown
    assert result["paper_progress_delta"]["count"] == 0
    assert result["paper_progress_delta"]["token_usage_total"] == 0
    assert result["platform_repair_delta"]["count"] == 1
def test_stage_progress_log_alone_does_not_trigger_platform_repair_delta(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff_projection",
            "schema_version": 1,
            "generated_at": "2026-05-04T06:00:00+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "running",
                    "active_run_id": "run-001",
                    "runtime_health": {"health_status": "healthy"},
                    "stage_progress_log": {"attempt_count": 1},
                    "blocked_reason": "waiting_for_quality_owner",
                    "next_owner": "write",
                }
            ],
        },
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "running",
            "decision": "continue",
            "reason": "quality_repair_followthrough",
            "runtime_health_snapshot": {"attempt_state": "running"},
            "authority_snapshot": {"control_state": "active"},
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id="001-risk")
    assert result["paper_progress_delta"]["count"] == 0
    assert result["paper_progress_delta"]["token_usage_total"] == 0
    assert result["platform_repair_delta"]["count"] == 0
    assert result["platform_repair_delta"]["token_usage_total"] == 0


def test_accepted_typed_closeout_consumes_matching_handoff_action_queue(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    work_unit = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    fingerprint = "domain-transition::route_back_same_line::dpcc"
    handoff_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-10T07:27:46+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_status": "active",
                    "active_stage_attempt_id": "sat-dm003-gate",
                    "active_run_id": "opl-stage-attempt://sat-dm003-gate",
                    "active_workflow_id": "wf-dm003-gate",
                    "running_provider_attempt": False,
                    "runtime_health": {
                        "health_status": "terminal",
                        "runtime_liveness_status": "terminal",
                    },
                    "action_queue": [
                        {
                            "action_type": "run_gate_clearing_batch",
                            "owner": "finalize",
                            "next_owner": "finalize",
                            "next_work_unit": work_unit,
                            "work_unit_id": work_unit,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "authority": "mas_provider_admission_identity",
                            "action_id": "provider-admission::dm003::run_gate_clearing_batch",
                        }
                    ],
                    "next_owner": "finalize",
                    "blocked_reason": "quest_waiting_opl_runtime_owner_route",
                }
            ],
        },
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "sat-dm003-gate.closeout.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "stage_attempt_id": "sat-dm003-gate",
            "stage_id": "domain_owner/default-executor-dispatch",
            "stage_packet_ref": (
                f"studies/{study_id}/artifacts/supervision/consumer/"
                "default_executor_dispatches/run_gate_clearing_batch.json"
            ),
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "run_gate_clearing_batch",
            "generated_at": "2026-06-10T07:20:00+00:00",
            "status": "blocked",
            "outcome": "typed_blocker",
            "blocked_reason": "publication_gate_replay_blocked",
            "domain_ready": False,
            "work_unit_id": work_unit,
            "work_unit_fingerprint": fingerprint,
            "owner_route_basis": {
                "truth_epoch": "truth::dm003::2026-06-10T07:20:00Z",
                "source_eval_id": "publication-eval::dm003::ai-reviewer-record::current",
                "work_unit_id": work_unit,
                "work_unit_fingerprint": fingerprint,
                "owner_reason": "publication_gate_replay_blocked",
            },
            "domain_execution": {
                "action_type": "run_gate_clearing_batch",
                "execution_status": "blocked",
                "blocked_reason": "publication_gate_replay_blocked",
                "domain_owner": "publication_gate",
                "execution_id": "execution::dm003::run_gate_clearing_batch::2026-06-10T07:20:00Z",
            },
            "typed_blocker": {
                "surface_kind": "mas_typed_blocker",
                "reason": "publication_gate_replay_blocked",
                "status": "blocked",
                "blockers": [
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                ],
                "current_required_action": "return_to_publishability_gate",
                "recommended_route_back": "return_to_write",
                "phase_owner": "publication_gate",
                "evidence_refs": [
                    "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/controller/gate_clearing_batch/latest.json",
                    "runtime/quests/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/reports/publishability_gate/2026-06-10T072000Z.json",
                ],
            },
            "closeout_refs": [
                f"studies/{study_id}/artifacts/supervision/consumer/default_executor_execution/sat-dm003-gate.closeout.json",
                f"studies/{study_id}/artifacts/controller/gate_clearing_batch/latest.json",
            ],
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "schema_version": 1,
                "status": "available",
                "stage_name": "publication_gate_replay",
                "current_owner": "publication_gate",
                "problem_summary": "Gate replay remains blocked after default executor closeout.",
                "stage_goal": "Return a typed blocker instead of re-running the consumed gate replay work unit.",
                "stage_work_done": ["Recorded gate replay typed blocker."],
                "paper_work_done": [
                    "No manuscript-body quality verdict or publication readiness claim was made."
                ],
                "changed_stage_surfaces": [
                    f"studies/{study_id}/artifacts/controller/gate_clearing_batch/latest.json"
                ],
                "changed_paper_surfaces": [],
                "outcome": "typed_blocker",
                "remaining_blockers": [
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                ],
                "progress_delta_classification": "typed_blocker",
            },
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": quest_id,
            "quest_root": str(profile.runtime_root / quest_id),
            "quest_status": "active",
            "decision": "blocked",
            "reason": "quest_waiting_opl_runtime_owner_route",
            "active_run_id": None,
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-event-after-gate-closeout",
                "runtime_liveness_status": "none",
                "attempt_state": "blocked",
            },
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id=study_id)

    handoff = result["opl_current_control_state_handoff"]
    current_work_unit = result["current_work_unit"]
    envelope = result["current_execution_envelope"]
    assert handoff["blocked_reason"] == "publication_gate_replay_blocked"
    assert handoff["typed_blocker"]["blocker_type"] == "publication_gate_replay_blocked"
    assert handoff["typed_blocker"]["work_unit_id"] == work_unit
    assert handoff["typed_blocker"]["work_unit_fingerprint"] == fingerprint
    assert handoff["latest_typed_default_executor_closeout"]["receipt_ref"].endswith(
        "sat-dm003-gate.closeout.json"
    )
    assert handoff["consumed_action_queue"][0]["work_unit_id"] == work_unit
    assert handoff["action_queue"] == []
    assert current_work_unit["status"] == "typed_blocker"
    assert current_work_unit["owner"] == "publication_gate"
    assert current_work_unit["work_unit_id"] == work_unit
    assert current_work_unit["work_unit_fingerprint"] == fingerprint
    assert current_work_unit["state"]["typed_blocker"]["blocker_type"] == (
        "publication_gate_replay_blocked"
    )
    assert envelope["state_kind"] == "typed_blocker"
    assert envelope["owner"] == "publication_gate"
    assert envelope["typed_blocker"]["blocker_type"] == "publication_gate_replay_blocked"
    assert result["current_executable_owner_action"] is None
    assert result["current_execution_evidence"]["action_queue"] == []


def test_terminal_closeout_without_owner_answer_fail_closes_stale_running_handoff(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    work_unit = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    fingerprint = "domain-transition::route_back_same_line::dm003"
    handoff_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-10T08:00:00+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_status": "running",
                    "active_stage_attempt_id": "sat-dm003-terminal",
                    "active_run_id": "opl-stage-attempt://sat-dm003-terminal",
                    "active_workflow_id": "wf-dm003-terminal",
                    "running_provider_attempt": True,
                    "runtime_health": {
                        "health_status": "running",
                        "runtime_liveness_status": "live",
                    },
                    "action_queue": [
                        {
                            "action_type": "run_gate_clearing_batch",
                            "owner": "publication_gate",
                            "next_owner": "publication_gate",
                            "next_work_unit": work_unit,
                            "work_unit_id": work_unit,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "authority": "mas_provider_admission_identity",
                            "stage_attempt_id": "sat-dm003-terminal",
                        }
                    ],
                    "next_owner": "supervisor_only/live_provider_attempt",
                    "blocked_reason": None,
                }
            ],
        },
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "stage_attempt_closeouts"
        / "sat-dm003-terminal.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": quest_id,
            "stage_attempt_id": "sat-dm003-terminal",
            "stage_id": "domain_owner/default-executor-dispatch",
            "action_type": "run_gate_clearing_batch",
            "generated_at": "2026-06-10T08:05:00+00:00",
            "status": "completed",
            "work_unit_id": work_unit,
            "work_unit_fingerprint": fingerprint,
            "closeout_refs": [
                f"studies/{study_id}/artifacts/supervision/consumer/"
                "stage_attempt_closeouts/sat-dm003-terminal.json"
            ],
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "schema_version": 1,
                "status": "available",
                "stage_name": "publication_gate_replay",
                "current_owner": "publication_gate",
                "problem_summary": "Terminal provider attempt did not return a MAS owner answer.",
                "stage_goal": "Consume terminal attempt into owner answer or stable typed blocker.",
                "stage_work_done": ["Observed provider attempt terminal closeout."],
                "paper_work_done": [],
                "outcome": "completed_without_owner_answer",
            },
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": quest_id,
            "quest_root": str(profile.runtime_root / quest_id),
            "quest_status": "running",
            "decision": "continue",
            "reason": "live_managed_runtime",
            "active_run_id": "opl-stage-attempt://sat-dm003-terminal",
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-before-terminal-closeout-consumption",
                "runtime_liveness_status": "live",
                "health_status": "running",
            },
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id=study_id)

    handoff = result["opl_current_control_state_handoff"]
    current_work_unit = result["current_work_unit"]
    envelope = result["current_execution_envelope"]
    assert handoff["running_provider_attempt"] is False
    assert handoff["active_run_id"] is None
    assert handoff["runtime_health"]["health_status"] == "terminal"
    assert handoff["blocked_reason"] == "typed_closeout_packet_required"
    assert handoff["typed_blocker"]["blocker_type"] == "typed_closeout_packet_required"
    assert handoff["typed_blocker"]["owner"] == "MedAutoScience"
    assert handoff["typed_blocker"]["work_unit_id"] == work_unit
    assert handoff["typed_blocker"]["work_unit_fingerprint"] == fingerprint
    assert handoff["terminal_closeout_consumed"] is True
    assert handoff["consumed_action_queue"][0]["consumption"]["state"] == (
        "consumed_by_terminal_stage_closeout"
    )
    assert handoff["action_queue"] == []
    assert current_work_unit["status"] == "typed_blocker"
    assert current_work_unit["owner"] == "MedAutoScience"
    assert current_work_unit["state"]["typed_blocker"]["source"] == (
        "terminal_stage_closeout_missing_owner_answer"
    )
    assert envelope["state_kind"] == "typed_blocker"
    assert envelope["owner"] == "MedAutoScience"
    assert result["current_executable_owner_action"] is None
    assert result["current_execution_evidence"]["action_queue"] == []


def test_supervisor_tick_audit_uses_workspace_opl_current_control_state(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runtime_decision = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.publication_and_submission"
    )
    status_module = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-05-24T22:50:48+00:00",
            "provider_readiness": {
                "surface_kind": "opl_provider_readiness_projection",
                "source": "opl_family_runtime_status",
                "provider_kind": "temporal",
                "provider_ready": True,
                "worker_ready": True,
                "managed_worker_source_current": True,
            },
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "running",
                    "active_run_id": "run-001",
                    "runtime_health": {"health_status": "running"},
                }
            ],
        },
    )
    monkeypatch.setattr(
        runtime_decision,
        "_supervisor_tick_now",
        lambda: datetime.fromisoformat("2026-05-24T22:52:00+00:00"),
    )
    status = status_module.ProgressProjectionStatus.from_payload(
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
                "auto_resume": True,
            },
            "quest_id": "quest-001",
            "quest_root": str(profile.managed_runtime_home / "quests" / "quest-001"),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
        }
    )

    runtime_decision._record_supervisor_tick_audit(status=status, study_root=study_root)

    audit = status.extras["supervisor_tick_audit"]
    assert audit["status"] == "fresh"
    assert audit["reason"] == "opl_current_control_state_handoff_fresh"
    assert audit["latest_report_path"] == str(handoff_path)
    assert audit["latest_recorded_at"] == "2026-05-24T22:50:48+00:00"
    assert audit["seconds_since_latest_recorded_at"] == 72
    assert audit["provider_readiness"]["source"] == "opl_family_runtime_status"
    assert audit["provider_ready"] is True
    assert audit["worker_ready"] is True
    assert audit["managed_worker_source_current"] is True


def test_progress_projection_uses_opl_current_control_state_as_live_liveness_projection(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    publication_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.publication_and_submission"
    )
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
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_json(
        _runtime_state_path(quest_root),
        {
            "status": "active",
            "active_run_id": None,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "turn_closeout",
            "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
            "pending_user_message_count": 0,
        },
    )
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text("quest_id: quest-001\nstudy_id: 001-risk\n", encoding="utf-8")
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-05-24T22:50:48+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": "opl-stage-attempt://sat-live-001",
                    "active_stage_attempt_id": "sat-live-001",
                    "active_workflow_id": "wf-live-001",
                    "running_provider_attempt": True,
                    "runtime_health": {
                        "health_status": "running",
                        "runtime_liveness_status": "live",
                    },
                }
            ],
        },
    )
    monkeypatch.setattr(
        publication_module,
        "_supervisor_tick_now",
        lambda: datetime.fromisoformat("2026-05-24T22:52:00+00:00"),
    )

    result = module.progress_projection(profile=profile, study_id="001-risk")

    runtime_liveness = result["runtime_liveness_audit"]
    assert runtime_liveness["status"] == "live"
    assert runtime_liveness["source"] == "opl_current_control_state_provider_attempt"
    assert runtime_liveness["active_run_id"] == "opl-stage-attempt://sat-live-001"
    assert runtime_liveness["active_stage_attempt_id"] == "sat-live-001"
    assert runtime_liveness["active_workflow_id"] == "wf-live-001"
    assert runtime_liveness["provider_completion_is_domain_completion"] is False
    assert runtime_liveness["authority"] == "observability_only"
    assert "domain_ready" not in runtime_liveness
    assert "publication_ready" not in runtime_liveness
    assert "artifact_ready" not in runtime_liveness
    assert result["execution_owner_guard"]["guard_reason"] == "live_managed_runtime"
    assert result["execution_owner_guard"]["active_run_id"] == "opl-stage-attempt://sat-live-001"
    assert result["continuation_state"]["active_run_id"] == "opl-stage-attempt://sat-live-001"
    assert result["continuation_state"]["continuation_policy"] == "auto"
    assert result["continuation_state"]["continuation_anchor"] == "decision"
    assert result["continuation_state"]["continuation_reason"] == "controller_work_unit_pending"
    assert result["active_run_id"] == "opl-stage-attempt://sat-live-001"


def test_progress_projection_uses_opl_live_attempt_when_runtime_state_waiting_for_user(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    publication_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.publication_and_submission"
    )
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
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_json(
        _runtime_state_path(quest_root),
        {
            "status": "waiting_for_user",
            "active_run_id": None,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "turn_closeout",
            "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
            "pending_user_message_count": 3,
        },
    )
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text("quest_id: quest-001\nstudy_id: 001-risk\n", encoding="utf-8")
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-05-29T09:31:45+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "waiting_for_user",
                    "active_run_id": "opl-stage-attempt://sat-live-waiting",
                    "active_stage_attempt_id": "sat-live-waiting",
                    "active_workflow_id": "wf-live-waiting",
                    "running_provider_attempt": True,
                    "runtime_health": {
                        "health_status": "running",
                        "runtime_liveness_status": "live",
                    },
                }
            ],
        },
    )
    monkeypatch.setattr(
        publication_module,
        "_supervisor_tick_now",
        lambda: datetime.fromisoformat("2026-05-29T09:32:00+00:00"),
    )

    result = module.progress_projection(profile=profile, study_id="001-risk")

    runtime_liveness = result["runtime_liveness_audit"]
    assert runtime_liveness["status"] == "live"
    assert runtime_liveness["source"] == "opl_current_control_state_provider_attempt"
    assert runtime_liveness["active_run_id"] == "opl-stage-attempt://sat-live-waiting"
    assert result["execution_owner_guard"]["guard_reason"] == "live_managed_runtime"
    assert result["execution_owner_guard"]["active_run_id"] == "opl-stage-attempt://sat-live-waiting"
    assert result["continuation_state"]["active_run_id"] == "opl-stage-attempt://sat-live-waiting"
    assert result["continuation_state"]["continuation_policy"] == "auto"
    assert result["continuation_state"]["continuation_anchor"] == "decision"
    assert result["continuation_state"]["continuation_reason"] == "controller_work_unit_pending"
    assert result["active_run_id"] == "opl-stage-attempt://sat-live-waiting"


def test_progress_projection_uses_live_opl_queue_attempt_when_handoff_is_stale(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    decision_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.domain_status_authority"
    )
    publication_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.publication_and_submission"
    )
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
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_json(
        _runtime_state_path(quest_root),
        {
            "status": "active",
            "active_run_id": None,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "turn_closeout",
            "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
            "pending_user_message_count": 0,
        },
    )
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text("quest_id: quest-001\nstudy_id: 001-risk\n", encoding="utf-8")
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-05-26T20:11:03+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": None,
                    "running_provider_attempt": False,
                    "runtime_health": {
                        "health_status": "escalated",
                        "runtime_liveness_status": "stale",
                    },
                }
            ],
        },
    )

    monkeypatch.setattr(
        decision_module.opl_provider_attempts,
        "live_provider_attempt_for_study",
        lambda **_: {
            "surface_kind": "opl_current_control_state_provider_attempt",
            "source": "opl_family_runtime_queue_inspect",
            "active_run_id": "opl-stage-attempt://sat-live-queue",
            "active_stage_attempt_id": "sat-live-queue",
            "active_workflow_id": "wf-live-queue",
            "running_provider_attempt": True,
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
                "provider_status": "running",
            },
        },
    )
    monkeypatch.setattr(
        publication_module,
        "_supervisor_tick_now",
        lambda: datetime.fromisoformat("2026-05-26T20:16:00+00:00"),
    )

    result = module.progress_projection(profile=profile, study_id="001-risk")

    runtime_liveness = result["runtime_liveness_audit"]
    assert runtime_liveness["status"] == "live"
    assert runtime_liveness["source"] == "opl_current_control_state_provider_attempt"
    assert runtime_liveness["provider_attempt_source"] == "opl_family_runtime_queue_inspect"
    assert runtime_liveness["active_run_id"] == "opl-stage-attempt://sat-live-queue"
    assert runtime_liveness["active_stage_attempt_id"] == "sat-live-queue"
    assert runtime_liveness["active_workflow_id"] == "wf-live-queue"
    assert runtime_liveness["handoff_path"] == str(handoff_path)
    assert runtime_liveness["handoff_generated_at"] == "2026-05-26T20:11:03+00:00"
    assert runtime_liveness["provider_completion_is_domain_completion"] is False
    assert "domain_ready" not in runtime_liveness
    assert "publication_ready" not in runtime_liveness
    assert "artifact_ready" not in runtime_liveness
    assert result["execution_owner_guard"]["guard_reason"] == "live_managed_runtime"
    assert result["execution_owner_guard"]["active_run_id"] == "opl-stage-attempt://sat-live-queue"
    assert result["continuation_state"]["active_run_id"] == "opl-stage-attempt://sat-live-queue"
    assert result["continuation_state"]["continuation_policy"] == "auto"
    assert result["active_run_id"] == "opl-stage-attempt://sat-live-queue"


def test_progress_projection_uses_live_opl_attempt_when_quest_state_is_paused(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    decision_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.domain_status_authority"
    )
    publication_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.publication_and_submission"
    )
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
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_json(
        _runtime_state_path(quest_root),
        {
            "status": "paused",
            "active_run_id": None,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "turn_closeout",
            "continuation_reason": "quest_paused",
            "pending_user_message_count": 0,
        },
    )
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text("quest_id: quest-001\nstudy_id: 001-risk\n", encoding="utf-8")
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-05T03:00:00+00:00",
            "authority": "observability_only",
            "studies": [],
        },
    )

    monkeypatch.setattr(
        decision_module.opl_provider_attempts,
        "live_provider_attempt_for_study",
        lambda **_: {
            "surface_kind": "opl_current_control_state_provider_attempt",
            "source": "opl_family_runtime_attempt_inspect",
            "active_run_id": "opl-stage-attempt://sat-live-paused",
            "active_stage_attempt_id": "sat-live-paused",
            "active_workflow_id": "wf-live-paused",
            "running_provider_attempt": True,
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
                "provider_status": "running",
            },
        },
    )
    monkeypatch.setattr(
        publication_module,
        "_supervisor_tick_now",
        lambda: datetime.fromisoformat("2026-06-05T03:01:00+00:00"),
    )

    result = module.progress_projection(profile=profile, study_id="001-risk")

    runtime_liveness = result["runtime_liveness_audit"]
    assert runtime_liveness["status"] == "live"
    assert runtime_liveness["source"] == "opl_current_control_state_provider_attempt"
    assert runtime_liveness["provider_attempt_source"] == "opl_family_runtime_attempt_inspect"
    assert runtime_liveness["active_run_id"] == "opl-stage-attempt://sat-live-paused"
    assert runtime_liveness["active_stage_attempt_id"] == "sat-live-paused"
    assert runtime_liveness["active_workflow_id"] == "wf-live-paused"
    assert runtime_liveness["snapshot"] == {"status": "paused"}
    assert result["execution_owner_guard"]["guard_reason"] == "live_managed_runtime"
    assert result["execution_owner_guard"]["active_run_id"] == "opl-stage-attempt://sat-live-paused"
    assert result["continuation_state"]["active_run_id"] == "opl-stage-attempt://sat-live-paused"
    assert result["continuation_state"]["continuation_policy"] == "auto"
    assert result["continuation_state"]["continuation_anchor"] == "decision"
    assert result["continuation_state"]["continuation_reason"] == "controller_work_unit_pending"
    assert result["active_run_id"] == "opl-stage-attempt://sat-live-paused"


def test_progress_projection_treats_terminal_opl_success_handoff_as_settled_not_unhealthy(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    decision_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.domain_status_authority"
    )
    publication_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.publication_and_submission"
    )
    profile = make_profile(tmp_path)
    profile.runtime_root.mkdir(parents=True)
    medautosci_config = profile.workspace_root / "ops" / "medautoscience" / "config.env"
    medautosci_config.parent.mkdir(parents=True, exist_ok=True)
    medautosci_config.write_text("MEDAUTOSCI_PROFILE=diabetes\n", encoding="utf-8")
    controlled_backend = profile.workspace_root / "ops" / "mas"
    (controlled_backend / "bin").mkdir(parents=True, exist_ok=True)
    (controlled_backend / "config.env").write_text("MEDAUTOSCI_PROFILE=diabetes\n", encoding="utf-8")
    behavior_gate = controlled_backend / "behavior_equivalence_gate.yaml"
    behavior_gate.parent.mkdir(parents=True, exist_ok=True)
    behavior_gate.write_text(
        "\n".join(
            [
                "schema_version: v1",
                "phase_25_ready: true",
                "critical_overrides: []",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
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
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_json(
        _runtime_state_path(quest_root),
        {
            "status": "active",
            "active_run_id": None,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "turn_closeout",
            "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
            "pending_user_message_count": 0,
        },
    )
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text("quest_id: quest-001\nstudy_id: 001-risk\n", encoding="utf-8")
    _write_publication_eval(study_root, quest_root)
    _write_controller_decision(
        study_root,
        quest_root,
        decision_type="route_back_same_line",
        requires_human_confirmation=False,
        action_type="run_quality_repair_batch",
        reason="Route the current paper blocker to the owner work unit.",
    )
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-05-28T08:43:37+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": None,
                    "active_stage_attempt_id": None,
                    "active_workflow_id": None,
                    "running_provider_attempt": False,
                    "handoff_generated_at": "2026-05-28T08:43:37+00:00",
                    "task_id": "frt-terminal-success",
                    "task_kind": "domain_route/reconcile-apply",
                    "current_attempt_state": "succeeded",
                    "reconciliation_status": "succeeded",
                    "terminal_provider_transport_observation_superseded": True,
                    "superseded_terminal_observation_reason": "temporal_workflow_not_started_or_not_found",
                    "superseded_by_task_status": "succeeded",
                    "next_work_unit": {
                        "unit_id": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
                        "lane": "analysis-campaign",
                        "summary": (
                            "Add uncertainty intervals, grouped calibration evidence, "
                            "and reproducibility details."
                        ),
                    },
                    "runtime_health": {
                        "health_status": "settled",
                        "runtime_liveness_status": "none",
                        "summary": (
                            "OPL queue transport is terminal succeeded and no provider attempt is live."
                        ),
                    },
                }
            ],
        },
    )
    monkeypatch.setattr(decision_module.opl_provider_attempts, "live_provider_attempt_for_study", lambda **_: None)
    monkeypatch.setattr(
        publication_module,
        "_supervisor_tick_now",
        lambda: datetime.fromisoformat("2026-05-28T08:45:00+00:00"),
    )

    result = module.progress_projection(profile=profile, study_id="001-risk")

    runtime_liveness = result["runtime_liveness_audit"]
    assert runtime_liveness["status"] == "none"
    assert runtime_liveness["source"] == "opl_current_control_state_terminal_transport_settled"
    assert runtime_liveness["active_run_id"] is None
    assert runtime_liveness["running_provider_attempt"] is False
    assert runtime_liveness["reconciliation_status"] == "succeeded"
    assert runtime_liveness["current_attempt_state"] == "succeeded"
    assert runtime_liveness["terminal_provider_transport_observation_superseded"] is True
    assert runtime_liveness["provider_completion_is_domain_completion"] is False
    assert result.get("active_run_id") is None
    assert "execution_owner_guard" not in result
    assert result["decision"] == "resume"
    assert result["reason"] == "domain_transition_ai_reviewer_re_eval"
    assert result["runtime_health_snapshot"]["canonical_runtime_action"] == "continue_supervising_runtime"
    assert result["runtime_health_snapshot"]["worker_liveness_state"]["state"] == "not_live"
    assert "runtime_recovery_retry_budget_exhausted" not in result["runtime_health_snapshot"]["blocking_reasons"]


def test_study_progress_projects_stage_log_from_live_opl_queue_when_handoff_lacks_study(
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
            "generated_at": "2026-05-26T20:11:03+00:00",
            "authority": "observability_only",
            "studies": [{"study_id": "other-study"}],
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
                "provider_attempt_source": "opl_family_runtime_queue_inspect",
                "authority": "observability_only",
                "active_run_id": "opl-stage-attempt://sat-live-queue",
                "active_stage_attempt_id": "sat-live-queue",
                "active_workflow_id": "wf-live-queue",
                "running_provider_attempt": True,
                "handoff_path": str(handoff_path),
                "handoff_generated_at": "2026-05-26T20:11:03+00:00",
                "runtime_health": {
                    "health_status": "running",
                    "runtime_liveness_status": "live",
                },
                "stage_progress_log": {
                    "surface_kind": "opl_stage_progress_log_summary",
                    "projection_scope": "stage_attempt_workbench",
                    "attempt_count": 3,
                    "completed_attempt_count": 2,
                    "blocked_attempt_count": 1,
                    "missing_usage_telemetry_attempt_count": 1,
                    "attempt_refs": [
                        "/stage_attempt_workbench/attempts/sat-live-queue/stage_progress_log"
                    ],
                    "authority_boundary": {
                        "opl": "stage_attempt_progress_observability_projection_only",
                        "domain": "truth_quality_artifact_gate_owner",
                        "can_authorize_quality_verdict": False,
                    },
                },
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
    assert dashboard["surface_kind"] == "opl_current_control_state_provider_attempt_handoff"
    assert dashboard["source_path"] == str(handoff_path)
    assert dashboard["authority"] == "observability_only"
    assert dashboard["active_run_id"] == "opl-stage-attempt://sat-live-queue"
    assert dashboard["stage_progress_log"]["attempt_count"] == 3
    assert dashboard["stage_progress_log"]["attempt_refs"] == [
        "/stage_attempt_workbench/attempts/sat-live-queue/stage_progress_log"
    ]
    assert (
        dashboard["stage_progress_log"]["authority_boundary"]["can_authorize_quality_verdict"]
        is False
    )
    assert compact["opl_current_control_state_handoff"]["stage_progress_log"]["attempt_count"] == 3
    assert "stage_progress_log: attempts `3`" in markdown
