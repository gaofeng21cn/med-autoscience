from __future__ import annotations

from . import shared as _shared
from . import chunk_01 as _chunk_01
from . import chunk_02 as _chunk_02
from . import chunk_03 as _chunk_03
from . import chunk_04 as _chunk_04

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_chunk_01)
_module_reexport(_chunk_02)
_module_reexport(_chunk_03)
_module_reexport(_chunk_04)

def test_study_progress_suppresses_task_intake_route_inside_eval_surface_when_gate_blocked() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")

    payload = {
        "study_id": "001-risk",
        "quality_execution_lane": {
            "lane_id": "general_quality_repair",
            "route_target": "analysis-campaign",
        },
        "same_line_route_truth": {
            "surface_kind": "same_line_route_truth",
            "same_line_state": "bounded_analysis",
            "route_target": "analysis-campaign",
        },
        "same_line_route_surface": {
            "surface_kind": "same_line_route_surface",
            "route_target": "analysis-campaign",
        },
        "publication_supervisor_state": {
            "supervisor_phase": "publishability_gate_blocked",
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
        },
        "module_surfaces": {
            "eval_hygiene": {
                "quality_execution_lane": {
                    "lane_id": "general_quality_repair",
                    "route_target": "analysis-campaign",
                },
                "same_line_route_truth": {
                    "surface_kind": "same_line_route_truth",
                    "same_line_state": "bounded_analysis",
                    "route_target": "analysis-campaign",
                },
                "same_line_route_surface": {
                    "surface_kind": "same_line_route_surface",
                    "route_target": "analysis-campaign",
                },
            }
        },
    }

    result = module._normalize_study_progress_payload(payload)

    assert result["same_line_route_truth"] is None
    assert result["same_line_route_surface"] is None
    assert result["module_surfaces"]["eval_hygiene"]["same_line_route_truth"] is None
    assert result["module_surfaces"]["eval_hygiene"]["same_line_route_surface"] is None
    assert "## 同线路由真相" not in module.render_study_progress_markdown(result)


def test_render_study_progress_markdown_humanizes_decision_continuation_reason() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")

    markdown = module.render_study_progress_markdown(
        {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "current_stage": "runtime_blocked",
            "current_stage_summary": "当前 quest 已停止；如需继续，必须显式 rerun 或 relaunch。",
            "paper_stage": "publishability_gate_blocked",
            "paper_stage_summary": "论文当前建议推进到“论文可发表性门控未放行”阶段。",
            "runtime_decision": "blocked",
            "runtime_reason": "quest_stopped_requires_explicit_rerun",
            "current_blockers": ["quest_stopped_requires_explicit_rerun"],
            "next_system_action": "当前 quest 已停止；如需继续，必须显式 rerun 或 relaunch。",
            "latest_events": [],
            "continuation_state": {
                "continuation_reason": "decision:decision-4e192147",
            },
            "supervision": {
                "health_status": "unknown",
                "supervisor_tick_status": "fresh",
                "launch_report_path": "/tmp/studies/001-risk/artifacts/runtime/last_launch_report.json",
            },
        }
    )

    assert "decision:decision-4e192147" not in markdown
    assert "运行停在待处理的决策节点" in markdown


def test_render_study_progress_markdown_humanizes_latest_user_requirement_continuation_reason() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")

    markdown = module.render_study_progress_markdown(
        {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "current_stage": "publication_supervision",
            "current_stage_summary": "MAS 正在监督 live runtime 按最新任务推进。",
            "paper_stage": "publishability_gate_blocked",
            "paper_stage_summary": "论文仍在可发表性门控阶段。",
            "runtime_decision": "resume",
            "runtime_reason": "quest_already_running",
            "current_blockers": [],
            "next_system_action": "继续按最新用户要求推进。",
            "latest_events": [],
            "continuation_state": {
                "continuation_reason": "latest_user_requirement:msg-001",
            },
            "supervision": {
                "health_status": "live",
                "supervisor_tick_status": "fresh",
                "launch_report_path": "/tmp/studies/001-risk/artifacts/runtime/last_launch_report.json",
            },
        }
    )

    assert "latest_user_requirement:msg-001" not in markdown
    assert "最新用户要求已接管当前优先级" in markdown


