from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_domain_health_diagnostic_focused_same_tick_does_not_retain_unscanned_owner_route_studies(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    owner_route_reconcile = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    all_study_ids = ("001-risk", "002-risk", "003-risk", "004-risk")
    focused_study_ids = ("002-risk", "003-risk")
    for study_id in all_study_ids:
        study_root = profile.studies_root / study_id
        study_root.mkdir(parents=True, exist_ok=True)
        dump_json(study_root / "study.yaml", {"study_id": study_id})
    dump_json(
        profile.workspace_root / owner_route_reconcile.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-02T00:00:00+00:00",
            "studies": [
                {"study_id": "001-risk", "handoff_scan_status": "scanned"},
                {"study_id": "004-risk", "handoff_scan_status": "scanned"},
            ],
            "action_queue": [
                {
                    "study_id": "001-risk",
                    "action_id": "stale-001",
                    "action_type": "run_quality_repair_batch",
                },
                {
                    "study_id": "004-risk",
                    "action_id": "stale-004",
                    "action_type": "run_quality_repair_batch",
                },
            ],
        },
    )
    scan_calls: list[dict[str, object]] = []

    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(
        module.owner_route_reconcile.opl_provider_attempts,
        "current_provider_readiness",
        lambda **kwargs: {"status": "ready"},
    )
    monkeypatch.setattr(
        module.owner_route_reconcile,
        "_study_projection",
        lambda **kwargs: scan_calls.append(kwargs)
        or {
            "study_id": kwargs["study_id"],
            "study_root": str(profile.studies_root / kwargs["study_id"]),
            "current_execution_envelope": {},
            "action_queue": [
                {
                    "action_id": f"current-{kwargs['study_id']}",
                    "action_type": "run_quality_repair_batch",
                }
            ],
            "running_provider_attempt": False,
            "active_run_id": None,
            "active_stage_attempt_id": None,
        },
    )
    monkeypatch.setattr(
        module.owner_route_reconcile.workspace_daemon,
        "workspace_daemon_lifecycle",
        lambda **kwargs: {"status": "not_required"},
    )
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
            "codex_dispatch_count": 1,
            "executions": [{"execution_status": "handoff_ready", "will_start_llm": True}],
        },
    )

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        study_ids=focused_study_ids,
        request_opl_stage_attempts=True,
        request_opl_owner_route_reconcile=True,
    )

    supervisor_tick = result["developer_supervisor_same_tick"]
    provider_probe = supervisor_tick["iterations"][0]["provider_admission_probe"]
    observed_scan_ids = [call["study_id"] for call in scan_calls]
    assert observed_scan_ids == [
        "002-risk",
        "003-risk",
        "002-risk",
        "003-risk",
    ]
    assert [study["study_id"] for study in supervisor_tick["owner_route_reconcile"]["studies"]] == list(
        focused_study_ids
    )
    assert [study["study_id"] for study in provider_probe["studies"]] == list(focused_study_ids)
    assert [action["study_id"] for action in provider_probe["action_queue"]] == list(focused_study_ids)
    assert [action["study_id"] for action in result["opl_owner_route_reconcile_request"]["action_queue"]] == list(
        focused_study_ids
    )
