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


def test_domain_health_diagnostic_dry_run_surfaces_current_handoff_ready_provider_admission_candidate(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    quest_root = profile.runtime_root / "quests" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "complete_medical_paper_readiness_surface.json"
    )
    typed_blocker_ref = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "08-publication_package_handoff"
        / "receipts"
        / "typed_blocker.json"
    )
    work_unit_fingerprint = (
        "stage-current-owner-delta::complete_medical_paper_readiness_surface::"
        f"authoring_runtime_authorization::{typed_blocker_ref}"
    )
    dump_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "study_id": study_id,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "complete_medical_paper_readiness_surface",
                    "execution_status": "handoff_ready",
                    "owner_callable_surface": "opl_default_executor.stage_attempt",
                    "provider_attempt_or_lease_required": True,
                    "provider_completion_is_domain_completion": False,
                    "next_executable_owner": "MedAutoScience",
                    "required_output_surface": "complete_medical_paper_readiness_surface",
                    "dispatch_path": str(dispatch_path),
                    "dispatch_authority": "consumer_default_executor_dispatch",
                    "action_fingerprint": work_unit_fingerprint,
                    "owner_route_current": True,
                    "owner_route_basis": "scan_latest",
                    "will_start_llm": True,
                    "owner_route": {
                        "work_unit_fingerprint": work_unit_fingerprint,
                        "source_refs": {
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                            "work_unit_fingerprint": work_unit_fingerprint,
                            "blocked_reason": "medical_paper_readiness_not_ready",
                            "quest_root": str(quest_root),
                            "owner_route_currentness_basis": {
                                "work_unit_id": "complete_medical_paper_readiness_surface",
                                "work_unit_fingerprint": work_unit_fingerprint,
                            },
                        },
                    },
                }
            ],
        },
    )
    status_payload = {
        **make_progress_projection_payload(
            study_id=study_id,
            decision="resume",
            reason="quest_marked_running_but_no_live_session",
        ),
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(quest_root),
        "quest_status": "running",
    }
    current_action = {
        "status": "ready",
        "source": "stage_kernel_projection.current_owner_delta",
        "next_owner": "MedAutoScience",
        "work_unit_id": "complete_medical_paper_readiness_surface",
        "allowed_actions": ["complete_medical_paper_readiness_surface"],
        "surface_key": "authoring_runtime_authorization",
        "source_ref": str(typed_blocker_ref),
    }

    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "generated_at": "2026-06-07T19:56:40+00:00",
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "MedAutoScience",
                "next_work_unit": "complete_medical_paper_readiness_surface",
                "typed_blocker": None,
                "parked_state": None,
            },
            "current_executable_owner_action": current_action,
        },
    )

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
    )

    assert result["provider_admission_pending_count"] == 1
    candidate = result["managed_study_opl_provider_admission_candidates"][0]
    assert candidate["status"] == "provider_admission_pending"
    assert candidate["source"] == "default_executor_execution"
    assert candidate["study_id"] == study_id
    assert candidate["action_type"] == "complete_medical_paper_readiness_surface"
    assert candidate["work_unit_id"] == "complete_medical_paper_readiness_surface"
    assert candidate["work_unit_fingerprint"] == work_unit_fingerprint
    assert candidate["action_fingerprint"] == work_unit_fingerprint
    assert candidate["dispatch_path"] == str(dispatch_path)
    assert candidate["owner_callable_surface"] == "opl_default_executor.stage_attempt"
    assert candidate["provider_attempt_or_lease_required"] is True
    envelope = result["current_execution_envelopes"][study_id]
    assert envelope["state_kind"] == "executable_owner_action"
    assert envelope["owner"] == "MedAutoScience"
    assert envelope["next_work_unit"] == "complete_medical_paper_readiness_surface"
    assert envelope["typed_blocker"] is None
    assert result["action_fingerprints"] == [work_unit_fingerprint]


