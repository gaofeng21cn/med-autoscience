from __future__ import annotations

import importlib


def _truth_snapshot() -> dict[str, object]:
    return {
        "surface": "study_truth_snapshot",
        "truth_epoch": "truth-event-000004-live",
        "authority_epoch": "truth-event-000004-live",
        "canonical_next_action": "supervise_runtime",
        "blocking_reasons": [
            "execution_owner_guard.supervisor_only",
            "publication_supervisor_state.bundle_tasks_downstream_only",
        ],
        "dominant_authority_refs": [
            {
                "event_id": "truth-event-000004-live",
                "event_type": "runtime_supervision_tick",
                "recorded_at": "2026-05-01T00:00:00+00:00",
            }
        ],
        "allowed_controller_actions": ["read_runtime_status", "open_monitoring_entry"],
        "package_state": {
            "authority_state": "provisionally_current_for_epoch",
            "writer_epoch": "writer::run-e52f5574",
            "source_signature": "source::abc",
        },
        "writer_epoch": "writer::run-e52f5574",
        "source_signature": "truth-snapshot::abc",
    }


def test_mcp_progress_compact_projection_carries_truth_snapshot_summary() -> None:
    module = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")

    compact = module.compact_study_progress_projection(
        {
            "study_id": "003-dpcc",
            "truth_epoch": "truth-event-000004-live",
            "current_stage": "runtime_supervision",
            "study_truth_snapshot": _truth_snapshot(),
            "refs": {"study_truth_snapshot_path": "/workspace/studies/003/artifacts/truth/latest.json"},
        }
    )

    assert compact["truth_epoch"] == "truth-event-000004-live"
    assert compact["study_truth_snapshot"] == {
        "truth_epoch": "truth-event-000004-live",
        "authority_epoch": "truth-event-000004-live",
        "canonical_next_action": "supervise_runtime",
        "blocking_reasons": [
            "execution_owner_guard.supervisor_only",
            "publication_supervisor_state.bundle_tasks_downstream_only",
        ],
        "dominant_authority_refs": [
            {
                "event_id": "truth-event-000004-live",
                "event_type": "runtime_supervision_tick",
                "recorded_at": "2026-05-01T00:00:00+00:00",
            }
        ],
        "allowed_controller_actions": ["read_runtime_status", "open_monitoring_entry"],
        "package_state": {
            "authority_state": "provisionally_current_for_epoch",
            "writer_epoch": "writer::run-e52f5574",
            "source_signature": "source::abc",
        },
        "writer_epoch": "writer::run-e52f5574",
        "source_signature": "truth-snapshot::abc",
    }


def test_workspace_cockpit_study_item_carries_truth_snapshot_summary() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    item = module._study_item(
        progress_payload={
            "study_id": "003-dpcc",
            "truth_epoch": "truth-event-000004-live",
            "study_truth_snapshot": _truth_snapshot(),
            "supervision": {"active_run_id": "run-e52f5574"},
        },
        profile_ref="/tmp/profile.toml",
    )

    assert item["truth_epoch"] == "truth-event-000004-live"
    assert item["study_truth_snapshot"]["canonical_next_action"] == "supervise_runtime"
    assert item["study_truth_snapshot"]["package_state"]["authority_state"] == "provisionally_current_for_epoch"


def test_runtime_watch_managed_study_action_carries_truth_snapshot_summary() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch_parts.managed_wakeup")

    action = module._serialize_managed_study_action(
        {
            "study_id": "003-dpcc",
            "decision": "blocked",
            "reason": "study_completion_publishability_gate_blocked",
            "study_truth_snapshot": _truth_snapshot(),
        }
    )

    assert action["truth_epoch"] == "truth-event-000004-live"
    assert action["study_truth_snapshot"]["canonical_next_action"] == "supervise_runtime"
    assert action["study_truth_snapshot"]["allowed_controller_actions"] == [
        "read_runtime_status",
        "open_monitoring_entry",
    ]
