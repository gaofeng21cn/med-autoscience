from __future__ import annotations

import importlib
from pathlib import Path


def _truth_snapshot() -> dict[str, object]:
    return {
        "surface": "study_truth_snapshot",
        "truth_epoch": "truth-event-000004-live",
        "authority_epoch": "truth-event-000004-live",
        "canonical_next_action": "request_opl_handoff_hydration",
        "blocking_reasons": [
            "opl_current_control_state.handoff_required",
            "publication_supervisor_state.bundle_tasks_downstream_only",
        ],
        "dominant_authority_refs": [
            {
                "event_id": "truth-event-000004-live",
                "event_type": "opl_runtime_owner_handoff",
                "recorded_at": "2026-05-01T00:00:00+00:00",
            }
        ],
        "allowed_controller_actions": ["read_opl_current_control_state", "open_monitoring_entry"],
        "package_state": {
            "authority_state": "provisionally_current_for_epoch",
            "writer_epoch": "writer::run-e52f5574",
            "source_signature": "source::abc",
        },
        "writer_epoch": "writer::run-e52f5574",
        "source_signature": "truth-snapshot::abc",
    }


def _authority_snapshot() -> dict[str, object]:
    return {
        "surface": "authority_snapshot",
        "control_state": "opl_handoff_required",
        "canonical_next_action": "request_opl_handoff_hydration",
        "canonical_runtime_action": "request_opl_handoff_hydration",
        "dispatch_gate": {
            "state": "blocked",
            "dispatch_allowed": False,
            "blocking_reasons": ["opl_current_control_state.handoff_required"],
        },
        "route_authorization": {
            "authorized": False,
            "paper_write_allowed": False,
            "bundle_build_allowed": False,
        },
        "blocking_reasons": ["opl_current_control_state.handoff_required"],
        "allowed_controller_actions": ["read_opl_current_control_state", "open_monitoring_entry"],
        "authority_refs": {
            "study_truth": {"epoch": "truth-event-000004-live"},
            "opl_current_control_state": {"epoch": "opl-current-control-state-event-000004-live"},
        },
    }


def _study_macro_state() -> dict[str, object]:
    return {
        "surface": "study_macro_state",
        "schema_version": 1,
        "study_id": "003-dpcc",
        "writer_state": "parked",
        "user_next": "submit_info",
        "reason": "external_info",
        "details": {
            "truth_epoch": "truth-event-000004-live",
            "missing_external_info": ["authors", "ethics"],
            "package_delivered": True,
            "reopen_allowed": True,
            "reopen_mode": "external_info_or_revision_intake",
        },
        "conditions": [
            {
                "type": "ExternalInfoPending",
                "status": "true",
                "summary": "submission package waits for external metadata",
            }
        ],
        "source_fingerprint": "macro::003-dpcc",
    }


def test_study_progress_compact_payload_derives_macro_state_from_current_payload() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.projection")

    payload = module._normalize_study_progress_payload(
        {
            "study_id": "003-dpcc",
            "quest_status": "paused",
            "reason": "quest_waiting_for_submission_metadata",
            "auto_runtime_parked": {"parked": True, "parked_state": "external_metadata_pending"},
            "submission_metadata": {"missing_external_info": ["authors", "ethics"]},
            "study_truth_snapshot": {
                **_truth_snapshot(),
                "package_state": {"authority_state": "current"},
            },
        }
    )

    assert payload["study_macro_state"]["writer_state"] == "parked"
    assert payload["study_macro_state"]["user_next"] == "submit_info"
    assert payload["study_macro_state"]["reason"] == "external_info"