def test_render_study_progress_markdown_hides_runtime_blocker_wording_for_manual_finishing() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")

    markdown = module.render_study_progress_markdown(
        {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "current_stage": "manual_finishing",
            "current_stage_summary": "当前 study 已转入人工打磨收尾；MAS 只需保持兼容性与监督入口，不再把它视为默认自动续跑对象。",
            "paper_stage": "publishability_gate_blocked",
            "paper_stage_summary": "论文当前建议推进到“论文可发表性门控未放行”阶段。",
            "runtime_decision": "blocked",
            "runtime_reason": "quest_stopped_requires_explicit_rerun",
            "current_blockers": ["medical_publication_surface_blocked"],
            "next_system_action": "继续保持兼容性与监督入口；如需重新自动续跑，再显式 rerun 或 relaunch。",
            "latest_events": [],
            "continuation_state": {
                "continuation_reason": "decision:decision-4e192147",
            },
            "manual_finish_contract": {
                "status": "active",
                "summary": "当前 study 已转入人工打磨收尾；MAS 只需保持兼容性与监督入口，不再把它视为默认自动续跑对象。",
                "next_action_summary": "继续保持兼容性与监督入口；如需重新自动续跑，再显式 rerun 或 relaunch。",
                "compatibility_guard_only": True,
            },
            "supervision": {
                "health_status": "none",
                "supervisor_tick_status": "fresh",
                "launch_report_path": "/tmp/studies/001-risk/artifacts/runtime/last_launch_report.json",
            },
        }
    )

    assert "MAS 决策: 兼容性监督中" in markdown
    assert "当前被阻断" not in markdown
    assert "当前 quest 已停止；如需继续，必须显式 rerun 或 relaunch。" not in markdown
    assert "decision:decision-4e192147" not in markdown


def test_render_study_progress_markdown_humanizes_internal_stage_tokens_and_blockers() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")

    markdown = module.render_study_progress_markdown(
        {
            "study_id": "004-invasive-architecture",
            "quest_id": "004-invasive-architecture-managed-20260408",
            "current_stage": "publication_supervision",
            "current_stage_summary": (
                "paper bundle exists, but the active blockers still belong to the publishability surface; "
                "bundle suggestions stay downstream-only until the gate clears"
            ),
            "paper_stage": "publishability_gate_blocked",
            "paper_stage_summary": (
                "论文当前建议推进到“publishability gate blocked”阶段。 paper bundle exists, but the active blockers "
                "still belong to the publishability surface; bundle suggestions stay downstream-only until the gate clears"
            ),
            "runtime_decision": "noop",
            "runtime_reason": "quest_already_running",
            "current_blockers": [
                "missing_submission_minimal",
                "medical_publication_surface_blocked",
                "forbidden_manuscript_terminology",
                "submission_checklist_contains_unclassified_blocking_items",
                "submission checklist contains unclassified blocking items",
                "claim evidence map missing or incomplete",
                "figure catalog missing or incomplete",
                "ama pdf defaults missing",
            ],
            "next_system_action": "先补齐论文证据与叙事，再回到发表门控复核。",
            "latest_events": [],
            "supervision": {
                "health_status": "live",
                "supervisor_tick_status": "fresh",
                "browser_url": "http://127.0.0.1:21001",
                "quest_session_api_url": "http://127.0.0.1:21001/api/session",
                "active_run_id": "run-001",
                "launch_report_path": "/tmp/studies/004-invasive-architecture/artifacts/runtime/last_launch_report.json",
            },
        }
    )

    assert "publication_supervision" not in markdown
    assert "publishability_gate_blocked" not in markdown
    assert "missing_submission_minimal" not in markdown
    assert "论文可发表性" in markdown
    assert "最小投稿包" in markdown
    assert "术语" in markdown
    assert "投稿检查清单里仍有未归类的硬阻塞。" in markdown
    assert markdown.count("投稿检查清单里仍有未归类的硬阻塞。") == 1
    assert "关键 claim-to-evidence 对照仍不完整。" in markdown
    assert "关键图表目录仍不完整。" in markdown
    assert "AMA 稿件导出默认配置仍未补齐。" in markdown


