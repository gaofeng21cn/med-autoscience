from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_domain_health_diagnostic_apply_runs_mas_owner_callable_for_recovery_state(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    actuator = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.obligation_actuator"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    calls: list[dict[str, object]] = []
    recovery_state = {
        "surface_kind": "paper_recovery_state",
        "phase": "owner_action_ready",
        "next_safe_action": {
            "kind": "run_mas_owner_callable",
            "owner": "gate_clearing_batch",
            "provider_admission_allowed": False,
            "owner_callable": {
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
            },
        },
        "supervisor_decision": {"decision": "materialize_recovery_action"},
    }

    monkeypatch.setattr(
        module,
        "_run_domain_health_diagnostic_for_runtime_impl",
        lambda **kwargs: {
            "surface": "domain_health_diagnostic",
            "action_class": "observe_only",
            "scanned_at": "2026-06-15T00:00:00+00:00",
            "current_execution_evidence": {"progress_currentness": {}},
            "paper_recovery_states": {study_id: recovery_state},
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "study_root": str(study_root),
                    "paper_recovery_state": recovery_state,
                }
            ],
        },
    )
    monkeypatch.setattr(
        actuator.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **kwargs: calls.append(kwargs)
        or {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
        },
    )
    monkeypatch.setattr(
        module,
        "_materialize_report_provider_admission_current_control_state",
        lambda **kwargs: {
            "surface": "opl_current_control_state_handoff",
            "provider_admission_candidates": [],
        },
    )
    monkeypatch.setattr(
        module,
        "_sync_report_provider_admission_current_control_state",
        lambda report, **kwargs: None,
    )
    monkeypatch.setattr(
        module,
        "_fresh_progress_currentness_for_report",
        lambda **kwargs: {
            study_id: {
                "study_id": study_id,
                "current_work_unit": {"status": "typed_blocker", "owner": "gate_clearing_batch"},
            }
        },
    )

    report = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        apply=True,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
    )

    assert len(calls) == 1
    assert calls[0]["profile"] is profile
    assert calls[0]["study_id"] == study_id
    assert calls[0]["study_root"] == study_root
    assert calls[0]["quest_id"] == study_id
    assert calls[0]["source"] == "domain_health_diagnostic_mas_owner_callable"
    actions = report["managed_study_mas_owner_callable_actions"]
    assert actions[0]["callable_surface"] == "gate_clearing_batch.run_gate_clearing_batch"
    assert actions[0]["ok"] is True
    assert actions[0]["status"] == "executed"
    _assert_exactly_one_dhd_apply_outcome(
        report["managed_study_obligation_actuator_outcomes"][0],
        "owner_receipt_ref",
    )
    assert report["provider_admission_current_control_state"]["provider_admission_candidates"] == []
    assert report["managed_study_actions"][0]["current_work_unit"]["status"] == "typed_blocker"


def test_domain_health_diagnostic_apply_runs_mas_owner_callable_from_canonical_next_safe_action(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    actuator = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.obligation_actuator"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    calls: list[dict[str, object]] = []
    recovery_state = {
        "surface_kind": "paper_recovery_state",
        "phase": "owner_action_ready",
        "next_safe_action": {
            "kind": "run_mas_owner_callable",
            "owner": "write",
            "provider_admission_allowed": False,
            "owner_callable": {
                "owner": "quality_repair_batch",
                "action_type": "run_quality_repair_batch",
                "callable_surface": "quality_repair_batch.run_quality_repair_batch",
            },
        },
        "supervisor_decision": {"decision": "materialize_recovery_action"},
    }

    monkeypatch.setattr(
        module,
        "_run_domain_health_diagnostic_for_runtime_impl",
        lambda **kwargs: {
            "surface": "domain_health_diagnostic",
            "action_class": "observe_only",
            "scanned_at": "2026-06-15T00:00:00+00:00",
            "current_execution_evidence": {"progress_currentness": {}},
            "paper_recovery_states": {study_id: recovery_state},
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "study_root": str(study_root),
                    "paper_recovery_state": recovery_state,
                }
            ],
        },
    )
    monkeypatch.setattr(
        actuator.quality_repair_batch,
        "run_quality_repair_batch",
        lambda **kwargs: calls.append(kwargs)
        or {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"),
        },
    )
    monkeypatch.setattr(
        module,
        "_materialize_report_provider_admission_current_control_state",
        lambda **kwargs: {
            "surface": "opl_current_control_state_handoff",
            "provider_admission_candidates": [],
        },
    )
    monkeypatch.setattr(
        module,
        "_sync_report_provider_admission_current_control_state",
        lambda report, **kwargs: None,
    )
    monkeypatch.setattr(
        module,
        "_fresh_progress_currentness_for_report",
        lambda **kwargs: {
            study_id: {
                "study_id": study_id,
                "current_work_unit": {"status": "typed_blocker", "owner": "write"},
            }
        },
    )

    report = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        apply=True,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
    )

    assert len(calls) == 1
    assert calls[0]["profile"] is profile
    assert calls[0]["study_id"] == study_id
    assert calls[0]["study_root"] == study_root
    assert calls[0]["quest_id"] == study_id
    assert calls[0]["source"] == "domain_health_diagnostic_mas_owner_callable"
    actions = report["managed_study_mas_owner_callable_actions"]
    assert actions[0]["callable_surface"] == "quality_repair_batch.run_quality_repair_batch"
    assert actions[0]["ok"] is True
    assert actions[0]["status"] == "executed"
    _assert_exactly_one_dhd_apply_outcome(
        report["managed_study_obligation_actuator_outcomes"][0],
        "owner_receipt_ref",
    )