def test_current_write_routeback_overrides_stale_progress_run_and_package_handoff() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.projection")
    user_visible_projection = importlib.import_module(
        "med_autoscience.controllers.study_progress.user_visible_projection"
    )

    payload = module._normalize_study_progress_payload(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_status": "waiting_for_user",
            "reason": "opl_stage_attempt_admission_required",
            "active_run_id": None,
            "domain_transition": {
                "decision_type": "route_back_same_line",
                "route_target": "write",
                "owner": "write",
                "controller_action": "request_opl_stage_attempt",
                "next_work_unit": {
                    "unit_id": "dm002_same_line_publication_paper_repair",
                    "lane": "write",
                    "summary": "Controller-authorized paper repair and package rebuild from latest evidence.",
                },
            },
            "study_truth_snapshot": {
                "truth_epoch": "truth-event-dm002-write-route",
                "source_signature": "truth-source-dm002-write-route",
            },
            "current_stage": "opl_current_control_state_handoff_required",
            "paper_stage": "publishability_gate_blocked",
            "paper_progress_stall": {
                "state": "blocked_controller_route",
                "next_owner": "write",
                "summary": "Current write owner route is open.",
            },
            "delivery_inspection": {
                "status": "current",
                "freshness": {"delivery_status": "current"},
            },
            "gate_clearing_batch_followthrough": {
                "gate_replay_status": "clear",
                "failed_unit_count": 0,
            },
            "progress_freshness": {
                "meaningful_artifact_delta_freshness": {
                    "status": "fresh",
                    "latest_progress_at": "2026-05-22T10:32:16+00:00",
                }
            },
            "supervision": {
                "active_run_id": "mas-run-stale-progress-only",
                "health_status": "stale",
            },
        }
    )
    payload["user_visible_projection"] = user_visible_projection.build_user_visible_projection(payload)

    assert payload["study_macro_state"]["writer_state"] == "queued"
    assert payload["study_macro_state"]["user_next"] == "repair"
    assert payload["study_macro_state"]["reason"] == "quality"
    assert payload["user_visible_projection"]["next_owner"] == "write"
    assert payload["user_visible_projection"]["user_action_required"] is False
    assert "当前包已经可直接交给用户审阅" not in payload["user_visible_projection"]["next_system_action"]
    assert payload["user_visible_projection"]["next_system_action"] == "等待质量修复/复审 owner 完成处理。"


def test_legacy_current_work_unit_is_diagnostic_only_during_current_live_run() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.user_visible_projection"
    )
    live_condition = {"type": "LiveWriter", "status": "true"}

    projection = module.build_user_visible_projection(
        {
            "study_id": "study-live",
            "active_run_id": "opl-stage-attempt://sat-current",
            "current_stage": "managed_runtime_active",
            "study_macro_state": {
                "writer_state": "live",
                "user_next": "none",
                "reason": "runtime_active",
                "details": {"active_run_id": "opl-stage-attempt://sat-current"},
                "conditions": [live_condition],
            },
            "supervision": {
                "active_run_id": "opl-stage-attempt://sat-current",
                "health_status": "healthy",
                "supervisor_tick_status": "active",
            },
            "progress_freshness": {
                "meaningful_artifact_delta_freshness": {
                    "status": "fresh",
                    "latest_progress_at": "2026-07-10T00:00:00+00:00",
                    "changed_refs": ["paper/draft.md"],
                }
            },
            "current_work_unit": {
                "status": "typed_blocker",
                "owner": "legacy-owner",
                "state": {
                    "typed_blocker": {
                        "blocked_reason": "legacy_only_blocker",
                        "owner": "legacy-owner",
                    }
                },
            },
        }
    )

    assert projection["writer_state"] == "live"
    assert projection["next_owner"] is None
    assert projection["actual_write_active"] is True
    assert projection["why_not_progressing"] is None
    assert projection["next_system_action"] == "观察自动运行推进。"
    assert projection["paper_progress_state"]["actual_write_active"] is True
    assert projection["paper_progress_state"]["next_owner"] is None
    assert projection["supervision"]["active_run_id"] == "opl-stage-attempt://sat-current"
    assert projection["supervision"]["health_status"] == "healthy"
    assert "liveness_suppressed_by" not in projection["supervision"]
    assert projection["study_macro_state"]["writer_state"] == "live"
    assert projection["study_macro_state"]["details"]["active_run_id"] == (
        "opl-stage-attempt://sat-current"
    )
    assert projection["study_macro_state"]["conditions"] == [live_condition]