def test_render_study_progress_markdown_prefers_shared_human_status_narration() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    from opl_harness_shared.status_narration import build_status_narration_contract

    markdown = module.render_study_progress_markdown(
        {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "current_stage": "publication_supervision",
            "current_stage_summary": "旧版阶段摘要字段",
            "paper_stage": "bundle_stage_ready",
            "paper_stage_summary": "投稿打包阶段已放行。",
            "runtime_decision": "noop",
            "runtime_reason": "quest_already_running",
            "current_blockers": ["论文展示注册表与 reporting contract 不一致，需要先修正稿面契约。"],
            "next_system_action": "旧版 next_system_action 字段",
            "latest_events": [],
            "supervision": {
                "health_status": "live",
                "supervisor_tick_status": "fresh",
                "launch_report_path": "/tmp/studies/001-risk/artifacts/runtime/last_launch_report.json",
            },
            "status_narration_contract": build_status_narration_contract(
                contract_id="study-progress::001-risk",
                surface_kind="study_progress",
                stage={
                    "current_stage": "publication_supervision",
                    "recommended_next_stage": "bundle_stage_ready",
                },
                current_blockers=["论文展示注册表与 reporting contract 不一致，需要先修正稿面契约。"],
                latest_update="论文主体内容已经完成，当前进入投稿打包收口。",
                next_step="优先核对 submission package 与 studies 目录中的交付面是否一致。",
            ),
        }
    )

    assert "当前判断: 当前状态：论文可发表性监管；下一阶段：投稿打包就绪；当前卡点：论文展示注册表与 reporting contract 不一致，需要先修正稿面契约。" in markdown
    assert "下一步建议: 优先核对 submission package 与 studies 目录中的交付面是否一致。" in markdown
    assert "旧版阶段摘要字段" not in markdown
    assert "旧版 next_system_action 字段" not in markdown


def test_study_progress_surfaces_figure_loop_guard_blockers_from_runtime_watch(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    quest_root.mkdir(parents=True, exist_ok=True)

    _write_publication_eval(study_root, quest_root)
    _write_controller_decision(
        study_root,
        quest_root,
        decision_type="continue_same_line",
        requires_human_confirmation=False,
        action_type="ensure_study_runtime",
        reason="MAS should keep repairing the current publication blockers autonomously.",
    )
    _write_runtime_escalation(quest_root, study_root)
    _write_runtime_watch(quest_root)

    status_payload = {
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
        "decision": "resume",
        "reason": "quest_marked_running_but_no_live_session",
        "publication_supervisor_state": {
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
        },
        "supervisor_tick_audit": {
            "required": True,
            "status": "fresh",
            "summary": "监管心跳新鲜。",
        },
    }

    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **kwargs: status_payload)

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["intervention_lane"]["lane_id"] == "quality_floor_blocker"
    assert result["intervention_lane"]["recommended_action_id"] == "inspect_progress"
    assert "图表推进陷入重复打磨循环，当前 run 应被拉回主线。" in result["current_blockers"]
    assert "图表循环期间参考文献数量低于下限，当前稿件质量不达标。" in result["current_blockers"]