def test_provider_admission_candidate_requires_current_action_identity() -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    typed_blocker_ref = (
        "/workspace/studies/002-dm-china-us-mortality-attribution/"
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
    )
    current_fingerprint = (
        "stage-current-owner-delta::complete_medical_paper_readiness_surface::"
        f"authoring_runtime_authorization::{typed_blocker_ref}"
    )
    stale_fingerprint = "paper_progress_stall:002-dm-china-us-mortality-attribution:old-ai-reviewer"

    result = provider_admission.provider_admission_candidates_from_execution_payload(
        {
            "executions": [
                {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "execution_status": "handoff_ready",
                    "owner_callable_surface": "opl_default_executor.stage_attempt",
                    "provider_attempt_or_lease_required": True,
                    "dispatch_path": "/workspace/stale-ai-reviewer.json",
                    "action_fingerprint": stale_fingerprint,
                    "owner_route": {
                        "source_refs": {
                            "work_unit_id": "return_to_ai_reviewer_workflow",
                            "work_unit_fingerprint": stale_fingerprint,
                        }
                    },
                },
                {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "action_type": "complete_medical_paper_readiness_surface",
                    "execution_status": "handoff_ready",
                    "owner_callable_surface": "opl_default_executor.stage_attempt",
                    "provider_attempt_or_lease_required": True,
                    "dispatch_path": "/workspace/current-readiness.json",
                    "action_fingerprint": current_fingerprint,
                    "owner_route": {
                        "source_refs": {
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                            "work_unit_fingerprint": current_fingerprint,
                        }
                    },
                },
            ]
        },
        status_payload={
            "study_id": "002-dm-china-us-mortality-attribution",
            "current_executable_owner_action": {
                "status": "ready",
                "source": "stage_kernel_projection.current_owner_delta",
                "next_owner": "MedAutoScience",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "allowed_actions": ["complete_medical_paper_readiness_surface"],
                "surface_key": "authoring_runtime_authorization",
                "source_ref": typed_blocker_ref,
            },
        },
    )

    assert [candidate["action_fingerprint"] for candidate in result] == [current_fingerprint]


def test_provider_admission_candidate_accepts_study_progress_owner_ticket_identity() -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    typed_blocker_ref = (
        f"/workspace/studies/{study_id}/"
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
    )
    ticket_fingerprint = (
        f"study-progress-current-owner-ticket::{study_id}::"
        "complete_medical_paper_readiness_surface::complete_medical_paper_readiness_surface"
    )
    stale_fingerprint = f"paper_progress_stall::{study_id}::old-readiness"

    result = provider_admission.provider_admission_candidates_from_execution_payload(
        {
            "executions": [
                {
                    "study_id": study_id,
                    "action_type": "complete_medical_paper_readiness_surface",
                    "execution_status": "handoff_ready",
                    "owner_callable_surface": "opl_default_executor.stage_attempt",
                    "provider_attempt_or_lease_required": True,
                    "dispatch_path": "/workspace/stale-readiness.json",
                    "action_fingerprint": stale_fingerprint,
                    "owner_route": {
                        "source_refs": {
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                            "work_unit_fingerprint": stale_fingerprint,
                        }
                    },
                },
                {
                    "study_id": study_id,
                    "action_type": "complete_medical_paper_readiness_surface",
                    "execution_status": "handoff_ready",
                    "owner_callable_surface": "opl_default_executor.stage_attempt",
                    "provider_attempt_or_lease_required": True,
                    "dispatch_path": "/workspace/current-readiness.json",
                    "action_fingerprint": ticket_fingerprint,
                    "owner_route": {
                        "source_refs": {
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                            "work_unit_fingerprint": ticket_fingerprint,
                        }
                    },
                },
            ]
        },
        status_payload={
            "study_id": study_id,
            "current_executable_owner_action": {
                "status": "ready",
                "source": "stage_kernel_projection.current_owner_delta",
                "next_owner": "MedAutoScience",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "allowed_actions": ["complete_medical_paper_readiness_surface"],
                "surface_key": "authoring_runtime_authorization",
                "source_ref": typed_blocker_ref,
            },
        },
    )

    assert [candidate["action_fingerprint"] for candidate in result] == [ticket_fingerprint]


def test_provider_admission_candidate_is_suppressed_by_typed_blocker_envelope() -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    stale_fingerprint = "domain-transition::003-dpcc-primary-care-phenotype-treatment-gap::finalize"

    result = provider_admission.provider_admission_candidates_from_execution_payload(
        {
            "executions": [
                {
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "action_type": "request_opl_stage_attempt",
                    "execution_status": "handoff_ready",
                    "owner_callable_surface": "opl_default_executor.stage_attempt",
                    "provider_attempt_or_lease_required": True,
                    "dispatch_path": "/workspace/stale-finalize.json",
                    "action_fingerprint": stale_fingerprint,
                    "owner_route": {
                        "source_refs": {
                            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                            "work_unit_fingerprint": stale_fingerprint,
                        }
                    },
                },
            ]
        },
        status_payload={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_type": "medical_paper_readiness_missing",
                    "source_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "receipts/typed_blocker.json"
                    ),
                },
            },
            "current_executable_owner_action": {
                "source": "domain_transition",
                "next_owner": "finalize",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["request_opl_stage_attempt"],
            },
        },
    )

    assert result == []


