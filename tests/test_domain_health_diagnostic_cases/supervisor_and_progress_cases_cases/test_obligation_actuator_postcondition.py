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
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    record_path = str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json")
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
            "managed_study_mas_owner_callable_actions": [
                {
                    "surface_kind": "mas_owner_callable_action",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                    "callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
                    "ok": True,
                    "status": "executed",
                    "record_path": record_path,
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

    actions = report["managed_study_mas_owner_callable_actions"]
    assert actions[0]["callable_surface"] == "gate_clearing_batch.run_gate_clearing_batch"
    assert actions[0]["ok"] is True
    assert actions[0]["status"] == "executed"
    _assert_exactly_one_dhd_apply_outcome(
        report["managed_study_obligation_actuator_outcomes"][0],
        "owner_receipt_ref",
    )
    assert report["provider_admission_current_control_state"]["provider_admission_candidates"] == []


def test_domain_health_diagnostic_apply_runs_mas_owner_callable_from_canonical_next_safe_action(
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
    record_path = str(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json")
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
            "managed_study_mas_owner_callable_actions": [
                {
                    "surface_kind": "mas_owner_callable_action",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "quality_repair_batch",
                    "action_type": "run_quality_repair_batch",
                    "callable_surface": "quality_repair_batch.run_quality_repair_batch",
                    "ok": True,
                    "status": "executed",
                    "record_path": record_path,
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

    actions = report["managed_study_mas_owner_callable_actions"]
    assert actions[0]["callable_surface"] == "quality_repair_batch.run_quality_repair_batch"
    assert actions[0]["ok"] is True
    assert actions[0]["status"] == "executed"
    _assert_exactly_one_dhd_apply_outcome(
        report["managed_study_obligation_actuator_outcomes"][0],
        "owner_receipt_ref",
    )


def test_domain_health_diagnostic_apply_consumes_mas_owner_callable_without_same_tick_reconcile(
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
    events: list[str] = []
    record_path = str(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json")
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
            "managed_study_mas_owner_callable_actions": [
                {
                    "surface_kind": "mas_owner_callable_action",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "quality_repair_batch",
                    "action_type": "run_quality_repair_batch",
                    "callable_surface": "quality_repair_batch.run_quality_repair_batch",
                    "ok": True,
                    "status": "executed",
                    "record_path": record_path,
                }
            ],
        },
    )
    def fail_if_same_tick_runs(**kwargs):
        events.append("same_tick")
        raise AssertionError("terminal owner receipt must close before same-tick reconcile")

    monkeypatch.setattr(module, "_run_developer_supervisor_same_tick", fail_if_same_tick_runs)
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

    assert events == []
    assert report["managed_study_mas_owner_callable_actions"][0]["status"] == "executed"
    assert "developer_supervisor_same_tick" not in report
    _assert_exactly_one_dhd_apply_outcome(
        report["managed_study_obligation_actuator_outcomes"][0],
        "owner_receipt_ref",
    )


def test_domain_health_diagnostic_apply_drains_mas_owner_callable_created_by_same_tick_reconcile(
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

    assert events == ["same_tick"]
    assert "managed_study_mas_owner_callable_actions" not in report
    assert report["managed_study_obligation_actuator_outcomes"][0]["outcome_kind"] == "typed_blocker_ref"


def test_domain_health_diagnostic_apply_accepts_refreshed_owner_receipt_postcondition(
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
            "managed_study_mas_owner_callable_actions": [
                {
                    "surface_kind": "mas_owner_callable_action",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                    "callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
                    "ok": True,
                    "status": "executed",
                    "record_path": gate_replay_ref,
                }
            ],
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


def test_domain_health_diagnostic_apply_continues_same_tick_for_owner_receipt_consumption(
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
    gate_replay_ref = str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json")
    recovery_state = {
        "surface_kind": "paper_recovery_state",
        "phase": "owner_receipt_recorded",
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
            "paper_recovery_states": {study_id: recovery_state},
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "study_root": str(study_root),
                    "current_work_unit": {
                        "status": "owner_receipt_recorded",
                        "owner": "gate_clearing_batch",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": "sha256:gate-replay-current",
                    },
                    "paper_recovery_state": recovery_state,
                }
            ],
        },
    )

    same_tick_calls: list[dict[str, object]] = []

    def fake_same_tick(**kwargs):
        same_tick_calls.append(kwargs)
        return {
            "surface": "developer_supervisor_same_tick",
            "stop_reason": "typed_blocker_or_dispatch_blocker_observed",
            "study_ids": [study_id],
            "iterations": [{"owner_route_reconcile": {"surface": "portable_owner_route_reconcile"}}],
        }

    monkeypatch.setattr(module, "_run_developer_supervisor_same_tick", fake_same_tick)
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
                "current_work_unit": {
                    "status": "owner_receipt_recorded",
                    "owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": "sha256:gate-replay-current",
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
        request_opl_owner_route_reconcile=True,
    )

    assert [call["study_ids"] for call in same_tick_calls] == [(study_id,)]
    assert report["developer_supervisor_same_tick"]["stop_reason"] == (
        "typed_blocker_or_dispatch_blocker_observed"
    )
    outcomes = report["managed_study_obligation_actuator_outcomes"]
    assert not [
        outcome for outcome in outcomes if outcome.get("outcome_kind") == "owner_receipt_ref"
    ]
    typed_blocker_outcomes = [
        outcome for outcome in outcomes if outcome.get("outcome_kind") == "typed_blocker_ref"
    ]
    assert len(typed_blocker_outcomes) == 1
    _assert_exactly_one_dhd_apply_outcome(typed_blocker_outcomes[0], "typed_blocker_ref")
    blocker = typed_blocker_outcomes[0]["typed_control_blocker"]
    assert blocker["blocker_type"] == "non_advancing_apply"
    assert blocker["surface_kind"] == "mas_domain_typed_blocker"
    assert blocker["owner_answer_shape"] == "typed_blocker_ref"
    assert blocker["mas_authority_result_shape"] == "typed_blocker_ref"
    _assert_obligation_typed_blocker_authority_result(
        study_root=study_root,
        outcome=typed_blocker_outcomes[0],
    )
    assert blocker["private_actuator_surface_retired"] is True
    assert blocker["actuator_private_write_authority"] is False
    assert blocker["source"] == "domain_health_diagnostic.obligation_readback_projection"
    assert blocker["non_advancing_apply"] is True
    assert blocker["paper_progress_policy_result"]["recommended_opl_transition_kind"] == (
        "NonAdvancingApply"
    )
    assert blocker["authority_boundary"]["provider_admission_requires_opl_runtime_result"] is True
    assert blocker["authority_boundary"]["can_write_fail_closed_typed_control_blocker"] is False
    assert blocker["authority_boundary"]["fail_closed_typed_blocker_surface"] == (
        "mas_domain_typed_blocker"
    )
    assert blocker["authority_boundary"]["actuator_can_write_private_blocker_surface"] is False
    assert "provider_admission_pending_requires_mas_transition_request" not in blocker[
        "authority_boundary"
    ]
    assert blocker["next_safe_action_kind"] == (
        "consume_owner_receipt"
    )
    assert report["managed_study_actions"][0]["dhd_apply_postcondition"]["ok"] is False


def test_domain_health_diagnostic_apply_continues_same_tick_for_successor_owner_gate(
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
    typed_blocker_ref = (
        "artifacts/supervision/consumer/default_executor_execution/"
        "sat_67e10efde628859185249aa0.closeout.json#typed_blocker"
    )
    recovery_state = {
        "surface_kind": "paper_recovery_state",
        "phase": "owner_action_ready",
        "current_authority": {
            "obligation": {
                "owner": "one-person-lab",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "ai_reviewer_record_gate_consumption"
                ),
            }
        },
        "next_safe_action": {
            "kind": "materialize_successor_owner_gate",
            "owner": "one-person-lab",
            "provider_admission_allowed": False,
        },
        "supervisor_decision": {"decision": "materialize_recovery_action"},
        "evidence_refs": [f"typed_blocker:{typed_blocker_ref}"],
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
                    "current_work_unit": {
                        "status": "typed_blocker",
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "ai_reviewer_record_gate_consumption",
                        "work_unit_fingerprint": (
                            "domain-transition::route_back_same_line::"
                            "ai_reviewer_record_gate_consumption"
                        ),
                        "state": {
                            "typed_blocker": {
                                "blocker_type": "anti_loop_budget_exhausted",
                                "typed_blocker_ref": typed_blocker_ref,
                            }
                        },
                    },
                    "paper_recovery_state": recovery_state,
                }
            ],
        },
    )
    same_tick_calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        module,
        "_run_developer_supervisor_same_tick",
        lambda **kwargs: same_tick_calls.append(kwargs)
        or {
            "surface": "developer_supervisor_same_tick",
            "stop_reason": "owner_action_projected_but_not_materialized",
            "study_ids": [study_id],
            "iterations": [{"owner_route_reconcile": {"surface": "portable_owner_route_reconcile"}}],
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
    monkeypatch.setattr(module, "_fresh_progress_currentness_for_report", lambda **kwargs: {})

    report = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        apply=True,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
        request_opl_owner_route_reconcile=True,
    )

    assert [call["study_ids"] for call in same_tick_calls] == [(study_id,)]
    assert report["developer_supervisor_same_tick"]["stop_reason"] == (
        "owner_action_projected_but_not_materialized"
    )


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
            "kind": "materialize_mas_transition_request_or_owner_callable",
            "owner": "write",
            "provider_admission_allowed": True,
        },
        "supervisor_decision": {
            "decision": "materialize_recovery_action",
            "next_safe_action": {
                "kind": "materialize_recovery_work_unit_or_receipt",
                "source_next_safe_action": {
                    "kind": "materialize_mas_transition_request_or_owner_callable",
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
                        "owner_callable_adapter_count": 1,
                        "ready_owner_callable_adapter_count": 1,
                        "owner_callable_adapters": [
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
    blocker = outcome["typed_control_blocker"]
    assert blocker["blocker_type"] == "non_advancing_apply"
    assert blocker["surface_kind"] == "mas_domain_typed_blocker"
    assert blocker["owner_answer_shape"] == "typed_blocker_ref"
    assert blocker["mas_authority_result_shape"] == "typed_blocker_ref"
    _assert_obligation_typed_blocker_authority_result(
        study_root=study_root,
        outcome=outcome,
    )
    assert blocker["private_actuator_surface_retired"] is True
    assert blocker["actuator_private_write_authority"] is False
    assert blocker["source"] == "domain_health_diagnostic.obligation_readback_projection"
    assert blocker["non_advancing_apply"] is True
    assert blocker["paper_progress_policy_result"]["recommended_opl_transition_kind"] == (
        "NonAdvancingApply"
    )
    assert blocker["authority_boundary"]["provider_admission_requires_opl_runtime_result"] is True
    assert blocker["authority_boundary"]["can_write_fail_closed_typed_control_blocker"] is False
    assert blocker["authority_boundary"]["fail_closed_typed_blocker_surface"] == (
        "mas_domain_typed_blocker"
    )
    assert blocker["authority_boundary"]["actuator_can_write_private_blocker_surface"] is False
    assert "provider_admission_pending_requires_mas_transition_request" not in blocker[
        "authority_boundary"
    ]
    assert report["managed_study_actions"][0]["dhd_apply_postcondition"]["ok"] is False


def _assert_exactly_one_dhd_apply_outcome(
    outcome: dict[str, object],
    expected_kind: str,
) -> None:
    allowed = [
        "transition_request_pending",
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
    source_family = outcome["outcome_source_family"]
    foundation = outcome["opl_foundation_readback_boundary"]
    assert foundation["surface_kind"] == "opl_foundation_readback_boundary"
    assert foundation["source_family"] == source_family
    assert foundation["opl_runtime_owner"] == "one-person-lab"
    assert foundation["mas_role"] == "consume_only_projection"
    assert foundation["mas_can_store_recovery_obligation"] is False
    assert foundation["mas_can_run_supervisor_decision_engine"] is False
    assert foundation["mas_policy_request_projection_can_satisfy_success"] is False
    validator_boundary = foundation["readback_result_validator_boundary"]
    assert validator_boundary["validator_role"] == (
        "accepted_owner_answer_or_opl_readback_shape_validator"
    )
    assert validator_boundary["local_allowed_outcome_table_role"] == (
        "contract_bound_result_shape_validation_not_supervisor_decision_engine"
    )
    assert validator_boundary["mas_can_choose_supervisor_decision"] is False
    assert validator_boundary["mas_can_run_supervisor_decision_engine"] is False
    assert validator_boundary["mas_can_store_recovery_obligation"] is False
    assert validator_boundary["mas_can_create_opl_command_event_or_outbox"] is False
    assert outcome["success_requires_opl_foundation_readback_boundary"] is True
    assert outcome["success_requires_consumed_readback_identity"] is True
    if expected_kind == "transition_request_pending":
        assert source_family == "mas_policy_request_projection"
        assert outcome["request_projection_only"] is True
        assert outcome["postcondition_ok"] is False
        assert "success_outcome_source_family" not in outcome
        assert "consumed_obligation_readback_identity" not in outcome
        assert "dhd_apply_success_proof" not in outcome
        assert foundation["success_source_family_required"] is False
        assert "success_source_family" not in foundation
    else:
        assert source_family in {
            "opl_runtime_readback",
            "mas_owner_answer_readback",
            "mas_domain_authority_readback",
        }
        if outcome["postcondition_ok"] is not True:
            assert "success_outcome_source_family" not in outcome
            assert "dhd_apply_success_proof" not in outcome
            assert foundation["success_source_family"] == source_family
            assert foundation["success_source_family_required"] is True
            return
        assert outcome["success_outcome_source_family"] == source_family
        consumed_identity = outcome["consumed_obligation_readback_identity"]
        assert consumed_identity["surface_kind"] == "consumed_obligation_readback_identity"
        assert consumed_identity["source_family"] == source_family
        assert consumed_identity["outcome_kind"] == expected_kind
        assert consumed_identity["outcome_ref"] == outcome[expected_kind]
        if source_family == "mas_domain_authority_readback":
            assert consumed_identity["domain_authority_ref"] == outcome[expected_kind]
            assert consumed_identity["domain_authority_ref_source"] != (
                "paper_recovery_state.evidence_refs"
            )
            boundary = consumed_identity["domain_authority_boundary"]
            assert boundary["actuator_private_write_authority"] is False
            assert boundary["can_create_opl_command"] is False
            assert boundary["can_create_opl_event"] is False
            assert boundary["can_create_opl_outbox"] is False
            assert boundary["can_create_opl_stage_run"] is False
            assert boundary["can_store_recovery_obligation"] is False
            assert boundary["can_run_supervisor_decision_engine"] is False
            assert boundary["can_authorize_provider_admission"] is False
            assert boundary["can_claim_paper_progress"] is False
            if expected_kind == "typed_blocker_ref":
                assert consumed_identity["domain_authority_surface"] == (
                    "mas_domain_typed_blocker"
                )
                assert consumed_identity["authority_result_surface"] == (
                    "mas_domain_typed_blocker"
                )
                assert consumed_identity["accepted_answer_shape"] == "typed_blocker_ref"
            elif expected_kind in {"human_gate_ref", "route_back_evidence_ref"}:
                assert consumed_identity["domain_authority_surface"] == "owner_gate_decision"
                assert consumed_identity["authority_result_surface"] == "owner_gate_decision"
                assert consumed_identity["accepted_answer_shape"] == expected_kind
        success_proof = outcome["dhd_apply_success_proof"]
        assert success_proof["surface_kind"] == "dhd_apply_success_proof"
        assert success_proof["success_outcome_source_family"] == source_family
        assert success_proof["opl_foundation_readback_boundary"] == foundation
        assert success_proof["consumed_obligation_readback_identity"] == consumed_identity
        assert success_proof["consume_only_readback_boundary"] == outcome[
            "consume_only_readback_boundary"
        ]
        assert success_proof["request_projection_only"] is False
        assert success_proof["request_projection_is_success_outcome"] is False
        assert success_proof["supervisor_disallowed_outcome_is_success"] is False
        assert success_proof["mas_can_store_recovery_obligation"] is False
        assert success_proof["mas_can_run_supervisor_decision_engine"] is False
        assert success_proof["mas_can_run_fixed_point_runtime"] is False
        assert success_proof["mas_can_replay_obligation"] is False
        assert success_proof["opl_foundation_readback_boundary"][
            "readback_result_validator_boundary"
        ] == validator_boundary
        assert foundation["success_source_family"] == source_family
        assert foundation["success_source_family_required"] is True
        assert outcome.get("request_projection_only") is not True


def _assert_obligation_typed_blocker_authority_result(
    *,
    study_root: Path,
    outcome: dict[str, object],
) -> None:
    blocker = outcome["typed_control_blocker"]
    typed_blocker_ref = blocker["typed_blocker_ref"]
    latest_path = (
        study_root
        / "artifacts"
        / "mas_authority"
        / "typed_blockers"
        / "domain_health_diagnostic_obligation"
        / "latest.json"
    )
    history_path = latest_path.parent / "history.jsonl"
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    history = [
        json.loads(line)
        for line in history_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert typed_blocker_ref == str(latest_path)
    if outcome["outcome_kind"] == "typed_blocker_ref":
        assert outcome["typed_blocker_ref"] == typed_blocker_ref
    else:
        assert "typed_blocker_ref" not in outcome
    assert outcome["details"]["authority_result_ref"] == typed_blocker_ref
    assert outcome["details"]["authority_result_adapter"] == (
        "mas_domain_typed_blocker_authority_result_adapter"
    )
    assert blocker["authority_result_ref"] == typed_blocker_ref
    assert blocker["authority_result_adapter"] == (
        "mas_domain_typed_blocker_authority_result_adapter"
    )
    assert blocker["authority_owner"] == "med-autoscience"
    assert blocker["authority_result_surface"] == "mas_domain_typed_blocker"
    assert blocker["actuator_private_write_authority"] is False
    assert blocker["authority_result_boundary"] == outcome["details"][
        "authority_result_boundary"
    ]
    assert blocker["authority_result_boundary"] == {
        "surface_kind": "mas_domain_typed_blocker_authority_result_boundary",
        "authority_owner": "med-autoscience",
        "authority_result_surface": "mas_domain_typed_blocker",
        "adapter_role": "persist_mas_domain_typed_blocker_authority_result",
        "actuator_private_write_authority": False,
        "can_create_opl_command": False,
        "can_create_opl_event": False,
        "can_create_opl_outbox": False,
        "can_create_opl_stage_run": False,
        "can_store_recovery_obligation": False,
        "can_run_supervisor_decision_engine": False,
        "can_authorize_provider_admission": False,
        "can_claim_paper_progress": False,
        "can_write_publication_eval": False,
        "can_write_controller_decision": False,
    }
    assert latest["typed_blocker_ref"] == typed_blocker_ref
    assert latest["authority_result_ref"] == typed_blocker_ref
    assert latest["authority_result_adapter"] == blocker["authority_result_adapter"]
    assert latest["authority_owner"] == "med-autoscience"
    assert latest["authority_result_boundary"] == blocker["authority_result_boundary"]
    assert latest["actuator_private_write_authority"] is False
    assert history[-1] == latest


def test_obligation_actuator_readback_validator_is_not_supervisor_decision_engine() -> None:
    validator = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts."
        "obligation_actuator_parts.readback_result_validator"
    )

    boundary = validator.readback_result_validator_boundary()
    assert boundary["validator_role"] == "accepted_owner_answer_or_opl_readback_shape_validator"
    assert boundary["local_allowed_outcome_table_role"] == (
        "contract_bound_result_shape_validation_not_supervisor_decision_engine"
    )
    assert boundary["mas_can_choose_supervisor_decision"] is False
    assert boundary["mas_can_run_supervisor_decision_engine"] is False
    assert boundary["mas_can_store_recovery_obligation"] is False
    assert boundary["mas_can_replay_obligation"] is False
    assert boundary["mas_can_create_opl_command_event_or_outbox"] is False
    assert boundary["mas_can_generate_human_gate_resume_token"] is False
    assert boundary["postcondition_success_requires_consumed_readback_identity"] is True
    assert boundary["consumed_readback_identity_surface_kind"] == (
        "consumed_obligation_readback_identity"
    )
    assert boundary["mas_domain_authority_readback_requires_authority_boundary"] is True
    assert boundary["read_model_evidence_refs_can_satisfy_success"] is False

    assert validator.allowed_outcomes_for_policy_label("consume_terminal_closeout") == {
        "owner_receipt_ref",
        "typed_blocker_ref",
    }
    assert "owner_receipt_ref" not in validator.allowed_outcomes_for_policy_label(
        "execute_current_owner_delta"
    )
    request_foundation = validator.opl_foundation_readback_boundary(
        source_family="mas_policy_request_projection"
    )
    assert request_foundation["success_source_family_required"] is False
    assert validator.outcome_has_required_foundation_readback(
        source_family="mas_policy_request_projection",
        opl_foundation=request_foundation,
    ) is False


def test_obligation_actuator_transition_request_is_projection_not_success(
    tmp_path: Path,
) -> None:
    actuator = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.obligation_actuator"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action = {
        "study_id": study_id,
        "quest_id": study_id,
        "study_root": str(profile.studies_root / study_id),
        "current_executable_owner_action": {
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "fingerprint-current",
        },
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "owner_action_ready",
            "next_safe_action": {
                "kind": "materialize_mas_transition_request_or_owner_callable",
                "provider_admission_allowed": True,
            },
            "current_authority": {
                "obligation": {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "fingerprint-current",
                }
            },
            "supervisor_decision": {"decision": "execute_current_owner_delta"},
        },
        "provider_admission_candidates": [
            {
                "study_id": study_id,
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "fingerprint-current",
                "opl_domain_progress_transition_request": {
                    "surface_kind": "mas_domain_progress_transition_request",
                    "target_runtime_owner": "one-person-lab",
                    "target_runtime_kind": "DomainProgressTransitionRuntime",
                    "idempotency_key": "transition-request-current",
                    "mas_can_create_opl_outbox_record": False,
                    "aggregate_identity": {
                        "aggregate_kind": "paper_recovery_obligation",
                        "aggregate_id": f"{study_id}:medical_prose_write_repair:fingerprint-current",
                        "study_id": study_id,
                        "work_unit_id": "medical_prose_write_repair",
                    },
                    "source_generation": "source-generation-current",
                    "expected_version": 1,
                    "required_postcondition": {
                        "kind": "owner_receipt_or_typed_blocker",
                        "work_unit_fingerprint": "fingerprint-current",
                    },
                },
            }
        ],
    }
    report = {"managed_study_actions": [action]}

    actuator.apply_managed_study_obligation_actuator(
        report=report,
        profile=profile,
        study_ids=(study_id,),
        current_control_state={},
        fail_closed=True,
        phase="apply",
    )

    outcome = report["managed_study_obligation_actuator_outcomes"][0]
    _assert_exactly_one_dhd_apply_outcome(outcome, "transition_request_pending")
    postcondition = report["managed_study_actions"][0]["dhd_apply_postcondition"]
    assert postcondition["ok"] is False
    assert postcondition["outcome_source_family"] == "mas_policy_request_projection"
    assert postcondition["request_projection_only"] is True
    assert postcondition["dhd_apply_success_proof"] == {}
    assert postcondition["success_requires_opl_foundation_readback_boundary"] is True
    foundation = postcondition["opl_foundation_readback_boundary"]
    assert foundation["source_family"] == "mas_policy_request_projection"
    assert foundation["mas_policy_request_projection_can_satisfy_success"] is False
    assert foundation["success_source_family_required"] is False
    consume_only = postcondition["consume_only_readback_boundary"]
    assert consume_only["surface_kind"] == "domain_health_diagnostic_apply_consume_only_readback"
    assert consume_only["opl_recovery_obligation_store_owner"] == "one-person-lab"
    assert consume_only["opl_supervisor_decision_engine_owner"] == "one-person-lab"
    assert consume_only["mas_can_store_recovery_obligation"] is False
    assert consume_only["mas_can_run_fixed_point_runtime"] is False
    assert consume_only["request_projection_is_success_outcome"] is False


def test_obligation_actuator_disallowed_supervisor_outcome_fails_postcondition(
    tmp_path: Path,
) -> None:
    actuator = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.obligation_actuator"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action = {
        "study_id": study_id,
        "quest_id": study_id,
        "study_root": str(profile.studies_root / study_id),
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "owner_action_ready",
            "next_safe_action": {
                "kind": "run_mas_owner_callable",
                "provider_admission_allowed": False,
            },
            "current_authority": {
                "obligation": {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "fingerprint-current",
                }
            },
            "supervisor_decision": {"decision": "execute_current_owner_delta"},
        },
    }
    report = {
        "managed_study_actions": [action],
        "managed_study_mas_owner_callable_actions": [
            {
                "study_id": study_id,
                "action_type": "run_quality_repair_batch",
                "work_unit_fingerprint": "fingerprint-current",
                "ok": True,
                "status": "executed",
                "record_path": "artifacts/controller/quality_repair_batch/latest.json",
            }
        ],
    }

    actuator.apply_managed_study_obligation_actuator(
        report=report,
        profile=profile,
        study_ids=(study_id,),
        current_control_state={},
        fail_closed=True,
        phase="apply",
    )

    outcome = report["managed_study_obligation_actuator_outcomes"][0]
    assert outcome["outcome_kind"] == "owner_receipt_ref"
    assert outcome["paper_autonomy_supervisor_outcome_allowed"] is False
    assert outcome["postcondition_ok"] is False
    assert "success_outcome_source_family" not in outcome
    assert "dhd_apply_success_proof" not in outcome
    assert outcome["success_requires_opl_foundation_readback_boundary"] is True
    assert outcome["opl_foundation_readback_boundary"]["success_source_family"] == (
        "mas_owner_answer_readback"
    )
    assert outcome["consume_only_readback_boundary"]["supervisor_disallowed_outcome_is_success"] is False
    postcondition = report["managed_study_actions"][0]["dhd_apply_postcondition"]
    assert postcondition["ok"] is False
    assert postcondition["paper_autonomy_supervisor_outcome_allowed"] is False
    assert postcondition["dhd_apply_success_proof"] == {}
    assert postcondition["consume_only_readback_boundary"] == outcome["consume_only_readback_boundary"]
