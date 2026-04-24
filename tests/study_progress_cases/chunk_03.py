from __future__ import annotations

from . import shared as _shared
from . import chunk_01 as _chunk_01
from . import chunk_02 as _chunk_02

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_chunk_01)
_module_reexport(_chunk_02)

def test_study_progress_surfaces_bounded_analysis_quality_focus_without_human_gate(
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
    _write_publication_eval(
        study_root,
        quest_root,
        recommended_actions=[
            {
                "action_id": "action-201",
                "action_type": "bounded_analysis",
                "priority": "now",
                "reason": "先补一轮有限稳健性分析，再继续当前论文主线。",
                "route_target": "analysis-campaign",
                "route_key_question": "哪一轮最小稳健性分析足以支撑当前主张？",
                "route_rationale": "当前缺口是证据强度不足，先做 bounded analysis 最诚实。",
                "evidence_refs": [
                    str(
                        quest_root
                        / "artifacts"
                        / "reports"
                        / "escalation"
                        / "runtime_escalation_record.json"
                    )
                ],
                "requires_controller_decision": True,
            }
        ],
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"engine": "med-deepscientist", "quest_id": "quest-001", "auto_resume": True},
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "resume",
            "reason": "publishability_gate_blocked",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
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

    assert result["intervention_lane"]["lane_id"] == "quality_floor_blocker"
    assert result["intervention_lane"]["repair_mode"] == "bounded_analysis"
    assert result["intervention_lane"]["route_target"] == "analysis-campaign"
    assert "有限补充分析" in result["next_system_action"]
    assert "哪一轮最小稳健性分析足以支撑当前主张？" in result["next_system_action"]
    assert "补充分析与稳健性验证" in result["operator_status_card"]["current_focus"]
    assert result["needs_physician_decision"] is False


def test_study_progress_projects_finalize_metadata_wait_as_physician_decision(
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
    publication_eval_path = _write_publication_eval(study_root, quest_root)
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    _write_json(
        launch_report_path,
        {
            "recorded_at": "2026-04-10T09:05:00+00:00",
            "source": "controller",
            "decision": "resume",
            "reason": "quest_parked_on_unchanged_finalize_state",
            "quest_status": "active",
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
            "quest_status": "active",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "resume",
            "reason": "quest_parked_on_unchanged_finalize_state",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": [],
                "controller_stage_note": "paper bundle exists, but the active blockers still belong to the publishability surface; bundle suggestions stay downstream-only until the gate clears",
            },
            "pending_user_interaction": {
                "interaction_id": "progress-finalize-001",
                "kind": "progress",
                "waiting_interaction_id": "progress-finalize-001",
                "default_reply_interaction_id": "progress-finalize-001",
                "pending_decisions": ["progress-finalize-001"],
                "blocking": True,
                "reply_mode": "blocking",
                "expects_reply": True,
                "allow_free_text": True,
                "message": "当前只剩题名页与投稿声明的最终外部元数据需要确认。",
                "summary": "请确认最终作者顺序、单位映射与声明文案。",
                "reply_schema": {
                    "type": "object",
                    "properties": {
                        "choice": {"type": "string"},
                        "metadata": {"type": "object"},
                    },
                    "required": ["choice"],
                },
                "decision_type": None,
                "options_count": 3,
                "guidance_requires_user_decision": True,
                "source_artifact_path": str(
                    quest_root / ".ds" / "worktrees" / "paper-main" / "artifacts" / "progress" / "progress-finalize-001.json"
                ),
                "relay_required": True,
            },
            "interaction_arbitration": {
                "classification": "invalid_blocking",
                "action": "resume",
                "reason_code": "blocking_requires_structured_decision_request",
                "requires_user_input": False,
                "valid_blocking": False,
                "kind": "progress",
                "decision_type": None,
                "source_artifact_path": str(
                    quest_root / ".ds" / "worktrees" / "paper-main" / "artifacts" / "progress" / "progress-finalize-001.json"
                ),
                "controller_stage_note": (
                    "MAS-managed waiting_for_user is a controller-owned arbitration surface; "
                    "runtime blocking is rejected unless it is a valid structured decision request."
                ),
            },
            "continuation_state": {
                "quest_status": "active",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "unchanged_finalize_state",
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "MedAutoScience 外环监管心跳新鲜，当前仍在按合同持续监管。",
                "next_action_summary": "继续按周期 supervisor tick 监管当前托管运行。",
            },
            "runtime_supervision": {
                "health_status": "recovering",
                "summary": "系统正在自动启动或恢复托管运行。",
                "next_action_summary": "等待下一次巡检确认 worker 已重新上线并恢复 live。",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["current_stage"] == "waiting_physician_decision"
    assert result["needs_physician_decision"] is True
    assert result["physician_decision_summary"] == "请确认最终作者顺序、单位映射与声明文案。"
    assert "等待医生/PI 明确确认" in result["next_system_action"]
    assert any("作者顺序" in item for item in result["current_blockers"])
    assert result["refs"]["publication_eval_path"] == str(publication_eval_path)


def test_study_progress_projects_auditable_submission_metadata_wait_as_manual_finishing(
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
    write_submission_metadata_only_bundle(
        quest_root,
        blocking_item_ids=[
            "author_metadata",
            "ethics_statement",
            "human_subjects_consent_statement",
            "ai_declaration",
        ],
    )
    write_synced_submission_delivery(study_root, quest_root)
    publication_eval_path = _write_publication_eval(study_root, quest_root)

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
            "quest_status": "waiting_for_user",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "blocked",
            "reason": "quest_waiting_for_submission_metadata",
            "publication_supervisor_state": {
                "supervisor_phase": "bundle_stage_ready",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": False,
                "current_required_action": "continue_bundle_stage",
                "deferred_downstream_actions": [],
                "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
            },
            "pending_user_interaction": {
                "interaction_id": "progress-finalize-001",
                "kind": "progress",
                "waiting_interaction_id": "progress-finalize-001",
                "default_reply_interaction_id": "progress-finalize-001",
                "pending_decisions": ["progress-finalize-001"],
                "blocking": True,
                "reply_mode": "blocking",
                "expects_reply": True,
                "allow_free_text": True,
                "message": "当前只剩题名页与投稿声明的最终外部元数据需要确认。",
                "summary": "请确认最终作者顺序、单位映射与声明文案。",
                "reply_schema": {
                    "type": "object",
                    "properties": {
                        "choice": {"type": "string"},
                    },
                    "required": ["choice"],
                },
                "decision_type": None,
                "options_count": 2,
                "guidance_requires_user_decision": True,
                "source_artifact_path": str(
                    quest_root / ".ds" / "worktrees" / "paper-main" / "artifacts" / "progress" / "progress-finalize-001.json"
                ),
                "relay_required": True,
            },
            "interaction_arbitration": {
                "classification": "submission_metadata_only",
                "action": "block",
                "reason_code": "submission_metadata_only",
                "requires_user_input": True,
                "valid_blocking": True,
                "kind": None,
                "decision_type": None,
                "source_artifact_path": None,
                "controller_stage_note": "The auditable current package is already delivered.",
            },
            "continuation_state": {
                "quest_status": "waiting_for_user",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "paper_bundle_submitted",
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "MedAutoScience 外环监管心跳新鲜，当前仍在按合同持续监管。",
                "next_action_summary": "继续按周期 supervisor tick 监管当前托管运行。",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["current_stage"] == "manual_finishing"
    assert result["needs_physician_decision"] is False
    assert result["physician_decision_summary"] is None
    assert "系统已停车" in result["current_stage_summary"]
    assert "显式" in result["next_system_action"]
    assert not any("作者顺序" in item for item in result["current_blockers"])
    assert result["refs"]["publication_eval_path"] == str(publication_eval_path)


def test_study_progress_exposes_operator_status_card_for_runtime_recovery_in_progress(
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
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {
            "schema_version": 1,
            "recorded_at": "2026-04-12T10:00:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "health_status": "recovering",
            "summary": "Hermes 正在尝试恢复掉线的研究运行。",
            "next_action_summary": "等待 runtime supervision 的 health_status 回到 live，再确认研究继续推进。",
            "active_run_id": "run-001",
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
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "study_completion_contract": {},
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "controller_stage_note": "论文还在论文门控阶段，投稿包仍在后续件。",
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
                "summary": "MAS 外环监管心跳新鲜。",
                "latest_recorded_at": "2026-04-12T10:01:00+00:00",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["operator_status_card"]["surface_kind"] == "study_operator_status_card"
    assert result["operator_status_card"]["handling_state"] == "runtime_recovering"
    assert result["operator_status_card"]["latest_truth_source"] == "runtime_supervision"
    assert result["operator_status_card"]["user_visible_verdict"] == "MAS 正在处理 runtime recovery，当前 study 仍处在受管修复中。"
    assert "health_status 回到 live" in result["operator_status_card"]["next_confirmation_signal"]


def test_study_progress_exposes_operator_status_card_for_paper_surface_refresh_gap(
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
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-12T09:30:00+00:00",
            "verdict": {
                "overall_verdict": "blocked",
                "summary": "论文主线仍在可发表性门控下推进。",
            },
            "gaps": [
                {
                    "gap_id": "stale_study_delivery_mirror",
                    "gap_type": "delivery_surface",
                    "severity": "must_fix",
                    "summary": "study 目录里的投稿包镜像已经过期，仍停在旧版本，不能当作当前包。",
                }
            ],
        },
    )
    _write_runtime_watch(quest_root)
    _write_bash_summary(quest_root)

    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 4, 12, 10, 0, tzinfo=timezone.utc),
    )
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
            "study_completion_contract": {},
            "decision": "noop",
            "reason": "quest_already_running",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "controller_stage_note": "科学真相还在推进，给人看的投稿包需要同步刷新。",
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
                "summary": "MAS 外环监管心跳新鲜。",
                "latest_recorded_at": "2026-04-12T09:59:00+00:00",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")
    markdown = module.render_study_progress_markdown(result)

    assert result["operator_status_card"]["handling_state"] == "paper_surface_refresh_in_progress"
    assert result["operator_status_card"]["latest_truth_source"] == "publication_eval"
    assert result["operator_status_card"]["human_surface_freshness"] == "stale"
    assert result["operator_status_card"]["user_visible_verdict"] == "MAS 正在刷新给人看的投稿包镜像，科学真相已经先行一步。"
    assert "delivery_manifest" in result["operator_status_card"]["next_confirmation_signal"]
    assert "操作员状态卡" in markdown
    assert "投稿包镜像" in markdown


def test_study_progress_prefers_live_runtime_truth_over_recovering_health_hint(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-002"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "study_id": "002-risk",
            "quest_id": "quest-002",
            "emitted_at": "2026-04-12T10:16:00+00:00",
            "verdict": {
                "overall_verdict": "promising",
                "summary": "bundle-stage work is unlocked and can proceed on the critical path",
            },
            "gaps": [],
        },
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {
            "schema_version": 1,
            "recorded_at": "2026-04-12T10:16:47+00:00",
            "study_id": "002-risk",
            "quest_id": "quest-002",
            "health_status": "recovering",
            "summary": "系统正在自动启动或恢复托管运行。",
            "next_action_summary": "等待下一次巡检确认 worker 已重新上线并恢复 live。",
            "active_run_id": "run-live-002",
        },
    )
    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 4, 12, 10, 16, 48, tzinfo=timezone.utc),
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "002-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "quest_id": "quest-002",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "active",
            "study_completion_contract": {},
            "decision": "resume",
            "reason": "quest_stale_decision_after_write_stage_ready",
            "runtime_liveness_status": "live",
            "publication_supervisor_state": {
                "supervisor_phase": "bundle_stage_ready",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": False,
                "current_required_action": "continue_bundle_stage",
                "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
            },
            "autonomous_runtime_notice": {
                "required": True,
                "notice_key": "notice-live-002",
                "notification_reason": "detected_existing_live_managed_runtime",
                "quest_id": "quest-002",
                "quest_status": "running",
                "active_run_id": "run-live-002",
                "browser_url": "http://127.0.0.1:21999/quests/quest-002",
                "quest_session_api_url": "http://127.0.0.1:21999/api/quests/quest-002/session",
            },
            "execution_owner_guard": {
                "owner": "managed_runtime",
                "supervisor_only": True,
                "guard_reason": "live_managed_runtime",
                "active_run_id": "run-live-002",
                "current_required_action": "supervise_managed_runtime",
                "publication_gate_allows_direct_write": True,
            },
            "continuation_state": {
                "quest_status": "running",
                "active_run_id": "run-live-002",
                "continuation_policy": "auto",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "MAS 外环监管心跳新鲜。",
                "latest_recorded_at": "2026-04-12T10:16:47+00:00",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="002-risk")

    assert result["current_stage"] == "publication_supervision"
    assert result["current_stage_summary"] == "投稿打包阶段已被全局门控放行，可以进入关键路径。"
    assert result["next_system_action"] == "继续当前投稿打包阶段。"
    assert result["intervention_lane"]["lane_id"] == "monitor_only"
    assert result["operator_status_card"]["handling_state"] == "monitor_only"
    assert result["operator_status_card"]["user_visible_verdict"] == "MAS 正在持续监管当前 study。"


def test_study_progress_refreshes_publication_eval_from_newer_gate_report(
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
    _write_study_charter_and_controller_summary(study_root)
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-12T09:30:00+00:00",
            "evaluation_scope": "publication",
            "charter_context_ref": {
                "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                "charter_id": "charter::001-risk::v1",
                "publication_objective": "Objective text",
            },
            "runtime_context_refs": {
                "runtime_escalation_ref": str(
                    quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
                ),
                "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
            },
            "delivery_context_refs": {
                "paper_root_ref": str(quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"),
                "submission_minimal_ref": str(
                    quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "submission_minimal" / "submission_manifest.json"
                ),
            },
            "verdict": {
                "overall_verdict": "blocked",
                "primary_claim_status": "partial",
                "summary": "旧的外层结论还停在投稿包镜像过期。",
                "stop_loss_pressure": "watch",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "delivery",
                    "severity": "must_fix",
                    "summary": "stale_study_delivery_mirror",
                    "evidence_refs": [str(quest_root)],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "publication-eval-action::return_to_controller::2026-04-12T09:30:00+00:00",
                    "action_type": "return_to_controller",
                    "priority": "now",
                    "reason": "旧 blocker 仍未清掉。",
                    "evidence_refs": [str(quest_root)],
                    "requires_controller_decision": True,
                }
            ],
        },
    )
    _write_runtime_escalation(quest_root, study_root)
    _write_runtime_watch(quest_root)
    gate_report_path = _write_publishability_gate_report(quest_root)
    gate_report = json.loads(gate_report_path.read_text(encoding="utf-8"))
    gate_report.update(
        {
            "generated_at": "2026-04-12T09:40:00+00:00",
            "status": "blocked",
            "allow_write": False,
            "blockers": ["medical_publication_surface_blocked"],
            "study_delivery_status": "current",
            "study_delivery_stale_reason": None,
            "medical_publication_surface_status": "blocked",
            "medical_publication_surface_named_blockers": ["reviewer_first_concerns_unresolved"],
            "medical_publication_surface_route_back_recommendation": "return_to_write",
            "controller_stage_note": "稿件书写面还有医学论文表达硬阻塞，需要继续修文。",
        }
    )
    _write_json(gate_report_path, gate_report)
    _write_bash_summary(quest_root)

    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 4, 12, 10, 0, tzinfo=timezone.utc),
    )
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
            "study_completion_contract": {},
            "decision": "noop",
            "reason": "quest_already_running",
            "runtime_escalation_ref": {
                "record_id": "runtime-escalation::001-risk::quest-001::publishability_gate_blocked::2026-04-10T09:07:00+00:00",
                "artifact_path": str(
                    quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
                ),
                "summary_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            },
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "controller_stage_note": "稿件书写面还有医学论文表达硬阻塞，需要继续修文。",
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
                "summary": "MAS 外环监管心跳新鲜。",
                "latest_recorded_at": "2026-04-12T09:59:00+00:00",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")
    refreshed_publication_eval = json.loads(
        (study_root / "artifacts" / "publication_eval" / "latest.json").read_text(encoding="utf-8")
    )

    assert refreshed_publication_eval["emitted_at"] == "2026-04-12T09:40:00+00:00"
    assert refreshed_publication_eval["gaps"][0]["summary"] == "medical_publication_surface_blocked"
    assert refreshed_publication_eval["recommended_actions"][0]["action_type"] == "route_back_same_line"
    assert refreshed_publication_eval["recommended_actions"][0]["route_target"] == "write"
    assert "study 目录里的投稿包镜像已经过期，仍停在旧版本，不能当作当前包。" not in result["current_blockers"]
    assert "论文叙事或方法/结果书写面仍有硬阻塞。" in result["current_blockers"]
    assert result["operator_status_card"]["handling_state"] == "scientific_or_quality_repair_in_progress"
    assert result["operator_status_card"]["user_visible_verdict"] == "MAS 正在处理论文可发表性硬阻塞，给人看的稿件还没到放行状态。"
    assert result["module_surfaces"]["eval_hygiene"]["overall_verdict"] == "blocked"
    assert result["module_surfaces"]["eval_hygiene"]["status_summary"] == "稿件书写面还有医学论文表达硬阻塞，需要继续修文。"
    assert result["intervention_lane"]["repair_mode"] == "same_line_route_back"
    assert result["intervention_lane"]["route_target"] == "write"
    assert "What is the narrowest same-line manuscript repair or continuation step required now?" in result["next_system_action"]


def test_study_progress_refreshes_semantically_stale_publication_eval_even_when_eval_is_newer(
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
    _write_study_charter_and_controller_summary(study_root)
    publication_eval_path = _write_publication_eval(study_root, quest_root)
    stale_eval = json.loads(publication_eval_path.read_text(encoding="utf-8"))
    stale_eval.update(
        {
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-12T09:45:00+00:00",
            "emitted_at": "2026-04-12T09:45:00+00:00",
            "verdict": {
                "overall_verdict": "blocked",
                "primary_claim_status": "partial",
                "summary": "bundle suggestions are downstream-only until the publication gate allows write",
                "stop_loss_pressure": "watch",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "delivery",
                    "severity": "must_fix",
                    "summary": "stale_study_delivery_mirror",
                    "evidence_refs": [str(quest_root)],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "publication-eval-action::return_to_controller::2026-04-12T09:45:00+00:00",
                    "action_type": "return_to_controller",
                    "priority": "now",
                    "reason": "旧 blocker 仍未清掉。",
                    "evidence_refs": [str(quest_root)],
                    "requires_controller_decision": True,
                }
            ],
        }
    )
    _write_json(publication_eval_path, stale_eval)
    _write_runtime_escalation(quest_root, study_root)
    _write_runtime_watch(quest_root)
    gate_report_path = _write_publishability_gate_report(quest_root)
    gate_report = json.loads(gate_report_path.read_text(encoding="utf-8"))
    gate_report.update(
        {
            "generated_at": "2026-04-12T09:40:00+00:00",
            "status": "clear",
            "allow_write": True,
            "recommended_action": "continue_per_gate",
            "blockers": [],
            "study_delivery_status": "current",
            "study_delivery_stale_reason": None,
            "current_required_action": "continue_bundle_stage",
            "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
        }
    )
    _write_json(gate_report_path, gate_report)
    _write_bash_summary(quest_root)

    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 4, 12, 10, 0, tzinfo=timezone.utc),
    )
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
            "study_completion_contract": {},
            "decision": "noop",
            "reason": "quest_already_running",
            "runtime_escalation_ref": {
                "record_id": "runtime-escalation::001-risk::quest-001::publishability_gate_blocked::2026-04-10T09:07:00+00:00",
                "artifact_path": str(
                    quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
                ),
                "summary_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            },
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "controller_stage_note": "旧的 publication_eval 仍把纸面镜像错判成过期。",
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
                "summary": "MAS 外环监管心跳新鲜。",
                "latest_recorded_at": "2026-04-12T09:59:00+00:00",
            },
        },
    )

    module.read_study_progress(profile=profile, study_id="001-risk")
    refreshed_publication_eval = json.loads(publication_eval_path.read_text(encoding="utf-8"))

    assert refreshed_publication_eval["emitted_at"] == "2026-04-12T09:40:00+00:00"
    assert refreshed_publication_eval["verdict"]["overall_verdict"] == "promising"
    assert all(gap["severity"] == "optional" for gap in refreshed_publication_eval["gaps"])
    assert "stale_study_delivery_mirror" not in {
        gap["summary"] for gap in refreshed_publication_eval["gaps"]
    }
__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
