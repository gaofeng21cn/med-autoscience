from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_domain_health_diagnostic_does_not_expose_retired_materializer_or_dispatcher() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")

    assert not hasattr(module, "domain_action_request_materializer")
    assert not hasattr(module, "domain_owner_action_dispatch")


def test_domain_health_diagnostic_apply_requests_opl_readback_without_mas_local_pump(
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

    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    def fake_scan_domain_routes(**kwargs) -> dict[str, object]:
        scan_calls.append(kwargs)
        return {
            "surface": "portable_owner_route_reconcile",
            "apply_safe_actions": kwargs["apply_safe_actions"],
            "study_ids": list(kwargs["study_ids"]),
            "study_count": len(kwargs["study_ids"]),
            "action_queue": [
                {
                    "study_id": study_ids[0],
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "quality_repair",
                    "work_unit_fingerprint": "quality-repair::fp",
                }
            ],
            "studies": [
                {
                    "study_id": study_id,
                    "running_provider_attempt": False,
                    "active_run_id": None,
                    "active_stage_attempt_id": None,
                }
                for study_id in kwargs["study_ids"]
            ],
        }

    monkeypatch.setattr(module.owner_route_reconcile, "scan_domain_routes", fake_scan_domain_routes)

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
        request_opl_owner_route_reconcile=True,
    )

    assert len(scan_calls) == 1
    assert scan_calls[0]["study_ids"] == study_ids
    assert scan_calls[0]["retain_unscanned_studies"] is True
    supervisor_tick = result["developer_supervisor_same_tick"]
    assert supervisor_tick["stop_reason"] == "opl_transition_readback_required"
    assert supervisor_tick["actions"] == [
        "owner-route-reconcile",
        "OPL DomainProgressTransitionRuntime readback required",
        "MAS owner callable adapter blocked without OPL authorization",
    ]
    assert supervisor_tick["retired_private_surfaces"] == [
        "domain-action-request-materialize",
        "domain-owner-action-dispatch",
    ]
    assert supervisor_tick["owner_boundaries"][
        "mas_can_create_opl_command_event_outbox_or_stagerun"
    ] is False
    assert supervisor_tick["owner_boundaries"]["mas_can_authorize_provider_admission"] is False
    assert supervisor_tick["materialize"]["surface_kind"] == (
        "developer_supervisor_same_tick_retired_materialize_projection"
    )
    assert supervisor_tick["dispatch"]["surface_kind"] == (
        "developer_supervisor_same_tick_retired_dispatch_blocker"
    )
    diagnostic = supervisor_tick["progress_first_terminal_diagnostic"]
    assert diagnostic["requires_opl_transition_readback"] is True
    assert diagnostic["next_forced_delta"]["required_delta_kind"] == (
        "opl_domain_progress_transition_readback"
    )
    assert supervisor_tick["iterations"][0]["progress_first_delta"][
        "codex_dispatch_count"
    ] == 0


