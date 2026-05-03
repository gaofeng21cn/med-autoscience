from __future__ import annotations

from tests.test_runtime_watch_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_watch_runtime_closes_platform_repair_when_inputs_show_gate_delta(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    ledger = importlib.import_module("med_autoscience.controllers.work_unit_ledger")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    _write_charter(study_root)
    _write_publication_eval(study_root, quest_root, action_type="bounded_analysis")
    status_payload = {
        **make_study_runtime_status_payload(
            study_id="001-risk",
            decision="blocked",
            reason="study_completion_publishability_gate_blocked",
            include_control_plane_snapshot=True,
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "running",
    }
    tick_request = {
        "study_root": study_root,
        "charter_ref": _write_charter(study_root),
        "publication_eval_ref": _write_publication_eval(study_root, quest_root, action_type="bounded_analysis"),
        "decision_type": "bounded_analysis",
        "route_target": "analysis-campaign",
        "route_key_question": "analysis_claim_evidence_repair: Repair claim-evidence blockers.",
        "route_rationale": "Run bounded claim-evidence repair.",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "ensure_study_runtime",
                "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": "Run bounded claim-evidence repair.",
        "work_unit_fingerprint": "publication-blockers::same",
        "next_work_unit": {
            "unit_id": "analysis_claim_evidence_repair",
            "lane": "analysis-campaign",
            "summary": "Repair claim-evidence blockers.",
        },
    }
    identity = module.runtime_watch_work_units.identity_from_tick_request(
        study_id="001-risk",
        quest_id="quest-001",
        tick_request=tick_request,
    )
    ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="platform_repair_required",
        payload={
            "source": "runtime_watch_outer_loop_wakeup",
            "wakeup_outcome": "platform_repair_required",
            "wakeup_reason": "outer-loop work unit redrive budget exhausted without result evidence",
        },
        recorded_at="2026-05-02T04:45:16+00:00",
    )
    latest_path = study_root / "artifacts" / "runtime" / "runtime_watch_wakeup" / "latest.json"
    dump_json(
        latest_path,
        {
            "outcome": "platform_repair_required",
            "work_unit_dispatch_key": identity.dispatch_key,
            "input_fingerprint": "old-input",
            "watched_inputs": {
                "artifacts": {
                    "publication_eval_latest": {"sha256": "old-eval", "mtime_ns": 1},
                    "publication_gate_latest": {"sha256": "old-gate", "mtime_ns": 1},
                }
            },
        },
    )
    dump_json(
        quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json",
        {
            "schema_version": 1,
            "generated_at": "2026-05-02T05:00:00+00:00",
            "status": "blocked",
            "gate_fingerprint": "publication-gate::new",
        },
    )
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
            "executed_controller_action": {"action_type": "ensure_study_runtime", "result": {"status": "executed"}},
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
    wakeup_latest = json.loads(latest_path.read_text(encoding="utf-8"))
    ledger_events = [
        json.loads(line)
        for line in (
            study_root / "artifacts" / "runtime" / "work_unit_ledger" / "events.jsonl"
        ).read_text(encoding="utf-8").splitlines()
    ]

    assert calls == ["runtime_watch_outer_loop_wakeup"]
    assert len(result["managed_study_outer_loop_dispatches"]) == 1
    assert result["managed_study_no_op_suppressions"] == []
    assert wakeup_latest["outcome"] == "dispatched"
    assert [event["event_type"] for event in ledger_events] == [
        "platform_repair_required",
        "closed",
        "dispatched",
    ]
    assert ledger_events[1]["payload"]["gate_fingerprint_before"] == "old-gate"
    assert ledger_events[1]["payload"]["gate_fingerprint_after"] != "old-gate"