def test_study_progress_suppresses_conflicting_bundle_ready_runtime_events(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "004-invasive-architecture")
    quest_root = profile.runtime_root / "004-invasive-architecture-managed-20260408"
    quest_root.mkdir(parents=True, exist_ok=True)

    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "emitted_at": "2026-04-14T01:36:57+00:00",
            "verdict": {
                "summary": (
                    "paper bundle exists, but the active blockers still belong to the publishability surface; "
                    "bundle suggestions stay downstream-only until the gate clears"
                )
            },
            "gaps": [
                {
                    "summary": "submission_grade_active_figure_floor_unmet",
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {
            "schema_version": 1,
            "recorded_at": "2026-04-14T01:34:45+00:00",
            "health_status": "live",
            "summary": "托管运行时在线，研究仍在自动推进。",
        },
    )
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    _write_json(
        launch_report_path,
        {
            "recorded_at": "2026-04-14T01:34:45+00:00",
            "decision": "noop",
            "reason": "quest_already_running",
            "quest_status": "running",
            "publication_supervisor_state": {
                "supervisor_phase": "bundle_stage_ready",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": False,
                "current_required_action": "continue_bundle_stage",
                "deferred_downstream_actions": [],
                "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
            },
        },
    )
    runtime_watch_path = quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json"
    _write_json(
        runtime_watch_path,
        {
            "schema_version": 1,
            "scanned_at": "2026-04-14T01:34:45+00:00",
            "controllers": {
                "publication_gate": {
                    "status": "clear",
                    "blockers": [],
                    "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
                    "supervisor_phase": "bundle_stage_ready",
                    "phase_owner": "publication_gate",
                    "upstream_scientific_anchor_ready": True,
                    "bundle_tasks_downstream_only": False,
                    "current_required_action": "continue_bundle_stage",
                    "deferred_downstream_actions": [],
                },
                "medical_reporting_audit": {
                    "status": "blocked",
                    "blockers": ["registry_contract_mismatch"],
                },
            },
        },
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **kwargs: {
            "schema_version": 1,
            "study_id": "004-invasive-architecture",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "004-invasive-architecture-managed-20260408", "auto_resume": True},
            "quest_id": "004-invasive-architecture-managed-20260408",
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
                "deferred_downstream_actions": [],
                "controller_stage_note": (
                    "paper bundle exists, but the active blockers still belong to the publishability surface; "
                    "bundle suggestions stay downstream-only until the gate clears"
                ),
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "MedAutoScience 外环监管心跳新鲜，当前仍在按合同持续监管。",
            },
            "autonomous_runtime_notice": {
                "required": True,
                "notice_key": "notice-004",
                "notification_reason": "detected_existing_live_managed_runtime",
                "quest_id": "004-invasive-architecture-managed-20260408",
                "quest_status": "running",
                "active_run_id": "run-17ca96fb",
                "browser_url": "http://127.0.0.1:21001",
                "quest_api_url": "http://127.0.0.1:21001/api/quests/004-invasive-architecture-managed-20260408",
                "quest_session_api_url": "http://127.0.0.1:21001/api/quests/004-invasive-architecture-managed-20260408/session",
                "monitoring_available": True,
                "monitoring_error": None,
                "launch_report_path": str(launch_report_path),
            },
            "execution_owner_guard": {
                "owner": "managed_runtime",
                "supervisor_only": True,
                "guard_reason": "live_managed_runtime",
                "active_run_id": "run-17ca96fb",
                "current_required_action": "supervise_managed_runtime",
                "allowed_actions": ["read_runtime_status"],
                "forbidden_actions": ["direct_bundle_build"],
                "runtime_owned_roots": [str(quest_root)],
                "takeover_required": True,
                "takeover_action": "pause_runtime_then_explicit_human_takeover",
                "publication_gate_allows_direct_write": False,
                "controller_stage_note": "live managed runtime owns study-local execution",
            },
        },
    )
    result = module.read_study_progress(profile=profile, study_id="004-invasive-architecture")

    assert result["latest_events"][0]["category"] == "publication_eval"
    assert result["latest_events"][0]["summary"] == (
        "论文包雏形已经存在，但当前硬阻塞仍在论文可发表性面；在门控放行前，投稿包相关建议都只是后续件。"
    )
    assert all(item["category"] != "runtime_watch" for item in result["latest_events"])
    assert all(item["category"] != "launch_report" for item in result["latest_events"])
    assert "活跃主稿图数量仍低于投稿级下限，当前图证不足以支撑投稿级稿件。" in result["current_blockers"]
    assert "论文展示注册表与 reporting contract 不一致，需要先修正稿面契约。" in result["current_blockers"]


