from __future__ import annotations

import importlib
from pathlib import Path

import pytest


def make_status_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": "/tmp/studies/001-risk",
        "entry_mode": "full_research",
        "execution": {"quest_id": "quest-001", "auto_resume": True},
        "quest_id": "quest-001",
        "quest_root": "/tmp/runtime/quests/quest-001",
        "quest_exists": True,
        "quest_status": "paused",
        "runtime_binding_path": "/tmp/studies/001-risk/runtime_binding.yaml",
        "runtime_binding_exists": True,
        "workspace_contracts": {"overall_ready": True},
        "startup_data_readiness": {"status": "clear"},
        "startup_boundary_gate": {"allow_compute_stage": True},
        "runtime_reentry_gate": {"allow_runtime_entry": True},
        "study_completion_contract": {"status": "absent", "ready": False},
        "controller_first_policy_summary": "summary",
        "automation_ready_summary": "ready",
    }
    payload.update(overrides)
    return payload


def make_completion_sync_payload(
    *,
    quest_id: str = "quest-001",
    status: str = "completed",
    summary: str = "Study completed.",
    approval_text: str = "同意结题",
) -> dict[str, object]:
    return {
        "completion_request": {
            "status": "ok",
            "interaction_id": "interaction-001",
            "snapshot": {"quest_id": quest_id, "status": "running"},
        },
        "approval_message": {
            "ok": True,
            "message": {
                "id": "msg-approval",
                "content": approval_text,
            },
        },
        "completion": {
            "ok": True,
            "status": status,
            "snapshot": {"quest_id": quest_id, "status": status},
            "message": summary,
        },
    }


def make_startup_hydration_report(quest_root: Path) -> dict[str, object]:
    return {
        "status": "hydrated",
        "recorded_at": "2026-04-03T09:00:00+00:00",
        "quest_root": str(quest_root),
        "entry_state_summary": f"Study root: {quest_root}",
        "literature_report": {"record_count": 0},
        "written_files": [str(quest_root / "paper" / "medical_analysis_contract.json")],
        "report_path": str(quest_root / "artifacts" / "reports" / "startup" / "hydration_report.json"),
    }


def make_startup_hydration_validation_report(
    quest_root: Path,
    *,
    status: str = "clear",
    blockers: list[str] | None = None,
) -> dict[str, object]:
    return {
        "status": status,
        "recorded_at": "2026-04-03T09:05:00+00:00",
        "quest_root": str(quest_root),
        "blockers": blockers or [],
        "contract_statuses": {
            "medical_analysis_contract": "resolved",
            "medical_reporting_contract": "resolved",
        },
        "checked_paths": {
            "medical_analysis_contract_path": str(quest_root / "paper" / "medical_analysis_contract.json"),
            "medical_reporting_contract_path": str(quest_root / "paper" / "medical_reporting_contract.json"),
        },
        "report_path": str(
            quest_root / "artifacts" / "reports" / "startup" / "hydration_validation_report.json"
        ),
    }


def make_startup_contract_validation_payload(
    *,
    status: str = "clear",
    blockers: list[str] | None = None,
    medical_analysis_contract_status: str | None = "resolved",
    medical_reporting_contract_status: str | None = "resolved",
    medical_analysis_reason_code: str | None = None,
    medical_reporting_reason_code: str | None = None,
) -> dict[str, object]:
    return {
        "status": status,
        "blockers": list(blockers or []),
        "contract_statuses": {
            "medical_analysis_contract": medical_analysis_contract_status,
            "medical_reporting_contract": medical_reporting_contract_status,
        },
        "reason_codes": {
            "medical_analysis_contract": medical_analysis_reason_code,
            "medical_reporting_contract": medical_reporting_reason_code,
        },
    }


def make_analysis_bundle_result(*, ready: bool = True) -> dict[str, object]:
    before = {
        "ready": ready,
        "python": {"ready": ready},
        "r": {"ready": ready},
    }
    return {
        "action": "already_ready" if ready else "ensure_bundle",
        "before": before,
        "after": before,
        "ready": ready,
    }


def make_runtime_overlay_result(*, all_roots_ready: bool = True) -> dict[str, object]:
    return {
        "authority": {"selected_action": "noop", "post_status": {"all_targets_ready": True}},
        "materialization": {"materialized_surface_count": 1, "surfaces": []},
        "audit": {
            "all_roots_ready": all_roots_ready,
            "surface_count": 1,
            "surfaces": [],
        },
    }


def make_startup_context_sync_payload(*, quest_id: str = "quest-001") -> dict[str, object]:
    return {
        "ok": True,
        "quest_id": quest_id,
        "snapshot": {
            "quest_id": quest_id,
            "startup_contract": {"schema_version": 4},
            "requested_baseline_ref": None,
        },
    }


def make_partial_quest_recovery_payload(*, quest_id: str = "quest-001") -> dict[str, object]:
    return {
        "status": "archived_invalid_partial_quest_root",
        "quest_root": f"/tmp/runtime/quests/{quest_id}",
        "archived_root": f"/tmp/runtime/recovery/invalid_partial_quest_roots/{quest_id}-20260403T000000Z",
        "missing_required_files": ["quest.yaml"],
    }


def make_publication_supervisor_state_payload(
    *,
    supervisor_phase: str = "scientific_anchor_missing",
    current_required_action: str = "return_to_publishability_gate",
    bundle_tasks_downstream_only: bool = True,
    upstream_scientific_anchor_ready: bool = False,
) -> dict[str, object]:
    return {
        "supervisor_phase": supervisor_phase,
        "phase_owner": "publication_gate",
        "upstream_scientific_anchor_ready": upstream_scientific_anchor_ready,
        "bundle_tasks_downstream_only": bundle_tasks_downstream_only,
        "current_required_action": current_required_action,
        "deferred_downstream_actions": [],
        "controller_stage_note": "bundle suggestions are downstream-only until the publication gate allows write",
    }