def test_domain_health_diagnostic_focused_same_tick_scans_only_requested_studies(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    all_study_ids = ("001-risk", "002-risk", "003-risk", "004-risk")
    focused_study_ids = ("002-risk", "003-risk")
    for study_id in all_study_ids:
        study_root = profile.studies_root / study_id
        study_root.mkdir(parents=True, exist_ok=True)
        dump_json(study_root / "study.yaml", {"study_id": study_id})
    scan_calls: list[dict[str, object]] = []

    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(
        module.owner_route_reconcile,
        "scan_domain_routes",
        lambda **kwargs: scan_calls.append(kwargs)
        or {
            "surface": "portable_owner_route_reconcile",
            "study_ids": list(kwargs["study_ids"]),
            "action_queue": [
                {
                    "study_id": kwargs["study_ids"][0],
                    "action_type": "run_quality_repair_batch",
                }
            ],
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

    assert [call["study_ids"] for call in scan_calls] == [focused_study_ids]
    assert scan_calls[0]["retain_unscanned_studies"] is False
    assert result["developer_supervisor_same_tick"]["study_ids"] == list(focused_study_ids)


def test_domain_health_diagnostic_dry_run_preview_consumes_existing_transition_requests_only(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    transition_request = {
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "dispatch_status": "transition_request_pending",
        "provider_admission_pending": False,
        "provider_admission_requires_opl_runtime_result": True,
        "opl_transition_runtime_required": True,
    }
    recovery_state = {
        "surface_kind": "paper_recovery_state",
        "phase": "owner_action_ready",
        "next_safe_action": {"kind": "materialize_successor_owner_action"},
        "supervisor_decision": {"decision": "materialize_recovery_action"},
    }

    monkeypatch.setattr(
        module,
        "_run_domain_health_diagnostic_for_runtime_impl",
        lambda **kwargs: {
            "surface": "domain_health_diagnostic",
            "action_class": "observe_only",
            "scanned_at": "2026-06-19T00:00:00+00:00",
            "provider_admission_pending_count": 0,
            "transition_request_pending_count": 1,
            "managed_study_opl_provider_admission_candidates": [],
            "managed_study_opl_transition_request_candidates": [transition_request],
            "current_execution_evidence": {
                "provider_admission_candidates": [],
                "transition_request_candidates": [transition_request],
                "progress_currentness": {},
            },
            "paper_recovery_states": {study_id: recovery_state},
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "paper_recovery_state": recovery_state,
                }
            ],
        },
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

    preview = report["domain_action_request_materialization_preview"]
    assert preview["surface_kind"] == "dhd_materialization_preview_retired_opl_readback_required"
    assert preview["active_materializer_call"] is False
    assert preview["mas_can_create_opl_command_event_outbox_or_stagerun"] is False
    assert report["materialization_preview_request_task_count"] == 0
    assert report["materialization_preview_transition_request_count"] == 1
    assert report["materialization_preview_transition_request_pending_count"] == 1
    assert report["materialization_preview_legacy_owner_callable_adapter_count"] == 0
    [candidate] = report["managed_study_opl_transition_request_candidates"]
    assert candidate["study_id"] == study_id
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["work_unit_fingerprint"] == fingerprint
    assert candidate["status"] == "transition_request_pending"
    assert candidate["source"] == "dhd_materialization_preview_existing_transition_request"
    assert candidate["same_tick_materialization_source"] == (
        "existing_opl_transition_request_projection"
    )
    action_preview = report["managed_study_actions"][0][
        "domain_action_request_materialization_preview"
    ]
    assert action_preview["transition_request_count"] == 1
    assert action_preview["legacy_owner_callable_adapter_count"] == 0
    assert "owner_callable_adapters" not in action_preview
    assert report["provider_admission_pending_count"] == 0


def test_domain_health_diagnostic_dry_run_preview_fails_closed_without_transition_request(
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
    recovery_state = {
        "surface_kind": "paper_recovery_state",
        "phase": "owner_action_ready",
        "next_safe_action": {"kind": "run_mas_owner_callable"},
        "supervisor_decision": {"decision": "materialize_recovery_action"},
    }

    monkeypatch.setattr(
        module,
        "_run_domain_health_diagnostic_for_runtime_impl",
        lambda **kwargs: {
            "surface": "domain_health_diagnostic",
            "action_class": "observe_only",
            "scanned_at": "2026-06-19T00:00:00+00:00",
            "provider_admission_pending_count": 0,
            "transition_request_pending_count": 0,
            "managed_study_opl_provider_admission_candidates": [],
            "managed_study_opl_transition_request_candidates": [],
            "current_execution_evidence": {
                "provider_admission_candidates": [],
                "transition_request_candidates": [],
                "progress_currentness": {},
            },
            "paper_recovery_states": {study_id: recovery_state},
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "paper_recovery_state": recovery_state,
                }
            ],
        },
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

    preview = report["domain_action_request_materialization_preview"]
    assert preview["surface_kind"] == "dhd_materialization_preview_retired_opl_readback_required"
    assert preview["domain_progress_transition_requests"] == []
    assert preview["blocked_reason"] == "opl_domain_progress_transition_runtime_readback_required"
    assert report["materialization_preview_request_task_count"] == 0
    assert report["materialization_preview_transition_request_count"] == 0
    assert report["materialization_preview_owner_callable_adapter_count"] == 0
    assert report["materialization_preview_legacy_owner_callable_adapter_count"] == 0
    assert "domain_action_request_materialization_preview" not in report["managed_study_actions"][0]
    assert report["managed_study_opl_transition_request_candidates"] == []
    assert report["managed_study_opl_provider_admission_candidates"] == []
    assert report["provider_admission_pending_count"] == 0
    assert report["transition_request_pending_count"] == 0
