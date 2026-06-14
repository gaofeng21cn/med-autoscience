from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_domain_health_diagnostic_same_tick_treats_blocked_materialized_dispatch_as_blocker(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "001-risk"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})

    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(
        module.owner_route_reconcile,
        "scan_domain_routes",
        lambda **kwargs: {
            "surface": "portable_owner_route_reconcile",
            "action_queue": [{"study_id": study_id, "action_type": "return_to_ai_reviewer_workflow"}],
        },
    )
    monkeypatch.setattr(
        module.domain_action_request_materializer,
        "materialize_domain_action_requests",
        lambda **kwargs: {
            "surface": "domain_action_request_materializer",
            "request_task_count": 1,
            "default_executor_dispatch_count": 1,
            "ready_default_executor_dispatch_count": 0,
            "blocked_default_executor_dispatch_count": 1,
            "default_executor_dispatches": [
                {
                    "study_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "dispatch_status": "blocked",
                    "blocked_reason": "owner_route_currentness_basis_missing",
                    "next_executable_owner": "ai_reviewer",
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        lambda **kwargs: {
            "surface": "domain_owner_action_dispatch",
            "execution_count": 0,
            "executed_count": 0,
            "blocked_count": 0,
            "repeat_suppressed_count": 0,
            "codex_dispatch_count": 0,
            "executions": [],
        },
    )

    supervisor_tick = module._run_developer_supervisor_same_tick(profile=profile, max_passes=3)

    assert supervisor_tick["pass_count"] == 1
    assert supervisor_tick["stop_reason"] == "typed_blocker_or_dispatch_blocker_observed"
    delta = supervisor_tick["iterations"][0]["progress_first_delta"]
    assert delta["default_executor_dispatch_count"] == 0
    assert delta["default_executor_dispatch_total_count"] == 1
    assert delta["blocked_default_executor_dispatch_count"] == 1
    diagnostic = supervisor_tick["progress_first_terminal_diagnostic"]
    assert diagnostic["same_tick_terminal_projection"] == {
        "terminal_state": "stable_typed_blocker_observed",
        "owner_delta_produced": False,
        "provider_attempt_running": False,
        "stable_typed_blocker_observed": True,
        "provider_handoff_written": False,
    }
    assert diagnostic["requires_dispatch_blocker_resolution"] is True
    assert diagnostic["dispatch_blocker_summary"] == {
        "blocked_default_executor_dispatch_count": 1,
        "dispatch_blocked_count": 0,
        "blocked_reasons": ["owner_route_currentness_basis_missing"],
        "blocked_actions": ["return_to_ai_reviewer_workflow"],
    }
    assert diagnostic["next_forced_delta"]["required_delta_kind"] == (
        "dispatch_blocker_resolution_or_owner_route_currentness_delta"
    )
    assert "repeat_read_model_reconcile_without_owner_delta" in diagnostic["forbidden_next_actions"]


def test_domain_health_diagnostic_dry_run_includes_recovery_materialization_preview(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    materialize_calls: list[dict[str, object]] = []

    monkeypatch.setattr(
        module,
        "_run_domain_health_diagnostic_for_runtime_impl",
        lambda **kwargs: {
            "surface": "domain_health_diagnostic",
            "action_class": "observe_only",
            "scanned_at": "2026-06-14T00:00:00+00:00",
            "paper_recovery_states": {
                study_id: {
                    "phase": "owner_action_ready",
                    "next_safe_action": {"kind": "run_mas_owner_callable"},
                    "supervisor_decision": {"decision": "materialize_recovery_action"},
                }
            },
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "reason": "quest_waiting_for_user",
                    "paper_recovery_state": {
                        "phase": "owner_action_ready",
                        "next_safe_action": {"kind": "run_mas_owner_callable"},
                        "supervisor_decision": {"decision": "materialize_recovery_action"},
                    },
                }
            ],
        },
    )

    def fake_materialize_domain_action_requests(**kwargs) -> dict[str, object]:
        materialize_calls.append(kwargs)
        return {
            "surface": "domain_action_request_materializer",
            "dry_run": True,
            "request_task_count": 1,
            "default_executor_dispatch_count": 1,
            "ready_default_executor_dispatch_count": 1,
            "blocked_default_executor_dispatch_count": 0,
            "default_executor_dispatches": [
                {
                    "study_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "dispatch_status": "dry_run",
                }
            ],
        }

    monkeypatch.setattr(
        module.domain_action_request_materializer,
        "materialize_domain_action_requests",
        fake_materialize_domain_action_requests,
    )
    monkeypatch.setattr(
        module,
        "_materialize_report_provider_admission_current_control_state",
        lambda **kwargs: None,
    )

    report = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        apply=False,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
    )

    assert len(materialize_calls) == 1
    assert materialize_calls[0]["apply"] is False
    assert materialize_calls[0]["mode"] == "developer_apply_safe"
    assert materialize_calls[0]["study_ids"] == (study_id,)
    assert report["domain_action_request_materialization_preview"]["request_task_count"] == 1
    assert report["domain_action_request_materialization_preview"]["default_executor_dispatch_count"] == 1
    assert report["materialization_preview_request_task_count"] == 1
    assert report["materialization_preview_default_executor_dispatch_count"] == 1
    assert report["materialization_preview_ready_default_executor_dispatch_count"] == 1
    action_preview = report["managed_study_actions"][0]["domain_action_request_materialization_preview"]
    assert action_preview["study_id"] == study_id
    assert action_preview["request_task_count"] == 0
    assert action_preview["default_executor_dispatch_count"] == 1
    assert action_preview["ready_default_executor_dispatch_count"] == 1
    assert action_preview["default_executor_dispatches"][0]["action_type"] == (
        "run_quality_repair_batch"
    )
    assert report["action_class"] == "observe_only"


def test_domain_health_diagnostic_dry_run_includes_owner_resolution_preview(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    profiles = importlib.import_module("med_autoscience.profiles")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    profile = profiles.WorkspaceProfile(**{**profile.__dict__, "profile_ref": profile_ref})
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    fingerprint = "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    current_work_unit = {
        "surface_kind": "current_work_unit",
        "status": "typed_blocker",
        "study_id": study_id,
        "quest_id": study_id,
        "owner": "one-person-lab",
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "state": {
            "state_kind": "typed_blocker",
            "typed_blocker": {
                "blocker_id": "anti_loop_budget_exhausted",
                "blocker_type": "anti_loop_budget_exhausted",
                "owner": "one-person-lab",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "source_ref": (
                    "artifacts/supervision/consumer/default_executor_execution/"
                    "sat_67e10efde628859185249aa0.closeout.json"
                ),
            },
        },
    }
    recovery_state = {
        "surface_kind": "paper_recovery_state",
        "phase": "owner_action_ready",
        "current_authority": {
            "owner": "one-person-lab",
            "obligation": {
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "one-person-lab",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "blocker_type": "anti_loop_budget_exhausted",
            },
        },
        "next_safe_action": {
            "kind": "materialize_successor_owner_gate",
            "owner": "one-person-lab",
            "provider_admission_allowed": False,
            "required_input": (
                "publishability_repair_sprint_or_single_typed_blocker_or_human_or_operator_gate"
            ),
            "successor_owner_gate": {
                "owner": "one-person-lab",
                "required_input": (
                    "publishability_repair_sprint_or_single_typed_blocker_or_human_or_operator_gate"
                ),
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
        },
        "supervisor_decision": {
            "decision": "materialize_recovery_action",
            "identity_match": True,
            "paper_autonomy_obligation": {
                "study_id": study_id,
                "quest_id": study_id,
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
        },
    }

    monkeypatch.setattr(
        module,
        "_run_domain_health_diagnostic_for_runtime_impl",
        lambda **kwargs: {
            "surface": "domain_health_diagnostic",
            "action_class": "observe_only",
            "scanned_at": "2026-06-14T00:00:00+00:00",
            "paper_recovery_states": {study_id: recovery_state},
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "reason": "anti_loop_budget_exhausted",
                    "paper_recovery_state": recovery_state,
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.domain_action_request_materializer,
        "materialize_domain_action_requests",
        lambda **kwargs: {
            "surface": "domain_action_request_materializer",
            "dry_run": True,
            "request_task_count": 0,
            "default_executor_dispatch_count": 0,
            "ready_default_executor_dispatch_count": 0,
            "blocked_default_executor_dispatch_count": 0,
            "default_executor_dispatches": [],
        },
    )
    monkeypatch.setattr(
        module,
        "_materialize_report_provider_admission_current_control_state",
        lambda **kwargs: None,
    )

    def fake_read_study_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": current_work_unit,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "one-person-lab",
                "typed_blocker": current_work_unit["state"]["typed_blocker"],
            },
            "paper_recovery_state": recovery_state,
            "current_executable_owner_action": None,
        }

    monkeypatch.setattr(study_progress, "read_study_progress", fake_read_study_progress)

    report = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        apply=False,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
    )

    assert report["domain_handler_owner_resolution_preview_task_count"] == 1
    preview = report["domain_handler_owner_resolution_preview"]
    task = preview["tasks"][0]
    assert task["task_kind"] == "domain_route/reconcile-apply"
    assert task["reason"] == "current_work_unit_typed_blocker_owner_resolution"
    assert task["queue_owner"] == "one-person-lab"
    assert task["payload"]["required_owner_action"]["accepted_resolution_shapes"][:3] == [
        "matching_provider_attempt_or_lease_binding",
        "matching_terminal_closeout_receipt",
        "identity_different_successor_owner_action",
    ]
    action_preview = report["managed_study_actions"][0]["domain_handler_owner_resolution_preview"]
    assert action_preview["study_id"] == study_id
    assert action_preview["task_count"] == 1
    assert action_preview["tasks"][0]["task_kind"] == "domain_route/reconcile-apply"
    assert report["action_class"] == "observe_only"


def test_domain_health_diagnostic_rebuilds_recovery_state_with_fresh_progress_path_context(
    tmp_path: Path,
) -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    fingerprint = "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    closeout_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
        "consumer/default_executor_execution/sat_67e10efde628859185249aa0.closeout.json"
    )
    closeout_path = workspace_root / closeout_ref
    closeout_path.parent.mkdir(parents=True, exist_ok=True)
    dump_json(
        closeout_path,
        {
            "stage_attempt_id": "sat_67e10efde628859185249aa0",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": work_unit_id,
            "paper_stage_log": {
                "next_forced_delta": {
                    "required_delta_kind": (
                        "publishability_repair_sprint_or_single_typed_blocker_"
                        "or_human_or_operator_gate"
                    ),
                    "work_unit_id": work_unit_id,
                },
            },
        },
    )
    typed_blocker = {
        "blocker_id": "anti_loop_budget_exhausted",
        "blocker_type": "anti_loop_budget_exhausted",
        "owner": "one-person-lab",
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "source_ref": f"{closeout_ref}#typed_blocker",
        "typed_blocker_ref": f"{closeout_ref}#typed_blocker",
        "latest_owner_answer_ref": f"{closeout_ref}#typed_blocker",
        "closeout_refs": [closeout_ref],
    }

    result = report_aggregation.build_runtime_report(
        runtime_root=tmp_path / "runtime" / "quests",
        scanned=[],
        reports=[],
        managed_study_actions=[
            {
                "study_id": study_id,
                "reason": "anti_loop_budget_exhausted",
            }
        ],
        managed_study_auto_recoveries=[],
        managed_study_recovery_holds=[],
        managed_study_outer_loop_dispatches=[],
        managed_study_outer_loop_wakeup_audits=[],
        managed_study_no_op_suppressions=[],
        managed_study_opl_runtime_owner_handoffs=[],
        managed_study_opl_provider_admission_candidates=[],
        managed_study_progress_currentness={
            study_id: {
                "study_id": study_id,
                "quest_id": study_id,
                "study_root": str(study_root),
                "workspace_root": str(workspace_root),
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "typed_blocker",
                    "study_id": study_id,
                    "owner": "one-person-lab",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "currentness_basis": {
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "action_fingerprint": fingerprint,
                        "stage_attempt_id": "sat_67e10efde628859185249aa0",
                    },
                    "state": {
                        "state_kind": "typed_blocker",
                        "typed_blocker": typed_blocker,
                    },
                },
                "next_forced_delta": {
                    "required_delta_kind": "review_current_paper_delta",
                    "work_unit_id": work_unit_id,
                },
            }
        },
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
    )

    recovery = result["paper_recovery_states"][study_id]
    assert recovery["next_safe_action"]["required_input"] == (
        "publishability_repair_sprint_or_single_typed_blocker_or_human_or_operator_gate"
    )
    assert result["managed_study_actions"][0]["paper_recovery_state"]["next_safe_action"][
        "required_input"
    ] == (
        "publishability_repair_sprint_or_single_typed_blocker_or_human_or_operator_gate"
    )


