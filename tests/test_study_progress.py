from __future__ import annotations

import builtins
from datetime import datetime, timezone
import importlib
import json
from pathlib import Path
import sys

from tests.study_runtime_test_helpers import (
    make_profile,
    write_auditable_current_package,
    write_synced_submission_delivery,
    write_study,
    write_submission_metadata_only_bundle,
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_study_progress_import_does_not_require_submission_pdf_dependency(monkeypatch) -> None:
    for module_name in list(sys.modules):
        if module_name in {
            "med_autoscience.controllers.study_progress",
            "med_autoscience.controllers.gate_clearing_batch",
            "med_autoscience.controllers.publication_gate",
            "med_autoscience.controllers.submission_minimal",
            "pypdf",
        }:
            sys.modules.pop(module_name, None)

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "pypdf" or name.startswith("pypdf."):
            raise ModuleNotFoundError("No module named 'pypdf'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    module = importlib.import_module("med_autoscience.controllers.study_progress")

    assert callable(module.read_study_progress)


def _write_publication_eval(
    study_root: Path,
    quest_root: Path,
    *,
    recommended_actions: list[dict[str, object]] | None = None,
    quality_assessment: dict[str, object] | None = None,
) -> Path:
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
        "quality_assessment": quality_assessment
        or {
            "clinical_significance": {
                "status": "partial",
                "summary": "临床问题已经冻结，但当前结果表面还不够稳定。",
                "evidence_refs": [str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")],
            },
            "evidence_strength": {
                "status": "blocked",
                "summary": "当前 claim-evidence 证据链还没有闭环。",
                "evidence_refs": [str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")],
            },
            "novelty_positioning": {
                "status": "partial",
                "summary": "创新点边界已经开始成形，但 reviewer-facing framing 仍待收紧。",
                "evidence_refs": [str(study_root / "artifacts" / "controller" / "study_charter.json")],
            },
            "human_review_readiness": {
                "status": "blocked",
                "summary": "当前稿件还不能作为正式人工审阅包放行。",
                "evidence_refs": [str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")],
            },
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
        "recommended_actions": recommended_actions
        or [
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


def _write_study_charter_and_controller_summary(study_root: Path) -> tuple[Path, Path]:
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    controller_summary_path = study_root / "artifacts" / "controller" / "controller_summary.json"
    _write_json(
        charter_path,
        {
            "schema_version": 1,
            "charter_id": "charter::001-risk::v1",
            "study_id": "001-risk",
            "title": "Diabetes mortality risk paper",
            "publication_objective": "risk stratification external validation",
        },
    )
    _write_json(
        controller_summary_path,
        {
            "schema_version": 1,
            "summary_id": "controller-summary::001-risk::v1",
            "study_id": "001-risk",
            "study_charter_ref": {
                "charter_id": "charter::001-risk::v1",
                "artifact_path": str(charter_path),
            },
            "controller_policy": {
                "scope": "full_research",
                "required_first_anchor": "scout",
            },
            "route_trigger_authority": {
                "decision_policy": "autonomous",
                "launch_profile": "continue_existing_state",
                "startup_contract_profile": "paper_required_autonomous",
            },
        },
    )
    return charter_path, controller_summary_path


def _write_controller_decision(
    study_root: Path,
    quest_root: Path,
    *,
    decision_type: str = "stop_loss",
    requires_human_confirmation: bool = True,
    action_type: str = "stop_runtime",
    reason: str = "当前研究线触发止损边界，需要医生/PI确认。",
) -> Path:
    payload = {
        "schema_version": 1,
        "decision_id": f"study-decision::001-risk::quest-001::{decision_type}::2026-04-10T09:10:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-04-10T09:10:00+00:00",
        "decision_type": decision_type,
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
        "requires_human_confirmation": requires_human_confirmation,
        "controller_actions": [
            {
                "action_type": action_type,
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        "reason": reason,
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
            },
            "figure_loop_guard": {
                "status": "blocked",
                "action": "applied",
                "blockers": [
                    "figure_loop_budget_exceeded",
                    "references_below_floor_during_figure_loop",
                ],
                "advisories": [],
                "report_json": str(
                    quest_root / "artifacts" / "reports" / "figure_loop_guard" / "latest.json"
                ),
                "report_markdown": str(
                    quest_root / "artifacts" / "reports" / "figure_loop_guard" / "latest.md"
                ),
                "suppression_reason": None,
            }
        },
    }
    path = quest_root / "artifacts" / "reports" / "runtime_watch" / "20260410T090800Z.json"
    _write_json(path, payload)
    return path


def _write_publishability_gate_report(quest_root: Path) -> Path:
    path = quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"
    _write_json(
        path,
        {
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "generated_at": "2026-04-10T09:06:00+00:00",
            "quest_id": "quest-001",
            "status": "blocked",
            "allow_write": False,
            "recommended_action": "return_to_publishability_gate",
            "latest_gate_path": str(path),
            "supervisor_phase": "publishability_gate_blocked",
            "current_required_action": "return_to_publishability_gate",
            "controller_stage_note": "论文还没有通过可写门控，bundle 打包仍然属于后续步骤。",
            "blockers": ["missing_post_main_publishability_gate"],
        },
    )
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
        "next_action_summary": "请回到 MAS 控制面确认当前托管运行策略，并决定是否暂停、重启或接管。",
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


def test_study_progress_autonomy_contract_projects_latest_outer_loop_dispatch(
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
    runtime_watch_path = quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json"
    _write_json(
        runtime_watch_path,
        {
            "schema_version": 1,
            "scanned_at": "2026-04-21T04:16:00+00:00",
            "managed_study_outer_loop_dispatches": [
                {
                    "study_id": "001-risk",
                    "quest_id": "quest-001",
                    "decision_type": "continue_same_line",
                    "route_target": "write",
                    "route_key_question": "当前同线稿件还差哪一步最窄修订？",
                    "controller_action_type": "ensure_study_runtime_relaunch_stopped",
                    "dispatch_status": "executed",
                    "source": "runtime_watch_outer_loop_wakeup",
                }
            ],
            "controllers": {},
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
    markdown = module.render_study_progress_markdown(result)

    assert result["autonomy_contract"]["summary"] == (
        "最近一次自治外环已转到“论文写作与结果收紧”，当前关键问题是“当前同线稿件还差哪一步最窄修订？”。"
    )
    assert result["autonomy_contract"]["latest_outer_loop_dispatch"] == {
        "decision_type": "continue_same_line",
        "route_target": "write",
        "route_target_label": "论文写作与结果收紧",
        "route_key_question": "当前同线稿件还差哪一步最窄修订？",
        "dispatch_status": "executed",
        "summary": "最近一次自治外环已转到“论文写作与结果收紧”，当前关键问题是“当前同线稿件还差哪一步最窄修订？”。",
    }
    assert result["autonomy_soak_status"] == {
        "surface_kind": "study_autonomy_soak_status",
        "status": "autonomous_dispatch_visible",
        "summary": "最近一次自治外环已转到“论文写作与结果收紧”，当前关键问题是“当前同线稿件还差哪一步最窄修订？”。",
        "autonomy_state": "autonomous_progress",
        "dispatch_status": "executed",
        "route_target": "write",
        "route_target_label": "论文写作与结果收紧",
        "route_key_question": "当前同线稿件还差哪一步最窄修订？",
        "progress_freshness_status": "missing",
        "next_confirmation_signal": "先补齐论文证据与叙事，再回到发表门控复核。",
        "proof_refs": [
            str(runtime_watch_path),
            str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
        ],
    }
    assert "最近一次自治续跑" in markdown
    assert "自治 Proof / Soak" in markdown
    assert "当前同线稿件还差哪一步最窄修订？" in markdown


def test_study_progress_projects_quality_closure_truth_and_basis(monkeypatch, tmp_path: Path) -> None:
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
    _write_publication_eval(
        study_root,
        quest_root,
        quality_assessment={
            "clinical_significance": {
                "status": "ready",
                "summary": "临床问题与结果表面已经足够稳定，可以继续推进。",
                "evidence_refs": [str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")],
            },
            "evidence_strength": {
                "status": "ready",
                "summary": "核心科学证据已经闭环，剩余工作不在核心证据面。",
                "evidence_refs": [str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")],
            },
            "novelty_positioning": {
                "status": "ready",
                "summary": "创新性边界已经在 charter 与论文线中固定。",
                "evidence_refs": [str(study_root / "artifacts" / "controller" / "study_charter.json")],
            },
            "human_review_readiness": {
                "status": "partial",
                "summary": "当前 package 还需要一轮 finalize 收口后再进入人工审阅。",
                "evidence_refs": [str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")],
            },
        },
        recommended_actions=[
            {
                "action_id": "action-001",
                "action_type": "route_back_same_line",
                "priority": "now",
                "reason": "当前主线只剩 finalize / bundle 收口。",
                "route_target": "finalize",
                "route_key_question": "当前论文线还差哪一步 finalize / submission bundle 收口？",
                "route_rationale": "核心科学问题已经回答，当前只剩同线 finalize 收口。",
                "evidence_refs": [
                    str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json")
                ],
                "requires_controller_decision": True,
            }
        ],
    )
    _write_runtime_escalation(quest_root, study_root)
    _write_runtime_watch(quest_root)
    _write_bash_summary(quest_root)
    _write_details_projection(quest_root)
    publishability_gate_path = _write_publishability_gate_report(quest_root)
    _write_json(
        publishability_gate_path,
        {
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "generated_at": "2026-04-10T09:06:00+00:00",
            "quest_id": "quest-001",
            "status": "blocked",
            "allow_write": False,
            "recommended_action": "complete_bundle_stage",
            "latest_gate_path": str(publishability_gate_path),
            "supervisor_phase": "bundle_stage_blocked",
            "current_required_action": "complete_bundle_stage",
            "controller_stage_note": "bundle-stage blockers are now on the critical path for this paper line",
            "blockers": ["missing_submission_minimal"],
            "medical_publication_surface_named_blockers": ["submission_hardening_incomplete"],
            "medical_publication_surface_route_back_recommendation": "return_to_finalize",
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
                "supervisor_phase": "bundle_stage_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": False,
                "current_required_action": "complete_bundle_stage",
                "deferred_downstream_actions": [],
                "controller_stage_note": "bundle-stage blockers are now on the critical path for this paper line",
            },
            "runtime_escalation_ref": {
                "record_id": "runtime-escalation::001-risk::quest-001::publishability_gate_blocked::2026-04-10T09:07:00+00:00",
                "artifact_path": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
                "summary_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")
    markdown = module.render_study_progress_markdown(result)

    assert result["quality_closure_truth"] == {
        "state": "bundle_only_remaining",
        "summary": "核心科学质量已经闭环；剩余工作收口在定稿与投稿包收尾，同一论文线可以继续自动推进。",
        "current_required_action": "complete_bundle_stage",
        "route_target": "finalize",
    }
    assert result["quality_execution_lane"] == {
        "lane_id": "submission_hardening",
        "lane_label": "投稿包硬化收口",
        "repair_mode": "same_line_route_back",
        "route_target": "finalize",
        "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
        "summary": "当前质量执行线聚焦投稿包硬化收口；先回到定稿与投稿收尾，回答“当前论文线还差哪一个最窄的定稿或投稿包收尾动作？”。",
        "why_now": "核心科学问题已经回答，当前只剩同线 finalize 收口。",
    }
    assert result["same_line_route_truth"] == {
        "surface_kind": "same_line_route_truth",
        "same_line_state": "finalize_only_remaining",
        "same_line_state_label": "同线定稿与投稿包收尾",
        "route_mode": "return",
        "route_target": "finalize",
        "route_target_label": "定稿与投稿收尾",
        "summary": "当前同线路由已经收窄到定稿与投稿包收尾；先回到定稿与投稿收尾，完成当前最小投稿包收口。",
        "current_focus": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
    }
    assert result["quality_closure_basis"]["evidence_strength"]["status"] == "ready"
    assert result["module_surfaces"]["eval_hygiene"]["quality_closure_truth"] == result["quality_closure_truth"]
    assert result["module_surfaces"]["eval_hygiene"]["same_line_route_truth"] == result["same_line_route_truth"]
    assert result["quality_review_agenda"] == {
        "top_priority_issue": "必须优先修复：外部验证队列还没有补齐。",
        "suggested_revision": "先在 finalize 修订：当前主线只剩 finalize / bundle 收口。",
        "next_review_focus": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
        "agenda_summary": (
            "优先修复：必须优先修复：外部验证队列还没有补齐。；"
            "建议修订：先在 finalize 修订：当前主线只剩 finalize / bundle 收口。；"
            "下一轮复评重点：当前论文线还差哪一个最窄的定稿或投稿包收尾动作？"
        ),
    }
    assert result["quality_revision_plan"] == {
        "policy_id": "medical_publication_critique_v1",
        "plan_id": "quality-revision-plan::evaluation-summary::001-risk::quest-001::2026-04-10T09:09:00+00:00",
        "execution_status": "planned",
        "overall_diagnosis": "核心科学质量已经闭环；剩余工作收口在定稿与投稿包收尾，同一论文线可以继续自动推进。",
        "weight_contract": {
            "clinical_significance": 25,
            "evidence_strength": 35,
            "novelty_positioning": 20,
            "human_review_readiness": 20,
        },
        "items": [
            {
                "item_id": "quality-revision-item-1",
                "priority": "p0",
                "dimension": "human_review_readiness",
                "action_type": "stabilize_submission_bundle",
                "action": "先在 finalize 修订，完成当前最小投稿包收口。",
                "rationale": "核心科学质量已经闭环；剩余工作收口在定稿与投稿包收尾，同一论文线可以继续自动推进。",
                "done_criteria": "下一轮复评能够明确确认：当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                "route_target": "finalize",
            }
        ],
        "next_review_focus": ["当前论文线还差哪一个最窄的定稿或投稿包收尾动作？"],
    }
    assert result["quality_review_loop"] == {
        "policy_id": "medical_publication_critique_v1",
        "loop_id": "quality-review-loop::evaluation-summary::001-risk::quest-001::2026-04-10T09:09:00+00:00",
        "closure_state": "bundle_only_remaining",
        "lane_id": "submission_hardening",
        "current_phase": "bundle_hardening",
        "current_phase_label": "投稿包收口",
        "recommended_next_phase": "finalize",
        "recommended_next_phase_label": "定稿与投稿收尾",
        "active_plan_id": "quality-revision-plan::evaluation-summary::001-risk::quest-001::2026-04-10T09:09:00+00:00",
        "active_plan_execution_status": "planned",
        "blocking_issue_count": 1,
        "blocking_issues": ["核心科学质量已经闭环；剩余工作收口在定稿与投稿包收尾，同一论文线可以继续自动推进。"],
        "next_review_focus": ["当前论文线还差哪一个最窄的定稿或投稿包收尾动作？"],
        "re_review_ready": False,
        "summary": "核心科学质量已经闭环，当前只剩投稿包与人工审阅面的收口修订。",
        "recommended_next_action": "先在 finalize 修订，完成当前最小投稿包收口。",
    }
    assert result["module_surfaces"]["eval_hygiene"]["quality_review_agenda"] == result["quality_review_agenda"]
    assert result["module_surfaces"]["eval_hygiene"]["quality_revision_plan"] == result["quality_revision_plan"]
    assert result["module_surfaces"]["eval_hygiene"]["quality_review_loop"] == result["quality_review_loop"]
    assert result["module_surfaces"]["eval_hygiene"]["quality_execution_lane"] == result["quality_execution_lane"]
    assert "## 质量闭环" in markdown
    assert "## 质量评审议程" in markdown
    assert "## 质量评审闭环" in markdown
    assert "## 质量修订计划" in markdown
    assert "当前闭环阶段: 投稿包收口" in markdown
    assert "下一跳: 定稿与投稿收尾" in markdown
    assert "当前阻塞数: 1" in markdown
    assert "闭环摘要: 核心科学质量已经闭环，当前只剩投稿包与人工审阅面的收口修订。" in markdown
    assert "下一动作: 先在 定稿与投稿收尾 修订，完成当前最小投稿包收口。" in markdown
    assert "当前阻塞项: 核心科学质量已经闭环；剩余工作收口在定稿与投稿包收尾，同一论文线可以继续自动推进。" in markdown
    assert "复评关注点: 当前论文线还差哪一个最窄的定稿或投稿包收尾动作？" in markdown
    assert "当前优先问题: 必须优先修复：外部验证队列还没有补齐。" in markdown
    assert "建议修订动作:" in markdown
    assert "当前主线只剩 定稿与投稿收尾 / bundle 收口。" in markdown
    assert "下一轮复评重点: 当前论文线还差哪一个最窄的定稿或投稿包收尾动作？" in markdown
    assert "P0 [人工审阅准备度] -> 定稿与投稿收尾" in markdown
    assert "完成当前最小投稿包收口。" in markdown
    assert "完成标准: 下一轮复评能够明确确认：当前论文线还差哪一个最窄的定稿或投稿包收尾动作？" in markdown
    assert "核心科学质量已经闭环" in markdown
    assert "核心科学证据已经闭环，剩余工作不在核心证据面。" in markdown
    assert "当前质量执行线聚焦投稿包硬化收口" in markdown


def test_study_progress_normalizes_legacy_non_mapping_quality_execution_lane_from_existing_projection(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")

    result = module.build_study_progress_projection(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        status_payload={
            "progress_projection": {
                "schema_version": 1,
                "study_id": "001-risk",
                "current_stage": "publication_supervision",
                "current_stage_summary": "当前主线在 finalize 收口。",
                "paper_stage": "finalize",
                "paper_stage_summary": "当前主线只剩 finalize 收口。",
                "next_system_action": "继续 finalize 收口。",
                "needs_physician_decision": False,
                "quality_execution_lane": "legacy-string-payload",
                "module_surfaces": {
                    "eval_hygiene": {
                        "quality_execution_lane": {
                            "lane_id": "submission_hardening",
                            "summary": "Only finalize-level submission hardening remains.",
                        }
                    }
                },
            }
        },
    )

    assert result["quality_execution_lane"] == {
        "lane_id": "submission_hardening",
        "summary": "Only finalize-level submission hardening remains.",
    }
    assert result["same_line_route_truth"] == {
        "surface_kind": "same_line_route_truth",
        "same_line_state": "finalize_only_remaining",
        "same_line_state_label": "同线定稿与投稿包收尾",
        "route_mode": "return",
        "route_target": "finalize",
        "route_target_label": "定稿与投稿收尾",
        "summary": "当前同线路由已经收窄到定稿与投稿包收尾；先回到定稿与投稿收尾，完成当前最小投稿包收口。",
        "current_focus": "Only finalize-level submission hardening remains.",
    }
    assert result["module_surfaces"]["eval_hygiene"]["quality_execution_lane"] == result["quality_execution_lane"]
    assert result["module_surfaces"]["eval_hygiene"]["same_line_route_truth"] == result["same_line_route_truth"]
    markdown = module.render_study_progress_markdown(result)
    assert "# 研究进度" in markdown
    assert "study_id: `001-risk`" in markdown


def test_study_progress_suppresses_same_line_route_when_publication_supervisor_blocks_bundle_tasks(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")

    result = module.build_study_progress_projection(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        status_payload={
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
            },
            "progress_projection": {
                "schema_version": 1,
                "study_id": "001-risk",
                "current_stage": "publication_supervision",
                "current_stage_summary": "当前主线仍需先回到发表门控。",
                "paper_stage": "publishability_gate_blocked",
                "paper_stage_summary": "当前发表门控仍未放行。",
                "next_system_action": "先回到发表门控。",
                "needs_physician_decision": False,
                "quality_execution_lane": {
                    "lane_id": "submission_hardening",
                    "summary": "Only finalize-level submission hardening remains.",
                },
                "same_line_route_truth": {
                    "surface_kind": "same_line_route_truth",
                    "same_line_state": "finalize_only_remaining",
                    "same_line_state_label": "同线定稿与投稿包收尾",
                    "route_mode": "return",
                    "route_target": "finalize",
                    "route_target_label": "定稿与投稿收尾",
                    "summary": "当前同线路由已经收窄到定稿与投稿包收尾；先回到定稿与投稿收尾，完成当前最小投稿包收口。",
                    "current_focus": "Only finalize-level submission hardening remains.",
                },
                "same_line_route_surface": {
                    "surface_kind": "same_line_route_surface",
                    "lane_id": "submission_hardening",
                    "repair_mode": "same_line_route_back",
                    "route_target": "finalize",
                    "route_target_label": "定稿与投稿收尾",
                    "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                    "summary": "当前质量执行线聚焦投稿包硬化收口；先回到定稿与投稿收尾，回答“当前论文线还差哪一个最窄的定稿或投稿包收尾动作？”。",
                    "why_now": "bundle-stage work is unlocked and can proceed on the critical path",
                    "current_required_action": "continue_bundle_stage",
                    "closure_state": "bundle_only_remaining",
                },
                "module_surfaces": {
                    "eval_hygiene": {
                        "same_line_route_truth": {
                            "surface_kind": "same_line_route_truth",
                            "same_line_state": "finalize_only_remaining",
                            "same_line_state_label": "同线定稿与投稿包收尾",
                            "route_mode": "return",
                            "route_target": "finalize",
                            "route_target_label": "定稿与投稿收尾",
                            "summary": "当前同线路由已经收窄到定稿与投稿包收尾；先回到定稿与投稿收尾，完成当前最小投稿包收口。",
                            "current_focus": "Only finalize-level submission hardening remains.",
                        },
                        "same_line_route_surface": {
                            "surface_kind": "same_line_route_surface",
                            "lane_id": "submission_hardening",
                            "repair_mode": "same_line_route_back",
                            "route_target": "finalize",
                            "route_target_label": "定稿与投稿收尾",
                            "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                            "summary": "当前质量执行线聚焦投稿包硬化收口；先回到定稿与投稿收尾，回答“当前论文线还差哪一个最窄的定稿或投稿包收尾动作？”。",
                            "why_now": "bundle-stage work is unlocked and can proceed on the critical path",
                            "current_required_action": "continue_bundle_stage",
                            "closure_state": "bundle_only_remaining",
                        },
                    }
                },
            },
        },
    )

    assert result["same_line_route_truth"] is None
    assert result["same_line_route_surface"] is None
    assert result["module_surfaces"]["eval_hygiene"]["same_line_route_truth"] is None
    assert result["module_surfaces"]["eval_hygiene"]["same_line_route_surface"] is None


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
    assert result["refs"]["controller_confirmation_summary_path"] is None


def test_study_progress_does_not_project_autonomous_controller_gate_as_physician_decision(
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
    _write_controller_decision(
        study_root,
        quest_root,
        decision_type="continue_same_line",
        requires_human_confirmation=True,
        action_type="ensure_study_runtime",
        reason="MAS should decide the current evidence repair line autonomously.",
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
            "reason": "publishability_gate_blocked",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": [],
            },
            "pending_user_interaction": {},
            "interaction_arbitration": None,
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["current_stage"] == "publication_supervision"
    assert result["needs_physician_decision"] is False
    assert result["physician_decision_summary"] is None
    assert result["refs"]["publication_eval_path"] == str(publication_eval_path)
    assert result["refs"]["controller_confirmation_summary_path"] is None


def test_study_progress_labels_bounded_analysis_as_autonomous_next_step(
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
    _write_controller_decision(
        study_root,
        quest_root,
        decision_type="bounded_analysis",
        requires_human_confirmation=False,
        action_type="ensure_study_runtime",
        reason="MAS 将先完成一轮有限补充分析，再继续当前论文主线。",
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
            "reason": "publishability_gate_blocked",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": [],
            },
            "pending_user_interaction": {},
            "interaction_arbitration": None,
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["needs_physician_decision"] is False
    assert result["physician_decision_summary"] is None
    assert any("有限补充分析" in str(item.get("summary") or "") for item in result["latest_events"])


def test_study_progress_surfaces_same_line_route_back_quality_focus(
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
                "action_id": "action-101",
                "action_type": "route_back_same_line",
                "priority": "now",
                "reason": "当前先修正稿面 claim-evidence 对齐，再继续同线推进。",
                "route_target": "write",
                "route_key_question": "当前稿面最窄的 claim-evidence 修复动作是什么？",
                "route_rationale": "研究方向不变，质量硬阻塞集中在写作面，应该直接回到 write 收口。",
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
                "controller_stage_note": "当前论文仍需先修质量面，再考虑后续打包。",
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
    assert result["intervention_lane"]["repair_mode"] == "same_line_route_back"
    assert result["intervention_lane"]["route_target"] == "write"
    assert result["intervention_lane"]["route_key_question"] == "当前稿面最窄的 claim-evidence 修复动作是什么？"
    assert "论文写作与结果收紧" in result["current_stage_summary"]
    assert "当前稿面最窄的 claim-evidence 修复动作是什么？" in result["next_system_action"]
    assert "论文写作与结果收紧" in result["operator_status_card"]["current_focus"]
    assert "当前稿面最窄的 claim-evidence 修复动作是什么？" in result["operator_status_card"]["current_focus"]
    assert result["needs_physician_decision"] is False


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

    profile_ref = tmp_path / "profile.local.toml"

    result = module.read_study_progress(profile=profile, study_id="001-risk", profile_ref=profile_ref)

    assert result["current_stage"] == "managed_runtime_supervision_gap"
    assert result["intervention_lane"]["lane_id"] == "workspace_supervision_gap"
    assert result["intervention_lane"]["recommended_action_id"] == "refresh_supervision"
    assert result["operator_verdict"] == {
        "surface_kind": "study_operator_verdict",
        "verdict_id": "study_operator_verdict::001-risk::workspace_supervision_gap",
        "study_id": "001-risk",
        "lane_id": "workspace_supervision_gap",
        "severity": "critical",
        "decision_mode": "intervene_now",
        "needs_intervention": True,
        "focus_scope": "workspace",
        "summary": "MedAutoScience 外环监管心跳已陈旧，当前不能保证及时发现掉线并自动恢复。",
        "reason_summary": "MedAutoScience 外环监管心跳已陈旧，当前不能保证及时发现掉线并自动恢复。",
        "primary_step_id": "refresh_supervision",
        "primary_surface_kind": "runtime_watch_refresh",
        "primary_command": (
            "uv run python -m med_autoscience.cli runtime watch --runtime-root "
            + str(profile.runtime_root)
            + " --profile "
            + str(profile_ref.resolve())
            + " --ensure-study-runtimes --apply"
        ),
    }
    assert result["recommended_command"].endswith(
        "runtime watch --runtime-root "
        + str(profile.runtime_root)
        + " --profile "
        + str(profile_ref.resolve())
        + " --ensure-study-runtimes --apply"
    )
    assert result["recommended_commands"][0]["step_id"] == "refresh_supervision"
    assert result["recovery_contract"]["action_mode"] == "refresh_supervision"
    assert "监管心跳已陈旧" in result["current_stage_summary"]
    assert any("监管心跳已陈旧" in item for item in result["current_blockers"])
    assert "supervisor tick" in result["next_system_action"]
    assert result["supervision"]["supervisor_tick_status"] == "stale"


def test_study_progress_projects_explicit_runtime_blocker_before_publication_supervision(
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
            "quest_status": "stopped",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": [],
                "controller_stage_note": "论文还没有通过可写门控，bundle 打包仍然属于后续步骤。",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "reason": "supervisor_tick_report_fresh",
                "summary": "MedAutoScience 外环监管心跳新鲜，当前仍在按合同持续监管。",
                "next_action_summary": "继续按周期 supervisor tick 监管当前托管运行。",
                "latest_report_path": str(study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"),
                "latest_recorded_at": "2026-04-10T09:00:00+00:00",
                "seconds_since_latest_recorded_at": 30,
                "expected_interval_seconds": 300,
                "stale_after_seconds": 600,
            },
            "continuation_state": {
                "quest_status": "stopped",
                "active_run_id": None,
                "continuation_policy": "explicit_rerun_required",
                "continuation_anchor": "decision",
                "continuation_reason": "decision:decision-4e192147",
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["current_stage"] == "runtime_blocked"
    assert "显式" in result["current_stage_summary"]
    assert any("显式" in item for item in result["current_blockers"])
    assert "显式" in result["next_system_action"]


def test_study_progress_projects_manual_finishing_contract_before_runtime_blocker(
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
    study_yaml_path = study_root / "study.yaml"
    study_yaml_path.write_text(
        study_yaml_path.read_text(encoding="utf-8")
        + "\n".join(
            [
                "",
                "manual_finish:",
                "  status: active",
                "  summary: 当前 study 已转入人工打磨收尾；MAS 只需保持兼容性与监督入口，不再把它视为默认自动续跑对象。",
                "  next_action_summary: 继续保持兼容性与监督入口；如需重新自动续跑，再显式 rerun 或 relaunch。",
                "  compatibility_guard_only: true",
                "",
            ]
        ),
        encoding="utf-8",
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
            "quest_status": "stopped",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": [],
                "controller_stage_note": "论文还没有通过可写门控，bundle 打包仍然属于后续步骤。",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "reason": "supervisor_tick_report_fresh",
                "summary": "MedAutoScience 外环监管心跳新鲜，当前仍在按合同持续监管。",
                "next_action_summary": "继续按周期 supervisor tick 监管当前托管运行。",
                "latest_report_path": str(study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"),
                "latest_recorded_at": "2026-04-10T09:00:00+00:00",
                "seconds_since_latest_recorded_at": 30,
                "expected_interval_seconds": 300,
                "stale_after_seconds": 600,
            },
            "continuation_state": {
                "quest_status": "stopped",
                "active_run_id": None,
                "continuation_policy": "explicit_rerun_required",
                "continuation_anchor": "decision",
                "continuation_reason": "decision:decision-4e192147",
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["current_stage"] == "manual_finishing"
    assert "人工打磨收尾" in result["current_stage_summary"]
    assert not any("显式" in item for item in result["current_blockers"])
    assert "兼容性" in result["next_system_action"]


def test_study_progress_projects_bundle_only_submission_ready_parking_before_runtime_blocker(
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
    write_synced_submission_delivery(
        study_root,
        quest_root,
        include_submission_checklist=False,
    )
    summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        "{\n"
        '  "quality_closure_truth": {"state": "bundle_only_remaining"},\n'
        '  "quality_review_loop": {"closure_state": "bundle_only_remaining"},\n'
        '  "quality_assessment": {"human_review_readiness": {"status": "ready"}}\n'
        "}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        module,
        "read_evaluation_summary",
        lambda *, study_root, ref: {
            "schema_version": 1,
            "quality_closure_truth": {"state": "bundle_only_remaining"},
            "quality_assessment": {
                "human_review_readiness": {
                    "status": "ready",
                    "summary": "Human-review package is ready.",
                }
            },
            "quality_execution_lane": {
                "lane_id": "submission_hardening",
                "route_target": "finalize",
                "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                "summary": "Only finalize-level submission hardening remains.",
            },
            "quality_review_loop": {
                "closure_state": "bundle_only_remaining",
                "current_phase": "bundle_hardening",
                "current_phase_label": "投稿包收口",
                "recommended_next_phase": "finalize",
                "recommended_next_phase_label": "定稿与投稿收尾",
                "active_plan_id": "quality-plan::001-risk::v1",
                "active_plan_execution_status": "planned",
                "blocking_issue_count": 1,
                "blocking_issues": ["Only finalize-level cleanup remains."],
                "next_review_focus": ["当前论文线还差哪一个最窄的定稿或投稿包收尾动作？"],
                "re_review_ready": False,
                "summary": "Core scientific quality is closed; only finalize-level bundle cleanup remains.",
                "recommended_next_action": "Return to finalize only if the runtime is explicitly resumed later.",
            },
            "module": "eval_hygiene",
            "surface_kind": "evaluation_module_surface",
            "summary_id": "evaluation-summary::001-risk::latest",
            "summary_ref": str(study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"),
            "promotion_gate_ref": str(study_root / "artifacts" / "eval_hygiene" / "promotion_gate" / "latest.json"),
            "next_action_summary": "先在 finalize 修订，完成当前最小投稿包收口。",
            "overall_verdict": "promising",
            "primary_claim_status": "supported",
            "stop_loss_pressure": "none",
            "requires_controller_decision": True,
            "verdict_summary": "bundle-stage work is unlocked and can proceed on the critical path",
            "status_summary": "bundle-stage work is unlocked and can proceed on the critical path",
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
            "quest_status": "stopped",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
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
                "reason": "supervisor_tick_report_fresh",
                "summary": "MedAutoScience 外环监管心跳新鲜，当前仍在按合同持续监管。",
                "next_action_summary": "继续按周期 supervisor tick 监管当前托管运行。",
                "latest_report_path": str(study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"),
                "latest_recorded_at": "2026-04-10T09:00:00+00:00",
                "seconds_since_latest_recorded_at": 30,
                "expected_interval_seconds": 300,
                "stale_after_seconds": 600,
            },
            "continuation_state": {
                "quest_status": "stopped",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "unchanged_finalize_state",
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["current_stage"] == "manual_finishing"
    assert "投稿包里程碑" in result["current_stage_summary"]
    assert "显式 rerun 或 relaunch" not in result["current_stage_summary"]
    assert "当前 quest 已停止；如需继续，必须显式 rerun 或 relaunch。" not in result["current_blockers"]


def test_study_progress_reopened_task_intake_overrides_bundle_only_parking(
    monkeypatch,
    tmp_path: Path,
) -> None:
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
    current_package_root = study_root / "manuscript" / "current_package"
    current_package_root.mkdir(parents=True, exist_ok=True)
    for rel in ["manuscript.docx", "paper.pdf", "references.bib", "submission_manifest.json", "SUBMISSION_TODO.md"]:
        path = current_package_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("placeholder\n", encoding="utf-8")
    (study_root / "manuscript" / "current_package.zip").write_text("zip\n", encoding="utf-8")
    summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        "{\n"
        '  "quality_closure_truth": {"state": "bundle_only_remaining"},\n'
        '  "quality_review_loop": {"closure_state": "bundle_only_remaining"},\n'
        '  "quality_assessment": {"human_review_readiness": {"status": "ready"}}\n'
        "}\n",
        encoding="utf-8",
    )
    task_intake_module.write_task_intake(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        entry_mode="full_research",
        task_intent=(
            "按最新专家意见重新打开 001 同一论文线的修订任务；当前稿件不能按已达投稿包里程碑直接收口；"
            "必须补做并写入 manuscript 的分层统计分析，并把当前 submission-ready/finalize 判断降回待修订后再评估。"
        ),
        constraints=("本轮不得直接按外投收口。",),
        evidence_boundary=("统计扩展限于预设 subgroup / association analysis。",),
        first_cycle_outputs=("价格顾虑有/无分层的生物制剂使用结构比较表与统计检验结果。",),
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    monkeypatch.setattr(
        module,
        "read_evaluation_summary",
        lambda *, study_root, ref: {
            "schema_version": 1,
            "quality_closure_truth": {"state": "bundle_only_remaining"},
            "quality_assessment": {
                "human_review_readiness": {
                    "status": "ready",
                    "summary": "Human-review package is ready.",
                }
            },
            "quality_execution_lane": {
                "lane_id": "submission_hardening",
                "route_target": "finalize",
                "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                "summary": "Only finalize-level submission hardening remains.",
            },
            "same_line_route_truth": {
                "surface_kind": "same_line_route_truth",
                "same_line_state": "finalize_only_remaining",
                "same_line_state_label": "同线定稿与投稿包收尾",
                "route_mode": "return",
                "route_target": "finalize",
                "route_target_label": "定稿与投稿收尾",
                "summary": "旧的 finalize-only 判断。",
                "current_focus": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
            },
            "same_line_route_surface": {
                "surface_kind": "same_line_route_surface",
                "lane_id": "submission_hardening",
                "repair_mode": "same_line_route_back",
                "route_target": "finalize",
                "summary": "旧的 submission hardening 判断。",
                "closure_state": "bundle_only_remaining",
            },
            "module": "eval_hygiene",
            "surface_kind": "evaluation_module_surface",
            "summary_id": "evaluation-summary::001-risk::latest",
            "summary_ref": str(summary_path),
            "promotion_gate_ref": str(study_root / "artifacts" / "eval_hygiene" / "promotion_gate" / "latest.json"),
            "next_action_summary": "先在 finalize 修订，完成当前最小投稿包收口。",
            "overall_verdict": "promising",
            "primary_claim_status": "supported",
            "stop_loss_pressure": "none",
            "requires_controller_decision": True,
            "verdict_summary": "bundle-stage work is unlocked and can proceed on the critical path",
            "status_summary": "bundle-stage work is unlocked and can proceed on the critical path",
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
            "quest_status": "stopped",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
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
                "reason": "supervisor_tick_report_fresh",
                "summary": "MedAutoScience 外环监管心跳新鲜，当前仍在按合同持续监管。",
                "next_action_summary": "继续按周期 supervisor tick 监管当前托管运行。",
                "latest_report_path": str(study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"),
                "latest_recorded_at": "2026-04-10T09:00:00+00:00",
                "seconds_since_latest_recorded_at": 30,
                "expected_interval_seconds": 300,
                "stale_after_seconds": 600,
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["manual_finish_contract"] is None
    assert result["current_stage"] == "publication_supervision"
    assert result["paper_stage"] == "analysis-campaign"
    assert "待修订状态" in result["current_stage_summary"]
    assert "价格顾虑有/无分层" in result["next_system_action"]
    assert any("待修订状态" in item for item in result["current_blockers"])
    assert result["quality_closure_truth"]["state"] == "quality_repair_required"
    assert result["quality_execution_lane"]["lane_id"] == "general_quality_repair"
    assert result["same_line_route_truth"]["same_line_state"] == "bounded_analysis"
    assert result["same_line_route_truth"]["route_target"] == "analysis-campaign"
    assert result["module_surfaces"]["eval_hygiene"]["same_line_route_truth"]["route_target"] == "analysis-campaign"
    assert result["intervention_lane"]["lane_id"] == "quality_floor_blocker"


def test_study_progress_does_not_project_study_completed_when_completion_contract_is_not_ready(
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

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "002-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-002",
                "auto_resume": False,
            },
            "quest_id": "quest-002",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "completed",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {
                "ready": False,
                "status": "incomplete",
                "completion_status": "completed",
                "summary": "论文交付声明已写，但 final submission evidence 还没真正补齐。",
                "missing_evidence_paths": ["manuscript/final/submission_manifest.json"],
            },
            "decision": "blocked",
            "reason": "study_completion_contract_not_ready",
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
                "status": "fresh",
                "reason": "supervisor_tick_report_fresh",
                "summary": "MedAutoScience 外环监管心跳新鲜，当前仍在按合同持续监管。",
                "next_action_summary": "继续按周期 supervisor tick 监管当前托管运行。",
                "latest_report_path": str(study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"),
                "latest_recorded_at": "2026-04-10T09:00:00+00:00",
                "seconds_since_latest_recorded_at": 30,
                "expected_interval_seconds": 300,
                "stale_after_seconds": 600,
            },
            "continuation_state": {
                "quest_status": "completed",
                "active_run_id": None,
                "continuation_policy": "auto",
                "continuation_anchor": None,
                "continuation_reason": None,
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="002-risk")

    assert result["current_stage"] == "runtime_blocked"
    assert "收尾/交付" not in result["current_stage_summary"]
    assert any("final submission 证据还未补齐" in item for item in result["current_blockers"])


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