def make_execution_owner_guard_payload(
    *,
    active_run_id: str | None = "run-live",
    publication_gate_allows_direct_write: bool = False,
) -> dict[str, object]:
    return {
        "owner": "managed_runtime",
        "supervisor_only": True,
        "guard_reason": "live_managed_runtime",
        "active_run_id": active_run_id,
        "current_required_action": "supervise_managed_runtime",
        "allowed_actions": [
            "read_runtime_status",
            "notify_user_runtime_is_live",
            "open_monitoring_entry",
            "pause_runtime",
            "resume_runtime",
            "stop_runtime",
            "record_user_decision",
        ],
        "forbidden_actions": [
            "direct_study_execution",
            "direct_runtime_owned_write",
            "direct_paper_line_write",
            "direct_bundle_build",
            "direct_compiled_bundle_proofing",
        ],
        "runtime_owned_roots": [
            "/tmp/runtime/quests/quest-001",
            "/tmp/runtime/quests/quest-001/.ds",
            "/tmp/runtime/quests/quest-001/paper",
            "/tmp/runtime/quests/quest-001/release",
            "/tmp/runtime/quests/quest-001/artifacts",
        ],
        "takeover_required": True,
        "takeover_action": "pause_runtime_then_explicit_human_takeover",
        "publication_gate_allows_direct_write": publication_gate_allows_direct_write,
        "controller_stage_note": (
            "live managed runtime owns study-local execution; the foreground agent must stay supervisor-only "
            "until explicit takeover"
        ),
    }


def make_pending_user_interaction_payload() -> dict[str, object]:
    return {
        "interaction_id": "progress-standby-001",
        "kind": "progress",
        "waiting_interaction_id": "progress-standby-001",
        "default_reply_interaction_id": "progress-standby-001",
        "pending_decisions": ["progress-standby-001"],
        "blocking": True,
        "reply_mode": "blocking",
        "expects_reply": True,
        "allow_free_text": True,
        "message": "[等待决策] 请由 Gateway 接管并转发给用户。",
        "summary": "等待新的用户消息。",
        "reply_schema": {"type": "free_text"},
        "decision_type": None,
        "options_count": 0,
        "guidance_requires_user_decision": None,
        "source_artifact_path": "/tmp/runtime/quests/quest-001/.ds/worktrees/paper-main/artifacts/progress/progress-standby-001.json",
        "relay_required": True,
    }


def make_progress_projection_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "generated_at": "2026-04-11T01:00:00+00:00",
        "study_id": "001-risk",
        "study_root": "/tmp/studies/001-risk",
        "quest_id": "quest-001",
        "quest_root": "/tmp/runtime/quests/quest-001",
        "current_stage": "publication_supervision",
        "current_stage_summary": "当前已有论文包雏形，但真正的硬阻塞仍在论文可发表性面。",
        "paper_stage": "publishability_gate_blocked",
        "paper_stage_summary": "当前关键路径是补齐论文证据与叙事，而不是抢跑打包。",
        "latest_events": [
            {
                "timestamp": "2026-04-11T00:58:00+00:00",
                "time_label": "2026-04-11 00:58 UTC",
                "category": "runtime_progress",
                "title": "托管运行时完成一段推进",
                "summary": "完成外部验证数据清点，正在整理论文证据面。",
                "source": "bash_summary",
                "artifact_path": "/tmp/runtime/quests/quest-001/.ds/bash_exec/summary.json",
            }
        ],
        "current_blockers": [
            "缺少最小投稿包导出。",
            "论文叙事或方法/结果书写面仍有硬阻塞。",
        ],
        "next_system_action": "先补齐论文证据与叙事，再回到发表门控复核。",
        "needs_physician_decision": False,
        "physician_decision_summary": None,
        "runtime_decision": "noop",
        "runtime_reason": "quest_already_running",
        "continuation_state": {"quest_status": "running", "active_run_id": "run-001"},
        "interaction_arbitration": None,
        "supervision": {
            "browser_url": "http://127.0.0.1:21999/quests/quest-001",
            "quest_session_api_url": "http://127.0.0.1:21999/api/sessions/run-001",
            "active_run_id": "run-001",
            "health_status": "live",
            "supervisor_tick_status": "fresh",
            "supervisor_tick_required": True,
            "supervisor_tick_summary": "MAS 外环监管心跳新鲜。",
            "supervisor_tick_latest_recorded_at": "2026-04-11T00:59:00+00:00",
            "launch_report_path": "/tmp/studies/001-risk/artifacts/runtime/last_launch_report.json",
        },
        "refs": {
            "launch_report_path": "/tmp/studies/001-risk/artifacts/runtime/last_launch_report.json",
            "publication_eval_path": "/tmp/studies/001-risk/artifacts/publication_eval/latest.json",
            "controller_decision_path": "/tmp/studies/001-risk/artifacts/controller_decisions/latest.json",
            "runtime_supervision_path": "/tmp/studies/001-risk/artifacts/runtime/runtime_supervision/latest.json",
            "runtime_escalation_path": None,
            "runtime_watch_report_path": "/tmp/runtime/quests/quest-001/artifacts/reports/runtime_watch/latest.json",
            "bash_summary_path": "/tmp/runtime/quests/quest-001/.ds/bash_exec/summary.json",
            "details_projection_path": "/tmp/runtime/quests/quest-001/.ds/projections/details.v1.json",
        },
    }










































































