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


def test_publishability_gate_report_path_prefers_fresher_latest_gate_over_runtime_watch_pointer(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    quest_root = tmp_path / "runtime" / "quests" / "quest-001"
    gate_root = quest_root / "artifacts" / "reports" / "publishability_gate"
    stale_gate_path = gate_root / "2026-04-24T024953Z.json"
    latest_gate_path = gate_root / "latest.json"

    _write_json(
        stale_gate_path,
        {
            "schema_version": 1,
            "generated_at": "2026-04-24T02:49:53+00:00",
            "status": "blocked",
        },
    )
    _write_json(
        latest_gate_path,
        {
            "schema_version": 1,
            "generated_at": "2026-04-24T04:07:59+00:00",
            "status": "clear",
        },
    )

    result = module._publishability_gate_report_path(
        runtime_watch_payload={
            "controllers": {
                "publication_gate": {
                    "report_json": str(stale_gate_path),
                }
            }
        },
        quest_root=quest_root,
    )

    assert result == latest_gate_path.resolve()


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
