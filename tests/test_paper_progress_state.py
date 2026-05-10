from __future__ import annotations

import importlib


PUBLIC_STATES = {
    "progressing",
    "awaiting_controller_redrive",
    "blocked_controller_route",
    "awaiting_callable_owner",
    "awaiting_human",
    "downstream_only",
    "terminal_delivered",
}


def _module():
    return importlib.import_module("med_autoscience.controllers.paper_progress_state")


def test_dm002_retry_budget_controller_route_awaits_controller_redrive() -> None:
    state = _module().build_paper_progress_state(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "study_macro_state": {
                "writer_state": "live",
                "user_next": "watch",
                "reason": "runtime",
                "details": {"active_run_id": "run-dm002"},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "recover_runtime",
                "retry_budget_remaining": 0,
                "blocking_reasons": [
                    "runtime_recovery_retry_budget_exhausted",
                    "live_worker_meaningful_artifact_delta_timeout",
                ],
                "worker_liveness_state": {
                    "state": "activity_timeout",
                    "active_run_id": "run-dm002",
                    "worker_running": True,
                },
            },
            "control_plane_snapshot": {
                "dispatch_gate": {
                    "state": "blocked",
                    "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
                }
            },
            "owner_route": {
                "next_owner": "MAS/controller",
                "allowed_actions": ["runtime-redrive"],
                "owner_reason": "runtime_controller_redrive_required",
            },
            "progress_freshness": {
                "meaningful_artifact_delta_freshness": {"status": "missing"},
            },
            "runtime_reconcile_trigger": {
                "safe_to_request": True,
                "recommended_command": (
                    "uv run python -m med_autoscience.cli runtime-supervisor-reconcile "
                    "--profile /tmp/profile.json --studies 002-dm-china-us-mortality-attribution --dry-run"
                ),
            },
        }
    )

    assert state["state"] == "awaiting_controller_redrive"
    assert state["state"] in PUBLIC_STATES
    assert state["actual_write_active"] is False
    assert state["package_delivered"] is False
    assert state["meaningful_artifact_delta"] is False
    assert state["next_owner"] == "MAS/controller"
    assert state["why_not_progressing"] == "runtime_recovery_retry_budget_exhausted"
    assert state["safe_reconcile_command"].endswith(
        "--studies 002-dm-china-us-mortality-attribution --dry-run"
    )


def test_dm003_missing_callable_owner_without_user_input_awaits_callable_owner() -> None:
    state = _module().build_paper_progress_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "study_macro_state": {
                "writer_state": "parked",
                "user_next": "inspect",
                "reason": "blocked_turn_closeout_waiting_for_owner",
                "details": {"package_delivered": False},
            },
            "interaction_arbitration": {
                "classification": "blocked_closeout_owner_redrive",
                "action": "resume",
                "requires_user_input": False,
                "valid_blocking": False,
                "next_owner": "unknown_external_owner",
                "blocked_reason": "owner_callable_surface_missing",
            },
            "progress_freshness": {
                "meaningful_artifact_delta_freshness": {
                    "status": "missing",
                    "summary": "no paper artifact delta observed",
                }
            },
            "runtime_reconcile_trigger": {
                "safe_to_request": True,
                "recommended_command": (
                    "uv run python -m med_autoscience.cli runtime-supervisor-reconcile "
                    "--profile /tmp/profile.json --studies 003-dpcc-primary-care-phenotype-treatment-gap --dry-run"
                ),
            },
        }
    )

    assert state["state"] == "awaiting_callable_owner"
    assert state["state"] in PUBLIC_STATES
    assert state["actual_write_active"] is False
    assert state["package_delivered"] is False
    assert state["meaningful_artifact_delta"] is False
    assert state["next_owner"] == "unknown_external_owner"
    assert state["requires_user_input"] is False
    assert state["why_not_progressing"] == "owner_callable_surface_missing"
    assert state["safe_reconcile_command"].endswith(
        "--studies 003-dpcc-primary-care-phenotype-treatment-gap --dry-run"
    )


def test_obesity_live_artifact_delta_missing_downstream_delivery_is_downstream_only() -> None:
    state = _module().build_paper_progress_state(
        {
            "study_id": "obesity-treatment-gap",
            "active_run_id": "run-obesity",
            "study_macro_state": {
                "writer_state": "live",
                "user_next": "watch",
                "reason": "runtime",
                "details": {"active_run_id": "run-obesity", "package_delivered": False},
            },
            "progress_freshness": {
                "meaningful_artifact_delta_freshness": {
                    "status": "fresh",
                    "latest_progress_at": "2026-05-10T08:15:00+00:00",
                }
            },
            "publication_supervisor_state": {
                "bundle_tasks_downstream_only": True,
                "deferred_downstream_actions": ["delivery_sync"],
            },
            "control_plane_snapshot": {
                "blocking_reasons": ["publication_supervisor_state.bundle_tasks_downstream_only"],
                "route_authorization": {"bundle_build_allowed": False},
            },
            "owner_route": {
                "next_owner": "delivery_sync",
                "allowed_actions": ["delivery_sync"],
            },
        }
    )

    assert state["state"] == "downstream_only"
    assert state["state"] in PUBLIC_STATES
    assert state["actual_write_active"] is True
    assert state["package_delivered"] is False
    assert state["meaningful_artifact_delta"] is True
    assert state["next_owner"] == "delivery_sync"
    assert state["why_not_progressing"] == "publication_supervisor_state.bundle_tasks_downstream_only"
    assert state["safe_reconcile_command"] is None


def test_user_visible_projection_embeds_paper_progress_state() -> None:
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")

    projection = study_progress.build_user_visible_projection(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "study_macro_state": {
                "writer_state": "parked",
                "user_next": "inspect",
                "reason": "blocked_turn_closeout_waiting_for_owner",
                "details": {"package_delivered": False},
            },
            "interaction_arbitration": {
                "requires_user_input": False,
                "next_owner": "unknown_external_owner",
                "blocked_reason": "owner_callable_surface_missing",
            },
        }
    )

    assert projection["paper_progress_state"]["state"] == "awaiting_callable_owner"
    assert projection["paper_progress_state"]["state"] in PUBLIC_STATES
    assert projection["paper_progress_state"]["requires_user_input"] is False
