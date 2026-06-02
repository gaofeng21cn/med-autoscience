from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_domain_health_diagnostic_same_tick_reports_handoff_pending_without_provider_attempt(
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
            "studies": [
                {
                    "study_id": study_id,
                    "running_provider_attempt": False,
                    "active_run_id": None,
                    "active_stage_attempt_id": None,
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.domain_action_request_materializer,
        "materialize_domain_action_requests",
        lambda **kwargs: {"default_executor_dispatch_count": 1},
    )
    monkeypatch.setattr(
        module.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        lambda **kwargs: {
            "execution_count": 1,
            "codex_dispatch_count": 1,
            "executions": [{"execution_status": "handoff_ready", "will_start_llm": True}],
        },
    )

    supervisor_tick = module._run_developer_supervisor_same_tick(profile=profile, max_passes=3)

    assert supervisor_tick["stop_reason"] == "provider_handoff_written_admission_pending"
    diagnostic = supervisor_tick["progress_first_terminal_diagnostic"]
    assert diagnostic["same_tick_terminal_projection"] == {
        "terminal_state": "provider_handoff_written_admission_pending",
        "owner_delta_produced": False,
        "provider_attempt_running": False,
        "stable_typed_blocker_observed": False,
        "provider_handoff_written": True,
    }
    assert diagnostic["requires_provider_admission"] is True
    assert diagnostic["provider_admission_probe"] == {
        "observed": False,
        "running_provider_attempt_count": 0,
        "study_ids": [study_id],
    }
    assert diagnostic["next_forced_delta"]["target_surface"]["owner"] == "one-person-lab"


def test_domain_health_diagnostic_same_tick_reports_provider_attempt_started_after_admission_probe(
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
    scan_calls: list[dict[str, object]] = []

    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    def fake_scan_domain_routes(**kwargs) -> dict[str, object]:
        scan_calls.append(kwargs)
        admitted = len(scan_calls) == 2
        return {
            "surface": "portable_owner_route_reconcile",
            "action_queue": [{"study_id": study_id, "action_type": "run_quality_repair_batch"}],
            "studies": [
                {
                    "study_id": study_id,
                    "running_provider_attempt": admitted,
                    "active_run_id": "opl-stage-attempt://sat_123" if admitted else None,
                    "active_stage_attempt_id": "sat_123" if admitted else None,
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
        },
    )
    monkeypatch.setattr(
        module.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        lambda **kwargs: {
            "surface": "domain_owner_action_dispatch",
            "execution_count": 1,
            "executed_count": 1,
            "codex_dispatch_count": 1,
            "executions": [{"execution_status": "handoff_ready", "will_start_llm": True}],
        },
    )

    supervisor_tick = module._run_developer_supervisor_same_tick(profile=profile, max_passes=3)

    assert len(scan_calls) == 2
    assert scan_calls[0]["live_attempt_timeout_seconds"] == module.PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_TIMEOUT_SECONDS
    assert scan_calls[0]["live_attempt_max_inspect_count"] == module.PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_MAX_INSPECT_COUNT
    assert (
        scan_calls[0]["provider_readiness_timeout_seconds"]
        == module.PROGRESS_FIRST_SAME_TICK_PROVIDER_READINESS_TIMEOUT_SECONDS
    )
    assert scan_calls[1]["persist_surfaces"] is True
    assert scan_calls[1]["live_attempt_timeout_seconds"] == module.PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_TIMEOUT_SECONDS
    assert scan_calls[1]["live_attempt_max_inspect_count"] == module.PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_MAX_INSPECT_COUNT
    assert (
        scan_calls[1]["provider_readiness_timeout_seconds"]
        == module.PROGRESS_FIRST_SAME_TICK_PROVIDER_READINESS_TIMEOUT_SECONDS
    )
    assert supervisor_tick["pass_count"] == 1
    assert supervisor_tick["stop_reason"] == "provider_attempt_started"
    assert supervisor_tick["provider_probe_budget"] == {
        "live_attempt_timeout_seconds": module.PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_TIMEOUT_SECONDS,
        "provider_readiness_timeout_seconds": module.PROGRESS_FIRST_SAME_TICK_PROVIDER_READINESS_TIMEOUT_SECONDS,
        "live_attempt_max_inspect_count": module.PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_MAX_INSPECT_COUNT,
        "scope": "focused_same_tick_owner_route_scan",
    }
    diagnostic = supervisor_tick["progress_first_terminal_diagnostic"]
    assert diagnostic["same_tick_terminal_projection"] == {
        "terminal_state": "provider_attempt_running",
        "owner_delta_produced": False,
        "provider_attempt_running": True,
        "stable_typed_blocker_observed": False,
        "provider_handoff_written": True,
    }
    assert diagnostic["requires_provider_admission"] is False
    assert diagnostic["provider_admission_probe"] == {
        "observed": True,
        "running_provider_attempt_count": 1,
    }
    assert diagnostic["next_forced_delta"] is None
    assert diagnostic["forbidden_next_actions"] == []


def test_domain_health_diagnostic_same_tick_continues_after_partial_provider_admission(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_ids = ("001-risk", "002-risk")
    for study_id in study_ids:
        study_root = profile.studies_root / study_id
        study_root.mkdir(parents=True, exist_ok=True)
        dump_json(study_root / "study.yaml", {"study_id": study_id})
    scan_calls: list[dict[str, object]] = []
    materialize_calls: list[dict[str, object]] = []
    dispatch_calls: list[dict[str, object]] = []

    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    def fake_scan_domain_routes(**kwargs) -> dict[str, object]:
        scan_calls.append(kwargs)
        call_index = len(scan_calls)
        if call_index == 1:
            action_queue = [
                {"study_id": "001-risk", "action_type": "run_quality_repair_batch"},
                {"study_id": "002-risk", "action_type": "return_to_ai_reviewer_workflow"},
            ]
            running = set()
        elif call_index == 2:
            action_queue = [{"study_id": "002-risk", "action_type": "return_to_ai_reviewer_workflow"}]
            running = {"001-risk"}
        else:
            action_queue = []
            running = {"001-risk", "002-risk"}
        return {
            "surface": "portable_owner_route_reconcile",
            "action_queue": action_queue,
            "studies": [
                {
                    "study_id": study_id,
                    "running_provider_attempt": study_id in running,
                    "active_run_id": f"opl-stage-attempt://sat-{study_id}" if study_id in running else None,
                    "active_stage_attempt_id": f"sat-{study_id}" if study_id in running else None,
                }
                for study_id in study_ids
            ],
        }

    def fake_materialize(**kwargs) -> dict[str, object]:
        materialize_calls.append(kwargs)
        return {
            "surface": "domain_action_request_materializer",
            "request_task_count": 1,
            "default_executor_dispatch_count": 1,
        }

    def fake_dispatch(**kwargs) -> dict[str, object]:
        dispatch_calls.append(kwargs)
        return {
            "surface": "domain_owner_action_dispatch",
            "execution_count": 1,
            "executed_count": 1,
            "codex_dispatch_count": 1,
            "executions": [{"execution_status": "handoff_ready", "will_start_llm": True}],
        }

    monkeypatch.setattr(module.owner_route_reconcile, "scan_domain_routes", fake_scan_domain_routes)
    monkeypatch.setattr(module.domain_action_request_materializer, "materialize_domain_action_requests", fake_materialize)
    monkeypatch.setattr(module.domain_owner_action_dispatch, "dispatch_domain_owner_actions", fake_dispatch)

    supervisor_tick = module._run_developer_supervisor_same_tick(
        profile=profile,
        study_ids=study_ids,
        max_passes=4,
    )

    assert supervisor_tick["pass_count"] == 2
    assert supervisor_tick["stop_reason"] == "provider_attempt_started"
    assert len(dispatch_calls) == 2
    for call in scan_calls:
        assert call["live_attempt_timeout_seconds"] == module.PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_TIMEOUT_SECONDS
        assert call["live_attempt_max_inspect_count"] == module.PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_MAX_INSPECT_COUNT
        assert (
            call["provider_readiness_timeout_seconds"]
            == module.PROGRESS_FIRST_SAME_TICK_PROVIDER_READINESS_TIMEOUT_SECONDS
        )
    assert scan_calls[1]["persist_surfaces"] is True
    assert scan_calls[2]["persist_surfaces"] is True
    assert supervisor_tick["iterations"][0]["provider_admission_probe"]["action_queue"] == [
        {"study_id": "002-risk", "action_type": "return_to_ai_reviewer_workflow"}
    ]
    assert supervisor_tick["iterations"][0]["progress_first_delta"]["codex_dispatch_count"] == 1
    assert supervisor_tick["iterations"][1]["provider_admission_probe"]["action_queue"] == []
    assert supervisor_tick["iterations"][1]["post_admission_materialize"]["default_executor_dispatch_count"] == 1
    assert len(materialize_calls) == 3


def test_domain_health_diagnostic_same_tick_terminal_projection_reports_owner_delta_required() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")

    diagnostic = module._same_tick_terminal_diagnostic(
        stop_reason="repeat_suppressed_owner_delta_required",
        iterations=[
            {
                "progress_first_delta": {
                    "dispatch_repeat_suppressed_count": 1,
                    "codex_dispatch_count": 0,
                    "handoff_ready_count": 0,
                },
                "dispatch": {
                    "executions": [
                        {
                            "execution_status": "repeat_suppressed",
                            "repeat_suppressed": True,
                        }
                    ]
                },
            }
        ],
    )

    assert diagnostic["same_tick_terminal_projection"] == {
        "terminal_state": "owner_delta_required",
        "owner_delta_produced": True,
        "provider_attempt_running": False,
        "stable_typed_blocker_observed": False,
        "provider_handoff_written": False,
    }
