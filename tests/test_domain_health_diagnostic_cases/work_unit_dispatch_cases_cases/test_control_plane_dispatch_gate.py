from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def _domain_health_diagnostic_tick_request(study_root: Path, quest_root: Path) -> dict[str, object]:
    return {
        "study_root": study_root,
        "charter_ref": _write_charter(study_root),
        "publication_eval_ref": _write_publication_eval(
            study_root,
            quest_root,
            action_type="bounded_analysis",
        ),
        "decision_type": "bounded_analysis",
        "route_target": "analysis-campaign",
        "route_key_question": "analysis_claim_evidence_repair: Repair claim-evidence blockers.",
        "route_rationale": "Run bounded claim-evidence repair.",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "run_gate_clearing_batch",
                "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": "Run bounded claim-evidence repair.",
        "work_unit_fingerprint": "publication-blockers::control-plane",
        "next_work_unit": {
            "unit_id": "analysis_claim_evidence_repair",
            "lane": "analysis-campaign",
            "summary": "Repair claim-evidence blockers.",
        },
    }


def _authority_snapshot(*, state: str, blocking_reasons: list[str] | None = None) -> dict[str, object]:
    blocked = state == "blocked"
    return {
        "schema_version": 1,
        "surface": "authority_snapshot",
        "control_state": "ready" if not blocked else "supervisor_gated",
        "canonical_next_action": "resume_same_study_line",
        "canonical_runtime_action": "continue_supervising_runtime",
        "dispatch_gate": {
            "state": state,
            "dispatch_allowed": not blocked,
            "blocking_reasons": blocking_reasons or [],
        },
        "route_authorization": {
            "authorized": not blocked,
            "paper_write_allowed": not blocked,
            "bundle_build_allowed": not blocked,
            "runtime_recovery_allowed": True,
        },
        "blocking_reasons": blocking_reasons or [],
        "allowed_controller_actions": ["read_runtime_status", "reconcile_control_plane"],
        "quality_gate_relaxation_allowed": False,
    }


@pytest.mark.parametrize(
    "blocking_reasons",
    [
        ["execution_owner_guard.supervisor_only"],
        ["publication_supervisor_state.bundle_tasks_downstream_only"],
        ["runtime_recovery_retry_budget_exhausted"],
        ["study_truth_epoch_missing"],
    ],
)
def test_watch_runtime_control_plane_blocked_snapshot_suppresses_outer_loop_dispatch(
    tmp_path: Path,
    monkeypatch,
    blocking_reasons: list[str],
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    tick_request = _domain_health_diagnostic_tick_request(study_root, quest_root)
    status_payload = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="blocked",
            reason="study_completion_publishability_gate_blocked",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "running",
        "authority_snapshot": _authority_snapshot(
            state="blocked",
            blocking_reasons=blocking_reasons,
        ),
    }
    calls: list[str] = []

    def fake_outer_loop_tick(**kwargs):
        calls.append(str(kwargs.get("source") or ""))
        return {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "source": kwargs.get("source"),
            "study_decision_ref": {
                "artifact_path": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve())
            },
            "dispatch_status": "executed",
            "executed_controller_action": {"action_type": "run_gate_clearing_batch", "result": {"status": "executed"}},
        }

    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(module.domain_status_projection, "study_outer_loop_tick", fake_outer_loop_tick)
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )
    wakeup_latest = json.loads(
        (study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json").read_text(encoding="utf-8")
    )
    ledger_events = [
        json.loads(line)
        for line in (
            study_root / "artifacts" / "runtime" / "work_unit_ledger" / "events.jsonl"
        ).read_text(encoding="utf-8").splitlines()
    ]

    assert calls == []
    assert result["managed_study_outer_loop_dispatches"] == []
    assert result["managed_study_no_op_suppressions"][0]["outcome"] == "control_plane_dispatch_blocked"
    assert wakeup_latest["outcome"] == "control_plane_dispatch_blocked"
    assert wakeup_latest["no_op_acknowledged"] is True
    assert wakeup_latest["authority_snapshot"]["dispatch_gate"]["blocking_reasons"] == blocking_reasons
    assert wakeup_latest["control_plane_blocking_reasons"] == [
        *blocking_reasons,
        "route_not_authorized",
    ]
    assert [event["event_type"] for event in ledger_events] == ["control_plane_dispatch_blocked"]


def test_watch_runtime_control_plane_open_snapshot_allows_outer_loop_dispatch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    tick_request = _domain_health_diagnostic_tick_request(study_root, quest_root)
    status_payload = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="blocked",
            reason="study_completion_publishability_gate_blocked",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "running",
        "authority_snapshot": _authority_snapshot(state="open"),
    }
    calls: list[str] = []

    def fake_outer_loop_tick(**kwargs):
        calls.append(str(kwargs.get("source") or ""))
        return {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "source": kwargs.get("source"),
            "study_decision_ref": {
                "artifact_path": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve())
            },
            "dispatch_status": "executed",
            "executed_controller_action": {"action_type": "run_gate_clearing_batch", "result": {"status": "executed"}},
        }

    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(module.domain_status_projection, "study_outer_loop_tick", fake_outer_loop_tick)
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    assert calls == ["domain_health_diagnostic_outer_loop_wakeup"]
    assert len(result["managed_study_outer_loop_dispatches"]) == 1
    assert result["managed_study_no_op_suppressions"] == []


