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