def test_domain_health_diagnostic_apply_consumes_mas_owner_callable_before_same_tick_reconcile(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    actuator = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.obligation_actuator"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    events: list[str] = []
    recovery_state = {
        "surface_kind": "paper_recovery_state",
        "phase": "owner_action_ready",
        "next_safe_action": {
            "kind": "run_mas_owner_callable",
            "owner": "quality_repair_batch",
            "provider_admission_allowed": False,
            "owner_callable": {
                "owner": "quality_repair_batch",
                "action_type": "run_quality_repair_batch",
                "callable_surface": "quality_repair_batch.run_quality_repair_batch",
            },
        },
        "supervisor_decision": {"decision": "materialize_recovery_action"},
    }

    monkeypatch.setattr(
        module,
        "_run_domain_health_diagnostic_for_runtime_impl",
        lambda **kwargs: {
            "surface": "domain_health_diagnostic",
            "action_class": "observe_only",
            "scanned_at": "2026-06-15T00:00:00+00:00",
            "current_execution_evidence": {"progress_currentness": {}},
            "paper_recovery_states": {study_id: recovery_state},
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "study_root": str(study_root),
                    "paper_recovery_state": recovery_state,
                }
            ],
        },
    )
    monkeypatch.setattr(
        module,
        "_run_developer_supervisor_same_tick",
        lambda **kwargs: events.append("same_tick")
        or {
            "surface": "developer_supervisor_same_tick",
            "stop_reason": "typed_blocker_or_dispatch_blocker_observed",
            "iterations": [{"owner_route_reconcile": {"surface": "portable_owner_route_reconcile"}}],
        },
    )
    monkeypatch.setattr(
        actuator.quality_repair_batch,
        "run_quality_repair_batch",
        lambda **kwargs: events.append("owner_callable")
        or {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"),
        },
    )
    monkeypatch.setattr(
        module,
        "_fresh_progress_currentness_for_report",
        lambda **kwargs: {
            study_id: {
                "study_id": study_id,
                "current_work_unit": {
                    "status": "owner_action_ready",
                    "owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                },
            }
        },
    )
    monkeypatch.setattr(
        module,
        "_materialize_report_provider_admission_current_control_state",
        lambda **kwargs: {
            "surface": "opl_current_control_state_handoff",
            "provider_admission_candidates": [],
        },
    )
    monkeypatch.setattr(
        module,
        "_sync_report_provider_admission_current_control_state",
        lambda report, **kwargs: None,
    )

    report = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        apply=True,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
        request_opl_owner_route_reconcile=True,
    )

    assert events == ["owner_callable", "same_tick"]
    assert report["managed_study_mas_owner_callable_actions"][0]["status"] == "executed"
    assert report["developer_supervisor_same_tick"]["stop_reason"] == (
        "typed_blocker_or_dispatch_blocker_observed"
    )
    assert report["managed_study_actions"][0]["current_work_unit"]["owner"] == "gate_clearing_batch"


