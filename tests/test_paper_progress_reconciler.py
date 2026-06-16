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
        "surface": "domain_route_owner_route",
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


def test_reconciler_records_dm002_opl_stage_attempt_admission_outbox_receipt(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_progress_reconciler")
    transition_refs = importlib.import_module("med_autoscience.controllers.paper_progress_transition_refs")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    route = _owner_route(
        study_id=study_id,
        owner="one-person-lab",
        reason="runtime_recovery_retry_budget_exhausted",
        action_type="request_opl_stage_attempt",
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
                "authority_snapshot": {
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
                "execution_id": "execution::dm002::request_opl_stage_attempt",
                "execution_status": "executed",
                "action_type": "request_opl_stage_attempt",
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
    assert decision["current_state"]["state"] == "opl_stage_attempt_admission_required"
    assert decision["decision"] == "opl_stage_attempt_admission"
    assert decision["apply_eligible"] is True
    assert decision["action_receipt"]["receipt_status"] == (
        "transition_request_pending_opl_runtime_required"
    )
    assert decision["action_receipt"]["refs_only"] is True
    assert decision["action_receipt"]["started_worker"] is False
    assert decision["action_receipt"]["worker_start_ref"] is None
    assert decision["action_receipt"]["transition_runtime_owner"] == "one-person-lab"
    assert transition_refs.read_transition_refs(study_root=profile.studies_root / study_id)


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
    assert decision["next_owner"] == "med-autoscience"
    assert decision["why_not_progressing"] == "owner_callable_surface_missing"
    assert decision["action_receipt"]["receipt_status"] == "dry_run_not_recorded"


def test_reconciler_repo_route_gap_uses_typed_blocker_not_controller_inspector(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_progress_reconciler")
    profile = make_profile(tmp_path)
    study_id = "004-route-gap"
    write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    scan = {
        "studies": [
            {
                "study_id": study_id,
                "quest_id": f"quest-{study_id}",
                "study_macro_state": {
                    "writer_state": "parked",
                    "user_next": "inspect",
                    "reason": "route_gap",
                    "details": {"package_delivered": False},
                },
                "interaction_arbitration": {
                    "classification": "blocked_controller_route",
                    "action": "inspect",
                    "requires_user_input": False,
                    "valid_blocking": True,
                    "next_owner": "MAS/controller",
                    "blocked_reason": "controller_route_gap",
                },
                "current_blockers": ["controller_route_gap"],
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
        generated_at="2026-06-16T00:00:00+00:00",
    )

    decision = receipt["decisions"][0]
    assert decision["decision"] == "repo_level_blocker"
    assert decision["desired_state"]["owner"] == "med-autoscience"
    assert decision["desired_state"]["action_type"] == "repo_route_typed_blocker_required"
    assert decision["callable_contract"]["callable_surface"] == "mas_domain_authority.typed_blocker.repo_route_gap"
    assert decision["action_receipt"]["receipt_status"] == "dry_run_not_recorded"
    assert "inspect_controller_route" not in str(decision)


def test_reconciler_does_not_record_worker_start_without_dispatch_execution(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_progress_reconciler")
    transition_refs = importlib.import_module("med_autoscience.controllers.paper_progress_transition_refs")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    route = _owner_route(
        study_id=study_id,
        owner="one-person-lab",
        reason="execution_owner_guard_supervisor_only",
        action_type="request_opl_stage_attempt",
    )
    scan = {
        "studies": [
            {
                "study_id": study_id,
                "quest_id": f"quest-{study_id}",
                "active_run_id": "run-dm003",
                "study_macro_state": {
                    "writer_state": "live",
                    "user_next": "watch",
                    "reason": "runtime",
                    "details": {"active_run_id": "run-dm003", "package_delivered": False},
                },
                "owner_route": route,
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
        apply=True,
        generated_at="2026-05-10T00:00:00+00:00",
    )

    decision = receipt["decisions"][0]
    assert decision["current_state"]["state"] == "opl_stage_attempt_admission_required"
    assert decision["decision"] == "opl_stage_attempt_admission"
    assert decision["apply_eligible"] is False
    assert decision["action_receipt"]["receipt_status"] == "not_executed"
    assert decision["action_receipt"]["reason"] == "owner_dispatch_not_executed"
    assert receipt["action_receipt_count"] == 0
    assert transition_refs.read_transition_refs(study_root=profile.studies_root / study_id) == []


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


def test_reconciler_prefers_runtime_liveness_owner_route_over_downstream_bundle_gate(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_progress_reconciler")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    route = _owner_route(
        study_id=study_id,
        owner="one-person-lab",
        reason="runtime_recovery_retry_budget_exhausted",
        action_type="request_opl_stage_attempt",
    )
    scan = {
        "studies": [
            {
                "study_id": study_id,
                "quest_id": f"quest-{study_id}",
                "active_run_id": None,
                "study_macro_state": {
                    "writer_state": "queued",
                    "user_next": "runtime_handoff",
                    "reason": "runtime",
                    "details": {"package_delivered": False},
                },
                "runtime_health_snapshot": {
                    "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
                    "worker_liveness_state": {"state": "not_ready", "worker_running": False},
                },
                "authority_snapshot": {
                    "dispatch_gate": {
                        "state": "blocked",
                        "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
                    }
                },
                "owner_route": route,
                "progress_freshness": {
                    "meaningful_artifact_delta_freshness": {"status": "missing"},
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
    assert decision["current_state"]["state"] == "opl_stage_attempt_admission_required"
    assert decision["current_state"]["actual_write_active"] is False
    assert decision["current_state"]["why_not_progressing"] == "runtime_recovery_retry_budget_exhausted"
    assert decision["why_not_progressing"] == "runtime_recovery_retry_budget_exhausted"
    assert decision["decision"] == "opl_stage_attempt_admission"


def test_reconciler_projects_route_back_checklist_and_runtime_closeout_only_stage_log(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_progress_reconciler")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    scan = {
        "studies": [
            {
                "study_id": study_id,
                "quest_id": f"quest-{study_id}",
                "domain_transition": {
                    "decision_type": "route_back_same_line",
                    "route_target": "write",
                    "owner": "write",
                    "next_work_unit": {
                        "unit_id": "medical_prose_currentness_recheck",
                        "required_output_surface": "paper/build/review_manuscript.md",
                    },
                    "evidence_refs": {
                        "publication_eval": "artifacts/publication_eval/latest.json",
                    },
                    "expected_repair_result": "paper-facing story delta or typed blocker",
                },
                "study_macro_state": {
                    "writer_state": "queued",
                    "user_next": "repair",
                    "reason": "quality",
                    "details": {"package_delivered": False},
                },
                "opl_current_control_state_handoff": {
                    "surface_kind": "opl_current_control_state_study_handoff",
                    "latest_terminal_stage_log": {
                        "status": "handoff_ready",
                        "action_type": "run_quality_repair_batch",
                        "paper_stage_log": {
                            "current_owner": "write",
                            "progress_delta_classification": "platform_repair",
                            "deliverable_progress_delta": {"count": 0, "token_usage_total": 0},
                            "paper_progress_delta": {"count": 0, "token_usage_total": 0},
                            "platform_repair_delta": {"count": 1, "token_usage_total": 101},
                            "changed_paper_surfaces": [],
                            "changed_stage_surfaces": ["artifacts/runtime/closeout.json"],
                            "remaining_blockers": {
                                "typed_blocker": "manuscript_story_surface_delta_missing",
                            },
                            "evidence_refs": ["artifacts/controller/quality_repair_batch/latest.json"],
                        },
                    },
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

    state = receipt["decisions"][0]["current_state"]
    checklist = state["route_back_checklist"]
    closeout = state["stage_closeout_progress"]
    assert state["state"] == "awaiting_callable_owner"
    assert checklist["blockers"] == ["manuscript_story_surface_delta_missing"]
    assert checklist["route_target"] == "write"
    assert checklist["next_work_units"] == [
        {
            "unit_id": "medical_prose_currentness_recheck",
            "required_output_surface": "paper/build/review_manuscript.md",
        }
    ]
    assert checklist["evidence_refs"] == [
        "artifacts/controller/quality_repair_batch/latest.json",
        "artifacts/publication_eval/latest.json",
    ]
    assert checklist["expected_repair_result"] == "paper-facing story delta or typed blocker"
    assert closeout["classification"] == "platform_repair"
    assert closeout["runtime_closeout_only"] is True
    assert closeout["paper_facing_delta_present"] is False
    assert closeout["changed_stage_surfaces"] == ["artifacts/runtime/closeout.json"]


def test_reconciler_accepts_scan_domain_routes_artifact_delta_projection(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_progress_reconciler")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    scan = {
        "studies": [
            {
                "study_id": study_id,
                "quest_id": f"quest-{study_id}",
                "active_run_id": "run-dm003",
                "owner_route": {
                    "next_owner": "external_supervisor",
                    "owner_reason": "execution_owner_guard_supervisor_only",
                    "active_run_id": "run-dm003",
                    "source_refs": {
                        "study_macro_state": {
                            "writer_state": "live",
                            "user_next": "watch",
                            "reason": "runtime",
                        }
                    },
                },
                "execution_owner_guard": {"supervisor_only": True},
                "meaningful_artifact_delta": True,
                "artifact_delta": {
                    "status": "fresh",
                    "latest_meaningful_delta_at": "2026-05-12T23:22:36.498447+00:00",
                    "source": "gate_clearing_batch",
                },
                "progress_freshness": {
                    "meaningful_artifact_delta_freshness": {"status": "missing"},
                },
                "publication_supervisor_state": {
                    "bundle_tasks_downstream_only": True,
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
        generated_at="2026-05-12T23:23:00+00:00",
    )

    decision = receipt["decisions"][0]
    assert decision["current_state"]["state"] == "downstream_only"
    assert decision["current_state"]["actual_write_active"] is True
    assert decision["current_state"]["meaningful_artifact_delta"] is True
    assert decision["decision"] == "monitor_live_quality_repair"
