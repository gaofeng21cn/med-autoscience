from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_study_progress_projects_opl_current_control_state_handoff_and_mcp_markdown(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    mcp_projection = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    handoff_path = profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
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
    assert compact["opl_current_control_state_handoff"]["action_queue"][0]["queue_age_hours"] == 6.0
    assert compact["opl_current_control_state_handoff"]["action_queue"][0]["action_type"] == (
        "publication_gate_specificity_required"
    )
    assert "OPL Current Control State Handoff" in markdown
    assert "publication_gate_specificity_required" in markdown
    assert "owner_pickup: `overdue`" in markdown
    assert "developer_supervisor_attention_required: `True`" in markdown
    assert "runtime_recovery_retry_budget_exhausted" in markdown


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
    handoff_path = profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-05-24T22:50:48+00:00",
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
        quest_root / ".ds" / "runtime_state.json",
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
    handoff_path = profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
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
        quest_root / ".ds" / "runtime_state.json",
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
    handoff_path = profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
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
