from __future__ import annotations

import importlib
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _owner_route(
    *,
    study_id: str,
    owner: str,
    reason: str,
    action_type: str,
    fingerprint: str = "work-unit::001",
) -> dict[str, object]:
    return {
        "surface": "runtime_supervisor_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": f"quest-{study_id}",
        "truth_epoch": f"truth::{study_id}",
        "runtime_health_epoch": f"runtime::{study_id}",
        "work_unit_fingerprint": fingerprint,
        "failure_signature": reason,
        "trace_id": f"trace::{study_id}",
        "route_epoch": f"truth::{study_id}",
        "source_fingerprint": f"source::{study_id}::{fingerprint}",
        "current_owner": "mas_controller",
        "next_owner": owner,
        "owner_reason": reason,
        "active_run_id": None,
        "allowed_actions": [action_type],
        "blocked_actions": [],
        "idempotency_key": f"owner-route::{study_id}::{fingerprint}",
    }


def test_reconciler_records_dm002_controller_redrive_outbox_receipt(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_progress_reconciler")
    outbox = importlib.import_module("med_autoscience.controllers.paper_work_unit_outbox")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    route = _owner_route(
        study_id=study_id,
        owner="MAS/controller",
        reason="runtime_recovery_retry_budget_exhausted",
        action_type="runtime_platform_repair",
    )
    scan = {
        "studies": [
            {
                "study_id": study_id,
                "quest_id": f"quest-{study_id}",
                "study_macro_state": {
                    "writer_state": "live",
                    "user_next": "watch",
                    "reason": "runtime",
                    "details": {"active_run_id": "run-dm002", "package_delivered": False},
                },
                "runtime_health_snapshot": {
                    "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
                    "worker_liveness_state": {"state": "activity_timeout", "worker_running": True},
                },
                "control_plane_snapshot": {
                    "dispatch_gate": {
                        "state": "blocked",
                        "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
                    }
                },
                "owner_route": route,
                "progress_freshness": {
                    "meaningful_artifact_delta_freshness": {"status": "missing"},
                },
            }
        ]
    }
    executed = {
        "executions": [
            {
                "study_id": study_id,
                "quest_id": f"quest-{study_id}",
                "execution_id": "execution::dm002::runtime_platform_repair",
                "execution_status": "executed",
                "action_type": "runtime_platform_repair",
                "owner_route": route,
                "will_start_llm": True,
            }
        ]
    }

    receipt = module.build_paper_progress_reconcile_receipt(
        profile=profile,
        requested_study_ids=(study_id,),
        resolved_study_ids=(study_id,),
        before_scan=scan,
        consumed={},
        executed=executed,
        after_scan=scan,
        apply=True,
        generated_at="2026-05-10T00:00:00+00:00",
    )

    decision = receipt["decisions"][0]
    assert decision["current_state"]["state"] == "awaiting_controller_redrive"
    assert decision["decision"] == "controller_redrive"
    assert decision["apply_eligible"] is True
    assert decision["action_receipt"]["receipt_status"] == "started"
    assert decision["action_receipt"]["worker_start_ref"] == "execution::dm002::runtime_platform_repair"
    assert outbox.worker_starts(study_root=profile.studies_root / study_id)


def test_reconciler_routes_dm003_missing_callable_to_controller_registry_repair(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_progress_reconciler")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    scan = {
        "studies": [
            {
                "study_id": study_id,
                "quest_id": f"quest-{study_id}",
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
                    "meaningful_artifact_delta_freshness": {"status": "missing"},
                },
            }
        ]
    }

    receipt = module.build_paper_progress_reconcile_receipt(
        profile=profile,
        requested_study_ids=(study_id,),
        resolved_study_ids=(study_id,),
        before_scan=scan,
        consumed={},
        executed={},
        after_scan=scan,
        apply=False,
        generated_at="2026-05-10T00:00:00+00:00",
    )

    decision = receipt["decisions"][0]
    assert decision["current_state"]["state"] == "awaiting_callable_owner"
    assert decision["current_state"]["requires_user_input"] is False
    assert decision["decision"] == "registry_repair"
    assert decision["next_owner"] == "MAS/controller"
    assert decision["why_not_progressing"] == "owner_callable_surface_missing"
    assert decision["action_receipt"]["receipt_status"] == "dry_run_not_recorded"


def test_reconciler_keeps_obesity_delivery_missing_downstream_only(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_progress_reconciler")
    profile = make_profile(tmp_path)
    study_id = "obesity_multicenter_phenotype_atlas"
    write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    scan = {
        "studies": [
            {
                "study_id": study_id,
                "quest_id": f"quest-{study_id}",
                "active_run_id": "run-obesity",
                "study_macro_state": {
                    "writer_state": "live",
                    "user_next": "watch",
                    "reason": "runtime",
                    "details": {"active_run_id": "run-obesity", "package_delivered": False},
                },
                "owner_route": {
                    "next_owner": "external_supervisor",
                    "owner_reason": "publishability_gate_blocked",
                },
                "execution_owner_guard": {"supervisor_only": True},
                "progress_freshness": {
                    "meaningful_artifact_delta_freshness": {
                        "status": "fresh",
                        "latest_progress_at": "2026-05-10T08:15:00+00:00",
                    },
                },
                "publication_supervisor_state": {
                    "bundle_tasks_downstream_only": True,
                    "deferred_downstream_actions": ["delivery_sync"],
                },
            }
        ]
    }

    receipt = module.build_paper_progress_reconcile_receipt(
        profile=profile,
        requested_study_ids=(study_id,),
        resolved_study_ids=(study_id,),
        before_scan=scan,
        consumed={},
        executed={},
        after_scan=scan,
        apply=False,
        generated_at="2026-05-10T00:00:00+00:00",
    )

    decision = receipt["decisions"][0]
    assert decision["current_state"]["state"] == "downstream_only"
    assert decision["current_state"]["actual_write_active"] is True
    assert decision["current_state"]["meaningful_artifact_delta"] is True
    assert decision["current_state"]["package_delivered"] is False
    assert decision["next_owner"] == "supervisor_only/live_quality_repair"
    assert decision["decision"] == "monitor_live_quality_repair"
