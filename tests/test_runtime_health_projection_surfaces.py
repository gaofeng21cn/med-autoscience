from __future__ import annotations

import importlib


def _runtime_health_snapshot() -> dict[str, object]:
    return {
        "surface": "runtime_health_snapshot",
        "runtime_health_epoch": "runtime-health-event-000002-live",
        "canonical_runtime_action": "recover_runtime",
        "attempt_state": "recovering",
        "retry_budget_remaining": 2,
        "worker_liveness_state": {
            "state": "missing_live_session",
            "runtime_liveness_status": "none",
            "worker_running": False,
            "active_run_id": None,
        },
        "supervisor_state": {"status": "fresh"},
        "dominant_runtime_refs": [
            {
                "event_id": "runtime-health-event-000002-live",
                "event_type": "runtime_state_observed",
                "recorded_at": "2026-05-01T00:00:00+00:00",
            }
        ],
        "blocking_reasons": ["quest_marked_running_but_no_live_session"],
        "allowed_controller_actions": ["read_runtime_status", "recover_runtime"],
        "source_signature": "runtime-health-snapshot::abc",
    }


def test_mcp_progress_compact_projection_carries_runtime_health_snapshot_summary() -> None:
    module = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")

    compact = module.compact_study_progress_projection(
        {
            "study_id": "002-dm-cvd",
            "runtime_health_epoch": "runtime-health-event-000002-live",
            "current_stage": "managed_runtime_recovering",
            "runtime_health_snapshot": _runtime_health_snapshot(),
            "refs": {"runtime_health_snapshot_path": "/workspace/studies/002/artifacts/runtime/health/latest.json"},
        }
    )

    assert compact["runtime_health_epoch"] == "runtime-health-event-000002-live"
    assert compact["runtime_health_snapshot"] == {
        "runtime_health_epoch": "runtime-health-event-000002-live",
        "canonical_runtime_action": "recover_runtime",
        "attempt_state": "recovering",
        "retry_budget_remaining": 2,
        "worker_liveness_state": {
            "state": "missing_live_session",
            "runtime_liveness_status": "none",
            "worker_running": False,
            "active_run_id": None,
        },
        "supervisor_state": {"status": "fresh"},
        "dominant_runtime_refs": [
            {
                "event_id": "runtime-health-event-000002-live",
                "event_type": "runtime_state_observed",
                "recorded_at": "2026-05-01T00:00:00+00:00",
            }
        ],
        "blocking_reasons": ["quest_marked_running_but_no_live_session"],
        "allowed_controller_actions": ["read_runtime_status", "recover_runtime"],
        "source_signature": "runtime-health-snapshot::abc",
    }


def test_workspace_cockpit_study_item_carries_runtime_health_snapshot_summary() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    item = module._study_item(
        progress_payload={
            "study_id": "002-dm-cvd",
            "runtime_health_epoch": "runtime-health-event-000002-live",
            "runtime_health_snapshot": _runtime_health_snapshot(),
            "supervision": {"health_status": "recovering"},
        },
        profile_ref="/tmp/profile.toml",
    )

    assert item["runtime_health_epoch"] == "runtime-health-event-000002-live"
    assert item["runtime_health_snapshot"]["canonical_runtime_action"] == "recover_runtime"


def test_domain_health_diagnostic_managed_study_action_carries_runtime_health_snapshot_summary() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup")

    action = module._serialize_managed_study_action(
        {
            "study_id": "002-dm-cvd",
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "runtime_health_snapshot": _runtime_health_snapshot(),
        }
    )

    assert action["runtime_health_epoch"] == "runtime-health-event-000002-live"
    assert action["runtime_health_snapshot"]["canonical_runtime_action"] == "recover_runtime"
