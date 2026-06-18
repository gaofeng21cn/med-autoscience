from __future__ import annotations


def runtime_continuity_payload() -> dict[str, object]:
    return {
        "runtime_session": {
            "worker_state": "stale",
            "worker_running": False,
            "active_run_id": None,
            "last_known_run_id": "run-stale-001",
            "runtime_liveness_status": "stale",
            "last_seen_at": "2026-05-08T00:40:00+00:00",
            "monitor_kind": "mas_per_run_worker_wrapper",
            "monitor_state": "stale",
            "heartbeat_age_seconds": 420,
            "last_output_at": "2026-05-08T00:38:00+00:00",
            "stale_reason": "heartbeat_ttl_exceeded",
            "will_start_llm": False,
            "freshness_state": "stale",
            "freshness_age_seconds": 1500,
            "evidence_refs": ["studies/001-risk/artifacts/runtime/session/latest.json"],
        },
        "owner_receipt_handoff": {
            "current_action": "safe_reconcile_ready",
            "reason": "worker_stale",
            "next_owner": "mas_controller",
            "next_eligible_tick": "2026-05-08T01:10:00+00:00",
            "dedupe_fingerprint": "runtime-continuity-001",
            "authority": {
                "quality_ready_authorized": False,
                "publication_ready_authorized": False,
                "submission_ready_authorized": False,
            },
            "evidence_refs": ["studies/001-risk/artifacts/runtime/owner_receipt_handoff/latest.json"],
        },
        "runtime_reconcile_trigger": {
            "safe_to_request": True,
            "recommended_command": (
                "uv run python -m med_autoscience.cli owner-route-reconcile "
                "--profile /workspace/profile.toml --studies 001-risk "
                "--developer-supervisor-mode external_observe"
            ),
            "dedupe_fingerprint": "runtime-continuity-001",
            "will_start_llm": False,
            "source_refs": ["studies/001-risk/artifacts/runtime/owner_route/latest.json"],
        },
        "owner_route": {
            "next_owner": "mas_controller",
            "owner_reason": "runtime_stale",
            "source_fingerprint": "runtime-continuity-001",
            "work_unit_fingerprint": "runtime-continuity-001",
            "source_refs": {
                "runtime_health_epoch": "runtime-health-001",
                "publication_eval_path": "studies/001-risk/artifacts/publication_eval/latest.json",
            },
        },
        "paper_progress_stall": {
            "why_not_running": "worker heartbeat is stale; no new manuscript artifact delta",
            "same_fingerprint_or_handoff": "same_fingerprint",
            "source_refs": ["studies/001-risk/artifacts/autonomy/slo_status/latest.json"],
        },
    }


def progress_payload(study_id: str = "001-risk") -> dict[str, object]:
    return {
        "study_id": study_id,
        "generated_at": "2026-05-08T01:00:00+00:00",
        "user_visible_projection": {
            "schema_version": 2,
            "writer_state": "live",
            "user_next": "wait",
            "reason": "quality_repair",
            "state_label": "质量修复/复审中",
            "state_summary": "正在补齐统计和证据账本，当前无需医生操作。",
            "current_stage": "quality_repair",
            "current_stage_summary": "AI reviewer 要求补充 subgroup sensitivity analysis。",
            "paper_stage": "revision",
            "paper_stage_summary": "论文主线处于返修强化阶段。",
            "current_blockers": ["subgroup sensitivity table 尚未刷新"],
            "next_system_action": "补充 subgroup 分析并更新 review ledger。",
            "needs_physician_decision": False,
            "evidence": {
                "latest_events": [
                    {
                        "timestamp": "2026-05-08T00:58:00+00:00",
                        "summary": "完成 reviewer gap triage。",
                    }
                ],
                "refs": [
                    "studies/001-risk/artifacts/supervision/opl_runtime_owner_handoff/latest.json",
                ],
            },
            "evidence_refs": [
                "studies/001-risk/artifacts/controller_decisions/latest.json",
            ],
        },
        "progress_freshness": {
            "status": "stale",
            "summary": "最近 90 分钟没有新的可见写作推进。",
            "latest_event_at": "2026-05-08T00:58:00+00:00",
        },
        "publication_eval": {
            "verdict": {
                "overall_verdict": "blocked",
                "summary": "证据链仍需补强。",
            },
            "quality_assessment": {
                "statistics": {
                    "status": "blocked",
                    "summary": "缺少 subgroup sensitivity table。",
                }
            },
        },
        "delivery_inspection": {
            "current_package": {
                "status": "missing",
                "summary": "current package 尚未生成。",
            }
        },
        "supervision": {
            "browser_url": "http://127.0.0.1:20999",
            "health_status": "refs_only",
        },
        "opl_current_control_state": {
            "active_run_id": "run-001",
            "status": "provider_admitted",
            "supervisor_tick_status": "fresh",
        },
        "current_owner_delta": {
            "surface_kind": "current_owner_delta",
            "owner": "ai_reviewer",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "quality-repair-001",
            "work_unit_fingerprint": "quality-repair-fp-001",
            "required_delta_kind": "owner_receipt_or_typed_blocker",
            "target_surface": {
                "surface_ref": "studies/001-risk/artifacts/publication_eval/latest.json",
            },
            "latest_owner_answer_kind": "typed_blocker",
            "latest_owner_answer_ref": "studies/001-risk/artifacts/owner/typed_blocker.json",
        },
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "owner": "ai_reviewer",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "quality-repair-001",
            "work_unit_fingerprint": "quality-repair-fp-001",
        },
        "outer_supervision_slo": {
            "surface_kind": "outer_supervision_slo",
            "state": "fresh",
            "latest_outer_supervision_at": "2026-05-08T00:59:00+00:00",
        },
        "refs": {
            "progress_projection": "studies/001-risk/progress_projection.json",
            "domain_health_diagnostic": "studies/001-risk/artifacts/domain_health_diagnostic/latest.json",
            "publication_eval": "studies/001-risk/artifacts/publication_eval/latest.json",
        },
    }


_runtime_continuity_payload = runtime_continuity_payload
_progress_payload = progress_payload