def test_provider_admission_candidate_requires_dispatch_path() -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    fingerprint = "stage-current-owner-delta::complete_medical_paper_readiness_surface::typed-blocker"

    result = provider_admission.provider_admission_candidates_from_execution_payload(
        {
            "executions": [
                {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "action_type": "complete_medical_paper_readiness_surface",
                    "execution_status": "handoff_ready",
                    "owner_callable_surface": "opl_default_executor.stage_attempt",
                    "provider_attempt_or_lease_required": True,
                    "action_fingerprint": fingerprint,
                    "owner_route": {
                        "source_refs": {
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                            "work_unit_fingerprint": fingerprint,
                        }
                    },
                }
            ]
        },
        status_payload={"study_id": "002-dm-china-us-mortality-attribution"},
    )

    assert result == []


def test_request_opl_stage_attempt_carries_current_provider_admission_identity(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "complete_medical_paper_readiness_surface.json"
    )
    typed_blocker_ref = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "08-publication_package_handoff"
        / "receipts"
        / "typed_blocker.json"
    )
    work_unit_fingerprint = (
        "stage-current-owner-delta::complete_medical_paper_readiness_surface::"
        f"authoring_runtime_authorization::{typed_blocker_ref}"
    )
    dump_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "executions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "complete_medical_paper_readiness_surface",
                    "execution_status": "handoff_ready",
                    "owner_callable_surface": "opl_default_executor.stage_attempt",
                    "provider_attempt_or_lease_required": True,
                    "dispatch_path": str(dispatch_path),
                    "action_fingerprint": work_unit_fingerprint,
                    "owner_route": {
                        "source_refs": {
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                            "work_unit_fingerprint": work_unit_fingerprint,
                        }
                    },
                }
            ]
        },
    )
    status_payload = {
        **make_progress_projection_payload(
            study_id=study_id,
            decision="resume",
            reason="quest_marked_running_but_no_live_session",
        ),
        "quest_id": study_id,
            "current_executable_owner_action": {
                "status": "ready",
                "source": "stage_kernel_projection.current_owner_delta",
                "next_owner": "MedAutoScience",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "allowed_actions": ["complete_medical_paper_readiness_surface"],
                "surface_key": "authoring_runtime_authorization",
            "source_ref": str(typed_blocker_ref),
        },
    }
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)

    result = module._request_opl_stage_attempt(
        profile=profile,
        study_root=study_root,
        source="domain_health_diagnostic",
    )

    identity = result["opl_stage_attempt_request"]["provider_admission_identity"]
    assert identity["study_id"] == study_id
    assert identity["action_type"] == "complete_medical_paper_readiness_surface"
    assert identity["work_unit_id"] == "complete_medical_paper_readiness_surface"
    assert identity["action_fingerprint"] == work_unit_fingerprint
    assert identity["dispatch_path"] == str(dispatch_path)
    assert result["provider_admission_identity"] == identity


