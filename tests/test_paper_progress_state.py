from __future__ import annotations

import importlib


PUBLIC_STATES = {
    "progressing",
    "opl_stage_attempt_admission_required",
    "blocked_controller_route",
    "awaiting_callable_owner",
    "awaiting_human",
    "downstream_only",
    "terminal_delivered",
}


def _module():
    return importlib.import_module("med_autoscience.controllers.paper_progress_state")


def test_dm002_retry_budget_opl_route_requires_stage_attempt_admission() -> None:
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
            "authority_snapshot": {
                "dispatch_gate": {
                    "state": "blocked",
                    "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
                }
            },
            "owner_route": {
                "next_owner": "one-person-lab",
                "allowed_actions": ["request_opl_stage_attempt"],
                "owner_reason": "runtime_controller_redrive_required",
            },
            "progress_freshness": {
                "meaningful_artifact_delta_freshness": {"status": "missing"},
            },
            "runtime_reconcile_trigger": {
                "safe_to_request": True,
                "recommended_command": (
                    "uv run python -m med_autoscience.cli owner-route-reconcile "
                    "--profile /tmp/profile.json --studies 002-dm-china-us-mortality-attribution --dry-run"
                ),
            },
        }
    )

    assert state["state"] == "opl_stage_attempt_admission_required"
    assert state["state"] in PUBLIC_STATES
    assert state["actual_write_active"] is False
    assert state["package_delivered"] is False
    assert state["meaningful_artifact_delta"] is False
    assert state["next_owner"] == "one-person-lab"
    assert state["why_not_progressing"] == "runtime_recovery_retry_budget_exhausted"
    assert state["safe_reconcile_command"] is None


def test_dm002_retry_budget_with_blocked_route_surfaces_controller_route_blocker() -> None:
    state = _module().build_paper_progress_state(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "study_macro_state": {
                "writer_state": "parked",
                "user_next": "inspect",
                "reason": "unknown",
                "details": {"package_delivered": False},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
            "authority_snapshot": {
                "dispatch_gate": {
                    "state": "blocked",
                    "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
                },
                "route_authorization": {
                    "authorized": False,
                    "paper_write_allowed": True,
                    "bundle_build_allowed": True,
                    "runtime_recovery_allowed": False,
                },
            },
            "interaction_arbitration": {
                "requires_user_input": False,
                "next_owner": "MAS/controller route authorization owner for bundle_build_allowed on submission_minimal_refresh",
                "blocked_reason": (
                    "authority_route_blocked_bundle_build: dispatch_gate_blocked; "
                    "execution_owner_guard.supervisor_only; non_supervisor_gate=bundle_build_allowed_false"
                ),
            },
        }
    )

    assert state["state"] == "blocked_controller_route"
    assert state["next_owner"] == "MAS/controller"
    assert state["why_not_progressing"].startswith("authority_route_blocked_bundle_build")


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
                    "uv run python -m med_autoscience.cli owner-route-reconcile "
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
    assert state["safe_reconcile_command"] is None


def test_current_delivery_inspection_counts_as_package_delivered() -> None:
    state = _module().build_paper_progress_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "study_macro_state": {
                "writer_state": "parked",
                "user_next": "inspect",
                "reason": "unknown",
                "details": {"package_delivered": False},
            },
            "delivery_inspection": {
                "status": "current",
                "freshness": {
                    "delivery_status": "current",
                    "gate_freshness_handshake": {"status": "current"},
                },
            },
        }
    )

    assert state["state"] == "terminal_delivered"
    assert state["package_delivered"] is True
    assert state["why_not_progressing"] == "package_delivered"