def test_watch_runtime_downstream_bundle_gate_allows_authorized_paper_repair_dispatch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    tick_request = _domain_health_diagnostic_tick_request(study_root, quest_root)
    tick_request["controller_actions"] = [
        {
            "action_type": "run_quality_repair_batch",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]
    status_payload = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="resume",
            reason="quest_waiting_opl_runtime_owner_route",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "authority_snapshot": {
            **_authority_snapshot(
                state="blocked",
                blocking_reasons=[
                    "publication_supervisor_state.bundle_tasks_downstream_only",
                    "runtime_recovery_retry_budget_exhausted",
                ],
            ),
            "control_state": "blocked_runtime_escalation",
            "canonical_next_action": "resume_same_study_line",
            "canonical_runtime_action": "external_supervisor_required",
            "authority_refs": {
                "study_truth": {"epoch": "truth-1"},
                "runtime_health": {"epoch": "runtime-1"},
            },
            "route_authorization": {
                "authorized": False,
                "paper_write_allowed": True,
                "bundle_build_allowed": False,
                "runtime_recovery_allowed": False,
            },
        },
    }
    calls: list[str] = []

    def fake_outer_loop_tick(**kwargs):
        calls.append(str(kwargs.get("source") or ""))
        return {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "source": kwargs.get("source"),
            "study_decision_ref": {
                "artifact_path": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve())
            },
            "dispatch_status": "executed",
            "executed_controller_action": {
                "action_type": "run_quality_repair_batch",
                "result": {"status": "executed"},
            },
        }

    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(module.domain_status_projection, "study_outer_loop_tick", fake_outer_loop_tick)
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )
    wakeup_latest = json.loads(
        (study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json").read_text(encoding="utf-8")
    )

    assert calls == ["domain_health_diagnostic_outer_loop_wakeup"]
    assert len(result["managed_study_outer_loop_dispatches"]) == 1
    assert result["managed_study_no_op_suppressions"] == []
    assert wakeup_latest["outcome"] == "dispatched"
    assert wakeup_latest["work_unit_dispatch_key"] == (
        "publication-blockers::control-plane::analysis_claim_evidence_repair::run_quality_repair_batch"
    )


def test_watch_runtime_downstream_bundle_gate_allows_ai_reviewer_recheck_dispatch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "003-dpcc")
    quest_root = profile.runtime_root / "quest-003"
    recheck_work_unit = {
        "unit_id": "ai_reviewer_recheck",
        "lane": "review",
        "summary": "Return the current manuscript and evidence refs to the AI reviewer workflow.",
    }
    tick_request = {
        "study_root": study_root,
        "charter_ref": _write_charter(study_root),
        "publication_eval_ref": _write_publication_eval(
            study_root,
            quest_root,
            action_type="continue_same_line",
            work_unit_fingerprint="domain-transition::ai_reviewer_re_eval::ai_reviewer_recheck",
            next_work_unit=recheck_work_unit,
        ),
        "decision_type": "continue_same_line",
        "route_target": "review",
        "route_key_question": "ai_reviewer_recheck: Rebuild manuscript quality authority.",
        "route_rationale": "The migrated current manuscript body requires a fresh AI reviewer record.",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "return_to_ai_reviewer_workflow",
                "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": "Return the current manuscript and evidence refs to the AI reviewer workflow.",
        "work_unit_fingerprint": "domain-transition::ai_reviewer_re_eval::ai_reviewer_recheck",
        "next_work_unit": recheck_work_unit,
    }
    status_payload = {
        **make_progress_projection_payload(
            study_id="003-dpcc",
            decision="resume",
            reason="quest_waiting_opl_runtime_owner_route",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-003",
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "authority_snapshot": {
            **_authority_snapshot(
                state="blocked",
                blocking_reasons=["publication_supervisor_state.bundle_tasks_downstream_only"],
            ),
            "control_state": "supervisor_gated",
            "authority_refs": {
                "study_truth": {"epoch": "truth-1"},
                "runtime_health": {"epoch": "runtime-1"},
            },
            "route_authorization": {
                "authorized": False,
                "paper_write_allowed": True,
                "managed_worker_paper_write_allowed": True,
                "foreground_paper_write_allowed": True,
                "bundle_build_allowed": False,
                "foreground_bundle_build_allowed": False,
                "runtime_recovery_allowed": True,
            },
        },
    }
    calls: list[str] = []

    def fake_outer_loop_tick(**kwargs):
        calls.append(str(kwargs.get("source") or ""))
        return {
            "study_id": "003-dpcc",
            "quest_id": "quest-003",
            "source": kwargs.get("source"),
            "study_decision_ref": {
                "artifact_path": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve())
            },
            "dispatch_status": "executed",
            "executed_controller_action": {
                "action_type": "return_to_ai_reviewer_workflow",
                "result": {"status": "executed"},
            },
        }

    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(module.domain_status_projection, "study_outer_loop_tick", fake_outer_loop_tick)
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )
    wakeup_latest = json.loads(
        (study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json").read_text(encoding="utf-8")
    )

    assert calls == ["domain_health_diagnostic_outer_loop_wakeup"]
    assert len(result["managed_study_outer_loop_dispatches"]) == 1
    assert result["managed_study_no_op_suppressions"] == []
    assert wakeup_latest["outcome"] == "dispatched"
    assert wakeup_latest["work_unit_dispatch_key"] == (
        "domain-transition::ai_reviewer_re_eval::ai_reviewer_recheck::"
        "ai_reviewer_recheck::return_to_ai_reviewer_workflow"
    )


def test_watch_runtime_downstream_bundle_gate_allows_ai_reviewer_current_analysis_harmonization_record_dispatch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "002-dm")
    quest_root = profile.runtime_root / "quest-002"
    work_unit = {
        "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_analysis_harmonization",
        "lane": "review",
        "summary": "Produce a current AI reviewer publication-eval record before dispatching the publication-eval workflow.",
    }
    tick_request = {
        "study_root": study_root,
        "charter_ref": _write_charter(study_root),
        "publication_eval_ref": _write_publication_eval(
            study_root,
            quest_root,
            action_type="continue_same_line",
            work_unit_fingerprint=(
                "domain-transition::ai_reviewer_re_eval::"
                "produce_ai_reviewer_publication_eval_record_against_current_analysis_harmonization"
            ),
            next_work_unit=work_unit,
        ),
        "decision_type": "continue_same_line",
        "route_target": "review",
        "route_key_question": (
            "produce_ai_reviewer_publication_eval_record_against_current_analysis_harmonization: "
            "Rebuild current analysis-harmonization AI reviewer authority."
        ),
        "route_rationale": "The current analysis harmonization rerun requires a fresh AI reviewer record.",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "return_to_ai_reviewer_workflow",
                "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": "Return current analysis harmonization refs to the AI reviewer workflow.",
        "work_unit_fingerprint": (
            "domain-transition::ai_reviewer_re_eval::"
            "produce_ai_reviewer_publication_eval_record_against_current_analysis_harmonization"
        ),
        "next_work_unit": work_unit,
    }
    status_payload = {
        **make_progress_projection_payload(
            study_id="002-dm",
            decision="resume",
            reason="quest_waiting_opl_runtime_owner_route",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-002",
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "authority_snapshot": {
            **_authority_snapshot(
                state="blocked",
                blocking_reasons=["publication_supervisor_state.bundle_tasks_downstream_only"],
            ),
            "control_state": "supervisor_gated",
            "authority_refs": {
                "study_truth": {"epoch": "truth-1"},
                "runtime_health": {"epoch": "runtime-1"},
            },
            "route_authorization": {
                "authorized": False,
                "paper_write_allowed": True,
                "managed_worker_paper_write_allowed": True,
                "foreground_paper_write_allowed": True,
                "bundle_build_allowed": False,
                "foreground_bundle_build_allowed": False,
                "runtime_recovery_allowed": True,
            },
        },
    }
    calls: list[str] = []

    def fake_outer_loop_tick(**kwargs):
        calls.append(str(kwargs.get("source") or ""))
        return {
            "study_id": "002-dm",
            "quest_id": "quest-002",
            "source": kwargs.get("source"),
            "study_decision_ref": {
                "artifact_path": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve())
            },
            "dispatch_status": "executed",
            "executed_controller_action": {
                "action_type": "return_to_ai_reviewer_workflow",
                "result": {"status": "executed"},
            },
        }

    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(module.domain_status_projection, "study_outer_loop_tick", fake_outer_loop_tick)
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )
    wakeup_latest = json.loads(
        (study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json").read_text(encoding="utf-8")
    )

    assert calls == ["domain_health_diagnostic_outer_loop_wakeup"]
    assert len(result["managed_study_outer_loop_dispatches"]) == 1
    assert result["managed_study_no_op_suppressions"] == []
    assert wakeup_latest["outcome"] == "dispatched"
    assert wakeup_latest["work_unit_dispatch_key"] == (
        "domain-transition::ai_reviewer_re_eval::"
        "produce_ai_reviewer_publication_eval_record_against_current_analysis_harmonization::"
        "produce_ai_reviewer_publication_eval_record_against_current_analysis_harmonization::"
        "return_to_ai_reviewer_workflow"
    )


def test_watch_domain_route_only_runtime_block_allows_managed_submission_refresh_dispatch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "003-dpcc")
    quest_root = profile.runtime_root / "quest-003"
    submission_work_unit = {
        "unit_id": "submission_minimal_refresh",
        "lane": "controller",
        "summary": "Refresh stale submission package surfaces.",
    }
    tick_request = {
        "study_root": study_root,
        "charter_ref": _write_charter(study_root),
        "publication_eval_ref": _write_publication_eval(
            study_root,
            quest_root,
            action_type="bounded_analysis",
            work_unit_fingerprint="publication-blockers::submission-refresh",
            next_work_unit=submission_work_unit,
        ),
        "decision_type": "bounded_analysis",
        "route_target": "controller",
        "route_key_question": "submission_minimal_refresh: Refresh stale submission package surfaces.",
        "route_rationale": "Run controller-owned submission package refresh.",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "run_gate_clearing_batch",
                "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": "Run controller-owned submission package refresh.",
        "work_unit_fingerprint": "publication-blockers::submission-refresh",
        "next_work_unit": submission_work_unit,
        "blocking_work_units": [submission_work_unit],
    }
    status_payload = {
        **make_progress_projection_payload(
            study_id="003-dpcc",
            decision="resume",
            reason="quest_waiting_opl_runtime_owner_route",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-003",
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "authority_snapshot": {
            **_authority_snapshot(
                state="blocked",
                blocking_reasons=[
                    "execution_owner_guard.supervisor_only",
                    "live_worker_meaningful_artifact_delta_timeout",
                    "same_fingerprint_loop",
                ],
            ),
            "control_state": "supervisor_gated",
            "authority_refs": {
                "study_truth": {"epoch": "truth-1"},
                "runtime_health": {"epoch": "runtime-1"},
            },
            "route_authorization": {
                "authorized": False,
                "paper_write_allowed": False,
                "bundle_build_allowed": False,
                "runtime_recovery_allowed": False,
            },
        },
    }
    calls: list[str] = []

    def fake_outer_loop_tick(**kwargs):
        calls.append(str(kwargs.get("source") or ""))
        return {
            "study_id": "003-dpcc",
            "quest_id": "quest-003",
            "source": kwargs.get("source"),
            "study_decision_ref": {
                "artifact_path": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve())
            },
            "dispatch_status": "executed",
            "executed_controller_action": {
                "action_type": "run_gate_clearing_batch",
                "result": {"status": "executed"},
            },
        }

    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(module.domain_status_projection, "study_outer_loop_tick", fake_outer_loop_tick)
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )
    wakeup_latest = json.loads(
        (study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json").read_text(encoding="utf-8")
    )

    assert calls == ["domain_health_diagnostic_outer_loop_wakeup"]
    assert len(result["managed_study_outer_loop_dispatches"]) == 1
    assert result["managed_study_no_op_suppressions"] == []
    assert wakeup_latest["outcome"] == "dispatched"
    assert wakeup_latest["work_unit_dispatch_key"] == (
        "publication-blockers::submission-refresh::submission_minimal_refresh::run_gate_clearing_batch"
    )


def test_watch_runtime_downstream_only_still_blocks_managed_submission_refresh_dispatch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "003-dpcc")
    quest_root = profile.runtime_root / "quest-003"
    submission_work_unit = {
        "unit_id": "submission_minimal_refresh",
        "lane": "controller",
        "summary": "Refresh stale submission package surfaces.",
    }
    tick_request = {
        "study_root": study_root,
        "charter_ref": _write_charter(study_root),
        "publication_eval_ref": _write_publication_eval(
            study_root,
            quest_root,
            action_type="bounded_analysis",
            work_unit_fingerprint="publication-blockers::submission-refresh",
            next_work_unit=submission_work_unit,
        ),
        "decision_type": "bounded_analysis",
        "route_target": "controller",
        "route_key_question": "submission_minimal_refresh: Refresh stale submission package surfaces.",
        "route_rationale": "Run controller-owned submission package refresh.",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "run_gate_clearing_batch",
                "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": "Run controller-owned submission package refresh.",
        "work_unit_fingerprint": "publication-blockers::submission-refresh",
        "next_work_unit": submission_work_unit,
        "blocking_work_units": [submission_work_unit],
    }
    status_payload = {
        **make_progress_projection_payload(
            study_id="003-dpcc",
            decision="blocked",
            reason="study_completion_publishability_gate_blocked",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-003",
        "quest_root": str(quest_root),
        "quest_status": "running",
        "authority_snapshot": {
            **_authority_snapshot(
                state="blocked",
                blocking_reasons=["publication_supervisor_state.bundle_tasks_downstream_only"],
            ),
            "authority_refs": {
                "study_truth": {"epoch": "truth-1"},
                "runtime_health": {"epoch": "runtime-1"},
            },
            "route_authorization": {
                "authorized": False,
                "paper_write_allowed": False,
                "bundle_build_allowed": False,
                "runtime_recovery_allowed": True,
            },
        },
    }
    calls: list[str] = []

    def fake_outer_loop_tick(**kwargs):
        calls.append(str(kwargs.get("source") or ""))
        return {"dispatch_status": "executed"}

    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(module.domain_status_projection, "study_outer_loop_tick", fake_outer_loop_tick)
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )
    wakeup_latest = json.loads(
        (study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json").read_text(encoding="utf-8")
    )

    assert calls == []
    assert result["managed_study_outer_loop_dispatches"] == []
    assert result["managed_study_no_op_suppressions"][0]["outcome"] == "control_plane_dispatch_blocked"
    assert wakeup_latest["outcome"] == "control_plane_dispatch_blocked"
    assert "publication_supervisor_state.bundle_tasks_downstream_only" in wakeup_latest[
        "control_plane_blocking_reasons"
    ]


def test_control_plane_blocked_request_supersedes_stale_specificity_decision(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    _write_charter(study_root)
    specificity_work_unit = {
        "unit_id": "gate_needs_specificity",
        "lane": "controller",
        "summary": "Ask the publication gate to identify concrete blocker targets.",
    }
    specificity_publication_eval_ref = _write_publication_eval(
        study_root,
        quest_root,
        action_type="return_to_controller",
        work_unit_fingerprint="publication-blockers::vague",
        next_work_unit=specificity_work_unit,
    )
    specificity_tick_request = {
        "study_root": study_root,
        "charter_ref": _write_charter(study_root),
        "publication_eval_ref": specificity_publication_eval_ref,
        "decision_type": "return_to_controller",
        "route_target": "controller",
        "route_key_question": "gate_needs_specificity: Which exact claim is blocking the publication gate?",
        "route_rationale": "Publication gate needs concrete blocker targets before dispatch.",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "request_gate_specificity",
                "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": "Publication gate needs concrete blocker targets before dispatch.",
        "work_unit_fingerprint": "publication-blockers::vague",
        "next_work_unit": specificity_work_unit,
    }
    status_payload = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="blocked",
            reason="study_completion_publishability_gate_blocked",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "running",
    }

    monkeypatch.setattr(
        module.study_outer_loop,
        "build_domain_health_diagnostic_outer_loop_tick_request",
        lambda **_: specificity_tick_request,
    )
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )
    stale_decision = json.loads(
        (study_root / "artifacts" / "controller_decisions" / "latest.json").read_text(encoding="utf-8")
    )
    assert stale_decision["next_work_unit"]["unit_id"] == "gate_needs_specificity"

    actionable_work_unit = {
        "unit_id": "analysis_claim_evidence_repair",
        "lane": "analysis-campaign",
        "summary": "Repair claim-evidence blockers.",
    }
    actionable_publication_eval_ref = _write_publication_eval(
        study_root,
        quest_root,
        action_type="bounded_analysis",
        work_unit_fingerprint="publication-blockers::specific",
        next_work_unit=actionable_work_unit,
    )
    actionable_tick_request = {
        "study_root": study_root,
        "charter_ref": _write_charter(study_root),
        "publication_eval_ref": actionable_publication_eval_ref,
        "decision_type": "bounded_analysis",
        "route_target": "analysis-campaign",
        "route_key_question": "analysis_claim_evidence_repair: Repair claim-evidence blockers.",
        "route_rationale": "Run bounded claim-evidence repair.",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "request_opl_stage_attempt",
                "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": "Run bounded claim-evidence repair.",
        "work_unit_fingerprint": "publication-blockers::specific",
        "next_work_unit": actionable_work_unit,
        "blocking_work_units": [actionable_work_unit],
    }
    blocked_status_payload = {
        **status_payload,
        "authority_snapshot": _authority_snapshot(
            state="blocked",
            blocking_reasons=["execution_owner_guard.supervisor_only"],
        ),
    }
    dispatch_calls: list[str] = []

    def fake_outer_loop_tick(**kwargs):
        dispatch_calls.append(str(kwargs.get("source") or ""))
        return {"dispatch_status": "executed"}

    monkeypatch.setattr(
        module.study_outer_loop,
        "build_domain_health_diagnostic_outer_loop_tick_request",
        lambda **_: actionable_tick_request,
    )
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: blocked_status_payload)
    monkeypatch.setattr(module.domain_status_projection, "study_outer_loop_tick", fake_outer_loop_tick)

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )
    current_decision = json.loads(
        (study_root / "artifacts" / "controller_decisions" / "latest.json").read_text(encoding="utf-8")
    )
    wakeup_latest = json.loads(
        (study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json").read_text(encoding="utf-8")
    )

    assert dispatch_calls == []
    assert result["managed_study_outer_loop_dispatches"] == []
    assert result["managed_study_no_op_suppressions"][0]["outcome"] == "control_plane_dispatch_blocked"
    assert wakeup_latest["outcome"] == "control_plane_dispatch_blocked"
    assert wakeup_latest["controller_decision"]["dispatch_status"] == "recorded_non_dispatching"
    assert current_decision["decision_type"] == "bounded_analysis"
    assert current_decision["work_unit_fingerprint"] == "publication-blockers::specific"
    assert current_decision["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"


def test_watch_runtime_recovery_authorization_false_suppresses_runtime_recovery_dispatch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    status_payload = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="resume",
            reason="quest_marked_running_but_no_live_session",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(profile.runtime_root / "quest-001"),
        "quest_status": "running",
        "authority_snapshot": {
            **_authority_snapshot(
                state="blocked",
                blocking_reasons=["runtime_recovery_retry_budget_exhausted"],
            ),
            "canonical_runtime_action": "escalate_runtime",
            "route_authorization": {
                "authorized": False,
                "paper_write_allowed": False,
                "bundle_build_allowed": False,
                "runtime_recovery_allowed": False,
            },
        },
    }
    monkeypatch.setattr(module.domain_health_diagnostic_recovery_policy, "hold_for_flapping_circuit_breaker", lambda **_: None)
    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: None)
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    assert result["managed_study_auto_recoveries"] == []
    assert result["managed_study_actions"][0]["decision"] == "blocked"
    assert result["managed_study_actions"][0]["reason"] == "resume_request_failed"
    assert result["managed_study_actions"][0]["authority_snapshot"]["route_authorization"][
        "runtime_recovery_allowed"
    ] is False