def test_domain_health_diagnostic_apply_drains_mas_owner_callable_created_by_same_tick_reconcile(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    actuator = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.obligation_actuator"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    events: list[str] = []
    gate_recovery_state = {
        "surface_kind": "paper_recovery_state",
        "phase": "owner_action_ready",
        "next_safe_action": {
            "kind": "run_mas_owner_callable",
            "owner": "gate_clearing_batch",
            "provider_admission_allowed": False,
            "owner_callable": {
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
            },
        },
        "supervisor_decision": {"decision": "materialize_recovery_action"},
    }
    repair_recovery_state = {
        "surface_kind": "paper_recovery_state",
        "phase": "owner_action_ready",
        "next_safe_action": {
            "kind": "run_mas_owner_callable",
            "owner": "write",
            "provider_admission_allowed": False,
            "owner_callable": {
                "owner": "quality_repair_batch",
                "action_type": "run_quality_repair_batch",
                "callable_surface": "quality_repair_batch.run_quality_repair_batch",
            },
        },
        "supervisor_decision": {"decision": "materialize_recovery_action"},
    }

    monkeypatch.setattr(
        module,
        "_run_domain_health_diagnostic_for_runtime_impl",
        lambda **kwargs: {
            "surface": "domain_health_diagnostic",
            "action_class": "observe_only",
            "scanned_at": "2026-06-15T00:00:00+00:00",
            "current_execution_evidence": {"progress_currentness": {}},
            "paper_recovery_states": {study_id: gate_recovery_state},
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "study_root": str(study_root),
                    "paper_recovery_state": gate_recovery_state,
                }
            ],
        },
    )
    monkeypatch.setattr(
        module,
        "_run_developer_supervisor_same_tick",
        lambda **kwargs: events.append("same_tick")
        or {
            "surface": "developer_supervisor_same_tick",
            "stop_reason": "typed_blocker_or_dispatch_blocker_observed",
            "iterations": [{"owner_route_reconcile": {"surface": "portable_owner_route_reconcile"}}],
        },
    )
    monkeypatch.setattr(
        actuator.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **kwargs: events.append("gate_callable")
        or {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
        },
    )
    monkeypatch.setattr(
        actuator.quality_repair_batch,
        "run_quality_repair_batch",
        lambda **kwargs: events.append("repair_callable")
        or {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"),
        },
    )

    fresh_reads = 0

    def fake_fresh_progress_currentness(**kwargs) -> dict[str, dict[str, object]]:
        nonlocal fresh_reads
        fresh_reads += 1
        if fresh_reads <= 1:
            recovery = {
                **gate_recovery_state,
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "provider_admission_allowed": True,
                },
            }
        else:
            recovery = repair_recovery_state
        return {
            study_id: {
                "study_id": study_id,
                "current_work_unit": {
                    "status": "executable_owner_action",
                    "owner": _owner_from_recovery(recovery),
                },
                "paper_recovery_state": recovery,
            }
        }

    monkeypatch.setattr(
        module,
        "_fresh_progress_currentness_for_report",
        fake_fresh_progress_currentness,
    )
    monkeypatch.setattr(
        module,
        "_materialize_report_provider_admission_current_control_state",
        lambda **kwargs: {
            "surface": "opl_current_control_state_handoff",
            "provider_admission_candidates": [],
        },
    )
    monkeypatch.setattr(
        module,
        "_sync_report_provider_admission_current_control_state",
        lambda report, **kwargs: None,
    )

    report = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        apply=True,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
        request_opl_owner_route_reconcile=True,
    )

    assert events == ["gate_callable", "same_tick", "repair_callable"]
    actions = report["managed_study_mas_owner_callable_actions"]
    assert [action["callable_surface"] for action in actions] == [
        "gate_clearing_batch.run_gate_clearing_batch",
        "quality_repair_batch.run_quality_repair_batch",
    ]


