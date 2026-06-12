from __future__ import annotations

import os

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
                "duration": {"status": "missing", "seconds": None},
                "token_usage": {"status": "missing", "total_tokens": None},
                "cost": {"status": "missing", "usd": None},
                "usage_refs": [],
                "cost_refs": [],
                "evidence_refs": [
                    f"studies/{study_id}/artifacts/controller/gate_clearing_batch/latest.json"
                ],
                "progress_delta_classification": "typed_blocker",
                "deliverable_progress_delta": {"count": 0, "token_usage_total": None},
                "paper_progress_delta": {"count": 0, "token_usage_total": None},
                "platform_repair_delta": {"count": 1, "token_usage_total": None},
                "next_forced_delta": {
                    "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                    "work_unit_id": work_unit,
                    "owner_action": {
                        "next_owner": "publication_gate",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit,
                    },
                },
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


def test_anti_loop_typed_closeout_supersedes_newer_stale_latest_execution_projection(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    stale_work_unit = "analysis_claim_evidence_repair"
    stale_fingerprint = "publication-blockers::497d1260db522f01"
    next_work_unit = "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
    next_fingerprint = "owner-route::write::manuscript_story_surface_delta_missing::run_quality_repair_batch"
    source_fingerprint = "mas_default_executor_source_77f18f8da1eb6e57139208c1"
    idempotency_key = "idem_cd631f437e1e7f3be53f386e"
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
            "generated_at": "2026-06-11T21:28:34+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_status": "active",
                    "running_provider_attempt": False,
                    "runtime_health": {
                        "health_status": "provider_admission_pending",
                        "runtime_liveness_status": "not_running",
                    },
                    "action_queue": [
                        {
                            "action_type": "run_quality_repair_batch",
                            "status": "queued",
                            "owner": "analysis-campaign",
                            "work_unit_id": stale_work_unit,
                            "work_unit_fingerprint": stale_fingerprint,
                            "action_fingerprint": stale_fingerprint,
                            "authority": "mas_provider_admission_identity",
                        }
                    ],
                    "next_owner": "one-person-lab",
                    "blocked_reason": "provider_admission_current_control_state_required",
                }
            ],
        },
    )
    execution_root = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
    )
    latest_execution_path = execution_root / "latest.json"
    _write_json(
        latest_execution_path,
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "generated_at": "2026-06-11T21:11:35+00:00",
            "study_id": study_id,
            "executions": [
                {
                    "generated_at": "2026-06-11T21:12:35+00:00",
                    "study_id": study_id,
                    "action_type": "run_gate_clearing_batch",
                    "execution_status": "blocked",
                    "blocked_reason": "opl_execution_authorization_required",
                    "paper_stage_log": {
                        "surface_kind": "mas_paper_facing_stage_log_summary",
                        "schema_version": 1,
                        "status": "available",
                        "stage_name": "publication_gate_replay",
                        "current_owner": "gate_clearing_batch",
                        "problem_summary": "Stale gate closeout remains blocked by OPL authorization.",
                        "stage_goal": "Produce gate replay output.",
                        "stage_work_done": ["Recorded a stale gate typed blocker."],
                        "paper_work_done": ["Recorded a stale gate typed blocker."],
                        "changed_stage_surfaces": [],
                        "changed_paper_surfaces": [],
                        "outcome": "blocked",
                        "remaining_blockers": ["opl_execution_authorization_required"],
                        "progress_delta_classification": "typed_blocker",
                        "next_forced_delta": {
                            "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                            "work_unit_id": "publication_gate_replay",
                            "owner_action": {
                                "next_owner": "gate_clearing_batch",
                                "action_type": "run_gate_clearing_batch",
                                "work_unit_id": "publication_gate_replay",
                            },
                        },
                    },
                }
            ],
        },
    )
    anti_loop_closeout_path = execution_root / "sat_82.closeout.json"
    _write_json(
        anti_loop_closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": quest_id,
            "stage_attempt_id": "sat_82",
            "stage_id": "domain_owner/default-executor-dispatch",
            "generated_at": "2026-06-11T20:11:08Z",
            "source_fingerprint": source_fingerprint,
            "idempotency_key": idempotency_key,
            "status": "closed_with_typed_blocker",
            "outcome": "repeat_suppressed_with_typed_blocker",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": stale_work_unit,
            "typed_blocker": {
                "surface_kind": "mas_domain_typed_blocker",
                "schema_version": 1,
                "blocker_kind": "anti_loop_budget_exhausted",
                "reason": "anti_loop_budget_exhausted",
                "blocker_id": "opl_execution_authorization_required",
                "owner": "one-person-lab",
                "write_permitted": False,
                "required_next_owner": "one-person-lab",
                "anti_loop_budget": {
                    "status": "exhausted",
                    "study_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": next_work_unit,
                    "work_unit_fingerprint": next_fingerprint,
                    "blocker_reason": "opl_execution_authorization_required",
                    "escalation_route": "publishability_repair_sprint",
                },
            },
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "schema_version": 1,
                "status": "available",
                "stage_name": next_work_unit,
                "current_owner": "write",
                "problem_summary": "Repeated quality repair dispatch hit the anti-loop budget.",
                "stage_goal": "Produce a story-surface delta or stable typed blocker.",
                "stage_work_done": [
                    "Observed MAS domain dispatch result execution_status=repeat_suppressed."
                ],
                "paper_work_done": [
                    "No manuscript, package, publication gate, or readiness surface was modified."
                ],
                "changed_stage_surfaces": [
                    f"studies/{study_id}/artifacts/supervision/consumer/default_executor_execution/sat_82.closeout.json"
                ],
                "changed_paper_surfaces": [],
                "outcome": "typed_blocker_anti_loop_budget_exhausted",
                "remaining_blockers": [
                    "MAS domain dispatch suppressed another run_quality_repair_batch attempt."
                ],
                "duration": {"status": "missing", "seconds": None},
                "token_usage": {"status": "missing", "total_tokens": None},
                "cost": {"status": "missing", "usd": None},
                "usage_refs": [],
                "cost_refs": [],
                "evidence_refs": [
                    f"studies/{study_id}/artifacts/supervision/consumer/default_executor_execution/sat_82.closeout.json"
                ],
                "progress_delta_classification": "typed_blocker",
                "deliverable_progress_delta": {"count": 0, "token_usage_total": None},
                "paper_progress_delta": {"count": 0, "token_usage_total": None},
                "platform_repair_delta": {"count": 1, "token_usage_total": None},
                "next_forced_delta": {
                    "required_delta_kind": "publishability_repair_sprint_or_single_typed_blocker_or_human_or_operator_gate",
                    "work_unit_id": next_work_unit,
                    "owner_action": {
                        "next_owner": "one-person-lab",
                        "action_type": "publishability_repair_sprint",
                        "work_unit_id": next_work_unit,
                    },
                    "reason": "anti_loop_budget_exhausted_for_run_quality_repair_batch_same_action_fingerprint",
                },
            },
        },
    )
    os.utime(anti_loop_closeout_path, (100.0, 100.0))
    os.utime(latest_execution_path, (200.0, 200.0))
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
                "runtime_health_epoch": "runtime-health-after-anti-loop-closeout",
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
    assert handoff["latest_terminal_stage_log"]["source_path"] == str(latest_execution_path)
    assert handoff["latest_typed_default_executor_closeout"]["source_path"] == str(
        anti_loop_closeout_path
    )
    assert handoff["typed_blocker"]["blocker_type"] == "anti_loop_budget_exhausted"
    assert handoff["typed_blocker"]["owner"] == "one-person-lab"
    assert handoff["typed_blocker"]["work_unit_id"] == next_work_unit
    assert handoff["typed_blocker"]["work_unit_fingerprint"] == next_fingerprint
    assert handoff["typed_blocker"]["source_fingerprint"] == source_fingerprint
    assert handoff["typed_blocker"]["idempotency_key"] == idempotency_key
    assert handoff["typed_blocker"]["stage_attempt_id"] == "sat_82"
    assert handoff["consumed_action_queue"][0]["work_unit_id"] == stale_work_unit
    assert handoff["action_queue"] == []
    assert current_work_unit["status"] == "typed_blocker"
    assert current_work_unit["owner"] == "one-person-lab"
    assert current_work_unit["work_unit_id"] == next_work_unit
    assert current_work_unit["state"]["typed_blocker"]["currentness_basis"]["source_fingerprint"] == (
        source_fingerprint
    )
    assert current_work_unit["state"]["typed_blocker"]["currentness_basis"]["idempotency_key"] == (
        idempotency_key
    )
    assert current_work_unit["state"]["typed_blocker"]["currentness_basis"]["stage_attempt_id"] == "sat_82"
    assert current_work_unit["state"]["owner_answer_binding"]["source_fingerprint"] == source_fingerprint
    assert current_work_unit["state"]["owner_answer_binding"]["idempotency_key"] == idempotency_key
    assert current_work_unit["state"]["owner_answer_binding"]["stage_attempt_id"] == "sat_82"
    assert current_work_unit["state"]["blocker_type"] == "anti_loop_budget_exhausted"
    assert result["current_execution_envelope"]["typed_blocker"]["source_fingerprint"] == source_fingerprint
    assert result["current_execution_envelope"]["typed_blocker"]["idempotency_key"] == idempotency_key
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
