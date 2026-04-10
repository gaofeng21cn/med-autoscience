from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_publication_eval(study_root: Path, quest_root: Path) -> Path:
    payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::001-risk::quest-001::2026-04-10T09:09:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-04-10T09:09:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "risk stratification external validation",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(
                quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
            ),
            "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
        },
        "delivery_context_refs": {
            "paper_root_ref": str(study_root / "paper"),
            "submission_minimal_ref": str(
                study_root / "paper" / "submission_minimal" / "submission_manifest.json"
            ),
        },
        "verdict": {
            "overall_verdict": "blocked",
            "primary_claim_status": "partial",
            "summary": "论文主线仍缺少外部验证支持，暂时不能宣称主结论已经站稳。",
            "stop_loss_pressure": "watch",
        },
        "gaps": [
            {
                "gap_id": "gap-001",
                "gap_type": "evidence",
                "severity": "must_fix",
                "summary": "外部验证队列还没有补齐。",
                "evidence_refs": [str(quest_root / "artifacts" / "results" / "main_result.json")],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "action-001",
                "action_type": "return_to_controller",
                "priority": "now",
                "reason": "需要控制面决定是否继续投入外部验证。",
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
    }
    path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(path, payload)
    return path


def _write_controller_decision(study_root: Path, quest_root: Path) -> Path:
    payload = {
        "schema_version": 1,
        "decision_id": "study-decision::001-risk::quest-001::continue_same_line::2026-04-10T09:10:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-04-10T09:10:00+00:00",
        "decision_type": "continue_same_line",
        "charter_ref": {
            "charter_id": "charter::001-risk::v1",
            "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        },
        "runtime_escalation_ref": {
            "record_id": "runtime-escalation::001-risk::quest-001::publishability_gate_blocked::2026-04-10T09:07:00+00:00",
            "artifact_path": str(
                quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
            ),
            "summary_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
        },
        "publication_eval_ref": {
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-10T09:09:00+00:00",
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        },
        "requires_human_confirmation": True,
        "controller_actions": [
            {
                "action_type": "ensure_study_runtime",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        "reason": "外部验证是否继续投入需要医生/PI确认。",
    }
    path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    _write_json(path, payload)
    return path


def _write_runtime_escalation(quest_root: Path, study_root: Path) -> Path:
    payload = {
        "schema_version": 1,
        "record_id": "runtime-escalation::001-risk::quest-001::publishability_gate_blocked::2026-04-10T09:07:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-04-10T09:07:00+00:00",
        "trigger": {
            "trigger_id": "publishability_gate_blocked",
            "source": "publication_gate",
        },
        "scope": "quest",
        "severity": "quest",
        "reason": "publishability_gate_blocked",
        "recommended_actions": [
            "refresh_startup_hydration",
            "controller_review_required",
        ],
        "evidence_refs": [str(study_root / "artifacts" / "runtime" / "last_launch_report.json")],
        "runtime_context_refs": {
            "launch_report_path": str(study_root / "artifacts" / "runtime" / "last_launch_report.json")
        },
        "summary_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
        "artifact_path": str(
            quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
        ),
    }
    path = quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
    _write_json(path, payload)
    return path


def _write_runtime_watch(quest_root: Path) -> Path:
    payload = {
        "schema_version": 1,
        "scanned_at": "2026-04-10T09:08:00+00:00",
        "quest_root": str(quest_root),
        "quest_status": "running",
        "controllers": {
            "publication_gate": {
                "status": "blocked",
                "action": "suppressed",
                "blockers": ["missing_post_main_publishability_gate"],
                "advisories": [],
                "report_json": str(
                    quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"
                ),
                "report_markdown": str(
                    quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"
                ),
                "suppression_reason": "duplicate_fingerprint",
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": ["submission_minimal"],
                "controller_stage_note": "论文还没有通过可写门控，bundle 打包仍然属于后续步骤。",
            }
        },
    }
    path = quest_root / "artifacts" / "reports" / "runtime_watch" / "20260410T090800Z.json"
    _write_json(path, payload)
    return path


def _write_runtime_supervision(study_root: Path, quest_root: Path) -> Path:
    payload = {
        "schema_version": 1,
        "recorded_at": "2026-04-10T09:13:00+00:00",
        "study_id": "001-risk",
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "runtime_root": str(quest_root.parent),
        "health_status": "escalated",
        "runtime_decision": "blocked",
        "runtime_reason": "resume_request_failed",
        "quest_status": "running",
        "runtime_liveness_status": "none",
        "worker_running": False,
        "active_run_id": "run-001",
        "recovery_attempt_count": 2,
        "consecutive_failure_count": 2,
        "last_transition": "recovery_failed",
        "needs_human_intervention": True,
        "summary": "托管运行时已连续两次恢复失败，必须人工介入。",
        "clinician_update": "09:13 系统确认研究运行已经掉线，自动恢复连续失败，需要医生/PI看到明确告警。",
        "next_action": "manual_intervention_required",
        "next_action_summary": "请人工检查 MedDeepScientist 运行面，并决定是否暂停、重启或接管。",
        "refs": {
            "launch_report_path": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            "runtime_watch_report_path": str(quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json"),
        },
    }
    path = study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"
    _write_json(path, payload)
    return path


def _write_bash_summary(quest_root: Path) -> Path:
    payload = {
        "session_count": 1,
        "running_count": 1,
        "latest_session": {
            "bash_id": "bash-001",
            "status": "running",
            "updated_at": "2026-04-10T09:12:00+00:00",
            "last_progress": {
                "ts": "2026-04-10T09:12:00+00:00",
                "message": "完成外部验证数据清点，正在整理论文证据面。",
                "step": "external_validation_ready",
            },
        },
    }
    path = quest_root / ".ds" / "bash_exec" / "summary.json"
    _write_json(path, payload)
    return path


def _write_details_projection(quest_root: Path) -> Path:
    payload = {
        "schema_version": 1,
        "projection_id": "details.v1",
        "generated_at": "2026-04-10T09:11:00+00:00",
        "source_signature": "sig-001",
        "payload": {
            "summary": {
                "status_line": "外部验证数据已经准备好，当前在收紧论文结果与证据叙事。"
            },
            "paper_contract_health": {
                "recommended_next_stage": "write",
                "recommended_action": "polish_results_text",
            },
        },
    }
    path = quest_root / ".ds" / "projections" / "details.v1.json"
    _write_json(path, payload)
    return path


def test_study_progress_builds_physician_friendly_projection(monkeypatch, tmp_path: Path) -> None:
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

    publication_eval_path = _write_publication_eval(study_root, quest_root)
    controller_decision_path = _write_controller_decision(study_root, quest_root)
    runtime_escalation_path = _write_runtime_escalation(quest_root, study_root)
    runtime_watch_path = _write_runtime_watch(quest_root)
    bash_summary_path = _write_bash_summary(quest_root)
    details_projection_path = _write_details_projection(quest_root)
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

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["study_id"] == "001-risk"
    assert result["quest_id"] == "quest-001"
    assert result["current_stage"] == "waiting_physician_decision"
    assert result["paper_stage"] == "write"
    assert result["needs_physician_decision"] is True
    assert "医生" in result["current_stage_summary"]
    assert "写作" in result["paper_stage_summary"]
    assert any("外部验证" in item for item in result["current_blockers"])
    assert any("发表" in item for item in result["current_blockers"])
    assert "确认" in result["next_system_action"]
    assert result["supervision"]["browser_url"] == "http://127.0.0.1:21999/quests/quest-001"
    assert result["supervision"]["quest_session_api_url"] == "http://127.0.0.1:21999/api/sessions/run-001"
    assert result["supervision"]["active_run_id"] == "run-001"
    assert result["latest_events"][0]["category"] == "runtime_progress"
    assert result["latest_events"][0]["timestamp"] == "2026-04-10T09:12:00+00:00"
    assert "外部验证数据清点" in result["latest_events"][0]["summary"]
    assert result["refs"]["publication_eval_path"] == str(publication_eval_path)
    assert result["refs"]["controller_decision_path"] == str(controller_decision_path)
    assert result["refs"]["runtime_watch_report_path"] == str(runtime_watch_path)
    assert result["refs"]["bash_summary_path"] == str(bash_summary_path)
    assert result["refs"]["details_projection_path"] == str(details_projection_path)


def test_render_study_progress_markdown_uses_physician_friendly_sections(monkeypatch, tmp_path: Path) -> None:
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
    _write_controller_decision(study_root, quest_root)
    runtime_escalation_path = _write_runtime_escalation(quest_root, study_root)
    _write_runtime_watch(quest_root)
    _write_bash_summary(quest_root)
    _write_details_projection(quest_root)
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

    payload = module.read_study_progress(profile=profile, study_id="001-risk")
    markdown = module.render_study_progress_markdown(payload)

    assert "# 研究进度" in markdown
    assert "当前阶段" in markdown
    assert "论文推进" in markdown
    assert "最近进展" in markdown
    assert "监督入口" in markdown
    assert "外部验证数据清点" in markdown


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

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["current_stage"] == "managed_runtime_escalated"
    assert "人工介入" in result["current_stage_summary"]
    assert result["latest_events"][0]["category"] == "runtime_supervision"
    assert "连续两次恢复失败" in result["latest_events"][0]["summary"]
    assert any("人工介入" in item for item in result["current_blockers"])
    assert "人工检查" in result["next_system_action"]
    assert result["refs"]["runtime_supervision_path"] == str(runtime_supervision_path)


def test_study_progress_does_not_project_resume_arbitration_as_physician_decision(
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
    controller_decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    _write_json(
        controller_decision_path,
        {
            "schema_version": 1,
            "decision_id": "study-decision::001-risk::quest-001::continue_same_line::2026-04-10T09:10:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-10T09:10:00+00:00",
            "decision_type": "continue_same_line",
            "requires_human_confirmation": False,
            "controller_actions": [
                {
                    "action_type": "ensure_study_runtime",
                    "payload_ref": str(controller_decision_path),
                }
            ],
            "reason": "控制面要求继续 write/review，不需要医生追加确认。",
        },
    )
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
                "supervisor_phase": "scientific_anchor_missing",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": False,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": [],
                "controller_stage_note": "bundle suggestions are downstream-only until the publication gate allows write",
            },
            "pending_user_interaction": {
                "interaction_id": "progress-finalize-001",
                "kind": "decision_request",
                "waiting_interaction_id": "progress-finalize-001",
                "default_reply_interaction_id": "progress-finalize-001",
                "pending_decisions": ["progress-finalize-001"],
                "blocking": True,
                "reply_mode": "blocking",
                "expects_reply": True,
                "allow_free_text": False,
                "message": "这一步已经处理完，等待 Gateway 接管。",
                "summary": "运行时把 finalize 本地总结暂时停在这里。",
                "reply_schema": {"type": "decision", "decision_type": "finalize_paper_line"},
                "decision_type": "finalize_paper_line",
                "options_count": 1,
                "guidance_requires_user_decision": True,
                "source_artifact_path": str(quest_root / "artifacts" / "decisions" / "progress-finalize-001.json"),
                "relay_required": True,
            },
            "interaction_arbitration": {
                "classification": "invalid_blocking",
                "action": "resume",
                "reason_code": "mas_managed_policy_rejects_runtime_user_gate",
                "requires_user_input": False,
                "valid_blocking": False,
                "kind": "decision_request",
                "decision_type": "finalize_paper_line",
                "source_artifact_path": str(quest_root / "artifacts" / "decisions" / "progress-finalize-001.json"),
                "controller_stage_note": (
                    "MAS-managed studies must keep routing, finalize, adequacy, publishability, and completion "
                    "decisions inside the MAS outer loop; runtime blocking may only ask for external secrets or credentials."
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
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["study_id"] == "001-risk"
    assert result["current_stage"] == "publication_supervision"
    assert result["needs_physician_decision"] is False
    assert result["physician_decision_summary"] is None
    assert "等待医生/PI" not in result["next_system_action"]
    assert all("finalize 本地总结" not in item for item in result["current_blockers"])
    assert result["paper_stage"] == "scientific_anchor_missing"
    assert result["refs"]["publication_eval_path"] == str(publication_eval_path)


def test_study_progress_projects_supervisor_tick_gap_for_unsupervised_managed_runtime(
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
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
                "auto_resume": True,
            },
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "paused",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "resume",
            "reason": "quest_paused",
            "publication_supervisor_state": {
                "supervisor_phase": "scientific_anchor_missing",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": False,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": [],
                "controller_stage_note": "bundle suggestions are downstream-only until the publication gate allows write",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "stale",
                "reason": "supervisor_tick_report_stale",
                "summary": "MedAutoScience 外环监管心跳已陈旧，当前不能保证及时发现掉线并自动恢复。",
                "next_action_summary": "需要先恢复 MedAutoScience supervisor tick / heartbeat 调度，再继续托管监管与自动恢复。",
                "latest_report_path": str(study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"),
                "latest_recorded_at": "2026-04-10T09:00:00+00:00",
                "seconds_since_latest_recorded_at": 1800,
                "expected_interval_seconds": 300,
                "stale_after_seconds": 600,
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["current_stage"] == "managed_runtime_supervision_gap"
    assert "监管心跳已陈旧" in result["current_stage_summary"]
    assert any("监管心跳已陈旧" in item for item in result["current_blockers"])
    assert "supervisor tick" in result["next_system_action"]
    assert result["supervision"]["supervisor_tick_status"] == "stale"