def test_study_progress_does_not_treat_optional_publication_eval_gap_as_quality_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "004-invasive-architecture")
    quest_root = profile.runtime_root / "004-invasive-architecture-managed-20260408"
    quest_root.mkdir(parents=True, exist_ok=True)

    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "emitted_at": "2026-04-16T16:01:15+00:00",
            "verdict": {
                "summary": "bundle-stage work is unlocked and can proceed on the critical path",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "severity": "optional",
                    "summary": "bundle-stage work is unlocked and can proceed on the critical path",
                }
            ],
        },
    )
    _write_json(
        quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json",
        {
            "schema_version": 1,
            "scanned_at": "2026-04-16T16:01:16+00:00",
            "controllers": {
                "publication_gate": {
                    "status": "clear",
                    "blockers": [],
                    "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
                    "supervisor_phase": "bundle_stage_ready",
                    "phase_owner": "publication_gate",
                    "upstream_scientific_anchor_ready": True,
                    "bundle_tasks_downstream_only": False,
                    "current_required_action": "continue_bundle_stage",
                    "deferred_downstream_actions": [],
                }
            },
        },
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **kwargs: {
            "schema_version": 1,
            "study_id": "004-invasive-architecture",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "004-invasive-architecture-managed-20260408", "auto_resume": True},
            "quest_id": "004-invasive-architecture-managed-20260408",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "noop",
            "reason": "quest_already_running",
            "publication_supervisor_state": {
                "supervisor_phase": "bundle_stage_ready",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": False,
                "current_required_action": "continue_bundle_stage",
                "deferred_downstream_actions": [],
                "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "MedAutoScience 外环监管心跳新鲜，当前仍在按合同持续监管。",
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 4, 16, 16, 5, tzinfo=timezone.utc),
    )

    result = module.read_study_progress(profile=profile, study_id="004-invasive-architecture")

    assert result["progress_freshness"]["status"] == "fresh"
    assert result["intervention_lane"]["lane_id"] == "monitor_only"
    assert result["operator_verdict"]["surface_kind"] == "study_operator_verdict"
    assert result["operator_verdict"]["verdict_id"] == "study_operator_verdict::004-invasive-architecture::monitor_only"
    assert result["operator_verdict"]["study_id"] == "004-invasive-architecture"
    assert result["operator_verdict"]["lane_id"] == "monitor_only"
    assert result["operator_verdict"]["severity"] == "observe"
    assert result["operator_verdict"]["decision_mode"] == "monitor_only"
    assert result["operator_verdict"]["needs_intervention"] is False
    assert result["operator_verdict"]["focus_scope"] == "study"
    assert "投稿打包阶段" in result["operator_verdict"]["summary"]
    assert result["operator_verdict"]["reason_summary"] == result["operator_verdict"]["summary"]
    assert result["operator_verdict"]["primary_step_id"] == "inspect_study_progress"
    assert result["operator_verdict"]["primary_surface_kind"] == "study_progress"
    assert (
        result["operator_verdict"]["primary_command"]
        == "uv run python -m med_autoscience.cli study progress --profile <profile> --study-id 004-invasive-architecture"
    )
    assert result["current_blockers"] == []
    assert result["next_system_action"] == "继续当前投稿打包阶段。"


def test_study_progress_does_not_surface_reporting_checklist_gap_as_hard_blocker_after_write_unlock(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "004-invasive-architecture")
    quest_root = profile.runtime_root / "004-invasive-architecture-managed-20260408"
    quest_root.mkdir(parents=True, exist_ok=True)

    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "emitted_at": "2026-04-16T16:01:15+00:00",
            "verdict": {
                "summary": "the publication gate allows write; writing-stage work is now on the critical path",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "reporting",
                    "severity": "optional",
                    "summary": "the publication gate allows write; writing-stage work is now on the critical path",
                }
            ],
        },
    )
    _write_json(
        quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json",
        {
            "schema_version": 1,
            "scanned_at": "2026-04-16T16:01:16+00:00",
            "controllers": {
                "publication_gate": {
                    "status": "clear",
                    "blockers": [],
                    "controller_stage_note": "the publication gate allows write; writing-stage work is now on the critical path",
                    "supervisor_phase": "write_stage_ready",
                    "phase_owner": "publication_gate",
                    "upstream_scientific_anchor_ready": True,
                    "bundle_tasks_downstream_only": False,
                    "current_required_action": "continue_write_stage",
                    "deferred_downstream_actions": [],
                },
                "medical_reporting_audit": {
                    "status": "advisory",
                    "blockers": [],
                    "advisories": ["missing_reporting_guideline_checklist"],
                },
            },
        },
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **kwargs: {
            "schema_version": 1,
            "study_id": "004-invasive-architecture",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "004-invasive-architecture-managed-20260408", "auto_resume": True},
            "quest_id": "004-invasive-architecture-managed-20260408",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "noop",
            "reason": "quest_already_running",
            "publication_supervisor_state": {
                "supervisor_phase": "write_stage_ready",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": False,
                "current_required_action": "continue_write_stage",
                "deferred_downstream_actions": [],
                "controller_stage_note": "the publication gate allows write; writing-stage work is now on the critical path",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "MedAutoScience 外环监管心跳新鲜，当前仍在按合同持续监管。",
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 4, 16, 16, 5, tzinfo=timezone.utc),
    )

    result = module.read_study_progress(profile=profile, study_id="004-invasive-architecture")

    assert "报告规范核对表仍未补齐。" not in result["current_blockers"]
    assert result["intervention_lane"]["lane_id"] == "monitor_only"
    assert result["operator_status_card"]["handling_state"] == "monitor_only"
    assert result["operator_status_card"]["user_visible_verdict"] == "MAS 正在持续监管当前 study。"