def test_watch_runtime_blocks_retry_budget_exhausted_even_if_snapshot_was_marked_open(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    recovery_work_unit = {
        "unit_id": "runtime_recovery",
        "lane": "runtime",
        "summary": "Recover missing live worker.",
    }
    tick_request = {
        "study_root": study_root,
        "charter_ref": _write_charter(study_root),
        "publication_eval_ref": _write_publication_eval(study_root, quest_root, action_type="bounded_analysis"),
        "decision_type": "bounded_analysis",
        "route_target": "runtime",
        "route_key_question": "Recover the missing live worker before paper work continues.",
        "route_rationale": "Runtime retry budget was exhausted, but MAS controller owns a bounded recovery action.",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "request_opl_stage_attempt",
                "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": "Recover the missing live worker.",
        "work_unit_fingerprint": "runtime-recovery::retry-budget-exhausted",
        "next_work_unit": recovery_work_unit,
    }
    status_payload = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="resume",
            reason="quest_marked_running_but_no_live_session",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "running",
        "authority_snapshot": {
            "schema_version": 1,
            "surface": "authority_snapshot",
            "control_state": "ready",
            "canonical_next_action": "resume_same_study_line",
            "canonical_runtime_action": "recover_runtime",
            "dispatch_gate": {
                "state": "open",
                "dispatch_allowed": True,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
            "route_authorization": {
                "authorized": True,
                "paper_write_allowed": False,
                "bundle_build_allowed": False,
                "runtime_recovery_allowed": True,
            },
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
        },
    }
    dispatch_calls: list[str] = []

    def fake_outer_loop_tick(**kwargs):
        dispatch_calls.append(str(kwargs.get("source") or ""))
        return {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "source": kwargs.get("source"),
            "study_decision_ref": {
                "artifact_path": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve())
            },
            "dispatch_status": "executed",
            "executed_controller_action": {"action_type": "request_opl_stage_attempt", "result": {"status": "executed"}},
        }

    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(module.domain_status_projection, "study_outer_loop_tick", fake_outer_loop_tick)
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    wakeup_latest = json.loads(
        (study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json").read_text(encoding="utf-8")
    )

    assert dispatch_calls == []
    assert result["managed_study_outer_loop_dispatches"] == []
    assert result["managed_study_no_op_suppressions"][0]["outcome"] == "control_plane_dispatch_blocked"
    assert wakeup_latest["outcome"] == "control_plane_dispatch_blocked"
    assert "runtime_recovery_retry_budget_exhausted" in wakeup_latest["control_plane_blocking_reasons"]