def test_current_delivery_does_not_terminal_deliver_reactivated_same_line_repair() -> None:
    state = _module().build_paper_progress_state(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "study_macro_state": {
                "writer_state": "parked",
                "user_next": "inspect",
                "reason": "unknown",
                "details": {"paper_stage": "analysis-campaign"},
            },
            "delivery_inspection": {
                "status": "current",
                "freshness": {
                    "delivery_status": "current",
                    "gate_freshness_handshake": {"status": "current"},
                },
            },
            "quality_closure_truth": {
                "state": "quality_repair_required",
                "current_required_action": "return_to_analysis_campaign",
            },
            "study_truth_snapshot": {
                "canonical_next_action": "resume_same_study_line",
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
            "authority_snapshot": {
                "control_state": "blocked_runtime_escalation",
                "canonical_next_action": "resume_same_study_line",
                "dispatch_gate": {
                    "state": "blocked",
                    "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
                },
                "route_authorization": {
                    "authorized": False,
                    "paper_write_allowed": True,
                    "bundle_build_allowed": True,
                    "runtime_recovery_allowed": False,
                },
            },
            "interaction_arbitration": {
                "requires_user_input": False,
                "next_owner": "MAS/controller",
                "blocked_reason": (
                    "authority_route_blocked: bundle_build dispatch_gate_blocked "
                    "during submission_minimal_refresh"
                ),
            },
        }
    )

    assert state["state"] == "blocked_controller_route"
    assert state["package_delivered"] is True
    assert state["next_owner"] == "MAS/controller"
    assert state["why_not_progressing"].startswith("authority_route_blocked")


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
            "authority_snapshot": {
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


def test_obesity_supervisor_only_live_delta_projects_precise_owner() -> None:
    state = _module().build_paper_progress_state(
        {
            "study_id": "obesity_multicenter_phenotype_atlas",
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
            "execution_owner_guard": {"supervisor_only": True},
            "publication_supervisor_state": {"bundle_tasks_downstream_only": True},
            "opl_current_control_state_handoff": {
                "next_owner": "external_supervisor",
                "external_supervisor_required": False,
            },
        }
    )

    assert state["state"] == "downstream_only"
    assert state["actual_write_active"] is True
    assert state["meaningful_artifact_delta"] is True
    assert state["next_owner"] == "supervisor_only/live_quality_repair"


def test_obesity_supervisor_only_live_delta_reads_control_plane_truth() -> None:
    state = _module().build_paper_progress_state(
        {
            "study_id": "obesity_multicenter_phenotype_atlas",
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
            "study_truth_snapshot": {
                "blocking_reasons": [
                    "execution_owner_guard.supervisor_only",
                    "publication_supervisor_state.bundle_tasks_downstream_only",
                ]
            },
            "authority_snapshot": {
                "dispatch_gate": {
                    "blocking_reasons": [
                        "execution_owner_guard.supervisor_only",
                        "publication_supervisor_state.bundle_tasks_downstream_only",
                    ]
                }
            },
            "opl_current_control_state_handoff": {
                "next_owner": "external_supervisor",
                "external_supervisor_required": False,
            },
        }
    )

    assert state["state"] == "downstream_only"
    assert state["actual_write_active"] is True
    assert state["meaningful_artifact_delta"] is True
    assert state["next_owner"] == "supervisor_only/live_quality_repair"


def test_dm002_live_worker_without_paper_facing_delta_or_typed_blocker_is_not_progressing() -> None:
    state = _module().build_paper_progress_state(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "active_run_id": "run-dm002",
            "study_macro_state": {
                "writer_state": "live",
                "user_next": "watch",
                "reason": "runtime",
                "details": {"active_run_id": "run-dm002", "package_delivered": False},
            },
            "progress_freshness": {
                "meaningful_artifact_delta_freshness": {
                    "status": "fresh",
                    "latest_progress_at": "2026-05-23T09:00:00+00:00",
                    "surface_kind": "runtime_log_delta",
                    "changed_refs": ["artifacts/runtime/logs/latest.log"],
                }
            },
            "runtime_health_snapshot": {
                "worker_liveness_state": {
                    "state": "running",
                    "active_run_id": "run-dm002",
                    "worker_running": True,
                }
            },
            "owner_route": {
                "next_owner": "write",
                "allowed_actions": ["run_quality_repair_batch"],
            },
        }
    )

    assert state["state"] == "awaiting_callable_owner"
    assert state["actual_write_active"] is False
    assert state["meaningful_artifact_delta"] is False
    assert state["paper_facing_progress_slo"]["visible_as_progressing"] is False
    assert state["paper_facing_progress_slo"]["missing_required_delta_classes"] == [
        "canonical_manuscript",
        "figure_table",
        "claim_evidence",
        "review_ledger",
        "gate_replay",
        "ai_reviewer_request",
        "typed_blocker",
    ]
    assert state["why_not_progressing"] == "paper_facing_progress_delta_or_typed_blocker_missing"


