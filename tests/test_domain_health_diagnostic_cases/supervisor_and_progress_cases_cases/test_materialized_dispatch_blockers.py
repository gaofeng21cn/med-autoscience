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
