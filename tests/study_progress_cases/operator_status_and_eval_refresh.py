from __future__ import annotations

from . import shared as _shared
from . import runtime_projection_basics as _runtime_projection_basics
from . import autonomy_quality_and_route_projection as _autonomy_quality_and_route_projection
from . import publication_eval_currentness_projection as _publication_eval_currentness_projection

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_runtime_projection_basics)
_module_reexport(_autonomy_quality_and_route_projection)
_module_reexport(_publication_eval_currentness_projection)

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
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
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


def test_study_progress_does_not_treat_invalid_finalize_metadata_wait_as_user_decision(
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

    assert result["current_stage"] == "publication_supervision"
    assert result["auto_runtime_parked"]["parked"] is False
    assert result["needs_physician_decision"] is False
    assert result["needs_user_decision"] is False
    assert result["physician_decision_summary"] is None
    assert not any("作者顺序" in item for item in result["current_blockers"])
    assert result["refs"]["publication_eval_path"] == str(publication_eval_path)


def test_study_progress_projects_auditable_submission_metadata_wait_as_auto_runtime_parked(
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

    assert result["current_stage"] == "auto_runtime_parked"
    assert result["parked_state"] == "external_metadata_pending"
    assert result["legacy_current_stage"] == "manual_finishing"
    assert result["needs_physician_decision"] is False
    assert result["needs_user_decision"] is False
    assert result["physician_decision_summary"] is None
    assert "外部投稿元数据" in result["current_stage_summary"]
    assert "补齐外部投稿元数据" in result["next_system_action"]
    assert not any("作者顺序" in item for item in result["current_blockers"])
    assert result["refs"]["publication_eval_path"] == str(publication_eval_path)


def test_study_progress_domain_routeback_supersedes_auditable_metadata_parking(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(
        profile.workspace_root,
        study_id,
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / study_id
    write_submission_metadata_only_bundle(
        quest_root,
        blocking_item_ids=[
            "author_metadata",
            "ethics_statement",
        ],
    )
    write_synced_submission_delivery(study_root, quest_root)
    publication_eval_path = _write_publication_eval(study_root, quest_root)

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": study_id,
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": study_id,
                "auto_resume": True,
            },
            "quest_id": study_id,
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "failed",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "blocked",
            "reason": "quest_waiting_opl_runtime_owner_route",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": [],
                "controller_stage_note": (
                    "AI reviewer route-back requires harmonized validation uncertainty and grouped calibration."
                ),
            },
            "domain_transition": {
                "study_id": study_id,
                "decision_type": "route_back_same_line",
                "route_target": "analysis-campaign",
                "next_work_unit": {
                    "unit_id": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
                    "lane": "analysis-campaign",
                    "summary": (
                        "Add uncertainty intervals, grouped calibration evidence, and reproducibility "
                        "details to the unit-harmonized external validation."
                    ),
                },
                "controller_action": "ensure_study_runtime",
                "owner": "analysis-campaign",
                "typed_blocker": None,
            },
            "interaction_arbitration": {
                "classification": "domain_transition_runtime_redrive",
                "action": "resume",
                "reason_code": "quest_waiting_opl_runtime_owner_route",
                "requires_user_input": False,
                "valid_blocking": False,
                "kind": "domain_transition",
                "domain_transition_decision_type": "route_back_same_line",
                "domain_transition_route_target": "analysis-campaign",
                "domain_transition_controller_action": "ensure_study_runtime",
                "next_work_unit_id": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
            },
            "continuation_state": {
                "quest_status": "failed",
                "active_run_id": None,
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "runtime_platform_repair_redrive",
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

    result = module.read_study_progress(profile=profile, study_id=study_id)

    assert result["current_stage"] == "runtime_blocked"
    assert result["auto_runtime_parked"]["parked"] is False
    assert result["parked_state"] is None
    assert result["intervention_lane"]["lane_id"] != "auto_runtime_parked"
    assert result["interaction_arbitration"]["classification"] == "domain_transition_runtime_redrive"
    assert result["domain_transition"]["route_target"] == "analysis-campaign"
    assert result["domain_transition"]["next_work_unit"]["unit_id"] == (
        "unit_harmonized_validation_uncertainty_and_grouped_calibration"
    )
    assert "外部投稿元数据" not in result["current_stage_summary"]
    assert "补齐外部投稿元数据" not in result["next_system_action"]
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
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
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
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
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
    assert "freshness proof" in result["operator_status_card"]["human_surface_summary"]
    assert result["operator_status_card"]["user_visible_verdict"] == "MAS 正在刷新给人看的投稿包镜像，科学真相已经先行一步。"
    assert "current_package_freshness/latest.json" in result["operator_status_card"]["next_confirmation_signal"]
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
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
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
    assert result["active_run_id"] == "run-live-002"
    assert result["intervention_lane"]["lane_id"] == "monitor_only"
    assert result["operator_status_card"]["handling_state"] == "monitor_only"
    assert result["operator_status_card"]["user_visible_verdict"] == "MAS 正在持续监管当前 study。"

__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