def test_domain_health_diagnostic_same_tick_treats_opl_authorization_blocker_as_provider_handoff(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    scan_calls: list[dict[str, object]] = []

    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    def fake_scan_domain_routes(**kwargs) -> dict[str, object]:
        scan_calls.append(kwargs)
        return {
            "surface": "portable_owner_route_reconcile",
            "action_queue": [
                {
                    "study_id": study_id,
                    "action_type": "run_gate_clearing_batch",
                    "action_id": f"supervisor-action::{study_id}::gate-replay",
                }
            ],
            "studies": [
                {
                    "study_id": study_id,
                    "running_provider_attempt": False,
                    "active_run_id": None,
                    "active_stage_attempt_id": None,
                }
            ],
        }

    monkeypatch.setattr(module.owner_route_reconcile, "scan_domain_routes", fake_scan_domain_routes)
    monkeypatch.setattr(
        module.domain_action_request_materializer,
        "materialize_domain_action_requests",
        lambda **kwargs: {
            "surface": "domain_action_request_materializer",
            "request_task_count": 1,
            "default_executor_dispatch_count": 1,
            "ready_default_executor_dispatch_count": 1,
            "blocked_default_executor_dispatch_count": 0,
            "default_executor_dispatches": [
                {
                    "study_id": study_id,
                    "action_type": "run_gate_clearing_batch",
                    "dispatch_status": "ready",
                    "dispatch_authority": "consumer_default_executor_dispatch",
                    "next_executable_owner": "gate_clearing_batch",
                    "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        lambda **kwargs: {
            "surface": "domain_owner_action_dispatch",
            "execution_count": 1,
            "executed_count": 0,
            "blocked_count": 1,
            "repeat_suppressed_count": 0,
            "codex_dispatch_count": 0,
            "executions": [
                {
                    "study_id": study_id,
                    "action_type": "run_gate_clearing_batch",
                    "execution_status": "blocked",
                    "blocked_reason": "opl_execution_authorization_required",
                    "dispatch_path": str(
                        study_root
                        / "artifacts/supervision/consumer/default_executor_dispatches/run_gate_clearing_batch.json"
                    ),
                    "dispatch_authority": "consumer_default_executor_dispatch",
                    "provider_attempt_or_lease_required": True,
                    "owner_route_current": True,
                }
            ],
        },
    )

    supervisor_tick = module._run_developer_supervisor_same_tick(profile=profile, max_passes=1)

    assert len(scan_calls) == 2
    assert scan_calls[1]["persist_surfaces"] is True
    assert supervisor_tick["stop_reason"] == "provider_handoff_written_admission_pending"
    diagnostic = supervisor_tick["progress_first_terminal_diagnostic"]
    assert diagnostic["requires_provider_admission"] is True
    assert diagnostic["requires_dispatch_blocker_resolution"] is False
    assert diagnostic["same_tick_terminal_projection"] == {
        "terminal_state": "provider_handoff_written_admission_pending",
        "owner_delta_produced": False,
        "provider_attempt_running": False,
        "stable_typed_blocker_observed": False,
        "provider_handoff_written": True,
    }
    assert diagnostic["next_forced_delta"]["required_delta_kind"] == "opl_provider_attempt_admission"


def test_domain_health_diagnostic_same_tick_rejects_authorization_blocker_without_current_identity(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    scan_calls: list[dict[str, object]] = []

    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    def fake_scan_domain_routes(**kwargs) -> dict[str, object]:
        scan_calls.append(kwargs)
        return {
            "surface": "portable_owner_route_reconcile",
            "action_queue": [],
            "studies": [
                {
                    "study_id": study_id,
                    "running_provider_attempt": False,
                    "active_run_id": None,
                    "active_stage_attempt_id": None,
                }
            ],
        }

    monkeypatch.setattr(module.owner_route_reconcile, "scan_domain_routes", fake_scan_domain_routes)
    monkeypatch.setattr(
        module.domain_action_request_materializer,
        "materialize_domain_action_requests",
        lambda **kwargs: {
            "surface": "domain_action_request_materializer",
            "request_task_count": 1,
            "default_executor_dispatch_count": 1,
            "ready_default_executor_dispatch_count": 1,
            "blocked_default_executor_dispatch_count": 0,
            "default_executor_dispatches": [
                {
                    "study_id": study_id,
                    "action_type": "run_gate_clearing_batch",
                    "dispatch_status": "ready",
                    "dispatch_authority": "consumer_default_executor_dispatch",
                    "next_executable_owner": "gate_clearing_batch",
                    "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        lambda **kwargs: {
            "surface": "domain_owner_action_dispatch",
            "execution_count": 1,
            "executed_count": 0,
            "blocked_count": 1,
            "repeat_suppressed_count": 0,
            "codex_dispatch_count": 0,
            "executions": [
                {
                    "study_id": study_id,
                    "action_type": "run_gate_clearing_batch",
                    "execution_status": "blocked",
                    "blocked_reason": "opl_execution_authorization_required",
                    "dispatch_path": str(
                        study_root
                        / "artifacts/supervision/consumer/default_executor_dispatches/run_gate_clearing_batch.json"
                    ),
                    "dispatch_authority": "consumer_default_executor_dispatch",
                    "provider_attempt_or_lease_required": True,
                    "owner_route_current": True,
                }
            ],
        },
    )

    supervisor_tick = module._run_developer_supervisor_same_tick(profile=profile, max_passes=1)

    assert len(scan_calls) == 1
    assert supervisor_tick["stop_reason"] == "typed_blocker_or_dispatch_blocker_observed"
    diagnostic = supervisor_tick["progress_first_terminal_diagnostic"]
    assert diagnostic["requires_provider_admission"] is False
    assert diagnostic["requires_dispatch_blocker_resolution"] is True
    assert diagnostic["same_tick_terminal_projection"] == {
        "terminal_state": "stable_typed_blocker_observed",
        "owner_delta_produced": False,
        "provider_attempt_running": False,
        "stable_typed_blocker_observed": True,
        "provider_handoff_written": False,
    }


def test_domain_health_diagnostic_opl_authorization_blocker_matches_current_identity(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    blocked_study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    running_study_id = "002-dm-china-us-mortality-attribution"
    blocked_study_root = profile.studies_root / blocked_study_id
    blocked_study_root.mkdir(parents=True, exist_ok=True)
    dump_json(blocked_study_root / "study.yaml", {"study_id": blocked_study_id})
    running_study_root = profile.studies_root / running_study_id
    running_study_root.mkdir(parents=True, exist_ok=True)
    dump_json(running_study_root / "study.yaml", {"study_id": running_study_id})
    scan_calls: list[dict[str, object]] = []

    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    def fake_scan_domain_routes(**kwargs) -> dict[str, object]:
        scan_calls.append(kwargs)
        return {
            "surface": "portable_owner_route_reconcile",
            "action_queue": [
                {
                    "study_id": blocked_study_id,
                    "action_type": "run_gate_clearing_batch",
                    "action_id": f"supervisor-action::{blocked_study_id}::gate-replay",
                }
            ],
            "studies": [
                {
                    "study_id": running_study_id,
                    "running_provider_attempt": True,
                    "active_stage_attempt_id": "sat_other",
                    "opl_provider_attempt": {
                        "study_id": running_study_id,
                        "action_type": "run_gate_clearing_batch",
                        "dispatch_ref": (
                            f"studies/{running_study_id}/artifacts/supervision/consumer/"
                            "default_executor_dispatches/run_gate_clearing_batch.json"
                        ),
                    },
                },
                {
                    "study_id": blocked_study_id,
                    "running_provider_attempt": False,
                    "active_stage_attempt_id": None,
                },
            ],
        }

    monkeypatch.setattr(module.owner_route_reconcile, "scan_domain_routes", fake_scan_domain_routes)
    monkeypatch.setattr(
        module.domain_action_request_materializer,
        "materialize_domain_action_requests",
        lambda **kwargs: {
            "surface": "domain_action_request_materializer",
            "request_task_count": 1,
            "default_executor_dispatch_count": 1,
            "ready_default_executor_dispatch_count": 1,
            "blocked_default_executor_dispatch_count": 0,
            "default_executor_dispatches": [
                {
                    "study_id": blocked_study_id,
                    "action_type": "run_gate_clearing_batch",
                    "dispatch_status": "ready",
                    "dispatch_authority": "consumer_default_executor_dispatch",
                    "next_executable_owner": "gate_clearing_batch",
                    "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        lambda **kwargs: {
            "surface": "domain_owner_action_dispatch",
            "execution_count": 1,
            "executed_count": 0,
            "blocked_count": 1,
            "repeat_suppressed_count": 0,
            "codex_dispatch_count": 0,
            "executions": [
                {
                    "study_id": blocked_study_id,
                    "action_type": "run_gate_clearing_batch",
                    "execution_status": "blocked",
                    "blocked_reason": "opl_execution_authorization_required",
                    "dispatch_path": str(
                        blocked_study_root
                        / "artifacts/supervision/consumer/default_executor_dispatches/run_gate_clearing_batch.json"
                    ),
                    "dispatch_authority": "consumer_default_executor_dispatch",
                    "provider_attempt_or_lease_required": True,
                    "owner_route_current": True,
                }
            ],
        },
    )

    supervisor_tick = module._run_developer_supervisor_same_tick(
        profile=profile,
        study_ids=(blocked_study_id,),
        max_passes=1,
    )

    assert len(scan_calls) == 2
    assert supervisor_tick["stop_reason"] == "provider_handoff_written_admission_pending"
    diagnostic = supervisor_tick["progress_first_terminal_diagnostic"]
    assert diagnostic["requires_provider_admission"] is True
    assert diagnostic["same_tick_terminal_projection"]["provider_attempt_running"] is False
    assert diagnostic["provider_admission_probe"] == {
        "observed": False,
        "running_provider_attempt_count": 0,
        "study_ids": [running_study_id, blocked_study_id],
    }


def test_domain_health_diagnostic_same_tick_dispatch_consumes_materialize_payload(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    materialize_payload = {
        "surface": "domain_action_request_materializer",
        "request_task_count": 1,
        "default_executor_dispatch_count": 1,
        "ready_default_executor_dispatch_count": 1,
        "blocked_default_executor_dispatch_count": 0,
        "default_executor_dispatches": [
            {
                "study_id": study_id,
                "action_type": "run_quality_repair_batch",
                "dispatch_status": "ready",
                "dispatch_authority": "quality_repair_batch_writer_handoff",
                "next_executable_owner": "write",
            }
        ],
    }
    captured_consumer_payloads: list[object] = []

    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(
        module.owner_route_reconcile,
        "scan_domain_routes",
        lambda **kwargs: {
            "surface": "portable_owner_route_reconcile",
            "action_queue": [{"study_id": study_id, "action_type": "return_to_ai_reviewer_workflow"}],
        },
    )
    monkeypatch.setattr(
        module.domain_action_request_materializer,
        "materialize_domain_action_requests",
        lambda **kwargs: materialize_payload,
    )

    def fake_dispatch_domain_owner_actions(**kwargs) -> dict[str, object]:
        captured_consumer_payloads.append(kwargs.get("consumer_payload"))
        return {
            "surface": "domain_owner_action_dispatch",
            "execution_count": 1,
            "executed_count": 1,
            "blocked_count": 0,
            "repeat_suppressed_count": 0,
            "codex_dispatch_count": 1,
            "executions": [{"execution_status": "handoff_ready", "will_start_llm": True}],
        }

    monkeypatch.setattr(
        module.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        fake_dispatch_domain_owner_actions,
    )

    supervisor_tick = module._run_developer_supervisor_same_tick(profile=profile, max_passes=1)

    assert captured_consumer_payloads == [materialize_payload]
    assert supervisor_tick["pass_count"] == 1
    assert supervisor_tick["iterations"][0]["progress_first_delta"]["dispatch_execution_count"] == 1