def test_study_progress_blockers_override_bundle_stage_next_action(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "004-invasive-architecture")
    quest_root = profile.runtime_root / "004-invasive-architecture-managed-20260408"
    quest_root.mkdir(parents=True, exist_ok=True)

    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "emitted_at": "2026-04-16T16:01:15+00:00",
            "verdict": {
                "summary": "bundle-stage work is unlocked and can proceed on the critical path",
            },
            "gaps": [],
        },
    )
    _write_json(
        quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json",
        {
            "schema_version": 1,
            "scanned_at": "2026-04-16T16:01:16+00:00",
            "controllers": {
                "publication_gate": {
                    "status": "clear",
                    "blockers": [],
                    "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
                    "supervisor_phase": "bundle_stage_ready",
                    "phase_owner": "publication_gate",
                    "upstream_scientific_anchor_ready": True,
                    "bundle_tasks_downstream_only": False,
                    "current_required_action": "continue_bundle_stage",
                    "deferred_downstream_actions": [],
                },
                "medical_reporting_audit": {
                    "status": "blocked",
                    "blockers": ["registry_contract_mismatch"],
                },
            },
        },
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **kwargs: {
            "schema_version": 1,
            "study_id": "004-invasive-architecture",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "004-invasive-architecture-managed-20260408", "auto_resume": True},
            "quest_id": "004-invasive-architecture-managed-20260408",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "noop",
            "reason": "quest_already_running",
            "publication_supervisor_state": {
                "supervisor_phase": "bundle_stage_ready",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": False,
                "current_required_action": "continue_bundle_stage",
                "deferred_downstream_actions": [],
                "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "MedAutoScience 外环监管心跳新鲜，当前仍在按合同持续监管。",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="004-invasive-architecture")

    assert result["intervention_lane"]["lane_id"] == "quality_floor_blocker"
    assert "论文展示注册表与 reporting contract 不一致，需要先修正稿面契约。" in result["current_blockers"]
    assert result["next_system_action"] == "先修正当前质量阻塞，再决定是否继续投稿打包。"


def test_quality_review_followthrough_projects_auto_re_review_pending_when_runtime_recovery_requested() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")

    payload = module._quality_review_followthrough_projection(
        quality_review_loop={
            "current_phase": "re_review_required",
            "re_review_ready": True,
        },
        needs_physician_decision=False,
        interaction_arbitration={},
        runtime_decision="relaunch_stopped",
        quest_status="stopped",
        current_blockers=[],
        next_system_action="继续观察下一轮复评是否启动。",
    )

    assert payload == {
        "surface_kind": "quality_review_followthrough",
        "state": "auto_re_review_pending",
        "state_label": "等待系统自动复评",
        "waiting_auto_re_review": True,
        "auto_continue_expected": True,
        "summary": "当前在等系统自动发起下一轮复评，主线会自动继续。",
        "blocking_reason": None,
        "next_confirmation_signal": "看 publication_eval/latest.json 是否出现新的复评结论，或 blocking issues 是否继续收窄。",
        "user_intervention_required_now": False,
    }


def test_render_study_progress_markdown_surfaces_quality_review_followthrough() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")

    markdown = module.render_study_progress_markdown(
        {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "current_stage": "publishability_blocked",
            "current_stage_summary": "当前修订计划已完成，下一步应由 MAS 发起 re-review。",
            "paper_stage": "write",
            "paper_stage_summary": "当前主要是等待复评回写。",
            "latest_events": [],
            "current_blockers": [],
            "next_system_action": "等待系统自动复评。",
            "runtime_decision": "relaunch_stopped",
            "runtime_reason": "quest_stopped_requires_explicit_rerun",
            "progress_freshness": {},
            "supervision": {},
            "intervention_lane": {},
            "operator_status_card": {
                "handling_state_label": "持续监督中",
                "user_visible_verdict": "当前在等系统自动复评；你现在不用介入，先等待复评回写。",
                "current_focus": "当前在等系统自动发起下一轮复评，主线会自动继续。",
                "next_confirmation_signal": "看 publication_eval/latest.json 是否出现新的复评结论，或 blocking issues 是否继续收窄。",
            },
            "quality_review_followthrough": {
                "state_label": "等待系统自动复评",
                "waiting_auto_re_review": True,
                "auto_continue_expected": True,
                "summary": "当前在等系统自动发起下一轮复评，主线会自动继续。",
                "blocking_reason": None,
                "next_confirmation_signal": "看 publication_eval/latest.json 是否出现新的复评结论，或 blocking issues 是否继续收窄。",
            },
            "quality_review_loop": {
                "current_phase_label": "等待复评",
                "recommended_next_phase_label": "发起复评",
                "summary": "当前修订计划已完成，下一步应由 MAS 发起 re-review，重新判断 blocking issues 是否真正闭环。",
                "recommended_next_action": "发起下一轮 MAS quality re-review，确认当前 blocking issues 是否已真正闭环。",
                "blocking_issue_count": 1,
                "blocking_issues": ["当前 blocking issues 是否已真正闭环"],
                "next_review_focus": ["当前 blocking issues 是否已真正闭环"],
            },
            "module_surfaces": {},
        }
    )

    assert "当前判断: 当前在等系统自动发起下一轮复评，主线会自动继续。" in markdown
    assert "## 自动复评后续" in markdown
    assert "当前状态: 等待系统自动复评" in markdown
    assert "系统自动继续: 会" in markdown
    assert "后续摘要: 当前在等系统自动发起下一轮复评，主线会自动继续。" in markdown
    assert "下一确认信号: 看 publication_eval/latest.json 是否出现新的复评结论，或 blocking issues 是否继续收窄。" in markdown


def test_study_progress_projects_gate_clearing_batch_followthrough(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T05:58:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-05T05:58:00+00:00",
            "verdict": {
                "overall_verdict": "blocked",
                "primary_claim_status": "partial",
                "summary": "当前还存在 publication gate blocker。",
                "stop_loss_pressure": "watch",
            },
            "gaps": [],
            "recommended_actions": [],
        },
    )
    gate_batch_path = study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
    _write_json(
        gate_batch_path,
        {
            "schema_version": 1,
            "source_eval_id": "publication-eval::001-risk::quest-001::2026-04-05T05:58:00+00:00",
            "status": "executed",
            "unit_results": [
                {"unit_id": "freeze_scientific_anchor_fields", "status": "updated"},
                {"unit_id": "materialize_display_surface", "status": "updated"},
            ],
            "gate_replay": {
                "status": "blocked",
                "blockers": ["claim_evidence_consistency_failed", "registry_contract_mismatch"],
            },
        },
    )

    result = module._gate_clearing_batch_followthrough(
        study_root=study_root,
        publication_eval_payload=json.loads(publication_eval_path.read_text(encoding="utf-8")),
    )

    assert result == {
        "surface_kind": "gate_clearing_batch_followthrough",
        "status": "executed",
        "summary": "最近一轮 gate-clearing batch 已执行；当前仍剩 2 个 gate blocker。",
        "gate_replay_status": "blocked",
        "blocking_issue_count": 2,
        "failed_unit_count": 0,
        "next_confirmation_signal": "看 publication_eval/latest.json 或最新 gate replay 是否继续收窄 blocker。",
        "user_intervention_required_now": False,
        "latest_record_path": str(gate_batch_path),
    }


def test_study_progress_projects_quality_repair_batch_followthrough(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T05:58:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-05T05:58:00+00:00",
            "verdict": {
                "overall_verdict": "blocked",
                "primary_claim_status": "partial",
                "summary": "当前仍需 deterministic quality repair。",
                "stop_loss_pressure": "watch",
            },
            "gaps": [],
            "recommended_actions": [],
        },
    )
    quality_batch_path = study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"
    _write_json(
        quality_batch_path,
        {
            "schema_version": 1,
            "source_eval_id": "publication-eval::001-risk::quest-001::2026-04-05T05:58:00+00:00",
            "source_summary_id": "evaluation-summary::001-risk::latest",
            "status": "executed",
            "quality_closure_state": "quality_repair_required",
            "quality_execution_lane_id": "general_quality_repair",
            "gate_clearing_batch": {
                "status": "executed",
                "unit_results": [
                    {"unit_id": "materialize_display_surface", "status": "updated"},
                ],
                "gate_replay": {
                    "status": "blocked",
                    "blockers": ["medical_publication_surface_blocked"],
                },
            },
        },
    )

    result = module._quality_repair_batch_followthrough(
        study_root=study_root,
        publication_eval_payload=json.loads(publication_eval_path.read_text(encoding="utf-8")),
        recommended_command="uv run python -m med_autoscience.cli study quality-repair-batch --profile profile.local.toml --study-id 001-risk",
    )

    assert result == {
        "surface_kind": "quality_repair_batch_followthrough",
        "status": "executed",
        "quality_closure_state": "quality_repair_required",
        "quality_execution_lane_id": "general_quality_repair",
        "summary": "最近一轮 quality-repair batch 已执行；当前 gate replay 仍剩 1 个 blocker。",
        "gate_replay_status": "blocked",
        "blocking_issue_count": 1,
        "failed_unit_count": 0,
        "next_confirmation_signal": "看 publication_eval/latest.json 或最新 quality gate replay 是否继续收窄 blocker。",
        "user_intervention_required_now": False,
        "recommended_step_id": "run_quality_repair_batch",
        "recommended_command": "uv run python -m med_autoscience.cli study quality-repair-batch --profile profile.local.toml --study-id 001-risk",
        "latest_record_path": str(quality_batch_path),
    }