def test_domain_health_diagnostic_apply_accepts_refreshed_owner_receipt_postcondition(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    actuator = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.obligation_actuator"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    gate_replay_ref = str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json")
    initial_recovery_state = {
        "surface_kind": "paper_recovery_state",
        "phase": "owner_action_ready",
        "next_safe_action": {
            "kind": "run_mas_owner_callable",
            "owner": "gate_clearing_batch",
            "provider_admission_allowed": False,
            "owner_callable": {
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
            },
        },
        "supervisor_decision": {"decision": "materialize_recovery_action"},
    }
    refreshed_recovery_state = {
        "surface_kind": "paper_recovery_state",
        "phase": "owner_receipt_recorded",
        "evidence_refs": [gate_replay_ref],
        "current_authority": {
            "obligation": {
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "sha256:gate-replay-current",
            }
        },
        "next_safe_action": {
            "kind": "consume_owner_receipt",
            "owner": "gate_clearing_batch",
            "provider_admission_allowed": False,
            "owner_receipt_ref": gate_replay_ref,
        },
        "supervisor_decision": {"decision": "stop_with_owner_receipt"},
    }

    monkeypatch.setattr(
        module,
        "_run_domain_health_diagnostic_for_runtime_impl",
        lambda **kwargs: {
            "surface": "domain_health_diagnostic",
            "action_class": "observe_only",
            "scanned_at": "2026-06-15T00:00:00+00:00",
            "current_execution_evidence": {"progress_currentness": {}},
            "paper_recovery_states": {study_id: initial_recovery_state},
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "study_root": str(study_root),
                    "paper_recovery_state": initial_recovery_state,
                }
            ],
        },
    )
    monkeypatch.setattr(
        actuator.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **kwargs: {
            "ok": True,
            "status": "executed",
            "record_path": gate_replay_ref,
        },
    )
    monkeypatch.setattr(
        module,
        "_fresh_progress_currentness_for_report",
        lambda **kwargs: {
            study_id: {
                "study_id": study_id,
                "current_work_unit": {
                    "status": "owner_receipt_recorded",
                    "owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": "sha256:gate-replay-current",
                    "state": {
                        "state_kind": "owner_receipt_recorded",
                        "owner_receipt_ref": gate_replay_ref,
                    },
                },
                "paper_recovery_state": refreshed_recovery_state,
            }
        },
    )
    monkeypatch.setattr(
        module,
        "_materialize_report_provider_admission_current_control_state",
        lambda **kwargs: {"surface": "opl_current_control_state_handoff"},
    )
    monkeypatch.setattr(
        module,
        "_sync_report_provider_admission_current_control_state",
        lambda report, **kwargs: None,
    )

    report = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        apply=True,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
    )

    action = report["managed_study_actions"][0]
    assert action["paper_recovery_state"]["phase"] == "owner_receipt_recorded"
    assert action["dhd_apply_postcondition"]["ok"] is True
    assert action["dhd_apply_postcondition"]["outcome_kind"] == "owner_receipt_ref"
    outcomes = [
        outcome
        for outcome in report["managed_study_obligation_actuator_outcomes"]
        if outcome["study_id"] == study_id
    ]
    assert len(outcomes) == 1
    _assert_exactly_one_dhd_apply_outcome(outcomes[0], "owner_receipt_ref")
    assert outcomes[0]["owner_receipt_ref"] == gate_replay_ref


def _owner_from_recovery(recovery: dict[str, object]) -> str | None:
    next_safe_action = recovery.get("next_safe_action")
    if not isinstance(next_safe_action, dict):
        return None
    return next_safe_action.get("owner") if isinstance(next_safe_action.get("owner"), str) else None


def test_domain_health_diagnostic_apply_requires_materialize_decision_for_owner_callable(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    actuator = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.obligation_actuator"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    calls: list[dict[str, object]] = []
    recovery_state = {
        "surface_kind": "paper_recovery_state",
        "phase": "owner_action_ready",
        "next_safe_action": {
            "kind": "run_mas_owner_callable",
            "owner": "gate_clearing_batch",
            "provider_admission_allowed": False,
            "owner_callable": {
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
            },
        },
        "supervisor_decision": {"decision": "wait_for_owner_with_resume_token"},
    }

    monkeypatch.setattr(
        module,
        "_run_domain_health_diagnostic_for_runtime_impl",
        lambda **kwargs: {
            "surface": "domain_health_diagnostic",
            "action_class": "observe_only",
            "scanned_at": "2026-06-15T00:00:00+00:00",
            "current_execution_evidence": {"progress_currentness": {}},
            "paper_recovery_states": {study_id: recovery_state},
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "study_root": str(study_root),
                    "paper_recovery_state": recovery_state,
                }
            ],
        },
    )
    monkeypatch.setattr(
        actuator.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **kwargs: calls.append(kwargs) or {"ok": True, "status": "executed"},
    )
    monkeypatch.setattr(
        module,
        "_materialize_report_provider_admission_current_control_state",
        lambda **kwargs: {
            "surface": "opl_current_control_state_handoff",
            "provider_admission_candidates": [],
        },
    )
    monkeypatch.setattr(
        module,
        "_sync_report_provider_admission_current_control_state",
        lambda report, **kwargs: None,
    )

    report = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        apply=True,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
    )

    assert calls == []
    assert "managed_study_mas_owner_callable_actions" not in report
    assert report["provider_admission_current_control_state"]["provider_admission_candidates"] == []