def test_dm003_live_worker_with_ai_reviewer_request_delta_is_progressing() -> None:
    state = _module().build_paper_progress_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "active_run_id": "run-dm003",
            "study_macro_state": {
                "writer_state": "live",
                "user_next": "watch",
                "reason": "runtime",
                "details": {"active_run_id": "run-dm003", "package_delivered": False},
            },
            "progress_freshness": {
                "meaningful_artifact_delta_freshness": {
                    "status": "fresh",
                    "latest_progress_at": "2026-05-23T09:05:00+00:00",
                    "changed_refs": [
                        "artifacts/supervision/requests/ai_reviewer/latest.json"
                    ],
                }
            },
        }
    )

    assert state["state"] == "progressing"
    assert state["actual_write_active"] is True
    assert state["meaningful_artifact_delta"] is True
    assert state["paper_facing_progress_slo"]["satisfied_delta_classes"] == [
        "ai_reviewer_request"
    ]
    assert state["why_not_progressing"] is None


def test_dm003_opl_live_provider_attempt_with_paper_delta_is_progressing() -> None:
    state = _module().build_paper_progress_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "study_macro_state": {
                "writer_state": "queued",
                "user_next": "repair",
                "reason": "quality",
                "details": {"package_delivered": False},
            },
            "runtime_liveness_audit": {
                "active_stage_attempt_id": "sat-live",
                "running_provider_attempt": True,
                "runtime_health": {"provider_status": "running"},
            },
            "opl_current_control_state_handoff": {
                "active_run_id": "opl-stage-attempt://sat-live",
                "active_stage_attempt_id": "sat-live",
                "running_provider_attempt": True,
                "runtime_health": {"health_status": "running"},
            },
            "progress_freshness": {
                "meaningful_artifact_delta_freshness": {
                    "status": "fresh",
                    "latest_progress_at": "2026-05-30T03:51:42+00:00",
                    "changed_refs": [
                        "paper/evidence_ledger.json",
                        "paper/claim_evidence_map.json",
                        "paper/review/review_ledger.json",
                    ],
                },
            },
            "publication_supervisor_state": {"bundle_tasks_downstream_only": True},
            "owner_route": {"next_owner": "ai_reviewer"},
        }
    )

    assert state["state"] == "progressing"
    assert state["actual_write_active"] is True
    assert state["meaningful_artifact_delta"] is True
    assert state["paper_facing_progress_slo"]["visible_as_progressing"] is True
    assert state["paper_facing_progress_slo"]["satisfied_delta_classes"] == [
        "claim_evidence",
        "review_ledger",
    ]
    assert state["why_not_progressing"] is None


def test_current_work_unit_typed_blocker_suppresses_stale_provider_attempt_write_activity() -> None:
    state = _module().build_paper_progress_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "study_macro_state": {
                "writer_state": "live",
                "user_next": "watch",
                "reason": "runtime",
                "details": {"active_run_id": "opl-stage-attempt://sat_stale_or_superseded"},
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "owner": "MedAutoScience",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "gate-replay-route-back::write::publication-blockers::0915410f804b3697",
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "stage_packet_not_selected_by_domain_owner_action_dispatch",
                    },
                },
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_type": "stage_packet_not_selected_by_domain_owner_action_dispatch",
                },
            },
            "opl_current_control_state_handoff": {
                "active_run_id": "opl-stage-attempt://sat_stale_or_superseded",
                "active_stage_attempt_id": "sat_stale_or_superseded",
                "running_provider_attempt": True,
                "runtime_health": {
                    "health_status": "running",
                    "runtime_liveness_status": "live",
                },
            },
            "latest_terminal_stage_log": {
                "paper_stage_log": {
                    "changed_stage_surfaces": [
                        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/consumer/default_executor_execution/sat_590.closeout.json"
                    ],
                    "changed_paper_surfaces": [],
                }
            },
        }
    )

    assert state["actual_write_active"] is False
    assert state["state"] != "progressing"
    assert state["why_not_progressing"] == "paper_facing_progress_delta_or_typed_blocker_missing"


