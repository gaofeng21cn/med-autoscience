from __future__ import annotations

from . import shared as _shared

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)

def test_latest_events_prefers_runtime_progress_over_newer_launch_report_summary(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    launch_report_path = tmp_path / "studies" / "001-risk" / "artifacts" / "runtime" / "last_launch_report.json"
    publication_eval_path = tmp_path / "studies" / "001-risk" / "artifacts" / "publication_eval" / "latest.json"
    controller_decision_path = tmp_path / "studies" / "001-risk" / "artifacts" / "controller_decisions" / "latest.json"
    bash_summary_path = (
        tmp_path
        / "ops"
        / "med-deepscientist"
        / "runtime"
        / "quests"
        / "quest-001"
        / ".ds"
        / "bash_exec"
        / "summary.json"
    )

    events = module._latest_events(
        launch_report_payload={
            "recorded_at": "2026-04-10T09:14:00+00:00",
            "decision": "noop",
            "reason": "quest_already_running",
        },
        launch_report_path=launch_report_path,
        runtime_supervision_payload=None,
        runtime_supervision_path=None,
        runtime_escalation_payload=None,
        runtime_escalation_path=None,
        publication_eval_payload=None,
        publication_eval_path=publication_eval_path,
        controller_decision_payload=None,
        controller_decision_path=controller_decision_path,
        runtime_watch_payload=None,
        runtime_watch_path=None,
        details_projection_payload=None,
        details_projection_path=None,
        bash_summary_payload={
            "latest_session": {
                "updated_at": "2026-04-10T09:12:00+00:00",
                "last_progress": {
                    "ts": "2026-04-10T09:12:00+00:00",
                    "message": "完成外部验证数据清点，正在整理论文证据面。",
                },
            }
        },
        bash_summary_path=bash_summary_path,
    )

    assert [item["category"] for item in events[:2]] == ["runtime_progress", "launch_report"]
    assert "完成外部验证数据清点" in events[0]["summary"]


def _write_runtime_efficiency_fixture(quest_root: Path) -> tuple[Path, Path]:
    telemetry_path = quest_root / ".ds" / "runs" / "run-001" / "telemetry.json"
    evidence_index_path = quest_root / ".ds" / "evidence_packets" / "run-001" / "index.json"
    evidence_sidecar_path = quest_root / ".ds" / "evidence_packets" / "run-001" / "bash_exec-large-log.json"
    gate_cache_path = quest_root / ".ds" / "gate_cache" / "paper_contract_health.json"
    _write_json(
        telemetry_path,
        {
            "run_id": "run-001",
            "prompt_bytes": 123456,
            "stdout_bytes": 2345,
            "tool_result_bytes_total": 98765,
            "compacted_tool_result_count": 4,
            "full_detail_tool_call_count": 1,
            "mcp_tool_call_count": 9,
            "model_inherited": True,
            "runner_profile": None,
            "token_usage": {
                "input_tokens": 1000,
                "cached_input_tokens": 400,
                "output_tokens": 120,
            },
        },
    )
    _write_json(
        evidence_index_path,
        {
            "items": [
                {
                    "tool_name": "bash_exec",
                    "detail": "compact",
                    "summary": "bash_exec: log_line_count=1200; key_blockers=1",
                    "payload_bytes": 64000,
                    "sidecar_path": str(evidence_sidecar_path),
                    "payload_sha256": "abc123",
                    "key_blockers": ["submission_minimal missing"],
                }
            ],
        },
    )
    _write_json(
        gate_cache_path,
        {
            "input_fingerprint": "gate-fingerprint-001",
            "generated_at": "2026-04-10T09:30:00+00:00",
        },
    )
    return telemetry_path, evidence_index_path


def test_study_progress_builds_physician_friendly_projection(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="研究主线是糖尿病死亡风险外部验证。",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation"],
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"

    _write_study_charter_and_controller_summary(study_root)
    publication_eval_path = _write_publication_eval(study_root, quest_root)
    controller_decision_path = _write_controller_decision(study_root, quest_root)
    runtime_escalation_path = _write_runtime_escalation(quest_root, study_root)
    publishability_gate_report_path = _write_publishability_gate_report(quest_root)
    runtime_watch_path = _write_runtime_watch(quest_root)
    bash_summary_path = _write_bash_summary(quest_root)
    details_projection_path = _write_details_projection(quest_root)
    telemetry_path, evidence_index_path = _write_runtime_efficiency_fixture(quest_root)
    task_intake_module.write_task_intake(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        entry_mode="full_research",
        task_intent="把当前研究收口到 SCI-ready 投稿标准，并持续自检卡住、无进度和质量回退。",
        journal_target="BMC Medicine",
        first_cycle_outputs=("study-progress", "runtime_watch", "publication_eval/latest.json"),
    )
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    _write_json(
        launch_report_path,
        {
            "recorded_at": "2026-04-10T09:05:00+00:00",
            "source": "controller",
            "decision": "noop",
            "reason": "quest_already_running",
            "quest_status": "running",
        },
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
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
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "noop",
            "reason": "quest_already_running",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": ["submission_minimal"],
                "controller_stage_note": "论文还没有通过可写门控，bundle 打包仍然属于后续步骤。",
            },
            "autonomous_runtime_notice": {
                "required": True,
                "notice_key": "notice-001",
                "notification_reason": "managed_runtime_live",
                "quest_id": "quest-001",
                "quest_status": "running",
                "active_run_id": "run-001",
                "browser_url": "http://127.0.0.1:21999/quests/quest-001",
                "quest_api_url": "http://127.0.0.1:21999/api/quests/quest-001",
                "quest_session_api_url": "http://127.0.0.1:21999/api/sessions/run-001",
                "monitoring_available": True,
                "monitoring_error": None,
                "launch_report_path": str(launch_report_path),
            },
            "execution_owner_guard": {
                "owner": "managed_runtime",
                "supervisor_only": True,
                "guard_reason": "runtime_live",
                "active_run_id": "run-001",
                "current_required_action": "supervise_runtime_only",
                "allowed_actions": ["read_status", "monitor_runtime"],
                "forbidden_actions": ["write_runtime_owned_roots"],
                "runtime_owned_roots": [str(quest_root / ".ds")],
                "takeover_required": False,
                "takeover_action": "pause_before_takeover",
                "publication_gate_allows_direct_write": False,
                "controller_stage_note": "当前只能做监管，不能直接越过托管运行时写入其拥有的表面。",
            },
            "runtime_escalation_ref": {
                "record_id": "runtime-escalation::001-risk::quest-001::publishability_gate_blocked::2026-04-10T09:07:00+00:00",
                "artifact_path": str(runtime_escalation_path),
                "summary_ref": str(launch_report_path),
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 4, 10, 10, 0, tzinfo=timezone.utc),
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["study_id"] == "001-risk"
    assert result["quest_id"] == "quest-001"
    assert result["current_stage"] == "waiting_physician_decision"
    assert result["paper_stage"] == "write"
    assert result["needs_physician_decision"] is True
    assert "医生" in result["current_stage_summary"]
    assert result["status_narration_contract"]["contract_kind"] == "ai_status_narration"
    assert (
        result["status_narration_contract"]["narration_policy"]["answer_checklist"]
        == ["current_stage", "current_blockers", "next_step"]
    )
    assert "写作" in result["paper_stage_summary"]
    assert any("外部验证" in item for item in result["current_blockers"])
    assert any("发表" in item for item in result["current_blockers"])
    assert "确认" in result["next_system_action"]
    assert result["supervision"]["browser_url"] == "http://127.0.0.1:21999/quests/quest-001"
    assert result["supervision"]["quest_session_api_url"] == "http://127.0.0.1:21999/api/sessions/run-001"
    assert result["supervision"]["active_run_id"] == "run-001"
    assert result["task_intake"]["journal_target"] == "BMC Medicine"
    assert "SCI-ready 投稿标准" in result["task_intake"]["task_intent"]
    assert result["progress_freshness"]["status"] == "not_required"
    assert result["latest_events"][0]["category"] == "runtime_progress"
    assert result["latest_events"][0]["timestamp"] == "2026-04-10T09:12:00+00:00"
    assert "外部验证数据清点" in result["latest_events"][0]["summary"]
    assert result["refs"]["publication_eval_path"] == str(publication_eval_path)
    assert result["refs"]["controller_decision_path"] == str(controller_decision_path)
    assert result["refs"]["controller_confirmation_summary_path"] == str(
        study_root / "artifacts" / "controller" / "controller_confirmation_summary.json"
    )
    assert result["refs"]["runtime_watch_report_path"] == str(runtime_watch_path)
    assert result["refs"]["controller_summary_path"] == str(
        study_root / "artifacts" / "controller" / "controller_summary.json"
    )
    assert result["refs"]["evaluation_summary_path"] == str(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    )
    assert result["refs"]["promotion_gate_path"] == str(
        study_root / "artifacts" / "eval_hygiene" / "promotion_gate" / "latest.json"
    )
    assert result["module_surfaces"]["controller_charter"]["summary_ref"] == result["refs"]["controller_summary_path"]
    assert result["module_surfaces"]["controller_charter"]["human_confirmation"] == {
        "gate_id": "controller-human-confirmation-001-risk",
        "status": "pending",
        "requested_at": "2026-04-10T09:10:00+00:00",
        "question_for_user": "请确认是否允许 MAS 停止当前研究运行。",
        "allowed_responses": ["approve", "request_changes", "reject"],
        "next_action_if_approved": "停止当前研究运行",
        "summary_ref": str(study_root / "artifacts" / "controller" / "controller_confirmation_summary.json"),
    }
    assert result["module_surfaces"]["runtime"]["summary_ref"] == result["refs"]["runtime_status_summary_path"]
    assert result["module_surfaces"]["eval_hygiene"]["summary_ref"] == result["refs"]["evaluation_summary_path"]
    assert result["refs"]["bash_summary_path"] == str(bash_summary_path)
    assert result["refs"]["details_projection_path"] == str(details_projection_path)
    assert result["refs"]["runtime_telemetry_path"] == str(telemetry_path)
    assert result["refs"]["evidence_packet_index_path"] == str(evidence_index_path)
    assert result["runtime_efficiency"]["run_id"] == "run-001"
    assert result["runtime_efficiency"]["prompt_bytes"] == 123456
    assert result["runtime_efficiency"]["tool_result_bytes_total"] == 98765
    assert result["runtime_efficiency"]["compacted_tool_result_count"] == 4
    assert result["runtime_efficiency"]["full_detail_tool_call_count"] == 1
    assert result["runtime_efficiency"]["token_usage"]["cached_input_tokens"] == 400
    assert result["runtime_efficiency"]["latest_evidence_packets"][0]["summary"].startswith("bash_exec:")
    assert result["runtime_efficiency"]["gate_cache"]["input_fingerprint"] == "gate-fingerprint-001"
    assert publishability_gate_report_path.exists()


def test_study_progress_skips_eval_hygiene_materialization_when_runtime_escalation_record_is_missing(
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
        paper_framing_summary="研究主线是糖尿病死亡风险外部验证。",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation"],
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    runtime_escalation_path = quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"

    _write_study_charter_and_controller_summary(study_root)
    publication_eval_path = _write_publication_eval(study_root, quest_root)
    publishability_gate_report_path = _write_publishability_gate_report(quest_root)
    runtime_watch_path = _write_runtime_watch(quest_root)

    _write_json(
        launch_report_path,
        {
            "recorded_at": "2026-04-10T09:05:00+00:00",
            "source": "controller",
            "decision": "noop",
            "reason": "quest_already_running",
            "quest_status": "running",
        },
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
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
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "noop",
            "reason": "quest_already_running",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": ["submission_minimal"],
                "controller_stage_note": "论文还没有通过可写门控，bundle 打包仍然属于后续步骤。",
            },
            "runtime_escalation_ref": {
                "record_id": "runtime-escalation::missing",
                "artifact_path": str(runtime_escalation_path),
                "summary_ref": str(launch_report_path),
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["study_id"] == "001-risk"
    assert result["refs"]["publication_eval_path"] == str(publication_eval_path)
    assert result["refs"]["runtime_watch_report_path"] == str(runtime_watch_path)
    assert result["refs"]["runtime_escalation_path"] == str(runtime_escalation_path)
    assert result["refs"]["evaluation_summary_path"] is None
    assert result["refs"]["promotion_gate_path"] is None
    assert "eval_hygiene" not in result["module_surfaces"]
    assert not runtime_escalation_path.exists()
    assert publishability_gate_report_path.exists()


def test_render_study_progress_markdown_uses_physician_friendly_sections(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    _write_study_charter_and_controller_summary(study_root)
    _write_publication_eval(study_root, quest_root)
    _write_controller_decision(
        study_root,
        quest_root,
        decision_type="continue_same_line",
        requires_human_confirmation=False,
        action_type="ensure_study_runtime",
        reason="MAS should keep repairing the current publication blockers autonomously.",
    )
    runtime_escalation_path = _write_runtime_escalation(quest_root, study_root)
    _write_publishability_gate_report(quest_root)
    _write_runtime_watch(quest_root)
    _write_bash_summary(quest_root)
    _write_details_projection(quest_root)
    _write_runtime_efficiency_fixture(quest_root)
    task_intake_module.write_task_intake(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        entry_mode="full_research",
        task_intent="优先保证系统能发现卡住、没进度和质量回退。",
        journal_target="JAMA Network Open",
    )
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    _write_json(
        launch_report_path,
        {
            "recorded_at": "2026-04-10T09:05:00+00:00",
            "source": "controller",
            "decision": "noop",
            "reason": "quest_already_running",
            "quest_status": "running",
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
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
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "noop",
            "reason": "quest_already_running",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": ["submission_minimal"],
                "controller_stage_note": "论文还没有通过可写门控，bundle 打包仍然属于后续步骤。",
            },
            "autonomous_runtime_notice": {
                "required": True,
                "notice_key": "notice-001",
                "notification_reason": "managed_runtime_live",
                "quest_id": "quest-001",
                "quest_status": "running",
                "active_run_id": "run-001",
                "browser_url": "http://127.0.0.1:21999/quests/quest-001",
                "quest_api_url": "http://127.0.0.1:21999/api/quests/quest-001",
                "quest_session_api_url": "http://127.0.0.1:21999/api/sessions/run-001",
                "monitoring_available": True,
                "monitoring_error": None,
                "launch_report_path": str(launch_report_path),
            },
            "execution_owner_guard": {
                "owner": "managed_runtime",
                "supervisor_only": True,
                "guard_reason": "runtime_live",
                "active_run_id": "run-001",
                "current_required_action": "supervise_runtime_only",
                "allowed_actions": ["read_status", "monitor_runtime"],
                "forbidden_actions": ["write_runtime_owned_roots"],
                "runtime_owned_roots": [str(quest_root / ".ds")],
                "takeover_required": False,
                "takeover_action": "pause_before_takeover",
                "publication_gate_allows_direct_write": False,
                "controller_stage_note": "当前只能做监管，不能直接越过托管运行时写入其拥有的表面。",
            },
            "runtime_escalation_ref": {
                "record_id": "runtime-escalation::001-risk::quest-001::publishability_gate_blocked::2026-04-10T09:07:00+00:00",
                "artifact_path": str(runtime_escalation_path),
                "summary_ref": str(launch_report_path),
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 4, 10, 10, 0, tzinfo=timezone.utc),
    )

    payload = module.read_study_progress(profile=profile, study_id="001-risk")
    markdown = module.render_study_progress_markdown(payload)

    assert "# 研究进度" in markdown
    assert "当前阶段" in markdown
    assert "干预类型" in markdown
    assert "当前任务" in markdown
    assert "论文推进" in markdown
    assert "最近进展" in markdown
    assert "监督入口" in markdown
    assert "JAMA Network Open" in markdown
    assert "研究进度信号" in markdown
    assert "上下文效率" in markdown
    assert "紧凑证据包" in markdown
    assert "Gate cache fingerprint" in markdown
    assert "主线模块" in markdown
    assert "controller_charter:" in markdown
    assert "eval_hygiene:" in markdown
    assert "runtime:" in markdown
    assert "外部验证数据清点" in markdown


def test_study_progress_projects_stale_progress_signal_for_active_runtime(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"

    _write_publication_eval(study_root, quest_root)
    _write_runtime_watch(quest_root)
    _write_bash_summary(quest_root)
    task_intake_module.write_task_intake(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        entry_mode="full_research",
        task_intent="持续推进论文主线，并在卡住时及时暴露给用户。",
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
                "auto_resume": True,
            },
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": [],
                "controller_stage_note": "论文还没有通过可写门控，bundle 打包仍然属于后续步骤。",
            },
            "autonomous_runtime_notice": {
                "required": True,
                "quest_id": "quest-001",
                "quest_status": "running",
                "active_run_id": "run-001",
                "browser_url": "http://127.0.0.1:21999/quests/quest-001",
                "quest_session_api_url": "http://127.0.0.1:21999/api/sessions/run-001",
            },
            "execution_owner_guard": {
                "owner": "managed_runtime",
                "supervisor_only": True,
                "active_run_id": "run-001",
                "current_required_action": "supervise_runtime_only",
                "publication_gate_allows_direct_write": False,
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "MedAutoScience 外环监管心跳新鲜，当前仍在按合同持续监管。",
                "latest_recorded_at": "2026-04-12T09:50:00+00:00",
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 4, 12, 10, 0, tzinfo=timezone.utc),
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["current_stage"] == "publication_supervision"
    assert result["progress_freshness"]["status"] == "stale"
    assert "超过 12 小时" in result["progress_freshness"]["summary"]
    assert any("超过 12 小时" in item for item in result["current_blockers"])


def test_study_progress_prioritizes_runtime_supervision_alerts_over_paper_stage_when_runtime_is_escalated(
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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    _write_publication_eval(study_root, quest_root)
    _write_runtime_watch(quest_root)
    runtime_supervision_path = _write_runtime_supervision(study_root, quest_root)
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    _write_json(
        launch_report_path,
        {
            "recorded_at": "2026-04-10T09:05:00+00:00",
            "source": "controller",
            "decision": "blocked",
            "reason": "resume_request_failed",
            "quest_status": "running",
        },
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
                "auto_resume": True,
            },
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "blocked",
            "reason": "resume_request_failed",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": ["submission_minimal"],
                "controller_stage_note": "论文还没有通过可写门控，bundle 打包仍然属于后续步骤。",
            },
            "execution_owner_guard": {
                "owner": "managed_runtime",
                "supervisor_only": True,
                "guard_reason": "managed_runtime_audit_unhealthy",
                "active_run_id": "run-001",
                "current_required_action": "inspect_runtime_health_and_decide_intervention",
                "allowed_actions": ["read_status", "monitor_runtime"],
                "forbidden_actions": ["write_runtime_owned_roots"],
                "runtime_owned_roots": [str(quest_root / ".ds")],
                "takeover_required": True,
                "takeover_action": "pause_before_takeover",
                "publication_gate_allows_direct_write": False,
                "controller_stage_note": "当前只能做监管，不能直接越过托管运行时写入其拥有的表面。",
            },
        },
    )

    profile_ref = tmp_path / "profile.local.toml"

    result = module.read_study_progress(profile=profile, study_id="001-risk", profile_ref=profile_ref)

    assert result["current_stage"] == "managed_runtime_escalated"
    assert "人工介入" in result["current_stage_summary"]
    assert result["intervention_lane"]["lane_id"] == "runtime_recovery_required"
    assert result["intervention_lane"]["recommended_action_id"] == "continue_or_relaunch"
    assert result["operator_verdict"] == {
        "surface_kind": "study_operator_verdict",
        "verdict_id": "study_operator_verdict::001-risk::runtime_recovery_required",
        "study_id": "001-risk",
        "lane_id": "runtime_recovery_required",
        "severity": "critical",
        "decision_mode": "intervene_now",
        "needs_intervention": True,
        "focus_scope": "study",
        "summary": "托管运行时已连续两次恢复失败，必须人工介入。",
        "reason_summary": "托管运行时已连续两次恢复失败，必须人工介入。",
        "primary_step_id": "continue_or_relaunch",
        "primary_surface_kind": "launch_study",
        "primary_command": (
            "uv run python -m med_autoscience.cli study launch --profile "
            + str(profile_ref.resolve())
            + " --study-id 001-risk"
        ),
    }
    assert result["recommended_command"].endswith(
        "study launch --profile " + str(profile_ref.resolve()) + " --study-id 001-risk"
    )
    assert result["recommended_commands"][0]["step_id"] == "continue_or_relaunch"
    assert result["recommended_commands"][0]["surface_kind"] == "launch_study"
    assert result["recovery_contract"] == {
        "contract_kind": "study_recovery_contract",
        "lane_id": "runtime_recovery_required",
        "action_mode": "continue_or_relaunch",
        "summary": "托管运行时已连续两次恢复失败，必须人工介入。",
        "recommended_step_id": "continue_or_relaunch",
        "steps": [
            {
                "step_id": "continue_or_relaunch",
                "title": "继续或重新拉起当前 study",
                "surface_kind": "launch_study",
                "command": (
                    "uv run python -m med_autoscience.cli study launch --profile "
                    + str(profile_ref.resolve())
                    + " --study-id 001-risk"
                ),
            },
            {
                "step_id": "inspect_runtime_status",
                "title": "读取结构化运行真相",
                "surface_kind": "study_runtime_status",
                "command": (
                    "uv run python -m med_autoscience.cli study-runtime-status --profile "
                    + str(profile_ref.resolve())
                    + " --study-id 001-risk"
                ),
            },
            {
                "step_id": "inspect_study_progress",
                "title": "读取当前研究进度",
                "surface_kind": "study_progress",
                "command": (
                    "uv run python -m med_autoscience.cli study progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id 001-risk"
                ),
            },
        ],
    }
    assert result["autonomy_contract"] == {
        "contract_kind": "study_autonomy_contract",
        "autonomy_state": "runtime_recovery",
        "summary": "托管运行时已连续两次恢复失败，必须人工介入。",
        "recommended_command": (
            "uv run python -m med_autoscience.cli study launch --profile "
            + str(profile_ref.resolve())
            + " --study-id 001-risk"
        ),
        "next_signal": "请回到 MAS 控制面确认当前托管运行策略，并决定是否暂停、重启或接管。",
        "restore_point": {
            "resume_mode": None,
            "continuation_policy": None,
            "continuation_reason": None,
            "human_gate_required": False,
            "summary": "当前还没有额外 checkpoint resume contract；可以直接回到 MAS 主线继续恢复或重启当前 study。",
        },
        "latest_outer_loop_dispatch": None,
    }
    projection = result["research_runtime_control_projection"]
    assert projection["surface_kind"] == "research_runtime_control_projection"
    assert projection["session_lineage_surface"]["field_path"] == "family_checkpoint_lineage"
    assert projection["restore_point_surface"]["field_path"] == "autonomy_contract.restore_point"
    assert projection["progress_surface"]["field_path"] == "operator_status_card.current_focus"
    assert projection["artifact_pickup_surface"]["field_path"] == "refs.evaluation_summary_path"
    assert str(study_root / "artifacts" / "publication_eval" / "latest.json") in projection["artifact_pickup_surface"]["pickup_refs"]
    assert str(study_root / "artifacts" / "controller_decisions" / "latest.json") in projection["artifact_pickup_surface"][
        "pickup_refs"
    ]
    assert projection["research_gate_surface"]["approval_gate_field"] == "needs_physician_decision"
    assert projection["research_gate_surface"]["approval_gate_required"] is False
    assert projection["research_gate_surface"]["interrupt_policy"] == "continue_or_relaunch"
    assert result["latest_events"][0]["category"] == "runtime_supervision"
    assert "连续两次恢复失败" in result["latest_events"][0]["summary"]
    assert any("人工介入" in item for item in result["current_blockers"])
    assert result["next_system_action"] == "请回到 MAS 控制面确认当前托管运行策略，并决定是否暂停、重启或接管。"
    assert "MedDeepScientist" not in result["next_system_action"]
    assert result["refs"]["runtime_supervision_path"] == str(runtime_supervision_path)
    markdown = module.render_study_progress_markdown(result)
    assert "恢复合同" in markdown
    assert "launch-study" in markdown
    assert "自治合同" in markdown
    assert "当前还没有额外 checkpoint resume contract" in markdown


def test_study_progress_autonomy_contract_projects_restore_point_from_checkpoint_lineage(
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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "resume",
            "reason": "quest_already_running",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "controller_stage_note": "当前同线质量修复仍在继续。",
            },
            "continuation_state": {
                "quest_status": "running",
                "active_run_id": "run-001",
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "unchanged_finalize_state",
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
            "family_checkpoint_lineage": {
                "version": "family-checkpoint-lineage.v1",
                "resume_contract": {
                    "resume_mode": "resume_from_checkpoint",
                    "human_gate_required": False,
                },
            },
            "pending_user_interaction": {},
            "interaction_arbitration": None,
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["autonomy_contract"]["autonomy_state"] == "autonomous_progress"
    assert result["autonomy_contract"]["latest_outer_loop_dispatch"] is None
    assert result["autonomy_contract"]["restore_point"] == {
        "resume_mode": "resume_from_checkpoint",
        "continuation_policy": "wait_for_user_or_resume",
        "continuation_reason": "运行停在未变化的定稿总结态",
        "human_gate_required": False,
        "summary": "当前恢复点采用 resume_from_checkpoint；continuation policy 为 wait_for_user_or_resume；最近一次续跑原因是运行停在未变化的定稿总结态。",
    }
    projection = result["research_runtime_control_projection"]
    assert projection["session_lineage_surface"]["lineage_version"] == "family-checkpoint-lineage.v1"
    assert projection["session_lineage_surface"]["continuation_anchor"] == "decision"
    assert projection["restore_point_surface"]["lineage_anchor_field"] == "family_checkpoint_lineage.resume_contract"
    assert projection["research_gate_surface"]["approval_gate_required"] is False
__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