def test_domain_health_diagnostic_apply_fails_closed_when_ready_action_has_no_closed_outcome(
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
        "next_safe_action": {
            "kind": "materialize_provider_admission_or_owner_callable",
            "owner": "write",
            "provider_admission_allowed": True,
        },
        "supervisor_decision": {
            "decision": "materialize_recovery_action",
            "next_safe_action": {
                "kind": "materialize_recovery_work_unit_or_receipt",
                "source_next_safe_action": {
                    "kind": "materialize_provider_admission_or_owner_callable",
                    "owner": "write",
                    "provider_admission_allowed": True,
                },
            },
        },
    }

    monkeypatch.setattr(
        module,
        "_run_domain_health_diagnostic_for_runtime_impl",
        lambda **kwargs: {
            "surface": "domain_health_diagnostic",
            "action_class": "observe_only",
            "scanned_at": "2026-06-15T00:00:00+00:00",
            "current_execution_evidence": {"progress_currentness": {}},
            "paper_recovery_states": {study_id: recovery_state},
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "study_root": str(study_root),
                    "paper_recovery_state": recovery_state,
                    "current_executable_owner_action": {
                        "status": "ready",
                        "next_owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    },
                    "domain_action_request_materialization_preview": {
                        "default_executor_dispatch_count": 1,
                        "ready_default_executor_dispatch_count": 1,
                        "default_executor_dispatches": [
                            {
                                "study_id": study_id,
                                "action_type": "run_quality_repair_batch",
                                "dispatch_status": "ready",
                            }
                        ],
                    },
                }
            ],
        },
    )
    monkeypatch.setattr(
        module,
        "_materialize_report_provider_admission_current_control_state",
        lambda **kwargs: {
            "surface": "opl_current_control_state_handoff",
            "provider_admission_candidates": [],
            "running_provider_attempt": False,
        },
    )
    monkeypatch.setattr(
        module,
        "_sync_report_provider_admission_current_control_state",
        lambda report, **kwargs: None,
    )
    monkeypatch.setattr(
        module,
        "_fresh_progress_currentness_for_report",
        lambda **kwargs: {
            study_id: {
                "study_id": study_id,
                "current_work_unit": {
                    "status": "executable_owner_action",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                },
                "current_executable_owner_action": {
                    "status": "ready",
                    "next_owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                },
                "paper_recovery_state": recovery_state,
            }
        },
    )

    report = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        apply=True,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
    )

    outcomes = report["managed_study_obligation_actuator_outcomes"]
    assert len(outcomes) == 1
    outcome = outcomes[0]
    assert outcome["outcome_kind"] == "typed_blocker_ref"
    _assert_exactly_one_dhd_apply_outcome(outcome, "typed_blocker_ref")
    assert outcome["typed_control_blocker"]["blocker_type"] == (
        "dhd_apply_no_closed_obligation_outcome"
    )
    assert report["managed_study_actions"][0]["dhd_apply_postcondition"]["ok"] is False


def _assert_exactly_one_dhd_apply_outcome(
    outcome: dict[str, object],
    expected_kind: str,
) -> None:
    allowed = [
        "provider_admission_pending",
        "running_provider_attempt",
        "owner_receipt_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]
    present = [key for key in allowed if outcome.get(key)]
    assert outcome["exactly_one_outcome"] is True
    assert outcome["outcome_kind"] == expected_kind
    assert present == [expected_kind]
