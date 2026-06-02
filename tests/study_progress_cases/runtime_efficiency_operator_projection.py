from __future__ import annotations

from . import shared as _shared
from .runtime_projection_basics import _write_runtime_efficiency_fixture


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_study_progress_operator_view_surfaces_noop_suppression_and_runtime_efficiency(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_publication_eval(study_root, quest_root)
    telemetry_path, evidence_index_path = _write_runtime_efficiency_fixture(quest_root)
    gate_batch_path = study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
    _write_json(
        gate_batch_path,
        {
            "schema_version": 1,
            "source_eval_id": "publication-eval::001-risk::quest-001::2026-04-10T09:00:00+00:00",
            "status": "executed",
            "gate_replay": {"status": "clear", "allow_write": True, "blockers": []},
            "gate_replay_step": {
                "step_id": "publication_gate_replay",
                "status": "clear",
                "finished_at": "2026-04-28T10:01:00+00:00",
            },
        },
    )
    domain_health_diagnostic_path = quest_root / "artifacts" / "reports" / "domain_health_diagnostic" / "latest.json"
    _write_json(
        domain_health_diagnostic_path,
        {
            "schema_version": 1,
            "scanned_at": "2026-04-28T10:00:00+00:00",
            "quest_root": str(quest_root),
            "quest_status": "running",
            "controllers": {
                "publication_gate": {
                    "status": "blocked",
                    "action": "suppressed",
                    "blockers": ["claim_evidence_consistency_failed"],
                    "suppression_reason": "unchanged_fingerprint",
                    "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                }
            },
            "managed_study_no_op_suppressions": [
                {
                    "study_id": "001-risk",
                    "quest_id": "quest-001",
                    "outcome": "skipped_matching_work_unit",
                    "reason": "outer-loop work unit already dispatched for the same blocker fingerprint",
                    "dedupe_scope": "controller_decision_blocker_authority",
                    "work_unit_fingerprint": "publication-blockers::same",
                    "next_work_unit": {
                        "unit_id": "analysis_claim_evidence_repair",
                        "lane": "analysis-campaign",
                        "summary": "Repair claim-evidence blockers.",
                    },
                    "operator_summary": "同一 blocker fingerprint 已执行过同一 controller work unit；继续空转不会增加论文证据。",
                }
            ],
            "runtime_efficiency": {
                "run_id": "run-001",
                "evidence_packet_index_path": str(evidence_index_path),
                "evidence_packet_count": 1,
                "latest_evidence_packets": [
                    {
                        "tool_name": "bash_exec",
                        "detail": "compact",
                        "summary": "bash_exec: log_line_count=1200; key_blockers=1",
                        "sidecar_path": str(evidence_index_path.parent / "bash_exec-large-log.json"),
                    }
                ],
                "gate_cache_surfaces": [
                    {
                        "surface_id": "publication_gate",
                        "input_fingerprint": "publication-gate-fp-1",
                    }
                ],
            },
        },
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-001", "auto_resume": True},
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "decision": "blocked",
            "reason": "study_completion_publishability_gate_blocked",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["runtime_efficiency"]["telemetry_path"] == str(telemetry_path)
    assert result["runtime_efficiency"]["tool_result_bytes_saved_total"] == 86420
    assert result["runtime_efficiency"]["unique_command_count"] == 3
    assert result["runtime_efficiency"]["repeated_read_result_count"] == 2
    assert result["runtime_efficiency"]["repeated_read_ratio"] == 0.5
    assert result["runtime_efficiency"]["gate_replay_hit_count"] == 1
    assert result["operator_status_card"]["no_op_suppression"]["outcome"] == "skipped_matching_work_unit"
    assert "继续空转不会增加论文证据" in result["operator_status_card"]["current_focus"]
    assert "evidence packet" in result["operator_status_card"]["runtime_efficiency_summary"]
    assert "repeated reads 2/4" in result["operator_status_card"]["runtime_efficiency_summary"]
    assert "saved bytes 86420" in result["operator_status_card"]["runtime_efficiency_summary"]
    assert "gate replay hits 1" in result["operator_status_card"]["runtime_efficiency_summary"]
    assert result["operator_status_card"]["runtime_efficiency_metrics"]["unique_command_count"] == 3
    assert result["operator_status_card"]["runtime_efficiency_metrics"]["gate_replay_hit_count"] == 1
    assert result["operator_status_card"]["runtime_efficiency_refs"]["evidence_packet_index_path"] == str(evidence_index_path)


def test_study_progress_projects_autonomy_slo_ai_doctor_state(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_publication_eval(study_root, quest_root)
    _write_json(
        study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json",
        {
            "surface": "autonomy_progress_slo_status",
            "schema_version": 1,
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "state": "breach",
            "breach_types": ["gate_closure_drift"],
            "ai_doctor_request_required": True,
            "ai_doctor_state": "request_ready",
            "ai_doctor_request": {"request_id": "ai-doctor-request::001", "state": "request_ready"},
            "repair_recommendation": {
                "state": "awaiting_ai_doctor",
                "action_count": 2,
                "top_action": {"action_type": "ai_doctor_diagnosis"},
            },
            "last_meaningful_progress_at": "2026-04-30T12:00:00+00:00",
            "quality_gate_relaxation_allowed": False,
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "execution": {"quest_id": "quest-001", "auto_resume": True},
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "decision": "blocked",
            "reason": "study_completion_publishability_gate_blocked",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "current_required_action": "return_to_publishability_gate",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["autonomy_slo"]["state"] == "breach"
    assert result["ai_doctor_state"] == {"request_id": "ai-doctor-request::001", "state": "request_ready"}
    assert result["repair_recommendation"]["state"] == "awaiting_ai_doctor"
    assert result["last_meaningful_progress_at"] == "2026-04-30T12:00:00+00:00"
    assert result["refs"]["autonomy_slo_status_path"].endswith("artifacts/autonomy/slo_status/latest.json")


def test_study_progress_materializes_autonomy_slo_when_surface_is_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_publication_eval(study_root, quest_root)
    slo_path = study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json"

    def _materialize_slo(**kwargs):
        assert kwargs["study_root"] == study_root
        payload = {
            "surface": "autonomy_progress_slo_status",
            "schema_version": 1,
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "state": "ok",
            "breach_types": [],
            "ai_doctor_request_required": False,
            "ai_doctor_state": "not_required",
            "quality_gate_relaxation_allowed": False,
        }
        _write_json(slo_path, payload)
        return {"autonomy_progress_slo_status": payload}

    monkeypatch.setattr(profiler, "profile_study_cycle", _materialize_slo)
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "execution": {"quest_id": "quest-001", "auto_resume": True},
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "decision": "blocked",
            "reason": "study_completion_publishability_gate_blocked",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "current_required_action": "return_to_publishability_gate",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["autonomy_slo"]["state"] == "ok"
    assert result["refs"]["autonomy_slo_status_path"] == str(slo_path)
    assert slo_path.exists()


def test_study_progress_projects_completed_parked_auto_continue_without_live_run(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    run_id = "run-parked-001"
    run_root = quest_root / ".ds" / "runs" / run_id
    _write_json(
        run_root / "command.json",
        {
            "turn_reason": "auto_continue",
            "turn_mode": "parked",
            "turn_intent": "continue_stage",
        },
    )
    _write_json(
        run_root / "result.json",
        {
            "run_id": run_id,
            "exit_code": 0,
            "output_text": "No new user message or /resume; staying parked.",
        },
    )
    _write_publication_eval(study_root, quest_root)

    monkeypatch.setattr(
        profiler,
        "profile_study_cycle",
        lambda **_: {
            "autonomy_progress_slo_status": {
                "surface": "autonomy_progress_slo_status",
                "schema_version": 1,
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "state": "ok",
                "breach_types": [],
                "ai_doctor_request_required": False,
                "ai_doctor_state": "not_required",
                "quality_gate_relaxation_allowed": False,
            }
        },
    )

    result = module.build_study_progress_projection(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        status_payload={
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "execution": {"quest_id": "quest-001", "auto_resume": True},
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "runtime_liveness_status": "live",
            "active_run_id": run_id,
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": run_id,
                "runtime_audit": {"worker_running": True, "active_run_id": run_id},
            },
            "autonomous_runtime_notice": {
                "active_run_id": run_id,
                "browser_url": "http://127.0.0.1:20999",
            },
        },
    )

    assert result["auto_runtime_parked"]["parked"] is True
    assert result["parked_state"] == "explicit_resume_pending"
    assert result["supervision"]["active_run_id"] is None
    assert result["operator_status_card"]["handling_state"] == "explicit_resume_pending"


def test_study_progress_prioritizes_no_live_recovery_over_closeout_continuation(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_publication_eval(study_root, quest_root)
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "recorded_at": "2026-05-01T03:19:43+00:00",
            "health_status": "recovering",
            "summary": "系统已检测到运行掉线，正在自动尝试恢复。",
            "next_action_summary": "等待下一次巡检确认 worker 已重新上线并恢复 live。",
        },
    )
    monkeypatch.setattr(
        profiler,
        "profile_study_cycle",
        lambda **_: {
            "autonomy_progress_slo_status": {
                "surface": "autonomy_progress_slo_status",
                "schema_version": 1,
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "state": "ok",
                "breach_types": [],
                "ai_doctor_request_required": False,
                "ai_doctor_state": "not_required",
                "quality_gate_relaxation_allowed": False,
            }
        },
    )

    result = module.build_study_progress_projection(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        status_payload={
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "product",
            "execution": {"quest_id": "quest-001", "auto_resume": True},
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "active",
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "runtime_liveness_status": "unknown",
            "active_run_id": None,
            "runtime_liveness_audit": {
                "status": "unknown",
                "active_run_id": None,
                "runtime_audit": {
                    "status": "unknown",
                    "active_run_id": None,
                    "worker_running": False,
                },
            },
            "continuation_state": {
                "quest_status": "active",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "parked_after_checkpoint_no_new_message",
            },
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
            },
        },
    )

    assert result["current_stage"] == "managed_runtime_recovering"
    assert result["auto_runtime_parked"]["parked"] is False
    assert result["auto_runtime_parked"]["parked_state"] is None
    assert result["auto_runtime_parked"]["source_reason"] == "quest_marked_running_but_no_live_session"
    assert result["supervision"]["active_run_id"] is None
    assert result["supervision"]["health_status"] == "recovering"
    assert result["module_surfaces"]["runtime"]["health_status"] == "recovering"
    assert result["operator_status_card"]["handling_state"] == "runtime_recovering"


def test_study_progress_merges_autonomy_slo_refs_into_existing_projection(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    slo_path = study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json"
    _write_json(
        slo_path,
        {
            "surface": "autonomy_progress_slo_status",
            "schema_version": 1,
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "state": "breach",
            "breach_types": ["read_churn_without_artifact_delta"],
            "ai_doctor_request_required": True,
            "ai_doctor_state": "request_ready",
            "ai_doctor_request": {"request_id": "ai-doctor-request::001", "state": "request_ready"},
            "repair_recommendation": {
                "state": "awaiting_ai_doctor",
                "action_count": 1,
                "top_action": {"action_type": "ai_doctor_diagnosis"},
            },
            "last_meaningful_progress_at": "2026-04-30T12:00:00+00:00",
            "quality_gate_relaxation_allowed": False,
        },
    )

    result = module.build_study_progress_projection(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        status_payload={
            "progress_projection": {
                "schema_version": 1,
                "study_id": "001-risk",
                "current_stage": "publication_supervision",
                "current_stage_summary": "当前主线仍需先回到发表门控。",
                "paper_stage": "publishability_gate_blocked",
                "paper_stage_summary": "当前发表门控仍未放行。",
                "next_system_action": "先回到发表门控。",
                "needs_physician_decision": False,
                "refs": {"autonomy_slo_status_path": None},
            }
        },
    )

    assert result["autonomy_slo"]["breach_types"] == ["read_churn_without_artifact_delta"]
    assert result["ai_doctor_state"] == {"request_id": "ai-doctor-request::001", "state": "request_ready"}
    assert result["repair_recommendation"]["state"] == "awaiting_ai_doctor"
    assert result["last_meaningful_progress_at"] == "2026-04-30T12:00:00+00:00"
    assert result["refs"]["autonomy_slo_status_path"] == str(slo_path)


def test_study_progress_freshness_uses_gate_clearing_batch_closure_as_progress_signal(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    eval_id = "publication-eval::001-risk::quest-001::2026-04-10T09:00:00+00:00"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": eval_id,
            "emitted_at": "2026-04-09T09:00:00+00:00",
            "verdict": {"status": "blocked", "summary": "旧发表评估仍有阻塞。"},
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": eval_id,
            "status": "executed",
            "gate_replay": {"status": "clear", "allow_write": True, "blockers": []},
            "gate_replay_step": {
                "step_id": "publication_gate_replay",
                "status": "clear",
                "finished_at": "2026-04-10T09:58:00+00:00",
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {
            "recorded_at": "2026-04-10T09:59:00+00:00",
            "health_status": "live",
            "summary": "runtime heartbeat only",
        },
    )
    _write_json(
        study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json",
        {
            "surface": "autonomy_progress_slo_status",
            "schema_version": 1,
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "state": "ok",
            "breach_types": [],
            "last_meaningful_progress_at": "2026-04-10T09:58:00+00:00",
            "mds_progress_markers": {
                "meaningful_artifact_delta_at": "2026-04-10T09:58:00+00:00",
                "meaningful_artifact_delta_kind": "gate_clearing_batch",
            },
            "ai_doctor_request_required": False,
            "ai_doctor_state": "not_required",
            "quality_gate_relaxation_allowed": False,
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-001", "auto_resume": True},
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "runtime_liveness_status": "live",
            "active_run_id": "run-live-001",
            "worker_running": True,
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-live-001",
                "runtime_audit": {"worker_running": True, "active_run_id": "run-live-001"},
            },
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "current_required_action": "return_to_publishability_gate",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 4, 10, 10, 0, tzinfo=timezone.utc),
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["progress_freshness"]["status"] == "fresh"
    assert result["progress_freshness"]["latest_progress_source"] == "gate_clearing_batch"
    assert "gate-clearing batch" in result["progress_freshness"]["latest_progress_summary"]


def test_study_progress_freshness_separates_supervisor_tick_from_artifact_delta(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-dm",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    _write_publication_eval(study_root, quest_root)
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {
            "recorded_at": "2026-05-02T01:45:00+00:00",
            "health_status": "live",
            "summary": "supervisor tick only",
        },
    )
    _write_json(
        study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json",
        {
            "surface": "autonomy_progress_slo_status",
            "schema_version": 1,
            "study_id": "002-dm",
            "quest_id": "quest-002",
            "state": "breach",
            "breach_types": ["read_churn_without_artifact_delta"],
            "last_meaningful_progress_at": "2026-05-01T18:30:00+00:00",
            "mds_progress_markers": {
                "meaningful_artifact_delta_at": "2026-05-01T18:30:00+00:00",
                "turn_progress_kind": "read_churn_without_artifact_delta",
            },
            "ai_doctor_request_required": True,
            "ai_doctor_state": "request_ready",
            "quality_gate_relaxation_allowed": False,
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "002-dm",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-002", "auto_resume": True},
            "quest_id": "quest-002",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "active",
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "runtime_liveness_status": "live",
            "active_run_id": None,
            "worker_running": True,
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
                "latest_recorded_at": "2026-05-02T01:45:00+00:00",
            },
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "current_required_action": "return_to_publishability_gate",
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 5, 2, 7, 0, tzinfo=timezone.utc),
    )

    result = module.read_study_progress(profile=profile, study_id="002-dm")

    assert result["progress_freshness"]["status"] == "stale"
    assert result["progress_freshness"]["supervisor_tick_freshness"]["status"] == "fresh"
    assert result["progress_freshness"]["worker_liveness_freshness"]["status"] == "invalid"
    assert result["progress_freshness"]["meaningful_artifact_delta_freshness"]["status"] == "stale"
    assert result["progress_freshness"]["meaningful_artifact_delta_freshness"]["latest_progress_at"] == "2026-05-01T18:30:00+00:00"
    assert result["current_stage"] == "managed_runtime_recovering"
    assert result["supervision"]["health_status"] == "recovering"
    assert result["supervision"]["active_run_id"] is None


def test_study_progress_treats_live_worker_with_stale_artifact_delta_as_activity_timeout(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-dm",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    _write_publication_eval(
        study_root,
        quest_root,
        recommended_actions=[
            {
                "action_id": "action-201",
                "action_type": "bounded_analysis",
                "priority": "now",
                "reason": "Gate still reports claim-evidence repair and delivery refresh blockers.",
                "route_target": "analysis-campaign",
                "route_key_question": "Which claim-evidence object still needs repair?",
                "route_rationale": "Quality repair is still blocked.",
                "requires_controller_decision": True,
            }
        ],
    )
    _write_json(
        study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json",
        {
            "surface": "autonomy_progress_slo_status",
            "schema_version": 1,
            "study_id": "002-dm",
            "quest_id": "quest-002",
            "state": "breach",
            "breach_types": ["read_churn_without_artifact_delta"],
            "last_meaningful_progress_at": "2026-05-01T18:30:00+00:00",
            "mds_progress_markers": {
                "meaningful_artifact_delta_at": "2026-05-01T18:30:00+00:00",
                "meaningful_artifact_delta_kind": "paper_bundle",
            },
            "ai_doctor_request_required": True,
            "ai_doctor_state": "request_ready",
            "quality_gate_relaxation_allowed": False,
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "002-dm",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-002", "auto_resume": True},
            "quest_id": "quest-002",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "runtime_liveness_status": "live",
            "active_run_id": "run-live-stale",
            "worker_running": True,
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-live-stale",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "run-live-stale",
                    "worker_running": True,
                },
            },
            "autonomous_runtime_notice": {
                "required": True,
                "quest_status": "running",
                "active_run_id": "run-live-stale",
                "browser_url": "http://127.0.0.1:20999",
            },
            "execution_owner_guard": {
                "owner": "managed_runtime",
                "supervisor_only": True,
                "guard_reason": "live_managed_runtime",
                "active_run_id": "run-live-stale",
                "current_required_action": "supervise_managed_runtime",
                "publication_gate_allows_direct_write": False,
            },
            "continuation_state": {
                "quest_status": "running",
                "active_run_id": "run-live-stale",
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "controller_work_unit_pending",
            },
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "controller_stage_note": "current_package is stale and quality repair is still blocked.",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
                "latest_recorded_at": "2026-05-02T10:40:00+00:00",
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 5, 2, 10, 40, tzinfo=timezone.utc),
    )

    result = module.read_study_progress(profile=profile, study_id="002-dm")

    assert result["progress_freshness"]["status"] == "stale"
    assert result["progress_freshness"]["worker_liveness_freshness"]["status"] == "fresh"
    assert result["progress_freshness"]["activity_timeout"]["state"] == "timed_out"
    assert result["progress_freshness"]["activity_timeout"]["active_run_id"] == "run-live-stale"
    assert result["intervention_lane"]["lane_id"] == "progress_continuation_required"
    assert result["intervention_lane"]["severity"] == "critical"
    assert result["intervention_lane"].get("route_target") != "analysis-campaign"
    assert result["operator_status_card"]["handling_state"] == "progress_continuation_required"
    assert result["operator_status_card"]["human_surface_freshness"] == "monitoring_runtime"
    assert "supervisor ticks alone cannot prove paper progress" in result["operator_status_card"]["current_focus"]
    assert "domain_route/reconcile-apply" in result["operator_status_card"]["next_confirmation_signal"]


def test_study_progress_gives_new_live_run_grace_before_activity_timeout(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-dm",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    _write_publication_eval(study_root, quest_root)
    _write_json(
        study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json",
        {
            "surface": "autonomy_progress_slo_status",
            "schema_version": 1,
            "study_id": "002-dm",
            "quest_id": "quest-002",
            "state": "breach",
            "breach_types": ["same_fingerprint_loop"],
            "last_meaningful_progress_at": "2026-05-01T18:30:00+00:00",
            "mds_progress_markers": {
                "meaningful_artifact_delta_at": "2026-05-01T18:30:00+00:00",
                "meaningful_artifact_delta_kind": "paper_bundle",
            },
            "ai_doctor_request_required": True,
            "ai_doctor_state": "request_ready",
            "quality_gate_relaxation_allowed": False,
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "002-dm",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-002", "auto_resume": True},
            "quest_id": "quest-002",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "runtime_liveness_status": "live",
            "active_run_id": "run-new-live",
            "worker_running": True,
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-new-live",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "run-new-live",
                    "worker_running": True,
                },
            },
            "autonomous_runtime_notice": {
                "required": True,
                "quest_status": "running",
                "active_run_id": "run-new-live",
                "browser_url": "http://127.0.0.1:20999",
            },
            "execution_owner_guard": {
                "owner": "managed_runtime",
                "supervisor_only": True,
                "guard_reason": "live_managed_runtime",
                "active_run_id": "run-new-live",
                "current_required_action": "supervise_managed_runtime",
                "publication_gate_allows_direct_write": False,
            },
            "continuation_state": {
                "quest_status": "running",
                "active_run_id": "run-new-live",
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "controller_work_unit_pending",
            },
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
                "latest_recorded_at": "2026-05-02T10:40:00+00:00",
            },
            "runtime_health_snapshot": {
                "dominant_runtime_refs": [
                    {
                        "recorded_at": "2026-05-02T10:30:00+00:00",
                    }
                ],
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 5, 2, 10, 40, tzinfo=timezone.utc),
    )

    result = module.read_study_progress(profile=profile, study_id="002-dm")

    assert result["progress_freshness"]["worker_liveness_freshness"]["status"] == "fresh"
    assert result["progress_freshness"]["meaningful_artifact_delta_freshness"]["status"] == "stale"
    assert result["progress_freshness"]["activity_timeout"]["state"] == "watching_new_run"
    assert result["progress_freshness"]["activity_timeout"]["new_run_grace"]["active_run_id"] == "run-new-live"
    assert result["intervention_lane"]["lane_id"] != "runtime_recovery_required"