def test_render_study_progress_markdown_surfaces_gate_clearing_batch_followthrough() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")

    markdown = module.render_study_progress_markdown(
        {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "current_stage": "publication_supervision",
            "current_stage_summary": "当前仍在门控收口。",
            "paper_stage": "finalize",
            "paper_stage_summary": "当前只剩投稿打包收尾。",
            "latest_events": [],
            "current_blockers": [],
            "next_system_action": "等待下一轮门控回放。",
            "runtime_decision": "blocked",
            "runtime_reason": "quest_waiting_for_submission_metadata",
            "progress_freshness": {},
            "supervision": {},
            "intervention_lane": {},
            "operator_status_card": {},
            "gate_clearing_batch_followthrough": {
                "status": "executed",
                "summary": "最近一轮 gate-clearing batch 已执行；当前仍剩 2 个 gate blocker。",
                "failed_unit_count": 0,
                "blocking_issue_count": 2,
                "next_confirmation_signal": "看 publication_eval/latest.json 或最新 gate replay 是否继续收窄 blocker。",
            },
            "module_surfaces": {},
        }
    )

    assert "## Gate-Clearing Batch" in markdown
    assert "当前判断: 最近一轮 gate-clearing batch 已执行；当前仍剩 2 个 gate blocker。" in markdown
    assert "剩余 gate blocker: 2" in markdown