def test_stale_paper_delta_refs_do_not_count_as_active_progress() -> None:
    state = _module().build_paper_progress_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "study_macro_state": {
                "writer_state": "queued",
                "user_next": "repair",
                "reason": "quality",
                "details": {"package_delivered": False},
            },
            "progress_freshness": {
                "meaningful_artifact_delta_freshness": {
                    "status": "stale",
                    "latest_progress_at": "2026-06-07T01:53:49+00:00",
                    "changed_refs": [
                        (
                            "artifacts/stage_outputs/_body_authority/paper_authority_cutover/"
                            "current_body/paper/figures/generated/F1_cohort_flow.png"
                        ),
                    ],
                },
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "next_owner": "08-publication_package_handoff",
                "allowed_actions": ["materialize_stage_artifact_delta"],
            },
        }
    )

    assert state["actual_write_active"] is False
    assert state["meaningful_artifact_delta"] is False
    assert state["paper_facing_progress_slo"]["visible_as_progressing"] is False
    assert state["paper_facing_progress_slo"]["changed_refs"] == []


def test_body_authority_stage_output_mirror_does_not_count_as_current_paper_progress() -> None:
    state = _module().build_paper_progress_state(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "study_macro_state": {
                "writer_state": "queued",
                "user_next": "runtime_handoff",
                "reason": "runtime",
                "details": {"package_delivered": False},
            },
            "progress_freshness": {
                "meaningful_artifact_delta_freshness": {
                    "status": "fresh",
                    "latest_progress_at": "2026-06-07T18:10:22+00:00",
                    "latest_progress_source": "gate_clearing_batch",
                    "changed_refs": [
                        (
                            "artifacts/stage_outputs/_body_authority/paper_authority_cutover/"
                            "current_body/paper/figures/generated/F1_cohort_flow.png"
                        ),
                        (
                            "artifacts/stage_outputs/_body_authority/paper_authority_cutover/"
                            "current_body/paper/tables/table_catalog.json"
                        ),
                    ],
                }
            },
            "deliverable_progress_delta": {"count": 0, "token_usage_total": 0, "sources": []},
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_id": "medical_paper_readiness_missing",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                },
            },
        }
    )

    assert state["actual_write_active"] is False
    assert state["meaningful_artifact_delta"] is False
    assert state["paper_facing_progress_slo"]["visible_as_progressing"] is False
    assert state["paper_facing_progress_slo"]["changed_refs"] == []


def test_paper_facing_stage_log_refs_count_as_meaningful_delta() -> None:
    state = _module().build_paper_progress_state(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "study_macro_state": {
                "writer_state": "queued",
                "user_next": "repair",
                "reason": "quality",
                "details": {"package_delivered": False},
            },
            "opl_current_control_state_handoff": {
                "active_run_id": "opl-stage-attempt://sat-dm002",
                "active_stage_attempt_id": "sat-dm002",
                "running_provider_attempt": True,
                "runtime_health": {"health_status": "running"},
            },
            "latest_terminal_stage_log": {
                "paper_stage_log": {
                    "changed_paper_surfaces": [
                        "studies/002-dm-china-us-mortality-attribution/paper/claim_evidence_map.json",
                        "studies/002-dm-china-us-mortality-attribution/paper/evidence_ledger.json",
                        "studies/002-dm-china-us-mortality-attribution/paper/review/review_ledger.json",
                    ],
                    "changed_stage_surfaces": [],
                }
            },
            "owner_route": {"next_owner": "write"},
        }
    )

    assert state["meaningful_artifact_delta"] is True
    assert state["paper_facing_progress_slo"]["visible_as_progressing"] is True
    assert state["paper_facing_progress_slo"]["satisfied_delta_classes"] == [
        "claim_evidence",
        "review_ledger",
    ]
    assert state["why_not_progressing"] is None


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