def test_domain_health_diagnostic_same_tick_refreshes_materialize_after_pending_provider_probe(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    scan_calls: list[dict[str, object]] = []
    materialize_calls: list[dict[str, object]] = []

    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    def fake_scan_domain_routes(**kwargs) -> dict[str, object]:
        scan_calls.append(kwargs)
        fingerprint = f"truth-snapshot::{len(scan_calls)}"
        return {
            "surface": "portable_owner_route_reconcile",
            "action_queue": [
                {
                    "study_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "owner_route": {
                        "work_unit_fingerprint": fingerprint,
                        "source_refs": {
                            "owner_route_currentness_basis": {
                                "work_unit_id": fingerprint,
                                "work_unit_fingerprint": fingerprint,
                            }
                        },
                    },
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

    def fake_materialize(**kwargs) -> dict[str, object]:
        materialize_calls.append(kwargs)
        generation = "initial" if len(materialize_calls) == 1 else "post-probe"
        work_unit = f"truth-snapshot::{generation}"
        return {
            "surface": "domain_action_request_materializer",
            "request_task_count": 1,
            "default_executor_dispatch_count": 1,
            "ready_default_executor_dispatch_count": 1,
            "blocked_default_executor_dispatch_count": 0,
            "default_executor_dispatches": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "dispatch_status": "ready",
                    "dispatch_authority": "ai_reviewer_record_production_handoff",
                    "next_executable_owner": "ai_reviewer",
                    "required_output_surface": "ai_reviewer_record",
                    "owner_route": {
                        "work_unit_fingerprint": work_unit,
                        "source_refs": {
                            "owner_route_currentness_basis": {
                                "work_unit_id": work_unit,
                                "work_unit_fingerprint": work_unit,
                            }
                        },
                    },
                    "refs": {
                        "dispatch_path": f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/{generation}.json"
                    },
                }
            ],
        }

    monkeypatch.setattr(module.owner_route_reconcile, "scan_domain_routes", fake_scan_domain_routes)
    monkeypatch.setattr(module.domain_action_request_materializer, "materialize_domain_action_requests", fake_materialize)
    monkeypatch.setattr(
        module.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        lambda **kwargs: pytest.fail("record-only provider handoff should not start MAS-local LLM dispatch"),
    )

    supervisor_tick = module._run_developer_supervisor_same_tick(profile=profile, max_passes=3)

    assert supervisor_tick["stop_reason"] == "provider_handoff_written_admission_pending"
    assert len(scan_calls) == 2
    assert scan_calls[1]["persist_surfaces"] is True
    assert len(materialize_calls) == 2
    iteration = supervisor_tick["iterations"][0]
    assert iteration["post_admission_materialize"]["default_executor_dispatches"][0]["refs"]["dispatch_path"].endswith(
        "/post-probe.json"
    )
    assert supervisor_tick["materialize"] == iteration["post_admission_materialize"]
    diagnostic = supervisor_tick["progress_first_terminal_diagnostic"]
    assert diagnostic["requires_provider_admission"] is True
    assert diagnostic["post_admission_materialize"] == {
        "observed": True,
        "default_executor_dispatch_count": 1,
        "ready_default_executor_dispatch_count": 1,
    }


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


def test_domain_health_diagnostic_same_tick_rejects_stale_provider_attempt_for_new_handoff(
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
    dispatch_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        "run_quality_repair_batch.json"
    )

    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    scan_calls: list[dict[str, object]] = []

    def fake_scan_domain_routes(**kwargs) -> dict[str, object]:
        scan_calls.append(kwargs)
        admitted = len(scan_calls) == 2
        return {
            "surface": "portable_owner_route_reconcile",
            "action_queue": [
                {
                    "study_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "controller_next_work_unit": {
                        "unit_id": "medical_prose_write_repair",
                        "owner": "write",
                    },
                }
            ],
            "studies": [
                {
                    "study_id": study_id,
                    "running_provider_attempt": admitted,
                    "active_run_id": "opl-stage-attempt://sat-stale-ai" if admitted else None,
                    "active_stage_attempt_id": "sat-stale-ai" if admitted else None,
                    "opl_provider_attempt": (
                        {
                            "running_provider_attempt": True,
                            "active_stage_attempt_id": "sat-stale-ai",
                            "active_run_id": "opl-stage-attempt://sat-stale-ai",
                            "action_type": "return_to_ai_reviewer_workflow",
                            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                            "dispatch_ref": (
                                f"studies/{study_id}/artifacts/supervision/consumer/"
                                "default_executor_dispatches/return_to_ai_reviewer_workflow.json"
                            ),
                        }
                        if admitted
                        else {}
                    ),
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
            "executions": [
                {
                    "study_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "dispatch_path": str(profile.workspace_root / dispatch_ref),
                    "execution_status": "handoff_ready",
                    "will_start_llm": True,
                }
            ],
        },
    )

    supervisor_tick = module._run_developer_supervisor_same_tick(profile=profile, max_passes=1)

    assert len(scan_calls) == 2
    assert supervisor_tick["stop_reason"] == "provider_handoff_written_admission_pending"
    diagnostic = supervisor_tick["progress_first_terminal_diagnostic"]
    assert diagnostic["same_tick_terminal_projection"]["provider_attempt_running"] is False
    assert diagnostic["requires_provider_admission"] is True


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