def test_render_study_progress_markdown_surfaces_quality_repair_batch_followthrough() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")

    markdown = module.render_study_progress_markdown(
        {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "current_stage": "publication_supervision",
            "current_stage_summary": "当前仍在质量修复收口。",
            "paper_stage": "finalize",
            "paper_stage_summary": "当前仍需 deterministic quality repair。",
            "latest_events": [],
            "current_blockers": [],
            "next_system_action": "等待下一轮质量门控回放。",
            "runtime_decision": "blocked",
            "runtime_reason": "publication_quality_gap",
            "progress_freshness": {},
            "supervision": {},
            "intervention_lane": {},
            "operator_status_card": {},
            "quality_repair_batch_followthrough": {
                "status": "executed",
                "summary": "最近一轮 quality-repair batch 已执行；当前 gate replay 仍剩 1 个 blocker。",
                "failed_unit_count": 0,
                "blocking_issue_count": 1,
                "next_confirmation_signal": "看 publication_eval/latest.json 或最新 quality gate replay 是否继续收窄 blocker。",
            },
            "module_surfaces": {},
        }
    )

    assert "## Quality-Repair Batch" in markdown
    assert "当前判断: 最近一轮 quality-repair batch 已执行；当前 gate replay 仍剩 1 个 blocker。" in markdown
    assert "剩余 gate blocker: 1" in markdown
    assert "下一确认信号: 看 publication_eval/latest.json 或最新 quality gate replay 是否继续收窄 blocker。" in markdown
__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
