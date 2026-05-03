from __future__ import annotations

from tests.test_runtime_watch_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def _runtime_watch_tick_request(study_root: Path, quest_root: Path) -> dict[str, object]:
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


def _control_plane_snapshot(*, state: str, blocking_reasons: list[str] | None = None) -> dict[str, object]:
    blocked = state == "blocked"
    return {
        "schema_version": 1,
        "surface": "control_plane_snapshot",
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
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    tick_request = _runtime_watch_tick_request(study_root, quest_root)
    status_payload = {
        **make_study_runtime_status_payload(
            study_id="001-risk",
            decision="blocked",
            reason="study_completion_publishability_gate_blocked",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "running",
        "control_plane_snapshot": _control_plane_snapshot(
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

    monkeypatch.setattr(module.study_outer_loop, "build_runtime_watch_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(module.study_runtime_router, "study_outer_loop_tick", fake_outer_loop_tick)
    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", lambda **_: status_payload)
    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )
    wakeup_latest = json.loads(
        (study_root / "artifacts" / "runtime" / "runtime_watch_wakeup" / "latest.json").read_text(encoding="utf-8")
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
    assert wakeup_latest["control_plane_snapshot"]["dispatch_gate"]["blocking_reasons"] == blocking_reasons
    assert wakeup_latest["control_plane_blocking_reasons"] == [
        *blocking_reasons,
        "route_not_authorized",
    ]
    assert [event["event_type"] for event in ledger_events] == ["control_plane_dispatch_blocked"]


def test_watch_runtime_control_plane_open_snapshot_allows_outer_loop_dispatch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    tick_request = _runtime_watch_tick_request(study_root, quest_root)
    status_payload = {
        **make_study_runtime_status_payload(
            study_id="001-risk",
            decision="blocked",
            reason="study_completion_publishability_gate_blocked",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "running",
        "control_plane_snapshot": _control_plane_snapshot(state="open"),
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

    monkeypatch.setattr(module.study_outer_loop, "build_runtime_watch_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(module.study_runtime_router, "study_outer_loop_tick", fake_outer_loop_tick)
    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", lambda **_: status_payload)
    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert calls == ["runtime_watch_outer_loop_wakeup"]
    assert len(result["managed_study_outer_loop_dispatches"]) == 1
    assert result["managed_study_no_op_suppressions"] == []


def test_watch_runtime_recovery_authorization_false_suppresses_runtime_recovery_dispatch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    status_payload = {
        **make_study_runtime_status_payload(
            study_id="001-risk",
            decision="resume",
            reason="quest_marked_running_but_no_live_session",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(profile.runtime_root / "quest-001"),
        "quest_status": "running",
        "control_plane_snapshot": {
            **_control_plane_snapshot(
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
    calls: list[str] = []

    def fake_ensure_study_runtime(**kwargs):
        calls.append(str(kwargs.get("source") or ""))
        return status_payload

    monkeypatch.setattr(module.runtime_watch_recovery_policy, "hold_for_flapping_circuit_breaker", lambda **_: None)
    monkeypatch.setattr(module.study_outer_loop, "build_runtime_watch_outer_loop_tick_request", lambda **_: None)
    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure_study_runtime)
    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert calls == []
    assert result["managed_study_auto_recoveries"] == []
    assert result["managed_study_actions"][0]["decision"] == "blocked"
    assert result["managed_study_actions"][0]["reason"] == "resume_request_failed"
    assert result["managed_study_actions"][0]["control_plane_snapshot"]["route_authorization"][
        "runtime_recovery_allowed"
    ] is False
